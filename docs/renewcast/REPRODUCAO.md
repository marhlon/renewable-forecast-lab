# Reprodução e conferência do Renewcast

Este guia separa a leitura das evidências curadas, a conferência do pacote local completo e os fluxos que fazem novas execuções. Os números da apresentação vêm da avaliação final retrospectiva de setembro/2026, identificada em [FONTES.md](FONTES.md). A revisão editorial de 27/11/2026 não instalou dependências, baixou dados, treinou ou executou inferência.

## Ler a evidência curada

Os seis arquivos em [evidencias](evidencias/fontes_editoriais.json) preservam os bytes de summary, métricas de intervalos, bootstrap agregado, resultado, protocolo e congelamento. Permitem conferir os números publicados e os critérios, mas não contêm todos os alvos, previsões, modelos e entradas necessários para uma reprodução integral.

O resultado de 671 origens não tem campo `run_id`; diretório, timestamp e hash o identificam. As 168 origens do estudo anterior têm runs próprios e não são a mesma partição. Setembro e outubro já foram examinados e devem continuar assim identificados.

## Conferir o pacote local completo

Na estação Windows registrada, o ambiente principal usou Python 3.12.13, NumPy 2.5.3, pandas 3.0.5 e PyArrow 25.0.1. O [pyproject.toml](../../pyproject.toml) declara Python `>=3.12,<3.13` e faixas das dependências principais. Não existe `environment.yml` na raiz.

É necessário ter o ambiente `renewable-forecast` já preparado, as fontes do bloco 3 e todos os arquivos dos manifestos nos caminhos relativos registrados. A partir da raiz:

```powershell
conda activate renewable-forecast
python -X utf8 scripts/verificar_roadmap.py --bloco 3 --gate engenharia
python -X utf8 scripts/conferir_bloco3.py
```

O primeiro verificador confere estado, critérios, revisão, dependências e identidades documentais. O conferidor recalcula métricas e verifica artefatos salvos, sem carregar modelos ou inferir. Gera um recibo novo em `reports/fechamento_m00_m09/bloco3_engenharia/reverificacoes/` e preserva a auditoria anterior.

Apesar de não carregar modelos, o auditor exige que eles existam para conferir seus hashes. Também lê Parquet, portanto precisa de um motor compatível como PyArrow. A seleção curada não satisfaz sozinha esses pré-requisitos.

| Grupo necessário | Exemplos de caminhos relativos | Situação observada |
| --- | --- | --- |
| Fontes de conferência | `scripts/conferir_bloco3.py`, `auditar_bloco3.py`, `conferir_ci_remoto_bloco3.py`, `verificar_roadmap.py` | Presentes localmente; fontes novas fora do índice Git na inspeção |
| Cadastro e relatórios | `config/roadmap_m00_m09.json`, `reports/fechamento_m00_m09/bloco3_engenharia/` | Presentes no workspace; não presumir presença no clone |
| Fonte e derivados | `data/raw/bloco3_locked/`, Parquets intermediários e resultados de dados | Brutos e diversos Parquets ignorados |
| Pacotes de modelos | Bundles dos blocos 2/3 e checkpoints neurais anteriores | Vários `.joblib`/`.pt` ignorados |
| Chronos | `models/pretrained/chronos-bolt-tiny/` na revisão fixada | Pesos locais ignorados |
| Ensaios de integração contínua | Cópia isolada e logs reais referenciados pelo auditor | Cópia e logs ignorados; recibos/manifestos identificam a origem |

Um clone não recebe arquivos ignorados ou arquivos locais ainda não versionados. Se uma entrada faltar, a conferência deve parar. Não remover exigências de hash nem criar recibos substitutos. É necessário disponibilizar o pacote de evidências autorizado e verificar sua identidade.

## Instalação básica e fluxo inicial h+1

