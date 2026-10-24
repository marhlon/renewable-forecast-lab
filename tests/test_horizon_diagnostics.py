"""Instalar em tests/test_horizon_diagnostics.py."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyRegressor

from renewable_forecast.features import FEATURE_COLUMNS
from renewable_forecast.horizon_diagnostics import evaluate_selected_folds
from renewable_forecast.supervised import (
    build_horizon_training_frame,
    purged_time_series_splits,
)


@pytest.mark.parametrize("direction", [1, -1])
def test_oof_refits_each_fold_and_preserves_bias_direction(direction):
    series = pd.DataFrame({
        "din_instante": pd.date_range("2026-01-01", periods=360, freq="h"),
        "val_geracao": 1000.0 + direction * np.arange(360),
    })
    frame = build_horizon_training_frame(
        series, horizon_hours=6, availability_delay_hours=2
    )
    splits = list(purged_time_series_splits(frame, n_splits=2, test_size=24))

    # Simula best_estimator_: ele já viu todo o desenvolvimento no refit.
    refitted = DummyRegressor(strategy="mean").fit(
        frame[FEATURE_COLUMNS], frame["target_generation"]
    )
    search = SimpleNamespace(best_estimator_=refitted, cv=splits)
    predictions, metrics = evaluate_selected_folds(search, frame)

    assert len(predictions) == 48
    assert predictions["forecast_origin"].is_unique
    np.testing.assert_array_equal(np.sign(metrics["signed_bias"]), direction)

    for fold, (train_idx, valid_idx) in enumerate(splits, start=1):
        actual = predictions.loc[predictions["fold"] == fold]
        expected = frame.iloc[train_idx]["target_generation"].mean()
        np.testing.assert_allclose(actual["prediction"], expected)

        # Reutilizar diretamente o modelo global daria outro resultado.
        leaked = refitted.predict(frame.iloc[valid_idx][FEATURE_COLUMNS])
        assert not np.allclose(actual["prediction"], leaked)

        residual = actual["target_generation"] - actual["prediction"]
        np.testing.assert_allclose(actual["residual"], residual)
        np.testing.assert_allclose(
            metrics.loc[metrics["fold"] == fold, "signed_bias"],
            residual.mean(),
        )
