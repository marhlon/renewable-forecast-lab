"""Controles locais do bloco 3. Não habilita produção nem fontes externas.

O registro MLflow é exercitado pelo runner. Este módulo contém o serviço
loopback e contratos de coleta/reconciliação, separando replay de shadow real.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone, timedelta
import hashlib
import hmac
import json
import math
from pathlib import Path
import threading
import time
import uuid

import numpy as np
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc(value):
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("explicit_timezone_required")
    return result.astimezone(timezone.utc)


class Jsonl:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()

    def append(self, record):
        with self.lock, self.path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")


def create_local_app(model, features, identity, key, telemetry, *, max_body=8192,
                     rate=1000, rate_window=1.0):
    """ASGI; token nunca é registrado, corpos limitados mesmo sem Content-Length.

    O runner fixa o socket em 127.0.0.1. A validação do peer evita aceitar
    acidentalmente uma implantação pública; cabeçalhos de proxy são ignorados.
    """
    if len(key) < 32 or max_body < 1 or rate < 1 or rate_window <= 0:
        raise ValueError("invalid_security_configuration")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    expected = tuple(features)
    slots = deque()
    lock = threading.Lock()

    @app.get("/health")
    def health():
        return {"status": "ready", "scope": "local_engineering", **identity}

    @app.post("/predict")
    async def predict(request: Request):
        try:
            payload = await request.json()
            values = payload["features"]
            if set(payload) != {"features"} or not isinstance(values, dict) or set(values) != set(expected):
                raise ValueError
            if any(isinstance(values[k], bool) or not isinstance(values[k], (int, float)) or
                   not math.isfinite(values[k]) for k in expected):
                raise ValueError
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            return JSONResponse({"detail": "invalid_feature_contract"}, 422)
        frame = pd.DataFrame([[float(values[k]) for k in expected]], columns=expected)
        prediction = float(np.asarray(model.predict(frame)).ravel()[0])
        if not math.isfinite(prediction):
            return JSONResponse({"detail": "nonfinite_model_output"}, 503)
        return {"prediction": prediction, **identity}

    class Guard:
        async def __call__(self, scope, receive, send):
            if scope["type"] != "http":
                return await app(scope, receive, send)
            start = time.perf_counter()
            request_id = uuid.uuid4().hex
            status, size = 500, 0
            headers = dict(scope.get("headers", []))

            async def respond(code, detail):
                await JSONResponse({"detail": detail}, code)(scope, receive, instrument)

            async def instrument(message):
                nonlocal status
                if message["type"] == "http.response.start":
                    status = message["status"]
                    message = {**message, "headers": list(message.get("headers", [])) +
                               [(b"x-request-id", request_id.encode())]}
                await send(message)

            try:
                if (scope.get("client") or ("",))[0] != "127.0.0.1":
                    return await respond(403, "loopback_only")
                supplied = headers.get(b"x-api-key", b"")
                if not hmac.compare_digest(supplied, key.encode("ascii")):
                    return await respond(401, "unauthorized")
                with lock:
                    now = time.monotonic()
                    while slots and now - slots[0] >= rate_window:
                        slots.popleft()
                    limited = len(slots) >= rate
                    if not limited:
                        slots.append(now)
                if limited:
                    return await respond(429, "request_limit")
                declared = headers.get(b"content-length")
                if declared is not None:
                    try:
                        length = int(declared)
                    except ValueError:
                        return await respond(400, "invalid_content_length")
                    if length < 0 or length > max_body:
                        return await respond(413, "request_too_large")
                chunks = []
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    chunk = message.get("body", b"")
                    size += len(chunk)
                    if size > max_body:
                        return await respond(413, "request_too_large")
                    chunks.append(chunk)
                    if not message.get("more_body", False):
                        break
                consumed = False

                async def bounded_receive():
                    nonlocal consumed
                    if consumed:
                        return {"type": "http.disconnect"}
                    consumed = True
                    return {"type": "http.request", "body": b"".join(chunks), "more_body": False}

                await app(scope, bounded_receive, instrument)
            finally:
                # Exclusively server-generated identifiers, no user path/body/headers.
                telemetry.append({"recorded_at": datetime.now(timezone.utc).isoformat(),
                                  "request_id": request_id, "status": status, "bytes_read": size,
                                  "elapsed_ms": (time.perf_counter()-start)*1000, **identity})
    return Guard()


class ShadowLedger:
    """Append-only arrivals and emissions; live collection fails closed on PIT.

    Journal replay timestamps remain simulated; local received_at is always real.
    A caller cannot turn a historical input into a contemporaneous live emission.
    """
    def __init__(self, path, *, model_sha256, source_contract_verified=False,
                 mode="replay", max_age_hours=3):
        if mode not in {"replay", "live"}:
            raise ValueError("invalid_mode")
        if mode == "live" and not source_contract_verified:
            raise ValueError("M04_point_in_time_contract_not_verified")
        self.journal = Jsonl(path)
        self.model_sha256, self.mode = model_sha256, mode
        self.max_age = timedelta(hours=max_age_hours)
        self.emissions, self.targets = {}, {}
        if self.journal.path.exists():
            for line in self.journal.path.read_text(encoding="utf-8").splitlines():
                record = json.loads(line)
                if record.get("mode") != mode or record.get("model_sha256") != model_sha256:
                    raise ValueError("journal_identity_mismatch")
                origin = record["origin"]
                if record["kind"] == "emission":
                    if origin in self.emissions:
                        raise ValueError("journal_duplicate_emission")
                    self.emissions[origin] = record
                elif record["kind"] == "reconciliation":
                    if origin not in self.emissions or origin in self.targets:
                        raise ValueError("journal_invalid_reconciliation")
                    self.targets[origin] = record
                else:
                    raise ValueError("journal_unknown_record")

    def emit(self, *, origin, target_time, source_event_time, source_arrived_at,
             source_vintage, source_sha256, prediction, trace_id, replay_clock=None):
        origin, target = utc(origin), utc(target_time)
        event, arrival = utc(source_event_time), utc(source_arrived_at)
        now = datetime.now(timezone.utc)
        clock = utc(replay_clock) if self.mode == "replay" and replay_clock else now
        if self.mode == "replay" and replay_clock is None:
            raise ValueError("replay_clock_required")
        if not all(len(v) == 64 and all(c in "0123456789abcdef" for c in v)
                   for v in (source_sha256, self.model_sha256)):
            raise ValueError("sha256_required")
        vintage = utc(source_vintage)
        if arrival > clock or vintage > arrival or event > arrival:
            raise ValueError("input_not_available_at_emission")
        if target != origin + timedelta(hours=24) or clock < origin or clock-origin > timedelta(minutes=5):
            raise ValueError("invalid_origin_or_horizon")
        if event > origin or origin-event > self.max_age:
            raise ValueError("stale_or_future_input")
        if not math.isfinite(prediction) or not trace_id or origin.isoformat() in self.emissions:
            raise ValueError("invalid_or_duplicate_emission")
        record = {"kind": "emission", "mode": self.mode, "received_at": now.isoformat(),
                  "emission_clock": clock.isoformat(), "origin": origin.isoformat(),
                  "target_time": target.isoformat(), "source_event_time": event.isoformat(),
                  "source_arrived_at": arrival.isoformat(), "source_vintage": vintage.isoformat(),
                  "source_sha256": source_sha256, "prediction": prediction,
                  "model_sha256": self.model_sha256, "trace_id": trace_id}
        self.emissions[origin.isoformat()] = record
        self.journal.append(record)
        return record

    def reconcile(self, *, origin, target_time, value, arrived_at, source_vintage,
                  source_sha256, observed_at=None):
        origin, target, arrival = utc(origin), utc(target_time), utc(arrived_at)
        now = datetime.now(timezone.utc)
        clock = utc(observed_at) if self.mode == "replay" and observed_at else now
        emission = self.emissions.get(origin.isoformat())
        if not emission or target.isoformat() != emission["target_time"]:
            raise ValueError("unmatched_target")
        if arrival < target or arrival > clock or utc(source_vintage) > arrival:
            raise ValueError("target_not_available_at_reconciliation")
        if len(source_sha256) != 64 or any(c not in "0123456789abcdef" for c in source_sha256) or not math.isfinite(value) or origin.isoformat() in self.targets:
            raise ValueError("invalid_or_duplicate_target")
        record = {"kind": "reconciliation", "mode": self.mode, "received_at": now.isoformat(),
                  "observed_clock": clock.isoformat(), "origin": origin.isoformat(),
                  "target_time": target.isoformat(), "target_arrived_at": arrival.isoformat(),
                  "target_vintage": utc(source_vintage).isoformat(), "source_sha256": source_sha256,
                  "target": value, "absolute_error": abs(value-emission["prediction"]),
                  "label_delay_hours": (arrival-target).total_seconds()/3600,
                  "trace_id": emission["trace_id"], "model_sha256": self.model_sha256}
        self.targets[origin.isoformat()] = record
        self.journal.append(record)
        return record


def drift_report(reference, current, reference_errors, current_errors, *, missing_fraction,
                 label_delay_hours, protocol):
    """Predefined effect-size alarms; no statistical p-value or automatic retrain.

    A conservative screening protocol calls for human investigation. It does not
    promise a statistical false-positive bound or causal concept-drift diagnosis.
    """
    reference = np.asarray(reference, dtype=float)
    current = np.asarray(current, dtype=float)
    scale = max(float(np.std(reference)), 1e-12)
    shift = abs(float(np.mean(current)-np.mean(reference)))/scale
    old_mae, new_mae = float(np.mean(np.abs(reference_errors))), float(np.mean(np.abs(current_errors)))
    complete = min(len(reference), len(current), len(reference_errors), len(current_errors)) >= protocol["min_samples"]
    quality = missing_fraction > protocol["max_missing_fraction"] or label_delay_hours > protocol["max_label_delay_hours"]
    input_alarm = complete and shift > protocol["mean_shift_reference_sd"]
    performance = complete and new_mae > max(old_mae*protocol["mae_ratio"], old_mae+protocol["mae_absolute_increase_mw"])
    return {"n_reference": len(reference), "n_current": len(current), "enough_samples": complete,
            "mean_shift_reference_sd": shift, "reference_mae": old_mae, "current_mae": new_mae,
            "quality_or_delay_alarm": quality, "input_distribution_alarm": input_alarm,
            "performance_alarm": performance,
            "classification": "investigate_quality_first" if quality else "investigate_model" if performance else "investigate_input" if input_alarm else "no_alarm",
            "automatic_retrain": False, "automatic_promotion": False,
            "false_alert_budget": protocol["false_alert_budget"]}
