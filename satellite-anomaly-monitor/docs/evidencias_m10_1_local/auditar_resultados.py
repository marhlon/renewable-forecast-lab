"""Confere a grade salva por searchsorted, sem importar o sincronizador.

Execute na raiz do projeto: python satellite-anomaly-monitor/docs/evidencias_m10_1_local/auditar_resultados.py
Depende de NumPy, pandas e biblioteca padrão. Não executa detector ou download.
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
DATA = PROJECT / "data/reference/esa_mission1_2007"
DEFAULT_RUN = PROJECT / "reports/m10_1/20261118T203614Z_7e13daae"
OUTPUT = Path(__file__).with_name("auditoria_resultados.json")
CATEGORIES = {
    "Anomaly": "anomaly_annotation",
    "Rare Event": "rare_event_annotation",
    "Communication Gap": "communication_gap_annotation",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc(values):
    # pandas 2 e 3 podem inferir resoluções diferentes: os inteiros serão ns.
    return pd.to_datetime(values, utc=True, format="mixed").astype("datetime64[ns, UTC]")


def same_numbers(actual, expected, name):
    np.testing.assert_allclose(np.asarray(actual, dtype=float), np.asarray(expected, dtype=float),
                               rtol=1e-12, atol=1e-10, equal_nan=True, err_msg=name)


def same_times(actual, expected_ns, name):
    parsed = utc(actual)
    np.testing.assert_array_equal(parsed.array.asi8, expected_ns, err_msg=name)


def same_frame(actual, expected, name, temporal=()):
    require(actual.columns.tolist() == expected.columns.tolist(), f"Colunas divergentes: {name}")
    require(len(actual) == len(expected), f"Quantidade de linhas divergente: {name}")
    for column in expected:
        if column in temporal:
            same_times(actual[column], utc(expected[column]).array.asi8, f"{name}.{column}")
        elif pd.api.types.is_numeric_dtype(expected[column]):
            same_numbers(actual[column], expected[column], f"{name}.{column}")
        else:
            require(actual[column].reset_index(drop=True).equals(expected[column].reset_index(drop=True)),
                    f"Valores divergentes: {name}.{column}")


def audit(run):
    result = read_json(run / "resultado.json")
    source = read_json(DATA / "source.json")
    require(result["schema"] == "satmon-m10-1-contract-v1" and result["completed"] is True,
            "Resultado incompleto ou contrato desconhecido.")
    require(result["run_id"] == run.name, "Identidade da execução divergente.")
    require(result["source_doi"] == source["doi"], "Identidade da fonte divergente.")
    latest = read_json(run.parent / "latest_run.json")
    require(latest["run_id"] == run.name and latest["resultado_sha256"] == sha(run / "resultado.json"),
            "O ponteiro latest não corresponde a esta execução.")

    checked_hashes = {}

    def check_hash(path, expected):
        actual = sha(path)
        require(actual == expected, f"SHA-256 divergente: {path}")
        checked_hashes[path.relative_to(PROJECT).as_posix()] = actual

    check_hash(DATA / "source.json", result["source_spec_sha256"])
    require(source["schema"] == "satmon-esa-curated-source-v1", "Contrato da fonte desconhecido.")
    for name, entry in source["files"].items():
        require((DATA / name).stat().st_size == entry["bytes"], f"Tamanho divergente: {name}")
        check_hash(DATA / name, entry["sha256"])
    check_hash(PROJECT / "scripts/executar_m10_1.py", result["code_sha256"]["runner"])
    check_hash(PROJECT / "src/satmon/temporal.py", result["code_sha256"]["temporal.py"])
    check_hash(PROJECT / "notebooks/m10_sincronizacao_autoral.py", result["authorship_sha256"])
    for name, expected in result["output_sha256"].items():
        check_hash(run / name, expected)
    require(read_json(run / "conferencia.json") == result["checks"], "Conferência divergente.")
    require(result["checks"]["passed"] is True and result["checks"]["groups"] == 5,
            "As cinco conferências não estão aprovadas.")
    for field in ("future_sample_used", "labels_used_as_features", "models_trained", "operational_approval"):
        require(result[field] is False, f"Escopo inesperado: {field}")

    grid = pd.date_range("2007-01-01T00:00:00Z", "2008-01-01T00:00:00Z",
                         freq="90s", inclusive="left").astype("datetime64[ns, UTC]")
    grid_ns = grid.asi8
    require(len(grid) == result["grid_rows"] == 350400, "Dimensão da grade incorreta.")
    require(result["grid_step_seconds"] == 90 and result["max_age_seconds"] == 180,
            "Passo ou tolerância divergente.")
    features = pd.read_csv(run / "grade_features.csv.gz")
    expected_columns = ["timestamp"]
    for channel in source["channels"]:
        expected_columns += [f"{channel}_{suffix}" for suffix in ("value", "sample_time", "age_seconds", "usable")]
    expected_columns += ["all_channels_usable"]
    require(features.columns.tolist() == expected_columns, "Features perderam colunas ou incluem rótulos.")
    require(len(features) == len(grid), "Quantidade de linhas da grade divergente.")
    same_times(features.timestamp, grid_ns, "Grade completa")

    profiles, reuse, masks, channel_clocks = [], [], {}, []
    for channel in source["channels"]:
        raw = pd.read_csv(DATA / f"{channel}.csv.gz")
        raw["timestamp"] = utc(raw.timestamp)
        require(not raw.timestamp.isna().any() and not raw.timestamp.duplicated().any(),
                f"Instantes inválidos ou duplicados: {channel}")
        raw = raw.sort_values("timestamp").reset_index(drop=True)
        times = raw.timestamp.array.asi8
        values = raw.value.to_numpy(dtype=float)
        require(not np.isinf(values).any(), f"Medição infinita: {channel}")
        channel_clocks.append(times)
        delta = np.diff(times) / 1e9
        # side=right inclui a igualdade; -1 retorna o último instante <= grade.
        positions = np.searchsorted(times, grid_ns, side="right") - 1
        has_sample = positions >= 0
        safe_positions = positions.clip(min=0)
        selected = values[safe_positions]
        sample_ns = np.full(len(grid), pd.NaT.value, dtype=np.int64)
        sample_ns[has_sample] = times[positions[has_sample]]
        ages = np.full(len(grid), np.nan, dtype=float)
        ages[has_sample] = (grid_ns[has_sample] - sample_ns[has_sample]) / 1e9
        usable = has_sample & (ages >= 0) & (ages <= 180) & ~np.isnan(selected)
        expected_values = np.where(usable, selected, np.nan)
        same_times(features[f"{channel}_sample_time"], sample_ns, f"Última amostra: {channel}")
        same_numbers(features[f"{channel}_age_seconds"], ages, f"Idades: {channel}")
        same_numbers(features[f"{channel}_value"], expected_values, f"Valores: {channel}")
        require(pd.api.types.is_bool_dtype(features[f"{channel}_usable"]), f"usable não booleano: {channel}")
        np.testing.assert_array_equal(features[f"{channel}_usable"], usable,
                                      err_msg=f"Máscara utilizável: {channel}")
        require(np.all(sample_ns[has_sample] <= grid_ns[has_sample]), f"Amostra futura: {channel}")
        masks[channel] = usable
        profiles.append({"channel": channel, "raw_rows": len(raw), "null_values": int(np.isnan(values).sum()),
            "median_spacing_seconds": float(np.median(delta)), "p99_spacing_seconds": float(np.quantile(delta, .99)),
            "largest_spacing_seconds": float(delta.max()), "spacing_over_180s": int((delta > 180).sum()),
            "usable_grid_rows": int(usable.sum()), "unusable_grid_rows": int((~usable).sum()),
            "usable_fraction": float(usable.mean())})
        unique, counts = np.unique(positions[usable], return_counts=True)
        repeated = unique[counts > 1]
        examples = []
        for position in repeated[:2]:
            use = np.flatnonzero(usable & (positions == position))
            examples.append({"sample_time": raw.timestamp.iloc[position].isoformat(),
                "value": float(values[position]), "grid_times": [grid[i].isoformat() for i in use],
                "age_seconds": ages[use].tolist()})
        reuse.append({"channel": channel, "raw_rows": len(raw), "usable_grid_rows": int(usable.sum()),
            "distinct_raw_samples_used": len(unique), "raw_samples_not_used": len(raw) - len(unique),
            "samples_used_more_than_once": int((counts > 1).sum()), "additional_grid_uses": int((counts - 1).sum()),
            "max_grid_uses_per_sample": int(counts.max()), "no_previous_sample_grid_rows": int((~has_sample).sum()),
            "expired_grid_rows": int((has_sample & (ages > 180)).sum()),
            "missing_latest_value_grid_rows": int((has_sample & np.isnan(selected)).sum()),
            "examples": examples})
    profile = pd.DataFrame(profiles)
    same_frame(pd.read_csv(run / "perfil_canais.csv"), profile, "Perfil dos canais")
    all_usable = np.logical_and.reduce(list(masks.values()))
    np.testing.assert_array_equal(features.all_channels_usable, all_usable)
    require(int(all_usable.sum()) == result["all_channels_usable"], "Usabilidade conjunta divergente.")
    require(int(profile.raw_rows.sum()) == result["raw_rows_total"], "Quantidade bruta divergente.")

    labels = pd.read_csv(DATA / "labels.csv")
    types = pd.read_csv(DATA / "anomaly_types.csv")
    events = labels[labels.Channel.isin(source["channels"])].merge(types, on="ID", how="left", validate="many_to_one")
    events["StartTime"], events["EndTime"] = utc(events.StartTime), utc(events.EndTime)
    events = events[(events.StartTime < pd.Timestamp("2008-01-01T00:00:00Z")) &
                    (events.EndTime >= pd.Timestamp("2007-01-01T00:00:00Z"))].copy()
    require(events.Category.isin(CATEGORIES).all() and events.StartTime.le(events.EndTime).all(), "Eventos incompatíveis.")
    same_frame(pd.read_csv(run / "eventos_fonte.csv"), events.reset_index(drop=True), "Eventos fonte",
               temporal=("StartTime", "EndTime"))
    annotations = {column: np.zeros(len(grid), dtype=bool) for column in CATEGORIES.values()}
    coverages = []
    for event in events.itertuples(index=False):
        selected = (grid >= event.StartTime) & (grid <= event.EndTime)
        annotations[CATEGORIES[event.Category]] |= selected
        coverages.append({"ID": event.ID, "Channel": event.Channel, "StartTime": event.StartTime,
            "EndTime": event.EndTime, "Category": event.Category,
            "grid_rows_in_interval": int(selected.sum()),
            "usable_grid_rows_in_interval": int((selected & masks[event.Channel]).sum())})
    annotations["unannotated"] = ~np.logical_or.reduce(list(annotations.values()))
    saved_annotations = pd.read_csv(run / "rotulos_grade.csv.gz")
    require(saved_annotations.columns.tolist() == ["timestamp", *annotations], "Colunas de rótulos divergentes.")
    same_times(saved_annotations.timestamp, grid_ns, "Instantes de anotação")
    for name, expected in annotations.items():
        require(pd.api.types.is_bool_dtype(saved_annotations[name]), f"Rótulo não booleano: {name}")
        np.testing.assert_array_equal(saved_annotations[name], expected, err_msg=name)
    same_frame(pd.read_csv(run / "cobertura_eventos.csv"), pd.DataFrame(coverages), "Cobertura dos eventos",
               temporal=("StartTime", "EndTime"))
    categories = []
    for name, column in CATEGORIES.items():
        group = events[events.Category.eq(name)]
        categories.append({"category": name, "source_annotation_rows": len(group),
            "distinct_annotation_ids": int(group.ID.nunique()), "grid_rows_with_annotation": int(annotations[column].sum())})
    same_frame(pd.read_csv(run / "categorias.csv"), pd.DataFrame(categories), "Categorias")
    require(categories == result["category_summary"], "Resumo das categorias divergente.")
    require(len(events) == result["event_annotation_rows"] and int(events.ID.nunique()) == result["event_ids"],
            "Contagem de anotações ou IDs divergente.")

    mini = pd.read_csv(run / "contraprova_sintetica.csv")
    same_numbers(mini.c_value, [0, np.nan, 10], "Valores da contraprova")
    same_numbers(mini.c_age_seconds, [2, 7, 2], "Idades da contraprova")
    require(mini.c_usable.tolist() == [True, False, True], "Usabilidade da contraprova divergente.")

    return {"schema": "satmon-m10-1-independent-audit-v1", "verified": True,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(), "run_id": run.name,
        "run_directory": run.relative_to(PROJECT).as_posix(),
        "method": "NumPy searchsorted on persisted raw timestamps; no merge_asof, synchronizer, reference or runner imported.",
        "audit_versions": {"numpy": np.__version__, "pandas": pd.__version__},
        "checks": {"all_input_output_source_code_author_hashes": True, "latest_result_identity": True,
            "all_grid_rows_compared_independently": True, "sample_time_age_value_usable": True,
            "no_future_samples_and_maximum_age": True, "expired_sample_evidence_preserved": True,
            "profile_recomputed": True, "source_events_and_closed_interval_annotations_recomputed": True,
            "labels_separate_from_features": True, "categories_ids_and_event_coverage_recomputed": True},
        "checked_hashes": checked_hashes, "grid_rows": len(grid), "raw_rows_total": int(profile.raw_rows.sum()),
        "profiles_recomputed": profiles, "sample_reuse": reuse,
        "real_channel_clocks_coincide": all(np.array_equal(channel_clocks[0], x) for x in channel_clocks[1:]),
        "all_channels_usable": int(all_usable.sum()), "event_annotation_rows": len(events),
        "distinct_event_ids": int(events.ID.nunique()), "category_summary_recomputed": categories,
        "event_intervals_with_no_grid_point": sum(row["grid_rows_in_interval"] == 0 for row in coverages),
        "source_checksum_limits": {"derived_local_files_sha256_verified_now": True,
            "whole_archive_checksum_verified_by_this_audit": False,
            "whole_archive_checksum_verified_declared_by_source": source["whole_archive_checksum_verified"],
            "individual_zip_members_crc32_verified_declared_by_source": source["individual_zip_members_crc32_verified"]},
        "limits": "Consistency of this exploratory UTC grid does not establish physical units, actual arrival latency, annotation completeness, detector performance or operational approval."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    args = parser.parse_args()
    result = audit(args.run_dir.resolve())
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Auditoria aprovada: {result['grid_rows']} instantes, três canais e anotações conferidos.")
    print(f"Run: {result['run_id']}; JSON: {OUTPUT}")


if __name__ == "__main__":
    main()
