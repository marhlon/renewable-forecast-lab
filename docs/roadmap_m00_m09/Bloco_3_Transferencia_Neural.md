# Transferência neural aplicada no bloco 3

25/11/2026. Itens M08-02, M08-03 e M09-02. Solução, execução e interpretação fornecidas pelo Codex no modo de engenharia solicitado. Não houve resposta independente do usuário ou certificação de autonomia. Os critérios pedagógicos anteriores permanecem no cadastro histórico; esta entrega é técnica e aplicada.

Os protocolos em `reports/fechamento_m00_m09/bloco3_engenharia/<ID>/protocolo.json` foram registrados antes das verificações e dos cálculos desta rodada. Eles identificam código, versões, hipóteses, recorte, shapes antecipados e critérios. A reanálise do M08.3 usa previsões salvas de uma semana de desenvolvimento já examinada; os outros dois casos usam entradas sintéticas e pesos aleatórios. Não se treinou um novo modelo nem se utilizou outro mês para avaliar qualidade preditiva.

## M08-02: GRU e HGB nos números preservados

O run de 15/11/2026 `20261115T170309Z_90a6625f` conserva 168 origens de avaliação, três sementes GRU prescritas (17, 29 e 41) e HGB com os mesmos 24 lags de geração, sem meteorologia. A comparação é pareada por origem, verifica igualdade dos alvos, recalcula os erros e confere o SHA-256 de `predictions.csv` contra seu recibo histórico. Não houve novo ajuste, escolha retrospectiva de semente nem alteração do período aceito.

MAE atribui custo linear à magnitude do erro. RMSE calcula a raiz da média dos quadrados e dá peso maior aos erros grandes. Uma rede pode reduzir poucos erros grandes e aumentar vários erros médios: assim melhora RMSE e piora MAE. Para localizar essa situação, `perdas_por_origem.csv` contém todas as 504 comparações GRU/HGB (168 por semente), inclusive diferenças de erro absoluto e quadrático. O resultado também separa as cinco origens mais favoráveis à GRU em perda quadrática das outras 163; trata-se de diagnóstico retrospectivo, sem remover origens da métrica principal.

Nesta rodada o viés é `previsão − alvo`, portanto um valor negativo significa subestimação. O parecer histórico usa `observado − previsto`: seus números têm sinal oposto por definição. Para distinguir deslocamento de dispersão, `metricas.csv` inclui a raiz da média dos resíduos centrados. A identidade `RMSE² = viés² + média((erro−viés)²)` permite verificar que viés menor, isoladamente, não determina o RMSE. A faixa e o desvio entre três sementes descrevem sensibilidade à inicialização; não são intervalo de confiança, amostra de origens independentes nem resultado de um ensemble.

A regra de decisão previamente registrada mantém HGB como referência de desenvolvimento sob prioridade de MAE em CPU, quando as três sementes não oferecem ganho consistente. Priorizar RMSE ou custo de eventos extremos pode justificar outra hipótese de uso, mas requer uma política de seleção definida no desenvolvimento e confirmação posterior. Para mudar a decisão seriam necessários novos períodos com alvos/versões congelados, disponibilidade histórica verificável, custos de erro previamente declarados, comparação pareada sem escolher semente no teste e medição controlada de latência/memória. O custo de treino já registrado não mede latência de inferência. Nenhuma conclusão desta reanálise autoriza operação.

## M08-03: nova janela, lotes desiguais e estado

A adaptação troca a janela de 24 por 12 posições, o estado de 16 por oito coordenadas e utiliza 11 exemplos em três lotes de tamanhos 4, 4 e 3. Antes da execução foram antecipados entrada `[B,12,1]`, saída recorrente `[B,12,8]`, estado `[1,B,8]`, seleção da última camada `[B,8]` e previsão `[B,1]`. A GRU contém `24 + 192 + 24 + 24 = 264` parâmetros; a cabeça linear soma oito pesos e um viés, totalizando 273. Os pesos aleatórios testam o contrato, sem pretensão de prever geração.

A referência de MSE soma os 11 erros quadráticos e divide por 11. Fazer média das três médias por lote dá peso 1/3 ao lote de três, embora esse lote contenha apenas 3/11 dos exemplos. A saída salva contém tanto a conta correta como esse controle incorreto; o CSV preserva previsão, alvo e perda de cada exemplo.

O avaliador existente é reutilizado. Ele chama `eval()` e `no_grad()` e restaura individualmente as flags anteriores em `finally`. A contraprova começa com modos mistos, alguns gradientes preexistentes e outros ausentes. Compara pesos, `state_dict`, gradientes, flags e RNG antes e depois, inclusive quando um erro de shape ou NaN ocorre após um lote válido. Também testa loader vazio e janela incorreta. A avaliação não chama otimizador nem altera gradientes. A GRU recebe estado inicial zero em cada chamada: repetição e permutação do lote não devem ligar janelas distintas. As portas r/z/n são ainda conferidas em 12 passos contra a célula NumPy preservada, com os mesmos pesos e tolerância `1e-12`.

