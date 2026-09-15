import numpy as np
import pandas as pd
import pytest

from renewable_forecast.backtest import (
    generate_folds,
    run_backtest,
    save_backtest_results,
)
from renewable_forecast.cli import build_parser
from renewable_forecast.features import (
    FEATURE_COLUMNS,
    build_feature_frame,
)


def make_series(hours: int = 1000) -> pd.DataFrame:
    return pd.DataFrame({
        "din_instante": pd.date_range(
            "2025-01-01",
            periods=hours,
            freq="h",
        ),
        "val_geracao": np.arange(
            hours,
            dtype=float,
        ),
    })


def test_current_target_is_not_used_as_feature() -> None:
    original = make_series()
    changed = original.copy()

    timestamp = original.loc[
        900,
        "din_instante",
    ]

    changed.loc[
        changed["din_instante"] == timestamp,
        "val_geracao",
    ] = 999_999.0

    original_features = build_feature_frame(original)
    changed_features = build_feature_frame(changed)

    original_row = original_features.loc[
        original_features["din_instante"] == timestamp
    ].iloc[0]

    changed_row = changed_features.loc[
        changed_features["din_instante"] == timestamp
    ].iloc[0]

    np.testing.assert_allclose(
        original_row[FEATURE_COLUMNS].astype(float),
        changed_row[FEATURE_COLUMNS].astype(float),
    )

    assert (
        original_row["val_geracao"]
        != changed_row["val_geracao"]
    )


def test_folds_preserve_temporal_order() -> None:
    frame = build_feature_frame(
        make_series(hours=24 * 365)
    )

    folds = generate_folds(frame)

    assert folds

    for fold in folds:
        assert fold.train_end == fold.test_start
        assert fold.test_start < fold.test_end


def test_rejects_non_hourly_series() -> None:
    series = make_series().drop(index=500).reset_index(drop=True)

    with pytest.raises(ValueError, match="frequência horária"):
        build_feature_frame(series)


def test_rejects_invalid_fold_parameters() -> None:
    frame = build_feature_frame(make_series(hours=24 * 365))

    with pytest.raises(ValueError, match="step_days"):
        generate_folds(frame, step_days=0)


def test_cli_parses_backtest_command(tmp_path) -> None:
    input_path = tmp_path / "series.parquet"
    output_dir = tmp_path / "results"
    args = build_parser().parse_args([
        "backtest", "--input", str(input_path),
        "--output-dir", str(output_dir),
    ])

    assert args.command == "backtest"
    assert args.input == input_path
    assert args.output_dir == output_dir


def test_backtest_and_result_files(tmp_path) -> None:
    input_path = tmp_path / "series.parquet"
    output_dir = tmp_path / "results"
    make_series(hours=24 * 200).to_parquet(input_path, index=False)

    predictions, fold_metrics, summary = run_backtest(input_path)
    save_backtest_results(
        predictions, fold_metrics, summary, output_dir
    )

    assert not predictions.empty
    assert not fold_metrics.empty
    assert set(summary["model"]) == {
        "persistence_1h", "seasonal_24h", "seasonal_168h",
        "hourly_drift", "ridge", "hist_gradient_boosting",
    }
    assert (output_dir / "predictions.parquet").is_file()
    assert (output_dir / "fold_metrics.csv").is_file()
    assert (output_dir / "summary.csv").is_file()
