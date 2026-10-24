"""Diagnóstico por fold e registro do experimento h+6.

Instalar em src/renewable_forecast/horizon_diagnostics.py.
Recebe a busca criada por fit_horizon_search; o holdout não é avaliado aqui.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone

from renewable_forecast.features import FEATURE_COLUMNS


def evaluate_selected_folds(search, frame: pd.DataFrame):
    """Reconstrói previsões fora do treino para os parâmetros selecionados.

    Os hiperparâmetros já foram escolhidos usando estes folds. Portanto estas
    previsões são diagnósticos do desenvolvimento, não uma avaliação final.
    Viés = média(observado - previsto): positivo indica subprevisão.
    """
    prediction_parts = []
    metrics = []

    for fold, (train_idx, valid_idx) in enumerate(search.cv, start=1):
        train = frame.iloc[train_idx]
        valid = frame.iloc[valid_idx]
        latest_label = train["target_available_at"].max()
        first_origin = valid["forecast_origin"].min()
        if not latest_label < first_origin:
            raise ValueError("Fold contém rótulos indisponíveis no corte.")

        # clone conserva os hiperparâmetros, mas descarta o ajuste anterior.
        model = clone(search.best_estimator_)
        model.fit(train[FEATURE_COLUMNS], train["target_generation"])
        prediction = np.maximum(model.predict(valid[FEATURE_COLUMNS]), 0.0)

        target = valid["target_generation"].to_numpy()
        persistence = valid["lag_1h"].to_numpy()
        residual = target - prediction
        mae = float(np.abs(residual).mean())
        baseline_mae = float(np.abs(target - persistence).mean())
        bias = float(residual.mean())
        ramp = np.abs(target - persistence)
        ramp_mask = ramp >= np.quantile(ramp, 0.90)

        metrics.append({
            "fold": fold,
            "train_rows": len(train),
            "valid_rows": len(valid),
            "valid_start": first_origin,
            "valid_end": valid["forecast_origin"].max(),
            "latest_train_label_available_at": latest_label,
            "mae": mae,
            "persistence_mae": baseline_mae,
            "mae_gain_pct": (
                100 * (1 - mae / baseline_mae)
                if baseline_mae > 0 else np.nan
            ),
            "rmse": float(np.sqrt(np.square(residual).mean())),
            "signed_bias": bias,
            "absolute_bias": abs(bias),
            "ramp_mae": float(np.abs(residual[ramp_mask]).mean()),
        })

        part = valid[[
            "forecast_origin", "target_time", "target_available_at",
            "history_end", "target_generation",
        ]].copy()
        part["fold"] = fold
        part["prediction"] = prediction
        part["persistence_prediction"] = persistence
        part["residual"] = residual
        prediction_parts.append(part)

    predictions = pd.concat(prediction_parts, ignore_index=True)
    return predictions, pd.DataFrame(metrics)


def candidate_metrics(search) -> pd.DataFrame:
    """Exibe os critérios já utilizados por constrained_refit."""
    results = search.cv_results_
    table = pd.DataFrame({
        "candidate": np.arange(len(results["params"])),
        "mae": -results["mean_test_neg_mae"],
        "persistence_mae": -results["mean_test_neg_persistence_mae"],
        "mean_absolute_bias": -results["mean_test_neg_absolute_bias"],
        "rmse": -results["mean_test_neg_rmse"],
        "ramp_mae": -results["mean_test_neg_ramp_mae"],
        "params": [json.dumps(p, sort_keys=True) for p in results["params"]],
    })
    table["mae_gate"] = table["mae"] <= 1.02 * table["persistence_mae"]
    table["bias_gate"] = table["mean_absolute_bias"] <= 2.0
    table["eligible"] = table["mae_gate"] & table["bias_gate"]
    table["selected"] = table["candidate"] == search.best_index_
    return table


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--experiment", default="renewable-h6-diagnostics")
    parser.add_argument("--horizon-hours", type=int, required=True)
    parser.add_argument("--availability-delay-hours", type=int, required=True)
    parser.add_argument("--holdout-days", type=int, default=28)
    args = parser.parse_args(argv)
    if args.horizon_hours <= 0 or args.holdout_days <= 0:
        parser.error("Horizonte e duração do holdout devem ser positivos.")
    if args.availability_delay_hours < 0:
        parser.error("O atraso não pode ser negativo.")

    import joblib
    import mlflow
    import sklearn
    from renewable_forecast.modeling import (
        _configure_mlflow,
        _validation_metrics,
        fit_horizon_search,
    )

    series = pd.read_parquet(args.input)
    series["din_instante"] = pd.to_datetime(series["din_instante"], errors="raise")
    if series["din_instante"].isna().any():
        raise ValueError("Há timestamps ausentes na série de entrada.")
    holdout_start = (
        series["din_instante"].max() + pd.Timedelta(hours=1)
        - pd.Timedelta(days=args.holdout_days)
    )
    available_at = (
        series["din_instante"]
        + pd.Timedelta(hours=args.availability_delay_hours)
    )
    development = series.loc[available_at < holdout_start].copy()

    _configure_mlflow(args.experiment)
    with mlflow.start_run(run_name="horizon-search-and-fold-diagnostics") as run:
        output = args.output_dir / run.info.run_id
        output.mkdir(parents=True, exist_ok=False)
        protocol = {
            "horizon_hours": args.horizon_hours,
            "availability_delay_hours": args.availability_delay_hours,
            "availability_is_assumed": True,
            "holdout_start": str(holdout_start),
            "holdout_days": args.holdout_days,
            "cv_splits": 5,
            "cv_test_rows": 672,
            "cv_label_boundary": "strictly_before_validation_origin",
            "early_stopping": False,
            "mae_constraint_ratio": 1.02,
            "absolute_bias_constraint": 2.0,
        }
        mlflow.log_params(protocol)
        print(f"Run: {run.info.run_id}", flush=True)
        print(f"Holdout reservado desde: {holdout_start}", flush=True)
        print("Busca de hiperparâmetros em andamento...", flush=True)
        search, frame = fit_horizon_search(
            development,
            horizon_hours=args.horizon_hours,
            availability_delay_hours=args.availability_delay_hours,
        )
        if not (frame["target_available_at"] < holdout_start).all():
            raise ValueError("O desenvolvimento alcançou o período reservado.")

        # Salva a busca antes do diagnóstico para preservar o trabalho caro.
        joblib.dump(search, output / "search.joblib")
        frame.to_parquet(output / "development_frame.parquet", index=False)
        pd.DataFrame(search.cv_results_).to_csv(output / "cv_results.csv", index=False)
        candidates = candidate_metrics(search)
        candidates.to_csv(output / "candidate_metrics.csv", index=False)
        metrics = _validation_metrics(search)
        (output / "validation_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
        metadata = {
            "run_id": run.info.run_id,
            "protocol": protocol,
            "input_path": str(args.input.resolve()),
            "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
            "development_rows": len(frame),
            "features": FEATURE_COLUMNS,
            "best_params": search.best_params_,
            "estimator_params": search.best_estimator_.get_params(),
            "selection_approved": bool(metrics["selection_approved"]),
            "evaluation_scope": "development_cv_after_hyperparameter_selection",
            "holdout_evaluated": False,
            "bias_convention": "observed_minus_predicted",
            "prediction_floor": 0.0,
            "versions": {
                "python": platform.python_version(),
                "pandas": pd.__version__,
                "sklearn": sklearn.__version__,
                "mlflow": mlflow.__version__,
            },
        }
        (output / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        print("Reconstruindo previsões fora do treino nos cinco folds...", flush=True)
        predictions, folds = evaluate_selected_folds(search, frame)
        predictions.to_parquet(output / "oof_predictions.parquet", index=False)
        folds.to_csv(output / "fold_metrics.csv", index=False)
        mlflow.log_params({f"best_{k}": v for k, v in search.best_params_.items()})
        mlflow.log_metrics(metrics)
        mlflow.log_metric("oof_signed_bias", float(predictions["residual"].mean()))
        mlflow.log_artifacts(str(output), artifact_path="horizon_diagnostics")

        print("\nCandidatos:")
        print(candidates.drop(columns="params").round(3).to_string(index=False))
        print("\nDiagnóstico do candidato selecionado por fold:")
        print(folds[[
            "fold", "valid_start", "mae", "persistence_mae",
            "mae_gain_pct", "signed_bias", "absolute_bias",
        ]].round(3).to_string(index=False))
        print("\nMédia dos vieses absolutos dos folds:", folds["absolute_bias"].mean())
        print("Viés com sinal das previsões OOF:", predictions["residual"].mean())
        print("Seleção aprovada pelos critérios atuais:", bool(metrics["selection_approved"]))
        print("Arquivos do experimento:", output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
