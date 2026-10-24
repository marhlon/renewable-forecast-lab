"""M05.1: quantis h24 em validação temporal, com baseline probabilístico.

Destino: src/renewable_forecast/weather_quantiles.py.
Reusa model_frame.csv e metadata.json. Não consulta fontes nem promove modelo.
"""
from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_pinball_loss
from threadpoolctl import threadpool_limits

from renewable_forecast.supervised import purged_time_series_splits
from renewable_forecast.weather_ablation import HGB_PARAMS, load_model_frame, sha256


RELEASE = "2026.10.02-quantiles-1"
QUANTILES = (0.1, 0.5, 0.9)
Q_COLUMNS = ("p10", "p50", "p90")
METHODS = ("persistence_residual_quantiles", "hgb_weather_quantiles")


def interval_score(y, lower, upper, alpha=0.2):
    """Largura mais penalização dos alvos fora do intervalo central 1-alpha."""
    return (
        upper - lower
        + (2 / alpha) * np.maximum(lower - y, 0.0)
        + (2 / alpha) * np.maximum(y - upper, 0.0)
    )


def probabilistic_metrics(part):
    """Métricas após piso zero e ordenação dos três quantis por emissão."""
    y = part["target_generation"].to_numpy(dtype=float)
    q = part[list(Q_COLUMNS)].to_numpy(dtype=float)
    lower, median, upper = q.T
    scores = {
        f"pinball_{name}": float(mean_pinball_loss(y, q[:, i], alpha=tau))
        for i, (tau, name) in enumerate(zip(QUANTILES, Q_COLUMNS))
    }
    return {
        "rows": len(part),
        "coverage_80": float(((y >= lower) & (y <= upper)).mean()),
        "below_p10_rate": float((y < lower).mean()),
        "above_p90_rate": float((y > upper).mean()),
        "mean_width_mwmed": float((upper - lower).mean()),
        "interval_score_80": float(interval_score(y, lower, upper).mean()),
        "mae_p50": float(np.abs(y - median).mean()),
        **scores,
        "mean_pinball": float(np.mean(list(scores.values()))),
        "raw_crossing_rate": float(part["raw_quantile_crossing"].mean()),
    }


def prediction_table(valid, raw, fold, method):
    """Preserva saídas originais e registra a correção de ordem sem usar y."""
    raw = np.asarray(raw, dtype=float)
    if raw.shape != (len(valid), 3) or not np.isfinite(raw).all():
        raise ValueError("O estimador deve produzir três quantis finitos por emissão.")
    part = valid[["forecast_origin", "target_time", "target_available_at", "target_generation"]].copy()
    part["fold"] = fold
    part["method"] = method
    part["persistence_prediction"] = valid["lag_1h"].to_numpy(dtype=float)
    part["raw_quantile_crossing"] = (np.diff(raw, axis=1) < 0).any(axis=1)
    # Modelos independentes podem cruzar. Esta regra é fixada antes da avaliação.
    # Ordenar produz limites coerentes; não garante cobertura ou calibração.
    ordered = np.sort(np.maximum(raw, 0.0), axis=1)
    for i, name in enumerate(Q_COLUMNS):
        part[f"raw_{name}"] = raw[:, i]
        part[name] = ordered[:, i]
    part["covered_80"] = part.target_generation.between(part.p10, part.p90)
    part["width_mwmed"] = part.p90 - part.p10
    return part


