"""Recalcula a entrega M09.3 a partir dos arquivos salvos, sem inferência.

Na raiz: python docs/evidencias_m09_3_local/auditar_resultados.py
Exige NumPy, pandas, PyArrow (engine da leitura Parquet) e biblioteca padrão.
Não importa o controlador, a implementação autoral, Chronos ou PyTorch e
não faz downloads.
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


ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "reports/transformer/CJU_BA5EIGT/m09_3_pre_treinado/20261117T213329Z_3b201a01"
BASELINE = ROOT / "reports/neural/CJU_BA5EIGT/m08_3_gru/20261115T170309Z_90a6625f"
INPUT = ROOT / "dist/databricks/CJU_BA5EIGT/m07_3"
OUTPUT = Path(__file__).with_name("auditoria_resultados.json")
METHOD = "chronos_bolt_tiny_zero_shot"
HOUR_NS = 3_600_000_000_000


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def same(actual, expected, message, *, equal_nan=False):
    a, b = np.asarray(actual), np.asarray(expected)
    require(a.shape == b.shape, f"{message}: shapes {a.shape} e {b.shape}")
    np.testing.assert_allclose(a, b, rtol=1e-12, atol=1e-10,
                               equal_nan=equal_nan, err_msg=message)


def dates(values):
    result = pd.to_datetime(values, errors="raise")
    require(not result.isna().any(), "Timestamp NaT encontrado.")
    require(result.dt.tz is None, "Esperado o eixo temporal sem fuso do pacote.")
    return result


def metrics(y, prediction):
    residual = np.asarray(y, dtype=float) - np.asarray(prediction, dtype=float)
    return {"mae_mwmed": float(np.mean(np.abs(residual))),
            "rmse_mwmed": float(np.sqrt(np.mean(residual ** 2))),
            "bias_observed_minus_predicted_mwmed": float(np.mean(residual))}


def audit(allow_missing_model=False):
    result, protocol = read_json(RUN / "resultado.json"), read_json(RUN / "protocol.json")
    baseline_result = read_json(BASELINE / "resultado.json")
    require(result["schema"] == "renewcast-pretrained-result-v1" and result["completed"], "Resultado incompleto ou schema inválido.")
    require(protocol["schema"] == "renewcast-pretrained-protocol-v1", "Schema do protocolo inválido.")
    require(baseline_result["schema"] == "renewcast-gru-result-v1" and baseline_result["completed"], "Baseline inválido.")
    require(result["baseline_run_id"] == protocol["baseline_run_id"] == BASELINE.name, "Baseline diferente do caminho fixado.")
    require(result["run_id"] == RUN.name, "Run ID divergente.")
    latest = read_json(RUN.parent / "latest_run.json")
    require(latest["run_id"] == RUN.name and latest["resultado_sha256"] == digest(RUN / "resultado.json"), "Ponteiro latest inválido.")

    checked_hashes = {}
    for name, expected in result["output_sha256"].items():
        actual = digest(RUN / name)
        require(actual == expected, f"Hash de saída divergente: {name}")
        checked_hashes[f"run/{name}"] = actual
    for name, expected in protocol["baseline_hashes"].items():
        actual = digest(BASELINE / name)
        require(actual == expected, f"Hash do baseline divergente: {name}")
        if name != "resultado.json":
            require(actual == baseline_result["output_sha256"][name], f"Hash fora do resultado M08.3: {name}")
        checked_hashes[f"baseline/{name}"] = actual
    require(result["input_sha256"] == protocol["input_sha256"] == baseline_result["input_sha256"], "Entradas distintas entre os experimentos.")
    for name, expected in result["input_sha256"].items():
        actual = digest(INPUT / name)
        require(actual == expected, f"Hash de entrada divergente: {name}")
        checked_hashes[f"input/{name}"] = actual
    manifest = read_json(INPUT / "manifesto_entrada.json")
    for name, expected in manifest["files"].items():
        require((INPUT / name).stat().st_size == expected["bytes"] and digest(INPUT / name) == expected["sha256"], f"Entrada fora do manifesto: {name}")
    require(manifest["package_id"] == protocol["source_package_id"], "Identidade do pacote divergente.")
    codes = {"laboratorio_pre_treinado.py": ROOT / "notebooks/laboratorio_pre_treinado.py",
             "m09_pre_treinado_core.py": ROOT / "notebooks/m09_pre_treinado_core.py",
             "executar_m09_3.py": ROOT / "scripts/executar_m09_3.py",
             "m08_3_base.py": ROOT / "notebooks/m08_3_base.py"}
    require(set(codes) == set(protocol["code_sha256"]), "Lista de códigos divergente.")
    for name, path in codes.items():
        require(digest(path) == protocol["code_sha256"][name], f"Código alterado: {name}")
    require(digest(ROOT / "notebooks/m09_alinhamento_autoral.py") == protocol["authorship_sha256"], "Hash da função autoral divergente.")
    for name, field in (("model_source_m09_3.json", "model_spec_sha256"), ("requirements_m09_3.lock.txt", "requirements_sha256")):
        require(digest(ROOT / "docs" / name) == protocol[field], f"Documento de protocolo alterado: {name}")
    spec = read_json(ROOT / "docs/model_source_m09_3.json")
    require(spec == protocol["model"], "Especificação do snapshot diferente.")
    require(result["model_repo"] == spec["repo_id"] and result["model_revision"] == spec["revision"], "Identidade do modelo divergente.")
    snapshot = ROOT / "models/pretrained/chronos-bolt-tiny" / spec["revision"]
    model_files, missing_model = {}, []
    for name, expected in spec["files"].items():
        require(result["model_file_sha256"][name] == expected["sha256"], f"SHA esperado do modelo divergente: {name}")
        path = snapshot / name
        entry = {"expected_sha256": expected["sha256"], "expected_bytes": expected["bytes"]}
        if not path.is_file():
            missing_model.append(name)
            entry["status"] = "missing"
            require(allow_missing_model, f"Modelo ausente: {path}; SHA esperado {expected['sha256']}. Use --allow-missing-model somente para auditar dados sem verificar pesos.")
        else:
            entry.update(status="verified", actual_sha256=digest(path), actual_bytes=path.stat().st_size)
            require(entry["actual_sha256"] == expected["sha256"] and entry["actual_bytes"] == expected["bytes"], f"Snapshot alterado: {name}")
        model_files[name] = entry

    conference = read_json(RUN / "conferencia.json")
    require(conference == result["checks"] and conference["passed"], "Conferência ausente ou inconsistente.")
    for field in ("models_trained", "weights_finetuned", "future_targets_used_as_inputs", "operational_approval"):
        require(result[field] is False, f"Flag de escopo inesperada: {field}")
    require(result["optimizer_steps"] == 0 and result["frozen_parameters"], "Protocolo exige pesos congelados e zero atualizações.")

    aligned = pd.read_csv(RUN / "alinhamento_alvos.csv")
    require(len(aligned) == 168, "Esperadas 168 origens alinhadas.")
    for name in ("forecast_origin", "history_end", "target_time", "target_available_at"):
        aligned[name] = dates(aligned[name])
    origins = aligned.forecast_origin
    require(not origins.duplicated().any() and origins.is_monotonic_increasing, "Origens duplicadas ou fora de ordem.")
    require(origins.diff().dropna().eq(pd.Timedelta(hours=1)).all(), "Origens não horárias.")
    require(aligned.history_end.eq(origins - pd.Timedelta(hours=2)).all(), "Fim do histórico incompatível com atraso.")
    require(aligned.target_time.eq(origins + pd.Timedelta(hours=24)).all(), "Alvo não é h24.")
    require(aligned.target_available_at.eq(aligned.target_time + pd.Timedelta(hours=2)).all(), "Disponibilidade do alvo divergente.")
    lead = np.array([(target.value - end.value) // HOUR_NS for end, target in zip(aligned.history_end, aligned.target_time)], dtype=np.int64)
    require(all((target.value - end.value) > 0 and (target.value - end.value) % HOUR_NS == 0 for end, target in zip(aligned.history_end, aligned.target_time)), "Diferença temporal inválida.")
    index = lead - 1
    with np.load(RUN / "quantis_26_passos.npz", allow_pickle=False) as arrays:
        require(set(arrays.files) == {"forecast", "quantile_levels"}, "Conteúdo NPZ inesperado.")
        forecast, levels = arrays["forecast"].copy(), arrays["quantile_levels"].copy()
    require(forecast.shape == (168, 9, 26) and levels.shape == (9,), "Shapes da trajetória inválidos.")
    require(np.isfinite(forecast).all() and np.isfinite(levels).all(), "NPZ não finito.")
    require(np.all(np.diff(levels) > 0) and np.all((levels > 0) & (levels < 1)), "Níveis inválidos.")
    require(np.all(lead == 26) and np.all(index == 25) and np.all(index < forecast.shape[2]), "Alinhamento esperado é passo 26, índice 25.")
    same(aligned.lead_hours, lead, "Lead salvo")
    same(aligned.index_zero_based, index, "Índice salvo")
    selected = {}
    for name, tau in (("p10", .1), ("p50", .5), ("p90", .9)):
        matches = np.flatnonzero(np.abs(levels - tau) <= 1e-12)
        require(len(matches) == 1, f"Quantil {tau} ausente ou ambíguo.")
        selected[name] = np.array([forecast[b, int(matches[0]), int(index[b])] for b in range(168)], dtype=np.float64)
        same(aligned[name], selected[name], f"Seleção independente de {name}")
    same(aligned.prediction, selected["p50"], "Mediana como previsão")
    raw = pd.read_parquet(INPUT / "geracao.parquet")
    raw["din_instante"] = dates(raw.din_instante)
    require(not raw.din_instante.duplicated().any(), "Geração com instantes duplicados.")
    actual = raw.set_index("din_instante").val_geracao.reindex(pd.DatetimeIndex(aligned.target_time)).to_numpy()
    same(aligned.target_generation, actual, "Alvos contra geração fonte")

    paths = pd.read_csv(RUN / "trajetorias_26_passos.csv")
    require(len(paths) == 168 * 26 and paths.selected_target.dtype == bool, "Trajetórias incompletas ou seleção sem tipo booleano.")
    for name in ("forecast_origin", "history_end", "forecast_time"):
        paths[name] = dates(paths[name])
    require(np.array_equal(paths.forecast_origin.to_numpy(), np.repeat(origins.to_numpy(), 26)), "Ordem das trajetórias diverge do batch NPZ.")
    for b in range(168):
        part = paths.iloc[b * 26:(b + 1) * 26]
        require(np.array_equal(part.lead_hours.to_numpy(), np.arange(1, 27)), "Trajetória sem os 26 passos.")
        require(part.history_end.eq(aligned.history_end.iloc[b]).all(), "Fim do histórico na trajetória divergente.")
        require(part.forecast_time.eq(part.history_end + pd.to_timedelta(part.lead_hours, unit="h")).all(), "Tempo de passo incorreto.")
        require(np.array_equal(part.selected_target.to_numpy(), np.arange(1, 27) == lead[b]), "Passo selecionado errado na trajetória.")
        for q, level in enumerate(levels):
            same(part[f"p{int(round(level * 100)):02}"], forecast[b, q], "Valores da trajetória contra NPZ")

    predictions = pd.read_csv(RUN / "predictions.csv")
    baseline = pd.read_csv(BASELINE / "predictions.csv")
    summary = pd.read_csv(RUN / "summary.csv")
    require(len(predictions) == 1680 and len(summary) == 10, "Esperadas dez variantes de 168 origens.")
    for name in ("forecast_origin", "history_end", "target_time", "target_available_at", "history_start"):
        if name in predictions: predictions[name] = pd.to_datetime(predictions[name], errors="raise")
        if name in baseline: baseline[name] = pd.to_datetime(baseline[name], errors="raise")
    old = predictions.loc[~predictions.method.eq(METHOD), baseline.columns].reset_index(drop=True)
    require(len(old) == len(baseline) == 1512, "Baseline perdeu linhas.")
    for name in baseline:
        if pd.api.types.is_numeric_dtype(baseline[name]):
            same(old[name], baseline[name], f"Baseline preservado: {name}", equal_nan=True)
        else:
            require(old[name].equals(baseline[name]), f"Baseline alterado: {name}")
    recalculated, variants = [], set()
    for row in summary.to_dict("records"):
        seed = None if pd.isna(row["seed"]) else int(row["seed"])
        key = (row["method"], seed)
        require(key not in variants, "Variante duplicada no resumo.")
        variants.add(key)
        mask = predictions.method.eq(row["method"])
        mask &= predictions.seed.isna() if seed is None else predictions.seed.eq(seed)
        group = predictions.loc[mask].sort_values("forecast_origin")
        require(len(group) == 168 and row["rows"] == 168, f"Quantidade inválida: {key}")
        require(np.array_equal(group.forecast_origin.to_numpy(), origins.to_numpy()), f"Origens não pareadas: {key}")
        same(group.target_generation, actual, f"Alvos pareados: {key}")
        m = metrics(actual, group.prediction)
        for name, value in m.items(): same(value, row[name], f"Métrica {name}: {key}")
        recalculated.append(dict(method=key[0], seed=seed, rows=168, **m))
    expected_variants = {(r.method, None if pd.isna(r.seed) else int(r.seed)) for r in baseline[["method", "seed"]].drop_duplicates().itertuples()}
    require(variants == expected_variants | {(METHOD, None)} and len(expected_variants) == 9, "Conjunto de variantes divergente.")
    own = predictions.loc[predictions.method.eq(METHOD)].sort_values("forecast_origin")
    for name in ("prediction", "p10", "p50", "p90", "lead_hours", "index_zero_based"):
        same(own[name], aligned[name], f"Previsão combinada: {name}")
    point = metrics(actual, selected["p50"])
    for name, value in point.items(): same(value, result["forecast_metric"][name], f"Métrica no resultado: {name}")
    hgb = next(m for m in recalculated if m["method"] == "hgb_24h")
    persistence = next(m for m in recalculated if m["method"] == "persistence_d2")
    for row in summary.to_dict("records"):
        same(row["mae_gain_vs_hgb_pct"], 100 * (hgb["mae_mwmed"] - row["mae_mwmed"]) / hgb["mae_mwmed"], "Ganho percentual contra HGB")
        same(row["mae_gain_vs_persistence_pct"], 100 * (persistence["mae_mwmed"] - row["mae_mwmed"]) / persistence["mae_mwmed"], "Ganho percentual contra persistência")

    lower, median, upper = selected["p10"], selected["p50"], selected["p90"]
    width = upper - lower
    interval = {}
    for tau, predicted in ((.1, lower), (.5, median), (.9, upper)):
        residual = actual - predicted
        interval[f"pinball_p{int(tau * 100)}"] = float(np.mean(np.where(residual >= 0, tau * residual, (tau - 1) * residual)))
    below, above = actual < lower, actual > upper
    interval.update(coverage_80=float(np.mean((actual >= lower) & (actual <= upper))),
        below_p10=float(below.mean()), above_p90=float(above.mean()), mean_width_mwmed=float(width.mean()),
        interval_score_80=float(np.mean(width + (2 / .2) * (lower - actual) * below + (2 / .2) * (actual - upper) * above)),
        crossing_rows=int(np.count_nonzero((lower > median) | (median > upper))), negative_p50_rows=int(np.count_nonzero(median < 0)))
    saved_interval = read_json(RUN / "quantile_metrics.json")
    for name, value in interval.items():
        same(value, saved_interval[name], f"Quantis: {name}")
        same(value, result["interval_metrics"][name], f"Quantis no resultado: {name}")
    require(saved_interval["clipped"] is False and saved_interval["recalibrated"] is False, "Transformação de quantis não prevista.")
    hgb_rows = baseline.loc[baseline.method.eq("hgb_24h")].sort_values("forecast_origin")
    gains = np.abs(actual - hgb_rows.prediction.to_numpy()) - np.abs(actual - median)
    paired = pd.read_csv(RUN / "comparacao_pareada.csv")
    require(np.array_equal(dates(paired.forecast_origin).to_numpy(), origins.to_numpy()), "Comparação pareada em outra ordem.")
    same(paired.hgb_prediction, hgb_rows.prediction, "HGB na comparação pareada")
    same(paired.prediction, median, "Mediana na comparação pareada")
    same(paired.mae_gain_hgb_minus_chronos, gains, "Ganhos por origem")
    same(float(gains.mean()), result["paired_mae_gain_vs_hgb"], "Ganho médio pareado")
    wins = int(np.count_nonzero(gains > 0))
    require(wins == result["origins_abs_error_better_than_hgb"], "Vitórias por origem divergentes.")
    batches = pd.read_csv(RUN / "latencias_lotes.csv")
    require(len(batches) == 11 and batches.start.tolist() == list(range(0, 168, 16)), "Lotes incompletos ou reordenados.")
    require(batches.rows.tolist() == [16] * 10 + [8], "Tamanhos dos lotes divergentes.")
    require(np.isfinite(batches.seconds).all() and (batches.seconds > 0).all(), "Latências inválidas.")
    inference_seconds = math.fsum(batches.seconds.tolist())
    same(inference_seconds, result["inference_seconds"], "Soma das latências")

    return {"schema": "renewcast-m09-3-independent-audit-v1", "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "verified": not missing_model, "data_checks_passed": True,
        "run_directory": RUN.relative_to(ROOT).as_posix(), "baseline_directory": BASELINE.relative_to(ROOT).as_posix(),
        "audit_method": "Persisted arrays and tables only; no model, controller or authored function imported; no inference or training.",
        "checks": {"output_latest_input_baseline_code_hashes": True, "model_files_verified": not missing_model,
            "schema_and_authorship_hash": True, "alignment_recomputed_from_npz_and_timestamps": True,
            "all_26_steps_and_nine_quantiles_verified": True, "nine_baseline_variants_preserved": True,
            "ten_variants_on_same_168_origins": True, "all_30_point_metrics_recomputed": True,
            "pinball_interval_tails_width_and_score_recomputed": True, "paired_comparison_recomputed": True,
            "eleven_batches_and_recorded_latency_sum_verified": True},
        "model_files": model_files, "missing_model_files": missing_model, "checked_hashes": checked_hashes,
        "source_and_authorship_sha256": {**protocol["code_sha256"], "m09_alinhamento_autoral.py": protocol["authorship_sha256"]},
        "alignment": {"forecast_shape": list(forecast.shape), "levels": levels.tolist(), "rows": 168,
            "lead_hours_unique": np.unique(lead).tolist(), "index_zero_based_unique": np.unique(index).tolist(),
            "first_history_end": aligned.history_end.iloc[0].isoformat(), "first_target_time": aligned.target_time.iloc[0].isoformat()},
        "point_metrics_recomputed": recalculated, "quantile_metrics_recomputed": interval,
        "interval_counts": {"inside": int(np.count_nonzero((actual >= lower) & (actual <= upper))), "below": int(below.sum()), "above": int(above.sum()), "total": 168},
        "paired": {"wins_vs_hgb": wins, "losses_vs_hgb": int(np.count_nonzero(gains < 0)), "ties_vs_hgb": int(np.count_nonzero(gains == 0)), "mean_hgb_minus_chronos_absolute_error": float(gains.mean())},
        "latencies": {"batches": 11, "rows": int(batches.rows.sum()), "sizes": batches.rows.tolist(), "sum_seconds": inference_seconds, "not_remeasured": True},
        "limits": "File consistency and recalculated metrics do not certify pretraining non-overlap, future calibration or operational approval."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-missing-model", action="store_true", help="Permite dados sem pesos locais, registrando verified=false e arquivos missing. Não faz download.")
    args = parser.parse_args()
    result = audit(args.allow_missing_model)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Auditoria concluída: verified={result['verified']}; 10 variantes, 168 origens, 26 passos.")
    print(f"Vitórias por origem contra HGB: {result['paired']['wins_vs_hgb']}/168.")
    print(f"JSON: {OUTPUT}")


if __name__ == "__main__":
    main()
