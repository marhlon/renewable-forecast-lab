"""M06.1: envia uma probabilidade real do relatório e uma entrada inválida à API local."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/predictions.csv"
DEFAULT_OUTPUT = ROOT / "reports/service/CJU_BA5EIGT/h24_event_policy_v1"


def call_api(url: str, payload=None):
    data = None if payload is None else json.dumps(payload, allow_nan=False).encode("utf-8")
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read())
    except HTTPError as exc:
        return exc.code, json.loads(exc.read())
    except URLError as exc:
        raise RuntimeError("API inacessível. Mantenha o servidor aberto no outro terminal.") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args(argv)
    base_url = args.url.rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
        parser.error("Esta prática utiliza exclusivamente uma API HTTP local.")
    status, policy = call_api(base_url + "/policy")
    if status != 200:
        raise ValueError(f"Falha ao ler política: HTTP {status}: {policy}")
    source_sha = hashlib.sha256(args.input.read_bytes()).hexdigest()
    if source_sha != policy["source_predictions_sha256"]:
        raise ValueError("O relatório não corresponde à fonte registrada na política.")
    with args.input.open(encoding="utf-8", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if r["method"] == policy["selected"]["method"]]
    if not rows:
        raise ValueError("O método da política não existe no relatório.")
    row = min(rows, key=lambda r: r["forecast_origin"])
    payload = {
        "conjunto": policy["conjunto"], "method": row["method"],
        "forecast_origin": row["forecast_origin"], "history_end": row["history_end"],
        "target_time": row["target_time"],
        "drop_threshold_mwmed": float(row["drop_threshold_mwmed"]),
        "p_event": float(row["p_event"]),
    }
    status, decision = call_api(base_url + "/decisions", payload)
    if status != 200:
        raise ValueError(f"Pedido real rejeitado: HTTP {status}: {decision}")
    assert decision["alarm"] == (payload["p_event"] >= policy["selected"]["threshold"])
    # Contraprova explícita: uma probabilidade fora do domínio deve ser rejeitada.
    invalid_payload = {**payload, "p_event": 1.2}
    invalid_status, invalid_response = call_api(base_url + "/decisions", invalid_payload)
    if invalid_status != 422:
        raise AssertionError(f"Esperado HTTP 422 para p_event=1.2, recebido {invalid_status}.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "request.json": payload, "decision.json": decision,
        "invalid_request.json": invalid_payload, "invalid_response.json": invalid_response,
        "verification.json": {
            "valid_http_status": status, "invalid_http_status": invalid_status,
            "source_predictions_sha256": source_sha,
            "selected_policy_id": policy["policy_id"],
            "source_forecast_origin": row["forecast_origin"],
            "estimator_executed": False, "scope": "historical probability replay",
        },
    }
    for name, value in artifacts.items():
        (args.output_dir / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8",
        )
    print(f"Pedido real: HTTP {status}")
    print(json.dumps(decision, ensure_ascii=False, indent=2, allow_nan=False))
    print(f"Contraprova p_event=1.2: HTTP {invalid_status} (rejeição esperada).")
    print(f"Arquivos: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
