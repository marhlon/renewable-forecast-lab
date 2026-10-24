"""Avalia o procedimento h+6 congelado no período reservado.

Salvar em src/renewable_forecast/horizon_holdout.py.
Carrega o HGB já ajustado; atualiza somente a correção causal pela média.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from renewable_forecast.features import FEATURE_COLUMNS
from renewable_forecast.horizon_calibration import apply_available_offsets
from renewable_forecast.supervised import build_horizon_training_frame


METHODS = {
    "persistence": "persistence_prediction",
    "hgb_raw": "prediction",
    "hgb_mean": "prediction_mean",
}
PREDICTION_COLUMNS = [
    "forecast_origin", "target_time", "target_available_at", "history_end",
    "target_generation", "prediction", "persistence_prediction",
]


def evaluate_frozen_holdout(
    model, series, seed_oof, *, holdout_start, horizon_hours,
    availability_delay_hours, window_hours, min_history,
):
    """Features causais + HGB fixo + atualização com resíduos já disponíveis.

    As primeiras correções usam resíduos OOF do desenvolvimento. Depois,
    os resíduos do holdout entram apenas quando target_available_at < origem.
    Não se recalculam resíduos de treino com o modelo final.
    """
    start = pd.Timestamp(holdout_start)
    frame = build_horizon_training_frame(
        series, horizon_hours=horizon_hours,
        availability_delay_hours=availability_delay_hours,
    )
    holdout = frame.loc[frame["forecast_origin"] >= start].copy()
    if holdout.empty:
        raise ValueError("Não há emissões com alvo observado no período reservado.")

    # O modelo recebe exclusivamente as 27 features, nunca o alvo.
    holdout["prediction"] = np.maximum(
        model.predict(holdout[FEATURE_COLUMNS]), 0.0
    )
    holdout["persistence_prediction"] = holdout["lag_1h"]
    holdout = holdout[PREDICTION_COLUMNS].copy()
    holdout["evaluation_part"] = "holdout"

    seed = seed_oof[PREDICTION_COLUMNS].copy()
    for column in ("forecast_origin", "target_available_at"):
        seed[column] = pd.to_datetime(seed[column], errors="raise")
    if not (
        (seed["forecast_origin"] < start)
        & (seed["target_available_at"] < start)
    ).all():
        raise ValueError("A semente OOF contém dados fora do desenvolvimento.")
    # Resíduos mais antigos jamais entrarão nas janelas futuras.
    seed = seed.loc[
        seed["target_available_at"] >= start - pd.Timedelta(hours=window_hours)
    ].copy()
    seed["evaluation_part"] = "seed_oof"

    history = pd.concat([seed, holdout], ignore_index=True)
    replay = apply_available_offsets(
        history, window_hours=window_hours, min_history=min_history
    )
    result = replay.loc[replay["evaluation_part"].eq("holdout")].copy()
    # O método foi escolhido no desenvolvimento. A mediana não é avaliada aqui.
    result = result.drop(columns=["offset_median", "prediction_median"])
    result = result.reset_index(drop=True)
    latest = result["calibration_latest_available_at"]
    if not (latest.isna() | (latest < result["forecast_origin"])).all():
        raise ValueError("A correção utilizou um resultado ainda indisponível.")
    return result, seed


def summarize_holdout(predictions, *, holdout_start):
    """Métricas do período inteiro e diagnóstico em blocos fixos de sete dias."""
    data = predictions.copy()
    # Mesmos eventos para os três métodos; definição herdada do diagnóstico.
    change = (data["target_generation"] - data["persistence_prediction"]).abs()
    data["ramp_event"] = change >= change.quantile(0.90)
    data["week"] = (
        (data["forecast_origin"] - pd.Timestamp(holdout_start)).dt.days // 7 + 1
    )

    def metrics(group):
        records = []
        for method, column in METHODS.items():
            error = group["target_generation"] - group[column]
            ramps = error.loc[group["ramp_event"]]
            records.append({
                "method": method, "rows": len(group),
                "mae": float(error.abs().mean()),
                "rmse": float(np.sqrt(np.square(error).mean())),
                "signed_bias": float(error.mean()),
                "absolute_bias": float(abs(error.mean())),
                "ramp_mae": float(ramps.abs().mean()) if len(ramps) else np.nan,
                "ramp_rows": len(ramps),
            })
        return pd.DataFrame(records)

    summary = metrics(data)
    baseline = float(summary.loc[summary["method"].eq("persistence"), "mae"].iloc[0])
    raw = float(summary.loc[summary["method"].eq("hgb_raw"), "mae"].iloc[0])
    summary["mae_gain_vs_persistence_pct"] = (
        100 * (1 - summary["mae"] / baseline) if baseline > 0 else np.nan
    )
    summary["mae_gain_vs_raw_pct"] = (
        100 * (1 - summary["mae"] / raw) if raw > 0 else np.nan
    )
    # Aqui há UMA janela de avaliação. Viés absoluto = |viés do período|.
    summary["mae_not_worse_than_raw"] = summary["mae"] <= raw
    summary["mae_limit_passed"] = summary["mae"] <= 1.02 * baseline
    summary["bias_limit_passed"] = summary["absolute_bias"] <= 2.0
    weeks = []
    for week, group in data.groupby("week", sort=True):
        part = metrics(group)
        part.insert(0, "week", int(week))
        weeks.append(part)
    return data, summary, pd.concat(weeks, ignore_index=True)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--calibration-run-id", required=True)
    args = parser.parse_args(argv)
    source = args.run_dir
    calibration_dir = source / "calibration" / args.calibration_run_id
    parent = json.loads((source / "metadata.json").read_text(encoding="utf-8"))
    calibration = json.loads(
        (calibration_dir / "metadata.json").read_text(encoding="utf-8")
    )
    if calibration["source_run_id"] != parent["run_id"]:
        raise ValueError("A calibração não pertence ao experimento informado.")
    if calibration["source_protocol"] != parent["protocol"]:
        raise ValueError("Os protocolos da busca e da calibração divergem.")
    if sha256(args.input) != parent["input_sha256"]:
        raise ValueError("O arquivo de entrada mudou desde o diagnóstico salvo.")
    oof_path = source / "oof_predictions.parquet"
    if sha256(oof_path) != calibration["source_oof_sha256"]:
        raise ValueError("As previsões OOF mudaram desde a calibração.")
    if parent["features"] != list(FEATURE_COLUMNS):
        raise ValueError("A lista de features mudou desde o ajuste do modelo.")
    if (calibration["window_hours"], calibration["min_history"]) != (168, 48):
        raise ValueError("O procedimento escolhido usa janela 168h e mínimo 48.")

    selection = pd.read_csv(calibration_dir / "summary.csv").set_index("method")
    mean, raw = selection.loc["hgb_mean"], selection.loc["hgb_raw"]
    if not (mean["mae"] <= raw["mae"] and mean["mean_absolute_fold_bias"] <= 2.0):
        raise ValueError("A correção pela média não passou a regra de desenvolvimento.")

    import joblib
    import mlflow
    import sklearn
    from renewable_forecast.modeling import _configure_mlflow

    if sklearn.__version__ != parent["versions"]["sklearn"]:
        raise ValueError("Use a mesma versão de scikit-learn do modelo salvo.")
    protocol = parent["protocol"]
    start = pd.Timestamp(protocol["holdout_start"])
    development = pd.read_parquet(source / "development_frame.parquet")
    if not (pd.to_datetime(development["target_available_at"]) < start).all():
        raise ValueError("O treino salvo contém rótulos indisponíveis no corte.")
    search = joblib.load(source / "search.joblib")
    model = search.best_estimator_
    series = pd.read_parquet(args.input)
    series["din_instante"] = pd.to_datetime(series["din_instante"], errors="raise")
    seed_oof = pd.read_parquet(oof_path)

    _configure_mlflow("renewable-h6-holdout")
    with mlflow.start_run(run_name="frozen-hgb-with-causal-mean") as run:
        output = source / "holdout" / run.info.run_id
        output.mkdir(parents=True, exist_ok=False)
        frozen = {
            "run_id": run.info.run_id, "source_run_id": parent["run_id"],
            "calibration_run_id": calibration["run_id"],
            "selected_method": "hgb_mean", "source_protocol": protocol,
            "window_hours": 168, "min_history": 48,
            "calibration_update": "each_origin_using_available_original_residuals",
            "window_bounds": "[forecast_origin-168h, forecast_origin)",
            "warmup_offset": 0.0, "prediction_floor": 0.0,
            "initial_state": "OOF residuals available before holdout_start",
            "model_retrained": False, "features": list(FEATURE_COLUMNS),
            "best_params": parent["best_params"],
            "input_sha256": parent["input_sha256"],
            "model_source_sha256": sha256(source / "search.joblib"),
            "source_oof_sha256": calibration["source_oof_sha256"],
            "holdout_definition": "forecast_origin >= saved holdout_start; observed target required",
            "evaluation_scope": "holdout_with_predeclared_online_calibration",
            "period_checks": "mae <= raw; mae <= 1.02*persistence; absolute_period_bias <= 2",
            "weekly_metrics": "diagnostics, not a new selection rule",
            "production_approved": False,
        }
        # Este registro é escrito ANTES de calcular as métricas do holdout.
        (output / "frozen_protocol.json").write_text(
            json.dumps(frozen, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Run: {run.info.run_id}", flush=True)
        print(f"Período reservado desde: {start}", flush=True)
        print("Carregando HGB já ajustado; correção causal pela média.", flush=True)
        predictions, seed = evaluate_frozen_holdout(
            model, series, seed_oof, holdout_start=start,
            horizon_hours=protocol["horizon_hours"],
            availability_delay_hours=protocol["availability_delay_hours"],
            window_hours=168, min_history=48,
        )
        predictions, summary, weeks = summarize_holdout(predictions, holdout_start=start)
        last_observed = series["din_instante"].max()
        origins = series.loc[series["din_instante"] >= start, "din_instante"]
        tail = int((origins + pd.Timedelta(hours=protocol["horizon_hours"]) > last_observed).sum())
        chosen = summary.loc[summary["method"].eq("hgb_mean")].iloc[0]
        checks_passed = bool(chosen[[
            "mae_not_worse_than_raw", "mae_limit_passed", "bias_limit_passed"
        ]].all())
        metadata = {
            **frozen, "holdout_evaluated": True, "holdout_rows": len(predictions),
            "first_origin": str(predictions["forecast_origin"].min()),
            "last_origin": str(predictions["forecast_origin"].max()),
            "last_target": str(predictions["target_time"].max()),
            "tail_origins_without_observed_target": tail,
            "other_origins_without_complete_features_or_target": len(origins) - tail - len(predictions),
            "seed_rows": len(seed),
            "active_corrections": int(predictions["calibration_active"].sum()),
            "selected_method_period_checks_passed": checks_passed,
            "versions": {"pandas": pd.__version__, "sklearn": sklearn.__version__},
        }
        predictions.to_parquet(output / "predictions.parquet", index=False)
        seed.to_parquet(output / "initial_calibration_seed.parquet", index=False)
        summary.to_csv(output / "summary.csv", index=False)
        weeks.to_csv(output / "weekly_metrics.csv", index=False)
        (output / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        joblib.dump(model, output / "model.joblib")
        mlflow.set_tags({"source_run_id": parent["run_id"], "calibration_run_id": calibration["run_id"]})
        mlflow.log_params({
            "selected_method": "hgb_mean", "horizon_hours": protocol["horizon_hours"],
            "availability_delay_hours": protocol["availability_delay_hours"],
            "window_hours": 168, "min_history": 48, "holdout_start": str(start),
        })
        for row in summary.to_dict("records"):
            for metric in ("mae", "rmse", "signed_bias", "absolute_bias", "ramp_mae"):
                mlflow.log_metric(f"{row['method']}_{metric}", row[metric])
        mlflow.log_artifacts(str(output), artifact_path="frozen_holdout")
        print(f"\nEmissões avaliadas: {len(predictions)}; finais sem alvo observado: {tail}")
        print("Resumo do período reservado:")
        print(summary.round(3).to_string(index=False))
        print("\nDiagnóstico semanal do método escolhido:")
        print(weeks.loc[weeks["method"].eq("hgb_mean")].round(3).to_string(index=False))
        print(f"\nMétodo escolhido atende aos três limites no período: {checks_passed}")
        print("Arquivos:", output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
