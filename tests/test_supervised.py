import numpy as np
import pandas as pd
import pytest

from renewable_forecast.features import FEATURE_COLUMNS, build_feature_frame
from renewable_forecast.supervised import (
    build_horizon_pairs,
    build_horizon_training_frame,
    purged_time_series_splits,
)

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def synthetic_series():
    """Gera 12 observações horárias (00h às 11h) com geração de 100 a 111."""
    dates = pd.date_range("2026-01-01 00:00", periods=12, freq="h")
    return pd.DataFrame({
        "din_instante": dates,
        "val_geracao": [100 + i for i in range(12)]
    })


@pytest.fixture
def synthetic_series_48():
    """Gera 48 observações horárias com geração de 100 a 147."""
    dates = pd.date_range("2026-01-01 00:00", periods=48, freq="h")
    return pd.DataFrame({
        "din_instante": dates,
        "val_geracao": [100 + i for i in range(48)]
    })


@pytest.fixture
def synthetic_series_240():
    """Gera 240 observações horárias (10 dias) com geração de 100 a 339."""
    dates = pd.date_range("2026-01-01 00:00", periods=240, freq="h")
    return pd.DataFrame({
        "din_instante": dates,
        "val_geracao": [100 + i for i in range(240)]
    })

# -----------------------------------------------------------------------------
# Testes: build_horizon_pairs
# -----------------------------------------------------------------------------

def test_complete_series_horizon_6(synthetic_series):
    result = build_horizon_pairs(synthetic_series, horizon_hours=6)
    target = result.loc[result["forecast_origin"] == "2026-01-01 00:00", "target_generation"].values[0]
    assert target == 106


def test_missing_intermediate_hour_preserves_temporal_alignment(synthetic_series):
    df = synthetic_series[synthetic_series["din_instante"] != "2026-01-01 03:00"].copy()
    result = build_horizon_pairs(df, horizon_hours=6)
    target = result.loc[result["forecast_origin"] == "2026-01-01 00:00", "target_generation"].values[0]
    assert target == 106


def test_missing_target_hour_returns_nan(synthetic_series):
    df = synthetic_series[synthetic_series["din_instante"] != "2026-01-01 06:00"].copy()
    result = build_horizon_pairs(df, horizon_hours=6)
    target = result.loc[result["forecast_origin"] == "2026-01-01 00:00", "target_generation"].values[0]
    assert pd.isna(target)


def test_duplicate_timestamp_raises_error(synthetic_series):
    df = pd.concat([synthetic_series, synthetic_series.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError):
        build_horizon_pairs(df)


@pytest.mark.parametrize("invalid_horizon", [0, -1, 2.5, True, False, "6"])
def test_invalid_horizon_raises_error(synthetic_series, invalid_horizon):
    with pytest.raises(ValueError):
        build_horizon_pairs(synthetic_series, horizon_hours=invalid_horizon)


def test_missing_timestamp_raises_error(synthetic_series):
    df = synthetic_series.copy()
    df.loc[2, "din_instante"] = None
    with pytest.raises(ValueError):
        build_horizon_pairs(df)


@pytest.mark.parametrize("missing_timestamp", ["", "NaT"])
def test_missing_timestamp_after_parsing_raises_error(
    synthetic_series, missing_timestamp
):
    df = synthetic_series.astype({"din_instante": "string"})
    df.loc[2, "din_instante"] = missing_timestamp

    with pytest.raises(ValueError, match="ausentes ou nulos"):
        build_horizon_pairs(df)

# -----------------------------------------------------------------------------
# Testes: purged_time_series_splits
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "delay_hours, expected_train_sizes",
    [
        (0, [24, 30]),
        (2, [22, 28]),
    ]
)
def test_purged_time_series_splits_sizes_and_leakage(
    synthetic_series_48, delay_hours, expected_train_sizes
):
    pairs = build_horizon_pairs(synthetic_series_48, horizon_hours=6)
    frame = (
        pairs.dropna(subset=["target_generation"])
        .reset_index(drop=True)
    )
    frame["target_available_at"] = (
        frame["target_time"] + pd.Timedelta(hours=delay_hours)
    )

    splits = list(
        purged_time_series_splits(frame, n_splits=2, test_size=6)
    )

    assert len(splits) == 2

    for (train_idx, valid_idx), expected_size in zip(splits, expected_train_sizes):
        assert len(train_idx) == expected_size
        assert len(valid_idx) == 6

        latest_label = frame.iloc[train_idx]["target_available_at"].max()
        first_prediction = frame.iloc[valid_idx]["forecast_origin"].min()

        assert latest_label < first_prediction


def test_purged_splits_missing_dates_raises_error(synthetic_series_48):
    pairs = build_horizon_pairs(synthetic_series_48, horizon_hours=6).dropna().reset_index(drop=True)
    pairs["target_available_at"] = pairs["target_time"]
    pairs.loc[0, "target_available_at"] = None

    with pytest.raises(ValueError, match="preenchidas"):
        list(purged_time_series_splits(pairs, n_splits=2, test_size=6))


