# M09.3 — revisão da execução Windows e do alinhamento recebido

17/11/2026 · Marlon A. Bomfim · Do ferro ao pró — Data Science

**Aceite técnico:** execução normal e função de alinhamento aprovadas no escopo recebido. Não é necessário repetir inferência ou treinamento para avançar. A decisão própria do aluno pode ser consolidada em um parecer curto; não foi anexado o parecer citado no script de empacotamento.

## O que foi conferido nesta sessão

O `resultado(1).json` identifica a execução **20261117T212230Z_965de3d1**. Os onze arquivos de saída anexados coincidem com os onze SHA-256 desse recibo. Recalculei as trinta métricas das dez variantes, com diferença máxima de 7,11 × 10⁻¹⁵. As 1.512 linhas dos nove baselines também coincidem com o `predictions(6).csv` recebido anteriormente, cujo hash é o esperado no protocolo.

A saída completa `[168,9,26]` do NPZ foi confrontada com as 4.368 linhas de trajetórias e os três quantis selecionados. Todas as 168 origens têm `history_end=origem−2h`, alvo `origem+24h`, lead 26 e índice 25. A função enviada em texto foi transcrita, executada nos cinco grupos de conferência e aplicada ao NPZ real; os resultados coincidem. A transcrição não é uma cópia binária do arquivo Windows e não certifica o hash desse arquivo.

A conferência de atenção anexada registra oito grupos e diferença PyTorch 4,44 × 10⁻¹⁶ no modo autoral. A implementação já havia sido executada na revisão anterior; não há tarefa de atenção a refazer.

## Resultado local, sem substituir o HGB pelo resultado Linux

| Método | MAE (MWmed) | RMSE (MWmed) | Viés observado − previsto |
| --- | ---: | ---: | ---: |
| Persistência d2 | 37,991646 | 55,434342 | −3,016872 |
| Linear 24h | 33,678664 | 44,938111 | +15,148681 |
| HGB 24h | 32,323956 | 44,221683 | +13,119039 |
| Chronos-Bolt Tiny P50 | **31,340738** | 45,380136 | +2,962412 |

O Chronos reduz o MAE frente ao HGB em **0,983218 MWmed (3,041763%)**, mas aumenta o RMSE em **2,619649%**. O viés médio cai, sem desaparecer. MAE menor e RMSE maior são compatíveis: a distribuição dos erros mudou, e o quadrado atribui mais peso aos desvios grandes. Essa comparação usa as mesmas 168 origens, não outra divisão ou um novo teste final.

Há 95 vitórias e 73 derrotas por erro absoluto, ou 56,55% de vitórias. Em sete blocos consecutivos de 24 origens, o ganho médio HGB−Chronos é:

| Primeiro instante da origem | Ganho médio (MWmed) |
| --- | ---: |
| 03/07 04h | +1,653875 |
| 04/07 04h | +13,035838 |
| 05/07 04h | −2,223152 |
| 06/07 04h | −1,706148 |
| 07/07 04h | +1,016331 |
| 08/07 04h | +1,627859 |
| 09/07 04h | −6,522077 |

Essa decomposição é descritiva, sem teste de significância ou seleção posterior do candidato. O ganho concentra-se especialmente no segundo bloco; três blocos pioram. Os horários permanecem no eixo sem fuso físico validado do pacote.

No maior ganho, origem 05/07 01h e alvo 06/07 01h, o observado é 168,1105, o HGB prevê 110,469087 e o Chronos 157,154236 MWmed: ganho de 46,685148 MWmed. Na maior perda, origem 09/07 22h e alvo 10/07 22h, o observado é 49,778, o HGB prevê 122,806078 e o Chronos 167,710175: perda de 44,904096 MWmed. Nenhum dos dois modelos deste benchmark recebe vento; não há base para atribuir esses erros ao NWP.

## Intervalos e custo observado

O intervalo bruto cobre **135/168 alvos (80,36%)**. Há vinte observações abaixo do P10 e treze acima do P90; as caudas são diferentes, mesmo com cobertura total próxima de 80%. A largura média é **83,595237 MWmed**, e o interval score é **160,086514**. Não houve clipping, recalibração ou cruzamento nos três quantis selecionados. A cobertura desta semana não demonstra calibração futura ou condicional.

O tempo registrado dos onze lotes é **0,1872815 s**, somando 168 origens. O pico de memória relatado é 434,23 MiB para o processo inteiro. Não compare esse tempo de inferência com segundos de treinamento de MLP/GRU. Instalação, download e carga são operações distintas. O modelo tem 8.652.672 parâmetros congelados; não houve ajuste local.

**Decisão técnica desta revisão:** manter Chronos e HGB como candidatos de desenvolvimento. Chronos oferece menor MAE e menor viés neste recorte; HGB conserva vantagem de RMSE. A evidência não justifica trocar o serviço operacional, afirmar superioridade geral ou escolher novas configurações usando esta mesma semana como se ela fosse inédita.

## Proveniência: duas execuções, dois alcances de auditoria

Os arquivos numéricos anexados pertencem à rodada **212230Z** e foram conferidos diretamente. O `auditoria_resultados.json`, o `registro_execucao.json` e os scripts auxiliares citam a rodada autoral **213329Z_3b201a01**. Seu protocolo, suas latências e seu HTML têm hashes diferentes, e seu `resultado.json` não foi anexado. O protocolo efetivamente recebido tem `authorship_sha256=null`: ele é da rodada normal.

Isso não invalida as contas nem a função recebida. Impede apenas afirmar que estes anexos reconstituem integralmente a segunda execução. Não mover, editar ou renomear recibos para fazer suas identidades coincidirem.

O empacotador recebido escreve uma lista fixa de comandos e códigos de saída; não executa esses comandos. Portanto esse registro é uma declaração produzida pelo script, não uma captura independente do processo ou prova dos dez testes citados. O script de auditoria, por outro lado, contém cálculos e validações reais; não foi reexecutado integralmente aqui porque exige a árvore local dessa segunda rodada. Nesta revisão foi usado um recálculo independente sobre os arquivos efetivamente recebidos.

O Parquet fonte de geração com o hash declarado, os pesos Windows e o arquivo binário autoral não foram anexados. A presente auditoria valida consistência dos resultados persistidos e preservação dos baselines, sem afirmar inspeção desses arquivos ausentes. A sobreposição com o corpus de pré-treino permanece desconhecida.

## Encerramento e próxima competência

Execução, matemática do alinhamento e comparação técnica foram recebidas e aceitas. Permanecem como consolidação didática a decisão do aluno e sua explicação do contraste entre os blocos aleatórios do M09.2 e os pesos pré-treinados usados aqui. Isso pode ser respondido em três parágrafos, sem novas execuções: qual candidato manter, o que a cobertura permite dizer e por que h24/d2 exige 26 passos.

A próxima prática é M10.1, no produto `satellite-anomaly-monitor`: dados reais ESA, sincronização causal, frescor e identidade dos eventos. CI remoto, shadow ao vivo e validação física dos contratos de disponibilidade do Renewcast continuam separados deste aceite.
