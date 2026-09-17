# Renewable Forecast Lab

Ferramentas para preparar, validar e avaliar previsões horárias de geração
renovável.

## Instalação para desenvolvimento

```powershell
python -m pip install -e ".[dev]"
```

## Backtesting

O arquivo de entrada deve ser um Parquet com as colunas `din_instante` e
`val_geracao`, sem timestamps duplicados ou lacunas na frequência horária.

```powershell
renewcast backtest `
  --input data\processed\series.parquet `
  --output-dir reports\backtest
```

O comando produz `predictions.parquet`, `fold_metrics.csv` e `summary.csv` no
diretório informado.

## Seleção, treino e previsão

```powershell
renewcast tune --input data\processed\series.parquet

renewcast train `
  --input data\processed\series.parquet `
  --output models\hist-gradient-boosting-v1

renewcast predict `
  --model models\hist-gradient-boosting-v1 `
  --input data\processed\series.parquet
```

Os experimentos locais são registrados em `mlflow.db`; artefatos e modelos
gerados localmente não são versionados pelo Git.
