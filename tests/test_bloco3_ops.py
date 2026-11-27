from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from renewable_forecast.bloco3_ops import Jsonl, ShadowLedger, create_local_app, drift_report


HASH = "a"*64


def emission():
    return dict(origin="2026-06-01T00:00:00+00:00", target_time="2026-06-02T00:00:00+00:00",
                source_event_time="2026-05-31T22:00:00+00:00", source_arrived_at="2026-05-31T23:59:00+00:00",
                source_vintage="2026-05-31T23:59:00+00:00", source_sha256=HASH, prediction=10.,
                trace_id="trace-1", replay_clock="2026-06-01T00:00:00+00:00")


def test_live_historical_emission_and_unverified_contract_are_rejected(tmp_path):
    with pytest.raises(ValueError, match="M04"):
        ShadowLedger(tmp_path/"not_created", model_sha256=HASH, mode="live")
    assert not (tmp_path/"not_created").exists()
    live = ShadowLedger(tmp_path/"live", model_sha256=HASH, mode="live", source_contract_verified=True)
    args = emission()
    args.pop("replay_clock")
    with pytest.raises(ValueError, match="origin"):
        live.emit(**args)


@pytest.mark.parametrize("field,value,reason", [
    ("source_arrived_at", "2026-06-01T00:01:00+00:00", "not_available"),
    ("source_vintage", "2026-06-01T00:01:00+00:00", "not_available"),
    ("source_event_time", "2026-05-31T20:00:00+00:00", "stale"),
    ("origin", "2026-06-01T00:00:00", "timezone"),
    ("target_time", "2026-06-03T00:00:00+00:00", "horizon")])
def test_ledger_rejects_causal_violations(tmp_path, field, value, reason):
    ledger = ShadowLedger(tmp_path/"journal", model_sha256=HASH)
    with pytest.raises(ValueError, match=reason):
        ledger.emit(**{**emission(), field: value})


def test_restart_restores_emission_then_target_and_rejects_duplicate(tmp_path):
    path = tmp_path/"journal"
    ledger = ShadowLedger(path, model_sha256=HASH)
    first = ledger.emit(**emission())
    restored = ShadowLedger(path, model_sha256=HASH)
    assert restored.emissions[first["origin"]] == first
    args = dict(origin=first["origin"], target_time=first["target_time"], value=11.,
                arrived_at="2026-06-02T02:00:00+00:00", source_vintage="2026-06-02T02:00:00+00:00",
                source_sha256=HASH, observed_at="2026-06-02T02:00:00+00:00")
    with pytest.raises(ValueError, match="not_available"):
        restored.reconcile(**{**args, "observed_at": "2026-06-02T01:00:00+00:00"})
    result = restored.reconcile(**args)
    assert result["label_delay_hours"] == 2
    assert result["absolute_error"] == 1
    assert result["mode"] == "replay"
    restored_again = ShadowLedger(path, model_sha256=HASH)
    with pytest.raises(ValueError, match="duplicate"):
        restored_again.emit(**emission())
    with pytest.raises(ValueError, match="duplicate"):
        restored_again.reconcile(**args)
    with pytest.raises(ValueError, match="identity"):
        ShadowLedger(path, model_sha256="b"*64)


def test_drift_distinguishes_input_quality_and_performance():
    protocol = dict(min_samples=20, mean_shift_reference_sd=1.5, mae_ratio=1.5,
                    mae_absolute_increase_mw=10, max_missing_fraction=.05,
                    max_label_delay_hours=6, false_alert_budget="manual one investigation/window")
    reference = np.arange(24.)
    args = dict(reference=reference, current=reference, reference_errors=np.ones(24),
                current_errors=np.ones(24), missing_fraction=0, label_delay_hours=2, protocol=protocol)
    same = drift_report(**args)
    assert same["classification"] == "no_alarm"
    shifted = drift_report(**{**args, "current": reference+100})
    assert shifted["input_distribution_alarm"] and not shifted["performance_alarm"]
    bad_model = drift_report(**{**args, "current_errors": np.ones(24)*30})
    assert bad_model["performance_alarm"] and not bad_model["input_distribution_alarm"]
    late = drift_report(**{**args, "label_delay_hours": 12})
    assert late["classification"] == "investigate_quality_first"
    assert not late["automatic_retrain"] and not late["automatic_promotion"]


class FakeModel:
    def predict(self, frame):
        return np.asarray(frame["lag_1h"])


def test_asgi_rejects_non_loopback_even_with_valid_key(tmp_path):
    import asyncio
    key = "f"*64
    log = tmp_path/"http.jsonl"
    app = create_local_app(FakeModel(), ["lag_1h"], {"version": "1"}, key, Jsonl(log))
    messages = []
    async def receive():
        return {"type": "http.request", "body": b""}
    async def send(message):
        messages.append(message)
    asyncio.run(app({"type": "http", "method": "GET", "path": "/health",
                     "headers": [(b"x-api-key", key.encode())], "client": ("10.1.1.1", 1),
                     "http_version": "1.1", "query_string": b""}, receive, send))
    assert messages[0]["status"] == 403
    content = log.read_text()
    assert key not in content and "10.1.1.1" not in content
    assert json.loads(content)["status"] == 403
