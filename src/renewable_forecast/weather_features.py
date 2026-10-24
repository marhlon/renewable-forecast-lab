"""M04.4: vento por conjunto, ponderado pela capacidade instalada.

Destino: src/renewable_forecast/weather_features.py.
Entrada: pasta produzida por weather_asof; saída: uma linha por emissão.
As features só são calculadas com cobertura completa do conjunto.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from renewable_forecast.weather_asof import utc_timestamp


GROUP_COLUMNS = [
    "forecast_origin", "target_time", "id_ons_conjunto", "weather_model",
]
WEATHER_FEATURE_COLUMNS = [
    "wind_speed_mean_ms", "wind_speed_spatial_std_ms",
    "wind_u_mean_ms", "wind_v_mean_ms", "wind_speed_cubed_mean_m3s3",
]


def weighted_wind_features(plants: pd.DataFrame) -> dict[str, float]:
    """Núcleo numérico; recebe somente uma emissão com cobertura completa.

    u positivo aponta para leste; v positivo aponta para norte.
    A direção meteorológica indica DE ONDE o vento vem.
    O desvio é espacial e populacional. O termo cúbico não é potência em MW.
    """
    weights = plants["capacity_weight"].to_numpy(dtype=float)
    speed = plants["wind_speed_100m_ms"].to_numpy(dtype=float)
    radians = np.deg2rad(plants["wind_direction_100m_deg"].to_numpy(dtype=float))

    u = -speed * np.sin(radians)
    v = -speed * np.cos(radians)
    mean_speed = np.average(speed, weights=weights)
    spatial_variance = np.average((speed - mean_speed) ** 2, weights=weights)

    return {
        "wind_speed_mean_ms": float(mean_speed),
        "wind_speed_spatial_std_ms": float(np.sqrt(spatial_variance)),
        "wind_u_mean_ms": float(np.average(u, weights=weights)),
        "wind_v_mean_ms": float(np.average(v, weights=weights)),
        "wind_speed_cubed_mean_m3s3": float(np.average(speed ** 3, weights=weights)),
    }


def build_weather_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Agrega decisões do seletor, preservando linhas sem cobertura completa.

    Os pesos cadastrais devem ser constantes neste recorte. Linhas ausentes
    de uma usina em alguma emissão contam como falta de cobertura.
    """
    times = ["weather_valid_time", "weather_run_time", "weather_available_at"]
    numeric = ["wind_speed_100m_ms", "wind_direction_100m_deg", "grid_latitude", "grid_longitude"]
    required = {*GROUP_COLUMNS, "id_ons_usina", "capacity_weight", "weather_selected", *times, *numeric}
    missing = required - set(frame.columns)
    if frame.empty or missing:
        raise ValueError(f"Tabela de seleção vazia ou colunas ausentes: {sorted(missing)}")
    data = frame.copy()
    if data[[*GROUP_COLUMNS, "id_ons_usina", "capacity_weight"]].isna().any().any():
        raise ValueError("Chaves e pesos devem estar preenchidos.")
    if not pd.api.types.is_bool_dtype(data["weather_selected"]) or data["weather_selected"].isna().any():
        raise ValueError("weather_selected deve ser booleano e estar preenchido.")
    for column in ["forecast_origin", "target_time", *times]:
        data[column] = pd.Series(
            [pd.NaT if pd.isna(x) else utc_timestamp(x) for x in data[column]],
            index=data.index, dtype="datetime64[ns, UTC]",
        )
    if data.duplicated([*GROUP_COLUMNS, "id_ons_usina"]).any():
        raise ValueError("Usina duplicada na mesma emissão, alvo, conjunto e modelo.")
    if not data["target_time"].gt(data["forecast_origin"]).all():
        raise ValueError("O alvo deve ser posterior à emissão.")
    data["capacity_weight"] = pd.to_numeric(data["capacity_weight"], errors="raise")
    if not np.isfinite(data["capacity_weight"]).all() or not data["capacity_weight"].gt(0).all():
        raise ValueError("Os pesos devem ser finitos e positivos.")

    entities = ["id_ons_conjunto", "weather_model", "id_ons_usina"]
    if data.groupby(entities)["capacity_weight"].nunique().gt(1).any():
        raise ValueError("O peso de uma usina mudou dentro do recorte.")
    roster = data[[*entities, "capacity_weight"]].drop_duplicates()
    expected = roster.groupby(entities[:2]).agg(
        plants=("id_ons_usina", "size"), weight=("capacity_weight", "sum"),
    )
    if not np.allclose(expected["weight"], 1.0, rtol=0, atol=1e-8):
        raise ValueError("Os pesos cadastrais de cada conjunto/modelo devem somar 1.")

    mask = data["weather_selected"]
    for column in numeric:
        data[column] = pd.to_numeric(data[column], errors="raise")
    known = data.loc[mask]
    if known[times].isna().any().any() or not np.isfinite(known[numeric].to_numpy(dtype=float)).all():
        raise ValueError("Uma previsão selecionada contém dados ausentes ou não finitos.")
    if known["wind_speed_100m_ms"].lt(0).any() or not known["wind_direction_100m_deg"].between(0, 360).all():
        raise ValueError("Velocidade negativa ou direção fora de 0–360 graus.")
    if not known["weather_valid_time"].eq(known["target_time"]).all():
        raise ValueError("A validade meteorológica difere do alvo.")
    if (known["weather_available_at"] > known["forecast_origin"]).any():
        raise ValueError("Foi selecionada uma previsão ainda indisponível na emissão.")
    if (known["weather_run_time"] > known["weather_available_at"]).any():
        raise ValueError("Disponibilidade anterior à inicialização da rodada.")

    rows = []
    for key, decisions in data.groupby(GROUP_COLUMNS, sort=True):
        plants = decisions.loc[decisions["weather_selected"]]
        expected_plants = int(expected.loc[(key[2], key[3]), "plants"])
        weight_coverage = float(plants["capacity_weight"].sum())
        complete = len(plants) == expected_plants and np.isclose(weight_coverage, 1.0, rtol=0, atol=1e-8)
        row = dict(zip(GROUP_COLUMNS, key))
        row.update({
            "expected_plants": expected_plants,
            "matched_plants": len(plants),
            "capacity_coverage": weight_coverage,
            "grid_points": len(plants[["grid_latitude", "grid_longitude"]].drop_duplicates()),
            "weather_complete": bool(complete),
            "weather_status": "complete" if complete else ("missing" if plants.empty else "partial"),
            "selected_run_min": plants["weather_run_time"].min(),
            "selected_run_max": plants["weather_run_time"].max(),
            "weather_latest_available_at": plants["weather_available_at"].max(),
        })
        row.update({name: np.nan for name in WEATHER_FEATURE_COLUMNS})
        if complete:
            row.update(weighted_wind_features(plants))
        rows.append(row)
    return pd.DataFrame(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.input_dir.resolve() == args.output_dir.resolve():
        raise ValueError("Use uma pasta de saída diferente da pasta da seleção.")

    csv_path = args.input_dir / "weather_asof.csv"
    meta_path = args.input_dir / "metadata.json"
    source_meta = json.loads(meta_path.read_text(encoding="utf-8"))
    source_hash = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    if source_hash != source_meta["output_sha256"]:
        raise ValueError("O CSV difere do hash registrado pelo seletor meteorológico.")
    result = build_weather_features(pd.read_csv(csv_path))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "weather_features.csv"
    result.to_csv(output_path, index=False)
    metadata = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_csv_sha256": source_hash,
        "input_metadata_sha256": hashlib.sha256(meta_path.read_bytes()).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "source_selection": source_meta,
        "feature_columns": WEATHER_FEATURE_COLUMNS,
        "wind_height_m": 100,
        "weighting": "installed_capacity; fixed registry for this sample",
        "coverage_policy": "all plants and capacity weight sum 1; otherwise NaN features",
        "spatial_std": "weighted population standard deviation across locations",
        "wind_speed_cubed_mean_m3s3": "weighted mean of local speed cubed; not electrical power",
        "rows": len(result),
        "complete_rows": int(result["weather_complete"].sum()),
    }
    (args.output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Emissões: {len(result)}; completas: {metadata['complete_rows']}")
    display = result[["forecast_origin", "target_time", "capacity_coverage", "grid_points", "weather_status", *WEATHER_FEATURE_COLUMNS]].copy()
    display[WEATHER_FEATURE_COLUMNS] = display[WEATHER_FEATURE_COLUMNS].round(4)
    print(display.to_string(index=False))
    print("Features meteorológicas em UTC; disponibilidade histórica permanece conforme a hipótese da coleta.")
    print(f"CSV salvo: {output_path.resolve()}")


if __name__ == "__main__":
    main()
