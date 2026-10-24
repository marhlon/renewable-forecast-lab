from pathlib import Path
import pandas as pd

from renewable_forecast.weather_asof import load_weather_runs, select_weather_asof

def main():
    # 1. Definir os caminhos dos dois diretórios de rodadas
    base_dir = Path("data/external/weather/CJU_BA5EIGT")
    run_dirs = [
        base_dir / "gfs_20260901T0000Z",
        base_dir / "gfs_20260901T0600Z",
    ]

    # 2. Carregar as rodadas meteorológicas
    weather, _ = load_weather_runs(run_dirs)

    # 3. Criar uma cópia da tabela e acrescentar 2 horas à disponibilidade da rodada das 06h
    weather_modified = weather.copy()
    mask_06h = weather_modified["weather_run_time"] == pd.Timestamp("2026-09-01T06:00:00Z")
    weather_modified.loc[mask_06h, "weather_available_at"] += pd.Timedelta(hours=2)

    # 4. Definir as emissões (forecast_origin) das 05h às 15h UTC e executar a seleção h+6
    origins = pd.date_range("2026-09-01T05:00:00Z", "2026-09-01T15:00:00Z", freq="h")
    selected = select_weather_asof(weather_modified, origins, horizon_hours=6)

    # 5. Filtrar para BAEAMC (Amescla) e exibir as colunas solicitadas
    plant_mask = selected["id_ons_usina"].eq("BAEAMC") | selected["nom_usina"].str.contains("Amescla", case=False, na=False)
    cols = ["forecast_origin", "target_time", "weather_run_time", "weather_available_at"]
    
    result_baeamc = selected.loc[plant_mask, cols]

    output_dir = Path("data/interim/weather/CJU_BA5EIGT/h6_delay_simulation")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "amescla_delay_2h.csv"
    result_baeamc.to_csv(output_file, index=False)

    print(f"CSV salvo: {output_file.resolve()}")

    print("=== Diagnóstico de Atraso Meteorológico para BAEAMC (Amescla) ===")
    print(result_baeamc.to_string(index=False))

if __name__ == "__main__":
    main()