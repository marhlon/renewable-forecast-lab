"""Cliente local de inferencia Renewcast. Biblioteca padrao; nenhum modelo embarcado."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit

from politica_atualidade import POLICY_VERSION, avaliar_atualidade


VERSION = "1.1.0"
FIXED_FIELDS = ("mode", "model_id", "model_sha256", "manifest_sha256", "policy_id", "policy_sha256",
                "method", "drop_threshold_mwmed", "threshold", "feature_count", "estimator_executed",
                "model_retrained", "capacity_enforced_at_runtime", "availability_is_assumed")
EXIT_CODES = {"alarm": 0, "no_alarm": 0, "rejected": 2,
              "unavailable": 3, "invalid_response": 4, "invalid_input": 5,
              "presentation_blocked": 7}


def reject_constant(value):
    raise ValueError(f"JSON nao finito: {value}")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=reject_constant)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def instant(value):
    if not isinstance(value, str):
        raise ValueError("Data deve ser texto ISO 8601 com fuso.")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Data sem fuso.")
    return parsed.astimezone(timezone.utc)


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Numero ausente ou nao finito.")
    return float(value)


def validar_resposta(response, request, contract):
    """HTTP 200 so vira decisao se identidade, relogios e regra coincidirem."""
    if not isinstance(response, dict):
        raise ValueError("Resposta nao e um objeto JSON.")
    for key, expected in contract["fixed_response"].items():
        if key not in response or type(response[key]) is not type(expected) or response[key] != expected:
            raise ValueError(f"Contrato divergente: {key}.")
    for key in ("forecast_origin", "target_time", "history_end", "weather_latest_available_at"):
        if instant(response[key]) != instant(request[key]):
            raise ValueError(f"Resposta pertence a outro pedido: {key}.")
    p = number(response["p_event"])
    threshold = number(response["threshold"])
    if not 0 <= p <= 1 or not 0 <= threshold <= 1:
        raise ValueError("Probabilidade/limiar fora de [0,1].")
    if type(response["alarm"]) is not bool or response["alarm"] != (p >= threshold):
        raise ValueError("Alarme inconsistente com p >= threshold.")
    latest = number(request["features"]["lag_1h"])
    for key, expected in (
        ("last_available_generation", latest),
        ("event_generation_at_or_below_mwmed", latest - number(response["drop_threshold_mwmed"])),
    ):
        if not math.isclose(number(response[key]), expected, rel_tol=0, abs_tol=1e-9):
            raise ValueError(f"Referencia do evento inconsistente: {key}.")
    return "alarm" if response["alarm"] else "no_alarm"


def consultar(url, request, contract, timeout):
    target = urlsplit(url)
    if (target.scheme != "http" or target.hostname not in ("127.0.0.1", "localhost")
            or target.username or target.password or target.query or target.fragment
            or target.path not in ("", "/")):
        raise ValueError("Use a origem local http://127.0.0.1:PORTA, sem caminho.")
    body = json.dumps(request, allow_nan=False).encode("utf-8")
    conn = http.client.HTTPConnection(target.hostname, target.port or 80, timeout=timeout)
    started = time.perf_counter()
    status = None
    try:
        conn.request("POST", "/predict-decision", body=body,
                     headers={"Content-Type": "application/json", "Accept": "application/json"})
        reply = conn.getresponse()
        status = reply.status
        raw = reply.read(1_000_001)
    except (OSError, http.client.HTTPException) as exc:
        return {"state": "unavailable", "http_status": status, "response": None,
                "detail": f"{type(exc).__name__}: {exc}",
                "http_elapsed_ms": 1000 * (time.perf_counter() - started)}
    finally:
        conn.close()
    elapsed = 1000 * (time.perf_counter() - started)
    result = {"http_status": status, "response": None, "http_elapsed_ms": elapsed}
    if 400 <= status < 500:
        return {**result, "state": "rejected", "detail": "API recusou o pedido; conferir entrada e contrato."}
    if status >= 500:
        return {**result, "state": "unavailable", "detail": "API retornou falha do servidor."}
    if status != 200 or len(raw) > 1_000_000:
        return {**result, "state": "invalid_response", "detail": "Status ou tamanho de resposta inesperado."}
    try:
        response = json.loads(raw, parse_constant=reject_constant)
        state = validar_resposta(response, request, contract)
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        return {**result, "state": "invalid_response", "detail": str(exc)}
    return {**result, "state": state, "response": response, "detail": "Contrato conferido; inferencia de desenvolvimento."}


def aplicar_atualidade(result, *, mode, max_age, now):
    """Recebe resposta já validada; o relógio é fornecido pela borda da aplicação."""
    if result["state"] not in ("alarm", "no_alarm"):
        return {**result, "presentation": None, "audit_response": None}
    response = result["response"]
    decision = avaliar_atualidade(
        instant(response["forecast_origin"]), instant(response["target_time"]), now,
        mode=mode, max_age=max_age,
    )
    presentation = {
        "policy_version": POLICY_VERSION, "mode": mode,
        "evaluated_at_utc": now.astimezone(timezone.utc).isoformat(),
        "max_age_seconds": max_age.total_seconds(), **decision,
        "operational_policy_approved": False,
    }
    if not decision["allowed"]:
        return {**result, "state": "presentation_blocked", "response": None,
                "audit_response": response, "presentation": presentation,
                "detail": decision["reason"] + " Resposta preservada somente para auditoria."}
    detail = ("REPRODUCAO HISTORICA: esta resposta nao representa uma previsao atual."
              if mode == "historical_replay" else
              "Atualidade conferida; o modelo permanece de desenvolvimento, sem aprovacao operacional.")
    return {**result, "detail": detail, "presentation": presentation, "audit_response": None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Origem local da API, ex.: http://127.0.0.1:8000")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--presentation-mode", required=True,
                        choices=("historical_replay", "operational"),
                        help="Contexto de apresentação; não altera o modo nem a aprovação do modelo.")
    parser.add_argument("--max-age-hours", type=float, default=2.0,
                        help="Idade máxima didática da origem para apresentação (padrão: 2h).")
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("timeout deve ser finito e positivo.")
    if not math.isfinite(args.max_age_hours) or args.max_age_hours < 0:
        parser.error("max-age-hours deve ser finito e não negativo.")
    try:
        max_age = timedelta(hours=args.max_age_hours)
    except OverflowError:
        parser.error("max-age-hours excede a duração suportada.")
    output = args.output.resolve()
    if output in (args.request.resolve(), args.contract.resolve()):
        parser.error("A saida nao pode substituir pedido ou contrato.")
    if output.exists():
        parser.error("A saida ja existe. Escolha outro nome para preservar a consulta anterior.")
    record = {"schema": "renewcast-client-receipt-v2", "client_version": VERSION,
              "issued_at_utc": datetime.now(timezone.utc).isoformat(), "url": args.url,
              "frozen": bool(getattr(sys, "frozen", False)), "executable": sys.executable,
              "working_directory": str(Path.cwd()), "conda_active": bool(os.environ.get("CONDA_PREFIX")),
              "pythonpath_present": bool(os.environ.get("PYTHONPATH")),
              "request_sha256": None, "contract_sha256": None,
              "requested_presentation_mode": args.presentation_mode,
              "presentation": None, "audit_response": None}
    try:
        request, contract = read_json(args.request), read_json(args.contract)
        record.update(request_sha256=sha(args.request), contract_sha256=sha(args.contract))
        if (not isinstance(request, dict) or not isinstance(contract, dict)
                or contract.get("schema") != "renewcast-client-contract-v1"
                or not isinstance(contract.get("fixed_response"), dict)
                or set(contract["fixed_response"]) != set(FIXED_FIELDS)):
            raise ValueError("Pedido ou contrato local invalido.")
        if request.get("conjunto") != contract.get("conjunto") or not contract.get("conjunto"):
            raise ValueError("Pedido e contrato pertencem a conjuntos diferentes.")
        result = consultar(args.url, request, contract, args.timeout)
        # O relógio real é lido depois do HTTP. A CLI não permite falsificar --now.
        try:
            result = aplicar_atualidade(result, mode=args.presentation_mode,
                                       max_age=max_age, now=datetime.now(timezone.utc))
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            result = {**result, "state": "invalid_response", "response": None,
                      "presentation": None, "audit_response": None,
                      "detail": f"Relógios incompatíveis com a política de apresentação: {exc}"}
    except (OSError, ValueError, TypeError) as exc:
        result = {"state": "invalid_input", "http_status": None, "response": None, "detail": str(exc)}
    record.update(result)
    code = EXIT_CODES[record["state"]]
    record["exit_code"] = code
    output.parent.mkdir(parents=True, exist_ok=True)
    # Criacao exclusiva: uma falha nunca recicla o JSON de sucesso anterior.
    with output.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    # O arquivo retém a resposta bloqueada para auditoria; o console não a anuncia.
    console_record = {key: value for key, value in record.items() if key != "audit_response"}
    print(json.dumps(console_record, ensure_ascii=True, indent=2, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
