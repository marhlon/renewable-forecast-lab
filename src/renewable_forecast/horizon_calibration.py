"""Correção aditiva usando apenas resíduos disponíveis antes da emissão.

Instalar em src/renewable_forecast/horizon_calibration.py.
Lê oof_predictions.parquet de um experimento existente; não treina o HGB.
As comparações continuam pertencendo ao desenvolvimento pós-seleção.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def apply_available_offsets(
    predictions: pd.DataFrame,
    *,
    window_hours: int = 168,
    min_history: int = 48,
) -> pd.DataFrame:
    """Janela [origem - window_hours, origem) sobre a disponibilidade.

    A correção é zero enquanto há menos de min_history resíduos elegíveis.
    O histórico usa sempre resíduos do HGB original. Não reinicia por fold.
    """
    for name, value in (("window_hours", window_hours), ("min_history", min_history)):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} deve ser um inteiro positivo.")

    required = {
        "forecast_origin", "target_time", "target_available_at",
        "target_generation", "prediction",
    }
    missing = required - set(predictions.columns)
    if missing:
        raise ValueError(f"Colunas ausentes: {sorted(missing)}")
    data = predictions.copy()
    for column in ("forecast_origin", "target_time", "target_available_at"):
        data[column] = pd.to_datetime(data[column], errors="raise")
        if data[column].isna().any():
            raise ValueError(f"Há timestamps ausentes em {column}.")
    if data["forecast_origin"].duplicated().any():
        raise ValueError("As origens devem ser únicas para esta série/modelo.")
    if not (data["target_time"] > data["forecast_origin"]).all():
        raise ValueError("O alvo deve ocorrer depois da emissão.")
    if not (data["target_available_at"] >= data["target_time"]).all():
        raise ValueError("A disponibilidade não pode anteceder o alvo.")
    for column in ("target_generation", "prediction"):
        data[column] = pd.to_numeric(data[column], errors="raise")
        if not np.isfinite(data[column].to_numpy(dtype=float)).all():
            raise ValueError(f"Há valores não finitos em {column}.")

    data = data.sort_values("forecast_origin").reset_index(drop=True)
    residuals = data["target_generation"] - data["prediction"]
    window = pd.Timedelta(hours=window_hours)
    records = []

    for origin in data["forecast_origin"]:
        eligible = (
            (data["target_available_at"] >= origin - window)
            & (data["target_available_at"] < origin)
        )
        history = residuals.loc[eligible]
        active = len(history) >= min_history
        records.append({
            "calibration_n": len(history),
            "calibration_active": active,
            "calibration_latest_available_at": (
                data.loc[eligible, "target_available_at"].max()
            ),
            "offset_mean": float(history.mean()) if active else 0.0,
            "offset_median": float(history.median()) if active else 0.0,
        })

    result = pd.concat([data, pd.DataFrame(records)], axis=1)
    result["prediction_mean"] = (
        result["prediction"] + result["offset_mean"]
    ).clip(lower=0.0)
    result["prediction_median"] = (
        result["prediction"] + result["offset_median"]
    ).clip(lower=0.0)
    return result


def summarize_offsets(calibrated: pd.DataFrame):
    """Mesmas linhas e mesmos eventos de rampa para todos os métodos.

    MAE, RMSE, RampMAE e viés absoluto do resumo são médias dos folds,
    como na busca. global_signed_bias agrega todos os resíduos com sinal.
    """
    methods = {
        "persistence": "persistence_prediction",
        "hgb_raw": "prediction",
        "hgb_mean": "prediction_mean",
        "hgb_median": "prediction_median",
    }
    records = []
    for fold, group in calibrated.groupby("fold", sort=True):
        actual = group["target_generation"].to_numpy()
        ramp_size = np.abs(actual - group["persistence_prediction"].to_numpy())
        ramp_mask = ramp_size >= np.quantile(ramp_size, 0.90)
        for method, column in methods.items():
            error = actual - group[column].to_numpy()
            bias = float(error.mean())
            records.append({
                "fold": int(fold), "method": method, "rows": len(group),
                "mae": float(np.abs(error).mean()),
                "rmse": float(np.sqrt(np.square(error).mean())),
                "signed_bias": bias, "absolute_bias": abs(bias),
                "ramp_mae": float(np.abs(error[ramp_mask]).mean()),
            })
    folds = pd.DataFrame(records)
    raw_folds = folds.loc[folds["method"].eq("hgb_raw")].set_index("fold")
    summary_rows = []
    for method, column in methods.items():
        selected = folds.loc[folds["method"].eq(method)].set_index("fold")
        summary_rows.append({
            "method": method,
            "rows": len(calibrated),
            "mae": float(selected["mae"].mean()),
            "rmse": float(selected["rmse"].mean()),
            "ramp_mae": float(selected["ramp_mae"].mean()),
            "mean_absolute_fold_bias": float(selected["absolute_bias"].mean()),
            "global_signed_bias": float(
                (calibrated["target_generation"] - calibrated[column]).mean()
            ),
            "folds_mae_better_than_raw": int((selected["mae"] < raw_folds["mae"]).sum()),
        })
    summary = pd.DataFrame(summary_rows)
    raw_mae = float(summary.loc[summary["method"].eq("hgb_raw"), "mae"].iloc[0])
    baseline_mae = float(summary.loc[summary["method"].eq("persistence"), "mae"].iloc[0])
    summary["mae_gain_vs_raw_pct"] = (
        100 * (1 - summary["mae"] / raw_mae) if raw_mae > 0 else np.nan
    )
    summary["existing_gate_passed"] = (
        (summary["mae"] <= 1.02 * baseline_mae)
        & (summary["mean_absolute_fold_bias"] <= 2.0)
    )
    summary["calibration_rule_passed"] = (
        summary["method"].isin(["hgb_mean", "hgb_median"])
        & (summary["mae"] <= raw_mae)
        & (summary["mean_absolute_fold_bias"] <= 2.0)
    )
    return folds, summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--window-hours", type=int, default=168)
    parser.add_argument("--min-history", type=int, default=48)
    args = parser.parse_args(argv)
    source_path = args.run_dir / "oof_predictions.parquet"
    parent = json.loads((args.run_dir / "metadata.json").read_text(encoding="utf-8"))
    predictions = pd.read_parquet(source_path)
    holdout_start = pd.Timestamp(parent["protocol"]["holdout_start"])
    available = pd.to_datetime(predictions["target_available_at"], errors="raise")
    if not (available < holdout_start).all():
        raise ValueError("O arquivo contém alvos fora do desenvolvimento autorizado.")

    calibrated = apply_available_offsets(
        predictions, window_hours=args.window_hours, min_history=args.min_history
    )
    folds, summary = summarize_offsets(calibrated)

    import mlflow
    from renewable_forecast.modeling import _configure_mlflow

    _configure_mlflow("renewable-h6-calibration")
    with mlflow.start_run(run_name="available-residual-mean-vs-median") as run:
        output = args.run_dir / "calibration" / run.info.run_id
        output.mkdir(parents=True, exist_ok=False)
        metadata = {
            "run_id": run.info.run_id,
            "source_run_id": parent["run_id"],
            "source_oof_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            "source_protocol": parent["protocol"],
            "window_hours": args.window_hours,
            "min_history": args.min_history,
            "window_clock": "target_available_at",
            "window_bounds": "[forecast_origin-window, forecast_origin)",
            "insufficient_history_offset": 0.0,
            "history_residual": "target_generation - original_prediction",
            "reset_at_fold_boundary": False,
            "corrected_rows": int(calibrated["calibration_active"].sum()),
            "total_rows": len(calibrated),
            "evaluation_scope": "development_post_selection_prequential",
            "holdout_evaluated": False,
            "calibration_rule": "mean_fold_mae <= raw AND mean_absolute_fold_bias <= 2",
            "summary_metrics": "equal_weight_fold_means_except_global_signed_bias",
        }
        calibrated.to_parquet(output / "calibrated_predictions.parquet", index=False)
        folds.to_csv(output / "fold_metrics.csv", index=False)
        summary.to_csv(output / "summary.csv", index=False)
        (output / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        mlflow.set_tag("source_run_id", parent["run_id"])
        mlflow.log_params({
            "window_hours": args.window_hours, "min_history": args.min_history,
            "horizon_hours": parent["protocol"]["horizon_hours"],
            "availability_delay_hours": parent["protocol"]["availability_delay_hours"],
            "holdout_start": str(holdout_start), "calibration_bias_limit": 2.0,
        })
        for row in summary.to_dict("records"):
            for metric in ("mae", "rmse", "ramp_mae", "mean_absolute_fold_bias", "global_signed_bias"):
                mlflow.log_metric(f"{row['method']}_{metric}", row[metric])
        mlflow.log_artifacts(str(output), artifact_path="causal_calibration")
        print("\nResumo (MAE/RMSE/RampMAE/viés absoluto: médias dos folds):")
        print(summary.round(3).to_string(index=False))
        print("\nResultados por fold:")
        print(folds.loc[folds["method"].ne("persistence"), [
            "fold", "method", "mae", "signed_bias", "absolute_bias"
        ]].round(3).to_string(index=False))
        print(f"\nCorreção ativa em {metadata['corrected_rows']}/{len(calibrated)} emissões.")
        print("Arquivos:", output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
