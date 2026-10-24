"""Coleta histórica GFS h+6 e atraso meteorológico assumido de 6h.

Destino: src/renewable_forecast/weather_history.py.
Reutiliza weather_runs, weather_asof e weather_features, sem treinar modelos.
Na pasta de saída, h6_sample contém decisões por usina e h6_spatial_sample
contém atributos agregados. As coletas ficam em --run-root.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path

import pandas as pd

from renewable_forecast import weather_asof, weather_features, weather_runs


HORIZON_HOURS = 6
ASSUMED_LATENCY_HOURS = 6
FORECAST_HOURS_PER_RUN = 48


def plan_history(origin_start, origin_end):
    """Origens inclusivas; última inicialização elegível em cada emissão.

    Sob atraso fixo de6h: emissão menos6h, arredondada para baixo até
    o ciclo00/06/12/18 UTC, fornece a rodada que deve ser consultada.
    """
    start = weather_asof.utc_timestamp(origin_start)
    end = weather_asof.utc_timestamp(origin_end)
    if start != start.floor("h") or end != end.floor("h") or end < start:
        raise ValueError("Use horas inteiras com fuso e fim maior ou igual ao início.")
    origins = pd.date_range(start, end, freq="h")
    runs = (origins - pd.Timedelta(hours=ASSUMED_LATENCY_HOURS)).floor("6h").unique().sort_values()
    weather_runs.parse_run(runs[0].isoformat())
    return origins, runs


def run_stage(function, arguments):
    """Mostra o diagnóstico completo da etapa se ela falhar."""
    log = io.StringIO()
    try:
        with redirect_stdout(log):
            function(arguments)
    except Exception:
        print(log.getvalue(), end="", flush=True)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--origin-start", required=True)
    parser.add_argument("--origin-end", required=True, help="Última emissão, inclusiva.")
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    origins, runs = plan_history(args.origin_start, args.origin_end)
    registry = weather_runs.read_registry(args.registry)
    if registry["id_ons_conjunto"].nunique() != 1:
        raise ValueError("Este piloto recebe o cadastro de um único conjunto.")
    run_dirs = [args.run_root / f"gfs_{run.strftime('%Y%m%dT%H%MZ')}" for run in runs]
    selected_dir = args.output_dir / "h6_sample"
    features_dir = args.output_dir / "h6_spatial_sample"
    plan = {
        "origin_start": origins[0].isoformat(),
        "origin_end_inclusive": origins[-1].isoformat(),
        "origins": len(origins),
        "weather_model": weather_runs.MODEL,
        "horizon_hours": HORIZON_HOURS,
        "assumed_latency_hours": ASSUMED_LATENCY_HOURS,
        "forecast_hours_per_run": FORECAST_HOURS_PER_RUN,
        "registry_sha256": hashlib.sha256(args.registry.read_bytes()).hexdigest(),
        "run_times": [run.isoformat() for run in runs],
        "historical_availability_verified": False,
        "registry_historical_versions_verified": False,
        "generation_timezone_verified": False,
    }
    plan_path = args.output_dir / "plan.json"
    if plan_path.exists() and json.loads(plan_path.read_text(encoding="utf-8")) != plan:
        raise ValueError("Esta pasta contém outro plano. Use uma pasta própria para o novo período.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Planejamento: {len(origins)} emissões; {len(runs)} rodadas; {len(registry)} usinas.", flush=True)
    for number, (run, directory) in enumerate(zip(runs, run_dirs), start=1):
        cached = (directory / "response.json").exists() and (directory / "metadata.json").exists()
        mode = "verificar cache" if cached else "consultar API"
        print(f"[{number:02d}/{len(runs):02d}] {run.isoformat()} — {mode}", flush=True)
        run_stage(weather_runs.main, [
            "--registry", str(args.registry), "--run", run.isoformat(),
            "--hours", str(FORECAST_HOURS_PER_RUN),
            "--assumed-latency-hours", str(ASSUMED_LATENCY_HOURS),
            "--output-dir", str(directory),
        ])

    print("Selecionando a rodada elegível por usina e emissão...", flush=True)
    run_stage(weather_asof.main, [
        "--run-dirs", *map(str, run_dirs),
        "--origin-start", origins[0].isoformat(), "--origin-end", origins[-1].isoformat(),
        "--horizon-hours", str(HORIZON_HOURS), "--output-dir", str(selected_dir),
    ])
    print("Agregando por capacidade...", flush=True)
    run_stage(weather_features.main, [
        "--input-dir", str(selected_dir), "--output-dir", str(features_dir),
    ])
    features = pd.read_csv(features_dir / "weather_features.csv")
    coverage = pd.read_csv(selected_dir / "coverage.csv")
    if len(features) != len(origins) or not features["weather_complete"].all():
        raise ValueError("O piloto terminou com cobertura incompleta; consulte coverage.csv.")
    print(f"Emissões agregadas: {len(features)}; completas: {int(features.weather_complete.sum())}")
    print(f"Decisões por usina: {int(coverage.expected_plants.sum())}; ausências: {int(coverage.missing_plants.sum())}")
    print(f"Emissões UTC: {features.forecast_origin.iloc[0]} a {features.forecast_origin.iloc[-1]}")
    print(f"Alvos UTC: {features.target_time.iloc[0]} a {features.target_time.iloc[-1]}")
    print(f"Seleção por usina: {(selected_dir / 'weather_asof.csv').resolve()}")
    print(f"Atributos do conjunto: {(features_dir / 'weather_features.csv').resolve()}")
    print("Disponibilidade e cadastro históricos permanecem hipóteses; geração ainda não integrada.")


if __name__ == "__main__":
    main()
