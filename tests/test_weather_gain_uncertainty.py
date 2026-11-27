"""Contraprovas pequenas do contrato M02-05; nenhum dado/modelo real."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from renewable_forecast.weather_gain_uncertainty import (
    circular_means,
    load_predictions,
    summarize,
)


def paired_frame(first=(1, 1, 1), second=(3, 3, 3, 3, 3)):
    parts = []
    for fold, deltas in enumerate((first, second), 1):
        if not len(deltas):
            continue
        deltas = np.asarray(deltas, dtype=float)
        target = np.full(deltas.size, 100.0)
        parts.append(pd.DataFrame({
            "forecast_origin": pd.date_range(
                pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(days=3 * (fold - 1)),
                periods=deltas.size, freq="h",
            ),
            "fold": fold,
            "target_generation": target,
            "hgb_history": target + 2 + np.maximum(deltas, 0),
            "hgb_history_weather": target + 2 + np.maximum(-deltas, 0),
        }))
    return pd.concat(parts, ignore_index=True)


def calculate(frame, **changes):
    parameters = {"block_hours": [1, 2], "repetitions": 1000, "seed": 42}
    parameters.update(changes)
    return summarize(frame, **parameters)


def test_weighted_aggregate_and_no_cross_fold_mixing(record_property):
    # A bootstrap global de linhas variaria a proporcao dos deltas 1 e 3.
    # A estratificacao correta tem IC degenerado, mesmo com tamanhos 3 e 5.
    result = calculate(paired_frame())
    assert len(result) == 6
    aggregate = result[result.scope == "aggregate"]
    assert aggregate.n.tolist() == [8, 8]
    for column in ("mean_gain_mwmed", "bootstrap_mean_gain_mwmed",
                   "ci95_low_mwmed", "ci95_high_mwmed"):
        np.testing.assert_allclose(aggregate[column], [2.25, 2.25], rtol=0, atol=0)
    assert not np.isclose(aggregate.mean_gain_mwmed.iloc[0], (1 + 3) / 2)
    assert result[result.scope == "fold"].n.tolist() == [3, 5, 3, 5]
    record_property("evidence", json.dumps({
        "fold_sizes": [3, 5], "fold_gains": [1.0, 3.0],
        "weighted_aggregate": 2.25, "unweighted_mean_rejected": 2.0,
        "ci95_each_block": [2.25, 2.25], "rows_summary": len(result),
    }))


def test_paired_errors_keep_the_constant_difference(record_property):
    frame = paired_frame((1, 1, 1), ())
    frame["hgb_history"] = [102.0, 106.0, 110.0]
    frame["hgb_history_weather"] = [101.0, 105.0, 109.0]
    result = calculate(frame)
    assert result.mean_gain_mwmed.eq(1).all()
    assert result.ci95_low_mwmed.eq(1).all()
    assert result.ci95_high_mwmed.eq(1).all()
    record_property("evidence", json.dumps({
        "reference_absolute_errors": [2, 6, 10],
        "candidate_absolute_errors": [1, 5, 9],
        "paired_gain": 1, "ci95": [1, 1],
    }))


def test_circular_indices_match_manual_blocks_and_preserve_values(record_property):
    values = np.array([0.0, 2.0, 5.0, 11.0, 31.0])
    before = values.copy()
    n, block, repetitions, seed = 5, 2, 1031, 17
    starts = np.random.default_rng(seed).integers(0, n, size=(repetitions, 3))
    expected = []
    wrapped = False
    for replica_starts in starts:
        indices = []
        for start in replica_starts:
            wrapped = wrapped or start == n - 1
            for offset in range(block):
                indices.append(int((start + offset) % n))
        expected.append(sum(values[index] for index in indices[:n]) / n)
    actual = circular_means(values, block, repetitions, np.random.default_rng(seed))
    assert wrapped
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(values, before)
    record_property("evidence", json.dumps({
        "n": n, "block": block, "repetitions": repetitions, "seed": seed,
        "first_starts": starts[0].tolist(),
        "first_mean_manual": expected[0],
        "first_mean_function": float(actual[0]),
        "circular_wrap_observed": bool(wrapped),
        "max_absolute_difference": float(np.max(np.abs(actual - expected))),
    }))


def test_aggregate_intervals_are_from_weighted_replicas(record_property):
    values_by_fold = [np.array([-2.0, 1.0, 8.0]), np.array([7.0, -4.0, 3.0, 10.0, 2.0])]
    result = calculate(paired_frame(*values_by_fold), block_hours=[2])
    aggregate = result[result.scope == "aggregate"].iloc[0]
    # Oracle direto: nao chama circular_means nem usa medias de ICs por fold.
    samples = []
    for fold, values in enumerate(values_by_fold, 1):
        rng = np.random.default_rng(np.random.SeedSequence([42, 2, fold]))
        fold_samples = []
        for _ in range(1000):
            selected = []
            for start in rng.integers(0, len(values), size=(len(values) + 1) // 2):
                selected.extend([values[start], values[(start + 1) % len(values)]])
            fold_samples.append(sum(selected[:len(values)]) / len(values))
        samples.append(np.asarray(fold_samples))
    weighted = (3 * samples[0] + 5 * samples[1]) / 8
    low, high = np.quantile(weighted, [0.025, 0.975], method="linear")
    assert aggregate.mean_gain_mwmed == pytest.approx(25 / 8)
    assert aggregate.bootstrap_mean_gain_mwmed == pytest.approx(weighted.mean(), abs=1e-14)
    assert aggregate.ci95_low_mwmed == pytest.approx(low, abs=1e-14)
    assert aggregate.ci95_high_mwmed == pytest.approx(high, abs=1e-14)
    record_property("evidence", json.dumps({
        "point_gain": float(aggregate.mean_gain_mwmed),
        "manual_ci95": [float(low), float(high)],
        "function_ci95": [float(aggregate.ci95_low_mwmed), float(aggregate.ci95_high_mwmed)],
    }))


def test_determinism_order_and_input_global_rng_preservation():
    frame = paired_frame((-8, 1, 30), (-4, 3, 10, 19, 41))
    before = frame.copy(deep=True)
    rng_before = np.random.get_state()
    first = calculate(frame)
    second = calculate(frame)
    reordered = calculate(frame.iloc[::-1], block_hours=[2, 1])
    pd.testing.assert_frame_equal(first, second, check_exact=True)
    keys = ["block_hours", "scope", "fold"]
    pd.testing.assert_frame_equal(
        first.sort_values(keys).reset_index(drop=True),
        reordered.sort_values(keys).reset_index(drop=True), check_exact=True,
    )
    pd.testing.assert_frame_equal(frame, before, check_exact=True)
    rng_after = np.random.get_state()
    assert rng_before[0] == rng_after[0]
    np.testing.assert_array_equal(rng_before[1], rng_after[1])
    assert rng_before[2:] == rng_after[2:]
    changed_seed = calculate(frame, seed=43)
    # Um unico percentil pode coincidir por acaso em uma distribuicao discreta.
    assert not first.drop(columns="seed").equals(changed_seed.drop(columns="seed"))


def test_nonpositive_fraction_and_zero_gain():
    negative = calculate(paired_frame((-1, -1, -1), (-2, -2, -2, -2, -2)))
    assert negative.bootstrap_fraction_nonpositive.eq(1).all()
    zero = calculate(paired_frame((0, 0, 0), (0, 0, 0, 0, 0)))
    assert zero.mean_gain_mwmed.eq(0).all()
    assert zero.ci95_low_mwmed.eq(0).all()
    assert zero.ci95_high_mwmed.eq(0).all()


def test_overflow_of_finite_bootstrap_values_is_rejected():
    with pytest.raises(ValueError, match="finita"):
        circular_means(np.array([1e308, 1e308]), 1, 2, np.random.default_rng(42))


def test_overflow_of_finite_mae_values_is_rejected():
    frame = paired_frame((0, 0, 0), ())
    frame["target_generation"] = 0.0
    frame["hgb_history"] = 1e308
    frame["hgb_history_weather"] = 1e308
    with np.errstate(over="ignore", invalid="ignore"):
        with pytest.raises(ValueError, match="finitas"):
            calculate(frame)


@pytest.mark.parametrize("case", [
    "empty", "missing_column", "duplicate_column", "duplicate_time", "bad_time",
    "nat_time", "numeric_time", "gap", "singleton", "interleaved_folds",
    "zero_fold", "negative_fold", "fractional_fold", "bool_fold", "infinite_fold",
    "overflow_fold", "text_fold", "missing_target", "infinite_prediction",
    "text_prediction", "bool_prediction", "complex_prediction",
    "wrong_saved_delta", "missing_saved_delta",
])
def test_invalid_prediction_contracts(case):
    frame = paired_frame().astype({"fold": object, "hgb_history": object, "forecast_origin": object})
    if case == "empty":
        frame = frame.iloc[:0]
    elif case == "missing_column":
        frame = frame.drop(columns="hgb_history")
    elif case == "duplicate_column":
        frame = pd.concat([frame, frame[["fold"]]], axis=1)
    elif case == "duplicate_time":
        frame.loc[1, "forecast_origin"] = frame.loc[0, "forecast_origin"]
    elif case in ("bad_time", "nat_time", "numeric_time"):
        frame.loc[0, "forecast_origin"] = {"bad_time": "invalid", "nat_time": "NaT", "numeric_time": 123}[case]
    elif case == "gap":
        frame.loc[2, "forecast_origin"] += pd.Timedelta(hours=1)
    elif case == "singleton":
        frame = frame.iloc[[0, 3, 4, 5, 6, 7]]
    elif case == "interleaved_folds":
        frame.loc[1, "fold"] = 2
    elif case.endswith("_fold"):
        frame.loc[0, "fold"] = {
            "zero_fold": 0, "negative_fold": -1, "fractional_fold": 1.5,
            "bool_fold": True, "infinite_fold": np.inf, "overflow_fold": 2**64,
            "text_fold": "invalid",
        }[case]
    elif case == "missing_target":
        frame.loc[0, "target_generation"] = np.nan
    elif case.endswith("_prediction"):
        frame.loc[0, "hgb_history"] = {
            "infinite_prediction": np.inf, "text_prediction": "invalid",
            "bool_prediction": True, "complex_prediction": 1 + 2j,
        }[case]
    elif case in ("wrong_saved_delta", "missing_saved_delta"):
        frame["delta_absolute_error"] = -999.0 if case == "wrong_saved_delta" else np.nan
    with pytest.raises(ValueError):
        calculate(frame)


@pytest.mark.parametrize("changes", [
    {"block_hours": []}, {"block_hours": [0]}, {"block_hours": [3]},
    {"block_hours": [True]}, {"block_hours": [1.5]}, {"block_hours": [1, 1]},
    {"block_hours": "1"}, {"block_hours": None},
    {"repetitions": 999}, {"repetitions": 1000.0}, {"repetitions": True},
    {"seed": -1}, {"seed": 1.5}, {"seed": True},
])
def test_invalid_bootstrap_parameters(changes):
    with pytest.raises(ValueError):
        calculate(paired_frame(), **changes)


@pytest.mark.parametrize("values,block,repetitions,rng", [
    ([], 1, 1, np.random.default_rng(1)),
    ([1], 1, 1, np.random.default_rng(1)),
    ([[1, 2], [3, 4]], 1, 1, np.random.default_rng(1)),
    ([True, False], 1, 1, np.random.default_rng(1)),
    ([1 + 2j, 3], 1, 1, np.random.default_rng(1)),
    ([1, np.inf], 1, 1, np.random.default_rng(1)),
    ([1, 2, 3], 3, 1, np.random.default_rng(1)),
    ([1, 2, 3], 1, 0, np.random.default_rng(1)),
    ([1, 2, 3], 1, 1, None),
])
def test_invalid_circular_inputs_and_rng(values, block, repetitions, rng):
    with pytest.raises(ValueError):
        circular_means(np.asarray(values), block, repetitions, rng)


def test_csv_loader_recomputes_delta_without_writing_input(tmp_path):
    source = tmp_path / "paired.csv"
    frame = paired_frame()
    frame.to_csv(source, index=False)
    before = source.read_bytes()
    loaded = load_predictions(source)
    assert loaded.delta_absolute_error.tolist() == [1, 1, 1, 3, 3, 3, 3, 3]
    assert source.read_bytes() == before


def test_csv_loader_rejects_duplicate_header(tmp_path):
    source = tmp_path / "ambiguous.csv"
    source.write_text("fold,fold,forecast_origin\n1,2,2026-01-01\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicados"):
        load_predictions(source)


def test_cli_creates_real_csv_receipt_and_refuses_overwrite(tmp_path, record_property):
    source = tmp_path / "paired_fixture.csv"
    paired_frame().to_csv(source, index=False)
    input_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    output = tmp_path / "output"
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    command = [
        sys.executable, "-m", "renewable_forecast.weather_gain_uncertainty",
        "--predictions", str(source), "--output-dir", str(output),
        "--block-hours", "1", "2", "--repetitions", "1000", "--seed", "42",
    ]
    run = subprocess.run(command, capture_output=True, text=True, env=env, cwd=root, timeout=60)
    assert run.returncode == 0, run.stderr
    receipt_file = output / "receipt.json"
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    summary_file = output / "summary.csv"
    summary = pd.read_csv(summary_file)
    assert len(summary) == 6
    assert receipt["completed"] and receipt["exit_code"] == 0
    assert receipt["rows_input"] == 8 and receipt["fold_counts"] == {"1": 3, "2": 5}
    assert receipt["rows_summary"] == 6
    assert receipt["input"]["sha256"] == input_hash
    assert hashlib.sha256(source.read_bytes()).hexdigest() == input_hash
    assert receipt["output_sha256"]["summary.csv"] == hashlib.sha256(summary_file.read_bytes()).hexdigest()
    module = root / "src/renewable_forecast/weather_gain_uncertainty.py"
    assert receipt["code"]["sha256"] == hashlib.sha256(module.read_bytes()).hexdigest()
    assert not receipt["models_trained"] and not receipt["models_refitted"]
    assert not receipt["independent_holdout_certified"]
    assert not receipt["nonpositive_fraction_is_p_value"]
    preserved = {p.name: p.read_bytes() for p in output.iterdir()}
    repeated = subprocess.run(command, capture_output=True, text=True, env=env, cwd=root, timeout=60)
    assert repeated.returncode == 2
    assert {p.name: p.read_bytes() for p in output.iterdir()} == preserved
    record_property("evidence", json.dumps({
        "fixture_only": True, "command": command, "exit_code": run.returncode,
        "overwrite_exit_code": repeated.returncode,
        "input_sha256": input_hash, "receipt": receipt,
        "receipt_sha256": hashlib.sha256(receipt_file.read_bytes()).hexdigest(),
        "temporary_artifacts_retention_not_audited": True,
    }))


def test_cli_rejects_invalid_parameters_without_publishing(tmp_path):
    source = tmp_path / "paired_fixture.csv"
    paired_frame().to_csv(source, index=False)
    output = tmp_path / "invalid_output"
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    command = [
        sys.executable, "-m", "renewable_forecast.weather_gain_uncertainty",
        "--predictions", str(source), "--output-dir", str(output),
        "--block-hours", "3", "--repetitions", "1000",
    ]
    run = subprocess.run(command, capture_output=True, text=True, env=env, cwd=root, timeout=60)
    assert run.returncode == 2
    assert not output.exists()
