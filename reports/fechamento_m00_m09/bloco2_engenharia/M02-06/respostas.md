# Perda, quantil e decisão — respostas aplicadas

25/11/2026 · interpretação fornecida com assistência de Codex

## 1. Por que a melhor previsão depende da perda?

Com custos iguais de subestimar e superestimar, a perda é o erro absoluto. Nas 168 origens arquivadas, Chronos P50 tem MAE de 31,340738 MWmed; HGB, 32,323956 MWmed. Quando subestimar custa quatro vezes mais, o custo médio passa a 82,795464 para P50 e 100,488448 para HGB. Usar P80 dá custo 58,740425, embora aumente o MAE para 39,016937 MWmed. A ação mais alta evita parte dos erros mais caros, pagando mais pelos erros do outro lado. Isso não torna seu MAE melhor.

Se `r = observado − ação`, a perda é `cu × max(r, 0) + co × max(−r, 0)`. Seu mínimo populacional é um quantil de ordem `cu / (cu + co)`, sob esse contrato de custo. Assim, 4:1 aponta para P80, 1:4 para P20 e 1:1 para P50. Quantis estimados pelo modelo ainda podem estar incorretos ou descalibrados; a fórmula não elimina esse risco. Nesta semana, P20 apresentou o menor custo observado no cenário 1:4: 54,573165.

## 2. Como custo e probabilidade definem o corte do alarme?

Para probabilidade `p` do evento, alarmar tem custo esperado `cFP × (1 − p)`; ficar em silêncio, `cFN × p`. Alarmar é preferível quando `p >= cFP / (cFP + cFN)`. A igualdade permite qualquer uma das ações pelo custo esperado; o contrato usa `>=`.

Com FP=1 e FN=4, o corte é 0,2. Nas 504 emissões arquivadas, HGB com corte 0,5 teve 74 acertos positivos, 35 falsos positivos e 39 falsos negativos: custo `35 + 4 × 39 = 191`. No corte 0,2, teve 90 acertos positivos, 66 falsos positivos e 23 falsos negativos: custo `66 + 4 × 23 = 158`. O custo caiu, mas os alarmes passaram de 109 a 156. O corte 0,2 não satisfaz o orçamento histórico de 120 alarmes e não substituiu a política salva. Tampouco há prova de calibração operacional das probabilidades.

## 3. O que pode ser concluído e o que precisa ser testado depois?

O resultado comprova a aplicação correta dos custos às previsões salvas, não uma economia operacional ou desempenho em dados novos. As 168 origens da previsão contínua e as 504 origens do classificador pertencem a estudos diferentes. O evento mede queda entre extremidades separadas por 26 horas, não uma rampa horária. As probabilidades vieram do `p_event` arquivado; não foram deduzidas de P10/P50/P90 ou de três quantis.

Para uma decisão nova, devem ser congelados os custos, a definição do evento, a política de capacidade, o corte e a rotina de avaliação antes de uma janela futura. É preciso acompanhar custo, quantidade de alarmes, falsos negativos, calibração e estabilidade temporal. Sete blocos de 24 emissões mostram variação nesta amostra, mas não são sete experimentos independentes. A consulta a esta semana não pode ser convertida em um teste futuro intocado.

Estas são respostas técnicas entregues integralmente. Não foram recebidas como explicação independente do usuário.
