"""Audita os escores M10.2 persistidos, sem ajuste de modelos ou inferência.

Na raiz: python satellite-anomaly-monitor/docs/evidencias_m10_2_local/auditar_resultados.py
Usa NumPy, pandas e biblioteca padrão. Não importa o laboratório, Detectores,
a função autoral ou a referência. AP é recalculada por blocos de empates.
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
DATA = PROJECT / "data/reference/esa_mission1_m10_2"
DEFAULT_RUN = PROJECT / "reports/m10_2/20261119T101049Z_253ff59f"
OUTPUT = Path(__file__).with_name("auditoria_resultados.json")
CHANNELS = ("channel_50", "channel_51", "channel_52")
SCORES = ("score_robusto", "score_pca", "score_isolation")
CATEGORIES = {"Anomaly": "anomaly", "Rare Event": "rare", "Communication Gap": "gap"}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def csv(path):
    # Preserva os empates emitidos pelo writer para AP e percentis.
    return pd.read_csv(path, float_precision="round_trip")


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def times(values):
    return pd.DatetimeIndex(pd.to_datetime(values, format="mixed", utc=True)).astype("datetime64[ns, UTC]")


def same(actual, expected, name, *, atol=1e-10, rtol=1e-12):
    np.testing.assert_allclose(np.asarray(actual, dtype=float), np.asarray(expected, dtype=float),
                               atol=atol, rtol=rtol, equal_nan=True, err_msg=name)


def same_frame(actual, expected, name, temporal=()):
    require(actual.columns.tolist() == expected.columns.tolist(), f"Colunas divergentes: {name}")
    require(len(actual) == len(expected), f"Quantidade de linhas divergente: {name}")
    for column in expected:
        if column in temporal:
            np.testing.assert_array_equal(times(actual[column]).asi8, times(expected[column]).asi8,
                                          err_msg=f"{name}.{column}")
        elif pd.api.types.is_numeric_dtype(expected[column]):
            same(actual[column], expected[column], f"{name}.{column}")
        else:
            require(actual[column].reset_index(drop=True).equals(expected[column].reset_index(drop=True)),
                    f"Valores divergentes: {name}.{column}")


def ap_by_ties(y, scores):
    """AP não interpolada: avança todos os exemplos com mesmo escore juntos."""
    y, scores = np.asarray(y, dtype=bool), np.asarray(scores, dtype=float)
    require(y.shape == scores.shape and y.ndim == 1 and y.any() and (~y).any(), "Coorte AP inválida.")
    require(np.isfinite(scores).all(), "Escores AP não finitos.")
    order = np.argsort(-scores, kind="stable")
    ranked_scores, ranked_y = scores[order], y[order]
    ends = np.flatnonzero(np.r_[ranked_scores[:-1] != ranked_scores[1:], True])
    tp = ranked_y.cumsum()[ends]
    precision = tp / (ends + 1)
    added_tp = np.diff(np.r_[0, tp])
    return float(np.dot(precision, added_tp) / y.sum())


def ap_table(y, cohort):
    return {"constante": float(y.mean()), **{name: ap_by_ties(y, cohort[name]) for name in SCORES}}


def audit(run):
    result = read_json(run / "resultado.json")
    spec = read_json(DATA / "protocolo.json")
    require(result["schema"] == "satmon-m10-2-result-v1" and result["completed"] is True, "Resultado incompleto.")
    require(result["run_id"] == run.name and spec["schema"] == "satmon-m10-2-source-v1", "Identidades incompatíveis.")
    require(tuple(spec["channels"]) == CHANNELS, "Canais fora do contrato.")
    require(result["settings"] == spec["settings"], "Configuração diferente do protocolo.")
    require(result["source_slice"] == [spec[k] for k in ("start", "split", "stop_exclusive")], "Cortes divergentes.")
    latest = read_json(run.parent / "latest_run.json")
    require(latest["run_id"] == run.name and latest["resultado_sha256"] == sha(run / "resultado.json"), "Ponteiro latest divergente.")
    checked_hashes = {}

    def check_hash(path, expected):
        actual = sha(path)
        require(actual == expected, f"SHA-256 divergente: {path}")
        checked_hashes[path.relative_to(PROJECT).as_posix()] = actual

    check_hash(DATA / "protocolo.json", result["source_spec_sha256"])
    for name, entry in spec["files"].items():
        require((DATA / name).stat().st_size == entry["bytes"], f"Tamanho divergente: {name}")
        check_hash(DATA / name, entry["sha256"])
    check_hash(PROJECT / "scripts/executar_m10_2.py", result["code_sha256"]["runner"])
    check_hash(PROJECT / "src/satmon/detectores_m10_2.py", result["code_sha256"]["core"])
    check_hash(PROJECT / "notebooks/m10_2_pca_autoral.py", result["authorship_sha256"])
    for name, expected in result["output_sha256"].items():
        check_hash(run / name, expected)
    for field in ("threshold_selected", "holdout_scored", "operational_approval"):
        require(result[field] is False, f"Escopo inesperado: {field}")
    require(result["small_projection_checks_passed"] is True, "Contas geométricas não aprovadas.")

    raw = csv(DATA / "canais_grade.csv.gz")
    require(raw.columns.tolist() == ["timestamp", *(f"{c}_{suffix}" for c in CHANNELS
            for suffix in ("sample_time", "age_seconds", "value"))], "Colunas de entrada fora do contrato.")
    index = times(raw.timestamp)
    first, split, end = (pd.Timestamp(spec[key]) for key in ("start", "split", "stop_exclusive"))
    expected_index = pd.date_range(first, end, freq=f"{spec['step_seconds']}s", inclusive="left").astype("datetime64[ns, UTC]")
    require(len(raw) == spec["grid_rows"], "Tamanho da grade divergente.")
    np.testing.assert_array_equal(index.asi8, expected_index.asi8)
    fit_partition = np.asarray(index < split)
    dev = ~fit_partition
    values = raw[[f"{channel}_value" for channel in CHANNELS]].to_numpy(dtype=float)
    usable = np.isfinite(values).all(axis=1)
    time_contract = []
    for column in CHANNELS:
        sample = times(raw[f"{column}_sample_time"])
        known = ~sample.isna()
        ages = raw[f"{column}_age_seconds"].to_numpy(dtype=float)
        age_expected = np.full(len(raw), np.nan)
        age_expected[known] = (index.asi8[known] - sample.asi8[known]) / 1e9
        same(ages, age_expected, f"Idades de {column}", rtol=0, atol=1e-9)
        bounds = np.where(fit_partition, first.value, split.value)
        require(np.all(sample.asi8[known] <= index.asi8[known]), f"Amostra futura em {column}.")
        require(np.all(sample.asi8[known] >= bounds[known]), f"Amostra de outra partição em {column}.")
        has_value = raw[f"{column}_value"].notna().to_numpy()
        require(not np.isinf(raw[f"{column}_value"]).any(), f"Valor infinito em {column}.")
        require(not np.any(has_value & (~known | (ages > spec["max_age_seconds"]))), f"Frescor inválido em {column}.")
        time_contract.append({"channel": column, "grid_rows_with_value": int(has_value.sum()),
            "no_previous_sample_rows": int((~known).sum()), "expired_sample_rows": int((known & (ages > spec["max_age_seconds"])).sum())})

    events = csv(DATA / "eventos.csv")
    require(events.Channel.isin(CHANNELS).all() and events.Category.isin(CATEGORIES).all(), "Canal ou categoria inválida.")
    require(events.partition.isin(("ajuste", "desenvolvimento")).all(), "Partição inválida.")
    require(events.groupby("ID").partition.nunique().le(1).all() and events.groupby("ID").Category.nunique().le(1).all(), "IDs compartilhados entre partições ou categorias.")
    starts, stops = times(events.StartTime), times(events.EndTime)
    require(np.all(starts.asi8 <= stops.asi8), "Evento com intervalo invertido.")
    event_fit = events.partition.eq("ajuste").to_numpy()
    require(np.all(stops.asi8 >= np.where(event_fit, first.value, split.value)), "Evento anterior à partição.")
    require(np.all(stops.asi8 < np.where(event_fit, split.value, end.value)), "Evento posterior à partição.")
    require(np.all(starts.asi8[~event_fit] >= split.value), "Evento cruzou o corte ajuste/desenvolvimento.")
    flags = {name: np.zeros(len(raw), dtype=bool) for name in CATEGORIES.values()}
    event_masks = {}
    # União de intervalos sobre todos os canais: não soma uma linha por canal.
    for row, start, stop in zip(events.itertuples(index=False), starts.asi8, stops.asi8):
        mask = (index.asi8 >= start) & (index.asi8 <= stop)
        flags[CATEGORIES[row.Category]] |= mask
        event_masks.setdefault(row.ID, np.zeros(len(raw), dtype=bool))[:] |= mask
    unannotated = ~(flags["anomaly"] | flags["rare"] | flags["gap"])
    fit_ok = fit_partition & usable & unannotated
    evaluate = dev & usable & ~(flags["rare"] | flags["gap"])
    scoreable = dev & usable
    y = flags["anomaly"][evaluate]
    counts = {"grid_rows_fit": int(fit_partition.sum()), "fit_rows_used": int(fit_ok.sum()),
        "grid_rows_dev": int(dev.sum()), "dev_rows_unscored": int((dev & ~usable).sum()),
        "dev_rows_scored": int(scoreable.sum()), "dev_rows_evaluated": int(evaluate.sum()),
        "dev_positive_points": int(y.sum())}
    for name, expected in counts.items():
        require(result[name] == expected, f"Contagem divergente: {name}")

    dev_rows = csv(run / "escores_desenvolvimento.csv.gz")
    require(len(dev_rows) == dev.sum(), "Faltam linhas de desenvolvimento, inclusive não pontuadas.")
    same_frame(dev_rows[raw.columns], raw.loc[dev].reset_index(drop=True), "Inputs conservados",
               temporal=("timestamp", *(f"{c}_sample_time" for c in CHANNELS)))
    for name, expected in {"utilizavel": usable[dev], "entra_no_ranking": evaluate[dev],
                           **{f"anotacao_{name}": mask[dev] for name, mask in flags.items()}}.items():
        require(pd.api.types.is_bool_dtype(dev_rows[name]), f"Máscara não booleana: {name}")
        np.testing.assert_array_equal(dev_rows[name], expected, err_msg=name)
    local_scoreable = scoreable[dev]
    for name in (*SCORES, "grupo_kmeans"):
        require(np.isfinite(dev_rows.loc[local_scoreable, name]).all(), f"Escore ausente: {name}")
        require(dev_rows.loc[~local_scoreable, name].isna().all(), f"Linha sem dados foi pontuada: {name}")

    medians = np.asarray(result["robust_medians"], dtype=float)
    scales = np.asarray(result["robust_scaled_mads"], dtype=float)
    require(medians.shape == scales.shape == (3,) and np.isfinite(medians).all() and np.all(scales > 0), "Parâmetros robustos inválidos.")
    # Conferência de estatísticas fixas; nenhum modelo ou scaler é reajustado.
    fit_medians = np.median(values[fit_ok], axis=0)
    fit_scales = 1.4826 * np.median(np.abs(values[fit_ok] - fit_medians), axis=0)
    same(medians, fit_medians, "Medianas do ajuste", atol=1e-15)
    same(scales, fit_scales, "MADs do ajuste", atol=1e-15)
    z = (values[scoreable] - medians) / scales
    robust = np.max(np.abs(z), axis=1)
    same(dev_rows.loc[local_scoreable, "score_robusto"], robust, "Escores robustos de todos os instantes")
    center = np.asarray(result["pca_center_in_scaled_space"], dtype=float)
    components = np.asarray(result["pca_components"], dtype=float)
    require(center.shape == (3,) and components.shape == (spec["settings"]["pca_components"], 3), "Shapes PCA inválidos.")
    same(components @ components.T, np.eye(len(components)), "Ortonormalidade das linhas PCA", atol=1e-12)
    # Projeção complementar independente da reconstrução usada pela função autoral.
    residual = (z - center) @ (np.eye(3) - components.T @ components)
    pca = np.einsum("ij,ij->i", residual, residual)
    persisted_pca = dev_rows.loc[local_scoreable, "score_pca"].to_numpy()
    same(persisted_pca, pca, "PCA por projeção complementar", atol=1e-11, rtol=1e-10)
    zfit = (values[fit_ok] - medians) / scales
    same(center, zfit.mean(axis=0), "Centro PCA do ajuste", atol=1e-12)
    variance_ratios = np.var((zfit - center) @ components.T, axis=0, ddof=1) / np.var(zfit, axis=0, ddof=1).sum()
    same(result["pca_explained_variance_ratios"], variance_ratios, "Variância nas direções persistidas", atol=1e-12)

    cohort = dev_rows.loc[dev_rows.entra_no_ranking].copy()
    np.testing.assert_array_equal(cohort.anotacao_anomaly, y)
    full_ap = ap_table(y, cohort)
    metrics = pd.DataFrame([{"escore": name, "average_precision": value, "linhas": len(y), "positivos": int(y.sum())} for name, value in full_ap.items()])
    same_frame(csv(run / "metricas.csv"), metrics, "AP completa")
    for name, value in full_ap.items():
        same(value, result["average_precision"][name], f"AP no resultado: {name}", atol=1e-14)

    coverages = []
    for eid, group in events.groupby("ID", sort=True):
        mask = event_masks[eid]
        coverages.append({"id": eid, "categoria": group.Category.iloc[0], "particao": group.partition.iloc[0],
            "anotacoes_canal_intervalo": len(group), "inicio_utc": group.StartTime.min(), "fim_utc": group.EndTime.max(),
            "linhas_na_grade": int(mask.sum()), "linhas_utilizaveis": int((mask & usable).sum()),
            "linhas_entram_no_ranking_dev": int((mask & evaluate).sum())})
    coverage = pd.DataFrame(coverages)
    same_frame(csv(run / "cobertura_eventos.csv"), coverage, "Cobertura por ID", temporal=("inicio_utc", "fim_utc"))
    focus = coverage.loc[coverage.particao.eq("desenvolvimento") & coverage.categoria.eq("Anomaly")]
    require(len(focus) == result["dev_anomaly_ids"], "Quantidade de IDs Anomaly divergente.")
    require(int(focus.linhas_entram_no_ranking_dev.eq(0).sum()) == result["dev_anomaly_ids_without_eval_points"], "IDs sem cobertura divergentes.")
    largest = focus.loc[focus.linhas_entram_no_ranking_dev.idxmax()]
    omitted = event_masks[largest.id][evaluate]
    require(np.all(y[omitted]), "A remoção do maior ID incluiu pontos não positivos.")
    reduced_cohort = cohort.loc[~omitted]
    reduced_y = y[~omitted]
    reduced_ap = ap_table(reduced_y, reduced_cohort)
    sensitivity = pd.DataFrame([{"escore": name, "average_precision": value, "id_removido": largest.id,
        "linhas": len(reduced_y), "positivos": int(reduced_y.sum())} for name, value in reduced_ap.items()])
    same_frame(csv(run / "sensibilidade_evento.csv"), sensitivity, "Sensibilidade com escores fixos")
    saved_sensitivity = result["sensitivity_to_largest_annotation"]
    require(saved_sensitivity["id"] == largest.id and saved_sensitivity["refit"] is False and saved_sensitivity["diagnostic_only"] is True, "Diagnóstico de sensibilidade incompatível.")
    require(int(omitted.sum()) == saved_sensitivity["removed_positive_points"], "Quantidade removida divergente.")
    same(float(omitted.sum() / y.sum()), saved_sensitivity["share_of_all_positive_points"], "Participação do maior evento")
    for name, value in reduced_ap.items():
        same(value, saved_sensitivity["average_precision"][name], f"AP reduzida: {name}", atol=1e-14)

    for name in SCORES:
        cohort[f"rank_{name}_pct"] = 100 * cohort[name].rank(method="average", pct=True)
    positives = cohort.loc[cohort.anotacao_anomaly]
    difference = positives.rank_score_pca_pct - positives.rank_score_robusto_pct
    selected = {"pca_relativamente_alto": difference.idxmax(), "robusto_relativamente_alto": difference.idxmin(),
        "isolation_alto_sem_anotacao": cohort.loc[~cohort.anotacao_anomaly, "score_isolation"].idxmax()}
    case_columns = ["timestamp", "anotacao_anomaly", *(f"{c}_value" for c in CHANNELS),
        *SCORES, *(f"rank_{name}_pct" for name in SCORES)]
    cases = pd.DataFrame([{"caso": name, **cohort.loc[idx, case_columns].to_dict()} for name, idx in selected.items()])
    same_frame(csv(run / "casos_reais.csv"), cases, "Seleção de casos e percentis", temporal=("timestamp",))
    require(cohort.grupo_kmeans.isin(range(spec["settings"]["kmeans_clusters"])).all(), "ID K-means fora da faixa.")
    contexts = cohort.groupby("grupo_kmeans", as_index=False).agg(linhas=("anotacao_anomaly", "size"),
        positivos=("anotacao_anomaly", "sum"), mediana_escore_pca=("score_pca", "median"),
        mediana_escore_robusto=("score_robusto", "median"))
    contexts["fracao_positiva_anotada"] = contexts.positivos / contexts.linhas
    same_frame(csv(run / "contextos.csv"), contexts, "Contextos com atribuições persistidas")
    case_records = cases.to_dict(orient="records")
    return {"schema": "satmon-m10-2-independent-audit-v1", "verified": True,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(), "run_id": run.name,
        "run_directory": run.relative_to(PROJECT).as_posix(),
        "audit_versions": {"numpy": np.__version__, "pandas": pd.__version__},
        "method": "Persisted-score audit; NumPy tie-block AP; complementary PCA projection. No model, authored function, reference or runner imported; no refit.",
        "checks": {"source_input_code_author_output_hashes": True, "latest_result_identity": True,
            "time_grid_age_partition_and_freshness": True, "fit_and_development_cohorts_recomputed": True,
            "category_masks_and_union_coverage_per_id": True, "robust_scores_recomputed": True,
            "pca_scores_from_persisted_components": True, "full_ap_recomputed_with_ties": True,
            "sensitivity_ap_uses_same_fixed_scores": True, "case_selection_and_percentiles": True,
            "context_aggregates_from_persisted_assignments": True},
        "checked_hashes": checked_hashes, "cohort_counts": counts,
        "dev_scored_but_excluded_by_category": int((scoreable & ~evaluate).sum()),
        "time_contract": time_contract, "full_average_precision": full_ap,
        "largest_anomaly_id": largest.id, "largest_id_grid_rows": int(largest.linhas_na_grade),
        "largest_id_usable_eval_rows": int(largest.linhas_entram_no_ranking_dev),
        "largest_id_share_of_positive_points": float(omitted.sum() / y.sum()),
        "reduced_cohort_rows": len(reduced_y), "reduced_positive_points": int(reduced_y.sum()),
        "average_precision_without_largest_id_fixed_scores": reduced_ap,
        "pca_independent_projection_max_abs_difference": float(np.max(np.abs(persisted_pca - pca))),
        "pca_retained_variance_fraction": float(variance_ratios.sum()),
        "cases_recomputed": case_records,
        "coverage_development_anomaly_ids": focus.to_dict(orient="records"),
        "limits": {"forest_checkpoint_available": False, "forest_scores_reproduced": False,
            "forest_score_ap_audited_from_persisted_values": True,
            "kmeans_centers_available": False, "kmeans_assignment_reproduced": False,
            "kmeans_aggregates_audited_from_persisted_values": True,
            "raw_archive_members_reacquired_or_verified_now": False,
            "input_grid_source_hashes_and_time_contract_verified": True,
            "reserved_period_evaluated": False, "new_models_fitted": False,
            "notes": "This audits the supplied grid, not the unavailable full raw mission or physical arrival latency. Annotation completeness and operational performance remain unverified."}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    args = parser.parse_args()
    result = audit(args.run_dir.resolve())
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Auditoria aprovada: {result['cohort_counts']['dev_rows_evaluated']} instantes na coorte; escores fixos, sem refit.")
    print(f"Run: {result['run_id']}; JSON: {OUTPUT}")


if __name__ == "__main__":
    main()
