"""Investiga alcance do corte e estabilidade ao retirar canais. Sem refazer M10.3."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import importlib.util
from importlib.metadata import version
from pathlib import Path
import sys
from time import perf_counter
from uuid import uuid4

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score
from threadpoolctl import threadpool_limits

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))
from satmon.alarmes_m10_3 import Avaliador, iniciar_alarmes
from satmon.diagnostico_m10_4 import (conferir_autoria, janela_conferida, limite_confirmacao,
                                       limites_por_id, perfil_temporal)
from executar_m10_3 import (PROTOCOL as M103_PROTOCOL, TEST_DATA, VALUE_COLS,
                             conferir_grade, ler_desenvolvimento, ler_teste, read_json, require_hash,
                             sha, write_json)

DEFAULT_M102 = PROJECT / "reports/m10_2/20261119T101049Z_253ff59f"
DEFAULT_M103 = PROJECT / "reports/m10_3/20261123T195301Z_332fb306"
PROTOCOL = PROJECT / "docs/m10_4/protocolo_diagnostico.json"
MASKS = {"tres_canais": (0, 1, 2), "sem_50": (1, 2), "sem_51": (0, 2), "sem_52": (0, 1)}


def load_function(path, name):
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo necessário não encontrado: {path}")
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Arquivo Python necessário: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, name)


def load_chain(m102, m103):
    result_path = m103 / "resultado.json"
    result = read_json(result_path)
    require_hash(M103_PROTOCOL, result["protocol_sha256"])
    require_hash(PROJECT / "scripts/executar_m10_3.py", result["code_sha256"]["runner"])
    require_hash(PROJECT / "src/satmon/alarmes_m10_3.py", result["code_sha256"]["core"])
    protocol_old = read_json(M103_PROTOCOL)
    receipt, dev, evaluator, events = ler_desenvolvimento(m102, protocol_old)
    policy_path = m103 / "politica_congelada.json"
    require_hash(policy_path, result["politica_sha256"])
    require_hash(policy_path, result["output_sha256"]["politica_congelada.json"])
    policy = read_json(policy_path)
    choice = policy["candidato"]
    if (result["schema"] != "satmon-m10-3-result-v1" or result["completed"] is not True
            or result["periodo_reservado_avaliado"] is not True or result["run_id"] != m103.name
            or policy["schema"] != "satmon-m10-3-frozen-policy-v1" or policy["status"] != "congelada"
            or result["source_run_id"] != receipt["run_id"] or policy["source_run_id"] != receipt["run_id"]
            or policy["protocol_sha256"] != result["protocol_sha256"]
            or policy["source_receipt_sha256"] != sha(m102 / "resultado.json")
            or policy["development_scores_sha256"] != receipt["output_sha256"]["escores_desenvolvimento.csv.gz"]
            or choice["metodo"] != "score_isolation" or choice["quantil"] != .9995
            or policy["consecutivos"] != 2 or receipt["settings"]["random_state"] != 17):
        raise ValueError("Use as duas execuções encadeadas de M10.2 e M10.3 conforme COMECE_M10_4.md.")
    old_runner = PROJECT / "scripts/executar_m10_2.py"
    require_hash(old_runner, receipt["code_sha256"]["runner"])
    require_hash(PROJECT / "src/satmon/detectores_m10_2.py", receipt["code_sha256"]["core"])
    spec, _, _, all_values, valid, fit, _, flags = load_function(old_runner, "carregar")()
    rows = fit & valid & ~(flags["anomaly"] | flags["rare"] | flags["gap"])
    if (int(rows.sum()) != receipt["fit_rows_used"] or spec["settings"] != receipt["settings"]
            or not np.array_equal(all_values[~fit], dev[VALUE_COLS].to_numpy(dtype=float), equal_nan=True)):
        raise ValueError("Coorte de ajuste/desenvolvimento difere de M10.2.")
    center = np.asarray(receipt["robust_medians"], dtype=float)
    scale = np.asarray(receipt["robust_scaled_mads"], dtype=float)
    if (center.shape != (3,) or scale.shape != (3,) or not np.isfinite(center).all()
            or not np.isfinite(scale).all() or (scale <= 0).any()):
        raise ValueError("Escala original inválida.")
    return (result, receipt, policy, all_values[rows], dev, evaluator, events,
            protocol_old, center, scale)


def quantil_superior(scores, valid, q, method):
    if not np.isfinite(scores[valid]).all():
        raise ValueError("Escores utilizáveis não finitos.")
    return float(np.quantile(scores[valid], q, method=method))


def grade_scores(model, transformed, mask, cols):
    scores = np.full(len(mask), np.nan)
    scores[mask] = -model.score_samples(transformed[mask][:, cols])
    if not np.isfinite(scores[mask]).all():
        raise ValueError("A floresta produziu escores não finitos.")
    return scores


def fit_dev(protocol, policy, config, fit, z_dev, dev, ev_dev):
    models = {}
    q = protocol["quantil_dev"]
    threshold_frozen = policy["candidato"]["limiar"]
    print("Ajuste 2004–2007; mesma coorte completa para todas as variantes.", flush=True)
    for seed in protocol["seeds"]:
        for name, cols in MASKS.items():
            if (seed, name) == (17, "tres_canais"):
                model = None
                scores = dev.score_isolation.to_numpy(dtype=float)
                cut = threshold_frozen
                actual = quantil_superior(scores, ev_dev.valid, q, protocol["metodo_quantil"])
                if actual != cut:
                    raise ValueError("O corte gravado não corresponde aos escores da referência M10.3.")
            else:
                model = IsolationForest(n_estimators=config["forest_trees"], max_samples=config["forest_max_samples"],
                                        contamination="auto", random_state=seed, n_jobs=2).fit(fit[:, cols])
                scores = grade_scores(model, z_dev, ev_dev.valid, cols)
                cut = quantil_superior(scores, ev_dev.valid, q, protocol["metodo_quantil"])
            models[(seed, name)] = (model, cut, scores)
        print(f"Semente {seed}: quatro variantes com cortes determinados exclusivamente em desenvolvimento.", flush=True)
    return models


def scores_diagnostico(m103, receipt, protocol, old_events):
    require_hash(TEST_DATA / "proveniencia.json", receipt["source_test_sha256"])
    times, x, events = ler_teste(protocol, old_events)
    path = m103 / "escores_teste.csv.gz"
    require_hash(path, receipt["output_sha256"][path.name])
    ref = pd.read_csv(path, float_precision="round_trip")
    dates = conferir_grade(ref.timestamp, protocol["teste_inicio_utc"],
                           protocol["teste_fim_exclusivo_utc"], protocol["grid_step_seconds"])
    valid = np.isfinite(x).all(axis=1)
    scores = ref.escore.to_numpy(dtype=float)
    np.testing.assert_array_equal(times.asi8, dates.asi8)
    np.testing.assert_array_equal(valid, ref.utilizavel.to_numpy())
    if not np.isfinite(scores[valid]).all() or not np.isnan(scores[~valid]).all():
        raise ValueError("Escores de teste persistidos não correspondem à máscara.")
    return x, Avaliador(times, valid, events, step_seconds=protocol["grid_step_seconds"]), ref


def sample_metrics(escores, ev, cut, k, func):
    starts = iniciar_alarmes(escores, ev.valid, limiar=cut, consecutivos=k)
    metrics, events, _, _ = ev.avaliar(starts, details=True)
    ones = janela_conferida(func, escores, ev.valid, 1)
    twos = janela_conferida(func, escores, ev.valid, k)
    highest = twos["limiar_maximo"]
    if bool(starts.any()) != (highest is not None and highest >= cut):
        raise ValueError("Inícios e limite por janelas não reconciliados.")
    y = ev.anomaly[ev.eligible]
    valid_scores = escores[ev.valid]
    return {
        **metrics, "limiar": cut, "pontos_no_corte": int((valid_scores >= cut).sum()),
        "empates_no_corte": int((valid_scores == cut).sum()),
        "fracao_instantes_no_corte": float((valid_scores >= cut).mean()),
        "prevalencia_provisoria": float(y.mean()),
        "ap_por_instante": float(average_precision_score(y, escores[ev.eligible])) if y.any() and not y.all() else None,
        "s1": ones["limiar_maximo"], "s2": highest,
        "s2_menos_limiar": highest - cut if highest is not None else None,
    }, events, starts


def reconcile_original(result, metrics, partition):
    old_name = "teste" if partition == "diagnostico" else partition
    old = next(row for row in result["metricas"] if row["particao"] == old_name)
    for new, earlier in [("pontos_no_corte", "pontos_atingiram_limiar"), ("s1", "escore_maximo_utilizavel")]:
        if metrics[new] != old[earlier]:
            raise ValueError(f"{partition}: a referência deixou de reproduzir {earlier}.")
    for key in ("instantes_utilizaveis", "ids_observaveis", "ids_detectados", "alarmes_total",
                "alarmes_atribuidos", "alarmes_sem_anotacao", "alarmes_repetidos_no_evento"):
        if metrics[key] != old[key]:
            raise ValueError(f"{partition}: a referência deixou de reproduzir {key}.")


def var_summary(rows):
    keys = ("ap_por_instante", "ids_detectados", "taxa_sem_anotacao_por_dia")
    frames = []
    for (part, name), group in rows.groupby(["particao", "variante"], sort=False):
        record = {"particao": part, "variante": name, "n_sementes": len(group)}
        for key in keys:
            for statistic, val in (("min", group[key].min()), ("mediana", group[key].median()), ("max", group[key].max())):
                record[f"{key}_{statistic}"] = val
        frames.append(record)
    return pd.DataFrame(frames)


def changes(events):
    slim = ["particao", "semente", "variante", "id", "estado", "atraso_min", "canais_anotados"]
    baseline = events.loc[events.variante.eq("tres_canais"), slim[:-1]].drop(columns="variante")
    baseline = baseline.rename(columns={"estado": "estado_tres_canais", "atraso_min": "atraso_tres_canais_min"})
    paired = events.loc[~events.variante.eq("tres_canais"), slim].merge(
        baseline, how="left", validate="many_to_one", on=["particao", "semente", "id"], sort=False)
    if paired.estado_tres_canais.isna().any() or (paired.estado.eq("nao_observavel") !=
                                                 paired.estado_tres_canais.eq("nao_observavel")).any():
        raise ValueError("A ablação mudou o universo de avaliação.")
    b, r = paired.estado_tres_canais.eq("detectado"), paired.estado.eq("detectado")
    paired["mudanca"] = np.select([r & ~b, b & ~r], ["ganho", "perda"], default="mesmo_estado")
    return paired


def render_report(frames, result, chosen):
    page = """<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<title>M10.4 — Estabilidade e ablação</title>
