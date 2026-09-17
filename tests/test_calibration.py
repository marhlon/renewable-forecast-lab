from __future__ import annotations

import pandas as pd
import pytest

from renewable_forecast.calibration import (
    apply_prequential_calibration,
    summarize_calibration,
)


def _synthetic_predictions() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    times = pd.date_range("2026-01-01", periods=4, freq="h")
    actuals = [10.0, 20.0, 30.0, 40.0]

    for index, (timestamp, actual) in enumerate(zip(times, actuals)):
        fold = 1 if index < 2 else 2
        rows.extend(
            [
                {
                    "fold": fold,
                    "model": "hist_gradient_boosting",
                    "timestamp": timestamp,
                    "actual": actual,
                    "prediction": actual - 2.0,
                    "is_ramp": False,
                },
                {
                    "fold": fold,
                    "model": "persistence_1h",
                    "timestamp": timestamp,
                    "actual": actual,
                    "prediction": actual - 4.0,
                    "is_ramp": False,
                },
            ]
        )

    return pd.DataFrame(rows)


def test_calibration_uses_previous_folds_only() -> None:
    result = apply_prequential_calibration(
        _synthetic_predictions(),
        history_window=10,
        min_history=1,
    )
    calibrated = result[
        result["model"].eq(
            "hist_gradient_boosting_calibrated_mean"
        )
    ]

    assert set(
        calibrated.loc[
            calibrated["fold"].eq(1),
            "calibration_offset",
        ]
    ) == {0.0}
    assert set(
        calibrated.loc[
            calibrated["fold"].eq(2),
            "calibration_offset",
        ]
    ) == {2.0}
    assert (
        calibrated.loc[calibrated["fold"].eq(2), "error"] == 0.0
    ).all()


def test_summary_contains_candidate_and_baseline() -> None:
    result = apply_prequential_calibration(
        _synthetic_predictions(),
        history_window=10,
        min_history=1,
    )
    _, summary = summarize_calibration(result)

    assert "persistence_1h" in set(summary["model"])
    assert (
        "hist_gradient_boosting_calibrated_mean"
        in set(summary["model"])
    )

    with pytest.raises(ValueError, match="min_history"):
        apply_prequential_calibration(
            _synthetic_predictions(),
            history_window=10,
            min_history=11,
        )