No caso temporal, a origem é t14 e a latência assumida é quatro passos horários. Os valores t−1 a t10 formam a janela de 12 posições, pois `evento+4 <= origem`. O alvo t15 fica separado. Alterar t11 e posteriores preserva a previsão quando o filtro de disponibilidade é aplicado. Um controle que inclui indevidamente t11..t14 altera a saída e demonstra que a invariância segura decorre do contrato de entrada. Esses tempos são sintéticos, sem alegação de publicação ONS observada.

## M09-02: mudar contexto e proteger a disponibilidade no prefixo

O contexto novo tem 12 posições, cinco consultas, duas origens por batch, 12 coordenadas de representação e três cabeças de quatro coordenadas. Em cada cabeça o score é `Q @ Kᵀ / sqrt(4)`. O softmax normaliza as chaves no último eixo. Na self-attention do encoder, Q/K/V vêm do histórico; na self-attention do decoder, vêm do estado das consultas; na cross-attention, Q vem do decoder e K/V da memória do encoder. Os shapes previstos incluem probabilidades `[2,3,12,12]`, `[2,3,5,5]` e `[2,3,5,12]`, respectivamente.

O caso trabalha diretamente com representações sintéticas já em E=12; não reaplica uma projeção escalar nem transforma o resultado em MWmed. Q/K/V são projeções afins distintas. A reconstrução explícita confere os scores escalonados, a máscara, a soma das probabilidades, o produto por V, concatenação das cabeças e projeção de saída. Não se interpreta peso de atenção como importância causal de uma medição.

Cada subcamada soma sua transformação à representação que recebeu, e aplica LayerNorm sobre as 12 coordenadas daquele token. A FFN aplica `12→24→12` com ReLU, separadamente em cada posição. O encoder tem atenção e FFN; o decoder tem self-attention, cross-attention e FFN. As duas camadas de cada pilha têm pesos próprios. O relatório verifica numericamente as equações de residual, normas e FFN em todas as camadas.

A fonte é indexada de 0 a 11, com disponibilidade assumida `j+4`. As cinco consultas têm origens sintéticas 7, 8, 9, 10 e 11; logo podem consultar diretamente fontes até 3, 4, 5, 6 e 7. `True` significa permitido na implementação preservada. O CSV salva essas 60 combinações, a disponibilidade e uma cabeça de atenção. Essas consultas são slots definidos para a contraprova de origens sucessivas; não são automaticamente cinco previsões horárias, horizontes h1..h5 nem teacher forcing.

Uma máscara apenas na cross-attention é insuficiente quando o encoder foi livre: a memória da posição 0 pode ter incorporado fontes 4..11, embora a primeira consulta só leia memórias 0..3. O teste altera fontes 4..11, que ainda não estavam disponíveis na origem 7. O controle de encoder livre mais cross mascarada muda a primeira saída. Com encoder causal em cada camada e cross limitada pela disponibilidade, essa primeira saída permanece igual. Alterar fontes 6..11 também preserva os três primeiros slots, cujas origens só permitem fontes até 5.

A proteção do prefixo do decoder é uma exigência distinta. Mantendo a memória, alterar as consultas 3 e 4 preserva as consultas 0..2 quando a self-attention é causal em todas as camadas. O controle com self-attention livre altera esse prefixo; os slots perturbados mudam também no caso causal, confirmando que o teste responde à intervenção.

Na previsão única emitida depois de todo o contexto ter chegado, um encoder livre pode combinar qualquer posição desse contexto conhecido. Exigir reconstrução de decisões de prefixos anteriores muda a pergunta: deve-se reconstruir a disponibilidade de cada decisão, truncar as entradas ou impedir caminhos indiretos por toda a composição. Causalidade de índice e disponibilidade são conceitos diferentes; latência de publicação obriga a máscara adicional de cross-attention mesmo com encoder causal.

## Reprodução e limites

Os comandos desta rodada usam o Python do ambiente `renewable-forecast`:

```powershell
python notebooks/bloco3_transferencia_neural.py --protocol
python -m pytest tests/test_bloco3_transferencia_neural.py -q
python notebooks/bloco3_transferencia_neural.py --run
```

O primeiro comando preserva protocolos existentes e recusa sobrescrevê-los. O runner confere que código e entradas continuam com os hashes registrados. Resultados, CSVs e recibo de execução ficam no diretório do bloco 3, separados dos runs históricos. Os pareceres de cada item registram os valores efetivamente executados. Esta entrega demonstra reanálise e contratos locais. Não comprova acurácia da adaptação aleatória, transferência independente de uma pessoa, CI remoto, shadow ao vivo, disponibilidade histórica real ou sustentação operacional.
