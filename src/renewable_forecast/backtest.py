from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from renewable_forecast.features import (
    FEATURE_COLUMNS,
    build_feature_frame,
)


@dataclass(frozen=True)
class TimeFold:
    fold_id: int
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


def generate_folds(
    frame: pd.DataFrame,
    initial_train_days: int = 180,
    test_days: int = 7,
    step_days: int = 7,
) -> list[TimeFold]:
    """Cria janelas expansivas com testes semanais."""

    parameters = {
        "initial_train_days": initial_train_days,
        "test_days": test_days,
        "step_days": step_days,
    }

    invalid = [
        name
        for name, value in parameters.items()
        if value <= 0
    ]

    if invalid:
        raise ValueError(
            "Os parâmetros dos folds devem ser positivos: "
            f"{', '.join(invalid)}."
        )

    first_timestamp = frame["din_instante"].min()
    final_exclusive = (
        frame["din_instante"].max()
        + pd.Timedelta(hours=1)
    )

    test_start = (
        first_timestamp
        + pd.Timedelta(days=initial_train_days)
    )

    test_duration = pd.Timedelta(days=test_days)
    step = pd.Timedelta(days=step_days)

    folds: list[TimeFold] = []
    fold_id = 1

    while test_start + test_duration <= final_exclusive:
        folds.append(
            TimeFold(
                fold_id=fold_id,
                train_end=test_start,
                test_start=test_start,
                test_end=test_start + test_duration,
            )
        )

        fold_id += 1
        test_start += step

    if not folds:
        raise ValueError(
            "Dados insuficientes para gerar folds temporais."
        )

    return folds


def _calculate_metrics(
    predictions: pd.DataFrame,
) -> dict[str, float | int]:
    error = (
        predictions["actual"]
        - predictions["prediction"]
    )

    ramp_predictions = predictions.loc[
        predictions["is_ramp"]
    ]

    return {
        "observations": len(predictions),
        "mae": error.abs().mean(),
        "rmse": np.sqrt(np.mean(np.square(error))),
        "bias": error.mean(),
        "maximum_error": error.abs().max(),
        "ramp_observations": len(ramp_predictions),
        "ramp_mae": (
            (
                ramp_predictions["actual"]
                - ramp_predictions["prediction"]
            )
            .abs()
            .mean()
            if not ramp_predictions.empty
            else np.nan
        ),
    }


def run_backtest(
    input_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Executa backtesting expanding-window de uma hora à frente."""

    series = pd.read_parquet(input_path)
    frame = build_feature_frame(series)
    folds = generate_folds(frame)

    prediction_frames: list[pd.DataFrame] = []

    for fold in folds:
        train = frame.loc[
            frame["din_instante"] < fold.train_end
        ].copy()

        test = frame.loc[
            (
                frame["din_instante"]
                >= fold.test_start
            )
            & (
                frame["din_instante"]
                < fold.test_end
            )
        ].copy()

        train_ramps = (
            train["val_geracao"]
            - train["lag_1h"]
        ).abs()

        ramp_threshold = train_ramps.quantile(0.90)

        is_ramp = (
            test["val_geracao"]
            - test["lag_1h"]
        ).abs() >= ramp_threshold

        train_delta = (
            train["val_geracao"]
            - train["lag_1h"]
        )

        hourly_drift = (
            train
            .assign(target_delta=train_delta)
            .groupby("hour")["target_delta"]
            .mean()
        )

        drift_adjustment = (
            test["hour"]
            .map(hourly_drift)
            .fillna(0.0)
        )

        ridge = make_pipeline(
            StandardScaler(),
            Ridge(alpha=1.0),
        )

        gradient_boosting = (
            HistGradientBoostingRegressor(
                learning_rate=0.05,
                max_iter=200,
                max_leaf_nodes=31,
                l2_regularization=1.0,
                random_state=42,
            )
        )

        ridge.fit(
            train[FEATURE_COLUMNS],
            train["val_geracao"],
        )

        gradient_boosting.fit(
            train[FEATURE_COLUMNS],
            train["val_geracao"],
        )

        model_predictions = {
            "persistence_1h": test["lag_1h"],
            "seasonal_24h": test["lag_24h"],
            "seasonal_168h": test["lag_168h"],
            "hourly_drift": (
                test["lag_1h"] + drift_adjustment
            ),
            "ridge": ridge.predict(
                test[FEATURE_COLUMNS]
            ),
            "hist_gradient_boosting": (
                gradient_boosting.predict(
                    test[FEATURE_COLUMNS]
                )
            ),
        }

        for model_name, prediction in model_predictions.items():
            prediction_frame = pd.DataFrame({
                "fold": fold.fold_id,
                "din_instante": test["din_instante"],
                "model": model_name,
                "actual": test["val_geracao"],
                "prediction": np.maximum(
                    np.asarray(prediction, dtype=float),
                    0.0,
                ),
                "is_ramp": is_ramp.to_numpy(),
                "ramp_threshold": ramp_threshold,
            })

            prediction_frames.append(prediction_frame)

    predictions = pd.concat(
        prediction_frames,
        ignore_index=True,
    )

    fold_metrics_records = []

    for (fold_id, model), group in predictions.groupby(
        ["fold", "model"]
    ):
        fold_metrics_records.append({
            "fold": fold_id,
            "model": model,
            **_calculate_metrics(group),
        })

    fold_metrics = pd.DataFrame(fold_metrics_records)

    summary_records = []

    for model, group in predictions.groupby("model"):
        summary_records.append({
            "model": model,
            "folds": group["fold"].nunique(),
            **_calculate_metrics(group),
        })

    summary = pd.DataFrame(summary_records)

    persistence_mae = summary.loc[
        summary["model"] == "persistence_1h",
        "mae",
    ].iloc[0]

    summary["mae_improvement_vs_persistence_pct"] = (
        1 - summary["mae"] / persistence_mae
    ) * 100

    summary = (
        summary
        .sort_values("mae")
        .reset_index(drop=True)
    )

    return predictions, fold_metrics, summary


def save_backtest_results(
    predictions: pd.DataFrame,
    fold_metrics: pd.DataFrame,
    summary: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    predictions.to_parquet(
        output_dir / "predictions.parquet",
        index=False,
    )

    fold_metrics.to_csv(
        output_dir / "fold_metrics.csv",
        index=False,
    )

    summary.to_csv(
        output_dir / "summary.csv",
        index=False,
    )
