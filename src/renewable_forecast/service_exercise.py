"""M06: laboratório HTTP completo sobre o classificador já salvo.

Inicia servidor local em 8001, faz requisições, concilia logs e encerra o servidor.
20 normais; 5 rejeições de entrada; 20 de incidente (3 lentas e 2 falhas 500).
"""
from __future__ import annotations

import argparse
import copy
import json
import socket
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import uvicorn

from renewable_forecast.event_artifact import sha256
from renewable_forecast import http_telemetry
from renewable_forecast.http_telemetry import RELEASE, observed_app


DEFAULT_MODEL = Path("models/CJU_BA5EIGT/h24_event_batch_v1")
DEFAULT_POLICY = Path("reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json")
DEFAULT_OUTPUT = Path("reports/service/CJU_BA5EIGT/h24_event_telemetry_v1")
LATENCY_LIMIT_MS = 250.0
ERROR_RATE_LIMIT = 0.01


def require(condition, message):
    if not condition:
        raise ValueError(message)


def call(url, payload, run_id, phase, fault=None):
    headers = {"Content-Type": "application/json", "X-Renewcast-Run": run_id, "X-Renewcast-Phase": phase}
    if fault:
        headers["X-Renewcast-Lab"] = fault
    request = Request(url, data=json.dumps(payload, allow_nan=False).encode(), headers=headers, method="POST")
    start = time.perf_counter_ns()
    try:
        response = urlopen(request, timeout=15)
    except HTTPError as exc:
        response = exc  # uma resposta HTTP de erro ainda tem status, cabeçalhos e corpo
    with response:
        body = response.read()
        elapsed = (time.perf_counter_ns() - start) / 1e6
        return response.code, response.headers.get("X-Request-ID"), json.loads(body), elapsed


def summarize(frame, *, latency_limit_ms=LATENCY_LIMIT_MS, error_rate_limit=ERROR_RATE_LIMIT):
    rows = []
    for phase, group in frame.groupby("phase", sort=False):
        status = group["status_code"]
        successful = status.between(200, 299)
        rejected = status.between(400, 499)
        failed = status.between(500, 599)
        eligible = int(successful.sum() + failed.sum())
        error_rate = float(failed.sum() / eligible) if eligible else None
        durations = group.loc[successful, "duration_ms"]
        p95 = float(durations.quantile(.95, interpolation="linear")) if len(durations) else None
        action = "inspect_rejections" if not eligible else (
            "review_service" if error_rate > error_rate_limit or p95 is None or p95 > latency_limit_ms else "within_exercise_rule"
        )
        rows.append({
            "phase": phase, "requests": len(group), "success_2xx": int(successful.sum()),
            "rejected_4xx": int(rejected.sum()), "failed_5xx": int(failed.sum()),
            "eligible_requests": eligible, "server_error_rate": error_rate,
            "median_success_ms": float(durations.median()) if len(durations) else None,
            "p95_success_ms": p95, "slow_successes": int((durations > latency_limit_ms).sum()),
            "p95_client_success_ms": float(group.loc[successful, "client_duration_ms"].quantile(.95)) if len(durations) else None,
            "action": action,
        })
    return rows


def reconcile(client, log_path, run_id, model_hash):
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    server = pd.DataFrame([r for r in records if r["run_id"] == run_id and r["phase"] != "warmup"])
    client = pd.DataFrame([r for r in client if r["phase"] != "warmup"])
    require(not client.empty and not server.empty, "Faltam requisições ou telemetria.")
    require(client.request_id.notna().all() and not client.request_id.duplicated().any(), "IDs do cliente ausentes/duplicados.")
    require(not server.request_id.duplicated().any(), "IDs do servidor duplicados.")
    require(set(client.request_id) == set(server.request_id), "Cliente e servidor não possuem as mesmas requisições.")
    joined = client.merge(server, on="request_id", validate="one_to_one", suffixes=("_client", ""))
    require(joined.phase_client.eq(joined.phase).all(), "Fases divergentes.")
    require(joined.status_code_client.eq(joined.status_code).all(), "Status divergente entre cliente/servidor.")
    require(joined.response_complete.all(), "Existe resposta incompleta.")
    require(joined.http_method.eq("POST").all() and joined.route.eq("/predict-decision").all(), "Escopo de endpoint inválido.")
    require(joined.model_sha256.eq(model_hash).all(), "Modelo mudou entre requisições.")
    require(np.isfinite(joined.duration_ms).all() and joined.duration_ms.ge(0).all(), "Duração inválida.")
    require(joined.status_code.eq(joined.expected_status).all(), "Resposta diferente da prevista no exercício; examine client_requests.csv.")
    success = joined.loc[joined.status_code.eq(200)]
    require(success.estimator_executed.eq(True).all(), "Resposta 200 não confirma execução do estimador.")
    probabilities = success.p_event.to_numpy(dtype=float)
    require(np.isfinite(probabilities).all() and np.allclose(probabilities, probabilities[0], rtol=0, atol=1e-12),
            "O mesmo pedido produziu probabilidades diferentes; investigue antes de interpretar latência.")
    return joined.drop(columns=["phase_client", "status_code_client"])


