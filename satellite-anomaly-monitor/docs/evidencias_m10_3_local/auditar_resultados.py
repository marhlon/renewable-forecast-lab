"""Audita 33 candidatas DEV e o replay da única política congelada no teste.

Não importa a função autoral, o core ou qualquer runner. Não ajusta modelos,
não reconstitui a floresta e não avalia políticas alternativas no teste.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[2]
DEFAULT_RUN = PROJECT / "reports/m10_3/20261123T195301Z_332fb306"
M102 = PROJECT / "reports/m10_2/20261119T101049Z_253ff59f"
M102_DATA = PROJECT / "data/reference/esa_mission1_m10_2"
TEST_DATA = PROJECT / "data/reference/esa_mission1_m10_3"
PROTOCOL = PROJECT / "docs/m10_3/protocolo_politica.json"
OUTPUT = Path(__file__).with_name("auditoria_resultados.json")
CHANNELS = ("channel_50", "channel_51", "channel_52")
EVENT_COLUMNS = ["id", "estado", "inicio_anotado_utc", "primeiro_alarme_utc", "atraso_min", "anotacoes_canal_intervalo"]
ALARM_COLUMNS = ["instante_utc", "classe", "id_atribuido"]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def csv(path):
    return pd.read_csv(path, float_precision="round_trip")


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def times(values):
    return pd.DatetimeIndex(pd.to_datetime(values, format="mixed", utc=True)).astype("datetime64[ns, UTC]")


def same(a, b, name):
    np.testing.assert_allclose(np.asarray(a, dtype=float), np.asarray(b, dtype=float),
                               rtol=1e-12, atol=1e-10, equal_nan=True, err_msg=name)


def same_frame(actual, expected, name, temporal=()):
    require(actual.columns.tolist() == expected.columns.tolist() and len(actual) == len(expected),
            f"Formato divergente: {name}")
    for column in expected:
        if column in temporal:
            np.testing.assert_array_equal(times(actual[column]).asi8, times(expected[column]).asi8,
                                          err_msg=f"{name}.{column}")
        elif pd.api.types.is_numeric_dtype(expected[column]):
            same(actual[column], expected[column], f"{name}.{column}")
        else:
            a = actual[column].astype(object).where(actual[column].notna(), None).tolist()
            b = expected[column].astype(object).where(expected[column].notna(), None).tolist()
            require(a == b, f"Valores divergentes: {name}.{column}")


def same_record(actual, expected, name):
    require(set(actual) == set(expected), f"Campos divergentes: {name}")
    for key, value in expected.items():
        if value is None:
            require(actual[key] is None, f"Valor indefinido convertido: {name}.{key}")
        elif isinstance(value, (int, float, bool, np.number, np.bool_)):
            same(actual[key], value, f"{name}.{key}")
        else:
            require(actual[key] == value, f"Valor divergente: {name}.{key}")


def replay(scores, valid, threshold, k):
    """Uma passagem causal. Para o teste, só é chamada com a política congelada."""
    starts = np.zeros(len(valid), dtype=bool)
    count = largest = above = 0
    for i, (score, available) in enumerate(zip(scores, valid)):
        if available and score >= threshold:
            count += 1
            above += 1
            largest = max(largest, count)
            if count == k:
                starts[i] = True
        else:
            count = 0
    diagnostic = {"pontos_atingiram_limiar": above, "maior_sequencia_acima": largest,
                  "escore_maximo_utilizavel": float(scores[valid].max()) if valid.any() else None}
    return starts, diagnostic


def context(index, valid, events, step):
    require(len(index) == len(valid) and not index.hasnans, "Dimensão temporal inválida.")
    require(np.all(np.diff(index.asi8) == step * 10**9), "Grade irregular ou filtrada.")
    require(events[["ID", "Channel", "Category", "StartTime", "EndTime"]].notna().all().all(), "Evento incompleto.")
    require(events.Channel.isin(CHANNELS).all() and events.Category.isin(("Anomaly", "Rare Event", "Communication Gap")).all(), "Canal ou categoria inválida.")
    require(events.groupby("ID").Category.nunique().le(1).all(), "Categoria inconsistente por ID.")
    starts, ends = times(events.StartTime), times(events.EndTime)
    require(np.all(starts.asi8 <= ends.asi8), "Intervalo de evento invertido.")
    ignore, anomaly = np.zeros(len(index), dtype=bool), np.zeros(len(index), dtype=bool)
    spans = {}
    for row, begin, end in zip(events.itertuples(index=False), starts.asi8, ends.asi8):
        # Intervalos fechados; não expandir uma união para o fecho de seu envelope.
        mask = (index.asi8 >= begin) & (index.asi8 <= end)
        if row.Category == "Anomaly":
            spans.setdefault(str(row.ID), []).append({"channel": row.Channel, "start": int(begin),
                                                     "end": int(end), "mask": mask})
            anomaly |= mask
        else:
            ignore |= mask
    eligible = valid & ~ignore
    nominal = eligible & ~anomaly
    observable = {eid: any(np.any(eligible & span["mask"]) for span in group) for eid, group in spans.items()}
    return {"index": index, "valid": valid, "step": step, "ignore": ignore, "anomaly": anomaly,
            "eligible": eligible, "nominal": nominal, "spans": spans, "observable": observable}


def evaluate(ctx, starts):
    index, valid, spans = ctx["index"], ctx["valid"], ctx["spans"]
    require(starts.dtype == bool and starts.shape == valid.shape and not np.any(starts & ~valid), "Início fora do contrato.")
    first = {}
    counts = {"atribuido": 0, "repetido_no_evento": 0, "sem_anotacao": 0, "ignorado_categoria": 0}
    alarms = []
    for position in np.flatnonzero(starts):
        assigned = None
        if ctx["ignore"][position]:
            status = "ignorado_categoria"
        elif not ctx["anomaly"][position]:
            status = "sem_anotacao"
        else:
            choices = [(span["end"], eid) for eid, group in spans.items() if eid not in first
                       for span in group if span["mask"][position]]
            if choices:
                _, assigned = min(choices)
                first[assigned] = int(position)
                status = "atribuido"
            else:
                status = "repetido_no_evento"
        counts[status] += 1
        alarms.append({"instante_utc": index[position].isoformat(), "classe": status, "id_atribuido": assigned})
    begin = {eid: min(span["start"] for span in group) for eid, group in spans.items()}
    delays = {eid: (int(index.asi8[position]) - begin[eid]) / (60 * 10**9) for eid, position in first.items()}
    observable = sum(ctx["observable"].values())
    exposure = float(ctx["nominal"].sum() * ctx["step"] / 86400)
    audited_starts = int(starts.sum()) - counts["ignorado_categoria"]
    summary = {"instantes_na_grade": len(index), "instantes_utilizaveis": int(valid.sum()),
        "ids_anomalia": len(spans), "ids_observaveis": observable, "ids_nao_observaveis": len(spans) - observable,
        "ids_detectados": len(first), "recall_observaveis": len(first) / observable if observable else None,
        "recall_todos_ids": len(first) / len(spans) if spans else None,
        "precisao_por_inicio_avaliavel": len(first) / audited_starts if audited_starts else None,
        "alarmes_total": int(starts.sum()), "alarmes_atribuidos": counts["atribuido"],
        "alarmes_repetidos_no_evento": counts["repetido_no_evento"], "alarmes_sem_anotacao": counts["sem_anotacao"],
        "alarmes_ignorados_categoria": counts["ignorado_categoria"],
        "exposicao_sem_anotacao_dias_equivalentes": exposure,
        "taxa_sem_anotacao_por_dia": counts["sem_anotacao"] / exposure if exposure else None,
        "atraso_mediano_min": float(np.median(list(delays.values()))) if delays else None,
        "atraso_p90_min": float(np.quantile(list(delays.values()), .9)) if delays else None}
    details = []
    for eid, group in sorted(spans.items()):
        details.append({"id": eid, "estado": "detectado" if eid in first else ("perdido" if ctx["observable"][eid] else "nao_observavel"),
            "inicio_anotado_utc": pd.Timestamp(begin[eid], unit="ns", tz="UTC").isoformat(),
            "primeiro_alarme_utc": index[first[eid]].isoformat() if eid in first else None,
            "atraso_min": delays.get(eid), "anotacoes_canal_intervalo": len(group)})
    channel_rows = []
    for channel in CHANNELS:
        annotated = {eid: [s for s in group if s["channel"] == channel] for eid, group in spans.items()
                     if any(s["channel"] == channel for s in group)}
        seen = {eid for eid, group in annotated.items() if any(np.any(ctx["eligible"] & s["mask"]) for s in group)}
        hits = {eid for eid in seen if eid in first and any(s["mask"][first[eid]] for s in annotated[eid])}
        channel_rows.append({"canal_anotado": channel, "ids_anotados": len(annotated), "ids_observaveis": len(seen),
            "ids_primeiro_alarme_no_intervalo": len(hits), "fracao_entre_observaveis": len(hits) / len(seen) if seen else None})
    return summary, details, alarms, channel_rows


def audit(run):
    report = read_json(run / "resultado.json")
    protocol = read_json(PROTOCOL)
    policy_path = run / "politica_congelada.json"
    policy = read_json(policy_path)
    m102 = read_json(M102 / "resultado.json")
    m102_source = read_json(M102_DATA / "protocolo.json")
    require(report["schema"] == "satmon-m10-3-result-v1" and report["completed"] is True and report["run_id"] == run.name, "Resultado incompleto.")
    require(report["source_run_id"] == policy["source_run_id"] == m102["run_id"] == M102.name, "A execução M10.2 fixada foi substituída.")
    require(policy["schema"] == "satmon-m10-3-frozen-policy-v1" and policy["status"] == report["politica_status"] == "congelada", "Política não congelada.")
    require(policy["test_opened_at_freeze"] is False and policy["selection_partition"] == "2008–2010", "Declaração de congelamento incompatível.")
    require(report["periodo_reservado_avaliado"] is True and report["operational_approval"] is False and report["autoria_conferida_contra_referencia"] is True, "Escopo inesperado.")
    latest = read_json(run.parent / "latest_run.json")
    require(latest["run_id"] == run.name and latest["resultado_sha256"] == sha(run / "resultado.json"), "Ponteiro latest divergente.")
    checked_hashes = {}

    def check_hash(path, expected):
        digest = sha(path)
        require(digest == expected, f"SHA-256 divergente: {path}")
        checked_hashes[path.relative_to(PROJECT).as_posix()] = digest

    check_hash(M102 / "resultado.json", policy["source_receipt_sha256"])
    check_hash(PROTOCOL, report["protocol_sha256"])
    require(policy["protocol_sha256"] == report["protocol_sha256"], "Protocolo diferente na política.")
    check_hash(policy_path, report["politica_sha256"])
    check_hash(PROJECT / "notebooks/m10_3_alarme_autoral.py", policy["authorship_sha256"])
    require(report["authorship_sha256"] == policy["authorship_sha256"], "Função diferente entre política e resultado.")
    check_hash(PROJECT / "scripts/executar_m10_3.py", report["code_sha256"]["runner"])
    check_hash(PROJECT / "src/satmon/alarmes_m10_3.py", report["code_sha256"]["core"])
    check_hash(M102_DATA / "protocolo.json", protocol["source_spec_m10_2_sha256"])
    require(m102["source_spec_sha256"] == protocol["source_spec_m10_2_sha256"], "Fonte M10.2 divergente.")
    for name, identity in m102_source["files"].items():
        require((M102_DATA / name).stat().st_size == identity["bytes"], f"Tamanho alterado: {name}")
        check_hash(M102_DATA / name, identity["sha256"])
    for name, expected in m102["output_sha256"].items():
        check_hash(M102 / name, expected)
    check_hash(PROJECT / "scripts/executar_m10_2.py", m102["code_sha256"]["runner"])
    check_hash(PROJECT / "src/satmon/detectores_m10_2.py", m102["code_sha256"]["core"])
    for name, expected in report["output_sha256"].items():
        check_hash(run / name, expected)
    require(policy["development_scores_sha256"] == m102["output_sha256"]["escores_desenvolvimento.csv.gz"], "Escores DEV não são os fixados.")

    step = protocol["grid_step_seconds"]
    k = policy["consecutivos"]
    require(k == protocol["consecutivos"] and protocol["quantil_metodo"] == "higher", "Método de quantil ou confirmação divergente.")
    dev = csv(M102 / "escores_desenvolvimento.csv.gz")
    dev_index = times(dev.timestamp)
    expected_dev = pd.date_range(protocol["desenvolvimento_inicio_utc"], protocol["teste_inicio_utc"], freq=f"{step}s", inclusive="left").astype("datetime64[ns, UTC]")
    np.testing.assert_array_equal(dev_index.asi8, expected_dev.asi8)
    require(pd.api.types.is_bool_dtype(dev.utilizavel), "Disponibilidade DEV não booleana.")
    dev_valid = dev.utilizavel.to_numpy()
    old_events = csv(M102_DATA / "eventos.csv")
    dev_events = old_events.loc[old_events.partition.eq("desenvolvimento")].copy()
    dev_ctx = context(dev_index, dev_valid, dev_events, step)
    np.testing.assert_array_equal(dev_ctx["eligible"], dev.entra_no_ranking)
    np.testing.assert_array_equal(dev_ctx["anomaly"], dev.anotacao_anomaly)
    candidates = []
    methods = protocol["metodos_em_ordem_de_desempate"]
    budget = protocol["max_alarmes_sem_anotacao_por_dia_equivalente_no_dev"]
    for method in methods:
        scores = dev[method].to_numpy(dtype=float)
        require(np.isfinite(scores[dev_valid]).all() and np.isnan(scores[~dev_valid]).all(), f"Escores DEV inválidos: {method}")
        ordered = np.sort(scores[dev_valid])
        for q in protocol["candidatos_quantil"]:
            threshold = float(ordered[math.ceil(q * (len(ordered) - 1))])
            starts, _ = replay(scores, dev_valid, threshold, k)
            summary, _, _, _ = evaluate(dev_ctx, starts)
            viable = summary["taxa_sem_anotacao_por_dia"] <= budget and summary["ids_detectados"] > 0
            candidates.append({"metodo": method, "quantil": q, "limiar": threshold, "viavel": viable, **summary})
    viable = [c for c in candidates if c["viavel"]]
    require(viable, "Nenhuma candidata DEV viável.")
    winner = min(viable, key=lambda row: (-row["ids_detectados"], row["taxa_sem_anotacao_por_dia"],
        row["atraso_mediano_min"], methods.index(row["metodo"]), -row["quantil"]))
    for row in candidates:
        row["escolhida"] = row is winner
    require(len(candidates) == report["n_candidatos"] == 33 and len(viable) == report["n_viaveis"], "Contagem de candidatas divergente.")
    same_frame(csv(run / "candidatos_dev.csv"), pd.DataFrame(candidates), "Todas as candidatas somente DEV")
    same_record(policy["candidato"], winner, "Candidata congelada selecionada")

    # A partir daqui existe exatamente um limiar, um método e um k para TESTE.
    threshold = policy["candidato"]["limiar"]
    frozen_method = policy["candidato"]["metodo"]
    dev_starts, dev_diagnostic = replay(dev[frozen_method].to_numpy(dtype=float), dev_valid, threshold, k)
    dev_summary, dev_detail, dev_alarm_rows, dev_channels = evaluate(dev_ctx, dev_starts)
    dev_summary = {"particao": "desenvolvimento", **dev_summary, **dev_diagnostic}

    source = read_json(TEST_DATA / "proveniencia.json")
    check_hash(TEST_DATA / "proveniencia.json", report["source_test_sha256"])
    require(source["source_spec_m10_2_sha256"] == protocol["source_spec_m10_2_sha256"], "Origem do teste divergente.")
    for name, expected in source["files"].items():
        check_hash(TEST_DATA / name, expected)
    test_raw = csv(TEST_DATA / "grade_teste.csv.gz")
    test_events_source = csv(TEST_DATA / "eventos_teste.csv")
    require(not (set(old_events.ID) & set(test_events_source.ID)), "ID compartilhado entre períodos.")
    test_index = times(test_raw.timestamp)
    expected_test = pd.date_range(protocol["teste_inicio_utc"], protocol["teste_fim_exclusivo_utc"], freq=f"{step}s", inclusive="left").astype("datetime64[ns, UTC]")
    np.testing.assert_array_equal(test_index.asi8, expected_test.asi8)
    values = test_raw[[f"{c}_value" for c in CHANNELS]].to_numpy(dtype=float)
    test_valid = np.isfinite(values).all(axis=1)
    for channel in CHANNELS:
        samples = times(test_raw[f"{channel}_sample_time"])
        known = ~samples.isna()
        ages = np.full(len(test_index), np.nan)
        ages[known] = (test_index.asi8[known] - samples.asi8[known]) / 1e9
        same(test_raw[f"{channel}_age_seconds"], ages, f"Idades TESTE: {channel}")
        has_value = test_raw[f"{channel}_value"].notna().to_numpy()
        require(np.all(samples.asi8[known] <= test_index.asi8[known]) and np.all(samples[known] >= pd.Timestamp(protocol["teste_inicio_utc"])), "Futuro ou fronteira temporal violada.")
        require(not np.isinf(values).any() and not np.any(has_value & (~known | (ages > source["max_age_seconds"]))), "Frescor do teste violado.")
    test = csv(run / "escores_teste.csv.gz")
    require(test.columns.tolist() == ["timestamp", "utilizavel", "escore", "atingiu_limiar", "inicio_alarme"], "Colunas TESTE divergentes.")
    np.testing.assert_array_equal(times(test.timestamp).asi8, test_index.asi8)
    np.testing.assert_array_equal(test.utilizavel, test_valid)
    score = test.escore.to_numpy(dtype=float)
    require(np.isfinite(score[test_valid]).all() and np.isnan(score[~test_valid]).all(), "Escores TESTE inválidos.")
    test_starts, test_diagnostic = replay(score, test_valid, threshold, k)
    np.testing.assert_array_equal(test.inicio_alarme, test_starts)
    np.testing.assert_array_equal(test.atingiu_limiar, test_valid & (score >= threshold))
    test_ctx = context(test_index, test_valid, test_events_source, step)
    test_summary, test_detail, test_alarm_rows, test_channels = evaluate(test_ctx, test_starts)
    test_summary = {"particao": "teste", **test_summary, **test_diagnostic}

    summaries = [dev_summary, test_summary]
    same_frame(csv(run / "metricas_episodios.csv"), pd.DataFrame(summaries), "Métricas da política congelada")
    for actual, expected in zip(report["metricas"], summaries):
        same_record(actual, expected, f"Resumo JSON: {expected['particao']}")
    for name, details, alarms, channels in (("desenvolvimento", dev_detail, dev_alarm_rows, dev_channels),
                                            ("teste", test_detail, test_alarm_rows, test_channels)):
        same_frame(csv(run / f"eventos_{name}.csv"), pd.DataFrame(details, columns=EVENT_COLUMNS),
                   f"IDs {name}", temporal=("inicio_anotado_utc", "primeiro_alarme_utc"))
        same_frame(csv(run / f"alarmes_{name}.csv"), pd.DataFrame(alarms, columns=ALARM_COLUMNS),
                   f"Inícios {name}", temporal=("instante_utc",))
        same_frame(csv(run / f"cobertura_canais_{name}.csv"), pd.DataFrame(channels), f"Cobertura por canal {name}")

    delta = report["max_delta_escore_dev_para_pontuar_teste"]
    require(report["reconstituicao_floresta_usou_somente_ajuste_original"] is True and frozen_method == "score_isolation", "Método ou declaração de reconstrução diferente desta entrega.")
    require(np.isfinite(delta) and 0 <= delta <= 1e-12 + 1e-10 * abs(dev[frozen_method]).max(), "A reconstrução declarada excedeu a tolerância.")
    frozen = pd.Timestamp(policy["frozen_at_utc"])
    require(frozen.tzinfo is not None, "Congelamento sem fuso.")
    test_output_mtime = pd.Timestamp((run / "escores_teste.csv.gz").stat().st_mtime, unit="s", tz="UTC")
    require(frozen <= test_output_mtime, "O congelamento é posterior à gravação dos escores de teste.")
    require(sha(policy_path) == report["politica_sha256"], "A política mudou durante a auditoria.")
    return {"schema": "satmon-m10-3-independent-audit-v1", "verified": True,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(), "run_id": run.name,
        "run_directory": run.relative_to(PROJECT).as_posix(),
        "audit_versions": {"numpy": np.__version__, "pandas": pd.__version__},
        "method": "Independent causal counter and union-interval assignment; 33 DEV candidates, exactly one frozen TEST policy. No project code imported, model fit or forest reconstruction.",
        "checks": {"pinned_m10_2_source_and_all_hashes": True, "frozen_policy_code_author_latest_hashes": True,
            "all_33_development_candidates_recomputed": True, "feasibility_and_tiebreak_winner": True,
            "one_fixed_test_policy_replayed": True, "missing_rows_preserved_and_ignore_not_used_for_resets": True,
            "id_union_assignment_repetition_and_ignore_precedence": True, "nominal_exposure_and_rates": True,
            "undefined_precision_and_delays_preserved": True, "event_and_channel_details_recomputed": True,
            "sample_age_availability_and_partition_contract": True},
        "checked_hashes": checked_hashes, "candidate_count": len(candidates), "viable_candidate_count": len(viable),
        "selected_policy": winner, "same_cutoff_selected_for_quantiles": [c["quantil"] for c in candidates if c["metodo"] == frozen_method and c["limiar"] == threshold],
        "metrics_recomputed": summaries,
        "nominal_exposure_grid_rows": {"desenvolvimento": int(dev_ctx["nominal"].sum()), "teste": int(test_ctx["nominal"].sum())},
        "test_event_states": test_detail, "channel_coverage_recomputed": {"desenvolvimento": dev_channels, "teste": test_channels},
        "freeze_evidence": {"policy_sha256": sha(policy_path), "frozen_at_utc": frozen.isoformat(),
            "test_opened_at_freeze_declared": policy["test_opened_at_freeze"],
            "test_scores_file_mtime_utc": test_output_mtime.isoformat(), "frozen_before_test_scores_file_mtime": True,
            "first_test_read_timestamp_available": False,
            "limit": "File chronology and declarations support the preserved artifact order; no independent timestamp records the first test-file read."},
        "forest_reconstruction_receipt_only": {"declared_original_fit_only": report["reconstituicao_floresta_usou_somente_ajuste_original"],
            "declared_max_development_score_delta": delta, "forest_reconstructed_by_auditor": False,
            "limit": "The runner asserted matching development scores/starts before test scoring. No checkpoint or rebuilt development score vector is persisted to independently repeat that assertion."},
        "analytic_k1_conclusion": "With zero usable points reaching the frozen threshold, no positive confirmation count could emit an alarm. This follows from the condition; k=1 was not replayed on the test." if test_diagnostic["pontos_atingiram_limiar"] == 0 else None,
        "test_alternative_policies_evaluated": 0, "models_fitted_by_auditor": 0,
        "limits": "This checks persisted artifacts, episode rules and the supplied temporal grid, not physical ground-arrival latency, annotation completeness, ESA operational validity or the full raw mission archives."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    args = parser.parse_args()
    result = audit(args.run_dir.resolve())
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Auditoria aprovada: {result['candidate_count']} candidatas DEV; uma política congelada no TESTE.")
    print(f"Run: {result['run_id']}; JSON: {OUTPUT}")


if __name__ == "__main__":
    main()
