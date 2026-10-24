"""M06: cliente HTTP de inferência. Salvar em notebooks/consultar_api_inferencia.py."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT / "models/CJU_BA5EIGT/h24_event_api_v1"
OUTPUT = PROJECT / "reports/service/CJU_BA5EIGT/h24_event_inference_v1"


def call_api(url, payload):
    body = json.dumps(payload, allow_nan=False).encode("utf-8")
    req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=30) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        return error.code, json.loads(error.read())
    except URLError as error:
        raise RuntimeError("Servidor indisponível. Deixe a API com --model-dir aberta no outro terminal.") from error


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=MODEL_DIR / "example_request.json")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--url", default="http://127.0.0.1:8000/predict-decision")
    args = parser.parse_args(argv)
    request = json.loads(args.request.read_text(encoding="utf-8"))
    if {"p_event", "event_drop", "target_generation"} & set(request):
        raise ValueError("Pedido deve conter somente features e metadados, sem probabilidade pronta/alvo.")
    status, response = call_api(args.url, request)
    if status != 200:
        raise RuntimeError(f"HTTP {status}: {response}")
    assert response["estimator_executed"] is True
    assert response["model_retrained"] is False
    assert response["alarm"] == (response["p_event"] >= response["threshold"])
    print(f"Inferência: HTTP {status}")
    print(json.dumps(response, indent=2, ensure_ascii=False))

    reversed_request = copy.deepcopy(request)
    reversed_request["features"] = dict(reversed(list(request["features"].items())))
    order_status, ordered = call_api(args.url, reversed_request)
    assert order_status == 200 and ordered == response, "A ordem do JSON alterou a resposta."
    missing = copy.deepcopy(request)
    del missing["features"]["lag_1h"]
    missing_status, missing_response = call_api(args.url, missing)
    assert missing_status == 422, "Feature ausente deveria ser rejeitada."
    injected = {**request, "p_event": 0.99}
    injected_status, injected_response = call_api(args.url, injected)
    assert injected_status == 422, "A probabilidade deve ser calculada no servidor."

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in {
        "request.json": request, "prediction.json": response,
        "missing_feature_response.json": missing_response,
        "injected_probability_response.json": injected_response,
        "verification.json": {
            "valid_http_status": status, "order_invariance": True,
            "missing_feature_http_status": missing_status,
            "injected_probability_http_status": injected_status,
            "request_sha256": hashlib.sha256(args.request.read_bytes()).hexdigest(),
            "model_sha256": response["model_sha256"], "policy_sha256": response["policy_sha256"],
            "estimator_executed": True, "independent_performance_evaluation": False,
        },
    }.items():
        write_json(args.output_dir / name, value)
    print("Ordem das features invertida: mesma resposta.")
    print("Feature ausente e tentativa de enviar p_event: HTTP 422.")
    print(f"Arquivos: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
