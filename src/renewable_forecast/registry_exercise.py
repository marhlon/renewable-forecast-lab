"""M06: v1 -> v2 -> rollback v1, com HTTP real e registro SQLite.

Usa dois artefatos existentes, inicia/encerra a API automaticamente e não treina.
Cada execução cria uma pasta própria; falhas injetadas ficam identificadas.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import socket
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid

import numpy as np
import pandas as pd
import uvicorn

from renewable_forecast.event_artifact import sha256
from renewable_forecast.event_registry import (
    RegistryConflict, active_version, connection, initialize, register_version,
    rollback, switch_version, verify_version,
)
from renewable_forecast.registry_service import registered_app

RELEASE = "2026.10.07-registry-exercise-1"
DEFAULT_OLD = Path("models/CJU_BA5EIGT/h24_event_batch_v1")
DEFAULT_NEW = Path("models/CJU_BA5EIGT/h24_event_api_v1")
DEFAULT_POLICY = Path("reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json")
DEFAULT_OUTPUT = Path("reports/registry/CJU_BA5EIGT/h24_event_registry_v1")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


@contextmanager
def running_server(app, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server, thread = None, None
    try:
        sock.bind(("127.0.0.1", port))
        actual_port = sock.getsockname()[1]
        config = uvicorn.Config(app, host="127.0.0.1", port=actual_port, workers=1, log_level="warning", access_log=False)
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
        thread.start()
        deadline = time.monotonic() + 20
        while not server.started:
            require(thread.is_alive() and time.monotonic() < deadline, "Servidor não iniciou em 20 segundos.")
            time.sleep(.05)
        yield f"http://127.0.0.1:{actual_port}"
    finally:
        if server:
            server.should_exit = True
        if thread:
            thread.join(timeout=20)
        sock.close()
        require(thread is None or not thread.is_alive(), "Servidor não encerrou corretamente.")


def http_call(base_url, path, *, run_id, payload=None, fault=None, phase="normal"):
    headers = {"Content-Type": "application/json", "X-Renewcast-Run": run_id, "X-Renewcast-Phase": phase}
    if fault:
        headers["X-Renewcast-Lab"] = fault
    data = None if payload is None else json.dumps(payload, allow_nan=False).encode()
    req = Request(base_url + path, data=data, headers=headers, method="GET" if data is None else "POST")
    start = time.perf_counter_ns()
    try:
        response = urlopen(req, timeout=15)
    except HTTPError as exc:
        response = exc
    with response:
        body = json.loads(response.read())
        return {
            "request_id": response.headers.get("X-Request-ID"), "status_code": response.code,
            "version_id": response.headers.get("X-Renewcast-Version"),
            "generation": int(response.headers["X-Renewcast-Generation"]),
            "activation_id": response.headers.get("X-Renewcast-Activation"),
            "bundle_sha256": response.headers.get("X-Renewcast-Bundle"),
            "client_duration_ms": (time.perf_counter_ns() - start) / 1e6, "body": body,
        }


def run_exercise(old_model, new_model, policy, output_root, *, port=0, threads=2):
    old_model, new_model, policy, output_root = map(Path, (old_model, new_model, policy, output_root))
    sources = {f"{label}/{name}": folder / name for label, folder in (("v1", old_model), ("v2", new_model))
               for name in ("model.joblib", "manifest.json", "example_request.json")}
    sources["policy"] = policy
    before = {name: sha256(path) for name, path in sources.items()}
    require(before["v1/model.joblib"] != before["v2/model.joblib"], "O exercício requer os dois artefatos distintos já produzidos.")
    # Pedido comum: emissão do exemplo mais recente, elegível nos dois modelos.
    payload = json.loads((new_model / "example_request.json").read_text(encoding="utf-8"))
    run_id = uuid.uuid4().hex
    output = output_root.resolve() / run_id
    output.mkdir(parents=True, exist_ok=False)
    registry = initialize(output / "registry")
    server_log = output / "server_requests.jsonl"
    rows, probes, responses, rejections = [], [], [], []
    versions = [register_version(registry, name, folder, policy, threads=threads)
                for name, folder in (("v1", old_model), ("v2", new_model))]
    repeat = register_version(registry, "v1", old_model, policy, threads=threads)
    require(repeat == versions[0], "Repetir registro alterou a identidade da versão.")
    for record in versions:
        print(f"Registrada {record['version_id']}; corte={record['training_cutoff']}; modelo={record['model_sha256'][:12]}", flush=True)

    def probe(url, step, expected):
        result = http_call(url, "/deployment", run_id=run_id)
        probes.append({"step": step, **result})
        require(result["status_code"] == expected, f"Readiness inesperada em {step}.")
        return result

    def predict(url, step, expected, *, fault=None):
        phase = "incident" if expected >= 500 else "normal"
        result = http_call(url, "/predict-decision", run_id=run_id, payload=payload, fault=fault, phase=phase)
        responses.append({"step": step, **result})
        body = result.pop("body")
        rows.append({"sequence": len(rows) + 1, "step": step, "phase": phase, "expected_status": expected,
                     **result, "requested_fault": fault, "p_event": body.get("p_event"),
                     "alarm": body.get("alarm"), "estimator_executed": body.get("estimator_executed"),
                     "response_model_sha256": body.get("model_sha256")})
        require(result["status_code"] == expected, f"Resposta inesperada em {step}: {body}")
        return result["request_id"]

    try:
        switch_version(registry, "v1", expected_generation=0, reason="Inicialização do exercício local", threads=threads)
        with running_server(registered_app(registry, server_log, threads=threads, lab_faults=True), port) as url:
            probe(url, "v1_loaded", 200)
            for _ in range(3):
                predict(url, "v1_before", 200)
            active_before = active_version(registry)
            try:
                switch_version(registry, "v2", expected_generation=0, reason="Contraprova: leitura desatualizada", threads=threads)
            except RegistryConflict as exc:
                rejections.append({"case": "stale_generation", "expected_generation": 0, "message": str(exc)})
            else:
                raise ValueError("Controle de concorrência aceitou uma geração antiga.")
            require(active_version(registry) == active_before, "Rejeição alterou o alias.")
            switch_version(registry, "v2", expected_generation=1, reason="Ativação técnica do candidato no laboratório; sem promoção estatística", threads=threads)
            probe(url, "v1_stale", 503)
            predict(url, "v1_stale", 503)
        print("Alias v2/g2: processo v1 recusou inferência até reiniciar.", flush=True)

        with running_server(registered_app(registry, server_log, threads=threads, lab_faults=True), port) as url:
            probe(url, "v2_loaded", 200)
            for _ in range(3):
                predict(url, "v2_ready", 200)
            incident_ids = [predict(url, "v2_injected_error", 500, fault="error") for _ in range(2)]
            rollback(registry, expected_generation=2, reason="Exercício: duas falhas HTTP 500 injetadas; restaurar versão anterior",
                     evidence_request_ids=incident_ids, threads=threads)
            probe(url, "v2_stale", 503)
            predict(url, "v2_stale", 503)
        print("Rollback registrado: v2/g2 -> v1/g3, com os dois request_ids do incidente.", flush=True)

        with running_server(registered_app(registry, server_log, threads=threads, lab_faults=True), port) as url:
            probe(url, "v1_restored", 200)
            for _ in range(3):
                predict(url, "v1_restored", 200)
    finally:
        pd.DataFrame(rows).to_csv(output / "client_requests.csv", index=False)
        write_json(output / "responses.json", responses)
        write_json(output / "deployment_probes.json", probes)
        write_json(output / "rejected_changes.json", rejections)

    client = pd.DataFrame(rows)
    records = [json.loads(line) for line in server_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    server = pd.DataFrame([r for r in records if r["http_method"] == "POST" and r["route"] == "/predict-decision"])
    require(len(client) == len(server) == 13, "Deveriam existir 13 inferências/tentativas conciliáveis.")
    require(client.request_id.is_unique and server.request_id.is_unique and set(client.request_id) == set(server.request_id), "IDs ausentes ou repetidos na conciliação.")
    joined = client.merge(server, on="request_id", validate="one_to_one", suffixes=("_client", ""))
    for column in ("phase", "status_code", "version_id", "generation", "activation_id", "bundle_sha256"):
        require(joined[column].eq(joined[column + "_client"]).all(), f"Cliente/servidor divergem em {column}.")
    require(joined.run_id.eq(run_id).all() and joined.response_complete.all(), "Run incorreto ou resposta incompleta.")
    success = joined.loc[joined.status_code.eq(200)]
    require(success.estimator_executed.eq(True).all(), "Sucesso sem execução confirmada do estimador.")
    require(success.response_model_sha256.eq(success.model_sha256).all(), "Resposta e log identificam modelos diferentes.")
    joined = joined.drop(columns=[c for c in joined if c.endswith("_client")])
    v1_before = joined.loc[joined.step.eq("v1_before")]
    restored = joined.loc[joined.step.eq("v1_restored")]
    require(np.allclose(restored.p_event, v1_before.p_event, rtol=0, atol=1e-12), "Rollback não restaurou as probabilidades do mesmo pedido.")
    require(restored.model_sha256.eq(before["v1/model.joblib"]).all(), "Rollback serviu outro modelo.")
    require(restored.generation.eq(3).all(), "Rollback reutilizou a geração antiga.")
    require({name: sha256(path) for name, path in sources.items()} == before, "Os artefatos de origem foram modificados.")
    for name in ("v1", "v2"):
        verify_version(registry, name)
    with connection(registry) as con:
        deployments = pd.read_sql_query("SELECT * FROM deployments ORDER BY generation", con)
        saved_versions = pd.read_sql_query("SELECT * FROM versions ORDER BY version_id", con)
    require(deployments.to_version.tolist() == ["v1", "v2", "v1"], "Histórico de ativação inesperado.")
    require(deployments.generation.tolist() == [1, 2, 3], "Gerações não avançaram exatamente uma vez por commit.")
    require(json.loads(deployments.iloc[-1].evidence_request_ids_json) == incident_ids, "Rollback não cita os IDs que dispararam a ação.")
    joined.to_csv(output / "requests.csv", index=False)
    deployments.to_csv(output / "deployments.csv", index=False)
    saved_versions.to_csv(output / "versions.csv", index=False)
    write_json(output / "common_request.json", payload)
    summary = joined.groupby(["step", "version_id", "generation", "status_code"], sort=False, as_index=False).agg(
        requests=("request_id", "size"), p_event=("p_event", "first"))
    summary.to_csv(output / "summary.csv", index=False)
    outputs = ["client_requests.csv", "server_requests.jsonl", "requests.csv", "responses.json", "deployment_probes.json",
               "rejected_changes.json", "deployments.csv", "versions.csv", "common_request.json", "summary.csv", "registry/registry.sqlite"]
    from renewable_forecast import event_registry, registry_service
    verification = {"verified": True, "run_id": run_id, "release": RELEASE,
        "source_sha256": before, "source_artifacts_unchanged": True, "models_retrained": False,
        "http_predictions_or_attempts": 13, "successful_predictions": 9,
        "injected_errors": 2, "expected_stale_process_rejections": 2,
        "deployment_probe_count": len(probes), "registered_versions": 2, "registration_idempotent": True,
        "committed_generations": [1, 2, 3], "stale_generation_rejected": True,
        "rollback_probability_restored": True, "rollback_model_restored": True,
        "final_active": active_version(registry), "rollback_evidence_request_ids": incident_ids,
        "output_sha256": {name: sha256(output / name) for name in outputs},
        "code_sha256": {"registry_exercise": sha256(Path(__file__)),
                        "event_registry": sha256(Path(event_registry.__file__)),
                        "registry_service": sha256(Path(registry_service.__file__))},
        "scope": "Local registry and restart/rollback exercise; intentional faults, historical common request, no new model-performance evaluation",
    }
    write_json(output / "verification.json", verification)
    pointer = output_root.resolve() / f".latest-{run_id}.json"
    write_json(pointer, {"run_id": run_id, "directory": str(output), "verification_sha256": sha256(output / "verification.json")})
    pointer.replace(output_root.resolve() / "latest_run.json")
    print(summary.to_string(index=False))
    print("Verificado: duas versões; três commits; 13 tentativas HTTP; rollback restaurou v1 com geração 3.")
    print("Falhas deliberadas de serviço não comparam a qualidade dos modelos.")
    print(f"Arquivos: {output}")
    return verification


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-model-dir", type=Path, default=DEFAULT_OLD)
    parser.add_argument("--new-model-dir", type=Path, default=DEFAULT_NEW)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--port", type=int, default=0, help="0 escolhe uma porta local livre em cada início.")
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args(argv)
    if args.threads < 1 or not 0 <= args.port <= 65535:
        parser.error("threads deve ser positivo; port deve estar entre 0 e 65535.")
    try:
        run_exercise(args.old_model_dir, args.new_model_dir, args.policy, args.output_dir, port=args.port, threads=args.threads)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"EXERCÍCIO INTERROMPIDO: {exc}\nExamine a execução parcial; latest_run.json não aponta para ela.\n")


if __name__ == "__main__":
    main()
