"""M04: junta as 27 features de geração às 5 features meteorológicas.

Destino: src/renewable_forecast/weather_training.py.
O fuso informado é uma hipótese explícita; não certifica o contrato do ONS.
A tabela preserva todas as emissões meteorológicas, inclusive sem par na geração.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from renewable_forecast.features import FEATURE_COLUMNS, build_feature_frame
from renewable_forecast.supervised import build_horizon_training_frame
from renewable_forecast.weather_asof import utc_timestamp
from renewable_forecast.weather_features import WEATHER_FEATURE_COLUMNS


JOIN_KEYS = ["forecast_origin", "target_time"]
MODEL_FEATURE_COLUMNS = [*FEATURE_COLUMNS, *WEATHER_FEATURE_COLUMNS]
GENERATION_TIMES = [
    *JOIN_KEYS, "history_reference_time", "history_end", "target_available_at",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_weather_training_frame(
    series: pd.DataFrame,
    weather: pd.DataFrame,
    *,
    conjunto: str,
    generation_timezone: str,
    horizon_hours: int = 6,
    availability_delay_hours: int = 2,
) -> pd.DataFrame:
    """Junta por emissão E alvo, após colocar as chaves no mesmo fuso.

    Calendário: calculado no fuso declarado para a geração, como no baseline.
    Chaves da junção: UTC. Alvo: target_generation, separado das 32 entradas.
    model_row_complete indica completude numérica, não aprovação do modelo.
    """
    data = series.copy()
    required = {"din_instante", "val_geracao"}
    if not required.issubset(data.columns):
        raise ValueError(f"Geração: faltam {sorted(required - set(data.columns))}.")
    if "id_ons_conjunto" in data.columns:
        if data["id_ons_conjunto"].isna().any() or not data["id_ons_conjunto"].eq(conjunto).all():
            raise ValueError("A geração deve conter somente o conjunto informado.")

    ts = pd.to_datetime(data["din_instante"], errors="raise")
    if ts.isna().any() or not pd.api.types.is_datetime64_any_dtype(ts):
        raise ValueError("Geração: timestamps ausentes ou mistura de fusos.")
    # Localizar atribui significado ao relógio ingênuo; converter preserva o instante.
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize(generation_timezone, ambiguous="raise", nonexistent="raise")
    else:
        ts = ts.dt.tz_convert(generation_timezone)
    data["din_instante"] = ts

    # O histórico completo é necessário para os lags, inclusive o de 168 horas.
    generation = build_horizon_training_frame(
        data,
        horizon_hours=horizon_hours,
        availability_delay_hours=availability_delay_hours,
    )
    generation = generation[[*GENERATION_TIMES, *FEATURE_COLUMNS, "target_generation"]].copy()
    for column in [*JOIN_KEYS, "history_end"]:
        generation[f"{column}_local"] = generation[column]
    for column in GENERATION_TIMES:
        generation[column] = generation[column].dt.tz_convert("UTC")

    met = weather.copy()
    required_weather = {
        *JOIN_KEYS, "id_ons_conjunto", "weather_model", "weather_complete",
        "weather_latest_available_at", *WEATHER_FEATURE_COLUMNS,
    }
    missing = required_weather - set(met.columns)
    if met.empty or missing:
        raise ValueError(f"Meteorologia vazia ou colunas ausentes: {sorted(missing)}.")
    if met["id_ons_conjunto"].isna().any() or not met["id_ons_conjunto"].eq(conjunto).all():
        raise ValueError("A meteorologia deve conter somente o conjunto informado.")
    if met["weather_model"].isna().any() or met["weather_model"].nunique() != 1:
        raise ValueError("Use um único modelo meteorológico por tabela.")
    if not pd.api.types.is_bool_dtype(met["weather_complete"]) or met["weather_complete"].isna().any():
        raise ValueError("weather_complete deve ser booleano e estar preenchido.")
    for column in [*JOIN_KEYS, "weather_latest_available_at"]:
        met[column] = pd.Series(
            [pd.NaT if pd.isna(x) else utc_timestamp(x) for x in met[column]],
            index=met.index, dtype="datetime64[ns, UTC]",
        )
    if met[JOIN_KEYS].isna().any().any() or met.duplicated(JOIN_KEYS).any():
        raise ValueError("Meteorologia: chaves ausentes ou duplicadas.")
    if not (met["target_time"] - met["forecast_origin"]).eq(pd.Timedelta(hours=horizon_hours)).all():
        raise ValueError("O horizonte meteorológico difere do horizonte solicitado.")
    complete_weather = met.loc[met["weather_complete"]]
    if complete_weather["weather_latest_available_at"].isna().any() or (
        complete_weather["weather_latest_available_at"] > complete_weather["forecast_origin"]
    ).any():
        raise ValueError("Meteorologia completa sem disponibilidade causal válida.")
    overlap = (set(met.columns) & set(generation.columns)) - set(JOIN_KEYS)
    if overlap:
        raise ValueError(f"Colunas sobrepostas inesperadas: {sorted(overlap)}.")

    # Esta é a junção central: nenhuma emissão desaparece silenciosamente.
    frame = met.merge(
        generation, on=JOIN_KEYS, how="left", validate="one_to_one",
        indicator="generation_match",
    ).sort_values("forecast_origin").reset_index(drop=True)
    matched = frame["generation_match"].eq("both")
    delay = pd.Timedelta(hours=availability_delay_hours)
    if not (frame.loc[matched, "history_end"] + delay).eq(frame.loc[matched, "forecast_origin"]).all():
        raise ValueError("O final do histórico não respeita o atraso de geração.")
    if not (frame.loc[matched, "target_time"] + delay).eq(frame.loc[matched, "target_available_at"]).all():
        raise ValueError("Disponibilidade do alvo inconsistente com o atraso.")

    numeric_columns = [*MODEL_FEATURE_COLUMNS, "target_generation"]
    frame[numeric_columns] = frame[numeric_columns].apply(pd.to_numeric, errors="raise")
    finite = np.isfinite(frame[numeric_columns].to_numpy(dtype=float)).all(axis=1)
    frame["model_row_complete"] = matched & frame["weather_complete"] & finite
    frame["join_status"] = "complete"
    frame.loc[~finite, "join_status"] = "missing_or_nonfinite_features_or_target"
    frame.loc[~frame["weather_complete"], "join_status"] = "incomplete_weather"
    frame.loc[~matched, "join_status"] = "missing_generation_target_or_history"
    return frame


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation", type=Path, required=True)
    parser.add_argument("--weather-dir", type=Path, required=True)
    parser.add_argument("--conjunto", required=True)
    parser.add_argument("--generation-timezone", required=True, help="Hipótese explícita, ex.: America/Sao_Paulo")
    parser.add_argument("--horizon-hours", type=int, default=6)
    parser.add_argument("--availability-delay-hours", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output_dir.resolve() == args.weather_dir.resolve():
        raise ValueError("Use uma pasta de saída diferente da pasta meteorológica.")

    weather_csv = args.weather_dir / "weather_features.csv"
    weather_metadata = args.weather_dir / "metadata.json"
    source = json.loads(weather_metadata.read_text(encoding="utf-8"))
    if source.get("feature_columns") != WEATHER_FEATURE_COLUMNS:
        raise ValueError("Use a pasta h6_spatial_sample, que contém as cinco features de vento.")
    if sha256(weather_csv) != source.get("output_sha256"):
        raise ValueError("O CSV meteorológico difere do hash registrado.")
    series = pd.read_parquet(args.generation)
    frame = build_weather_training_frame(
        series, pd.read_csv(weather_csv), conjunto=args.conjunto,
        generation_timezone=args.generation_timezone,
        horizon_hours=args.horizon_hours,
        availability_delay_hours=args.availability_delay_hours,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = args.output_dir / "model_frame.csv"
    frame.to_csv(output_csv, index=False)
    metadata = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "conjunto": args.conjunto,
        "generation_entity_evidence": "column_checked" if "id_ons_conjunto" in series.columns else "declared_by_cli",
        "horizon_hours": args.horizon_hours,
        "generation_timezone_hypothesis": args.generation_timezone,
        "generation_timezone_verified": False,
        "generation_interval_semantics": "original_reference_label; interval_start_or_end_unverified",
        "availability_delay_hours": args.availability_delay_hours,
        "generation_availability_is_assumed": True,
        "calendar_timezone": args.generation_timezone,
        "calendar_reference": "target_time",
        "join_timezone": "UTC",
        "join_keys": JOIN_KEYS,
        "join_type": "left; one_to_one; weather_origins_preserved",
        "generation_rows_read": len(series),
        "rows": len(frame),
        "matched_generation_rows": int(frame["generation_match"].eq("both").sum()),
        "complete_rows": int(frame["model_row_complete"].sum()),
        "forecast_origin_min": frame["forecast_origin"].min().isoformat(),
        "forecast_origin_max": frame["forecast_origin"].max().isoformat(),
        "historical_feature_columns": FEATURE_COLUMNS,
        "weather_feature_columns": WEATHER_FEATURE_COLUMNS,
        "model_feature_columns": MODEL_FEATURE_COLUMNS,
        "target_column": "target_generation",
        "training_performed": False,
        "generation_file_sha256": sha256(args.generation),
        "weather_csv_sha256": sha256(weather_csv),
        "weather_metadata_sha256": sha256(weather_metadata),
        "code_sha256": sha256(Path(__file__)),
        "generation_features_code_sha256": sha256(Path(inspect.getsourcefile(build_feature_frame))),
        "generation_supervised_code_sha256": sha256(Path(inspect.getsourcefile(build_horizon_training_frame))),
        "output_sha256": sha256(output_csv),
        "source_weather": source,
    }
    (args.output_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    print(f"Emissões meteorológicas: {len(frame)}")
    print(f"Com par na geração: {metadata['matched_generation_rows']}; linhas completas: {metadata['complete_rows']}")
    print(f"Entradas: {len(FEATURE_COLUMNS)} históricas/calendário + {len(WEATHER_FEATURE_COLUMNS)} meteorológicas = {len(MODEL_FEATURE_COLUMNS)}")
    print("Alvo separado: target_generation")
    display = [
        "forecast_origin", "forecast_origin_local", "history_end_local",
        "target_time", "target_time_local", "lag_1h", "wind_speed_mean_ms",
        "target_generation", "join_status",
    ]
    print(frame[display].head(3).to_string(index=False))
    print(f"Hipótese de fuso da geração: {args.generation_timezone}; contrato de intervalo ainda não verificado.")
    print(f"CSV salvo: {output_csv.resolve()}")
    print(f"Metadados: {(args.output_dir / 'metadata.json').resolve()}")
    if not frame["model_row_complete"].all():
        raise SystemExit("Há emissões incompletas. Consulte join_status no CSV; nenhuma foi descartada.")


if __name__ == "__main__":
    main()