def test_purged_splits_non_monotonic_origins_raises_error(synthetic_series_48):
    pairs = build_horizon_pairs(synthetic_series_48, horizon_hours=6).dropna().reset_index(drop=True)
    pairs["target_available_at"] = pairs["target_time"]
    pairs = pairs.iloc[::-1].reset_index(drop=True)

    with pytest.raises(ValueError, match="ordenadas"):
        list(purged_time_series_splits(pairs, n_splits=2, test_size=6))

# -----------------------------------------------------------------------------
# Testes: build_horizon_training_frame
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "delay, exp_ref, exp_end, exp_lag1, exp_roll6, exp_tgt_time, exp_tgt_gen, exp_avail",
    [
        (
            0,
            "2026-01-09 11:00:00",
            "2026-01-09 10:00:00",
            302,
            299.5,
            "2026-01-09 16:00:00",
            308,
            "2026-01-09 16:00:00",
        ),
        (
            2,
            "2026-01-09 09:00:00",
            "2026-01-09 08:00:00",
            300,
            297.5,
            "2026-01-09 16:00:00",
            308,
            "2026-01-09 18:00:00",
        ),
    ]
)
def test_build_horizon_training_frame_specific_emission(
    synthetic_series_240,
    delay,
    exp_ref,
    exp_end,
    exp_lag1,
    exp_roll6,
    exp_tgt_time,
    exp_tgt_gen,
    exp_avail,
):
    frame = build_horizon_training_frame(
        synthetic_series_240, horizon_hours=6, availability_delay_hours=delay
    )

    emission = frame[frame["forecast_origin"] == "2026-01-09 10:00:00"].iloc[0]

    assert str(emission["history_reference_time"]) == exp_ref
    assert str(emission["history_end"]) == exp_end
    assert emission["lag_1h"] == exp_lag1
    assert emission["rolling_mean_6h"] == pytest.approx(exp_roll6)
    assert str(emission["target_time"]) == exp_tgt_time
    assert emission["target_generation"] == exp_tgt_gen
    assert str(emission["target_available_at"]) == exp_avail

    # Calendário relativo às 16h do target_time
    assert emission["hour_sin_1"] == pytest.approx(-0.8660254038)
    assert emission["hour_cos_1"] == pytest.approx(-0.5)


def test_invariance_to_unavailable_future_data(synthetic_series_240):
    delay_hours = 2
    frame_orig = build_horizon_training_frame(
        synthetic_series_240, horizon_hours=6, availability_delay_hours=delay_hours
    )

    target_origin = pd.Timestamp("2026-01-09 10:00:00")
    row_orig = frame_orig[frame_orig["forecast_origin"] == target_origin].iloc[0]
    cutoff_time = row_orig["history_end"]  # 2026-01-09 08:00:00

    # Adultera a geração futura na série original (após history_end)
    series_tampered = synthetic_series_240.copy()
    future_mask = series_tampered["din_instante"] > cutoff_time
    series_tampered.loc[future_mask, "val_geracao"] *= 100

    frame_tampered = build_horizon_training_frame(
        series_tampered, horizon_hours=6, availability_delay_hours=delay_hours
    )
    row_tampered = frame_tampered[frame_tampered["forecast_origin"] == target_origin].iloc[0]

    # As 27 features de entrada permanecem estritamente idênticas
    for feature in FEATURE_COLUMNS:
        assert row_orig[feature] == pytest.approx(row_tampered[feature]), f"Leakage detectado na feature {feature}"

    # O alvo reflete a alteração (passa de 308 para 30800)
    assert row_orig["target_generation"] == 308
    assert row_tampered["target_generation"] == 30800


def test_equivalence_h1_delay0_with_original_constructor(synthetic_series_240):
    base_frame = build_feature_frame(synthetic_series_240, require_target=True)
    horizon_frame = build_horizon_training_frame(
        synthetic_series_240, horizon_hours=1, availability_delay_hours=0
    )

    merged = base_frame.merge(
        horizon_frame,
        left_on="din_instante",
        right_on="target_time",
        how="inner",
        validate="one_to_one",
        suffixes=("_base", "_horizon"),
    )

    assert len(merged) == len(base_frame) == len(horizon_frame)

    for feature in FEATURE_COLUMNS:
        np.testing.assert_allclose(
            merged[feature + "_base"],
            merged[feature + "_horizon"],
            err_msg=f"Divergência na feature {feature}"
        )

    np.testing.assert_allclose(
        merged["val_geracao"],
        merged["target_generation"],
        err_msg="Divergência no alvo de geração"
    )


@pytest.mark.parametrize("invalid_delay", [-1, 1.5, True, False, "2"])
def test_invalid_availability_delay_raises_error(synthetic_series_240, invalid_delay):
    with pytest.raises(ValueError):
        build_horizon_training_frame(
            synthetic_series_240, horizon_hours=6, availability_delay_hours=invalid_delay
        )