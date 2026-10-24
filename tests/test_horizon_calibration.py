"""Instalar em tests/test_horizon_calibration.py."""
import numpy as np
import pandas as pd

from renewable_forecast.horizon_calibration import apply_available_offsets


def make_predictions():
    origin = pd.date_range("2026-01-01", periods=12, freq="h")
    residual = np.array([0, 1, 2, 30, 4, 5, 6, 7, 8, 9, 10, 11], dtype=float)
    return pd.DataFrame({
        "forecast_origin": origin,
        "target_time": origin + pd.Timedelta(hours=2),
        "target_available_at": origin + pd.Timedelta(hours=3),
        "prediction": np.full(12, 10.0),
        "target_generation": 10.0 + residual,
    })


def test_offsets_respect_availability_window_and_minimum_history():
    result = apply_available_offsets(make_predictions(), window_hours=3, min_history=2)

    # Às 04h, só há um resíduo disponível: a correção ainda fica em zero.
    assert result.loc[4, "calibration_n"] == 1
    assert not result.loc[4, "calibration_active"]
    assert result.loc[4, "offset_mean"] == 0.0
    assert result.loc[4, "prediction_mean"] == 10.0

    # Às 07h, a janela de disponibilidade [04h, 07h) contém [1, 2, 30].
    row = result.iloc[7]
    assert row["calibration_n"] == 3
    assert row["calibration_latest_available_at"] == pd.Timestamp("2026-01-01 06:00")
    assert row["offset_mean"] == 11.0
    assert row["offset_median"] == 2.0
    assert row["prediction_mean"] == 21.0
    assert row["prediction_median"] == 12.0


def test_unavailable_targets_do_not_change_past_corrections():
    original = make_predictions()
    cutoff = pd.Timestamp("2026-01-01 07:00")
    tampered = original.copy()
    unavailable = tampered["target_available_at"] >= cutoff
    tampered.loc[unavailable, "target_generation"] += 10000.0

    before = apply_available_offsets(original, window_hours=3, min_history=2)
    after = apply_available_offsets(tampered, window_hours=3, min_history=2)
    past = before["forecast_origin"] <= cutoff
    columns = ["offset_mean", "offset_median", "prediction_mean", "prediction_median"]
    pd.testing.assert_frame_equal(before.loc[past, columns], after.loc[past, columns])
