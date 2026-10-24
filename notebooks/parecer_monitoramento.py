"""M06.3: auditoria independente dos relatórios do lote, somente leitura.

Salvar em notebooks/parecer_monitoramento.py; executar na raiz do projeto.
Saída separada em parecer_validado. Não treina nem cria dados de entrada.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_DB = PROJECT / "reports/service/CJU_BA5EIGT/h24_event_batch_v1/ledger.sqlite"
DEFAULT_MANIFEST = PROJECT / "models/CJU_BA5EIGT/h24_event_batch_v1/manifest.json"
DEFAULT_MONITOR_DIR = PROJECT / "reports/monitoring/CJU_BA5EIGT/h24_event_batch_v1"
DEFAULT_AS_OF = "2026-08-02T07:00:00Z"
SCENARIOS = ("normal", "missing_observation", "changed_probability", "missing_assessment")
ATOL = 1e-9


def exigir(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ler_json(path):
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")
    result = json.loads(path.read_text(encoding="utf-8"))
    exigir(isinstance(result, dict), f"Objeto JSON esperado: {path}")
    return result


def instante_utc(value):
    ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    exigir(ts.tzinfo is not None, "as_of deve informar fuso horário.")
    return ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def consultar_resultados_observados(db_path, as_of):
    """Chave da avaliação: (as_of, forecast_origin), e não só a origem."""
    db_path = Path(db_path).resolve()
    if not db_path.is_file():
        raise FileNotFoundError(f"Banco obrigatório ausente: {db_path}; nenhum fallback será criado.")
    con = sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True)
    try:
        con.execute("BEGIN")
        tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {"configuration", "predictions", "assessments"}
        exigir(required <= tables, f"Não é o ledger do lote. Faltam tabelas: {sorted(required - tables)}")
        config_row = con.execute("SELECT config_json FROM configuration WHERE id=1").fetchone()
        exigir(config_row is not None, "Configuração do lote ausente.")
        config = json.loads(config_row[0])
        counts = dict(con.execute(
            "SELECT status, COUNT(*) FROM assessments WHERE as_of=? GROUP BY status", (as_of,),
        ).fetchall())
        exigir(bool(counts), f"Nenhuma avaliação no corte {as_of}.")
        observed = pd.read_sql_query(
            """SELECT a.forecast_origin, a.event_drop, p.p_event
               FROM assessments AS a
               JOIN predictions AS p ON p.forecast_origin = a.forecast_origin
               WHERE a.as_of = ? AND a.status = 'observed'
               ORDER BY a.forecast_origin""", con, params=(as_of,),
        )
    finally:
        con.close()
    exigir(not observed.empty, "Sem resultados observados neste corte; métricas não calculáveis.")
    exigir(not observed.forecast_origin.duplicated().any(), "Origem duplicada no corte selecionado.")
    exigir(len(observed) == counts.get("observed", 0), "O JOIN perdeu ou multiplicou avaliações.")
    return observed, config, counts


def obter_frequencia_treino(manifest):
    n, events = manifest["training_rows"], manifest["training_events"]
    exigir(type(n) is int and n > 0, "training_rows deve ser inteiro positivo.")
    exigir(type(events) is int and 0 <= events <= n, "training_events inválido.")
    return events / n


def recalcular_metricas(observed, baseline_probability):
    """NumPy sobre os rótulos e probabilidades; não usa a.brier nem event_monitor."""
    y = observed["event_drop"].to_numpy(dtype=float)
    p = observed["p_event"].to_numpy(dtype=float)
    exigir(y.size > 0 and np.isfinite(y).all() and np.isin(y, [0, 1]).all(), "Rótulos 0/1 obrigatórios.")
    exigir(np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all(), "Probabilidades inválidas.")
    exigir(math.isfinite(baseline_probability) and 0 <= baseline_probability <= 1, "Referência inválida.")
    brier = float(np.mean((p - y) ** 2))
    reference = float(np.mean((baseline_probability - y) ** 2))
    return {
        "observed": len(y), "brier": brier, "baseline_brier": reference,
        "baseline_probability": baseline_probability,
        "brier_skill": 1.0 - brier / reference if reference > 0 else None,
    }


def comparar_com_monitor(metrics, monitor):
    """Chaves obrigatórias, tolerância absoluta; zero é valor, null é indefinição."""
    official = monitor["performance"]["metrics"]
    exigir(isinstance(official, dict), "Monitor sem métricas utilizáveis.")
    rows = []
    for name, computed in metrics.items():
        exigir(name in official, f"Métrica obrigatória ausente: performance.metrics.{name}.")
        reported = official[name]
        if computed is None or reported is None:
            passed = computed is None and reported is None
            delta = None
        else:
            exigir(type(reported) in (int, float) and math.isfinite(reported), f"Métrica inválida: {name}")
            delta = abs(computed - reported)
            passed = delta == 0 if name == "observed" else delta <= ATOL
        exigir(passed, f"Divergência em {name}: recalculado={computed}; monitor={reported}.")
        rows.append({"metric": name, "recalculated": computed, "reported": reported,
                     "absolute_difference": delta, "passed": True})
    return rows


def ler_relatorios_cenarios(monitor_dir, normal, db_hash, as_of):
    """Valores vêm de cada JSON; não existe tabela de resultados pré-preenchida."""
    reports, rows = {}, []
    for scenario in SCENARIOS:
        report = ler_json(monitor_dir / scenario / "monitor.json")
        exigir(instante_utc(report["as_of"]) == as_of, f"Corte diferente em {scenario}.")
        for key in ("model_sha256", "policy_sha256", "rules_sha256", "monitor_code_sha256"):
            exigir(report[key] == normal[key], f"Identidade divergente em {scenario}: {key}.")
        if scenario != "normal":
            fault = report["fault_injection"]
            exigir(fault["scenario"] == scenario and fault["temporary_copy"] is True,
                   f"Cenário sem identificação da cópia temporária: {scenario}.")
            exigir(fault["original_db_sha256"] == db_hash, f"Cenário de outro ledger: {scenario}.")
        data = report["data"]
        rows.append({
            "scenario": scenario, "integrity_status": report["integrity"]["status"],
            "data_status": data["status"], "performance_status": report["performance"]["status"],
            "action": report["action"]["code"], "priority": report["action"]["priority"],
            "observed": data["observed"], "missing_observation": data["missing_observation"],
            "assessment_rows": data["assessment_rows"],
            "expected_predictions": data["expected_predictions"],
        })
        reports[scenario] = report
    return reports, pd.DataFrame(rows)


def auditar(db, manifest_path, monitor_dir, as_of):
    as_of = instante_utc(as_of)
    inputs = {"ledger": db, "manifest": manifest_path}
    inputs.update({scenario: monitor_dir / scenario / "monitor.json" for scenario in SCENARIOS})
    for path in inputs.values():
        if not path.is_file():
            raise FileNotFoundError(f"Entrada obrigatória ausente: {path}")
    before = {name: sha256(path) for name, path in inputs.items()}
    normal = ler_json(inputs["normal"])
    exigir(instante_utc(normal["as_of"]) == as_of, "Corte diferente do relatório normal.")
    exigir(normal["source_db_sha256"] == before["ledger"],
           "Ledger diferente do auditado pelo monitor. Reexecute event_monitor --exercise antes do parecer.")
    exigir(normal["integrity"]["status"] == "pass", "O caso normal está sem integridade aprovada.")
    manifest = ler_json(manifest_path)
    observed, config, counts = consultar_resultados_observados(db, as_of)
    exigir(config["manifest_sha256"] == before["manifest"], "Manifesto não pertence a este lote.")
    exigir(config["model_sha256"] == manifest["model_sha256"] == normal["model_sha256"],
           "Modelo do lote, manifesto e monitor não coincidem.")
    exigir(config["policy_sha256"] == normal["policy_sha256"], "Política do monitor difere do lote.")
    exigir(sum(counts.values()) == normal["data"]["assessment_rows"], "Contagem de avaliações divergente.")
    for status in ("observed", "awaiting_label", "missing_observation"):
        exigir(counts.get(status, 0) == normal["data"][status], f"Contagem divergente: {status}.")
    metrics = recalcular_metricas(observed, obter_frequencia_treino(manifest))
    comparisons = comparar_com_monitor(metrics, normal)
    reports, scenarios = ler_relatorios_cenarios(monitor_dir, normal, before["ledger"], as_of)
    after = {name: sha256(path) for name, path in inputs.items()}
    exigir(before == after, "Uma entrada mudou durante a leitura; repita com o lote estável.")
    audit = {
        "audit_passed": True, "as_of": as_of, "absolute_tolerance": ATOL,
        "inputs": {name: {"path": str(path), "sha256": before[name]} for name, path in inputs.items()},
        "model_id": manifest["model_id"], "model_sha256": manifest["model_sha256"],
        "training_events": manifest["training_events"], "training_rows": manifest["training_rows"],
        "metrics": metrics, "comparisons": comparisons, "input_hashes_unchanged": True,
        "inspection_code_sha256": sha256(Path(__file__)), "synthetic_fallback_used": False,
        "estimator_executed": False, "production_approved": False,
        "scope": "Independent metric calculation and exported scenario comparison; historical development batch.",
    }
    return audit, reports, scenarios


def gerar_parecer_md(audit, reports, scenarios):
    metrics = audit["metrics"]
    format_value = lambda v: "indefinido (referência zero)" if v is None else f"{v:.9f}"
    lines = [
        "# M06.3 — Parecer sobre o lote histórico", "",
        f"Corte: `{audit['as_of']}`. Modelo: `{audit['model_id']}`.", "",
        "## Evidência recalculada", "",
        f"Foram usadas {metrics['observed']} emissões únicas do mesmo corte, com status observed.",
        f"Referência fixa: {audit['training_events']}/{audit['training_rows']} rótulos do treino.", "",
        "| Métrica | Recalculado | Relatório normal |", "|---|---:|---:|",
    ]
    for row in audit["comparisons"]:
        if row["metric"] != "observed":
            lines.append(f"| {row['metric']} | {format_value(row['recalculated'])} | {format_value(row['reported'])} |")
    lines += ["", "Todas as comparações passaram com tolerância absoluta 1e-9. Banco aberto em modo somente leitura; hashes das entradas preservados.",
              "", "## Cenários efetivamente lidos", "",
              "| Cenário | Integridade | Dados | Desempenho | Ação | Observados | Sem observação |",
              "|---|---|---|---|---|---:|---:|"]
    for row in scenarios.to_dict("records"):
        lines.append("| " + " | ".join(str(row[k]) for k in (
            "scenario", "integrity_status", "data_status", "performance_status", "action", "observed", "missing_observation",
        )) + " |")
    lines += ["", "## Condutas e limites", ""]
    for scenario, report in reports.items():
        lines.append(f"- **{scenario}** — prioridade `{report['action']['priority']}`: {report['action']['instruction']}")
    lines += ["",
        "1. Falhas de integridade têm precedência: métricas de registros incoerentes não sustentam decisão sobre o modelo. A regra exportada não estabelece ordem adicional entre os dois incidentes críticos.",
        f"2. O mínimo de {reports['normal']['rules']['min_observed']} observações é uma regra didática de triagem. Não prova independência, representatividade, concept drift ou segurança operacional. Este parecer não autoriza promoção ou retreino.",
        "3. missing_observation conserva a avaliação e informa falta do resultado após target_available_at. missing_assessment significa que falta o próprio registro de avaliação. A causa e o tempo de recuperação precisam de investigação.", "",
        "O recálculo é independente de event_monitor; os cenários são lidos dos relatórios exportados e não são reexecutados por este programa. A conferência não autentica medições físicas nem detecta toda adulteração coordenada.",
        "O lote usa política retrospectiva e hipóteses de disponibilidade. Não é novo holdout, monitoramento contínuo ou evidência de funcionamento ao vivo.", "",
        "Os arquivos gerados por uma execução anterior com fallback sintético não medem este lote e não devem integrar sua avaliação de desempenho.", "",
        "Este texto foi gerado por uma implementação revisada com orientação. Sua execução valida o contrato técnico; não comprova, isoladamente, autoria independente ou domínio completo.", "",
    ]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--monitor-dir", type=Path, default=DEFAULT_MONITOR_DIR)
    parser.add_argument("--as-of", default=DEFAULT_AS_OF)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        db, manifest, monitor_dir = args.db.resolve(), args.manifest.resolve(), args.monitor_dir.resolve()
        audit, reports, scenarios = auditar(db, manifest, monitor_dir, args.as_of)
        output = (args.output_dir or monitor_dir / "parecer_validado").resolve()
        output.mkdir(parents=True, exist_ok=True)
        scenarios.to_csv(output / "parecer.csv", index=False)
        (output / "parecer.md").write_text(gerar_parecer_md(audit, reports, scenarios), encoding="utf-8")
        (output / "auditoria.json").write_text(
            json.dumps(audit, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8",
        )
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        parser.exit(1, f"AUDITORIA REPROVADA: {exc}\nEsta execução não certifica relatórios anteriores.\n")
    print(f"Banco: {db}\nCorte: {audit['as_of']}; observados: {audit['metrics']['observed']}")
    print(pd.DataFrame(audit["comparisons"]).to_string(index=False, float_format=lambda v: f"{v:.9f}"))
    print("\nConferência aprovada: métricas coincidem; quatro cenários lidos; entradas preservadas.")
    print(scenarios.to_string(index=False))
    print(f"Arquivos: {output}")


if __name__ == "__main__":
    main()
