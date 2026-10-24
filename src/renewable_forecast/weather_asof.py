"""M04.3: selecionar a rodada meteorológica elegível em cada emissão.

Destino: src/renewable_forecast/weather_asof.py.
Lê coletas locais; preserva emissões sem previsão e não treina modelos.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ENTITY = ["id_ons_usina", "weather_model"]
WEATHER_KEY = [*ENTITY, "weather_run_time", "weather_valid_time"]
DECISION_KEY = ["forecast_origin", "target_time", *ENTITY]
TIMES = ["weather_run_time", "weather_valid_time", "weather_available_at", "weather_fetched_at"]
STATIC = ["id_ons_conjunto", "nom_usina", "capacity_weight"]


def utc_timestamp(value) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    if pd.isna(stamp) or stamp.tzinfo is None:
        raise ValueError("Use timestamps com fuso explícito, por exemplo 2026-09-01T06:00:00Z.")
    return stamp.tz_convert("UTC")


def validate_weather(frame: pd.DataFrame) -> pd.DataFrame:
    required = {*WEATHER_KEY, *TIMES, *STATIC, "wind_speed_100m_ms", "wind_direction_100m_deg", "availability_is_assumed"}
    missing = required - set(frame.columns)
    if frame.empty or missing:
        raise ValueError(f"Meteorologia vazia ou incompleta: {sorted(missing)}")
    data = frame.copy()
    if data[list(required)].isna().any().any():
        raise ValueError("Há dados obrigatórios ausentes nas rodadas.")
    for column in TIMES:
        data[column] = pd.Series(
            [utc_timestamp(x) for x in data[column]],
            index=data.index, dtype="datetime64[ns, UTC]",
        )
    if data.duplicated(WEATHER_KEY).any():
        raise ValueError("Há duas linhas para a mesma usina, modelo, rodada e validade.")
    if (data.weather_available_at < data.weather_run_time).any():
        raise ValueError("Disponibilidade anterior à inicialização da rodada.")
    if (data.weather_valid_time < data.weather_run_time).any():
        raise ValueError("Validade anterior à inicialização da rodada.")
    for column in ("capacity_weight", "wind_speed_100m_ms", "wind_direction_100m_deg"):
        data[column] = pd.to_numeric(data[column], errors="raise")
        if not np.isfinite(data[column]).all():
            raise ValueError(f"Valor não finito em {column}.")
    if (data.capacity_weight <= 0).any() or (data.wind_speed_100m_ms < 0).any():
        raise ValueError("Peso deve ser positivo e velocidade não negativa.")
    if not data.wind_direction_100m_deg.between(0, 360).all():
        raise ValueError("Direção fora de 0–360 graus.")
    flag = data.availability_is_assumed.astype(str).str.lower().map({"true": True, "false": False})
    if flag.isna().any():
        raise ValueError("availability_is_assumed deve ser True ou False.")
    data["availability_is_assumed"] = flag.astype("boolean")
    return data


def load_weather_runs(run_dirs) -> tuple[pd.DataFrame, list[dict]]:
    """Carrega as tabelas produzidas por weather_runs e registra suas origens."""
    frames, sources, registry_hashes = [], [], set()
    for directory in map(Path, run_dirs):
        csv_path = directory / "weather_forecasts.csv"
        raw_path = directory / "response.json"
        meta_path = directory / "metadata.json"
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        protocol = metadata["protocol"]
        raw_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        if raw_hash != metadata["response_sha256"]:
            raise ValueError(f"Resposta original alterada: {directory}")
        frame = validate_weather(pd.read_csv(csv_path))
        run = utc_timestamp(protocol["run_time_utc"])
        if not frame.weather_run_time.eq(run).all() or not frame.weather_model.eq(protocol["weather_model"]).all():
            raise ValueError(f"Rodada/modelo diferem dos metadados: {directory}")
        if set(frame.id_ons_usina) != set(protocol["request_plant_ids"]):
            raise ValueError(f"Usinas diferem do pedido registrado: {directory}")
        expected_available = run + pd.Timedelta(hours=protocol["assumed_latency_hours"])
        if protocol["availability_is_assumed"] is not True or not frame.availability_is_assumed.all():
            raise ValueError("Este leitor recebe as coletas com latência assumida de weather_runs.")
        if not frame.weather_available_at.eq(expected_available).all():
            raise ValueError(f"Disponibilidade difere da hipótese registrada: {directory}")
        expected_times = pd.date_range(run, periods=protocol["hours"], freq="h")
        for _, plant_rows in frame.groupby("id_ons_usina"):
            actual = plant_rows.weather_valid_time.sort_values().reset_index(drop=True)
            if len(actual) != len(expected_times) or not actual.eq(pd.Series(expected_times)).all():
                raise ValueError(f"Horas ausentes ou excedentes na rodada: {directory}")
        registry_hashes.add(protocol["registry_sha256"])
        source = {
            "directory": str(directory.resolve()),
            "weather_run_time": run.isoformat(),
            "registry_sha256": protocol["registry_sha256"],
            "response_sha256": raw_hash,
            "normalized_csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
            "metadata_sha256": hashlib.sha256(meta_path.read_bytes()).hexdigest(),
        }
        frame["source_csv_sha256"] = source["normalized_csv_sha256"]
        sources.append(source)
        frames.append(frame)
    if not frames:
        raise ValueError("Informe pelo menos um diretório de rodada.")
    if len(registry_hashes) != 1:
        raise ValueError("As rodadas usam versões diferentes do cadastro; reconcilie-as antes da junção.")
    return validate_weather(pd.concat(frames, ignore_index=True)), sources


def select_weather_asof(weather, origins, *, horizon_hours=6):
    """Iguala validade ao alvo, filtra disponibilidade e escolhe a rodada mais nova.

    O limite é inclusivo: disponível exatamente na emissão é elegível.
    A escolha prioriza a inicialização mais recente entre as rodadas elegíveis.
    """
    if isinstance(horizon_hours, bool) or not isinstance(horizon_hours, int) or horizon_hours <= 0:
        raise ValueError("O horizonte deve ser inteiro positivo.")
    data = validate_weather(weather)
    origin_times = pd.Series([utc_timestamp(x) for x in origins], dtype="datetime64[ns, UTC]")
    if origin_times.empty or not origin_times.is_unique:
        raise ValueError("Informe origens não vazias e únicas.")
    entities = data[[*ENTITY, *STATIC]].drop_duplicates()
    if entities.duplicated(ENTITY).any():
        raise ValueError("Atributos cadastrais divergentes para a mesma usina/modelo.")
    if entities.id_ons_conjunto.nunique() != 1:
        raise ValueError("Use um conjunto por execução.")
    if not np.allclose(entities.groupby("weather_model").capacity_weight.sum(), 1):
        raise ValueError("O peso das usinas deve somar 1 em cada modelo meteorológico.")

    # 1. Todas as decisões esperadas existem, mesmo quando falta meteorologia.
    decisions = pd.DataFrame({"forecast_origin": origin_times}).merge(entities, how="cross")
    decisions["target_time"] = decisions.forecast_origin + pd.Timedelta(hours=horizon_hours)

    # 2. Cada decisão pode ter várias rodadas prevendo o MESMO horário-alvo.
    candidates = decisions.merge(
        data.drop(columns=STATIC),
        left_on=[*ENTITY, "target_time"],
        right_on=[*ENTITY, "weather_valid_time"],
        how="inner", validate="one_to_many",
    )

    # 3. Inicialização não substitui disponibilidade. Filtre ANTES de escolher.
    eligible = candidates.loc[candidates.weather_available_at <= candidates.forecast_origin].copy()

    # 4. Uma linha por decisão: inicialização mais recente dentre as elegíveis.
    chosen = (
        eligible.sort_values([*DECISION_KEY, "weather_run_time"])
        .drop_duplicates(DECISION_KEY, keep="last")
    )
    payload_columns = [c for c in chosen if c in DECISION_KEY or c not in decisions]
    result = decisions.merge(chosen[payload_columns], on=DECISION_KEY, how="left", validate="one_to_one")

    # 5. Guardar ausências evita avaliar apenas emissões convenientes.
    for name, table in (("candidate_count", candidates), ("eligible_count", eligible)):
        counts = table.groupby(DECISION_KEY).size().rename(name).reset_index()
        result = result.merge(counts, on=DECISION_KEY, how="left", validate="one_to_one")
        result[name] = result[name].fillna(0).astype(int)
    result["weather_selected"] = result.weather_run_time.notna()
    result["selection_status"] = np.select(
        [result.weather_selected, result.candidate_count.eq(0)],
        ["selected", "no_forecast_for_target"], default="not_available_at_origin",
    )
    result["horizon_hours"] = horizon_hours
    result["lead_hours"] = ((result.weather_valid_time - result.weather_run_time) / pd.Timedelta(hours=1)).astype("Int64")
    result["run_age_hours"] = (result.forecast_origin - result.weather_run_time) / pd.Timedelta(hours=1)
    return result.sort_values(DECISION_KEY).reset_index(drop=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dirs", type=Path, nargs="+", required=True)
    parser.add_argument("--origin-start", required=True)
    parser.add_argument("--origin-end", required=True, help="Fim inclusivo; emissões horárias.")
    parser.add_argument("--horizon-hours", type=int, default=6)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    start, end = utc_timestamp(args.origin_start), utc_timestamp(args.origin_end)
    if end < start or start != start.floor("h") or end != end.floor("h"):
        parser.error("Informe início/fim em horas inteiras, com fim >= início.")
    weather, sources = load_weather_runs(args.run_dirs)
    origins = pd.date_range(start, end, freq="h")
    selected = select_weather_asof(weather, origins, horizon_hours=args.horizon_hours)
    coverage = selected.groupby(["forecast_origin", "target_time", "weather_model"], as_index=False).agg(
        expected_plants=("id_ons_usina", "size"),
        matched_plants=("weather_selected", "sum"),
        selected_run_min=("weather_run_time", "min"),
        selected_run_max=("weather_run_time", "max"),
    )
    coverage["missing_plants"] = coverage.expected_plants - coverage.matched_plants
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "weather_asof.csv"
    selected.to_csv(output_path, index=False)
    coverage.to_csv(args.output_dir / "coverage.csv", index=False)
    metadata = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "horizon_hours": args.horizon_hours,
        "origin_start": start.isoformat(), "origin_end_inclusive": end.isoformat(),
        "origins": len(origins), "decision_rows": len(selected),
        "selected_rows": int(selected.weather_selected.sum()),
        "policy": "valid_time == origin + horizon; available_at <= origin; latest eligible run_time",
        "historical_availability_verified": False,
        "generation_timezone_verified": False,
        "sources": sources,
        "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
    }
    (args.output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Rodadas carregadas: {len(sources)}; linhas meteorológicas: {len(weather)}")
    print(f"Emissões: {len(origins)}; decisões usina/emissão: {len(selected)}")
    print(f"Com meteorologia: {selected.weather_selected.sum()}; sem meteorologia: {(~selected.weather_selected).sum()}")
    print(coverage.to_string(index=False))
    print("Disponibilidade histórica assumida; seleção calculada sob essa hipótese.")
    print(f"Arquivos: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
