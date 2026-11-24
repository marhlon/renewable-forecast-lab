# RenewableForecastLab

Laboratório de Ciência de Dados aplicada a séries temporais, com dois projetos:
previsão de geração renovável e detecção de anomalias em telemetria de satélite.
O trabalho conecta preparação dos dados, avaliação temporal, implementação dos
algoritmos e entrega de software com evidências de execução.

| Projeto | Problema | Saída estudada |
|---|---|---|
| **P1 — Renewcast** | Prever geração a partir do histórico e investigar o uso de meteorologia | Previsões pontuais, quantis e decisões sobre eventos |
| **P2 — Satellite Anomaly Monitor** | Sincronizar sensores, comparar escores e avaliar alarmes no tempo | Escores por instante, inícios de alarme e métricas por evento |

Os resultados ao final são experimentos locais delimitados. O repositório registra
também falhas de generalização e hipóteses abertas; nenhum projeto tem aprovação operacional.

## O que foi implementado

### P1 — Renewcast

| Etapa | Implementação e evidências |
|---|---|
| Dados e avaliação | Contratos de esquema, frequência, duplicidade e cobertura; SQL/DuckDB; features temporais, baselines e backtesting cronológico |
| Modelagem clássica | Regressão, HistGradientBoosting, seleção temporal, calibração de viés, horizontes e experimentos com meteorologia disponível na emissão |
| Incerteza e eventos | Quantis, calibração de intervalos, classificação de eventos e seleção de política sob restrições de capacidade |
| Engenharia de entrega | API HTTP, contratos, lote idempotente em SQLite, conciliação, monitoramento, registro/rollback local, empacotamento, contêiner e cliente Windows |
| Processamento distribuído | Reprodução com PySpark/Delta e comparação com a referência local; equivalência do recorte sem presumir necessidade de escala |
| Redes e modelos pré-treinados | Autograd, MLP, GRU, atenção NumPy, composição encoder–decoder e inferência zero-shot com Chronos-Bolt Tiny |

A reprodução do serviço em contêiner e o cliente Windows foram conferidos no protocolo local.
CI remoto, shadow ao vivo e monitoramento contínuo permanecem fora dessas evidências.
Consulte o [aceite do contêiner](docs/Aceite_E87_Container.json) e o
[protocolo do cliente](docs/Aceite_E94_Cliente_1_1.md).

### P2 — Satellite Anomaly Monitor

| Unidade | Entrega |
|---|---|
| M10.1 | Sincronização multicanal causal, idade máxima, preservação da origem da amostra e auditoria de anotações |
| M10.2 | Escore robusto, erro de reconstrução PCA e Isolation Forest; rankings e sensibilidade a um evento dominante |
| M10.3 | Confirmação de alarmes, seleção no desenvolvimento, política congelada e avaliação temporal por ID de evento |
| M10.4 | Pacote de diagnóstico recebido; execução ainda não demonstrada nesta versão |

O percurso e seus limites estão nos guias de
[sincronização](satellite-anomaly-monitor/docs/Explicacao_M10_1_Passo_a_Passo.md),
[detectores](satellite-anomaly-monitor/docs/m10_2/Explicacao_Passo_a_Passo.md) e
[alarmes](satellite-anomaly-monitor/docs/m10_3/Explicacao_Passo_a_Passo.md).

## Dados e método

**P1.** O recorte principal usa geração horária do ONS, identificador `CJU_BA5EIGT`,
em MWmed. A reprodução M07.3 compara 8.760 registros de geração e 7.485 linhas elegíveis
de treino. Os experimentos h+24 de M08/M09 usam as mesmas 168 origens de avaliação:
contexto de 24 horas disponível até `origem−2h` e alvo em `origem+24h`. Ajuste, seleção
e avaliação são separados no tempo; normalizadores locais usam somente o ajuste.

O alinhamento usa timestamps: do fim do histórico ao alvo decorrem 26 horas, portanto
o índice da trajetória prevista é 25. A disponibilidade com atraso de duas horas e
o fuso físico permanecem hipóteses. Os experimentos meteorológicos anteriores têm
contratos próprios; a comparação M08/M09 usa somente geração passada.

**P2.** A fonte é o ESA Anomaly Dataset v2, Mission1, registro Zenodo
`10.5281/zenodo.15237121`, canais 50, 51 e 52. A
[documentação de origem e licença](satellite-anomaly-monitor/docs/Aula_M10_1_Contrato_Telemetria.md)
identifica os recortes derivados e a licença CC BY 3.0 IGO. Esta adaptação não
reproduz o benchmark ESA-ADB completo nem implica endosso da ESA.

A busca usa a última amostra anterior ou igual à decisão e limita sua idade a 180 s.
M10.1 usa grade de 90 s em 2007; M10.2/M10.3 usam 15 minutos, com ajuste em 2004–2007,
desenvolvimento em 2008–2010 e teste em 2011–2013. Rótulos retrospectivos ficam separados
das features; no ajuste, as anotações ajudam a definir a coorte. Ausência de anotação
não comprova normalidade. As unidades dos canais e a disponibilidade real de chegada
não são conhecidas; interpretação UTC e disponibilidade na medição são assumidas.

