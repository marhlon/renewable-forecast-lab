"""Audita tabelas M10.4 e a referência persistida, sem fit ou novas ablações.

Escores das 11 florestas novas não foram persistidos. Nelas, esta auditoria
verifica identidades, coortes, agregações, IDs e coerência algébrica; não
alega reconstruir escores, cortes ou árvores. A referência é recalculável.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[2]
RUN = PROJECT / "reports/m10_4/20261124T152509Z_3878d5e2"
M102 = PROJECT / "reports/m10_2/20261119T101049Z_253ff59f"
M103 = PROJECT / "reports/m10_3/20261123T195301Z_332fb306"
D2 = PROJECT / "data/reference/esa_mission1_m10_2"
D3 = PROJECT / "data/reference/esa_mission1_m10_3"
PROTOCOL = PROJECT / "docs/m10_4/protocolo_diagnostico.json"
OUTPUT = Path(__file__).with_name("auditoria_resultados.json")
CHANNELS = ("channel_50", "channel_51", "channel_52")
VARIANTS = ("tres_canais", "sem_50", "sem_51", "sem_52")
FROZEN_SHA = "8d4259755d41c1c1194dd4aa2bde15adacb9ee052b94c1e23395a1fe296d2c81"


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
                               rtol=1e-11, atol=1e-10, equal_nan=True, err_msg=name)


def same_frame(actual, expected, name, temporal=()):
    require(actual.columns.tolist() == expected.columns.tolist() and len(actual) == len(expected), f"Formato divergente: {name}")
    for column in expected:
        if column in temporal:
            np.testing.assert_array_equal(times(actual[column]).asi8, times(expected[column]).asi8,
                                          err_msg=f"{name}.{column}")
        elif pd.api.types.is_numeric_dtype(expected[column]):
            same(actual[column], expected[column], f"{name}.{column}")
        else:
            left = actual[column].astype(object).where(actual[column].notna(), None).tolist()
            right = expected[column].astype(object).where(expected[column].notna(), None).tolist()
            require(left == right, f"Valores divergentes: {name}.{column}")


def bound(scores, mask, k):
    """Máximo dos mínimos por alinhamento de vetores; primeiro fim empatado."""
    if k == 1:
        indices = np.flatnonzero(mask)
        values = scores[indices]
    elif k == 2:
        indices = np.flatnonzero(mask[:-1] & mask[1:]) + 1
        values = np.minimum(scores[indices - 1], scores[indices])
    else:
        raise ValueError("Esta auditoria usa apenas k=1 e k=2 fixados no protocolo.")
    if not len(indices):
        return {"limiar_maximo": None, "indice_confirmacao": None}
    pos = int(np.argmax(values))
    return {"limiar_maximo": float(values[pos]), "indice_confirmacao": int(indices[pos])}


def ap(y, scores):
    y = np.asarray(y, dtype=bool)
    order = np.argsort(-scores, kind="stable")
    sorted_scores, positives = scores[order], y[order]
    ends = np.flatnonzero(np.r_[sorted_scores[:-1] != sorted_scores[1:], True])
    tp = positives.cumsum()[ends]
    return float(np.dot(tp / (ends + 1), np.diff(np.r_[0, tp])) / y.sum())


def ranks(values):
    _, inverse, count = np.unique(values, return_inverse=True, return_counts=True)
    last = np.cumsum(count)
    average = (last - count + last - 1) / 2 + 1
    return average[inverse]


def context(index, valid, events):
    spans, masks = {}, {}
    ignored, anomaly = np.zeros(len(index), bool), np.zeros(len(index), bool)
    starts, ends = times(events.StartTime), times(events.EndTime)
    require(np.all(starts.asi8 <= ends.asi8), "Evento invertido.")
    for row, start, end in zip(events.itertuples(index=False), starts.asi8, ends.asi8):
        mask = (index.asi8 >= start) & (index.asi8 <= end)
        if row.Category == "Anomaly":
            spans.setdefault(row.ID, []).append({"start": int(start), "end": int(end), "channel": row.Channel, "mask": mask})
            masks.setdefault(row.ID, np.zeros(len(index), bool))[:] |= mask
            anomaly |= mask
        else:
            require(row.Category in ("Rare Event", "Communication Gap"), "Categoria desconhecida.")
            ignored |= mask
    eligible = valid & ~ignored
    return {"index": index, "valid": valid, "spans": spans, "masks": masks, "ignore": ignored,
        "anomaly": anomaly, "eligible": eligible, "nominal": eligible & ~anomaly,
        "observable": {eid: bool(np.any(mask & eligible)) for eid, mask in masks.items()}}


def replay(scores, valid, threshold):
    starts = np.zeros(len(scores), bool)
    count = 0
    for i, (score, usable) in enumerate(zip(scores, valid)):
        count = count + 1 if usable and score >= threshold else 0
        if count == 2:
            starts[i] = True
    return starts


def episodes(ctx, starts):
    first, counts = {}, dict(atribuido=0, repetido_no_evento=0, sem_anotacao=0, ignorado_categoria=0)
    for i in np.flatnonzero(starts):
        if ctx["ignore"][i]:
            status = "ignorado_categoria"
        elif not ctx["anomaly"][i]:
            status = "sem_anotacao"
        else:
            active = [(span["end"], eid) for eid, spans in ctx["spans"].items() if eid not in first
                      for span in spans if span["mask"][i]]
            if active:
                _, eid = min(active)
                first[eid] = int(i)
                status = "atribuido"
            else:
                status = "repetido_no_evento"
        counts[status] += 1
    delays = {eid: (int(ctx["index"].asi8[i]) - min(s["start"] for s in ctx["spans"][eid])) / 60e9
              for eid, i in first.items()}
    observed = sum(ctx["observable"].values())
    exposure = float(ctx["nominal"].sum() / 96)
    available_starts = int(starts.sum()) - counts["ignorado_categoria"]
    return {"instantes_na_grade": len(starts), "instantes_utilizaveis": int(ctx["valid"].sum()),
        "ids_anomalia": len(ctx["masks"]), "ids_observaveis": observed,
        "ids_nao_observaveis": len(ctx["masks"]) - observed, "ids_detectados": len(first),
        "recall_observaveis": len(first) / observed if observed else None,
        "recall_todos_ids": len(first) / len(ctx["masks"]) if ctx["masks"] else None,
        "precisao_por_inicio_avaliavel": len(first) / available_starts if available_starts else None,
        "alarmes_total": int(starts.sum()), "alarmes_atribuidos": counts["atribuido"],
        "alarmes_repetidos_no_evento": counts["repetido_no_evento"], "alarmes_sem_anotacao": counts["sem_anotacao"],
        "alarmes_ignorados_categoria": counts["ignorado_categoria"],
        "exposicao_sem_anotacao_dias_equivalentes": exposure,
        "taxa_sem_anotacao_por_dia": counts["sem_anotacao"] / exposure,
        "atraso_mediano_min": float(np.median(list(delays.values()))) if delays else None,
        "atraso_p90_min": float(np.quantile(list(delays.values()), .9)) if delays else None}, first


def annual(part, z, scores, ctx, threshold):
    score_rows, channel_rows, pair_rows = [], [], []
    years = ctx["index"].year.to_numpy()
    for year in np.unique(years):
        for name, cohort in (("utilizavel", ctx["valid"]), ("sem_anotacao", ctx["nominal"])):
            mask = (years == year) & cohort
            selected = scores[mask]
            q = np.quantile(selected, [.5, .9, .99, .9995])
            score_rows.append({"particao": part, "ano": int(year), "coorte": name, "instantes": len(selected),
                "p50": q[0], "p90": q[1], "p99": q[2], "p9995": q[3], "s1": float(selected.max()),
                "s2": bound(scores, mask, 2)["limiar_maximo"], "limiar_congelado": threshold,
                "pontos_no_corte": int(np.count_nonzero(selected >= threshold))})
            if name != "sem_anotacao":
                continue
            for j, channel in enumerate(CHANNELS):
                p10, med, p90 = np.quantile(z[mask, j], [.1, .5, .9])
                channel_rows.append({"particao": part, "ano": int(year), "canal": channel, "instantes": int(mask.sum()),
                                     "z_p10": p10, "z_p50": med, "z_p90": p90})
            for a, channel in enumerate(CHANNELS):
                for b in range(a + 1, 3):
                    pair_rows.append({"particao": part, "ano": int(year), "par": f"{channel}/{CHANNELS[b]}",
                        "instantes": int(mask.sum()), "spearman": float(np.corrcoef(ranks(z[mask, a]), ranks(z[mask, b]))[0, 1])})
    return score_rows, channel_rows, pair_rows


def audit(run):
    result, r2, r3 = read_json(run / "resultado.json"), read_json(M102 / "resultado.json"), read_json(M103 / "resultado.json")
    policy, protocol = read_json(M103 / "politica_congelada.json"), read_json(PROTOCOL)
    require(result["schema"] == "satmon-m10-4-result-v1" and result["completed"] and result["run_id"] == run.name, "Resultado incompleto.")
    require(result["source_m10_2_run_id"] == r2["run_id"] == M102.name and result["source_m10_3_run_id"] == r3["run_id"] == M103.name, "Cadeia de execuções substituída.")
    require(result["seeds"] == protocol["seeds"] == [17, 29, 41] and tuple(protocol["variantes"]) == VARIANTS, "Desenho de variantes alterado.")
    require(protocol["consecutivos"] == 2 and protocol["quantil_dev"] == .9995 and protocol["metodo_quantil"] == "higher", "Parâmetros de confirmação ou quantil alterados.")
    require(result["author_cases_passed"] == 7 and result["verified_against_reference_real_data"] is True, "Verificação autoral ausente.")
    for key in ("same_full_channel_cohort", "original_scores_used_verbatim", "test_is_retrospective", "frozen_policy_unchanged"):
        require(result[key] is True, f"Declaração incompatível: {key}")
    require(result["test_used_to_choose_parameters"] is False and result["operational_approval"] is False and result["forests_fitted_only_on_adjustment"] == 11, "Escopo incompatível.")
    checked_hashes = {}

    def check_hash(path, expected):
        actual = sha(path)
        require(actual == expected, f"SHA-256 divergente: {path}")
        checked_hashes[path.relative_to(PROJECT).as_posix()] = actual

    paths = {"receipt_m10_2": M102 / "resultado.json", "receipt_m10_3": M103 / "resultado.json",
        "scores_dev": M102 / "escores_desenvolvimento.csv.gz", "scores_test": M103 / "escores_teste.csv.gz",
        "policy": M103 / "politica_congelada.json"}
    for name, path in paths.items():
        check_hash(path, result["inputs_sha256"][name])
    require(result["inputs_sha256"]["policy"] == r3["politica_sha256"] == FROZEN_SHA, "A política congelada original mudou.")
    require(policy["source_receipt_sha256"] == result["inputs_sha256"]["receipt_m10_2"] and policy["development_scores_sha256"] == result["inputs_sha256"]["scores_dev"], "Política ou escores fora da cadeia.")
    for old_run, receipt in ((M102, r2), (M103, r3)):
        for name, expected in receipt["output_sha256"].items():
            check_hash(old_run / name, expected)
    check_hash(PROJECT / "scripts/executar_m10_2.py", r2["code_sha256"]["runner"])
    check_hash(PROJECT / "src/satmon/detectores_m10_2.py", r2["code_sha256"]["core"])
    check_hash(PROJECT / "scripts/executar_m10_3.py", r3["code_sha256"]["runner"])
    check_hash(PROJECT / "src/satmon/alarmes_m10_3.py", r3["code_sha256"]["core"])
    check_hash(PROJECT / "docs/m10_3/protocolo_politica.json", r3["protocol_sha256"])
    check_hash(PROTOCOL, result["protocol_sha256"])
    check_hash(PROJECT / "scripts/executar_m10_4.py", result["runner_sha256"])
    check_hash(PROJECT / "src/satmon/diagnostico_m10_4.py", result["core_sha256"])
    check_hash(PROJECT / "notebooks/m10_4_limite_autoral.py", result["authorship_sha256"])
    for name, expected in result["output_sha256"].items():
        check_hash(run / name, expected)
    check_hash(D2 / "protocolo.json", r2["source_spec_sha256"])
    spec2 = read_json(D2 / "protocolo.json")
    for name, identity in spec2["files"].items():
        check_hash(D2 / name, identity["sha256"])
    check_hash(D3 / "proveniencia.json", r3["source_test_sha256"])
    for name, expected in read_json(D3 / "proveniencia.json")["files"].items():
        check_hash(D3 / name, expected)

    raw = csv(D2 / "canais_grade.csv.gz")
    old_events = csv(D2 / "eventos.csv")
    full_times = times(raw.timestamp)
    fit_partition = full_times < pd.Timestamp(spec2["split"])
    full_values = raw[[f"{c}_value" for c in CHANNELS]].to_numpy(dtype=float)
    full_valid = np.isfinite(full_values).all(axis=1)
    full_ctx = context(full_times, full_valid, old_events)
    fit_ok = fit_partition & full_valid & ~full_ctx["ignore"] & ~full_ctx["anomaly"]
    require(int(fit_ok.sum()) == result["fitted_rows"] == r2["fit_rows_used"], "Coorte de ajuste alterada.")
    dev = csv(M102 / "escores_desenvolvimento.csv.gz")
    same(dev[[f"{c}_value" for c in CHANNELS]], full_values[~fit_partition], "Mesmos valores DEV completos")
    test_raw, test_saved = csv(D3 / "grade_teste.csv.gz"), csv(M103 / "escores_teste.csv.gz")
    np.testing.assert_array_equal(times(test_raw.timestamp).asi8, times(test_saved.timestamp).asi8)
    test_values = test_raw[[f"{c}_value" for c in CHANNELS]].to_numpy(dtype=float)
    test_valid = np.isfinite(test_values).all(axis=1)
    np.testing.assert_array_equal(test_valid, test_saved.utilizavel)
    contexts = {
        "desenvolvimento": context(times(dev.timestamp), dev.utilizavel.to_numpy(), old_events.loc[old_events.partition.eq("desenvolvimento")]),
        "diagnostico": context(times(test_saved.timestamp), test_valid, csv(D3 / "eventos_teste.csv")),
    }
    score_vectors = {"desenvolvimento": dev.score_isolation.to_numpy(dtype=float), "diagnostico": test_saved.escore.to_numpy(dtype=float)}
    values = {"desenvolvimento": dev[[f"{c}_value" for c in CHANNELS]].to_numpy(dtype=float), "diagnostico": test_values}
    med, scale = np.asarray(r2["robust_medians"]), np.asarray(r2["robust_scaled_mads"])
    frozen = policy["candidato"]["limiar"]
    metrics, ids = csv(run / "metricas_ablacao.csv"), csv(run / "limites_por_id.csv")
    require(len(metrics) == 24 and len(ids) == 192, "Número de linhas ou IDs inconsistente.")
    expected_keys = {(part, seed, variant) for part in contexts for seed in protocol["seeds"] for variant in VARIANTS}
    require(set(map(tuple, metrics[["particao", "semente", "variante"]].to_numpy())) == expected_keys and not metrics.duplicated(["particao", "semente", "variante"]).any(), "Combinações ausentes ou repetidas.")
    require(metrics.groupby(["semente", "variante"]).limiar.nunique().eq(1).all(), "Um corte mudou entre DEV e diagnóstico.")
    expected_reference = metrics.variante.eq("tres_canais") & metrics.semente.eq(17)
    np.testing.assert_array_equal(metrics.referencia_m10_3, expected_reference)

    for row in metrics.itertuples(index=False):
        ctx = contexts[row.particao]
        observed = sum(ctx["observable"].values())
        require(row.instantes_na_grade == len(ctx["valid"]) and row.instantes_utilizaveis == int(ctx["valid"].sum()) and row.ids_anomalia == len(ctx["masks"]) and row.ids_observaveis == observed, "Universo de avaliação alterado.")
        same(row.ids_nao_observaveis, len(ctx["masks"]) - observed, "IDs não observáveis")
        exposure = ctx["nominal"].sum() / 96
        same(row.exposicao_sem_anotacao_dias_equivalentes, exposure, "Exposição comum")
        same(row.taxa_sem_anotacao_por_dia, row.alarmes_sem_anotacao / exposure, "Taxa de inícios")
        same(row.alarmes_total, row.alarmes_atribuidos + row.alarmes_repetidos_no_evento + row.alarmes_sem_anotacao + row.alarmes_ignorados_categoria, "Classes de inícios")
        same(row.alarmes_atribuidos, row.ids_detectados, "Primeiros créditos")
        same(row.recall_observaveis, row.ids_detectados / observed, "Recall observável")
        same(row.recall_todos_ids, row.ids_detectados / len(ctx["masks"]), "Recall todos IDs")
        denominator = row.alarmes_total - row.alarmes_ignorados_categoria
        same(row.precisao_por_inicio_avaliavel, row.ids_detectados / denominator if denominator else np.nan, "Precisão ou indefinido")
        same(row.prevalencia_provisoria, ctx["anomaly"][ctx["eligible"]].mean(), "Prevalência comum")
        require(0 <= row.empates_no_corte <= row.pontos_no_corte <= row.instantes_utilizaveis, "Contagens de corte ou igualdade inválidas.")
        same(row.fracao_instantes_no_corte, row.pontos_no_corte / row.instantes_utilizaveis, "Fração >= corte")
        same(row.s2_menos_limiar, row.s2 - row.limiar, "Margem S2")
        require(row.s2 <= row.s1 and bool(row.pontos_no_corte) == bool(row.s1 >= row.limiar) and bool(row.alarmes_total) == bool(row.s2 >= row.limiar), "S1/S2 e existência de pontos/inícios incompatíveis.")
        require(row.alarmes_total * 2 <= row.pontos_no_corte and 0 <= row.ap_por_instante <= 1, "Escore ou número de inícios inválido.")

    reference, annual_scores, annual_channels, annual_pairs = {}, [], [], []
    for part, ctx in contexts.items():
        scores = score_vectors[part]
        require(np.isfinite(scores[ctx["valid"]]).all() and np.isnan(scores[~ctx["valid"]]).all(), "Vetor de referência inválido.")
        one, two = bound(scores, ctx["valid"], 1), bound(scores, ctx["valid"], 2)
        starts = replay(scores, ctx["valid"], frozen)
        if part == "diagnostico":
            np.testing.assert_array_equal(starts, test_saved.inicio_alarme)
            np.testing.assert_array_equal(ctx["valid"] & (scores >= frozen), test_saved.atingiu_limiar)
        summary, first = episodes(ctx, starts)
        row = metrics.loc[metrics.particao.eq(part) & expected_reference].iloc[0]
        for key, expected in summary.items():
            same(row[key], expected, f"Referência {part}.{key}")
        old = next(x for x in r3["metricas"] if x["particao"] == ("teste" if part == "diagnostico" else part))
        for key, expected in summary.items():
            same(old[key], expected, f"Reconciliação M10.3 {part}.{key}")
        old_part = "teste" if part == "diagnostico" else part
        original_ids = csv(M103 / f"eventos_{old_part}.csv")
        current_ids = ids.loc[ids.particao.eq(part) & ids.semente.eq(17) & ids.variante.eq("tres_canais"),
                              original_ids.columns].reset_index(drop=True)
        same_frame(current_ids, original_ids, "Mesmos IDs e primeiros alarmes da M10.3",
                   temporal=("inicio_anotado_utc", "primeiro_alarme_utc"))
        for entry in current_ids.itertuples(index=False):
            require(entry.estado == ("detectado" if entry.id in first else "perdido" if ctx["observable"][entry.id] else "nao_observavel"),
                    "Estado de ID não reproduziu o pareamento independente.")
            if entry.id in first:
                require(times([entry.primeiro_alarme_utc]).asi8[0] == ctx["index"].asi8[first[entry.id]],
                        "Primeiro crédito de ID não reproduziu o pareamento independente.")
        same(row.limiar, frozen, "Mesmo corte congelado")
        same(row.s1, one["limiar_maximo"], "S1 da referência")
        same(row.s2, two["limiar_maximo"], "S2 da referência")
        same(row.pontos_no_corte, np.count_nonzero(scores[ctx["valid"]] >= frozen), "Pontos >= corte")
        same(row.empates_no_corte, np.count_nonzero(scores[ctx["valid"]] == frozen), "Empates == corte")
        same(row.ap_por_instante, ap(ctx["anomaly"][ctx["eligible"]], scores[ctx["eligible"]]), "AP da referência com empates")
        reference[part] = {"s1": one, "s2": two, "episode_metrics": summary,
            "s2_confirmation_utc": ctx["index"][two["indice_confirmacao"]].isoformat()}
        profiles = annual(part, (values[part] - med) / scale, scores, ctx, frozen)
        annual_scores.extend(profiles[0]); annual_channels.extend(profiles[1]); annual_pairs.extend(profiles[2])

    same_frame(csv(run / "perfil_escores_ano.csv"), pd.DataFrame(annual_scores), "Perfil anual de escores")
    same_frame(csv(run / "perfil_canais_ano.csv"), pd.DataFrame(annual_channels), "Perfil anual dos canais")
    same_frame(csv(run / "associacao_canais_ano.csv"), pd.DataFrame(annual_pairs), "Associação anual de postos")

    for key, group in ids.groupby(["particao", "semente", "variante"], sort=False):
        part, seed, variant = key
        ctx = contexts[part]
        require(set(group.id) == set(ctx["masks"]) and len(group) == len(ctx["masks"]), "Ablação mudou o universo de IDs.")
        metric = metrics.loc[metrics.particao.eq(part) & metrics.semente.eq(seed) & metrics.variante.eq(variant)].iloc[0]
        require(int(group.estado.eq("detectado").sum()) == metric.ids_detectados, "Contagem de IDs detectados divergente.")
        delays = group.loc[group.estado.eq("detectado"), "atraso_min"].to_numpy()
        same(metric.atraso_mediano_min, np.median(delays) if len(delays) else np.nan, "Mediana dos atrasos por ID")
        same(metric.atraso_p90_min, np.quantile(delays, .9) if len(delays) else np.nan, "P90 dos atrasos por ID")
        for event in group.itertuples(index=False):
            spans = ctx["spans"][event.id]
            mask = ctx["masks"][event.id] & ctx["eligible"]
            require(event.canais_anotados == ",".join(sorted({s["channel"] for s in spans})) and event.anotacoes_canal_intervalo == len(spans) and event.slots_anotados_avaliaveis == int(mask.sum()), "Metadados ou slots do ID divergentes.")
            begin = min(s["start"] for s in spans)
            require(times([event.inicio_anotado_utc]).asi8[0] == begin, "Relógio inicial do ID alterado.")
            if not ctx["observable"][event.id]:
                require(event.estado == "nao_observavel", "ID não observável classificado como perda.")
            else:
                require(event.estado in ("detectado", "perdido"), "Estado incompatível com observabilidade.")
            if event.estado == "detectado":
                alarm = times([event.primeiro_alarme_utc]).asi8[0]
                position = int(np.searchsorted(ctx["index"].asi8, alarm))
                require(position < len(mask) and ctx["index"].asi8[position] == alarm and mask[position], "Primeiro alarme fora da união elegível do ID.")
                same(event.atraso_min, (int(alarm) - begin) / 60e9, "Atraso desde primeira anotação")
                require(event.s1_no_id >= metric.limiar, "Detecção sem alcance pontual no ID.")
            else:
                require(pd.isna(event.primeiro_alarme_utc) and pd.isna(event.atraso_min), "Atraso fabricado para ID não detectado.")
            if pd.notna(event.s2_no_id):
                end = times([event.fim_janela_mais_forte_utc]).asi8[0]
                position = int(np.searchsorted(ctx["index"].asi8, end))
                require(0 < position < len(mask) and ctx["index"].asi8[position] == end and mask[position - 1] and mask[position], "Janela por ID atravessou lacuna ou anotação.")
                require(event.s2_no_id <= event.s1_no_id, "S2 do ID supera seu S1.")
            else:
                require(pd.isna(event.fim_janela_mais_forte_utc) and not np.any(mask[:-1] & mask[1:]), "Ausência de janela por ID incorreta.")
            if seed == 17 and variant == "tres_canais":
                scores = score_vectors[part]
                expected_bound = bound(scores, mask, 2)
                same(event.s1_no_id, scores[mask].max() if mask.any() else np.nan, "S1 real por ID")
                same(event.s2_no_id, expected_bound["limiar_maximo"], "S2 real por ID")
                i = expected_bound["indice_confirmacao"]
                if i is not None:
                    require(times([event.fim_janela_mais_forte_utc]).asi8[0] == ctx["index"].asi8[i], "Primeiro fim empatado do ID incorreto.")

    stability = []
    for (part, variant), group in metrics.groupby(["particao", "variante"], sort=False):
        record = {"particao": part, "variante": variant, "n_sementes": len(group)}
        for name in ("ap_por_instante", "ids_detectados", "taxa_sem_anotacao_por_dia"):
            record.update({f"{name}_min": group[name].min(), f"{name}_mediana": group[name].median(), f"{name}_max": group[name].max()})
        stability.append(record)
    same_frame(csv(run / "estabilidade_sementes.csv"), pd.DataFrame(stability), "Agregação de três sementes")
    slim = ["particao", "semente", "variante", "id", "estado", "atraso_min", "canais_anotados"]
    baseline = ids.loc[ids.variante.eq("tres_canais"), slim[:-1]].drop(columns="variante").rename(
        columns={"estado": "estado_tres_canais", "atraso_min": "atraso_tres_canais_min"})
    changes = ids.loc[~ids.variante.eq("tres_canais"), slim].merge(baseline, on=["particao", "semente", "id"], validate="many_to_one", how="left", sort=False)
    detected, original = changes.estado.eq("detectado"), changes.estado_tres_canais.eq("detectado")
    changes["mudanca"] = np.select([detected & ~original, original & ~detected], ["ganho", "perda"], default="mesmo_estado")
    same_frame(csv(run / "mudancas_por_id.csv"), changes, "Mudanças pareadas por ID")
    compare = metrics.loc[metrics.particao.eq("diagnostico") & metrics.semente.eq(17) & metrics.variante.isin(("tres_canais", "sem_51", "sem_52")),
        ["variante", "limiar", "s1", "s2", "pontos_no_corte", "empates_no_corte", "ids_detectados"]].to_dict(orient="records")
    algebra = []
    for row in compare:
        isolated = row["pontos_no_corte"] > 0 and row["s2"] < row["limiar"]
        algebra.append({**row, "max_run_acima_inferido": 1 if isolated else 0 if not row["pontos_no_corte"] else None,
            "inicios_admissiveis_k1_inferidos": int(row["pontos_no_corte"]) if isolated or not row["pontos_no_corte"] else None,
            "k1_policy_replayed": False, "ids_k1_not_inferred": True})
    require(sha(M103 / "politica_congelada.json") == FROZEN_SHA, "Política M10.3 alterada durante auditoria.")
    losses = changes.loc[changes.particao.eq("desenvolvimento") & changes.mudanca.eq("perda")]
    return {"schema": "satmon-m10-4-independent-audit-v1", "verified": True,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(), "run_id": run.name,
        "run_directory": run.relative_to(PROJECT).as_posix(),
        "audit_versions": {"numpy": np.__version__, "pandas": pd.__version__},
        "method": "Persisted-table consistency plus independent aligned-pair minima, tie-block AP, annual ranks and ID masks for the persisted reference; no project imports or model fits.",
        "checks": {"source_inputs_outputs_protocol_code_author_hashes": True, "original_m10_3_policy_hash_unchanged": True,
            "twenty_four_rows_twelve_combinations_three_seeds": True, "fixed_full_channel_fit_and_evaluation_cohorts": True,
            "algebra_of_metrics_and_threshold_counts": True, "reference_m10_3_metrics_from_persisted_scores_recomputed": True,
            "reference_s1_s2_and_first_tied_id_end_indices": True, "reference_annual_score_channel_and_rank_profiles": True,
            "all_ids_masks_and_reported_alarm_times_consistent": True, "paired_id_changes_recomputed": True,
            "seed_aggregates_recomputed": True},
        "checked_hashes": checked_hashes, "metric_rows": len(metrics), "id_rows": len(ids), "change_rows": len(changes),
        "fit_rows_recomputed": int(fit_ok.sum()), "reference_recomputed": reference,
        "diagnostic_seed17_cutoff_comparison": algebra,
        "development_id_losses": losses.astype(object).where(losses.notna(), None).to_dict(orient="records"),
        "all_diagnostic_combinations_detected_zero_ids": bool(metrics.loc[metrics.particao.eq("diagnostico"), "ids_detectados"].eq(0).all()),
        "latest_pointer": {"written_by_runner": False, "audit_uses_explicit_fixed_run_id": True},
        "limits": {"new_forest_models_fitted_by_auditor": 0, "new_ablation_scores_reproduced": False,
            "new_ablation_threshold_quantiles_independently_recomputed": False, "new_ablation_weights_or_full_scores_persisted": False,
            "new_ablation_reported_tables_and_algebra_audited": True, "persisted_reference_metrics_and_limits_recomputed_without_refit": True,
            "alternative_diagnostic_policy_replayed": False,
            "note": "Absence of new-variant score vectors/checkpoints limits their audit to identities, cohorts, reported algebra, ID times and aggregates. Three seeds are not temporal confidence intervals; annotation completeness and physical causes remain unknown."}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=RUN)
    args = parser.parse_args()
    result = audit(args.run_dir.resolve())
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Auditoria aprovada: {result['metric_rows']} métricas e referência persistida; nenhum ajuste novo.")
    print(f"Run: {result['run_id']}; JSON: {OUTPUT}")


if __name__ == "__main__":
    main()