<style>body{font:16px/1.5 system-ui;max-width:1150px;margin:36px auto;padding:0 18px;color:#183141}
td,th{padding:6px;border:1px solid #c6d6de}table{border-collapse:collapse;font-size:14px}
th{background:#eaf2f5}section{overflow:auto}.nota{background:#f0f5f7;padding:12px}
</style><h1>M10.4 — O que explica o silêncio?</h1>"""
    page += (f"<p>Referência auditada: {html.escape(result['run_id'])}; corte <b>{chosen:.10f}</b>. "
             "2011–2013 é diagnóstico retrospectivo. As ablações usam as mesmas linhas de ajuste e avaliação. "
             "Os candidatos recebem um corte em seus próprios escores de desenvolvimento; nenhuma política foi alterada.</p>")
    main = frames["metricas_ablacao.csv"]
    cols = ["particao", "variante", "limiar", "s1", "s2", "ap_por_instante", "ids_detectados",
            "ids_observaveis", "taxa_sem_anotacao_por_dia", "atraso_mediano_min", "empates_no_corte"]
    view = main.loc[main.semente.eq(17), cols]
    tables = [("Ablações pareadas: semente 17", view),
              ("Faixa entre três sementes", frames["estabilidade_sementes.csv"]),
              ("Mesma floresta: perfil por ano", frames["perfil_escores_ano.csv"]),
              ("Medições: percentis na escala do ajuste", frames["perfil_canais_ano.csv"]),
              ("Associação de postos entre canais", frames["associacao_canais_ano.csv"]),
              ("Limites e detecção por ID: semente 17", frames["limites_por_id.csv"].loc[
                  frames["limites_por_id.csv"].semente.eq(17), ["particao", "variante", "id", "estado",
                      "canais_anotados", "slots_anotados_avaliaveis", "s1_no_id", "s2_no_id",
                      "atraso_min"]])]
    for title, frame in tables:
        page += f"<h2>{title}</h2><section>{frame.round(6).to_html(index=False, na_rep='—')}</section>"
    page += """<p class="nota"> S1 é o maior escore utilizável; S2 é o maior mínimo entre pares consecutivos válidos.
S2 dentro de um ID não implica novo alarme dentro dele: um início pode ter ocorrido antes, ou o pareamento pode dar
crédito a outro ID. Quantis iguais não garantem taxas iguais. Coortes e anotações são aproximadas; sementes não
medem incerteza temporal. Os resultados não autorizam mudança de política nem provam uma causa física. </p>"""
    return page


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m10-2-run", type=Path, default=DEFAULT_M102)
    parser.add_argument("--m10-3-run", type=Path, default=DEFAULT_M103)
    parser.add_argument("--output-dir", type=Path, default=PROJECT / "reports/m10_4")
    parser.add_argument("--autoria", type=Path, help="Arquivo .py com limite_confirmacao.")
    parser.add_argument("--verificar", action="store_true", help="Roda só contas pequenas, sem ler dados ou ajustar.")
    args = parser.parse_args(argv)
    start = perf_counter()
    func = load_function(args.autoria, "limite_confirmacao") if args.autoria else limite_confirmacao
    nc = conferir_autoria(func)
    print(f"{nc} contraprovas de confirmação aprovadas.", flush=True)
    if args.verificar:
        return 0
    protocol = read_json(PROTOCOL)
    if (protocol["schema"] != "satmon-m10-4-diagnostic-protocol-v1" or protocol["seeds"] != [17, 29, 41]
            or tuple(protocol["variantes"]) != tuple(MASKS) or protocol["consecutivos"] != 2
            or protocol["quantil_dev"] != .9995 or protocol["metodo_quantil"] != "higher"):
        raise ValueError("Protocolo diagnóstico incompatível.")
    r2, r3 = args.m10_2_run.resolve(), args.m10_3_run.resolve()
    (previous, receipt, policy, fit, dev, ev_dev, events_old,
        protocol_old, center, scale) = load_chain(r2, r3)
    k = protocol["consecutivos"]
    frozen = policy["candidato"]["limiar"]
    policy_hash = sha(r3 / "politica_congelada.json")
    z_dev = (dev[VALUE_COLS].to_numpy(dtype=float) - center) / scale
    metrics, ids, temporal, marg, pairs = [], [], [], [], []

    with threadpool_limits(limits=2):
        models = fit_dev(protocol, policy, receipt["settings"], (fit - center) / scale,
                         z_dev, dev, ev_dev)
        print("Cortes calculados; lendo 2011–2013 para diagnóstico retrospectivo.", flush=True)
        x, ev_test, test_ref = scores_diagnostico(r3, previous, protocol_old, events_old)
        z_test = (x - center) / scale
        for (seed, name), (model, cut, score_dev) in models.items():
            is_reference = model is None
            score_test = (test_ref.escore.to_numpy(dtype=float) if is_reference
                          else grade_scores(model, z_test, ev_test.valid, MASKS[name]))
            for part, ev, z, s in (("desenvolvimento", ev_dev, z_dev, score_dev),
                                   ("diagnostico", ev_test, z_test, score_test)):
                opts = {"particao": part, "semente": seed, "variante": name}
                total, event_rows, starts = sample_metrics(s, ev, cut, k, func)
                metrics.append({**opts, **total, "referencia_m10_3": is_reference})
                ids.extend({**opts, **item} for item in limites_por_id(s, ev, event_rows, func, k))
                if is_reference:
                    reconcile_original(previous, total, part)
                    if part == "diagnostico":
                        np.testing.assert_array_equal(starts, test_ref.inicio_alarme.to_numpy())
                        np.testing.assert_array_equal(ev.valid & (s >= cut), test_ref.atingiu_limiar.to_numpy())
                    p_rows, m_rows, r_rows = perfil_temporal(part, z, s, ev, cut, func, k)
                    temporal.extend(p_rows)
                    marg.extend(m_rows)
                    pairs.extend(r_rows)
    if sha(r3 / "politica_congelada.json") != policy_hash:
        raise ValueError("A política da M10.3 foi alterada durante o diagnóstico.")
    metrics = pd.DataFrame(metrics)
    ids = pd.DataFrame(ids)
    frames = {
        "metricas_ablacao.csv": metrics, "estabilidade_sementes.csv": var_summary(metrics),
        "limites_por_id.csv": ids, "mudancas_por_id.csv": changes(ids),
        "perfil_escores_ano.csv": pd.DataFrame(temporal), "perfil_canais_ano.csv": pd.DataFrame(marg),
        "associacao_canais_ano.csv": pd.DataFrame(pairs),
    }
    if len(metrics) != 24 or not metrics.groupby("particao").ids_observaveis.nunique().eq(1).all():
        raise ValueError("Coortes ou número de comparações inconsistentes.")
    outname = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    out = args.output_dir.resolve() / outname
    out.mkdir(parents=True, exist_ok=False)
    for name, frame in frames.items():
        frame.to_csv(out / name, index=False)
    (out / "relatorio.html").write_text(render_report(frames, previous, frozen), encoding="utf-8")
    outfiles = {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()}
    write_json(out / "resultado.json", {
        "schema": "satmon-m10-4-result-v1", "completed": True, "run_id": outname,
        "source_m10_2_run_id": receipt["run_id"], "source_m10_3_run_id": previous["run_id"],
        "inputs_sha256": {"receipt_m10_2": sha(r2 / "resultado.json"), "receipt_m10_3": sha(r3 / "resultado.json"),
                          "scores_dev": receipt["output_sha256"]["escores_desenvolvimento.csv.gz"],
                          "scores_test": previous["output_sha256"]["escores_teste.csv.gz"], "policy": policy_hash},
        "protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(Path(__file__)),
        "core_sha256": sha(PROJECT / "src/satmon/diagnostico_m10_4.py"),
        "authorship_sha256": sha(args.autoria) if args.autoria else None,
        "author_cases_passed": nc, "verified_against_reference_real_data": args.autoria is not None,
        "seeds": protocol["seeds"], "same_full_channel_cohort": True, "fitted_rows": len(fit),
        "forests_fitted_only_on_adjustment": 11, "original_scores_used_verbatim": True,
        "test_used_to_choose_parameters": False, "test_is_retrospective": True,
        "frozen_policy_unchanged": True, "operational_approval": False,
        "versions": {pkg: version(pkg) for pkg in ("numpy", "pandas", "scikit-learn")},
        "python": sys.version.split()[0], "elapsed_seconds": perf_counter() - start, "output_sha256": outfiles,
    })
    cols = ["particao", "variante", "limiar", "s1", "s2", "ap_por_instante", "ids_detectados",
            "taxa_sem_anotacao_por_dia"]
    print(metrics.loc[metrics.semente.eq(17), cols].round(6).to_string(index=False))
    print(f"Relatório: {out / 'relatorio.html'}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError) as exc:
        print(f"M10.4: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