Recibos registram configurações, versões, hashes e métricas. Integridade do artefato,
compatibilidade com o contrato e atualidade da decisão são verificações diferentes.
Igualdade de uma execução não prova validade futura.

## Organização

```text
.
├── src/renewable_forecast/      # P1: dados, modelos, API e auditoria
├── notebooks/                  # Laboratórios e implementações NumPy
├── scripts/                    # Ambiente, execução e distribuição
├── tests/                      # Contratos, regras e integrações
├── config/                     # Configurações de monitoramento
├── deploy/                     # Templates do serviço em contêiner
├── infra/                      # Infraestrutura dos laboratórios Spark
├── data/                       # Referências e dados locais do P1
├── dist/databricks/             # Recorte e contratos de reprodução M07.3
├── docs/                       # Guias, revisões e evidências selecionadas
├── reports/                    # Resultados e pareceres do P1
└── satellite-anomaly-monitor/   # P2: src/satmon, scripts, notebooks, testes e dados
```

A [política de versionamento](docs/VERSIONAMENTO.md) distingue código, referências
curadas, recibos e artefatos regeneráveis. Dados brutos do P1, ambientes, bancos MLflow,
pesos, checkpoints e distribuições binárias locais não acompanham necessariamente o clone.
Confira recortes de referência e manifestos antes de executar cada laboratório.

## Instalação

Use **Python 3.12**. O pacote principal declara DuckDB, pandas, NumPy, PyArrow,
scikit-learn e MLflow em [pyproject.toml](pyproject.toml). Na raiz, em PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
renewcast --help
```

PyTorch, Spark/Delta, Docker e o runtime Chronos são requisitos específicos dos guias.
A instalação básica não baixa pesos nem prepara todos esses ambientes. O controlador
M09.3 usa ambiente privado e versões fixadas; o primeiro preparo requer rede.
O modo offline exige ambiente e snapshot já prontos.

## Executar a CLI do P1

Estes comandos pertencem ao fluxo inicial **h+1**, separado dos resultados h+24 ao final.
Disponibilize Parquets ONS compatíveis em `data/raw/`; a validação exige o esquema
de origem, além de tempo e geração.

```powershell
renewcast validate --raw-dir data\raw --output reports\data_quality.json
renewcast prepare --raw-dir data\raw --plant-id CJU_BA5EIGT --output data\processed\series.parquet
```

A série preparada deve ter `din_instante` e `val_geracao`, frequência horária,
sem timestamps duplicados ou lacunas. Com esse arquivo disponível:

```powershell
renewcast backtest `
  --input data\processed\series.parquet `
  --output-dir reports\backtest

renewcast tune --input data\processed\series.parquet

renewcast train `
  --input data\processed\series.parquet `
  --output models\hist-gradient-boosting-v1

renewcast predict `
  --model models\hist-gradient-boosting-v1 `
  --input data\processed\series.parquet
