# M08.3 — execução de referência e verificação

Executado em 15/11/2026; run `20261115T163556Z_bd3adefd`. Ambiente Linux, Python 3.12.14, PyTorch 2.7.1+cpu, NumPy 2.3.5, pandas 2.2.3, scikit-learn 1.8.0. CPU, dois threads, redes float32. Este documento descreve trabalho executado; não substitui a execução Windows do aluno.

## Origem dos dados

Utilizado o pacote M07.3 do professor, preservado das etapas anteriores, com 8.760 horas de geração e 7.485 origens elegíveis. A geração havia sido reconstruída e conferida contra os dados reais entregues no laboratório temporal; não houve novo download ou fabricação de uma série sintética para este treino.

Package ID: `d0a487b16c9b40ab78661d901ddf52ff9fbe592f62d9ae0fda75352bcb4da87f`.

SHA-256 da geração: `b286eb4fb625cded4a59bcce0063081c714ca66422ec720ce4b4117ddf5e1fc3`.

SHA-256 do treino: `0aabb6829c0a3c7b6b0795a7f5e8447c4660859f8ce1610cb481a96c4b876f34`.

Esse pacote não é declarado binariamente idêntico ao Windows de Marlon. Cada execução do laboratório confere seus próprios arquivos contra o manifesto correspondente. Fuso físico, versões históricas da fonte e disponibilidade real continuam fora do alcance desta evidência.

## Execução

Três MLPs e três GRUs foram ajustadas com sementes 17/29/41. Linear e HGB foram ajustados nas mesmas 7.079 origens; persistência usa a última medição disponível. As redes selecionaram épocas em 168 origens anteriores à avaliação. Todos os checkpoints ficaram fixados antes das métricas finais nas mesmas 168 origens.

| Arquitetura | Semente | Melhor época | Parada | Tempo treino/avaliações por época (s) |
| --- | ---: | ---: | ---: | ---: |
| MLP | 17 | 8 | 16 | 1,12 |
| MLP | 29 | 20 | 28 | 2,01 |
| MLP | 41 | 15 | 23 | 1,68 |
| GRU | 17 | 23 | 31 | 9,36 |
| GRU | 29 | 38 | 46 | 13,97 |
| GRU | 41 | 24 | 32 | 9,63 |

MAE do HGB: 31,846768 MWmed. MAE mediano MLP: 33,159788; GRU: 34,911227. Todas as GRUs perdem em MAE para o linear e o HGB; duas vencem o HGB em RMSE. O protocolo não foi reajustado para fazer a GRU vencer. O relatório HTML e a aula discutem essa diferença entre critérios.

Os parâmetros das redes ocupam 3.332 bytes na MLP e 3.716 bytes na GRU em float32; isso não inclui gradientes, estados do otimizador, ativações ou bibliotecas. O pico residente observado foi aproximadamente 454 MiB para o processo inteiro. O tempo registrado de 39,03 s cobre o núcleo da execução até a preparação do relatório, não instalação, revisão ou empacotamento. Não é previsão do tempo Windows nem benchmark controlado.

## Conferências executadas

Onze grupos de contraprovas do pacote verificaram portas NumPy versus GRUCell; sequência de 24 passos; estado reiniciado; independência da ordem do lote; lote final menor; shapes; 929 parâmetros; avaliação ponderada; modos mistos e exceções; preservação de pesos/gradientes; rejeição de vazio/NaN/overflow. Maior diferença da célula: `2,220446049250313e-16`, abaixo de `1e-12`.

Nove grupos adicionais de auditoria conferiram hashes dos artefatos; execução da função M08.2 recebida; fronteiras e contagens; normalizadores recalculados diretamente no ajuste; pareamento e métricas das nove variantes; seleção e paciência; recarregamento dos seis checkpoints; invariância da janela a alterações futuras e preservação de lacunas; rejeição de uma implementação autoral incorreta. Os seis recarregamentos tiveram diferença zero em MWmed. HGB e coeficientes lineares também foram recarregados/conferidos pelo laboratório.

O recibo `verificacao_independente.json` registra os detalhes. As verificações não são nove ou onze provas de superioridade preditiva: são verificações do contrato de implementação e da consistência do experimento.

## Evidências incluídas e limites

A pasta `docs/evidencias_m08_3_professor/20261115T163556Z_bd3adefd/` contém a execução de referência: protocolo, partições, normalização, previsões, resumo, curvas, checkpoints, relatório e hashes. Ela está separada das execuções locais do aluno em `reports/neural/.../m08_3_gru/`.

O PowerShell foi revisado estaticamente; não foi executado em Windows nesta sessão. A medição nativa de pico de memória Windows também permanece a confirmar nessa plataforma. O núcleo Python e o caminho de conferência autoral foram executados em Linux. Não se aprovou operação, não se treinou em um novo holdout, não se alterou o modelo do serviço HTTP e não se declarou M08.3 concluído pelo aluno.
