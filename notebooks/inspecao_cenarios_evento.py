"""M06: autoria — sensibilidade do classificador a cenários hipotéticos de vento.

Salvar em notebooks/inspecao_cenarios_evento.py.
Execute com a API de inferência aberta.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
from pathlib import Path

import numpy as np

from consultar_api_inferencia import call_api


PROJECT = Path(__file__).resolve().parents[1]
WIND_LINEAR = (
    "wind_speed_mean_ms", "wind_speed_spatial_std_ms", "wind_u_mean_ms", "wind_v_mean_ms",
)
WIND_CUBIC = "wind_speed_cubed_mean_m3s3"


def escalar_vento(features: dict, fator: float) -> dict:
    """Devolve uma cópia das features com todas as velocidades locais multiplicadas pelo fator.

    Requisitos:
    - Valida se fator é um número real não-booleano, finito e >= 0.
    - Multiplica as features lineares de vento (WIND_LINEAR) por fator.
    - Multiplica a feature cúbica de vento (WIND_CUBIC) por fator^3.
    - Preserva intactas as demais 27 features.
    - Não altera o dicionário de entrada.
    """
    if isinstance(fator, bool) or not isinstance(fator, (int, float, np.number)):
        raise TypeError("O fator deve ser um número real (int ou float), não booleano.")
    if not np.isfinite(fator):
        raise ValueError("O fator deve ser um número finito (não NaN ou Inf).")
    if fator < 0:
        raise ValueError("O fator deve ser não negativo (>= 0).")

    res = copy.deepcopy(features)

    for name in WIND_LINEAR:
        if name in res:
            res[name] = float(res[name] * fator)

    if WIND_CUBIC in res:
        res[WIND_CUBIC] = float(res[WIND_CUBIC] * (fator ** 3))

    return res


def conferir_transformacao(original, modified, fator):
    if set(modified) != set(original):
        raise ValueError("A transformação alterou os nomes das features.")
    for name in original:
        if name in WIND_LINEAR:
            expected = original[name] * fator
        elif name == WIND_CUBIC:
            expected = original[name] * fator**3
        else:
            expected = original[name]
        if not np.isclose(modified[name], expected, rtol=1e-10, atol=1e-10):
            raise ValueError(f"Transformação incoerente em {name}: recebido={modified[name]}, esperado={expected}.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=PROJECT / "models/CJU_BA5EIGT/h24_event_api_v1/example_request.json")
    parser.add_argument("--output-dir", type=Path, default=PROJECT / "reports/service/CJU_BA5EIGT/h24_event_inference_v1/scenarios")
    parser.add_argument("--url", default="http://127.0.0.1:8000/predict-decision")
    args = parser.parse_args(argv)
    original_request = json.loads(args.request.read_text(encoding="utf-8"))
    original_features = copy.deepcopy(original_request["features"])
    for bad in (-1, True, "1", float("nan"), float("inf")):
        try:
            escalar_vento(copy.deepcopy(original_features), bad)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError(f"Fator inválido foi aceito: {bad!r}")
    zero = escalar_vento(copy.deepcopy(original_features), 0.0)
    conferir_transformacao(original_features, zero, 0.0)
    rows, requests = [], []
    for factor in (0.8, 1.0, 1.2):
        features = copy.deepcopy(original_features)
        changed = escalar_vento(features, factor)
        assert features == original_features, "A função alterou o dicionário de entrada."
        conferir_transformacao(original_features, changed, factor)
        payload = {**original_request, "features": changed}
        code, result = call_api(args.url, payload)
        if code != 200:
            raise RuntimeError(f"HTTP {code}: {result}")
        rows.append({"factor": factor, "wind_speed_mean_ms": changed["wind_speed_mean_ms"],
            "wind_speed_cubed_mean_m3s3": changed[WIND_CUBIC], "p_event": result["p_event"],
            "threshold": result["threshold"], "alarm": result["alarm"],
            "model_sha256": result["model_sha256"], "policy_sha256": result["policy_sha256"]})
        requests.append({"factor": factor, "hypothetical": True, "request": payload, "response": result})
    base = next(row["p_event"] for row in rows if row["factor"] == 1.0)
    for row in rows:
        row["delta_probability_pp"] = 100 * (row["p_event"] - base)
    assert len({row["model_sha256"] for row in rows}) == 1
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "scenarios.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (args.output_dir / "requests_responses.json").write_text(json.dumps(requests, indent=2, allow_nan=False), encoding="utf-8")
    print("Sensibilidade hipotética; não mede causalidade, acurácia ou calibração.")
    for row in rows:
        print(f"fator={row['factor']:.1f}; p={row['p_event']:.6f}; delta={row['delta_probability_pp']:+.3f}pp; alarme={row['alarm']}")
    print(f"Arquivos: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()