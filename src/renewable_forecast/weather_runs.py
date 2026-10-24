"""M04.2: uma rodada meteorológica real para as usinas cadastradas.

Destino: src/renewable_forecast/weather_runs.py
Saída: JSON original, metadados, tabela horária e correspondência espacial.
Disponibilidade histórica é uma hipótese explícita; coleta é observada.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd


ENDPOINT = "https://single-runs-api.open-meteo.com/v1/forecast"
MODEL = "gfs_global"
ARCHIVE_START = pd.Timestamp("2026-04-02T00:00:00Z")
VARIABLES = ("wind_speed_100m", "wind_direction_100m")


def parse_run(value: str) -> pd.Timestamp:
    """Exige fuso explícito e um ciclo GFS de seis em seis horas."""
    run = pd.Timestamp(value)
    if pd.isna(run) or run.tzinfo is None:
        raise ValueError("Informe --run com fuso explícito, por exemplo 2026-09-01T00:00:00Z.")
    run = run.tz_convert("UTC")
    if run != run.floor("h") or run.hour not in (0, 6, 12, 18):
        raise ValueError("O ciclo GFS deve ser 00, 06, 12 ou 18 horas UTC, sem minutos.")
    if run < ARCHIVE_START:
        raise ValueError("Este arquivo de rodadas GFS começa em 02/04/2026.")
    return run


def read_registry(path: Path) -> pd.DataFrame:
    """Uma linha por usina: ordem estável para associar pedido e resposta."""
    data = pd.read_csv(path)
    required = {
        "id_ons_conjunto", "id_ons_usina", "nom_usina", "ceg_key",
        "latitude", "longitude", "capacity_weight",
    }
    missing = required - set(data.columns)
    if missing or data.empty:
        raise ValueError(f"Cadastro vazio ou incompleto; colunas ausentes: {sorted(missing)}")
    if data[list(required)].isna().any().any():
        raise ValueError("Cadastro contém chaves, coordenadas ou pesos ausentes.")
    if data["id_ons_conjunto"].nunique() != 1:
        raise ValueError("Use o cadastro de um único conjunto por execução.")
    for key in ("id_ons_usina", "ceg_key"):
        if not data[key].is_unique:
            raise ValueError(f"A chave {key} deve ser única por usina.")
    for column in ("latitude", "longitude", "capacity_weight"):
        data[column] = pd.to_numeric(data[column], errors="raise")
        if not np.isfinite(data[column]).all():
            raise ValueError(f"Valores não finitos em {column}.")
    if not data["latitude"].between(-90, 90).all() or not data["longitude"].between(-180, 180).all():
        raise ValueError("Coordenadas fora dos limites geográficos.")
    if (data["capacity_weight"] <= 0).any() or not np.isclose(data["capacity_weight"].sum(), 1):
        raise ValueError("Os pesos de capacidade devem ser positivos e somar 1.")
    return data.sort_values("id_ons_usina").reset_index(drop=True)


def build_request(registry: pd.DataFrame, run: pd.Timestamp, hours: int) -> dict:
    """Seleciona um modelo e uma rodada; unidades e grade são explícitas."""
    return {
        "latitude": ",".join(registry["latitude"].map(lambda x: f"{x:.8f}")),
        "longitude": ",".join(registry["longitude"].map(lambda x: f"{x:.8f}")),
        "models": MODEL,
        "hourly": ",".join(VARIABLES),
        "wind_speed_unit": "ms",
        "timezone": "UTC",
        "run": run.strftime("%Y-%m-%dT%H:%M"),
        "forecast_hours": hours,
        "cell_selection": "nearest",
        # A API exige um valor de elevation por coordenada. nan desativa downscaling.
        "elevation": ",".join(["nan"] * len(registry)),
    }


def fetch_run(params: dict, protocol: dict, output: Path) -> tuple[object, dict]:
    """Conserva os bytes e o primeiro horário de coleta; reutiliza o cache."""
    raw_path, meta_path = output / "response.json", output / "metadata.json"
    if raw_path.exists() or meta_path.exists():
        if not (raw_path.exists() and meta_path.exists()):
            raise ValueError("Cache incompleto. Preserve-o e escolha outro --output-dir.")
        raw = raw_path.read_bytes()
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        if metadata["request_params"] != params or metadata["protocol"] != protocol:
            raise ValueError("Esse diretório pertence a outra configuração. Escolha outro --output-dir.")
        if hashlib.sha256(raw).hexdigest() != metadata["response_sha256"]:
            raise ValueError("O JSON original foi alterado: hash diferente do registrado.")
        print("Reutilizando a resposta original; nenhuma nova consulta.", flush=True)
        return json.loads(raw), metadata

    url = ENDPOINT + "?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "Renewcast-Lab/0.1"})
    print("Consultando uma rodada GFS para todos os pontos...", flush=True)
    for attempt in range(3):
        try:
            with urlopen(request, timeout=40) as response:
                raw = response.read()
                metadata = {
                    "request_url": url,
                    "request_params": params,
                    "protocol": protocol,
                    "http_status": response.status,
                    "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                    "response_sha256": hashlib.sha256(raw).hexdigest(),
                    "response_bytes": len(raw),
                    "http_last_modified": response.headers.get("Last-Modified"),
                    "etag": response.headers.get("ETag"),
                    "attribution": "Weather data: NOAA GFS via Open-Meteo; locations: ONS/ANEEL.",
                    "documentation": "https://open-meteo.com/en/docs/single-runs-api",
                }
            break
        except HTTPError as exc:
            reason = exc.read().decode("utf-8", errors="replace")[:1200]
            # Repetir 400 não corrige parâmetro inválido. Repetir 429 piora o limite.
            if exc.code not in (500, 502, 503, 504) or attempt == 2:
                raise RuntimeError(f"API respondeu HTTP {exc.code}: {reason}") from exc
            print(f"HTTP {exc.code}; nova tentativa em {2 ** attempt}s.", flush=True)
        except (URLError, TimeoutError) as exc:
            if attempt == 2:
                raise RuntimeError(f"Consulta não concluída: {exc}") from exc
            print(f"Falha temporária de rede; nova tentativa em {2 ** attempt}s.", flush=True)
        time.sleep(2 ** attempt)

    payload = json.loads(raw)
    if isinstance(payload, dict) and payload.get("error"):
        raise ValueError(f"Resposta de erro: {payload.get('reason')}")
    output.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(raw)
    meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload, metadata


def normalize_run(payload, registry, run, hours, assumed_latency_hours, fetched_at):
    """Expande os vetores JSON: uma linha por usina, rodada e hora prevista."""
    responses = payload if isinstance(payload, list) else [payload]
    if len(responses) != len(registry):
        raise ValueError("A API não retornou um objeto para cada usina solicitada.")
    expected_times = pd.date_range(run, periods=hours, freq="h")
    available = run + pd.Timedelta(hours=assumed_latency_hours)
    frames, points, seen = [], [], set()
    for response in responses:
        # Na resposta real, location_id=0 é omitido. Os demais IDs são explícitos.
        location_id = response.get("location_id", 0)
        if type(location_id) is not int or location_id in seen or not 0 <= location_id < len(registry):
            raise ValueError("location_id ausente, duplicado ou incompatível com o pedido.")
        seen.add(location_id)
        plant = registry.iloc[location_id]
        units = response.get("hourly_units", {})
        if response.get("utc_offset_seconds") != 0 or units.get("time") != "iso8601":
            raise ValueError("A resposta deve usar timestamps ISO 8601 em UTC.")
        if units.get("wind_speed_100m") != "m/s" or units.get("wind_direction_100m") != "°":
            raise ValueError(f"Unidades meteorológicas inesperadas: {units}")
        hourly = pd.DataFrame(response["hourly"])
        valid = pd.to_datetime(hourly["time"], utc=True, errors="raise")
        if len(valid) != hours or not (valid.reset_index(drop=True) == pd.Series(expected_times)).all():
            raise ValueError("A resposta não cobre todas as horas da rodada solicitada.")
        values = hourly[list(VARIABLES)].apply(pd.to_numeric, errors="raise")
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError("Existem valores de vento ausentes ou não finitos na resposta.")
        if (values["wind_speed_100m"] < 0).any() or not values["wind_direction_100m"].between(0, 360).all():
            raise ValueError("Velocidade negativa ou direção fora de 0–360 graus.")
        lat, lon = float(response["latitude"]), float(response["longitude"])
        if not np.isfinite([lat, lon]).all() or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("Coordenadas da grade inválidas.")
        point = {
            "location_id": location_id,
            "id_ons_conjunto": plant["id_ons_conjunto"],
            "id_ons_usina": plant["id_ons_usina"],
            "nom_usina": plant["nom_usina"],
            "ceg_key": plant["ceg_key"],
            "capacity_weight": float(plant["capacity_weight"]),
            "plant_latitude": float(plant["latitude"]),
            "plant_longitude": float(plant["longitude"]),
            "grid_latitude": lat,
            "grid_longitude": lon,
        }
        points.append(point)
        frame = pd.DataFrame({
            "weather_valid_time": valid,
            "wind_speed_100m_ms": values["wind_speed_100m"],
            "wind_direction_100m_deg": values["wind_direction_100m"],
        })
        for column, value in point.items():
            frame[column] = value
        frame["weather_model"] = MODEL
        frame["weather_run_time"] = run
        frame["lead_hours"] = ((valid - run) / pd.Timedelta(hours=1)).astype(int)
        frame["weather_available_at"] = available
        frame["availability_is_assumed"] = True
        frame["weather_fetched_at"] = pd.Timestamp(fetched_at)
        frames.append(frame)
    forecasts = pd.concat(frames, ignore_index=True)
    keys = ["id_ons_usina", "weather_model", "weather_run_time", "weather_valid_time"]
    if forecasts.duplicated(keys).any():
        raise ValueError("Chave meteorológica duplicada.")
    return forecasts.sort_values(keys).reset_index(drop=True), pd.DataFrame(points).sort_values("location_id")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--run", required=True, help="Inicialização com fuso, ex.: 2026-09-01T00:00:00Z")
    parser.add_argument("--hours", type=int, default=48)
    parser.add_argument("--assumed-latency-hours", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if not 1 <= args.hours <= 120:
        parser.error("--hours deve estar entre 1 e 120 para esta coleta inicial.")
    if not 1 <= args.assumed_latency_hours <= 120:
        parser.error("--assumed-latency-hours deve estar entre 1 e 120.")
    run = parse_run(args.run)
    registry = read_registry(args.registry)
    params = build_request(registry, run, args.hours)
    protocol = {
        "schema_version": 1,
        "weather_model": MODEL,
        "run_time_utc": run.isoformat(),
        "hours": args.hours,
        "assumed_latency_hours": args.assumed_latency_hours,
        "availability_is_assumed": True,
        "historical_availability_verified": False,
        "availability_rule": "weather_run_time + assumed_latency_hours; not observed release time",
        "registry_sha256": hashlib.sha256(args.registry.read_bytes()).hexdigest(),
        "request_plant_ids": registry["id_ons_usina"].tolist(),
        "registry_historical_versions_verified": False,
        "generation_timezone_verified": False,
    }
    payload, metadata = fetch_run(params, protocol, args.output_dir)
    forecasts, points = normalize_run(
        payload, registry, run, args.hours,
        args.assumed_latency_hours, metadata["fetched_at_utc"],
    )
    forecasts.to_csv(args.output_dir / "weather_forecasts.csv", index=False)
    points.to_csv(args.output_dir / "grid_mapping.csv", index=False)
    grid_count = len(points[["grid_latitude", "grid_longitude"]].drop_duplicates())
    print(f"Modelo: {MODEL}; rodada: {run.isoformat()}")
    print(f"Usinas: {len(points)}; pontos de grade distintos: {grid_count}")
    print(f"Horas por usina: {args.hours}; linhas: {len(forecasts)}")
    print(f"Validade UTC: {forecasts.weather_valid_time.min()} a {forecasts.weather_valid_time.max()}")
    print(f"Disponibilidade ASSUMIDA: {forecasts.weather_available_at.iloc[0]}")
    print(f"Coleta observada UTC: {metadata['fetched_at_utc']}")
    print("Previsões arquivadas; disponibilidade histórica e fuso da geração ainda não verificados.")
    print(f"Arquivos: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
