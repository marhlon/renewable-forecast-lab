"""Contratos do registro e do relógio; não dependem dos dados privados do projeto."""
import json
from pathlib import Path

import pandas as pd
import pytest

import renewable_forecast.event_batch as batch


@pytest.fixture
def ledger(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    source = input_dir / "model_frame.csv"
    pd.DataFrame({
        "target_time": ["2026-08-01T06:00:00Z", "2026-08-01T07:00:00Z"],
        "target_available_at": ["2026-08-01T08:00:00Z", "2026-08-01T09:00:00Z"],
        "target_generation": [60.0, 100.0],
    }).to_csv(source, index=False)
    digest = batch.sha256(source)
    (input_dir / "metadata.json").write_text(json.dumps({"output_sha256": digest}))
    config = {"release": batch.RELEASE, "code_sha256": batch.sha256(Path(batch.__file__)),
              "source_frame_sha256": digest, "policy": {"cost_fp": 1.0, "cost_fn": 4.0},
              "scope": "test", "model_sha256": "synthetic-test-model"}
    db = tmp_path / "ledger.sqlite"
    with batch.connect(db, create=True) as con:
        with batch.transaction(con):
            con.execute("INSERT INTO configuration VALUES (1, ?)", (batch.json_text(config),))
            for hour, prob in [(6, .2), (7, .7)]:
                origin = f"2026-07-31T{hour:02d}:00:00Z"
                con.execute("INSERT INTO predictions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                    origin, f"2026-08-01T{hour:02d}:00:00Z", f"2026-08-01T{hour+2:02d}:00:00Z",
                    "synthetic", "{}", "{}", prob, .5, int(prob >= .5), 77.23, "2026-10-05T00:00:00Z",
                ))
    return input_dir, db


def test_no_labels_before_availability(ledger):
    source, db = ledger
    result = batch.reconcile(source, db, "2026-08-01T07:59:59Z")
    assert result["observed"] == 0
    assert result["awaiting_label"] == 2
    assert result["brier"] is None
    assert result["cost_total"] is None


def test_exact_availability_and_observed_denominator(ledger):
    source, db = ledger
    result = batch.reconcile(source, db, "2026-08-01T08:00:00Z")
    assert (result["observed"], result["awaiting_label"], result["fn"]) == (1, 1, 1)
    assert result["brier"] == pytest.approx(.64)
    assert result["cost_per_observed_emission"] == 4.0


def test_later_snapshot_does_not_change_earlier_or_predictions(ledger):
    source, db = ledger
    with batch.connect(db) as con:
        before = [tuple(r) for r in con.execute("SELECT * FROM predictions")]
    early = batch.reconcile(source, db, "2026-08-01T08:00:00Z")
    late = batch.reconcile(source, db, "2026-08-01T09:00:00Z")
    assert (late["observed"], late["fn"], late["fp"], late["cost_total"]) == (2, 1, 1, 5)
    assert batch.reconcile(source, db, "2026-08-01T08:00:00Z") == early
    with batch.connect(db) as con:
        assert con.execute("SELECT COUNT(*) FROM assessments").fetchone()[0] == 4
        assert [tuple(r) for r in con.execute("SELECT * FROM predictions")] == before


def test_transaction_rolls_back_partial_write(ledger):
    _, db = ledger
    with batch.connect(db) as con:
        with pytest.raises(RuntimeError):
            with batch.transaction(con):
                con.execute("INSERT INTO assessments VALUES (?, ?, 'awaiting_label', NULL, NULL, NULL, NULL)",
                            ("2026-08-01T08:00:00Z", "2026-07-31T06:00:00Z"))
                raise RuntimeError("falha simulada")
        assert con.execute("SELECT COUNT(*) FROM assessments").fetchone()[0] == 0


def test_asof_before_last_emission_rejected(ledger):
    source, db = ledger
    with pytest.raises(ValueError, match="última emissão"):
        batch.reconcile(source, db, "2026-07-31T06:00:00Z")


def test_changed_observation_source_rejected(ledger):
    source, db = ledger
    path = source / "model_frame.csv"
    path.write_text(path.read_text().replace("60.0", "65.0"))
    with pytest.raises(ValueError, match="hash"):
        batch.reconcile(source, db, "2026-08-01T09:00:00Z")


def test_naive_clock_rejected():
    with pytest.raises(ValueError, match="fuso"):
        batch.iso("2026-08-01 08:00:00")
