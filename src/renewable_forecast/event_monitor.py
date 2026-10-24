"""M06.3: monitor de integridade, disponibilidade e desempenho de lote histórico.

Somente leitura do banco/modelo; não carrega estimador, não prevê e não retreina.
python -m renewable_forecast.event_monitor --help
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

RELEASE = "2026.10.05-event-monitor-1"
DEFAULT_DB = Path("reports/service/CJU_BA5EIGT/h24_event_batch_v1/ledger.sqlite")
DEFAULT_MODEL = Path("models/CJU_BA5EIGT/h24_event_batch_v1")
DEFAULT_RULES = Path("config/monitoring_h24_v1.json")
DEFAULT_OUTPUT = Path("reports/monitoring/CJU_BA5EIGT/h24_event_batch_v1")


def timestamp(value):
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamp deve informar fuso horário.")
    return result.astimezone(timezone.utc)


def iso(value):
    return timestamp(value).isoformat().replace("+00:00", "Z")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def read_only(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo ausente: {path.resolve()}")
    con = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def load_rules(path):
    rules = json.loads(Path(path).read_text(encoding="utf-8"))
    if rules.get("schema_version") != "1.0":
        raise ValueError("Versão das regras incompatível.")
    for name, minimum in (("min_observed", 1), ("max_missing_observations", 0)):
        if type(rules.get(name)) is not int or rules[name] < minimum:
            raise ValueError(f"Regra inválida: {name}.")
    tolerance = rules.get("brier_relative_tolerance")
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("brier_relative_tolerance deve ser finita e não negativa.")
    return rules


def select_action(integrity_status, missing, performance_status, rules):
    """Prioridade de triagem; não executa ações no ambiente."""
    if integrity_status != "pass":
        return {"code": "repair_record", "priority": "critical",
                "instruction": "Suspender o uso deste relatório para decisões; localizar a divergência e recuperar o registro confiável."}
    if missing > rules["max_missing_observations"]:
        return {"code": "investigate_data", "priority": "high",
                "instruction": "Investigar chegada, extração e associação temporal da geração; produzir nova avaliação em outro corte após a correção."}
    if performance_status == "review":
        return {"code": "review_model", "priority": "review",
                "instruction": "Investigar dados e erros por período/regime; comparar candidato e referência em protocolo novo antes de promover ou retreinar."}
    if performance_status == "insufficient_evidence":
        return {"code": "collect_evidence", "priority": "info",
                "instruction": "Continuar coletando resultados. Métricas disponíveis são descritivas; a regra mínima de observações ainda não foi atendida."}
    return {"code": "continue_monitoring", "priority": "info",
            "instruction": "Manter acompanhamento; estar dentro desta regra não comprova calibração, estabilidade futura ou aptidão operacional."}


def evaluate(db, model_dir, rules, as_of):
    cutoff, stamp = timestamp(as_of), iso(as_of)
    con = read_only(db)
    try:
        con.execute("BEGIN")  # fotografia consistente de leitura, inclusive com outro processo ativo
        quick = con.execute("PRAGMA quick_check").fetchone()[0]
        config_row = con.execute("SELECT config_json FROM configuration WHERE id=1").fetchone()
        if config_row is None:
            raise ValueError("Banco sem configuração do lote.")
        config = json.loads(config_row[0])
        predictions = [dict(r) for r in con.execute("SELECT * FROM predictions ORDER BY forecast_origin")]
        assessments = [dict(r) for r in con.execute("SELECT * FROM assessments WHERE as_of=?", (stamp,))]
    finally:
        con.close()
    manifest_path = model_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    policy = config["policy"]
    issues = []

    def check(condition, code, origin=None):
        if not condition:
            issues.append({"code": code, "forecast_origin": origin})

    check(quick == "ok", "sqlite_structure")
    check(digest(manifest_path) == config["manifest_sha256"], "manifest_identity")
    check(digest(model_dir / "model.joblib") == config["model_sha256"] == manifest["model_sha256"], "model_identity")
    check(canonical_hash(policy) == manifest["policy_contract_sha256"], "policy_contract")
    start, end = timestamp(config["origin_start"]), timestamp(config["origin_end"])
    if end < start or cutoff < end:
        raise ValueError("Período inválido ou as-of anterior à última emissão do lote.")
    expected = [iso(start + timedelta(hours=h)) for h in range(int((end-start).total_seconds()//3600)+1)]
    origins = [p["forecast_origin"] for p in predictions]
    check(origins == expected, "forecast_coverage")
    a_by_origin = {a["forecast_origin"]: a for a in assessments}
    check(len(a_by_origin) == len(assessments), "duplicate_assessment")
    check(set(a_by_origin) == set(origins), "assessment_coverage")
    observed, awaiting, missing = [], 0, 0
    for pred in predictions:
        origin = pred["forecast_origin"]
        try:
            request = json.loads(pred["request_json"])
            response = json.loads(pred["response_json"])
            p, threshold = pred["p_event"], pred["threshold"]
            check(math.isfinite(p) and 0 <= p <= 1, "invalid_probability", origin)
            check(pred["request_sha256"] == canonical_hash(request), "request_hash", origin)
            check(set(request["features"]) == set(manifest["feature_columns"]), "feature_names", origin)
            check(all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
                      for v in request["features"].values()), "feature_values", origin)
            check(not ({"target_generation", "p_event", "event_drop"} & set(request)), "target_in_request", origin)
            check(response["model_sha256"] == config["model_sha256"] and
                  response["policy_sha256"] == config["policy_sha256"], "response_identity", origin)
            for key in ("p_event", "threshold", "alarm", "event_generation_at_or_below_mwmed"):
                check(response[key] == pred[key], "response_"+key, origin)
            check(threshold == policy["selected"]["threshold"], "policy_threshold", origin)
            check(pred["alarm"] == int(p >= threshold), "alarm_rule", origin)
            for key in ("forecast_origin", "target_time"):
                check(iso(request[key]) == pred[key] == iso(response[key]), "clock_"+key, origin)
            t0, target, available = map(timestamp, (origin, pred["target_time"], pred["target_available_at"]))
            check(target == t0 + timedelta(hours=policy["horizon_hours"]), "horizon", origin)
            check(available == target + timedelta(hours=policy["availability_delay_hours"]), "label_clock", origin)
            check(timestamp(request["history_end"]) == t0-timedelta(hours=policy["availability_delay_hours"]), "history_clock", origin)
            check(timestamp(request["weather_latest_available_at"]) <= t0, "weather_clock", origin)
            check(timestamp(manifest["training_cutoff"]) <= t0 and
                  timestamp(manifest["latest_train_label_available_at"]) < t0, "training_clock", origin)
            limit = request["features"]["lag_1h"] - policy["drop_mw"]
            check(math.isclose(limit, pred["event_generation_at_or_below_mwmed"], abs_tol=1e-10), "event_reference", origin)
            a = a_by_origin.get(origin)
            if a is None:
                continue
            status = a["status"]
            values = [a[k] for k in ("target_generation", "event_drop", "brier", "cost")]
            if status == "observed":
                check(available <= cutoff, "label_used_early", origin)
                if any(v is None or not math.isfinite(v) for v in values):
                    check(False, "observed_values", origin)
                    continue
                y = int(a["target_generation"] <= limit)
                brier = (p-y)**2
                cost = policy["cost_fp"]*int(pred["alarm"] == 1 and y == 0) + policy["cost_fn"]*int(pred["alarm"] == 0 and y == 1)
                check(a["event_drop"] == y, "event_label", origin)
                check(math.isclose(a["brier"], brier, rel_tol=1e-9, abs_tol=1e-10), "brier_value", origin)
                check(math.isclose(a["cost"], cost, abs_tol=1e-10), "cost_value", origin)
                observed.append({"y": y, "p": p, "alarm": pred["alarm"], "brier": brier, "cost": cost})
            elif status == "awaiting_label":
                awaiting += 1
                check(available > cutoff and all(v is None for v in values), "awaiting_contract", origin)
            elif status == "missing_observation":
                missing += 1
                check(available <= cutoff and all(v is None for v in values), "missing_contract", origin)
            else:
                check(False, "unknown_label_status", origin)
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            issues.append({"code": "malformed_record", "forecast_origin": origin, "detail": str(exc)})

    n = len(observed)
    baseline_p = manifest["training_events"] / manifest["training_rows"]
    check(0 <= baseline_p <= 1, "training_frequency")
    integrity = "fail" if issues else "pass"
    metrics = None
    status = "blocked"
    if not issues:
        brier = math.fsum(o["brier"] for o in observed)/n if n else None
        reference = math.fsum((baseline_p-o["y"])**2 for o in observed)/n if n else None
        tp = sum(o["alarm"] == 1 and o["y"] == 1 for o in observed)
        fp = sum(o["alarm"] == 1 and o["y"] == 0 for o in observed)
        fn = sum(o["alarm"] == 0 and o["y"] == 1 for o in observed)
        tn = n-tp-fp-fn
        metrics = {"observed": n, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
                   "brier": brier, "baseline_brier": reference, "baseline_probability": baseline_p,
                   "brier_skill": 1-brier/reference if reference and n else None,
                   "cost_total": math.fsum(o["cost"] for o in observed) if n else None,
                   "cost_per_observed": math.fsum(o["cost"] for o in observed)/n if n else None,
                   "precision": tp/(tp+fp) if tp+fp else None,
                   "recall": tp/(tp+fn) if tp+fn else None}
        if n < rules["min_observed"]:
            status = "insufficient_evidence"
        elif brier > reference*(1+rules["brier_relative_tolerance"]):
            status = "review"
        else:
            status = "within_rule"
    action = select_action(integrity, missing, status, rules)
    return {
        "release": RELEASE, "as_of": stamp, "historical_simulation": True,
        "source_db": str(Path(db).resolve()), "source_db_sha256": digest(db),
        "model_sha256": config["model_sha256"], "policy_sha256": config["policy_sha256"],
        "monitor_code_sha256": digest(Path(__file__)), "rules": rules,
        "rules_sha256": canonical_hash(rules),
        "integrity": {"status": integrity, "issues": issues},
        "data": {"status": "blocked" if issues else ("investigate" if missing > rules["max_missing_observations"] else "ok"),
                 "expected_predictions": len(expected), "recorded_predictions": len(predictions),
                 "assessment_rows": len(assessments), "observed": n, "awaiting_label": awaiting,
                 "missing_observation": missing,
                 "due_label_completion": n/(n+missing) if n+missing and not issues else None},
        "performance": {"status": status, "metrics": metrics,
                        "reference": "constant frequency from this artifact's training labels",
                        "statistical_guarantee": False},
        "service": {"status": "not_measured", "reason": "O lote não registra latência, uptime nem taxa de erros HTTP."},
        "action": action, "automatic_retraining": False, "actions_executed": False,
        "scope": "Engineering audit of existing development batch; retrospective policy, assumed availability; no new holdout.",
    }


def save_report(report, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "monitor.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    escape = lambda value: html.escape(str(value))
    data, perf, action = report["data"], report["performance"], report["action"]
    status_rows = [("Integridade", report["integrity"]["status"]), ("Dados", data["status"]),
                   ("Desempenho", perf["status"]), ("Serviço HTTP", "não medido")]
    metrics = perf["metrics"] or {"avaliação": "bloqueada por inconsistência"}
    def table(rows):
        return '<table>' + ''.join('<tr><th>'+escape(k)+'</th><td>'+escape(v)+'</td></tr>' for k,v in rows) + '</table>'
    issues = report["integrity"]["issues"]
    issues_text = json.dumps(issues, indent=2, ensure_ascii=False) if issues else "Nenhuma divergência nas verificações implementadas."
    content = f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Renewcast | Monitor do lote</title><style>
body{{font:16px system-ui,sans-serif;max-width:1050px;margin:40px auto;padding:0 24px;color:#172337;background:#f5f7fa}}
h1{{font-size:30px}}h2{{font-size:21px;margin-top:28px}}.action{{background:#e6eef8;border-left:5px solid #356298;padding:18px}}
table{{border-collapse:collapse;width:100%;background:white;margin:14px 0}}th,td{{padding:9px 14px;border-bottom:1px solid #dae1e9;text-align:left}}
th{{font-weight:550;width:55%}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:16px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}.note{{color:#52627a}}@media(max-width:700px){{.grid{{display:block}}}}</style>
<h1>Renewcast · Monitor do lote</h1><p>Corte: <strong>{escape(report['as_of'])}</strong></p>
<p class="note">Simulação histórica de desenvolvimento. Diagnóstico gerado em leitura; nenhuma ação ou retreinamento executado.</p>
<div class="action"><strong>{escape(action['code'])} · {escape(action['priority'])}</strong><p>{escape(action['instruction'])}</p></div>
<div class="grid"><section><h2>Estados independentes</h2>{table(status_rows)}<h2>Disponibilidade</h2>
{table([(k,data[k]) for k in ('expected_predictions','recorded_predictions','assessment_rows','observed','awaiting_label','missing_observation','due_label_completion')])}</section>
<section><h2>Métricas sobre rótulos observados</h2>{table(metrics.items())}
<p class="note">Referência: frequência de eventos no treino deste artefato. Indicadores descritivos; a comparação não é um novo teste independente.</p></section></div>
<h2>Regras explícitas</h2>{table([(k,report['rules'][k]) for k in ('min_observed','max_missing_observations','brier_relative_tolerance')])}
<p>Mínimo de observações é uma regra didática para triagem, não uma garantia estatística. Serviço HTTP, drift e calibração não são diagnosticados por este relatório.</p>
<h2>Divergências do registro</h2><pre>{escape(issues_text)}</pre>
<h2>Identidade</h2><pre>Modelo: {escape(report['model_sha256'])}\nPolítica: {escape(report['policy_sha256'])}\nRegras: {escape(report['rules_sha256'])}</pre></html>'''
    (output / "monitor.html").write_text(content, encoding="utf-8")
    print(f"Integridade={report['integrity']['status']}; dados={data['status']}; desempenho={perf['status']}; ação={action['code']}")
    print(f"Relatório: {(output/'monitor.html').resolve()}")


def exercise(db, model_dir, rules, as_of, output):
    """Falhas em cópias temporárias; banco original aberto somente para leitura."""
    original_digest = digest(db)
    normal = evaluate(db, model_dir, rules, as_of)
    if normal["integrity"]["status"] != "pass":
        raise ValueError("Corrija primeiro o registro original: o exercício exige uma base íntegra.")
    save_report(normal, output / "normal")
    scenarios = {}
    with tempfile.TemporaryDirectory(prefix="renewcast_monitor_") as temporary:
        for scenario in ("missing_observation", "changed_probability", "missing_assessment"):
            copy_path = Path(temporary) / (scenario+".sqlite")
            source, destination = read_only(db), sqlite3.connect(copy_path)
            try:
                source.backup(destination)
                row = destination.execute("SELECT forecast_origin FROM assessments WHERE as_of=? AND status='observed' ORDER BY forecast_origin LIMIT 1", (iso(as_of),)).fetchone()
                if row is None:
                    raise ValueError("O exercício exige ao menos um rótulo observado no corte.")
                origin = row[0]
                if scenario == "missing_observation":
                    destination.execute("UPDATE assessments SET status='missing_observation', target_generation=NULL, event_drop=NULL, brier=NULL, cost=NULL WHERE as_of=? AND forecast_origin=?", (iso(as_of), origin))
                elif scenario == "changed_probability":
                    p = destination.execute("SELECT p_event FROM predictions WHERE forecast_origin=?", (origin,)).fetchone()[0]
                    destination.execute("UPDATE predictions SET p_event=? WHERE forecast_origin=?", (.99 if p != .99 else .01, origin))
                else:
                    destination.execute("DELETE FROM assessments WHERE as_of=? AND forecast_origin=?", (iso(as_of), origin))
                destination.commit()
            finally:
                source.close()
                destination.close()
            report = evaluate(copy_path, model_dir, rules, as_of)
            report["fault_injection"] = {"scenario": scenario, "temporary_copy": True,
                                         "original_db_sha256": original_digest}
            report["source_db"] = "temporary scenario copy (removed after experiment)"
            save_report(report, output / scenario)
            scenarios[scenario] = report["action"]["code"]
    if digest(db) != original_digest:
        raise RuntimeError("O arquivo original mudou durante a execução; não declare a comparação concluída.")
    result = {"normal": normal["action"]["code"], **scenarios, "original_db_unchanged": True}
    (output / "exercise_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--as-of", default="2026-08-02T07:00:00Z")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--exercise", action="store_true")
    args = parser.parse_args(argv)
    rules = load_rules(args.rules)
    if args.exercise:
        exercise(args.db, args.model_dir, rules, args.as_of, args.output_dir)
    else:
        save_report(evaluate(args.db, args.model_dir, rules, args.as_of), args.output_dir)


if __name__ == "__main__":
    main()
