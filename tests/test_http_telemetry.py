"""Contratos relevantes: resposta, erro, tempo e identidade da requisição."""
import json

import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from renewable_forecast.http_telemetry import HttpTelemetry, JsonlWriter, LabFaults
from renewable_forecast.service_exercise import summarize


class Payload(BaseModel):
    value: float


def fixture_app(path, *, faults=False):
    app = FastAPI()

    @app.post("/predict-decision")
    async def predict(payload: Payload):
        return {"p_event": payload.value}

    @app.get("/unexpected-error")
    async def fail():
        raise RuntimeError("falha para conferir observação de exceções")

    return HttpTelemetry(LabFaults(app, faults), JsonlWriter(path),
                         model_sha256="a" * 64, policy_sha256="b" * 64)


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_success_and_validation_error_correlate_without_storing_body(tmp_path):
    path = tmp_path / "http.jsonl"
    with TestClient(fixture_app(path)) as client:
        valid = client.post("/predict-decision?private=omit", json={"value": .2})
        invalid = client.post("/predict-decision", json={"wrong": 1})
    records = read(path)
    assert [r["status_code"] for r in records] == [200, 422]
    assert [r["request_id"] for r in records] == [valid.headers["x-request-id"], invalid.headers["x-request-id"]]
    assert records[0]["request_id"] != records[1]["request_id"]
    assert all(r["route"] == "/predict-decision" and r["response_complete"] and r["duration_ms"] >= 0 for r in records)
    assert "private" not in path.read_text() and "wrong" not in path.read_text()


def test_unhandled_500_is_recorded_with_its_response_id(tmp_path):
    path = tmp_path / "http.jsonl"
    with TestClient(fixture_app(path), raise_server_exceptions=False) as client:
        response = client.get("/unexpected-error")
    record, = read(path)
    assert response.status_code == 500 and record["status_code"] == 500
    assert record["request_id"] == response.headers["x-request-id"]
    assert record["response_complete"] and record["error_type"] == "RuntimeError"


def test_simulation_requires_explicit_activation(tmp_path):
    path = tmp_path / "http.jsonl"
    with TestClient(fixture_app(path)) as client:
        response = client.post("/predict-decision", json={"value": .2}, headers={"X-Renewcast-Lab": "error"})
    assert response.status_code == 403
    assert read(path)[0]["fault_injection"] is None


def test_injected_latency_preserves_prediction_and_error_is_labelled(tmp_path):
    path = tmp_path / "http.jsonl"
    with TestClient(fixture_app(path, faults=True)) as client:
        slow = client.post("/predict-decision", json={"value": .2}, headers={"X-Renewcast-Lab": "slow"})
        error = client.post("/predict-decision", json={"value": .2}, headers={"X-Renewcast-Lab": "error"})
    rows = read(path)
    assert slow.json() == {"p_event": .2} and rows[0]["duration_ms"] >= 700
    assert error.status_code == 500 and error.json()["simulated"] is True
    assert [r["fault_injection"] for r in rows] == ["slow", "error"]


def test_denominators_rejections_and_success_latency_are_separate():
    frame = pd.DataFrame({"phase": ["mixed"] * 4, "status_code": [200, 200, 422, 500],
                          "duration_ms": [10., 100., 1., 1.], "client_duration_ms": [11., 101., 2., 2.]})
    row, = summarize(frame)
    assert row["eligible_requests"] == 3 and row["rejected_4xx"] == 1
    assert row["server_error_rate"] == pytest.approx(1 / 3)
    assert row["p95_success_ms"] == pytest.approx(95.5)
    assert row["action"] == "review_service"


def test_only_422_means_undefined_service_metrics():
    frame = pd.DataFrame({"phase": ["invalid_payload"], "status_code": [422], "duration_ms": [1.], "client_duration_ms": [2.]})
    row, = summarize(frame)
    assert row["server_error_rate"] is None and row["p95_success_ms"] is None
    assert row["action"] == "inspect_rejections"
