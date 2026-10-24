"""Verifica incidentes que mudam a conduta; dados sintéticos, sem treinar modelos."""
import json
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from renewable_forecast import event_monitor as monitor
from renewable_forecast.event_batch import SCHEMA


@pytest.fixture
def case(tmp_path):
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "model.joblib").write_bytes(b"test artifact; never deserialized")
    policy = {"horizon_hours": 24, "availability_delay_hours": 2, "drop_mw": 22.77,
              "cost_fp": 1, "cost_fn": 4, "selected": {"threshold": .5}}
    manifest = {"training_events": 2, "training_rows": 8,
                "training_cutoff": "2026-07-31T06:00:00Z",
                "latest_train_label_available_at": "2026-07-31T05:00:00Z",
                "feature_columns": ["lag_1h"], "policy_contract_sha256": monitor.canonical_hash(policy),
                "model_sha256": monitor.digest(model_dir / "model.joblib")}
    (model_dir / "manifest.json").write_text(json.dumps(manifest))
    config = {"manifest_sha256": monitor.digest(model_dir / "manifest.json"),
              "model_sha256": manifest["model_sha256"], "policy_sha256": "test-policy",
              "policy": policy, "origin_start": "2026-07-31T06:00:00Z",
              "origin_end": "2026-07-31T07:00:00Z"}
    db = tmp_path / "ledger.sqlite"
    cutoff = "2026-08-01T09:00:00Z"
    with sqlite3.connect(db) as con:
        con.executescript(SCHEMA)
        con.execute("INSERT INTO configuration VALUES(1,?)", (json.dumps(config),))
        for offset, (p, generation) in enumerate(((.1, 90), (.8, 60))):
            origin = datetime(2026, 7, 31, 6+offset, tzinfo=timezone.utc)
            t0, target, available = [monitor.iso(t) for t in (origin, origin+timedelta(hours=24), origin+timedelta(hours=26))]
            request = {"forecast_origin": t0, "target_time": target, "history_end": monitor.iso(origin-timedelta(hours=2)),
                       "weather_latest_available_at": monitor.iso(origin-timedelta(hours=6)), "features": {"lag_1h": 100.0}}
            response = {"model_sha256": manifest["model_sha256"], "policy_sha256": "test-policy",
                        "forecast_origin": t0, "target_time": target, "p_event": p, "threshold": .5,
                        "alarm": p >= .5, "event_generation_at_or_below_mwmed": 77.23}
            con.execute("INSERT INTO predictions VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (t0, target, available, monitor.canonical_hash(request), json.dumps(request), json.dumps(response),
                         p, .5, int(p >= .5), 77.23, "2026-10-05T00:00:00Z"))
            y = int(generation <= 77.23)
            con.execute("INSERT INTO assessments VALUES(?,?,?,?,?,?,?)", (cutoff,t0,"observed",generation,y,(p-y)**2,0.0))
    rules = {"schema_version": "1.0", "min_observed": 168, "max_missing_observations": 0,
             "brier_relative_tolerance": .1}
    return db, model_dir, rules, cutoff


def test_normal_is_not_performance_approval(case):
    result = monitor.evaluate(*case)
    assert result["integrity"]["status"] == "pass"
    assert result["data"]["status"] == "ok"
    assert result["performance"]["status"] == "insufficient_evidence"
    assert result["action"]["code"] == "collect_evidence"
    assert result["performance"]["metrics"]["brier"] == pytest.approx(.025)
    assert result["performance"]["metrics"]["baseline_brier"] == pytest.approx(.3125)


def test_faults_have_distinct_actions_and_original_is_preserved(case, tmp_path):
    before = monitor.digest(case[0])
    result = monitor.exercise(*case, tmp_path / "reports")
    assert result["missing_observation"] == "investigate_data"
    assert result["changed_probability"] == "repair_record"
    assert result["missing_assessment"] == "repair_record"
    assert monitor.digest(case[0]) == before
    corrupted = json.loads((tmp_path / "reports/changed_probability/monitor.json").read_text())
    assert corrupted["performance"]["metrics"] is None


def test_waiting_labels_are_not_missing_observations(case):
    db, model, rules, _ = case
    early = "2026-08-01T07:00:00Z"
    with sqlite3.connect(db) as con:
        con.execute("UPDATE assessments SET as_of=?,status='awaiting_label',target_generation=NULL,event_drop=NULL,brier=NULL,cost=NULL",(early,))
    result = monitor.evaluate(db,model,rules,early)
    assert result["data"]["awaiting_label"] == 2
    assert result["data"]["missing_observation"] == 0
    assert result["data"]["status"] == "ok"
    assert result["performance"]["metrics"]["brier"] is None


def test_altered_model_is_integrity_failure(case):
    (case[1] / "model.joblib").write_bytes(b"changed")
    result = monitor.evaluate(*case)
    assert result["action"]["code"] == "repair_record"
    assert any(i["code"] == "model_identity" for i in result["integrity"]["issues"])


def test_future_label_is_rejected(case):
    db, model, rules, _ = case
    early = "2026-08-01T07:00:00Z"
    with sqlite3.connect(db) as con:
        con.execute("UPDATE assessments SET as_of=?", (early,))
    result = monitor.evaluate(db,model,rules,early)
    assert result["integrity"]["status"] == "fail"
    assert any(i["code"] == "label_used_early" for i in result["integrity"]["issues"])


def test_low_sample_rule_can_be_exercised_without_claiming_significance(case):
    db,model,rules,cutoff = case
    rules = {**rules, "min_observed": 2}
    result = monitor.evaluate(db,model,rules,cutoff)
    assert result["performance"]["status"] == "within_rule"
    assert result["performance"]["statistical_guarantee"] is False
    with sqlite3.connect(db) as con:
        for row in con.execute("SELECT forecast_origin,response_json,p_event FROM predictions").fetchall():
            origin,response,p = row
            p = 1-p
            response = json.loads(response)
            response.update(p_event=p,alarm=p>=.5)
            con.execute("UPDATE predictions SET p_event=?,alarm=?,response_json=? WHERE forecast_origin=?",
                        (p,int(p>=.5),json.dumps(response),origin))
            y = con.execute("SELECT event_drop FROM assessments WHERE forecast_origin=?",(origin,)).fetchone()[0]
            cost = 1 if y == 0 else 4
            con.execute("UPDATE assessments SET brier=?,cost=? WHERE forecast_origin=?",((p-y)**2,cost,origin))
    result = monitor.evaluate(db,model,rules,cutoff)
    assert result["performance"]["status"] == "review"
    assert result["action"]["code"] == "review_model"
    assert result["automatic_retraining"] is False
