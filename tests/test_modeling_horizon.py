import numpy as np
import pandas as pd
import pytest

from renewable_forecast.features import FEATURE_COLUMNS
from renewable_forecast.modeling import fit_horizon_search


@pytest.mark.parametrize(
    "delay, expected_persistence_mae",
    [(0, 6.0), (2, 8.0)],
)
def test_horizon_search_uses_correct_target_and_temporal_cuts(
    delay,
    expected_persistence_mae,
):
    series = pd.DataFrame({
        "din_instante": pd.date_range(
            "2026-01-01", periods=360, freq="h"
        ),
        "val_geracao": 100.0 + np.arange(360),
    })

    search, frame = fit_horizon_search(
        series,
        horizon_hours=6,
        availability_delay_hours=delay,
        n_splits=2,
        test_size=24,
        param_grid={
            "max_iter": [5, 10],
            "max_leaf_nodes": [3],
            "min_samples_leaf": [10],
        },
    )

    assert search.n_splits_ == 2
    assert len(search.cv_results_["params"]) == 2

    assert (
        search.best_estimator_.feature_names_in_.tolist()
        == FEATURE_COLUMNS
    )

    np.testing.assert_allclose(
        -search.cv_results_["mean_test_neg_persistence_mae"],
        expected_persistence_mae,
    )

    assert np.isfinite(
        search.cv_results_["mean_test_neg_mae"]
    ).all()

    for train_idx, valid_idx in search.cv:
        latest_label = (
            frame.iloc[train_idx]["target_available_at"].max()
        )
        first_prediction = (
            frame.iloc[valid_idx]["forecast_origin"].min()
        )

        assert latest_label < first_prediction