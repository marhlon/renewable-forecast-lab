"""Contraprovas do contrato novo, independentes das métricas observadas."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "notebooks"))
from bloco2_modelagem_core import FEATURES, build_frame, fit_mask, period_mask
from explicacao_local import exact_group_shapley
from selecao_atributos_temporal import CANDIDATES


def source(n=240):
    return pd.DataFrame({"din_instante": pd.date_range("2026-01-01", periods=n, freq="h"),
                         "val_geracao": np.arange(n, dtype=float)})


def test_clock_alignment_and_causal_features():
    data = source()
    original = data.copy(deep=True)
    frame = build_frame(data)
    row = frame.iloc[80]
    assert row.last_observed == 78
    assert row.previous_observed == 77
    assert row.lag_1h == 78 and row.lag_24h == 55
    assert row.y24 == 104
    assert row.ramp_down_1h == -1
    assert row.history_end == row.forecast_origin - pd.Timedelta(hours=2)
    assert row.target_time == row.forecast_origin + pd.Timedelta(hours=24)
    assert row.label_available_at == row.forecast_origin + pd.Timedelta(hours=26)
    assert row.ramp_label_available_at == row.forecast_origin + pd.Timedelta(hours=3)
    assert row.mean6 == np.mean(np.arange(73, 79))
    assert row.std6 == pytest.approx(np.std(np.arange(73, 79), ddof=0))
    changed = data.copy()
    changed.loc[79:, "val_geracao"] = 987654
    pd.testing.assert_series_equal(frame.iloc[80][FEATURES], build_frame(changed).iloc[80][FEATURES])
    pd.testing.assert_frame_equal(data, original)


def test_missing_hours_retained_without_zero_imputation():
    data = source().drop(index=60)
    frame = build_frame(data)
    assert len(frame) == 240
    assert np.isnan(frame.loc[62, "last_observed"])
    assert np.isnan(frame.loc[62, "mean6"])
    assert not fit_mask(frame, "2026-01-09").loc[62]
    assert not np.isfinite(frame.iloc[0].lag_24h)
    assert not np.isfinite(frame.iloc[-1].y24)


def test_strict_label_purge_including_exact_cutoff():
    frame = build_frame(source())
    cut = frame.loc[100, "label_available_at"]
    mask = fit_mask(frame, cut)
    assert not mask.loc[100]
    assert mask.loc[99]
    assert frame.loc[mask, "label_available_at"].lt(cut).all()
    ramp_cut = frame.loc[100, "ramp_label_available_at"]
    assert not fit_mask(frame, ramp_cut, "ramp_down_1h").loc[100]
    assert fit_mask(frame, ramp_cut, "ramp_down_1h").loc[99]


def test_candidates_use_same_cohort_and_feature_contract():
    assert len(CANDIDATES) == 8
    assert len(FEATURES) == 33 and len(set(FEATURES)) == 33
    assert all(set(features) <= set(FEATURES) for _, features in CANDIDATES)
    frame = build_frame(source())
    mask = period_mask(frame, "2026-01-03", "2026-01-04")
    assert mask.sum() == 24
    assert np.isfinite(frame.loc[mask, FEATURES + ["y24"]]).all().all()


def test_exact_group_shapley_matches_manual_linear_solution():
    background = pd.DataFrame({"a": [0., 2.], "b": [2., 4.], "c": [4., 6.]})
    example = pd.Series({"a": 5., "b": 7., "c": 9.})
    def model(data):
        return 3 + 2*data.a - data.b + .5*data.c
    groups = {"ab": ["a", "b"], "c": ["c"]}
    phi, base, prediction, coalitions = exact_group_shapley(model, example, background, groups)
    assert phi["ab"] == pytest.approx(2*(5-1) - (7-3))
    assert phi["c"] == pytest.approx(.5*(9-5))
    assert base == pytest.approx(4.5)
    assert base + sum(phi.values()) == pytest.approx(prediction)
    assert len(coalitions) == 4


def test_shapley_rejects_overlapping_or_incomplete_groups():
    background = pd.DataFrame({"a": [1.], "b": [2.]})
    with pytest.raises(ValueError, match="particionar"):
        exact_group_shapley(lambda data: data.sum(axis=1), background.iloc[0], background,
                           {"a": ["a"], "again": ["a", "b"]})
