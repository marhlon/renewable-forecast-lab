"""Contratos de ativação com os artefatos reais já existentes no projeto."""
import json
from pathlib import Path
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sklearn.ensemble import HistGradientBoostingClassifier

from renewable_forecast.event_registry import (
    RegistryConflict, active_version, connection, initialize, register_version,
    rollback, switch_version,
)
from renewable_forecast.registry_service import registered_app

PROJECT = Path(__file__).resolve().parents[1]


@pytest.fixture
def registry(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("fit não pertence ao registro/inferência")
    monkeypatch.setattr(HistGradientBoostingClassifier, "fit", forbidden)
    old = PROJECT / "models/CJU_BA5EIGT/h24_event_batch_v1"
    new = PROJECT / "models/CJU_BA5EIGT/h24_event_api_v1"
    policy = PROJECT / "reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json"
    if not all((p / "model.joblib").is_file() for p in (old, new)) or not policy.is_file():
        pytest.skip("Estes contratos de integração exigem os dois artefatos locais de M06.")
    folder = initialize(tmp_path / "registry")
    register_version(folder, "v1", old, policy)
    register_version(folder, "v2", new, policy)
    switch_version(folder, "v1", expected_generation=0, reason="Fixture")
    return folder, new, policy


def test_alias_and_history_rollback_together_if_second_write_fails(registry):
    folder, _, _ = registry
    before = active_version(folder)
    with connection(folder, write=True) as con:
        con.execute("CREATE TRIGGER fail_alias BEFORE UPDATE ON aliases BEGIN SELECT RAISE(ABORT, 'controlled write failure'); END")
    with pytest.raises(sqlite3.IntegrityError, match="controlled write failure"):
        switch_version(folder, "v2", expected_generation=1, reason="Contraprova transacional")
    assert active_version(folder) == before
    with connection(folder) as con:
        assert con.execute("SELECT COUNT(*) FROM deployments").fetchone()[0] == 1


def test_competing_writers_cannot_both_commit_the_same_generation(registry):
    folder, _, _ = registry
    def attempt():
        try:
            switch_version(folder, "v2", expected_generation=1, reason="Dois operadores com a mesma leitura")
            return "committed"
        except RegistryConflict:
            return "rejected"
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(results) == ["committed", "rejected"]
    assert active_version(folder)["generation"] == 2
    with connection(folder) as con:
        assert con.execute("SELECT COUNT(*) FROM deployments").fetchone()[0] == 2


def test_modified_bytes_never_activate_or_overwrite_registered_version(registry):
    folder, new, policy = registry
    before = active_version(folder)
    with pytest.raises(RegistryConflict, match="outros bytes"):
        register_version(folder, "v1", new, policy)
    path = folder / "versions/v2/model.joblib"
    with path.open("ab") as stream:
        stream.write(b"tampered")
    with pytest.raises(ValueError, match="Integridade"):
        switch_version(folder, "v2", expected_generation=1, reason="Artefato adulterado")
    assert active_version(folder) == before


def test_aba_requires_restart_even_when_version_name_returns_to_v1(registry, tmp_path):
    folder, new, _ = registry
    payload = json.loads((new / "example_request.json").read_text())
    app = registered_app(folder, tmp_path / "requests.jsonl")
    with TestClient(app) as client:
        assert client.post("/predict-decision", json=payload).status_code == 200
        switch_version(folder, "v2", expected_generation=1, reason="Candidato")
        rollback(folder, expected_generation=2, reason="Restaurar anterior")
        assert active_version(folder)["version_id"] == "v1"
        response = client.post("/predict-decision", json=payload)
        assert response.status_code == 503
        assert response.headers["x-renewcast-generation"] == "1"
        assert client.get("/deployment").json()["desired"]["generation"] == 3
        # Liveness e readiness são contratos diferentes.
        assert client.get("/health").status_code == 200