O caminho de instalação já documentado para o pacote principal, em PowerShell, é:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
renewcast --help
```

Esses comandos são instruções; não foram executados nesta edição. A instalação não obtém automaticamente dados ONS, checkpoints, PyTorch ou o runtime Chronos. As faixas do manifesto não são um lock integral do ambiente medido.

Com Parquets ONS compatíveis já disponíveis em `data/raw/`, o fluxo inicial usa comandos existentes da [CLI](../../src/renewable_forecast/cli.py). O ajuste exige histórico suficiente: o tuner atual requer pelo menos **3.361 linhas com atributos**, além das observações necessárias ao contexto. Um único mês de 720/744 horas não basta.

Escolha um identificador ainda não usado. O bloco abaixo interrompe antes da execução se qualquer destino já existir; backtest e tuning não têm proteção própria contra sobrescrita. Esta é uma nova experiência h+1, com treino, e não foi executada nesta revisão.

```powershell
$rodada = 'repro_h1_20261127_01'
foreach ($destino in @("reports/$rodada", "data/processed/$rodada", "models/$rodada")) {
    if (Test-Path -LiteralPath $destino) { throw "Destino existente: $destino. Escolha outra rodada." }
}
New-Item -ItemType Directory -Path "reports/$rodada", "data/processed/$rodada" | Out-Null
renewcast validate --raw-dir data/raw --output "reports/$rodada/data_quality.json"
if ($LASTEXITCODE -ne 0) { throw 'Falha na validação; interrompa a rodada.' }
renewcast prepare --raw-dir data/raw --plant-id CJU_BA5EIGT --output "data/processed/$rodada/series.parquet"
if ($LASTEXITCODE -ne 0) { throw 'Falha na preparação; interrompa a rodada.' }
renewcast backtest --input "data/processed/$rodada/series.parquet" --output-dir "reports/$rodada/backtest"
if ($LASTEXITCODE -ne 0) { throw 'Falha no backtest; interrompa a rodada.' }
renewcast tune --input "data/processed/$rodada/series.parquet" --output-dir "reports/$rodada/tuning" --experiment "renewable-h1-$rodada"
if ($LASTEXITCODE -ne 0) { throw 'Falha no tuning; interrompa a rodada.' }
renewcast train --input "data/processed/$rodada/series.parquet" --params "reports/$rodada/tuning/best_params.json" --output "models/$rodada" --experiment "renewable-h1-$rodada"
if ($LASTEXITCODE -ne 0) { throw 'Falha no treino; interrompa a rodada.' }
renewcast predict --model "models/$rodada" --input "data/processed/$rodada/series.parquet"
if ($LASTEXITCODE -ne 0) { throw 'Falha na previsão; preserve os registros da rodada.' }
```

Validate exige o esquema de origem. Prepare produz `din_instante` e `val_geracao`; frequência, duplicidade e lacunas precisam respeitar o contrato. Train recebe explicitamente os parâmetros do tuning dessa rodada e também recusa sobrescrever modelo existente. Conferir o retorno de cada comando e interromper em caso de erro antes de seguir.

Esse fluxo é **h+1**. Ele não reproduz a tabela h+24 de setembro. Seus resultados permanecem separados.

## Chronos e benchmark final h+24

O [guia histórico M09.3](../Explicacao_M09_3_Passo_a_Passo.md) descreve o ambiente privado, snapshot fixado, alinhamento e execução de 168 origens. Seu [lock](../requirements_m09_3.lock.txt) usa NumPy 2.3.5/pandas 2.2.3, diferentes dos mínimos do pacote principal. Não instalar esse lock por cima do ambiente principal. Modo offline exige ambiente e snapshot completos; o primeiro preparo dos pesos requer rede fora desta revisão.

Setembro reutiliza modelos e escalas congelados, além de alternativas ajustadas anteriormente. O [protocolo](evidencias/protocolo.json) e o [congelamento](evidencias/congelamento_final.json) identificam a rodada e 29 arquivos. Há bundles anteriores, escaladores, calibradores, política e pesos. Os cortes de ajuste e as entradas das famílias não são idênticos.

`notebooks/bloco3_benchmark.py executar-final` baixa a fonte e faz inferências; não é comando de leitura. `sintetizar` depende dos artefatos congelados e recusa saída final já existente. Nenhum deles deve ser executado sobre a rodada salva apenas para abrir seu resultado.

Uma repetição integral precisa de pacote completo, ambientes compatíveis e destino independente. O runner atual tem caminhos fixos e chama `.venvs/m09_3_chronos/Scripts/python.exe`; não oferece uma reprodução integral portátil em clone novo. Adaptar destinos e caminhos seria alteração de código fora desta edição. Não apagar resultados para liberar o comando.

A execução preservada falhou ao imprimir caracteres em CP1252 depois de salvar previsões. A recuperação foi apenas da síntese UTF-8. Em futura execução autorizada, o encoding do pai e dos filhos precisa ser definido antes da chamada, conforme o [relatório](../roadmap_m00_m09/Relatorio_Engenharia_Bloco3.md).

## Limites e documentação preservada

Faltam comprovações externas de fuso/intervalo ONS, latência histórica e versões cadastrais. A hipótese de duas horas não é uma chegada observada. Os estudos meteorológicos usam NOAA GFS via Open-Meteo, enquanto a comparação apresentada usa geração/calendário. Consulte a [rastreabilidade](../roadmap_m00_m09/Origem_Dados_e_Previsoes.md).

O [CI remoto dos contratos](../roadmap_m00_m09/Revisao_CI_Remoto_Bloco3.md) foi demonstrado em dois runs, sem merge/deploy; não recompõe o pacote inteiro nem comprova observação contínua ao vivo. API e distribuição local têm aceites próprios. O monitor de telemetria possui [README independente](../../satellite-anomaly-monitor/README.md).

O [consolidado M01–M09](../roadmap_m00_m09/Consolidado_M01_M09.md) reúne o trabalho. Os relatórios dos [blocos 1](../roadmap_m00_m09/Relatorio_Engenharia_Bloco1.md), [2](../roadmap_m00_m09/Relatorio_Engenharia_Bloco2.md) e [3](../roadmap_m00_m09/Relatorio_Engenharia_Bloco3.md) preservam protocolos, revisões, resultados negativos e atribuições. A [política de versionamento](../VERSIONAMENTO.md) continua vigente. Código, métricas, autoria, licença e política experimental não foram alterados.
