import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Adiciona a pasta src ao path do Python
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from renewable_forecast.weather_features import weighted_wind_features


def main():
    input_file = Path("data/interim/weather/CJU_BA5EIGT/h6_sample/weather_asof.csv")

    # 1. Ler weather_asof.csv e selecionar a emissão 2026-09-01 06:00:00+00:00
    df = pd.read_csv(input_file)
    df["forecast_origin"] = pd.to_datetime(df["forecast_origin"], utc=True)

    target_origin = pd.Timestamp("2026-09-01 06:00:00+00:00")
    df_06h = df[df["forecast_origin"] == target_origin].copy()

    print(f"Linhas selecionadas (15 usinas): {len(df_06h)}")

    # 2. Confirmar que velocidade e direção são únicas dentro de cada par de coordenadas
    uniques = df_06h.groupby(["grid_latitude", "grid_longitude"])[
        ["wind_speed_100m_ms", "wind_direction_100m_deg"]
    ].nunique()

    is_unique = (uniques["wind_speed_100m_ms"] == 1).all() and (
        uniques["wind_direction_100m_deg"] == 1
    ).all()
    print(f"Velocidade e direção são únicas em cada ponto de grade? {is_unique}")

    if not is_unique:
        raise ValueError("Valores divergentes de vento encontrados no mesmo ponto de grade!")

    # 3. Agrupar por coordenadas, somando capacity_weight e preservando velocidade e direção
    df_grid = df_06h.groupby(
        ["grid_latitude", "grid_longitude"], as_index=False
    ).agg({
        "capacity_weight": "sum",
        "wind_speed_100m_ms": "first",
        "wind_direction_100m_deg": "first",
    })

    print(f"Linhas após agrupamento (5 pontos de grade): {len(df_grid)}")

    # 4. Chamar weighted_wind_features nas duas tabelas e comparar os resultados
    features_plants = weighted_wind_features(df_06h)
    features_grid = weighted_wind_features(df_grid)

    comparison = pd.DataFrame({
        "Atributo": list(features_plants.keys()),
        "15 Usinas": list(features_plants.values()),
        "5 Pontos de Grade": list(features_grid.values()),
    })
    comparison["Diferença Absoluta"] = (
        comparison["15 Usinas"] - comparison["5 Pontos de Grade"]
    ).abs()

    print("\n=== Comparação das Features (15 Usinas vs 5 Pontos de Grade) ===")
    print(comparison.to_string(index=False))

    is_equivalent = np.allclose(
        list(features_plants.values()),
        list(features_grid.values()),
        rtol=1e-7,
        atol=1e-7,
    )
    if not is_equivalent:
    raise AssertionError("A agregação por grade alterou as features.")
    print(f"\nResultados idênticos dentro da tolerância numérica? {is_equivalent}")


if __name__ == "__main__":
    main()