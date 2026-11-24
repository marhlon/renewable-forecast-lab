"""M10.2: comparação temporal de detectores, sem escolher limiar."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import sys
import uuid

import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import average_precision_score

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from satmon.detectores_m10_2 import Detectores, conferir_projecao, erro_pca_por_amostra

DATA = PROJECT / "data/reference/esa_mission1_m10_2"
CHANNELS = ("channel_50", "channel_51", "channel_52")
SCORES = ("score_robusto", "score_pca", "score_isolation")
CATEGORIES = {"Anomaly": "anomaly", "Rare Event": "rare", "Communication Gap": "gap"}
NS = 1_000_000_000


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def times_utc(values):
    # A representação da resolução pode diferir no pandas 2 e 3.
    return pd.DatetimeIndex(pd.to_datetime(values, format="ISO8601", utc=True)).astype("datetime64[ns, UTC]")


def carregar():
    spec = json.loads((DATA / "protocolo.json").read_text(encoding="utf-8"))
    if spec["schema"] != "satmon-m10-2-source-v1" or tuple(spec["channels"]) != CHANNELS:
        raise ValueError("Protocolo M10.2 incompatível.")
    if set(spec["files"]) != {"canais_grade.csv.gz", "eventos.csv"}:
        raise ValueError("Lista de insumos M10.2 incompatível.")
    for name, metadata in spec["files"].items():
        path = DATA / name
        if not path.is_file() or path.stat().st_size != metadata["bytes"] or sha(path) != metadata["sha256"]:
            raise ValueError(f"Insumo do pacote ausente ou alterado: {path}")

    raw = pd.read_csv(DATA / "canais_grade.csv.gz", float_precision="round_trip")
    expected_cols = ["timestamp", *(f"{c}_{suffix}" for c in CHANNELS
                                     for suffix in ("sample_time", "age_seconds", "value"))]
    if raw.columns.tolist() != expected_cols:
        raise ValueError("A grade aceita somente as três medições e seu contrato de tempo.")
    index = times_utc(raw.timestamp)
    first, split, end = (pd.Timestamp(spec[k]) for k in ("start", "split", "stop_exclusive"))
    expected = pd.date_range(first, end, freq=f"{spec['step_seconds']}s", inclusive="left")
    if len(index) != spec["grid_rows"] or not np.array_equal(index.asi8, expected.astype("datetime64[ns, UTC]").asi8):
        raise ValueError("Grade com instantes faltantes, alterados ou fora de ordem.")
    fit_partition = index < split
    values = raw[[f"{c}_value" for c in CHANNELS]].to_numpy(dtype=float)
    usable = np.isfinite(values).all(axis=1)
    for channel in CHANNELS:
        sample = times_utc(raw[f"{channel}_sample_time"])
        selected = ~sample.isna()
        age_expected = np.full(len(raw), np.nan)
        age_expected[selected] = (index.asi8[selected] - sample.asi8[selected]) / NS
        ages = raw[f"{channel}_age_seconds"].to_numpy(dtype=float)
        np.testing.assert_allclose(ages, age_expected, rtol=0, atol=1e-9, equal_nan=True)
        lower_bound = np.where(fit_partition, first.value, split.value)
        has_value = raw[f"{channel}_value"].notna().to_numpy()
        if (np.isinf(values).any() or (ages[selected] < 0).any()
                or (sample.asi8[selected] < lower_bound[selected]).any()
                or (has_value & (~selected | (ages > spec["max_age_seconds"]))).any()):
            raise ValueError(f"Futuro, fronteira ou frescor violado em {channel}.")

    events = pd.read_csv(DATA / "eventos.csv")
    if (not set(events.Channel).issubset(CHANNELS)
            or not set(events.Category).issubset(CATEGORIES)
            or not set(events.partition).issubset({"ajuste", "desenvolvimento"})
            or events.groupby("ID").partition.nunique().gt(1).any()
            or events.groupby("ID").Category.nunique().gt(1).any()):
        raise ValueError("Anotações com canal/categoria/partição inválidos ou IDs compartilhados.")
    events["start_ns"] = times_utc(events.StartTime).asi8
    events["end_ns"] = times_utc(events.EndTime).asi8
    ft = events.partition.eq("ajuste").to_numpy()
    if (events.start_ns.gt(events.end_ns).any()
            or (events.end_ns < np.where(ft, first.value, split.value)).any()
            or (events.end_ns >= np.where(ft, split.value, end.value)).any()
            or (events.loc[~ft, "start_ns"] < split.value).any()):
        raise ValueError("Intervalo de anotação inválido ou fora da partição declarada.")
    flags = {key: np.zeros(len(index), dtype=bool) for key in CATEGORIES.values()}
    for event in events.itertuples(index=False):
        left = np.searchsorted(index.asi8, event.start_ns, side="left")
        right = np.searchsorted(index.asi8, event.end_ns, side="right")
        flags[CATEGORIES[event.Category]][left:right] = True
    return spec, raw, index, values, usable, fit_partition, events, flags


def load_authored(path):
    if not path.is_file():
        raise FileNotFoundError(f"Salve a sua função em {path}. Consulte a Aula 2; omita --autoria para usar a referência.")
    spec = importlib.util.spec_from_file_location("m10_2_pca_autoral", path.resolve())
    if spec is None or spec.loader is None:
        raise ValueError("O caminho autoral precisa apontar para um arquivo .py.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.erro_pca_por_amostra


def mascara_evento(index, group):
    mask = np.zeros(len(index), dtype=bool)
    instantes = index.asi8
    for row in group.itertuples(index=False):
        lo = np.searchsorted(instantes, row.start_ns, side="left")
        hi = np.searchsorted(instantes, row.end_ns, side="right")
        mask[lo:hi] = True
    return mask


def cobertura_por_id(index, events, usable, evaluate):
    rows = []
    for eid, group in events.groupby("ID", sort=True):
        mask = mascara_evento(index, group)
        rows.append({"id": eid, "categoria": group.Category.iloc[0], "particao": group.partition.iloc[0],
                     "anotacoes_canal_intervalo": len(group), "inicio_utc": group.StartTime.min(),
                     "fim_utc": group.EndTime.max(), "linhas_na_grade": int(mask.sum()),
                     "linhas_utilizaveis": int((mask & usable).sum()),
                     "linhas_entram_no_ranking_dev": int((mask & evaluate).sum())})
    return pd.DataFrame(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--autoria", type=Path, help="Arquivo .py com erro_pca_por_amostra(x, centro, componentes).")
    parser.add_argument("--output-dir", type=Path, default=PROJECT / "reports/m10_2")
    args = parser.parse_args(argv)
    method = load_authored(args.autoria) if args.autoria else erro_pca_por_amostra
    conferir_projecao(method)
    print("PCA: duas contas geométricas conferidas.", flush=True)
    spec, raw, index, values, usable, fit_partition, events, flags = carregar()
    unannotated = ~(flags["anomaly"] | flags["rare"] | flags["gap"])
    dev = ~fit_partition
    fit_ok = fit_partition & usable & unannotated
    eval_ok = dev & usable & ~(flags["rare"] | flags["gap"])
    y = flags["anomaly"][eval_ok]
    if not fit_ok.any() or not dev.any() or not (y.any() and (~y).any()):
        raise ValueError("O recorte não contém ajuste, ou as duas classes de avaliação.")

    print(f"Ajuste com {fit_ok.sum():,} linhas; desenvolvimento com {eval_ok.sum():,} linhas comparáveis.", flush=True)
    detectors = Detectores.ajustar(values[fit_ok], spec["settings"])
    dev_scoreable = dev & usable
    scores, pca_delta = detectors.pontuar(values[dev_scoreable], method)

    # Escores não recebem rótulos. A associação abaixo existe só para a análise.
    dev_rows = raw.loc[dev].copy()
    dev_rows["utilizavel"] = usable[dev]
    dev_rows["entra_no_ranking"] = eval_ok[dev]
    for label, mask in flags.items():
        dev_rows[f"anotacao_{label}"] = mask[dev]
    for column, vector in scores.items():
        if not np.isfinite(vector).all():
            raise ValueError(f"Saída não finita em {column}.")
        dev_rows.loc[dev_scoreable[dev], column] = vector
    cohort = dev_rows.loc[dev_rows.entra_no_ranking].copy()
    baseline_ap = float(y.mean())
    metrics = pd.DataFrame([
        {"escore": "constante", "average_precision": baseline_ap},
        *({"escore": sc, "average_precision": float(average_precision_score(y, cohort[sc]))}
          for sc in SCORES),
    ]).assign(linhas=len(y), positivos=int(y.sum()))
    for sc in SCORES:
        cohort[f"rank_{sc}_pct"] = 100 * cohort[sc].rank(method="average", pct=True)
    contexts = cohort.groupby("grupo_kmeans", as_index=False).agg(
        linhas=("anotacao_anomaly", "size"), positivos=("anotacao_anomaly", "sum"),
        mediana_escore_pca=("score_pca", "median"), mediana_escore_robusto=("score_robusto", "median"),
    )
    contexts["fracao_positiva_anotada"] = contexts.positivos / contexts.linhas

    positives = cohort.loc[cohort.anotacao_anomaly]
    difference = positives.rank_score_pca_pct - positives.rank_score_robusto_pct
    indices = {"pca_relativamente_alto": difference.idxmax(),
               "robusto_relativamente_alto": difference.idxmin(),
               "isolation_alto_sem_anotacao": cohort.loc[~cohort.anotacao_anomaly, "score_isolation"].idxmax()}
    case_columns = ["timestamp", "anotacao_anomaly", *(f"{c}_value" for c in CHANNELS),
                    *SCORES, *(f"rank_{c}_pct" for c in SCORES)]
    cases = pd.DataFrame([{"caso": name, **cohort.loc[idx, case_columns].to_dict()} for name, idx in indices.items()])
    coverage = cobertura_por_id(index, events, usable, eval_ok)
    focus = coverage.loc[coverage.particao.eq("desenvolvimento") & coverage.categoria.eq("Anomaly")].copy()
    longest = focus.loc[focus.linhas_entram_no_ranking_dev.idxmax()]
    omitted = mascara_evento(index, events.loc[events.ID.eq(longest.id)])[eval_ok]
    y_without = y[~omitted]
    if not (y_without.any() and (~y_without).any()):
        raise ValueError("Coorte diagnóstica sem as duas classes.")
    sensitivity = pd.DataFrame([
        {"escore": "constante", "average_precision": float(y_without.mean())},
        *({"escore": sc, "average_precision": float(average_precision_score(y_without, cohort[sc].to_numpy()[~omitted]))}
          for sc in SCORES),
    ]).assign(id_removido=longest.id, linhas=len(y_without), positivos=int(y_without.sum()))

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    output = args.output_dir.resolve() / run_id
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": "satmon-m10-2-result-v1", "completed": True, "run_id": run_id,
        "source_spec_sha256": sha(DATA / "protocolo.json"),
        "source_slice": [spec["start"], spec["split"], spec["stop_exclusive"]],
        "grid_rows_fit": int(fit_partition.sum()), "fit_rows_used": int(fit_ok.sum()),
        "grid_rows_dev": int(dev.sum()), "dev_rows_unscored": int((dev & ~usable).sum()),
        "dev_rows_scored": int(dev_scoreable.sum()), "dev_rows_evaluated": len(y),
        "dev_positive_points": int(y.sum()), "dev_anomaly_ids": len(focus),
        "dev_anomaly_ids_without_eval_points": int(focus.linhas_entram_no_ranking_dev.eq(0).sum()),
        "average_precision": dict(zip(metrics.escore, metrics.average_precision)),
        "sensitivity_to_largest_annotation": {
            "id": longest.id, "removed_positive_points": int(omitted.sum()),
            "share_of_all_positive_points": float(omitted.sum() / y.sum()),
            "average_precision": dict(zip(sensitivity.escore, sensitivity.average_precision)),
            "refit": False, "diagnostic_only": True,
        },
        "robust_medians": detectors.mediana.tolist(), "robust_scaled_mads": detectors.escala.tolist(),
        "pca_center_in_scaled_space": detectors.pca.mean_.tolist(),
        "pca_components": detectors.pca.components_.tolist(),
        "pca_explained_variance_ratios": detectors.pca.explained_variance_ratio_.tolist(),
        "max_pca_difference_vs_sklearn": pca_delta,
        "authorship_sha256": sha(args.autoria) if args.autoria else None,
        "code_sha256": {"runner": sha(Path(__file__)),
                        "core": sha(PROJECT / "src/satmon/detectores_m10_2.py")},
        "small_projection_checks_passed": True,
        "settings": spec["settings"], "platform": sys.platform,
        "versions": {"python": sys.version.split()[0], "pandas": pd.__version__,
                     "numpy": np.__version__, "scikit-learn": sklearn.__version__},
        "threshold_selected": False, "holdout_scored": False, "operational_approval": False,
    }
    for name, frame in (("metricas.csv", metrics), ("casos_reais.csv", cases),
                        ("cobertura_eventos.csv", coverage), ("contextos.csv", contexts),
                        ("sensibilidade_evento.csv", sensitivity),
                        ("escores_desenvolvimento.csv.gz", dev_rows)):
        if name.endswith(".gz"):
            frame.to_csv(output / name, index=False, compression={"method": "gzip", "mtime": 0})
        else:
            frame.to_csv(output / name, index=False)

    report_head = """<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>M10.2 — detectores</title>
    <style>body{font:16px/1.55 system-ui;margin:2em auto;padding:0 18px;max-width:1100px;color:#132630}
    table{border-collapse:collapse;font-size:14px;width:100%;margin:0.8em 0}th,td{text-align:right;padding:6px;border:1px solid #d5e0e6}
    th{background:#e9f2f5}th:first-child,td:first-child{text-align:left}.scroll{overflow:auto}pre{overflow:auto;background:#edf2f6;padding:10px}</style>"""
    report_body = (f"<h1>M10.2 — três detectores, mesmos instantes</h1><p>ESA Mission1: ajuste 2004–2007; desenvolvimento 2008–2010. "
                   f"{len(y):,} instantes comparados, {int(y.sum()):,} positivos anotados. Sem limiar ou teste final.</p>"
                   "<h2>Ranking de instantes</h2>" + metrics.round(6).to_html(index=False)
                   + "<p>AP favorece identificar instantes anotados no ranking. Eventos longos podem dominar a métrica. "
                     "Sem anotação é um negativo provisório no cálculo.</p><h2>Casos para explicar</h2><div class='scroll'>"
                   + cases.round(6).to_html(index=False) + "</div><p>Rank em % é posição no recorte de desenvolvimento, não probabilidade.</p>"
                   + "<h2>Eventos Anomaly no desenvolvimento</h2>" + focus.to_html(index=False)
                   + "<h2>Sensibilidade ao evento de maior presença</h2>" + sensitivity.round(6).to_html(index=False)
                   + "<p>Somente os instantes desse ID foram retirados da avaliação. Os escores permanecem fixos. "
                     "A prevalência e a coorte mudaram; compare métodos dentro de cada tabela.</p>"
                   + "<h2>Agrupamento para investigar contexto</h2>" + contexts.round(6).to_html(index=False)
                   + "<p>O ID do grupo é arbitrário. Não foi usado para definir rótulo nem alarme.</p>"
                   + "<h2>Configuração e limites</h2><pre>" + html.escape(json.dumps(report, ensure_ascii=False, indent=2)) + "</pre></html>")
    (output / "relatorio.html").write_text(report_head + report_body, encoding="utf-8")
    report["output_sha256"] = {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    write_json(output / "resultado.json", report)
    pointer = output.parent / f".latest_run_{run_id}.json"
    write_json(pointer, {"run_id": run_id, "directory": str(output), "resultado_sha256": sha(output / "resultado.json")})
    pointer.replace(output.parent / "latest_run.json")
    print(metrics.to_string(index=False, float_format=lambda v: f"{v:.6f}"))
    print(f"PCA: diferença máxima para scikit-learn = {pca_delta:.3g}.")
    print(f"Relatório: {output / 'relatorio.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
