# Bloco 1 — aplicação de engenharia e resultados

25/11/2026 · Renewcast/P1 · etapas 1–3

## 1. Resposta sobre o fechamento

O bloco passou a ser tratado como uma entrega de engenharia, conforme o esclarecimento do usuário: aplicar o código, executar as análises e explicar os resultados. As oito atividades que aguardavam respostas foram resolvidas como análises técnicas fornecidas. Não há prova, questionário ou resposta do usuário exigidos para aceitar essa entrega aplicada.

O aceite de engenharia cobre **14 itens**: M00-01, M01-01, M01-02, M02-01–05, M04-01, M06-01, M07-04, M08-01, M09-01 e M09-03. As quatro comprovações M04-02–05 permanecem no escopo **operacional**; seus relatórios e mecanismos foram produzidos, mas a evidência externa ainda é insuficiente para homologar operação.

Os recibos, protocolos e soluções anteriores foram preservados. As novas aplicações ficam em `reports/fechamento_m00_m09/bloco1_engenharia/`. O cadastro anterior e o esclarecimento de modo também estão arquivados ali. A aceitação de engenharia não é uma certificação de aprendizagem nem a aprovação de um serviço em produção.

## 2. De onde vêm os dados e as previsões

| Componente | Origem | Unidade / significado | Exemplo preservado |
| --- | --- | --- | --- |
| Histórico e alvo de geração | [ONS — Geração por Usina em Base Horária](https://dados.ons.org.br/dataset/geracao-usina-2) | `val_geracao`, MWmed, na referência horária do conjunto | `dist/databricks/CJU_BA5EIGT/m07_3/geracao.parquet` |
| Previsão de vento | NOAA GFS, acessado pelo [Open-Meteo Single Runs](https://open-meteo.com/en/docs/single-runs-api) | Velocidade em m/s e direção em graus, a 100 m | `data/external/weather/CJU_BA5EIGT/gfs_20260701T0000Z/` |
| Cadastro e pesos espaciais | ONS + SIGA/ANEEL | Identidades, coordenadas e capacidade instalada | `data/reference/CJU_BA5EIGT/asset_registry.csv` |
| Geração prevista, quantis e probabilidade de queda | Modelos executados no Renewcast | MWmed para geração/quantis; probabilidade entre 0 e 1 para evento | `reports/inference/`, `reports/probabilistic/`, `reports/events/` |

A fonte central informada pelo usuário é a origem da série usada pelo projeto. Ela não é o endpoint usado pelo código para obter vento previsto. O portal ONS ainda contém uma ressalva para certos grupos Tipo III que representam previsões; o nosso recorte é identificado como conjunto de usinas. Não generalizamos a classificação do recorte para todos os registros do portal.

A consulta meteorológica implementada está em [weather_runs.py](../../src/renewable_forecast/weather_runs.py):

```text
endpoint: https://single-runs-api.open-meteo.com/v1/forecast
models: gfs_global
hourly: wind_speed_100m,wind_direction_100m
wind_speed_unit: ms
timezone: UTC
run de referência: 2026-07-01T00:00
forecast_hours: 48
```

O pedido usa 15 pares de coordenadas. Eles correspondem a cinco células de grade distintas. Uma rodada normalizada contém 48 × 15 = **720 linhas**, sem que isso signifique 15 previsões meteorológicas espacialmente independentes.

O [metadata.json da consulta](../../data/external/weather/CJU_BA5EIGT/gfs_20260701T0000Z/metadata.json) registra a URL completa, parâmetros, coleta e hash. O `response.json` conserva a resposta bruta, o `weather_forecasts.csv` os valores normalizados e o `grid_mapping.csv` as células utilizadas. Foram localizadas 126 rodadas; 124 pertencem ao estudo h24. Os hashes das 126 respostas coincidem com os recibos.

A rastreabilidade detalhada e os caminhos de cada produto estão em [Origem_Dados_e_Previsoes.md](Origem_Dados_e_Previsoes.md), com [manifesto dos arquivos](../../reports/fechamento_m00_m09/bloco1_engenharia/fontes_manifesto.json).

## 3. Como vento se torna entrada de um modelo de geração

O código não interpreta 10 m/s como 10 MW. Primeiro, a seleção temporal procura uma rodada com validade igual ao alvo e disponibilidade elegível na origem. No cache histórico, essa disponibilidade foi construída pela hipótese de inicialização + seis horas.

Depois, o projeto usa a capacidade das 15 usinas, total de **227,7 MW**, para ponderar os valores meteorológicos. A direção meteorológica indica de onde vem o vento. O código calcula:

```text
u = -velocidade × sen(direção)
v = -velocidade × cos(direção)
peso_da_usina = capacidade_da_usina / capacidade_total
```

São cinco atributos: média ponderada da velocidade, dispersão espacial ponderada, componente u média, componente v média e média do cubo da velocidade. O termo cúbico tem unidade m³/s³ e **não é potência em MW**. Cobertura incompleta não vira vento zero: os atributos ficam ausentes conforme o contrato.

Nos estudos meteorológicos, esses cinco atributos se juntam a 27 atributos históricos/calendário, produzindo 32 entradas para os modelos. M08/M09, por sua vez, usaram apenas geração histórica; não receberam essas variáveis GFS. O HGB com 24 lags e o HGB com histórico + vento são experimentos diferentes.

Uma previsão pontual já existente é [143,6473739986 MWmed](../../reports/inference/CJU_BA5EIGT/h24_replay_20260801T0500Z/prediction.json), para o alvo histórico 02/08/2026 05h UTC sob a origem do replay 01/08/2026 05h UTC. Ela foi produzida pelo estimador local. Não veio como geração prevista do Open-Meteo e não é uma previsão emitida hoje.

## 4. Correção E51: geometria do vento

A função `validate_wind_geometry` em [weather_artifact.py](../../src/renewable_forecast/weather_artifact.py) procurava nomes por fragmentos de texto e pela ordem do dicionário. Isso podia confundir velocidade, componentes e o atributo cúbico.

Substituí a seleção pelas três chaves exatas:

```text
wind_speed_mean_ms
wind_u_mean_ms
wind_v_mean_ms
```

A verificação exige valores numéricos finitos, velocidade não negativa e:

```text
hypot(u_médio, v_médio) − velocidade_média ≤ 1e-8
```

A média dos vetores não pode superar a média das magnitudes além da tolerância. Componentes negativas são legítimas, pois indicam direção; velocidade negativa não é. `hypot` evita formar explicitamente quadrados intermediários muito grandes.

O caso velocidade 12, u 30 e v 0 é rejeitado, inclusive com a ordem das chaves invertida. A função preserva as entradas e a construção da linha de 32 atributos do pedido real. Foram aprovados **38 casos**; a integração usou somente JSONs e impediu treino e carregamento de pickle. O estimador e seus pesos não foram retreinados.

## 5. Bootstrap recuperado

[weather_gain_uncertainty.py](../../src/renewable_forecast/weather_gain_uncertainty.py) terminava em `rows = []`: faltavam o retorno do resumo e a CLI completa. A versão completa histórica não foi recuperada; a implementação foi reconstruída e identificada como outra versão.

Para cada emissão, o ganho é:

```text
|alvo − previsão_histórico| − |alvo − previsão_histórico_com_vento|
```

Um ganho positivo favorece o segundo modelo. O alvo e as duas previsões permanecem pareados. O sorteio ocorre em blocos consecutivos dentro de cada fold; quando chega ao fim, retorna ao começo do mesmo fold. Mantém-se o tamanho original da amostra de cada fold.

O agregado combina as réplicas com pesos proporcionais às contagens, antes de calcular os percentis. Não é uma média simples dos folds nem uma média dos limites dos intervalos. Na contraprova com três ganhos iguais a 1 e cinco iguais a 3, o agregado é:

```text
(3 × 1 + 5 × 3) / 8 = 2,25
```

A média simples das duas médias daria 2 e atribuiria peso excessivo ao fold menor. Outros casos conferem circularidade, pareamento, RNG local, validação, overflow e recusa de sobrescrever saídas. **59 testes passaram.**

A CLI grava resumo, parâmetros, versões e hashes. O bootstrap sobre as previsões reais permanece em M02-08, no bloco 2. Os testes desta reconstrução usaram exemplos pequenos e não geraram uma nova conclusão estatística sobre o ganho histórico.

## 6. SQL aplicado ao mês real

O recorte foi fixado em **novembro/2025**; não foi escolhido por desempenho de modelo. Foram executadas as consultas de qualidade, médias diárias, cobertura e LAG e comparadas integralmente com pandas.

| Medida | Resultado |
| --- | ---: |
| Registros e posições de calendário | 720 / 720 |
| Dias | 30 |
| Medições válidas | 720 |
| Valores zero informados | 49 |
| Valores nulos | 0 |
| Horas sem registro | 0 |
| Chaves duplicadas / linhas em quarentena | 0 / 0 |
| Cobertura dos dias | 100% |
| Média mensal | 28,2609791667 MWmed |

Os 49 zeros são valores preservados da fonte. Não foram usados para preencher ausência e não explicam sozinhos a causa física da geração zero.

Em 15/11, a soma dos 24 valores é 1.479,44; dividindo por 24, a média é **61,6433333333 MWmed**. As médias e contagens calculadas em SQL coincidem com pandas; a maior diferença numérica diária foi 8,88 × 10⁻¹⁶, compatível com a ordem das operações em ponto flutuante. As máscaras de valores ausentes coincidem.

O LAG de uma linha na série esparsa não significa automaticamente uma hora. Na série horária completa desse recorte, foram encontrados 719 pares dentro do mês. O primeiro LAG nulo é a fronteira da consulta: a hora anterior não estava no recorte, e isso não comprova lacuna na série original. Em features temporais, deve-se calcular a janela com contexto suficiente antes de filtrar o período avaliado.

Essa diferença foi aplicada em um suplemento com protocolo próprio: a consulta lê também 31/10 23h, calcula a janela e só depois filtra novembro. O resultado continua com 720 horas, mas passa a ter **720 pares LAG/delta**, com igualdade SQLite/pandas. A primeira hora de novembro tem 10,381 MWmed; a anterior tem 55,438 MWmed; o delta é **−45,057 MWmed**. O arquivo [lag_com_contexto.csv](../../reports/fechamento_m00_m09/bloco1_engenharia/M01-02/lag_com_contexto.csv) conserva essa saída, sem apagar a análise de 719 pares feita no recorte isolado. Isso corrige a fronteira da janela; não preenche uma lacuna inventada.

O caso pequeno com duplicidade aplica quarentena a todas as cópias da chave ambígua; não escolhe uma medição arbitrariamente. O calendário conserva dias sem dados, e somente contagens ausentes são preenchidas com zero. Média desconhecida continua nula.

As consultas, o diagnóstico, a conta manual e a análise dos relógios estão em [Diagnostico_SQL_Aplicado.md](Diagnostico_SQL_Aplicado.md).

## 7. Cálculos quantitativos executados

Estas contas usam cenários numéricos fixos, não uma nova avaliação do detector real ou do modelo eólico.

**Probabilidade condicional.** Em 20.000 oportunidades com 2% de eventos, sensibilidade de 85% e falso positivo de 3% entre os não eventos, a tabela executada tem 340 verdadeiros positivos, 60 falsos negativos, 588 falsos positivos e 19.012 verdadeiros negativos. Assim:

```text
P(evento | sinal positivo) = 340 / (340 + 588) = 36,637931%
```

Os 85% respondem a outra condição: sinal positivo dado que existe evento. Um escore alto ou uma sensibilidade alta não se tornam automaticamente alta probabilidade de evento após o sinal.

**Estimação e previsão.** Para [18, 20, 22, 24], a média é 21, a variância amostral é 20/3 e o erro-padrão da média é 1,29099445. Sob a hipótese Normal IID, com o valor t fornecido, o IC de 95% da média é **[16,89147988; 25,10852012]**. O intervalo de previsão de uma nova observação é **[11,81306973; 30,18693027]**. Ele é maior porque inclui a variação da nova observação além da incerteza da média.

No cenário separado de 72 leituras AR(1), com correlação 0,6, o tamanho efetivo aproximado é 18; o cálculo finito pela covariância conhecida deu 18,48128342. Isso ilustra por que 72 linhas correlacionadas não equivalem a 72 observações independentes; não é uma estimativa dessa dependência nos dados ONS.

**Hipóteses.** As seis diferenças médias de blocos fixadas no protocolo tiveram média 1,08333333 e erro-padrão 0,21972205. Contra H0: média ≤ 0,5, o teste unilateral retornou t=2,65486938, p=0,02258068 e limite inferior nominal de 0,64058286. Sob independência/normalidade das médias de blocos assumidas no caso, há evidência nominal de superar o efeito mínimo de 0,5. Não foram inventadas as 144 observações horárias que o cenário apenas mencionava.

Na outra família de três p-valores, Bonferroni usa 0,05/3=0,01666667. Somente 0,009 passa; 0,03 e 0,4 não passam. A família é separada do teste anterior.

**Regressão e estabilidade.** Para x=[−2,0,2] e y=[0,1,5], a matriz com intercepto tem shape (3,2), y tem (3,) e os coeficientes têm (2,). OLS retornou intercepto **2** e inclinação **1,25**. Com MSE dividida por n, λ=1/3 e intercepto não penalizado, Ridge retornou **[2; 10/9]**. O termo da equação normal é nλ=1.

No ponto inicial [0,0], o gradiente é **[−4; −20/3]**. Subtrair um pequeno múltiplo dele aumenta inicialmente os coeficientes. A MSE caiu de 8,6667 para 3,9674 no passo η=0,1; com η=1 subiu para 82,7407. Para essa quadrática OLS, a faixa estrita de convergência com taxa constante é 0<η<0,375.

Acrescentar a coluna 2x produz três colunas e posto 2. Há diferentes coeficientes com as mesmas previsões; a regularização não cria identificação causal de efeitos colineares. A média residual de ajuste próxima de zero também não demonstra generalização futura.

O [relatório quantitativo completo](Fundamentos_Aplicados_Resultados.md) contém as derivações. Foram aprovados quatro testes novos e 24 conferências analíticas nesta aplicação, preservando as demonstrações anteriores.

## 8. Registro, versões e auditoria

Os oito arquivos de versões v1/v2 do registro local foram encontrados e seus hashes coincidiram na leitura autorizada fora do sandbox. O problema observado sob o sandbox era de acesso; não houve restauração nem desserialização de modelos.

A auditoria M08/M09 preservou as saídas históricas e registrou três caminhos de código atuais diferentes dos hashes históricos. Isso não apaga os resultados antigos, mas impede chamar a árvore atual de cópia exata da execução antiga. As identidades permanecem separadas.

A rastreabilidade adicional identificou 78 artefatos de geração, meteorologia, cadastro, código e previsões. Hash preservado significa que os bytes comparados não mudaram; não autentica por si um horário de publicação nem prova validade futura.

## 9. Critério aplicado ao projeto

O cadastro conserva a versão anterior e os critérios formativos históricos. Para esta entrega, a classificação e a revisão passam a ser técnicas. Não há atribuição das soluções ao usuário como autoria independente.

```powershell
python scripts/verificar_roadmap.py --bloco 1 --gate engenharia
python scripts/verificar_entrega_bloco1.py
```

O primeiro comando exige os 14 itens aplicados do portão de engenharia. O segundo confere recibos, hashes e entregáveis, inclusive as versões anteriores preservadas.

O fechamento irrestrito de todos os 18 itens ou o portão operacional ainda devem apontar quatro pendências: fuso/borda do intervalo, publicação histórica da meteorologia, vigência cadastral e homologação point-in-time. O código bitemporal foi implementado e exclui vigências não comprovadas; isso não inventa as versões faltantes.

Não foi necessário abrir Docker ou outro aplicativo. Não foram feitos novos treinos de HGB/GRU/Chronos, atualização de pesos, emissão para hoje, contato com provedores ou implantação. Os blocos 2 e 3 não foram executados nesta consolidação.
