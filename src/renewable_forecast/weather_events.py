"""M05.3: probabilidade de queda da geração h24 frente ao último dado disponível.

Destino: src/renewable_forecast/weather_events.py.
Compara frequência histórica, regressão logística e HGB classificador.
As probabilidades são avaliadas, sem recalibração adicional ou promoção.
"""
from __future__ import annotations

import argparse
import json
import platform
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from renewable_forecast.supervised import purged_time_series_splits
from renewable_forecast.weather_ablation import HGB_PARAMS, load_model_frame, sha256


RELEASE = "2026.10.03-events-1"
METHODS = ("historical_frequency", "logistic_weather", "hgb_weather_classifier")
CLASSIFIER_PARAMS = {**HGB_PARAMS, "loss": "log_loss"}
LOGISTIC_PARAMS = {"C": 1.0, "solver": "lbfgs", "max_iter": 2000, "class_weight": None}
LABEL_COLUMNS = (
    "forecast_origin", "history_end", "target_time", "target_available_at",
    "last_available_generation", "target_generation", "generation_drop_mwmed",
    "drop_threshold_mwmed", "event_drop",
)


def build_event_labels(frame, drop_mw=22.77):
    """Queda >= drop_mw entre y(t-2), já disponível, e y(t+24), alvo futuro."""
    if isinstance(drop_mw, (bool, np.bool_)) or not np.isfinite(drop_mw) or drop_mw <= 0:
        raise ValueError("drop_mw deve ser finito e estritamente positivo.")
    values = frame[["lag_1h", "target_generation"]].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Geração de referência e alvo devem ser finitos.")
    labels = frame[["forecast_origin", "history_end", "target_time", "target_available_at", "target_generation"]].copy()
    labels["last_available_generation"] = frame.lag_1h.to_numpy(dtype=float)
    labels["generation_drop_mwmed"] = values[:, 0] - values[:, 1]
    labels["drop_threshold_mwmed"] = float(drop_mw)
    labels["event_drop"] = (labels.generation_drop_mwmed >= drop_mw).astype("int64")
    return labels[list(LABEL_COLUMNS)]


def fit_probability_models(train, y_train, valid, columns):
    """Ajusta o scaler somente no treino; probabilidades da classe evento=1."""
    if set(np.unique(y_train)) != {0, 1}:
        raise ValueError("Os dois eventos (0/1) devem ocorrer no treino deste piloto.")
    estimators = {
        "logistic_weather": Pipeline([
            ("scale", StandardScaler()),
            ("classifier", LogisticRegression(**LOGISTIC_PARAMS)),
        ]),
        "hgb_weather_classifier": HistGradientBoostingClassifier(**CLASSIFIER_PARAMS),
    }
    probabilities = {"historical_frequency": np.full(len(valid), float(np.mean(y_train)))}
    for method, estimator in estimators.items():
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            estimator.fit(train[columns], y_train)
        positive_index = list(estimator.classes_).index(1)
        probabilities[method] = estimator.predict_proba(valid[columns])[:, positive_index]
    return probabilities, estimators


def classification_metrics(part, alarm_threshold):
    y = part.event_drop.to_numpy(dtype=int)
    p = part.p_event.to_numpy(dtype=float)
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Probabilidades devem ser finitas e estar entre 0 e 1.")
    alarm = p >= alarm_threshold
    tp = int(((y == 1) & alarm).sum())
    fp = int(((y == 0) & alarm).sum())
    fn = int(((y == 1) & ~alarm).sum())
    tn = int(((y == 0) & ~alarm).sum())
    return {
        "rows": len(y), "events": int(y.sum()), "event_rate": float(y.mean()),
        "brier": float(np.square(p - y).mean()),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "average_precision": float(average_precision_score(y, p)) if y.sum() > 0 else np.nan,
        "alarm_threshold": float(alarm_threshold),
        "alarms": tp + fp, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": tp / (tp + fp) if tp + fp else np.nan,
        "recall": tp / (tp + fn) if tp + fn else np.nan,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else np.nan,
    }


def probability_bins(predictions):
    """Bins fixos [0,.2), ... [.8,1]; tabela descritiva, sem ajuste de p."""
    rows = []
    for method, all_rows in predictions.groupby("method", sort=True):
        scopes = [("pooled", 0, all_rows)] + [
            ("fold", int(fold), part) for fold, part in all_rows.groupby("fold", sort=True)
        ]
        for scope, fold, part in scopes:
            bin_index = np.minimum((part.p_event.to_numpy() * 5).astype(int), 4)
            for index in range(5):
                selected = part.iloc[np.flatnonzero(bin_index == index)]
                average_probability = float(selected.p_event.mean()) if len(selected) else np.nan
                observed_rate = float(selected.event_drop.mean()) if len(selected) else np.nan
                rows.append({
                    "scope": scope, "fold": fold, "method": method,
                    "bin_left": index / 5, "bin_right": (index + 1) / 5,
                    "right_inclusive": index == 4, "rows": len(selected),
                    "mean_probability": average_probability,
                    "observed_event_rate": observed_rate,
                    "observed_minus_predicted": observed_rate - average_probability,
                })
    return pd.DataFrame(rows)


