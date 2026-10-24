"""API local carregada pelo alias do registro; reinício aplica a nova versão."""
from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3

from fastapi.responses import JSONResponse
import uvicorn

from renewable_forecast.decision_api import create_app
from renewable_forecast.event_registry import active_version, verify_version
from renewable_forecast.http_telemetry import HttpTelemetry, JsonlWriter, LabFaults

RELEASE = "2026.10.07-registry-service-1"


def same_activation(loaded, desired):
    return desired is not None and all(loaded[key] == desired[key] for key in (
        "alias", "version_id", "generation", "activation_id", "bundle_sha256",
    ))


def registered_app(registry: Path, log_path: Path, *, threads=2, lab_faults=False):
    registry = Path(registry).resolve()
    loaded = active_version(registry)
    if loaded is None:
        raise ValueError("Ative uma versão antes de iniciar o serviço.")
    _, folder = verify_version(registry, loaded["version_id"])
    app = create_app(folder / "policy.json", folder, threads)

    @app.get("/deployment")
    async def deployment():
        try:
            desired = active_version(registry)
            verify_version(registry, loaded["version_id"])
            ready = same_activation(loaded, desired)
            reason = "loaded_matches_active" if ready else "restart_required"
        except (OSError, ValueError, sqlite3.Error) as exc:
            desired, ready, reason = None, False, type(exc).__name__
        return JSONResponse({"ready": ready, "reason": reason, "loaded": loaded, "desired": desired,
                             "mode": "development_registry"}, status_code=200 if ready else 503)

    class Guard:
        def __init__(self, inner):
            self.inner = inner

        async def __call__(self, scope, receive, send):
            if scope["type"] == "http":
                route = next((r for r in app.routes if getattr(r, "path", None) == scope["path"]), None)
                if route is not None:
                    scope["route"] = route
                if scope["path"] in {"/predict-decision", "/decisions"}:
                    try:
                        desired = active_version(registry)
                        ready = same_activation(loaded, desired)
                    except (OSError, ValueError, sqlite3.Error):
                        ready = False
                    if not ready:
                        return await JSONResponse({"detail": "loaded_version_is_not_active", "restart_required": True}, 503)(scope, receive, send)
            return await self.inner(scope, receive, send)

    class IdentityHeaders:
        def __init__(self, inner):
            self.inner = inner

        async def __call__(self, scope, receive, send):
            async def identity_send(message):
                if message["type"] == "http.response.start":
                    message = {**message, "headers": list(message.get("headers", [])) + [
                        (b"x-renewcast-version", loaded["version_id"].encode("ascii")),
                        (b"x-renewcast-generation", str(loaded["generation"]).encode("ascii")),
                        (b"x-renewcast-activation", loaded["activation_id"].encode("ascii")),
                        (b"x-renewcast-bundle", loaded["bundle_sha256"].encode("ascii")),
                    ]}
                await send(message)
            return await self.inner(scope, receive, identity_send)

    class Writer:
        def __init__(self):
            self.target = JsonlWriter(log_path)

        def write(self, record):
            self.target.write({**record, "version_id": loaded["version_id"],
                "generation": loaded["generation"], "activation_id": loaded["activation_id"],
                "bundle_sha256": loaded["bundle_sha256"]})

    return IdentityHeaders(HttpTelemetry(
        Guard(LabFaults(app, enabled=lab_faults)), Writer(),
        model_sha256=loaded["model_sha256"], policy_sha256=loaded["policy_sha256"],
    ))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args(argv)
    if args.threads < 1 or not 1 <= args.port <= 65535:
        parser.error("Porta ou número de threads inválido.")
    app = registered_app(args.registry, args.log, threads=args.threads)
    uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
