"""Auditoria documental/numérica B3: somente lê produtores, sem modelos/reexecução.

Não importa joblib, torch, notebooks produtores ou serviços externos. Recalcula
métricas de previsões salvas e verifica recibos/hashes, sem substituir os gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports/fechamento_m00_m09/bloco3_engenharia"
IDS = ["M03-04", "M05-04", "M05-05", *[f"M06-{i:02}" for i in range(2, 10)],
       "M07-01", "M07-02", "M07-03", "M08-02", "M08-03", "M09-02", "M09-04"]
OPEN = ["M06-02", "M06-04", "M06-05", "M06-06", "M06-07", "M06-08", "M06-09"]
CHECKS, DETAILS, WARNINGS = [], {}, []


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def sha(path):
    with Path(path).open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return digest


def local(path):
    candidate = (ROOT / path).resolve()
    if not candidate.is_relative_to(ROOT):
        raise ValueError("Manifesto aponta para fora do workspace")
    return candidate


def require(condition, explanation):
    if not condition:
        raise AssertionError(explanation)


def close(actual, expected, atol=1e-9):
    np.testing.assert_allclose(actual, expected, rtol=0, atol=atol)


def check(name, operation):
    try:
        detail = operation()
        CHECKS.append({"name": name, "passed": True})
        if detail is not None:
            DETAILS[name] = detail
    except Exception as error:
        CHECKS.append({"name": name, "passed": False, "error": f"{type(error).__name__}: {error}"})


def entries(document):
    field = document.get("files", document.get("artifacts"))
    if isinstance(field, dict):
        return list(field.items())
    return [(entry["path"], entry["sha256"]) for entry in field]


def verify_entries(items):
    items = list(items)
    bad = [path for path, expected in items if not local(path).is_file() or sha(local(path)) != expected]
    require(not bad, f"Hashes divergentes/ausentes: {bad}")
    return {"references_verified": len(items), "unique_files": len(set(p for p, _ in items))}


def manifests():
    paths = [BASE / "manifesto_transferencia_neural.json",
             *[BASE / item / "manifesto_sha256.json" for item in ["M07-01", "M07-02", "M07-03", "M05-05"]],
             BASE / "M06-03/manifesto_operacao_local.json", BASE / "M06-03/manifesto_codigo_documentacao.json",
             BASE / "M06-02/manifesto_pacote_ci.json"]
    return {rel(path): verify_entries(entries(read(path))) for path in paths}


def all_items():
    require(len(IDS) == len(set(IDS)) == 18, "Recorte deve conter 18 IDs distintos")
    missing = [f"{item}/{name}" for item in IDS for name in ["protocolo.json", "resultado.json", "parecer.md"]
               if not (BASE / item / name).is_file()]
    require(not missing, f"Entregáveis ausentes: {missing}")
    return {"scope": IDS, "full_engineering_recommended": [item for item in IDS if item not in OPEN],
            "operational_open": OPEN, "technical_local_acceptance_only": ["M06-06", "M06-07", "M06-08"],
            "counts": {"scope": 18, "full_engineering": 11, "operational_open": 7, "technical_deliveries_including_partial": 14}}


def frozen_and_time():
    seal_path = BASE / "congelamento_final.json"
    seal = read(seal_path)
    frozen = verify_entries(seal["files"].items())
    require(len(seal["files"]) == 29 and seal["raw_evaluation_present"] is False, "Selo final inesperado")
    receipt = read(BASE / "dados_final/fonte.json")
    require(receipt["freeze_sha256"] == sha(seal_path), "Recibo não aponta para selo atual")
    require(pd.Timestamp(seal["created_at_utc"]) < pd.Timestamp(receipt["downloaded_at_utc"]), "Download não posterior ao selo")
    require(receipt["historically_point_in_time_proven"] is False, "Disponibilidade histórica indevidamente afirmada")
    verify_entries([(receipt["raw_path"], receipt["raw_sha256"]), (receipt["filtered_path"], receipt["filtered_sha256"])])
    chronology = []
    for item in IDS:
        protocol, result = read(BASE / item / "protocolo.json"), read(BASE / item / "resultado.json")
        ptime = next((protocol[k] for k in ["registered_at_utc", "frozen_at_utc", "created_at_utc", "created_at"] if k in protocol), None)
        rtime = next((result[k] for k in ["started_at_utc", "executed_at_utc", "executed_at", "completed_at_utc", "recorded_at"] if k in result), None)
        require(ptime is not None and rtime is not None, f"Timestamp não localizado: {item}")
        require(pd.Timestamp(ptime) <= pd.Timestamp(rtime), f"Protocolo posterior ao resultado: {item}")
        chronology.append({"item": item, "protocol_time": ptime, "producer_time": rtime})
        if "code_sha256_before_execution" in protocol:
            verify_entries(protocol["code_sha256_before_execution"].items())
        if "code_sha256" in protocol:
            verify_entries(protocol["code_sha256"].items())
    verify_entries(read(BASE / "M05-04/freeze.json")["files"].items())
    return {"final_frozen": frozen, "freeze_time": seal["created_at_utc"], "download_time": receipt["downloaded_at_utc"],
            "chronology": chronology, "time_evidence_limit": "Recibos locais; não certifica relógio externo ou disponibilidade histórica na origem"}


def final_arrays_and_metrics():
    directory = BASE / "M03-04"
    source = read(BASE / "dados_final/fonte.json")
    filtered = pd.read_parquet(local(source["filtered_path"]))
    require(len(filtered) == 720, "Snapshot deve conter 720 horas")
    series = filtered.assign(din_instante=pd.to_datetime(filtered.din_instante)).set_index("din_instante").val_geracao
    require(series.index.equals(pd.date_range("2026-09-01", "2026-09-30 23:00", freq="h")), "Grade do snapshot divergente")
    require(np.isfinite(series).all(), "Geração não finita")
    origins = pd.date_range("2026-09-02 01:00", "2026-09-30", freq="h", inclusive="left")
    require(len(origins) == 671, "Grade de origens divergente")
    actual = series.reindex(origins + pd.Timedelta(hours=24)).to_numpy()
    context = np.column_stack([series.reindex(origins-pd.Timedelta(hours=i)).to_numpy() for i in range(25, 1, -1)])
    close(np.load(directory / "contexto_final.npy", allow_pickle=False), context, atol=0)
    predictions = pd.read_csv(directory / "predictions.csv")
    names = {"persistence", "linear_legacy", "hgb_legacy", "hgb_bloco2", "lightgbm", "catboost", "hgb_quantile_p50", "chronos_p50",
             *[f"{family}_{seed}" for family in ["mlp", "gru"] for seed in [17, 29, 41]]}
    require(set(predictions.method) == names and len(predictions) == 671*14, "Métodos/coorte final divergentes")
    summary = pd.read_csv(directory / "summary.csv").set_index("method")
    require(summary.index.is_unique and set(summary.index) == names, "Resumo sem os 14 métodos únicos")
    result = read(directory / "resultado.json")
    require(result == read(BASE / "M09-04/resultado.json"), "Resultados integrados dos dois IDs divergem")
    recorded = {row["method"]: row for row in result["metrics"]}
    arrays, recalculated = {}, []
    for method, frame in predictions.groupby("method"):
        frame = frame.sort_values("forecast_origin")
        require(pd.DatetimeIndex(pd.to_datetime(frame.forecast_origin)).equals(origins), f"Origens não pareadas: {method}")
        for column, expected in [("history_end", origins-pd.Timedelta(hours=2)), ("target_time", origins+pd.Timedelta(hours=24)),
                                 ("label_available_at", origins+pd.Timedelta(hours=26))]:
            require(pd.DatetimeIndex(pd.to_datetime(frame[column])).equals(expected), f"Relógio divergente: {method}/{column}")
        close(frame.y24, actual, atol=0)
        prediction = frame.prediction.to_numpy()
        require(np.isfinite(prediction).all(), f"Previsão não finita: {method}")
        arrays[method] = prediction
        error = actual-prediction
        row = {"method": method, "n": len(error), "mae": float(np.abs(error).mean()),
               "rmse": float(np.sqrt(np.mean(error**2))), "bias_observed_minus_predicted": float(error.mean())}
        for field in ["n", "mae", "rmse", "bias_observed_minus_predicted"]:
            close(row[field], summary.loc[method, field])
            close(row[field], recorded[method][field])
        recalculated.append(row)
    close(arrays["persistence"], context[:, -1], atol=1e-12)
    with np.load(directory / "chronos.npz", allow_pickle=False) as output:
        forecast, levels = output["forecast"], output["levels"]
    require(forecast.shape == (671, 9, 26) and np.isfinite(forecast).all(), "Shape/finidade Chronos divergentes")
    close(levels, np.arange(1, 10)/10, atol=1e-12)
    close(arrays["chronos_p50"], forecast[:, 4, 25], atol=1e-12)
    verify_entries([(rel(directory / name), expected) for name, expected in result["outputs"].items()])
    DETAILS["_arrays"] = (origins, actual, arrays, forecast)
    return {"source_rows": 720, "origins": 671, "paired_prediction_rows": len(predictions), "methods": 14,
            "context_start_offset_hours": -25, "context_end_offset_hours": -2, "target_offset_hours": 24,
            "chronos_shape": list(forecast.shape), "chronos_zero_based_index": 25, "metrics_recomputed": recalculated}


def intervals_costs_and_bootstrap():
    origins, actual, predictions, forecast = DETAILS["_arrays"]
    directory = BASE / "M03-04"
    intervals = pd.read_csv(directory / "intervalos_locais.csv")
    require(pd.DatetimeIndex(pd.to_datetime(intervals.forecast_origin)).equals(origins), "Intervalos com origens diferentes")
    close(intervals.y24, actual, atol=0)
    reported = pd.read_csv(directory / "metricas_intervalos.csv").set_index("method")
    raw_crossings = {}
    for method, q in [("hgb_raw", intervals[["p10", "p50", "p90"]].to_numpy()),
                      ("hgb_cqr", intervals[["cqr_p10", "cqr_p50", "cqr_p90"]].to_numpy()),
                      ("chronos_raw", forecast[:, [0, 4, 8], 25])]:
        require(np.isfinite(q).all(), f"Quantis não finitos: {method}")
        raw_crossings[method] = int((np.diff(q, axis=1) < 0).any(axis=1).sum())
        # O produtor usa np.asarray(..., dtype=float) antes da aritmética:
        # preservar float32 no auditor arredondaria a média da largura.
        q = np.sort(np.asarray(q, dtype=np.float64), axis=1)
        lo, mid, hi = q.T
        metrics = {"coverage": np.mean((actual >= lo) & (actual <= hi)), "width": np.mean(hi-lo),
                   "interval_score": np.mean((hi-lo)+10*np.maximum(lo-actual, 0)+10*np.maximum(actual-hi, 0))}
        for j, tau in enumerate([.1, .5, .9]):
            metrics[f"pinball_p{int(tau*100)}"] = np.maximum(tau*(actual-q[:, j]), (tau-1)*(actual-q[:, j])).mean()
        for name, value in metrics.items():
            close(value, reported.loc[method, name])
    costs = pd.read_csv(directory / "custos.csv")
    actions = dict(predictions, chronos_p20=forecast[:, 1, 25], chronos_p80=forecast[:, 7, 25])
    require(len(costs) == len(actions)*3 and not costs.duplicated(["method", "scenario"]).any(), "Grade de custos divergente")
    for row in costs.itertuples():
        error = actual-actions[row.method]
        value = (row.cost_under*np.maximum(error, 0)+row.cost_over*np.maximum(-error, 0)).mean()
        close(value, row.relative_loss_mean)
    rng = np.random.default_rng(31)
    starts = rng.integers(0, 671, size=(2000, math.ceil(671/24)))
    indices = ((starts[:, :, None]+np.arange(24)) % 671).reshape(2000, -1)[:, :671]
    ci = pd.read_csv(directory / "bootstrap_pareado.csv")
    require(len(ci) == 14 and ci.method.is_unique and set(ci.method) == set(predictions), "Bootstrap sem 14 métodos")
    require((ci.ci95_low <= ci.ci95_high).all(), "Intervalo bootstrap invertido")
    for row in ci.itertuples():
        delta = np.abs(actual-predictions["persistence"])-np.abs(actual-predictions[row.method])
        bounds = np.quantile(delta[indices].mean(axis=1), [.025, .975])
        close(delta.mean(), row.mean_gain)
        close(bounds, [row.ci95_low, row.ci95_high])
        require((row.block_hours, row.repetitions, row.seed) == (24, 2000, 31), "Parâmetros bootstrap divergentes")
    return {"interval_methods": len(reported), "quantile_crossings_before_report_rearrangement": raw_crossings,
            "point_cost_rows_recomputed": len(costs), "bootstrap_methods_recomputed": 14,
            "bootstrap_conditional_only": True, "retraining": False}


def probabilities_alarms_and_decision():
    origins, actual, predictions, _ = DETAILS["_arrays"]
    directory = BASE / "M03-04"
    data = pd.read_csv(directory / "probabilidades.csv")
    require(pd.DatetimeIndex(pd.to_datetime(data.forecast_origin)).equals(origins), "Probabilidades com origens diferentes")
    close(data.y24, actual, atol=0)
    expected_y = (data.last_observed.to_numpy()-actual >= 22.77).astype(int)
    close(data.event, expected_y, atol=0)
    policy = read(ROOT / "reports/fechamento_m00_m09/bloco2_engenharia/M05-02/politica_congelada.json")
    alarms = pd.read_csv(directory / "metricas_alarmes.csv").set_index("method")
    probabilities = pd.read_csv(directory / "metricas_probabilidades.csv").set_index("method")
    probability_checks = []
    max_daily = 0
    for method in ["raw", "calibrated", "frequency"]:
        p = data[f"p_{method}"].to_numpy()
        require(np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all(), "Probabilidade fora de [0,1]")
        clipped = np.clip(p, 1e-12, 1-1e-12)
        order = np.argsort(-p, kind="stable")
        last_equal_score = np.r_[np.flatnonzero(np.diff(p[order])), len(p)-1]
        cumulative_tp = np.cumsum(expected_y[order])[last_equal_score]
        recall = cumulative_tp/expected_y.sum()
        precision = cumulative_tp/(last_equal_score+1)
        recomputed_probability = {"brier": np.mean((p-expected_y)**2),
            "log_loss": -np.mean(expected_y*np.log(clipped)+(1-expected_y)*np.log(1-clipped)),
            "average_precision": np.sum(np.diff(np.r_[0, recall])*precision)}
        for field, value in recomputed_probability.items():
            close(value, probabilities.loc[method, field])
        probability_checks.append({"method": method, **{k: float(v) for k, v in recomputed_probability.items()}})
        threshold = policy["threshold"] if method == "calibrated" else .5
        generated = np.zeros(671, dtype=bool)
        for day in sorted(set(origins.date)):
            candidates = np.flatnonzero((origins.date == day) & (p >= threshold))[:policy["daily_budget"]]
            generated[candidates] = True
        saved = data[f"alarm_{method}"].astype(str).str.lower().isin(["true", "1"]).to_numpy()
        require(np.array_equal(saved, generated), f"Política causal divergente: {method}")
        daily = pd.Series(saved.astype(int), index=origins).groupby(origins.date).sum()
        require(int(daily.max()) <= policy["daily_budget"], "Orçamento diário excedido")
        max_daily = max(max_daily, int(daily.max()))
        tp, fp = int((saved & expected_y.astype(bool)).sum()), int((saved & ~expected_y.astype(bool)).sum())
        fn, tn = int((~saved & expected_y.astype(bool)).sum()), int((~saved & ~expected_y.astype(bool)).sum())
        for field, value in dict(tp=tp, fp=fp, fn=fn, tn=tn, alarms=int(saved.sum()), cost=fp*policy["cost_fp"]+fn*policy["cost_fn"]).items():
            close(value, alarms.loc[method, field], atol=0)
    decision = read(BASE / "M09-04/decisao_congelada_avaliada.json")
    gain = pd.read_csv(directory / "bootstrap_pareado.csv").set_index("method").loc["hgb_bloco2"]
    cqr = pd.read_csv(directory / "metricas_intervalos.csv").set_index("method").loc["hgb_cqr"]
    expected = {"mean_gain_at_least2": bool(gain.mean_gain >= 2), "gain_ci_above_zero": bool(gain.ci95_low > 0),
                "cqr_coverage_within70_90": bool(.7 <= cqr.coverage <= .9), "cqr_width_at_most100": bool(cqr.width <= 100),
                "policy_cost_better_than_never": bool(alarms.loc["calibrated", "cost"] < alarms.loc["never_alarm", "cost"]),
                "daily_alarm_limits_respected": max_daily <= 6}
    require(all(decision[k] == v for k, v in expected.items()), "Decisão não reproduz critérios declarados")
    require(decision["promotion_authorized"] is False and decision["operational_data_contract_proven"] is False,
            "Promoção/contrato operacional indevidamente afirmados")
    return {"event_horizon_between_endpoints_hours": 26, "daily_alarm_max_recomputed": max_daily,
            "frozen_daily_budget": policy["daily_budget"], "decision_checks": expected,
            "probability_metrics_recomputed": probability_checks,
            "promotion_authorized": False}


def recoveries_and_ops():
    original = read(BASE / "execucao_avaliacao_final.json")
    recovery = read(BASE / "recuperacao_relatorio_final.json")
    require(original["exit_code"] == recovery["original_exit_code"] == 1, "Falha original foi apagada")
    require(recovery["recovery_exit_code_observed"] == 0 and recovery["new_inference"] is False,
            "Recuperação não limitada à síntese")
    verify_entries([(rel(BASE / "execucao_avaliacao_final.json"), recovery["original_execution_receipt_sha256"]),
                    (original["log_path"], original["log_sha256"]),
                    (rel(BASE / "M03-04/chronos.npz"), recovery["chronos_forecast_sha256"]),
                    (rel(BASE / "M03-04/chronos.json"), recovery["chronos_metadata_sha256"])])
    chronos = read(BASE / "M03-04/chronos.json")
    require(chronos["offline"] and chronos["optimizer_steps"] == 0 and not chronos["weights_finetuned"], "Recibo Chronos inesperado")
    ci = read(BASE / "M06-02/resultado.json")
    require(ci["remote_ci_executed"] is False and ci["isolated_source_copy_verified"], "Recibo original da preparação local CI foi alterado")
    remote_verified = False
    if (BASE / "M06-02/execucao_ci_remoto.json").is_file():
        remote = read(BASE / "M06-02/execucao_ci_remoto.json")
        if remote.get("exit_code") == 0:
            from conferir_ci_remoto_bloco3 import verify_remote
            require(verify_remote()["valid"], "Evidência remota CI não confere")
            remote_verified = True
    require([e["exit_code"] for e in ci["executions"]] == [0, 1, 0], "Retornos CI local divergentes")
    for entry in ci["executions"]:
        verify_entries([(rel(BASE / "M06-02" / entry["log"]), entry["log_sha256"])])
    testlog = (BASE / "M06-02" / ci["executions"][-1]["log"]).read_text(encoding="utf-8")
    require("16 passed" in testlog, "Log da cópia não registra 16 testes aprovados")
    manifest = read(BASE / "M06-02/manifesto_pacote_ci.json")
    for path, digest in manifest["files"].items():
        copy = BASE / "M06-02/copia_isolada_1" / path
        require(copy.is_file() and sha(copy) == digest, f"Cópia CI divergente: {path}")
    require(len(manifest["files"]) == 14, "Pacote CI não contém 14 arquivos")
    require((BASE / "M06-02/adendo_copia_1.json").is_file() and (BASE / "M06-02/bloqueio_publicacao.json").is_file(), "Falha/bloqueio CI sem registro")
    first_log = (BASE / "M06-02/copia_isolada_2.log").read_text(encoding="utf-8")
    require("15 passed" in first_log and "m08_gru_autoral" in first_log, "Primeira falha CI não preservada no log")
    registry = read(BASE / "M06-03/registry_mlflow.json")
    require(registry["versions"] == ["1", "2"] and registry["active_version"] == "1", "Registro/rollback local divergente")
    require([r["resolved_version"] for r in registry["transitions"]] == ["1", "2", "1"], "Transições registry divergentes")
    require(all(row["max_prediction_difference"] == 0 for row in registry["transitions"]), "Paridade de registry não satisfeita")
    shadow, continuity, drift, security, load, cloud = [read(BASE / f"M06-{i:02}/resultado.json") for i in range(4, 10)]
    require(shadow["live_emissions"] == shadow["observed_live_hours"] == 0, "Shadow live indevidamente afirmado")
    require(continuity["live_observation_hours"] == 0 and not continuity["continuous_service_proven"], "Continuidade indevidamente afirmada")
    require(all(v is False for v in continuity["operational_criteria"].values()), "Critérios prospectivos C1-C4 devem permanecer abertos")
    require(not drift["operational_response_tested_live"], "Resposta de drift ao vivo indevidamente afirmada")
    require(security["all_passed"] and security["service_stopped"] and not security["production_security_certified"], "Segurança sem limite local")
    require(sum(v["completed"] for v in load["measurements"]) == 480 and load["all_local_slos_passed"] and not load["sustained_operation_proven"], "Carga sem limite local")
    require(not cloud["deployment_executed"] and not cloud["actual_cloud_cost_observed"], "Cloud indevidamente afirmada")
    WARNINGS.extend(["Execução final original terminou em 1 por impressão cp1252; NPZ preservado e somente síntese UTF-8 recuperada com retorno 0.",
                     "Primeira cópia CI omitiu dependência transitiva; tentativa/log preservados, empacotamento corrigido e segunda cópia registrou 16 aprovações.",
                     "M06-03 preserva falha de serialização inicial e adendo de compatibilidade anterior à segunda execução.",
                     "Live shadow, continuidade, resposta de drift, segurança/recursos em produção e cloud continuam sem comprovação."])
    if not remote_verified:
        WARNINGS.append("CI remoto ainda sem comprovação; pacote local não basta.")
    return {"original_final_exit": 1, "report_recovery_exit": 0, "new_model_inference_during_audit": False,
            "ci_isolated_source_files": 14, "ci_copy_passed_tests_recorded": 16, "remote_ci_executed": remote_verified,
            "registry_versions": [1, 2], "registry_transition": [1, 2, 1], "identical_model_package_versions": True,
            "live_shadow_emissions": 0, "load_requests_recorded": 480, "cloud_deployed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Arquivo NOVO dentro do projeto; padrão gera nome único em reverificacoes/.")
    args = parser.parse_args()
    for name, operation in [("eighteen_items", all_items), ("agent_manifests", manifests),
                            ("frozen_code_and_chronology", frozen_and_time), ("final_arrays_and_14_metrics", final_arrays_and_metrics),
                            ("intervals_costs_and_conditional_bootstrap", intervals_costs_and_bootstrap),
                            ("class_probabilities_alarm_cap_and_decision", probabilities_alarms_and_decision),
                            ("preserved_failures_partial_operation_and_ci", recoveries_and_ops)]:
        check(name, operation)
    DETAILS.pop("_arrays", None)
    valid = all(row["passed"] for row in CHECKS)
    output = {"schema": "bloco3-independent-audit-v1", "audited_at_utc": datetime.now(timezone.utc).isoformat(),
              "author": "Codex — revisão separada dos produtores finais; não é avaliação humana ou certificação pessoal",
              "scope": IDS, "valid": valid, "checks": CHECKS, "details": DETAILS, "warnings": WARNINGS,
              "audit_code_sha256": sha(Path(__file__)), "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
              "models_loaded": False, "models_executed": False, "old_tests_rerun": False, "credentials_read": False,
              "producer_files_modified": False, "operational_approval": False, "exit_code": 0 if valid else 1}
    import uuid
    destination=(args.output or BASE/"reverificacoes"/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")+"_"+uuid.uuid4().hex[:8]+".json")).resolve()
    if not destination.is_relative_to(ROOT) or destination.exists():
        raise ValueError("Saída deve ser arquivo novo dentro do projeto; não sobrescrever evidência.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x",encoding="utf-8") as stream:
        stream.write(json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"valid": valid, "checks": CHECKS, "output": rel(destination)}, ensure_ascii=False))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
