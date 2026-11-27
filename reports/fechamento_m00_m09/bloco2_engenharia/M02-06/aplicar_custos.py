"""Conferência aplicada de custos sobre previsões salvas; não executa modelos."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def save_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def audit_hashes(directory, declared):
    measured = {}
    for name, expected in declared.items():
        path = (directory / name).resolve()
        if not path.is_relative_to(directory.resolve()):
            raise ValueError("Caminho fora da fonte declarada")
        measured[name] = sha(path)
        if measured[name] != expected:
            raise ValueError(f"Hash divergente: {path}")
    return measured


def event_counts(y, alarm, fp_cost, fn_cost):
    tp = int(np.sum((y == 1) & alarm))
    fp = int(np.sum((y == 0) & alarm))
    fn = int(np.sum((y == 1) & ~alarm))
    tn = int(np.sum((y == 0) & ~alarm))
    total = fp_cost * fp + fn_cost * fn
    return {
        "rows": len(y), "events": int(y.sum()), "tp": tp, "fp": fp,
        "fn": fn, "tn": tn, "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "relative_cost_total": float(total), "relative_cost_per_emission": float(total / len(y)),
    }


def main(argv=None):
    started_at = datetime.now(timezone.utc).isoformat()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clinic-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    for output_name in ("custos.csv", "custos_alarmes.csv", "resultado.json"):
        if (HERE / output_name).exists():
            raise FileExistsError(f"Saida ja existente; nao sobrescrever: {output_name}")
    protocol_path = HERE / "protocolo.json"
    protocol = load_json(protocol_path)
    for name, expected in protocol["input_hashes"].items():
        if sha(ROOT / name) != expected:
            raise ValueError(f"Entrada alterada desde o protocolo: {name}")
    source = ROOT / protocol["source_run"]
    source_result = load_json(source / "resultado.json")
    source_hashes = audit_hashes(source, source_result["output_sha256"])
    event_source = ROOT / protocol["source_event_study"]
    event_meta = load_json(event_source / "metadata.json")
    event_hashes = audit_hashes(event_source, event_meta["output_sha256"])
    if sha(event_source / "protocol.json") != event_meta["protocol_sha256"]:
        raise ValueError("Protocolo dos eventos diverge do recibo")
    clinic = args.clinic_dir.resolve()
    if not clinic.is_relative_to(HERE / "clinica"):
        raise ValueError("A clínica deve ser uma execução explícita desta entrega")
    clinic_result = load_json(clinic / "resultado.json")
    if clinic_result["source_run_id"] != protocol["source_run_id"]:
        raise ValueError("Execução da clínica usa outro run")
    clinic_hashes = audit_hashes(clinic, clinic_result["output_sha256"])
    aligned = load_csv(source / "alinhamento_alvos.csv")
    origins = [row["forecast_origin"] for row in aligned]
    targets = [row["target_time"] for row in aligned]
    observed = np.asarray([float(row["target_generation"]) for row in aligned])
    if len(observed) != 168 or len(set(origins)) != 168 or origins != sorted(origins):
        raise ValueError("Coorte pontual diferente das 168 origens ordenadas")
    for row in aligned:
        delta = datetime.fromisoformat(row["target_time"]) - datetime.fromisoformat(row["history_end"])
        if delta.total_seconds() != 26 * 3600:
            raise ValueError("Alvo incompatível com o contrato h24/d2")
    predictions = load_csv(source / "predictions.csv")
    policies = {}
    for method, seed in sorted({(row["method"], row["seed"]) for row in predictions}):
        group = sorted((row for row in predictions if (row["method"], row["seed"]) == (method, seed)),
                       key=lambda row: row["forecast_origin"])
        if [row["forecast_origin"] for row in group] != origins or [row["target_time"] for row in group] != targets:
            raise ValueError("Políticas sem as mesmas origens/alvos")
        np.testing.assert_allclose([float(row["target_generation"]) for row in group], observed, rtol=0, atol=1e-12)
        label = method + (f"/seed={seed}" if seed else "")
        policies[label] = np.asarray([float(row["prediction"]) for row in group])
    with np.load(source / "quantis_26_passos.npz", allow_pickle=False) as archive:
        forecast = archive["forecast"]
        levels = archive["quantile_levels"]
    if forecast.shape != (168, 9, 26) or not np.isfinite(forecast).all():
        raise ValueError("Trajetória incompatível")
    indices = {}
    for tau in (0.2, 0.5, 0.8):
        selected = np.flatnonzero(np.isclose(levels, tau, rtol=0, atol=1e-12))
        if len(selected) != 1:
            raise ValueError("Nível quantílico ausente ou ambíguo")
        indices[str(tau)] = int(selected[0])
        action = forecast[:, selected[0], 25].astype(float)
        if tau == 0.5:
            np.testing.assert_allclose(action, policies["chronos_bolt_tiny_zero_shot"], rtol=0, atol=1e-10)
        else:
            policies[f"chronos_decisao_p{round(tau * 100):02}"] = action
    point_rows = load_csv(clinic / "perdas_cenarios.csv")
    for row in point_rows:
        action = policies[row["policy"]]
        cu, co = float(row["cost_under"]), float(row["cost_over"])
        residual = observed - action
        direct = cu * residual.clip(min=0) + co * (-residual).clip(min=0)
        tau = cu / (cu + co)
        pinball = np.where(residual >= 0, tau * residual, (tau - 1) * residual)
        np.testing.assert_allclose(direct, (cu + co) * pinball, rtol=1e-13, atol=1e-12)
        np.testing.assert_allclose(direct.mean(), float(row["mean_relative_loss"]), rtol=0, atol=1e-10)
        np.testing.assert_allclose(np.abs(residual).mean(), float(row["mae_mwmed"]), rtol=0, atol=1e-10)
    if len(point_rows) != 36:
        raise ValueError("Esperadas 12 políticas em três cenários")
    (HERE / "custos.csv").write_bytes((clinic / "perdas_cenarios.csv").read_bytes())

    event_rows = load_csv(event_source / "predictions.csv")
    event_groups = {}
    common = None
    for method in protocol["event_decisions"]["methods_expected"]:
        group = sorted((row for row in event_rows if row["method"] == method), key=lambda row: row["forecast_origin"])
        cohort = [(row["forecast_origin"], row["target_time"], row["event_drop"], row["fold"]) for row in group]
        if len(group) != 504 or len({row["forecast_origin"] for row in group}) != 504:
            raise ValueError("Coorte de eventos incorreta")
        if common is None:
            common = cohort
        if cohort != common:
            raise ValueError("Métodos de eventos sem a mesma coorte")
        y = np.asarray([float(row["event_drop"]) for row in group])
        probabilities = np.asarray([float(row["p_event"]) for row in group])
        if not np.isin(y, [0, 1]).all() or not np.isfinite(probabilities).all() or not ((probabilities >= 0) & (probabilities <= 1)).all():
            raise ValueError("Rótulo ou probabilidade inválida")
        drop = np.asarray([float(row["last_available_generation"]) - float(row["target_generation"]) for row in group])
        if not np.array_equal((drop >= 22.77).astype(int), y):
            raise ValueError("Definição do evento alterada")
        event_groups[method] = (group, y, probabilities)
    alarm_rows = []
    for scenario in protocol["event_decisions"]["scenarios"]:
        fp_cost, fn_cost = scenario["cost_fp"], scenario["cost_fn"]
        threshold_cost = fp_cost / (fp_cost + fn_cost)
        for method, (group, y, probabilities) in event_groups.items():
            folds = np.asarray([int(row["fold"]) for row in group])
            rules = {"fixed_0.5": (0.5, probabilities >= 0.5)}
            if threshold_cost != 0.5:
                rules["theoretical_cost_threshold"] = (threshold_cost, probabilities >= threshold_cost)
            for rule, (threshold, alarm) in rules.items():
                for fold in [0, *sorted(set(folds))]:
                    mask = np.ones(len(y), dtype=bool) if fold == 0 else folds == fold
                    alarm_rows.append({"scenario": scenario["name"], "method": method, "rule": rule,
                                       "threshold": threshold, "cost_fp": fp_cost, "cost_fn": fn_cost,
                                       "fold": "pooled" if fold == 0 else int(fold),
                                       **event_counts(y[mask], alarm[mask], fp_cost, fn_cost)})
        _, y, _ = next(iter(event_groups.values()))
        for action in [False, True]:
            alarm_rows.append({"scenario": scenario["name"], "method": "always_alarm" if action else "never_alarm",
                               "rule": "constant_action", "threshold": None,
                               "cost_fp": fp_cost, "cost_fn": fn_cost, "fold": "pooled",
                               **event_counts(y, np.full(len(y), action), fp_cost, fn_cost)})
    save_csv(HERE / "custos_alarmes.csv", alarm_rows)
    if source_hashes != audit_hashes(source, source_result["output_sha256"]):
        raise ValueError("Fonte M09.3 alterada")
    if event_hashes != audit_hashes(event_source, event_meta["output_sha256"]):
        raise ValueError("Fonte de eventos alterada")
    winners = {}
    for scenario in protocol["generation_decisions"]["scenarios"]:
        chosen = min((row for row in point_rows if row["scenario"] == scenario["name"]), key=lambda row: float(row["mean_relative_loss"]))
        winners[scenario["name"]] = {"policy": chosen["policy"], "mean_relative_loss": float(chosen["mean_relative_loss"])}
    result = {
        "schema": "renewcast-decision-risk-result-v1", "completed": True,
        "started_at_utc": started_at,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(), "roadmap_id": "M02-06",
        "protocol_sha256": sha(protocol_path), "code_sha256": sha(Path(__file__)),
        "clinic_run": clinic.relative_to(ROOT).as_posix(), "clinic_result_sha256": sha(clinic / "resultado.json"),
        "clinic_code_sha256": clinic_result["code_sha256"], "clinic_source_copy_equal": sha(ROOT / "notebooks/clinica_decisao_forecast.py") == protocol["source_clinic"]["sha256"],
        "generation_cohort": {"rows": 168, "origin_min": origins[0], "origin_max": origins[-1], "policies": 12,
                              "scenario_rows": len(point_rows), "quantile_grid": levels.tolist(), "direct_level_indices": indices,
                              "interpolation": False, "forecast_index_zero_based": 25},
        "generation_empirical_minimum_by_scenario": winners,
        "event_cohort": {"rows_per_method": 504, "methods": len(event_groups), "events": int(y.sum()),
                         "origin_min": common[0][0], "origin_max": common[-1][0], "cost_table_rows": len(alarm_rows)},
        "event_pooled_costs": [row for row in alarm_rows if row["fold"] == "pooled"],
        "cohorts_compared_to_each_other": False,
        "checks": {"source_hashes_verified_and_preserved": True, "same_cohort_within_each_study": True,
                   "point_cost_rows_recomputed_independently": 36, "loss_equals_scaled_pinball": True,
                   "native_p50_equals_saved_forecast": True, "event_labels_reconstructed": True,
                   "probabilities_finite_in_unit_interval": True, "event_probability_inferred_from_quantiles": False},
        "training_performed": False, "inference_performed": False, "probability_recalibration": False,
        "costs_are_hypothetical": True, "operational_approval": False, "independent_user_performance_claimed": False,
        "prepared_and_reviewed_by": "Codex engineering assistance; source clinic retained without attributing independent user authorship",
        "scope": "Previously explored development cohorts; descriptive post-hoc cost comparison, not a prospective validation or economic estimate",
        "execution_log_note": "Clinic process exited0. Initial PowerShell Tee-Object -Encoding was unsupported; the successful subprocess capture used replacement for non-UTF8 stdout accents. Numeric CSV/JSON artifacts are unaffected. The wrapper console echo failed after the successful clinic had written its receipt; no model or clinic rerun was needed.",
        "versions": {"python": sys.version, "numpy": np.__version__, "platform": platform.platform()},
        "source_m09_output_hashes": source_hashes, "source_event_output_hashes": event_hashes,
        "clinic_output_hashes": clinic_hashes,
        "output_sha256": {name: sha(HERE / name) for name in ["custos.csv", "custos_alarmes.csv", "execucao_clinica.log"]},
    }
    (HERE / "resultado.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"completed": True, "generation_rows": len(point_rows), "alarm_rows": len(alarm_rows), "winners": winners}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
