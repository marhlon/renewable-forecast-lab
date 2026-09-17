from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


COLUMN_ALIASES = {
    "fold": ("fold", "fold_id"),
    "model": ("model", "modelo"),
    "timestamp": ("timestamp", "din_instante", "datetime", "date"),
    "actual": ("actual", "y_true", "val_geracao", "observed"),
    "prediction": ("prediction", "y_pred", "pred", "forecast"),
    "is_ramp": ("is_ramp", "ramp", "ramp_flag", "is_ramp_event"),
}


def _find_column(
    columns: Iterable[str],
    canonical_name: str,
    *,
    required: bool = True,
) -> str | None:
    available = set(columns)
    for alias in COLUMN_ALIASES[canonical_name]:
        if alias in available:
            return alias

    if required:
        raise ValueError(
            f"Coluna obrigatória '{canonical_name}' não encontrada. "
            f"Alternativas aceitas: {COLUMN_ALIASES[canonical_name]}. "
            f"Colunas recebidas: {sorted(available)}"
        )
    return None


def _as_boolean(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    if pd.api.types.is_numeric_dtype(series):
        return series.fillna(0).ne(0)
    normalized = series.astype("string").str.strip().str.lower()
    return normalized.isin({"1", "true", "t", "yes", "y", "sim", "s"})


def normalize_predictions(
    predictions: pd.DataFrame,
    *,
    ramp_threshold: float = 30.0,
) -> pd.DataFrame:
    rename_map: dict[str, str] = {}
    for canonical in ("fold", "model", "timestamp", "actual", "prediction"):
        source = _find_column(predictions.columns, canonical)
        if source != canonical:
            rename_map[source] = canonical

    ramp_source = _find_column(
        predictions.columns,
        "is_ramp",
        required=False,
    )
    if ramp_source is not None and ramp_source != "is_ramp":
        rename_map[ramp_source] = "is_ramp"

    normalized = predictions.rename(columns=rename_map).copy()
    normalized["timestamp"] = pd.to_datetime(
        normalized["timestamp"],
        errors="raise",
    )
    normalized["actual"] = pd.to_numeric(normalized["actual"], errors="raise")
    normalized["prediction"] = pd.to_numeric(
        normalized["prediction"],
        errors="raise",
    )

    required = ["fold", "model", "timestamp", "actual", "prediction"]
    if normalized[required].isna().any().any():
        missing = normalized[required].isna().sum()
        raise ValueError(
            "Há valores ausentes em colunas obrigatórias: "
            f"{missing[missing.gt(0)].to_dict()}"
        )

    if "is_ramp" in normalized.columns:
        normalized["is_ramp"] = _as_boolean(normalized["is_ramp"])
    else:
        actual_by_time = (
            normalized[["fold", "timestamp", "actual"]]
            .drop_duplicates(["fold", "timestamp"])
            .sort_values(["fold", "timestamp"])
        )
        actual_by_time["is_ramp"] = (
            actual_by_time.groupby("fold", sort=False)["actual"]
            .diff()
            .abs()
            .ge(ramp_threshold)
        )
        normalized = normalized.merge(
            actual_by_time[["fold", "timestamp", "is_ramp"]],
            on=["fold", "timestamp"],
            how="left",
            validate="many_to_one",
        )
        normalized["is_ramp"] = normalized["is_ramp"].fillna(False)

    return normalized.sort_values(
        ["timestamp", "fold", "model"],
    ).reset_index(drop=True)


def apply_prequential_calibration(
    predictions: pd.DataFrame,
    *,
    candidate_model: str = "hist_gradient_boosting",
    baseline_model: str = "persistence_1h",
    history_window: int = 672,
    min_history: int = 168,
    ramp_threshold: float = 30.0,
) -> pd.DataFrame:
    if history_window < 1:
        raise ValueError("history_window deve ser maior que zero.")
    if min_history < 1:
        raise ValueError("min_history deve ser maior que zero.")
    if min_history > history_window:
        raise ValueError(
            "min_history não pode ser maior que history_window."
        )

    normalized = normalize_predictions(
        predictions,
        ramp_threshold=ramp_threshold,
    )

    selected = normalized[
        normalized["model"].isin([candidate_model, baseline_model])
    ].copy()
    present_models = set(selected["model"].unique())
    missing_models = {candidate_model, baseline_model} - present_models
    if missing_models:
        raise ValueError(
            f"Modelos ausentes nas previsões: {sorted(missing_models)}"
        )

    candidate = selected[selected["model"].eq(candidate_model)].copy()
    fold_order = (
        candidate.groupby("fold", as_index=False)["timestamp"]
        .min()
        .sort_values("timestamp")["fold"]
        .tolist()
    )

    calibrated_parts: list[pd.DataFrame] = []
    historical_residuals: list[float] = []

    for fold in fold_order:
        fold_rows = candidate[candidate["fold"].eq(fold)].copy()
        history = np.asarray(
            historical_residuals[-history_window:],
            dtype=float,
        )

        if history.size >= min_history:
            mean_offset = float(history.mean())
            median_offset = float(np.median(history))
        else:
            mean_offset = 0.0
            median_offset = 0.0

        for method, offset in (
            ("mean", mean_offset),
            ("median", median_offset),
        ):
            calibrated = fold_rows.copy()
            calibrated["model"] = f"{candidate_model}_calibrated_{method}"
            calibrated["prediction"] = (
                calibrated["prediction"] + offset
            ).clip(lower=0.0)
            calibrated["calibration_method"] = method
            calibrated["calibration_offset"] = offset
            calibrated["calibration_history_size"] = int(history.size)
            calibrated_parts.append(calibrated)

        fold_residuals = (
            fold_rows["actual"] - fold_rows["prediction"]
        ).astype(float)
        historical_residuals.extend(fold_residuals.tolist())

    selected["calibration_method"] = "none"
    selected["calibration_offset"] = 0.0
    selected["calibration_history_size"] = 0

    result = pd.concat(
        [selected, *calibrated_parts],
        ignore_index=True,
    )
    result["error"] = result["actual"] - result["prediction"]
    result["absolute_error"] = result["error"].abs()
    return result.sort_values(
        ["timestamp", "fold", "model"],
    ).reset_index(drop=True)


def _metric_record(group: pd.DataFrame) -> dict[str, float | int]:
    error = group["actual"] - group["prediction"]
    absolute_error = error.abs()
    ramp_error = absolute_error[group["is_ramp"]]
    return {
        "observations": int(len(group)),
        "mae": float(absolute_error.mean()),
        "rmse": float(np.sqrt(np.mean(np.square(error)))),
        "bias": float(error.mean()),
        "maximum_error": float(absolute_error.max()),
        "ramp_observations": int(group["is_ramp"].sum()),
        "ramp_mae": (
            float(ramp_error.mean()) if not ramp_error.empty else float("nan")
        ),
    }


def summarize_calibration(
    predictions: pd.DataFrame,
    *,
    baseline_model: str = "persistence_1h",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fold_records: list[dict[str, object]] = []
    for (fold, model), group in predictions.groupby(
        ["fold", "model"],
        sort=False,
    ):
        fold_records.append(
            {"fold": fold, "model": model, **_metric_record(group)}
        )
    fold_metrics = pd.DataFrame(fold_records)

    summary_records: list[dict[str, object]] = []
    for model, group in predictions.groupby("model", sort=False):
        summary_records.append(
            {
                "model": model,
                "folds": int(group["fold"].nunique()),
                **_metric_record(group),
            }
        )
    summary = pd.DataFrame(summary_records)

    baseline_rows = summary[summary["model"].eq(baseline_model)]
    if baseline_rows.empty:
        raise ValueError(f"Baseline '{baseline_model}' ausente do resumo.")
    baseline_mae = float(baseline_rows.iloc[0]["mae"])
    summary["mae_improvement_vs_persistence_pct"] = (
        (baseline_mae - summary["mae"]) / baseline_mae * 100.0
    )

    return (
        fold_metrics.sort_values(["fold", "model"]).reset_index(drop=True),
        summary.sort_values("mae").reset_index(drop=True),
    )


def run_calibration(
    *,
    backtest_dir: Path,
    output_dir: Path,
    candidate_model: str = "hist_gradient_boosting",
    baseline_model: str = "persistence_1h",
    history_window: int = 672,
    min_history: int = 168,
    ramp_threshold: float = 30.0,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    parquet_path = backtest_dir / "predictions.parquet"
    csv_path = backtest_dir / "predictions.csv"
    if parquet_path.exists():
        raw_predictions = pd.read_parquet(parquet_path)
        input_path = parquet_path
    elif csv_path.exists():
        raw_predictions = pd.read_csv(csv_path)
        input_path = csv_path
    else:
        raise FileNotFoundError(
            f"Nenhum arquivo de previsões encontrado em {backtest_dir}."
        )

    calibrated = apply_prequential_calibration(
        raw_predictions,
        candidate_model=candidate_model,
        baseline_model=baseline_model,
        history_window=history_window,
        min_history=min_history,
        ramp_threshold=ramp_threshold,
    )
    fold_metrics, summary = summarize_calibration(
        calibrated,
        baseline_model=baseline_model,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    calibrated.to_parquet(
        output_dir / "calibrated_predictions.parquet",
        index=False,
    )
    fold_metrics.to_csv(output_dir / "fold_metrics.csv", index=False)
    summary.to_csv(output_dir / "summary.csv", index=False)

    offsets = (
        calibrated[calibrated["calibration_method"].ne("none")]
        [["fold", "model", "calibration_offset", "calibration_history_size"]]
        .drop_duplicates()
        .sort_values(["fold", "model"])
        .to_dict(orient="records")
    )
    metadata: dict[str, object] = {
        "input": str(input_path),
        "candidate_model": candidate_model,
        "baseline_model": baseline_model,
        "history_window": history_window,
        "min_history": min_history,
        "ramp_threshold": ramp_threshold,
        "residual_definition": "actual_minus_prediction",
        "calibration_scope": "previous_folds_only",
        "offsets": offsets,
    }
    with (output_dir / "metadata.json").open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, ensure_ascii=False)

    return summary, fold_metrics, metadata
