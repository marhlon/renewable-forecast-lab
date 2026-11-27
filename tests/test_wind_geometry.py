"""E51: chaves exatas, geometria e pedido JSON, sem fit ou leitura de pickle."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys
from unittest.mock import patch

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from renewable_forecast.weather_artifact import validate_request, validate_wind_geometry

REAL = ROOT / "reports/inference/CJU_BA5EIGT/h24_replay_20260801T0500Z"
NAMES = ("wind_speed_mean_ms", "wind_u_mean_ms", "wind_v_mean_ms")


def geometry(speed=5.0, u=3.0, v=4.0):
    return dict(zip(NAMES, (speed, u, v)))


def cases():
    rows = []
    for label, data, expected in (
        ("valido", geometry(), "aceitar"),
        ("impossivel_v12_u30_v0", geometry(12.0, 30.0, 0.0), "rejeitar"),
    ):
        data["wind_speed_cubed_mean_m3s3"] = 2191.5364568023715
        for order, keys in (
            ("original", list(data)),
            ("invertida", list(reversed(data))),
            ("cubed_primeiro", ["wind_speed_cubed_mean_m3s3", *NAMES]),
        ):
            rows.append({"id": f"{label}_{order}", "features": {k: data[k] for k in keys}, "expected": expected})
    for label, data, expected in (
        ("velocidade_negativa", geometry(-5.0), "rejeitar"),
        ("u_negativo", geometry(5.0, -3.0, 4.0), "aceitar"),
        ("v_negativo", geometry(5.0, 3.0, -4.0), "aceitar"),
        ("u_v_negativos", geometry(5.0, -3.0, -4.0), "aceitar"),
        ("zero", geometry(0.0, 0.0, 0.0), "aceitar"),
        ("dentro_tolerancia", geometry(1.0, 1.0 + 5e-9, 0.0), "aceitar"),
        ("acima_tolerancia", geometry(1.0, 1.0 + 2e-8, 0.0), "rejeitar"),
        ("hypot_grande_finito", geometry(1.5e308, -1e308, -1e308), "aceitar"),
    ):
        rows.append({"id": label, "features": data, "expected": expected})
    for name in NAMES:
        missing = geometry()
        del missing[name]
        rows.append({"id": f"ausente_{name}", "features": missing, "expected": "rejeitar"})
        for label, value in (("nan", float("nan")), ("inf", float("inf")), ("menos_inf", -float("inf")),
                             ("nulo", None), ("booleano", True), ("texto", "3.0")):
            rows.append({"id": f"{label}_{name}", "features": geometry() | {name: value}, "expected": "rejeitar"})
    rows.extend({"id": label, "features": data, "expected": "rejeitar"}
                for label, data in (("entrada_nula", None), ("entrada_lista", [5, 3, 4])))
    return rows


CASES = cases()


def snapshot(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=True)


def check_case(case):
    data = deepcopy(case["features"])
    before = snapshot(data)
    error = None
    try:
        returned = validate_wind_geometry(data)
    except ValueError as exc:
        observed = "rejeitar"
        error = str(exc)
    else:
        assert returned is None
        observed = "aceitar"
    assert snapshot(data) == before, f"Entrada modificada: {case['id']}"
    assert observed == case["expected"], f"{case['id']}: {observed}, esperado {case['expected']}"
    return {"id": case["id"], "expected": case["expected"], "observed": observed,
            "input_preserved": True, "error": error, "passed": True}


def check_real_request():
    request_path, manifest_path = REAL / "request.json", REAL / "model/manifest.json"
    request = json.loads(request_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    before, manifest_before = snapshot(request), snapshot(manifest)
    columns = manifest["feature_columns"]
    blocked = AssertionError("Esta contraprova não pode ajustar ou carregar um estimador.")
    with patch("renewable_forecast.weather_artifact.joblib.load", side_effect=blocked), \
            patch("renewable_forecast.weather_artifact.HistGradientBoostingRegressor.fit", side_effect=blocked):
        normal = validate_request(request, manifest)
        reverse = deepcopy(request)
        reverse["features"] = dict(reversed(list(reverse["features"].items())))
        reverse_before = snapshot(reverse)
        inverted = validate_request(reverse, manifest)
        assert snapshot(reverse) == reverse_before
        np.testing.assert_array_equal(normal.to_numpy(), inverted.to_numpy())
        np.testing.assert_array_equal(normal.to_numpy()[0], [request["features"][name] for name in columns])
        assert list(normal.columns) == columns and normal.shape == (1, 32)
        invalid = deepcopy(reverse)
        invalid["features"].update(geometry(12.0, 30.0, 0.0))
        invalid_before = snapshot(invalid)
        with pytest.raises(ValueError, match="Inconsistência geométrica"):
            validate_request(invalid, manifest)
        assert snapshot(invalid) == invalid_before
    assert snapshot(request) == before and snapshot(manifest) == manifest_before
    return {"id": "pedido_historico_sem_modelo", "passed": True, "shape": list(normal.shape),
            "same_row_in_reversed_order": True, "impossible_reversed_request_rejected": True,
            "input_preserved": True, "fit_and_pickle_load_blocked": True,
            "inputs": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (request_path, manifest_path)}}


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_exact_names_geometry_and_input_preservation(case):
    check_case(case)


@pytest.mark.skipif(not (REAL / "request.json").is_file() or not (REAL / "model/manifest.json").is_file(),
                    reason="A integração opcional requer apenas os dois JSONs históricos, sem model.joblib.")
def test_real_request_geometry_without_fit_or_pickle():
    check_real_request()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contraprovas", type=Path, required=True)
    args = parser.parse_args()
    rows = [check_case(case) for case in CASES]
    rows.append(check_real_request())
    result = {"schema": "renewcast-m04-01-counterexamples-v1", "item": "M04-01",
              "executed_at_utc": datetime.now(timezone.utc).isoformat(),
              "argv": sys.argv, "python": sys.version.split()[0], "platform": platform.platform(),
              "versions": {name: version(name) for name in ("numpy", "pandas", "scikit-learn", "joblib", "pytest")},
              "passed": True, "case_count": len(rows), "cases": rows,
              "fit_called": False, "model_pickle_loaded": False}
    args.contraprovas.parent.mkdir(parents=True, exist_ok=True)
    args.contraprovas.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"{len(rows)} contraprovas aprovadas; sem fit ou carregamento de modelo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