```

O backtest grava `predictions.parquet`, `fold_metrics.csv` e `summary.csv`.
O treino exige `reports/tuning/best_params.json`, produzido pelo tuning, e recusa
sobrescrever um modelo existente. Experimentos usam MLflow local (`mlflow_tracking.db`
por padrão, configurável por `MLFLOW_TRACKING_URI`).

## Executar os laboratórios

Os comandos partem da raiz e exigem os arquivos dos guias. A conferência pequena
do P2 não lê o ano inteiro nem ajusta detectores:

```powershell
python satellite-anomaly-monitor/scripts/executar_m10_1.py --verificar --autoria satellite-anomaly-monitor/notebooks/m10_sincronizacao_autoral.py
pytest tests/test_data_contract.py tests/test_features.py tests/test_supervised.py
pytest satellite-anomaly-monitor/tests
```

Para a comparação pré-treinada, preserve o recorte M07.3 e as saídas do baseline M08.3.
O comando reutiliza esses baselines e não os treina novamente:

```powershell
python scripts/executar_m09_3.py --autoria --offline --baseline-run-dir reports/neural/CJU_BA5EIGT/m08_3_gru/20261115T170309Z_90a6625f
```

Leia o [guia M09.3](docs/Explicacao_M09_3_Passo_a_Passo.md) para preparar o snapshot
antes de `--offline`. No P2, siga o [M10.2](satellite-anomaly-monitor/docs/COMECE_M10_2.md)
para gerar escores e o [M10.3](satellite-anomaly-monitor/docs/COMECE_M10_3.md) para congelar
e avaliar a política; M10.3 depende de um run M10.2 válido. Os roteiros distinguem
ajuste, reutilização e reserva, evitando alterar a política depois de ver o teste.

## Resultados e limites

### P1 — comparação h+24 em Windows/CPU

Fonte: [summary M09.3](reports/transformer/CJU_BA5EIGT/m09_3_pre_treinado/20261117T213329Z_3b201a01/summary.csv),
run `20261117T213329Z_3b201a01`, com baselines do
[run M08.3](reports/neural/CJU_BA5EIGT/m08_3_gru/20261115T170309Z_90a6625f/summary.csv).
São as mesmas 168 origens; erros e viés estão em MWmed. Viés = observado − previsto.
As três sementes são mostradas sem selecionar a melhor pela avaliação.

| Método | Semente | MAE | RMSE | Viés |
|---|---:|---:|---:|---:|
| Persistência d2 | — | 37,991646 | 55,434342 | −3,016872 |
| Linear 24h | — | 33,678664 | 44,938111 | +15,148681 |
| HGB 24h | 17 | 32,323956 | 44,221683 | +13,119039 |
| MLP 24h | 17 | 32,724828 | 44,019866 | +10,655947 |
| MLP 24h | 29 | 33,700811 | 44,892316 | +12,652757 |
| MLP 24h | 41 | 33,159788 | 44,069511 | +13,724280 |
| GRU 24h | 17 | 35,675970 | 45,200733 | +18,525120 |
| GRU 24h | 29 | 34,911227 | 43,816199 | +17,993098 |
| GRU 24h | 41 | 34,573202 | 43,066020 | +14,777710 |
| Chronos-Bolt Tiny, zero-shot | — | 31,340738 | 45,380136 | +2,962412 |

Chronos reduz o MAE em **3,04176%** frente ao HGB, com RMSE maior. O intervalo P10–P90
cobre 135/168 alvos (**80,3571%**), com largura média de 83,595237 MWmed. A inferência
dos 168 exemplos levou 0,19884 s, além de carga e aquecimento; o pico de 397,293 MiB
é do processo inteiro. A latência dos baselines não foi medida: esses tempos não
sustentam uma comparação de velocidade.

Decisão: Chronos é candidato de desenvolvimento por MAE; HGB permanece referência.
A semana já foi examinada e a sobreposição com o pré-treino não foi verificada.
Não há superioridade estatística ou aprovação para produção estabelecida.
Veja o [parecer integrado](reports/parecer_m09_pre_treinado.md) e o
[recibo completo](reports/transformer/CJU_BA5EIGT/m09_3_pre_treinado/20261117T213329Z_3b201a01/resultado.json).

### P2 — sincronização, rankings e transferência dos alarmes

M10.1 sincronizou 1.046.703 medições em 350.400 decisões; 350.346 tiveram os três canais
utilizáveis. Isso mede frescor na grade, sem atestar normalidade. Veja o
[recibo M10.1](satellite-anomaly-monitor/reports/m10_1/20261118T203614Z_7e13daae/resultado.json)
e o [parecer](satellite-anomaly-monitor/reports/parecer_m10_1.md).

No [run M10.2](satellite-anomaly-monitor/reports/m10_2/20261119T101049Z_253ff59f/resultado.json),
o ajuste usou 136.202 instantes e a comparação de desenvolvimento, 105.042:
3.909 positivos em oito IDs. AP avalia rankings de instantes, não probabilidade
de falha nem recall por evento.

| Escore | AP completa | AP sem `id_134`, sem reajuste |
|---|---:|---:|
| Robusto | 0,716427 | 0,356114 |
| PCA | 0,502013 | 0,017142 |
| Isolation Forest | 0,758149 | 0,324910 |

O ID retirado responde por **75,08%** dos instantes positivos. A sensibilidade muda a
coorte e a prevalência, mantendo os escores; evidencia a influência da duração dos eventos.
A [devolutiva M10.2](satellite-anomaly-monitor/docs/m10_2/Resposta_M10_2.md) explica
por que esse ranking não basta para escolher uma política operacional.

No [run M10.3](satellite-anomaly-monitor/reports/m10_3/20261123T195301Z_332fb306/resultado.json),
33 candidatos competiram somente no desenvolvimento. A política congelada usa
Isolation Forest, limiar **0,7199442558** e **duas confirmações consecutivas**.

| Medida | Desenvolvimento 2008–2010 | Teste 2011–2013 |
|---|---:|---:|
| IDs detectados / observáveis | 3/8 | 0/8 |
| Inícios de alarme | 15 | 0 |
| Pontos que atingiram o limiar | 2.822 | 0 |
| Escore máximo utilizável | 0,759400 | 0,716436 |
| Precisão por início avaliável | 3/13 | Indefinida: 0/0 |

O silêncio no teste decorre de nenhum escore alcançar o limiar; não comprova ausência
de anomalias. A política atende ao orçamento no desenvolvimento, mas falha em detectar
os oito IDs observáveis do teste. A [decisão M10.3](satellite-anomaly-monitor/docs/m10_3/Resposta_M10_3.md)
mantém **sem aprovação operacional** e propõe diagnosticar distribuição, canais e regimes.
O teste já consultado não pode ser reapresentado como nova avaliação final intocada.
