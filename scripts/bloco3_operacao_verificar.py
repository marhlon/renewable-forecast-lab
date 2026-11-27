"""Verificação repetível dos recibos locais M06 sem executar nova carga/treino."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "notebooks")]
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
os.environ.setdefault("OMP_NUM_THREADS", "2")
from renewable_forecast.bloco3_ops import digest


def verify():
    from datetime import datetime, timezone
    import joblib
    import mlflow
    import numpy as np
    import pandas as pd
    from mlflow.tracking import MlflowClient
    from threadpoolctl import threadpool_limits

    base = ROOT / "reports/fechamento_m00_m09/bloco3_engenharia"
    manifest = json.loads((base / "M06-03/manifesto_operacao_local.json").read_text(encoding="utf-8"))
    mismatches = [record["path"] for record in manifest["artifacts"] if digest(ROOT / record["path"]) != record["sha256"]]
    if mismatches:
        raise AssertionError(f"artifact_hash_mismatch:{mismatches}")
    registry = json.loads((base / "M06-03/registry_mlflow.json").read_text(encoding="utf-8"))
    bundle_identity = registry["model_identity"]
    if digest(ROOT / bundle_identity["path"]) != bundle_identity["sha256"]:
        raise AssertionError("bundle_identity_mismatch")
    tracking = "sqlite:///" + (base / "M06-03/registry_run_02/mlflow_registry.sqlite").resolve().as_posix()
    mlflow.set_tracking_uri(tracking)
    mlflow.set_registry_uri(tracking)
    client = MlflowClient(tracking_uri=tracking, registry_uri=tracking)
    resolved = client.get_model_version_by_alias(registry["registered_model"], "active")
    if str(resolved.version) != registry["active_version"]:
        raise AssertionError("active_alias_mismatch")
    X = pd.read_csv(ROOT / registry["input_identity"]["path"])
    with threadpool_limits(limits=2):
        bundle = joblib.load(ROOT / bundle_identity["path"])
        expected = bundle["model"].predict(X)
        loaded = mlflow.pyfunc.load_model(f"models:/{registry['registered_model']}@active")
        actual = loaded.predict(X)
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-10)
    security = json.loads((base / "M06-07/resultado.json").read_text(encoding="utf-8"))
    replay = json.loads((base / "M06-04/resultado.json").read_text(encoding="utf-8"))
    assert security["all_passed"] and not security["secret_in_log"]
    assert replay["live_guard_rejected"] and replay["all_counterexamples_rejected"] and replay["live_emissions"] == 0
    allowed = {"recorded_at", "request_id", "status", "bytes_read", "elapsed_ms", "registry_model", "version", "bundle_sha256"}
    for line in (base / "M06-07/http_telemetry.jsonl").read_text(encoding="utf-8").splitlines():
        assert set(json.loads(line)) == allowed
    drift = pd.read_csv(base / "M06-06/drift.csv").set_index("case")
    assert drift.loc["no_change", "classification"] == "no_alarm"
    assert drift.loc["input_shift_only", "input_distribution_alarm"]
    assert not drift.loc["input_shift_only", "performance_alarm"]
    assert drift.loc["performance_only", "performance_alarm"]
    assert not drift.loc["performance_only", "input_distribution_alarm"]
    assert drift.loc["label_delay", "quality_or_delay_alarm"]
    result = {"verified_at": datetime.now(timezone.utc).isoformat(), "artifacts_verified": len(manifest["artifacts"]),
              "active_version": str(resolved.version), "registered_versions": registry["versions"],
              "inference_max_difference": float(np.max(np.abs(actual-expected))),
              "security_and_replay_controls_passed": True, "drift_counterexamples_passed": True,
              "live_shadow_or_cloud_proven": False}
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    verify()