def evaluate_quantiles(frame, columns, *, n_splits=3, test_size_hours=168):
    parts, fold_plan, reference_offsets = [], [], []
    splits = purged_time_series_splits(frame, n_splits=n_splits, test_size=test_size_hours)
    for fold, (train_idx, valid_idx) in enumerate(splits, start=1):
        train, valid = frame.iloc[train_idx], frame.iloc[valid_idx]
        cutoff = valid.forecast_origin.min()
        latest = train.target_available_at.max()
        if latest >= cutoff or train.forecast_origin.max() >= cutoff:
            raise ValueError("Treino incompatível com o início da validação.")
        fold_plan.append({
            "fold": fold, "train_rows": len(train), "valid_rows": len(valid),
            "train_origin_start": train.forecast_origin.min(),
            "train_origin_end": train.forecast_origin.max(),
            "latest_train_label_available_at": latest,
            "valid_start": cutoff, "valid_end": valid.forecast_origin.max(),
        })
        print(f"Fold {fold}: treino={len(train)}; validação={len(valid)}; corte={cutoff}", flush=True)

        # Baseline: persistência acrescida dos quantis de seus erros passados.
        # Todos esses erros possuem alvo disponível antes do corte do fold.
        residuals = train.target_generation.to_numpy() - train.lag_1h.to_numpy()
        offsets = np.quantile(residuals, QUANTILES, method="linear")
        reference_offsets.append({"fold": fold, **dict(zip(Q_COLUMNS, offsets))})
        reference = valid.lag_1h.to_numpy()[:, None] + offsets[None, :]
        parts.append(prediction_table(valid, reference, fold, METHODS[0]))

        raw = []
        for tau in QUANTILES:
            params = {**HGB_PARAMS, "loss": "quantile", "quantile": tau}
            model = HistGradientBoostingRegressor(**params)
            model.fit(train[columns], train.target_generation)
            raw.append(model.predict(valid[columns]))
        parts.append(prediction_table(valid, np.column_stack(raw), fold, METHODS[1]))

    predictions = pd.concat(parts, ignore_index=True)
    fold_metrics = pd.DataFrame([
        {"fold": int(fold), "method": method, **probabilistic_metrics(part)}
        for (fold, method), part in predictions.groupby(["fold", "method"], sort=True)
    ])
    summary = pd.DataFrame([
        {"method": method, **probabilistic_metrics(predictions.loc[predictions.method.eq(method)])}
        for method in METHODS
    ])
    return predictions, fold_metrics, summary, pd.DataFrame(fold_plan), reference_offsets


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--n-splits", type=int, default=3)
    parser.add_argument("--test-size-hours", type=int, default=168)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args(argv)
    if args.n_splits < 2 or args.test_size_hours < 1 or args.threads < 1:
        parser.error("n-splits >= 2; test-size-hours e threads positivos.")
    frame, source = load_model_frame(args.input_dir)
    if source["horizon_hours"] != 24 or source["availability_delay_hours"] != 2:
        raise ValueError("Esta prática está definida para h24 e atraso assumido de 2h.")
    if args.output_dir.resolve() == args.input_dir.resolve():
        raise ValueError("Use uma pasta de resultados diferente da entrada.")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise ValueError("A pasta de saída já contém um experimento. Para nova execução, use outra pasta.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    protocol = {
        "release": RELEASE,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "exploratory_july_development; not independent final evaluation",
        "model_promotion": False,
        "source_frame_sha256": sha256(args.input_dir / "model_frame.csv"),
        "source_metadata_sha256": sha256(args.input_dir / "metadata.json"),
        "code_sha256": sha256(Path(__file__)),
        "source_dataset": source,
        "feature_columns": source["model_feature_columns"],
        "quantiles": QUANTILES, "nominal_interval_coverage": 0.8,
        "n_splits": args.n_splits, "test_size_hours": args.test_size_hours,
        "estimator_params_by_quantile": {
            str(tau): HistGradientBoostingRegressor(**{**HGB_PARAMS, "loss": "quantile", "quantile": tau}).get_params()
            for tau in QUANTILES
        },
        "parameter_origin": "previous exploratory h6 settings; only loss and quantile changed; no tuning",
        "training_rule": "expanding origin; target_available_at strictly before first validation origin",
        "forecast_schedule": "weights and residual quantiles frozen within fold; features available at each origin",
        "reference": "lag_1h + empirical quantiles(y_train-lag_1h_train); method=linear",
        "postprocessing": "floor zero, then sort three quantiles per row; raw values preserved",
        "calibration": "no additional calibration; nominal 80 percent is an objective, not a guarantee",
        "metric_aggregation": "pooled rows per method; separate metrics by fold",
        "threads": args.threads,
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "sklearn": sklearn.__version__},
    }
    protocol_path = args.output_dir / "protocol.json"
    protocol_path.write_text(json.dumps(protocol, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(f"P10/P50/P90: {3 * args.n_splits} ajustes HGB; baseline de resíduos nos mesmos cortes.", flush=True)
    with threadpool_limits(limits=args.threads):
        predictions, folds, summary, plan, offsets = evaluate_quantiles(
            frame, source["model_feature_columns"],
            n_splits=args.n_splits, test_size_hours=args.test_size_hours,
        )
    outputs = {"predictions.csv": predictions, "fold_metrics.csv": folds, "summary.csv": summary, "folds.csv": plan}
    for name, table in outputs.items():
        table.to_csv(args.output_dir / name, index=False)
    metadata = {
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_rows": len(frame), "validation_origins": int(predictions.forecast_origin.nunique()),
        "prediction_rows": len(predictions), "methods": METHODS,
        "baseline_offsets_by_fold": offsets,
        "protocol_sha256": sha256(protocol_path),
        "output_sha256": {name: sha256(args.output_dir / name) for name in outputs},
        "model_promotion": False,
    }
    (args.output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    display = ["method", "rows", "coverage_80", "mean_width_mwmed", "interval_score_80", "mean_pinball", "mae_p50", "raw_crossing_rate"]
    print("\nResumo (menor pinball e interval score é melhor; cobertura nominal=0,80):")
    print(summary[display].round(4).to_string(index=False))
    print("\nCobertura por fold:")
    print(folds.pivot(index="fold", columns="method", values="coverage_80").round(4).to_string())
    print(f"\nArquivos: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