def evaluate_events(frame, columns, *, drop_mw=22.77, alarm_threshold=0.5, n_splits=3, test_size_hours=168):
    if not np.isfinite(alarm_threshold) or not 0 < alarm_threshold < 1:
        raise ValueError("alarm_threshold deve estar entre 0 e 1.")
    forbidden = {"target_generation", "generation_drop_mwmed", "event_drop", "target_available_at"}
    if set(columns) & forbidden:
        raise ValueError("Alvo ou metadado futuro não pode entrar como feature.")
    labels = build_event_labels(frame, drop_mw)
    predictions, fold_plan = [], []
    for fold, (train_idx, valid_idx) in enumerate(
        purged_time_series_splits(frame, n_splits=n_splits, test_size=test_size_hours), start=1
    ):
        train, valid = frame.iloc[train_idx], frame.iloc[valid_idx]
        y_train = labels.iloc[train_idx].event_drop.to_numpy()
        cutoff = valid.forecast_origin.min()
        if train.target_available_at.max() >= cutoff:
            raise ValueError("Um rótulo de treino está indisponível no corte.")
        probabilities, _ = fit_probability_models(train, y_train, valid, columns)
        fold_plan.append({
            "fold": fold, "train_rows": len(train), "valid_rows": len(valid),
            "train_events": int(y_train.sum()), "train_event_rate": float(y_train.mean()),
            "valid_events": int(labels.iloc[valid_idx].event_drop.sum()),
            "train_origin_start": train.forecast_origin.min(),
            "train_origin_end": train.forecast_origin.max(),
            "latest_train_label_available_at": train.target_available_at.max(),
            "valid_start": cutoff, "valid_end": valid.forecast_origin.max(),
        })
        print(
            f"Fold {fold}: treino={len(train)}; eventos treino={y_train.sum()}; "
            f"avaliação={len(valid)}; corte={cutoff}", flush=True,
        )
        for method in METHODS:
            part = labels.iloc[valid_idx].copy()
            part["fold"], part["method"] = fold, method
            part["p_event"] = probabilities[method]
            part["alarm_threshold"] = float(alarm_threshold)
            part["alarm"] = (part.p_event >= alarm_threshold).astype("int64")
            predictions.append(part)
    predictions = pd.concat(predictions, ignore_index=True)
    fold_metrics = pd.DataFrame([
        {"fold": int(fold), "method": method, **classification_metrics(part, alarm_threshold)}
        for (fold, method), part in predictions.groupby(["fold", "method"], sort=True)
    ])
    summary = pd.DataFrame([
        {"method": method, **classification_metrics(predictions.loc[predictions.method.eq(method)], alarm_threshold)}
        for method in METHODS
    ]).rename(columns={"average_precision": "pooled_average_precision"})
    for method in METHODS:
        mask = summary.method.eq(method)
        per_fold = fold_metrics.loc[fold_metrics.method.eq(method)]
        summary.loc[mask, "mean_fold_average_precision"] = per_fold.average_precision.mean()
        summary.loc[mask, "folds_with_defined_ap"] = per_fold.average_precision.notna().sum()
    reference_brier = float(summary.loc[summary.method.eq(METHODS[0]), "brier"].iloc[0])
    summary["brier_skill_vs_frequency"] = 1 - summary.brier / reference_brier if reference_brier > 0 else np.nan
    reference_by_fold = fold_metrics.loc[fold_metrics.method.eq(METHODS[0])].set_index("fold").brier
    reference = fold_metrics.fold.map(reference_by_fold)
    fold_metrics["brier_skill_vs_frequency"] = 1 - fold_metrics.brier / reference.replace(0, np.nan)
    return {
        "event_labels.csv": labels, "predictions.csv": predictions,
        "folds.csv": pd.DataFrame(fold_plan), "fold_metrics.csv": fold_metrics,
        "summary.csv": summary, "probability_bins.csv": probability_bins(predictions),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--drop-mw", type=float, default=22.77)
    parser.add_argument("--alarm-threshold", type=float, default=0.5)
    parser.add_argument("--n-splits", type=int, default=3)
    parser.add_argument("--test-size-hours", type=int, default=168)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args(argv)
    if args.n_splits < 2 or min(args.test_size_hours, args.threads) < 1:
        parser.error("n-splits >= 2; test-size-hours e threads positivos.")
    if not np.isfinite(args.alarm_threshold) or not 0 < args.alarm_threshold < 1:
        parser.error("alarm-threshold deve estar estritamente entre 0 e 1.")
    frame, source = load_model_frame(args.input_dir)
    if source["horizon_hours"] != 24 or source["availability_delay_hours"] != 2:
        raise ValueError("Esta prática exige h24 e atraso assumido de duas horas.")
    build_event_labels(frame, args.drop_mw)
    if args.input_dir.resolve() == args.output_dir.resolve():
        raise ValueError("Use saída diferente da entrada.")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise ValueError("A saída já contém um experimento. Preserve-a e escolha outra pasta para nova execução.")
    splits = list(purged_time_series_splits(frame, n_splits=args.n_splits, test_size=args.test_size_hours))
    if not splits:
        raise ValueError("Nenhum fold disponível.")
    protocol = {
        "release": RELEASE, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "exploratory July development; no independent holdout; no operational alert approval",
        "source_frame_sha256": sha256(args.input_dir / "model_frame.csv"),
        "source_metadata_sha256": sha256(args.input_dir / "metadata.json"),
        "source_dataset": source, "code_sha256": sha256(Path(__file__)),
        "feature_columns": source["model_feature_columns"], "methods": METHODS,
        "event_definition": "1 if lag_1h - target_generation >= drop_mw else 0",
        "event_semantics": "endpoint at t+24 versus last available observation at t-2; not hourly ramp nor any fall within next 24 hours",
        "event_label_available_at": "target_available_at; endpoint value arrives at t+26 under assumed delay",
        "drop_mw": args.drop_mw,
        "threshold_rationale": "default22.77 is a fixed development hypothesis, 10% of current registry reference227.7MW; not proof of historical capacity or operational relevance",
        "alarm_threshold": args.alarm_threshold,
        "alarm_rationale": "fixed0.5 by default for comparison; no costs supplied; not tuned on evaluation",
        "baseline": "fraction of positive labels in eligible training only; frozen within fold",
        "classifier_params": CLASSIFIER_PARAMS, "logistic_params": LOGISTIC_PARAMS,
        "scaling": "StandardScaler fit within each training fold in logistic Pipeline only",
        "class_reweighting": False, "resampling": False, "additional_probability_calibration": False,
        "parameter_origin": "HGB structural parameters from prior exploratory work; logistic C1 fixed; no search",
        "training_rule": "target_available_at strictly before first validation origin; frozen estimators within fold",
        "n_splits": args.n_splits, "test_size_hours": args.test_size_hours, "threads": args.threads,
        "metric_notes": "Brier mean((p-y)^2); average_precision is sklearn AP, not trapezoidal PR area; summary separates pooled AP and mean fold AP; undefined precision/recall stored as empty CSV values",
        "probability_bins": "fixed five bins over [0,1]; fold and pooled descriptive diagnostics, not probability recalibration",
        "model_promotion": False,
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "sklearn": sklearn.__version__},
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    protocol_path = args.output_dir / "protocol.json"
    protocol_path.write_text(json.dumps(protocol, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(f"Evento: queda >= {args.drop_mw} MWmed frente ao último dado disponível. Alarme se p >= {args.alarm_threshold}.")
    with threadpool_limits(limits=args.threads):
        tables = evaluate_events(
            frame, source["model_feature_columns"], drop_mw=args.drop_mw,
            alarm_threshold=args.alarm_threshold, n_splits=args.n_splits, test_size_hours=args.test_size_hours,
        )
    for name, table in tables.items():
        table.to_csv(args.output_dir / name, index=False)
    metadata = {
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_rows": len(frame), "validation_origins": int(tables["predictions.csv"].forecast_origin.nunique()),
        "prediction_rows": len(tables["predictions.csv"]), "model_promotion": False,
        "protocol_sha256": sha256(protocol_path),
        "output_sha256": {name: sha256(args.output_dir / name) for name in tables},
    }
    (args.output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    display = ["method", "rows", "events", "brier", "brier_skill_vs_frequency", "mean_fold_average_precision", "precision", "recall", "fp", "fn"]
    print("\nResumo: Brier menor é melhor; AP, precision e recall maiores são melhores dentro do mesmo protocolo.")
    print(tables["summary.csv"][display].round(4).to_string(index=False))
    print("\nBrier por fold:")
    print(tables["fold_metrics.csv"].pivot(index="fold", columns="method", values="brier").round(4).to_string())
    print("\nProbabilidade estimada não implica calibração comprovada; limiar de alarme ainda não é operacional.")
    print(f"Arquivos: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