def run_exercise(model_dir, policy, output_root, *, port=8001, threads=2):
    # Cada execução tem diretório próprio; não soma repetições como se fossem a mesma janela.
    run_id = uuid.uuid4().hex
    output = output_root / run_id
    tracked = {"model": model_dir / "model.joblib", "manifest": model_dir / "manifest.json",
               "request": model_dir / "example_request.json", "policy": policy}
    before = {key: sha256(path) for key, path in tracked.items()}
    payload = json.loads(tracked["request"].read_text(encoding="utf-8"))
    invalid = {**copy.deepcopy(payload), "p_event": 0.5}  # campo proibido na inferência
    output.mkdir(parents=True, exist_ok=False)
    log_path = output / "server_requests.jsonl"
    app = observed_app(policy, model_dir, log_path, threads=threads, lab_faults=True)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server, thread, client = None, None, []
    try:
        sock.bind(("127.0.0.1", port))
        config = uvicorn.Config(app, host="127.0.0.1", port=port, workers=1, log_level="warning", access_log=False)
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
        thread.start()
        deadline = time.monotonic() + 20
        while not server.started:
            require(thread.is_alive() and time.monotonic() < deadline, "Servidor não iniciou dentro de 20 segundos.")
            time.sleep(.05)
        url = f"http://127.0.0.1:{port}/predict-decision"
        schedule = [("warmup", None, payload, 200)]
        schedule += [("normal", None, payload, 200)] * 20
        schedule += [("invalid_payload", None, invalid, 422)] * 5
        schedule += [("incident", None, payload, 200)] * 15
        schedule += [("incident", "slow", payload, 200)] * 3
        schedule += [("incident", "error", payload, 500)] * 2
        for sequence, (phase, fault, body, expected) in enumerate(schedule):
            status, request_id, response, elapsed = call(url, body, run_id, phase, fault)
            if status == 200:
                require(response.get("model_sha256") == before["model"], "Servidor respondeu com outro modelo.")
            client.append({"sequence": sequence, "request_id": request_id, "phase": phase,
                "expected_status": expected, "status_code": status, "client_duration_ms": elapsed,
                "requested_fault": fault, "p_event": response.get("p_event"),
                "estimator_executed": response.get("estimator_executed")})
    finally:
        if server:
            server.should_exit = True
        if thread:
            thread.join(timeout=20)
        sock.close()
        pd.DataFrame(client).to_csv(output / "client_requests.csv", index=False)
    require(thread is not None and not thread.is_alive(), "Servidor não encerrou; execução não certificada.")
    joined = reconcile(client, log_path, run_id, before["model"])
    after = {key: sha256(path) for key, path in tracked.items()}
    require(before == after, "Artefatos do modelo/política foram alterados.")
    joined.to_csv(output / "requests.csv", index=False)
    rows = summarize(joined)
    summary = pd.DataFrame(rows)
    summary.to_csv(output / "summary.csv", index=False)
    verification = {
        "verified": True, "run_id": run_id, "release": RELEASE,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "requests_excluding_warmup": len(joined), "warmup_requests": 1,
        "all_statuses_as_planned": True, "request_id_join": "one_to_one",
        "all_successful_predictions_equal": True, "input_artifacts_unchanged": True,
        "model_retrained": False, "network": "loopback_http", "workers": 1,
        "request_pattern": "sequential repeated historical example; labelled lab faults",
        "model_sha256": before["model"], "policy_sha256": before["policy"],
        "input_sha256": before,
        "rules": {"status": "didactic", "p95_success_limit_ms": LATENCY_LIMIT_MS,
                  "max_server_error_rate": ERROR_RATE_LIMIT,
                  "error_denominator": "2xx + 5xx; 4xx tracked separately",
                  "p95_definition": "linear empirical quantile over successful responses"},
        "summary": rows,
        "output_sha256": {name: sha256(output / name) for name in (
            "requests.csv", "summary.csv", "server_requests.jsonl", "client_requests.csv")},
        "code_sha256": {"service_exercise": sha256(Path(__file__)),
                        "http_telemetry": sha256(Path(http_telemetry.__file__))},
        "scope": "instrumentation exercise, not throughput benchmark, live shadow, uptime or model-quality evaluation",
    }
    (output / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    (output_root / "latest_run.json").write_text(json.dumps({"run_id": run_id, "directory": str(output.resolve()),
        "verification_sha256": sha256(output / "verification.json")}, indent=2), encoding="utf-8")
    print(summary.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("\n45 requisições conciliadas; aquecimento separado; modelo preservado; servidor encerrado.")
    print("422 = rejeição de entrada; 500 = falha injetada; tempos são medições locais reais.")
    print(f"Arquivos: {output.resolve()}")
    return verification


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args(argv)
    if args.threads < 1 or not 1 <= args.port <= 65535:
        parser.error("threads deve ser positivo; port deve estar entre 1 e 65535.")
    try:
        run_exercise(args.model_dir, args.policy, args.output_dir, port=args.port, threads=args.threads)
    except (OSError, ValueError, KeyError, URLError) as exc:
        parser.exit(1, f"EXERCÍCIO INTERROMPIDO: {exc}\nNão houve aprovação desta execução.\n")


if __name__ == "__main__":
    main()
