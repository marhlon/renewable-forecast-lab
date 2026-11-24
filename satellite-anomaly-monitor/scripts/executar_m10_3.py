"""Congela a política em desenvolvimento; depois mede episódios no teste temporal."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html
import importlib.util
from importlib.metadata import version
import json
from pathlib import Path
import sys
import uuid

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from satmon.alarmes_m10_3 import (Avaliador, CHANNELS, conferir_autoria,
                                    conferir_saida, iniciar_alarmes, utc_index)

PROTOCOL = PROJECT / "docs/m10_3/protocolo_politica.json"
M102_DATA = PROJECT / "data/reference/esa_mission1_m10_2"
TEST_DATA = PROJECT / "data/reference/esa_mission1_m10_3"
VALUE_COLS = [f"{c}_value" for c in CHANNELS]
SCORES = ("score_robusto", "score_pca", "score_isolation")
DEFAULT_M102 = PROJECT / "reports/m10_2/20261119T101049Z_253ff59f"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def require_hash(path, expected):
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo necessário não encontrado: {path}")
    if sha(path) != expected:
        raise ValueError(f"Arquivo não corresponde ao recibo: {path}")


def carregar_autoria(path):
    if not path.is_file():
        raise FileNotFoundError(f"Crie {path} conforme a Aula 1, ou use o modo de referência sem --autoria.")
    spec = importlib.util.spec_from_file_location("m10_3_alarme_autoral", path.resolve())
    if spec is None or spec.loader is None:
        raise ValueError("A autoria deve ser um arquivo .py.")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.iniciar_alarmes


def conferir_grade(timestamps, start, stop, step):
    times = utc_index(timestamps)
    expected = pd.date_range(start, stop, freq=f"{step}s", inclusive="left").astype("datetime64[ns, UTC]")
    if not np.array_equal(times.asi8, expected.asi8):
        raise ValueError("Os instantes não formam a grade esperada para este período.")
    return times


def ler_desenvolvimento(run, protocol):
    receipt_path = run / "resultado.json"
    receipt = read_json(receipt_path)
    if (receipt.get("schema") != "satmon-m10-2-result-v1" or receipt.get("completed") is not True
            or receipt.get("run_id") != run.name or receipt.get("holdout_scored") is not False
            or receipt.get("source_spec_sha256") != protocol["source_spec_m10_2_sha256"]
            or receipt["source_slice"][1:] != [protocol["desenvolvimento_inicio_utc"], protocol["teste_inicio_utc"]]):
        raise ValueError("Indique a pasta completa de uma execução M10.2 deste recorte.")
    require_hash(M102_DATA / "protocolo.json", receipt["source_spec_sha256"])
    spec = read_json(M102_DATA / "protocolo.json")
    require_hash(M102_DATA / "eventos.csv", spec["files"]["eventos.csv"]["sha256"])
    if spec["settings"] != receipt["settings"]:
        raise ValueError("Configuração dos detectores diferente do protocolo M10.2.")
    raw_path = run / "escores_desenvolvimento.csv.gz"
    require_hash(raw_path, receipt["output_sha256"][raw_path.name])
    dev = pd.read_csv(raw_path, float_precision="round_trip")
    if dev.utilizavel.dtype != bool:
        raise ValueError("O marcador utilizavel precisa ser booleano.")
    valid = dev.utilizavel.to_numpy()
    a = dev[list(SCORES)].to_numpy(dtype=float)
    if (not np.isfinite(a[valid]).all() or not np.isnan(a[~valid]).all()
            or int(valid.sum()) != receipt["dev_rows_scored"]):
        raise ValueError("Escores e disponibilidade não reconciliados.")
    idx = conferir_grade(dev.timestamp, protocol["desenvolvimento_inicio_utc"],
                          protocol["teste_inicio_utc"], protocol["grid_step_seconds"])
    all_events = pd.read_csv(M102_DATA / "eventos.csv")
    ev = Avaliador(idx, valid, all_events[all_events.partition.eq("desenvolvimento")],
                   step_seconds=protocol["grid_step_seconds"])
    np.testing.assert_array_equal(ev.anomaly, dev.anotacao_anomaly.to_numpy())
    np.testing.assert_array_equal(ev.eligible, dev.entra_no_ranking.to_numpy())
    if ev.nominal_days <= 0:
        raise ValueError("Sem exposição utilizável e sem anotação no desenvolvimento.")
    return receipt, dev, ev, all_events


def escolher(dev, ev, protocol, func):
    rows = []
    k = protocol["consecutivos"]
    methods = protocol["metodos_em_ordem_de_desempate"]
    budget = protocol["max_alarmes_sem_anotacao_por_dia_equivalente_no_dev"]
    for method in methods:
        score = dev[method].to_numpy(dtype=float)
        for q in protocol["candidatos_quantil"]:
            threshold = float(np.quantile(score[ev.valid], q, method=protocol["quantil_metodo"]))
            starts = conferir_saida(func, score, ev.valid, threshold, k)
            expected = iniciar_alarmes(score, ev.valid, limiar=threshold, consecutivos=k)
            np.testing.assert_array_equal(starts, expected, err_msg=f"Confirmações divergentes: {method}, quantil {q}.")
            metrics = ev.avaliar(starts)
            passing = metrics["taxa_sem_anotacao_por_dia"] <= budget and metrics["ids_detectados"] > 0
            rows.append({"metodo": method, "quantil": q, "limiar": threshold, "viavel": passing, **metrics})
    possible = [row for row in rows if row["viavel"]]
    choice = min(possible, key=lambda r: (-r["ids_detectados"], r["taxa_sem_anotacao_por_dia"],
                                          r["atraso_mediano_min"], methods.index(r["metodo"]), -r["quantil"]),
                 default=None)
    for row in rows:
        row["escolhida"] = row is choice
    return rows, choice


def ler_teste(protocol, old_events):
    source = read_json(TEST_DATA / "proveniencia.json")
    step = protocol["grid_step_seconds"]
    start, end = (pd.Timestamp(protocol[key]) for key in ("teste_inicio_utc", "teste_fim_exclusivo_utc"))
    if (source["schema"] != "satmon-m10-3-esa-test-source-v1" or tuple(source["channels"]) != CHANNELS
            or source["source_spec_m10_2_sha256"] != protocol["source_spec_m10_2_sha256"]
            or pd.Timestamp(source["start"]) != start or pd.Timestamp(source["stop_exclusive"]) != end
            or source["step_seconds"] != step or source["max_age_seconds"] != 180):
        raise ValueError("Recorte reservado não corresponde ao protocolo.")
    for name in ("grade_teste.csv.gz", "eventos_teste.csv"):
        require_hash(TEST_DATA / name, source["files"][name])
    frame = pd.read_csv(TEST_DATA / "grade_teste.csv.gz", float_precision="round_trip")
    times = conferir_grade(frame.timestamp, start, end, step)
    values = frame[VALUE_COLS].to_numpy(dtype=float)
    for channel in CHANNELS:
        t = utc_index(frame[f"{channel}_sample_time"])
        present = ~t.isna()
        age = np.full(len(t), np.nan)
        age[present] = (times.asi8[present] - t.asi8[present]) / 1e9
        np.testing.assert_allclose(age, frame[f"{channel}_age_seconds"], atol=1e-9, rtol=0, equal_nan=True)
        filled = frame[f"{channel}_value"].notna().to_numpy()
        if (np.isinf(values).any() or (age[present] < 0).any() or (t[present] < start).any()
                or (filled & (~present | (age > 180))).any()):
            raise ValueError(f"Frescor, disponibilidade ou fronteira violados em {channel}.")
    events = pd.read_csv(TEST_DATA / "eventos_teste.csv")
    if (set(events.ID) & set(old_events.ID)
            or (utc_index(events.StartTime) < start).any()
            or (utc_index(events.EndTime) >= end).any()):
        raise ValueError("ID compartilhado ou anotação cruzando uma fronteira.")
    return times, values, events


def pontuador(receipt, method, dev, valid, policy):
    center = np.asarray(receipt["robust_medians"], dtype=float)
    scale = np.asarray(receipt["robust_scaled_mads"], dtype=float)
    if (center.shape != (3,) or scale.shape != (3,) or not np.isfinite(center).all()
            or not np.isfinite(scale).all() or (scale <= 0).any()):
        raise ValueError("Estado do escalonador inválido.")
    refit = False
    if method == "score_robusto":
        def scoring(x):
            return np.abs((x - center) / scale).max(axis=1)
    elif method == "score_pca":
        from satmon.detectores_m10_2 import erro_pca_por_amostra
        pca_mean = receipt["pca_center_in_scaled_space"]
        pca_components = receipt["pca_components"]

        def scoring(x):
            return erro_pca_por_amostra((x - center) / scale, pca_mean, pca_components)
    elif method == "score_isolation":
        # O M10.2 não serializou a floresta. Reconstruí-la somente do ajuste original.
        from sklearn.ensemble import IsolationForest
        from threadpoolctl import threadpool_limits
        old_runner = PROJECT / "scripts/executar_m10_2.py"
        require_hash(old_runner, receipt["code_sha256"]["runner"])
        require_hash(PROJECT / "src/satmon/detectores_m10_2.py", receipt["code_sha256"]["core"])
        old_spec = importlib.util.spec_from_file_location("satmon_m10_2_original_runner", old_runner)
        old_module = importlib.util.module_from_spec(old_spec)
        old_spec.loader.exec_module(old_module)
        settings, _, _, all_values, usable, fit, _, annotations = old_module.carregar()
        train = fit & usable & ~(annotations["anomaly"] | annotations["rare"] | annotations["gap"])
        if int(train.sum()) != receipt["fit_rows_used"] or settings["settings"] != receipt["settings"]:
            raise ValueError("Não foi possível reconstruir o ajuste M10.2.")
        config = receipt["settings"]
        with threadpool_limits(limits=2):
            forest = IsolationForest(n_estimators=config["forest_trees"], max_samples=config["forest_max_samples"],
                                     contamination="auto", random_state=config["random_state"], n_jobs=2)
            forest.fit((all_values[train] - center) / scale)
        refit = True

        def scoring(x):
            return -forest.score_samples((x - center) / scale)
    else:
        raise ValueError(f"Método não reconhecido: {method}")

    saved = dev[method].to_numpy(dtype=float)
    rebuilt = scoring(dev.loc[valid, VALUE_COLS].to_numpy(dtype=float))
    np.testing.assert_allclose(rebuilt, saved[valid], rtol=1e-10, atol=1e-12,
                               err_msg="O pontuador não reproduz os escores salvos no M10.2.")
    full = np.full(len(dev), np.nan)
    full[valid] = rebuilt
    opts = {"limiar": policy["limiar"], "consecutivos": policy["consecutivos"]}
    np.testing.assert_array_equal(iniciar_alarmes(full, valid, **opts), iniciar_alarmes(saved, valid, **opts),
                                  err_msg="A reconstrução mudou disparos no desenvolvimento.")
    return scoring, refit, float(np.max(np.abs(rebuilt - saved[valid])))


def table(rows, cols=None):
    frame = pd.DataFrame(rows, columns=cols)
    return frame.round(5).to_html(index=False, na_rep="—")


def export_details(out, name, summary, events, alarms, channels):
    pd.DataFrame(events, columns=["id", "estado", "inicio_anotado_utc", "primeiro_alarme_utc", "atraso_min",
                                "anotacoes_canal_intervalo"]).to_csv(out / f"eventos_{name}.csv", index=False)
    pd.DataFrame(alarms, columns=["instante_utc", "classe", "id_atribuido"]).to_csv(out / f"alarmes_{name}.csv", index=False)
    pd.DataFrame(channels).to_csv(out / f"cobertura_canais_{name}.csv", index=False)
    return {"particao": name, **summary}


def diagnostico_escore(scores, valid, threshold):
    above = valid & (scores >= threshold)
    idx = np.arange(len(above))
    streak = idx - np.maximum.accumulate(np.where(above, -1, idx))
    return {
        "pontos_atingiram_limiar": int(above.sum()),
        "maior_sequencia_acima": int(streak.max()),
        "escore_maximo_utilizavel": float(scores[valid].max()) if valid.any() else None,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_M102, help="Pasta de uma execução M10.2 completa.")
    parser.add_argument("--autoria", type=Path, help="Arquivo .py com iniciar_alarmes.")
    parser.add_argument("--output-dir", type=Path, default=PROJECT / "reports/m10_3")
    args = parser.parse_args(argv)
    input_dir = args.run_dir.resolve()
    func = carregar_autoria(args.autoria) if args.autoria else iniciar_alarmes
    conferir_autoria(func)
    protocol = read_json(PROTOCOL)
    if protocol.get("schema") != "satmon-m10-3-policy-protocol-v1" or tuple(protocol["metodos_em_ordem_de_desempate"]) != SCORES:
        raise ValueError("Protocolo M10.3 incompatível.")
    receipt, dev, evaluator, old_events = ler_desenvolvimento(input_dir, protocol)
    print(f"M10.2 recebido: {receipt['run_id']}; grade preservada. Buscando política só em 2008–2010.", flush=True)
    candidates, choice = escolher(dev, evaluator, protocol, func)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    output = args.output_dir.resolve() / run_id
    output.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(candidates).to_csv(output / "candidatos_dev.csv", index=False)
    basic = {
        "schema": "satmon-m10-3-frozen-policy-v1", "source_run_id": receipt["run_id"],
        "source_receipt_sha256": sha(input_dir / "resultado.json"),
        "development_scores_sha256": receipt["output_sha256"]["escores_desenvolvimento.csv.gz"],
        "protocol_sha256": sha(PROTOCOL), "authorship_sha256": sha(args.autoria) if args.autoria else None,
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "consecutivos": protocol["consecutivos"], "selection_partition": "2008–2010",
        "test_opened_at_freeze": False,
    }
    policy = {**basic, "status": "congelada" if choice else "sem_politica_viavel", "candidato": choice}
    policy_path = output / "politica_congelada.json"
    write_json(policy_path, policy)
    checksum = sha(policy_path)
    policy = read_json(policy_path)
    choice = policy["candidato"]
    heading = '''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Satmon M10.3</title>
    <style>body{font:16px/1.45 system-ui;color:#172933;max-width:1150px;margin:36px auto;padding:0 20px}
    table{border-collapse:collapse;font-size:14px}td,th{padding:6px;border:1px solid #cdd8df}
    th{background:#edf3f6}section{overflow:auto}.note{background:#eef5fa;padding:.8em}</style>
    <h1>M10.3 — Política congelada e avaliação por episódio</h1>'''
    page = heading
    totals, test_source, max_dev_delta = [], None, None
    refit = test_read = False
    if choice:
        method, threshold, k = choice["metodo"], choice["limiar"], policy["consecutivos"]
        print(f"Política gravada: {method}, limiar {threshold:.10g}, {k} confirmações.", flush=True)
        score_dev = dev[method].to_numpy(dtype=float)
        args_fn = {"limiar": threshold, "consecutivos": k}
        starts_dev = conferir_saida(func, score_dev, evaluator.valid, threshold, k)
        dev_summary, dev_events, dev_alarms, dev_channels = evaluator.avaliar(starts_dev, details=True)
        dev_summary.update(diagnostico_escore(score_dev, evaluator.valid, threshold))
        totals.append(export_details(output, "desenvolvimento", dev_summary, dev_events, dev_alarms, dev_channels))
        scoring, refit, max_dev_delta = pontuador(receipt, method, dev, evaluator.valid,
                                                 {"limiar": threshold, "consecutivos": k})

        # Primeira leitura da partição reservada. Nesta fase não há escolha nem ajuste.
        times, x, events = ler_teste(protocol, old_events)
        test_read = True
        test_source = sha(TEST_DATA / "proveniencia.json")
        valid = np.isfinite(x).all(axis=1)
        score = np.full(len(times), np.nan)
        score[valid] = scoring(x[valid])
        if not np.isfinite(score[valid]).all():
            raise ValueError("Escore reservado não finito em instante utilizável.")
        starts = conferir_saida(func, score, valid, threshold, k)
        np.testing.assert_array_equal(starts, iniciar_alarmes(score, valid, **args_fn))
        test = Avaliador(times, valid, events, step_seconds=protocol["grid_step_seconds"])
        test_summary, test_events, test_alarms, test_channels = test.avaliar(starts, details=True)
        test_summary.update(diagnostico_escore(score, valid, threshold))
        totals.append(export_details(output, "teste", test_summary, test_events, test_alarms, test_channels))
        pd.DataFrame({"timestamp": times, "utilizavel": valid, "escore": score,
                      "atingiu_limiar": valid & (score >= threshold),
                      "inicio_alarme": starts}).to_csv(output / "escores_teste.csv.gz", index=False,
                                                       compression={"method": "gzip", "mtime": 0})
        print(pd.DataFrame(totals)[["particao", "ids_detectados", "ids_observaveis", "alarmes_sem_anotacao",
                                      "taxa_sem_anotacao_por_dia", "atraso_mediano_min"]].to_string(index=False))
        page += f"<p>Candidato: <b>{html.escape(method)}</b>; limiar {threshold:.10g}; {k} confirmações.</p>"
        main_cols = ["particao", "ids_detectados", "ids_observaveis", "ids_nao_observaveis", "recall_observaveis",
                     "precisao_por_inicio_avaliavel", "alarmes_total", "alarmes_sem_anotacao", "taxa_sem_anotacao_por_dia",
                     "atraso_mediano_min", "atraso_p90_min"]
        page += "<h2>Mesma política em dois períodos</h2><section>" + table(totals, main_cols) + "</section>"
        page += "<h2>O limiar foi atingido?</h2>" + table(totals, [
            "particao", "escore_maximo_utilizavel", "pontos_atingiram_limiar", "maior_sequencia_acima", "alarmes_total"
        ])
        page += "<h2>IDs no teste</h2><section>" + table(test_events) + "</section>"
        page += "<h2>Primeiro alarme dentro da anotação de cada canal</h2>" + table(test_channels)
    else:
        page += "<p>Nenhum candidato detectou um ID e respeitou o teto. A partição reservada não foi lida.</p>"
        print("Sem política viável. O teste permanece fechado.")
    page += ("<p class='note'>Sem anotação não prova normalidade. As taxas são por 24 horas equivalentes de exposição "
             "utilizável fora de todas as anotações. Atraso descreve somente os IDs detectados. "
             "Experimento no recorte ESA Mission1; sem aprovação operacional.</p>")
    if sha(policy_path) != checksum:
        raise ValueError("A política congelada foi alterada durante a rodada.")
    if totals:
        pd.DataFrame(totals).to_csv(output / "metricas_episodios.csv", index=False)
    (output / "relatorio.html").write_text(page, encoding="utf-8")
    report = {
        "schema": "satmon-m10-3-result-v1", "completed": True, "run_id": run_id,
        "source_run_id": receipt["run_id"], "politica_sha256": checksum,
        "protocol_sha256": policy["protocol_sha256"], "authorship_sha256": policy["authorship_sha256"],
        "code_sha256": {"runner": sha(Path(__file__)), "core": sha(PROJECT / "src/satmon/alarmes_m10_3.py")},
        "versions": {"python": sys.version.split()[0], "numpy": np.__version__, "pandas": pd.__version__,
                     "scikit-learn": version("scikit-learn") if refit else None},
        "n_candidatos": len(candidates), "n_viaveis": int(sum(row["viavel"] for row in candidates)),
        "politica_status": policy["status"], "periodo_reservado_avaliado": test_read,
        "source_test_sha256": test_source, "reconstituicao_floresta_usou_somente_ajuste_original": refit,
        "max_delta_escore_dev_para_pontuar_teste": max_dev_delta, "metricas": totals,
        "operational_approval": False, "autoria_conferida_contra_referencia": bool(args.autoria),
        "output_sha256": {f.name: sha(f) for f in sorted(output.iterdir()) if f.is_file()},
    }
    write_json(output / "resultado.json", report)
    pointer = output.parent / f".latest_run_{run_id}.json"
    write_json(pointer, {"directory": str(output), "run_id": run_id, "resultado_sha256": sha(output / "resultado.json")})
    pointer.replace(output.parent / "latest_run.json")
    print(f"Relatório: {output / 'relatorio.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
