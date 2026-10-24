from pathlib import Path
import pandas as pd

# Caminho do arquivo de entrada
input_file = Path("data/external/weather/CJU_BA5EIGT/gfs_20260901T0000Z/grid_mapping.csv")

# Diretórios de saída dentro de data/reference
output_dir_reference = Path("data/reference")
output_dir_conjunto = Path("data/reference/CJU_BA5EIGT")

# Garante que as pastas existam
output_dir_reference.mkdir(parents=True, exist_ok=True)
output_dir_conjunto.mkdir(parents=True, exist_ok=True)

# 1. Ler grid_mapping.csv
df_mapping = pd.read_csv(input_file)

# Identificar a coluna do nome da usina
usina_col = "nom_usina" if "nom_usina" in df_mapping.columns else "usina"

# 2 e 3. Agrupar por latitude/longitude da grade, contar usinas e somar os pesos
grid_weights = (
    df_mapping.groupby(["grid_latitude", "grid_longitude"])
    .agg(
        num_usinas=("id_ons_usina", "nunique"),
        capacity_weight=("capacity_weight", "sum")
    )
    .reset_index()
)

# 4. Salvar o arquivo CSV na pasta data/reference
grid_weights.to_csv(input_file.with_name("grid_weights.csv"), index=False)
#grid_weights.to_csv(output_dir_reference / "grid_weights.csv", index=False)
#grid_weights.to_csv(output_dir_conjunto / "grid_weights.csv", index=False)

print("=== Resumo por Ponto da Grade ===")
print(grid_weights.to_string(index=False))
print(f"\nSalvo em: {output_dir_reference / 'grid_weights.csv'}")
print(f"Salvo em: {output_dir_conjunto / 'grid_weights.csv'}")
print(f"Total de linhas (pontos de grade): {len(grid_weights)}")
print(f"Soma total dos pesos: {grid_weights['capacity_weight'].sum():.6f}")