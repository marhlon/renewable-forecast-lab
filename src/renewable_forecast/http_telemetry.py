"""M06: telemetria HTTP por requisição, com falhas didáticas opcionais.

Mede tempo dentro da aplicação ASGI, até o último envio do corpo da resposta.
JSONL local para um processo; não é uptime, tracing distribuído ou benchmark.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from starlette.responses import JSONResponse

from renewable_forecast.decision_api import create_app
from renewable_forecast.event_artifact import sha256


RELEASE = "2026.10.05-http-telemetry-1"
PHASES = {"warmup", "normal", "invalid_payload", "incident"}


class JsonlWriter:
    """Append protegido entre threads; laboratório de um único processo."""
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        with self.path.open("a", encoding="utf-8"):
            pass

    def write(self, record):
        line = json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n"
        with self.lock, self.path.open("a", encoding="utf-8") as stream:
            stream.write(line)


class LabFaults:
    """Ativação explícita. Respostas 500 injetadas não executam o estimador."""
    def __init__(self, app, enabled=False):
        self.app, self.enabled = app, enabled

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        fault = headers.get(b"x-renewcast-lab", b"").decode("ascii", errors="replace")
        if fault:
            valid_route = scope["method"] == "POST" and scope["path"] == "/predict-decision"
            if not self.enabled or not valid_route or fault not in {"slow", "error"}:
                return await JSONResponse({"detail": "Simulação não habilitada ou inválida."}, 403)(scope, receive, send)
            scope["renewcast_fault"] = fault
            if fault == "error":
                return await JSONResponse({"detail": "Falha 500 injetada no exercício.", "simulated": True}, 500)(scope, receive, send)
            await asyncio.sleep(0.75)
        return await self.app(scope, receive, send)


class HttpTelemetry:
    """Intercepta envio ASGI, inclusive respostas 422/500 geradas pela aplicação."""
    def __init__(self, app, writer, *, model_sha256, policy_sha256):
        self.app, self.writer = app, writer
        self.model_sha256, self.policy_sha256 = model_sha256, policy_sha256

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        started = time.perf_counter_ns()
        timestamp = datetime.now(timezone.utc).isoformat()
        request_id = uuid.uuid4().hex  # gerado pelo servidor, não confiado ao cliente
        headers = dict(scope.get("headers", []))
        run_id = headers.get(b"x-renewcast-run", b"").decode("ascii", errors="replace")
        if not re.fullmatch(r"[0-9a-f]{32}", run_id):
            run_id = None
        phase = headers.get(b"x-renewcast-phase", b"").decode("ascii", errors="replace")
        phase = phase if phase in PHASES else "unclassified"
        status_code, completed_ns, error_type = None, None, None

        async def tracked_send(message):
            nonlocal status_code, completed_ns
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                message = {**message, "headers": [
                    (key, value) for key, value in message.get("headers", [])
                    if key.lower() != b"x-request-id"
                ] + [(b"x-request-id", request_id.encode("ascii"))]}
            await send(message)
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                completed_ns = time.perf_counter_ns()

        try:
            await self.app(scope, receive, tracked_send)
        except BaseException as exc:
            error_type = type(exc).__name__
            raise
        finally:
            record = {
                "schema_version": "1.0", "request_id": request_id,
                "received_at_utc": timestamp, "run_id": run_id, "phase": phase,
                "http_method": scope["method"],
                "route": scope.get("route").path if scope.get("route") else "<unmatched>",
                "status_code": status_code, "response_complete": completed_ns is not None,
                "duration_ms": ((completed_ns or time.perf_counter_ns()) - started) / 1e6,
                "error_type": error_type, "fault_injection": scope.get("renewcast_fault"),
                "model_sha256": self.model_sha256, "policy_sha256": self.policy_sha256,
            }
            # A falha de gravação fica explícita no stderr; a conciliação posterior
            # também reprova uma requisição que não possua seu registro de servidor.
            try:
                self.writer.write(record)
            except OSError:
                logging.exception("Falha ao gravar telemetria request_id=%s", request_id)


def observed_app(policy_path, model_dir, log_path, *, threads=2, lab_faults=False):
    app = create_app(Path(policy_path), Path(model_dir), threads)
    # A rota é anotada antes da injeção: 500 didático não chega ao roteador.
    class MarkRoute:
        def __init__(self, inner):
            self.inner = inner

        async def __call__(self, scope, receive, send):
            if scope["type"] == "http" and scope["path"] == "/predict-decision" and scope["method"] == "POST":
                scope["route"] = next(r for r in app.routes if getattr(r, "path", None) == "/predict-decision")
            return await self.inner(scope, receive, send)

    return HttpTelemetry(
        MarkRoute(LabFaults(app, enabled=lab_faults)), JsonlWriter(log_path),
        model_sha256=sha256(Path(model_dir) / "model.joblib"), policy_sha256=sha256(policy_path),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--lab-faults", action="store_true")
    args = parser.parse_args(argv)
    if args.threads < 1 or not 1 <= args.port <= 65535:
        parser.error("threads deve ser positivo; port deve estar entre 1 e 65535.")
    app = observed_app(args.policy, args.model_dir, args.log, threads=args.threads, lab_faults=args.lab_faults)
    uvicorn.run(app, host="127.0.0.1", port=args.port, workers=1)


if __name__ == "__main__":
    main()
