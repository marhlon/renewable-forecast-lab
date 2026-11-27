# M05-03 — prever a rampa média e detectar os extremos são tarefas diferentes

25/11/2026 · avaliação retrospectiva executada · entrega de engenharia

Este experimento tem alvo próprio de uma hora: `geração(t)−geração(t+1h)`. Uma queda de pelo menos 22,77 MWmed é um evento. Na origem, as entradas chegam somente até `t−2h`; o rótulo fica disponível em `t+3h`. Isso separa a rampa horária do evento anterior, que compara extremidades afastadas por 26 horas.

A execução única terminou com código 0. Foram usadas as mesmas 695 origens dos estudos de intervalo e probabilidade. Houve **39 rampas positivas**, prevalência de 5,6115%. O código, os modelos, o corte de classe 0,5 e o corte de queda 22,77 estavam congelados antes da obtenção dos dados de outubro.

## Regressão da rampa

| Modelo | MAE — MWmed | RMSE — MWmed | Viés observado menos previsto — MWmed |
| --- | ---: | ---: | ---: |
| HGB de rampa | 6,974245 | 12,029621 | 0,441065 |
| Rampa zero | 7,572565 | 14,543587 | −0,006223 |
| Última rampa observada | 12,829047 | 21,037676 | −0,006223 |

O HGB reduziu o erro agregado frente às duas referências. A referência de última rampa é `geração(t−3h)−geração(t−2h)`, sem consultar medições indisponíveis na origem. O HGB teve MAE menor que a rampa zero nas quatro semanas completas. Na parte final de 23 origens, piorou: 7,529193 contra 4,687826 MWmed. Esse trecho é pequeno e foi mantido separado.

Melhor erro médio não implica identificar as quedas extremas. Nenhuma previsão do regressor HGB atingiu o corte de 22,77 MWmed. Sua regra de alarme perdeu as 39 rampas, com zero falsos positivos. O custo hipotético FP=1/FN=4 foi 156, idêntico ao de nunca alarmar. A última rampa observada gerou 39 alarmes, mas apenas dois foram acertos: 37 falsos positivos, 37 falsos negativos e custo 185.

## Classificação do evento

| Probabilidade | Brier | Log loss | AP |
| --- | ---: | ---: | ---: |
| HGB de rampa | 0,043731 | 0,157831 | 0,328758 |
| Frequência fixa do treino | 0,053087 | 0,217157 | 0,056115 |

A classificação tem ordenação melhor que a referência constante no agregado. Isso não basta para o alarme fixado: **o corte 0,5 produziu zero alarmes e detectou 0/39 eventos**. O classificador e a frequência do treino tiveram o mesmo custo de alarme 156, embora suas probabilidades e suas APs sejam diferentes. A precisão de uma regra sem alarmes é indefinida e aparece vazia, em vez de ser inventada como zero ou 100%.

A AP do classificador também variou entre as semanas: 0,642242; 0,614459; 0,245596; 0,141259. Portanto, além de o corte fixo não detectar eventos, o ranking ficou mais fraco na segunda metade do recorte. Não foi feito outro ajuste para melhorar o resultado de outubro.

## Decisão e limites

A entrega de engenharia corrige o contrato do alvo, ajusta modelos separados e mede a mesma coorte com referências simples. A detecção com os cortes congelados falhou e não fica aprovada para operação. A regressão apresentou ganho médio, mas não sustentou a regra de detecção de extremos.

Um próximo estudo pode investigar perdas voltadas aos extremos, calibração ou seleção de corte com custos definidos, usando desenvolvimento separado e uma nova avaliação planejada antes de seus resultados. Esta conclusão não autoriza baixar o corte agora até obter acertos no mesmo outubro. O orçamento de seis alarmes por dia do outro item não foi aplicado silenciosamente à rampa: aqui foram mantidos os cortes próprios fixados no protocolo.

O arquivo é um snapshot consultado em 25/11/2026. A versão disponível em cada origem histórica, o fuso físico e a latência real de publicação continuam sem comprovação operacional. A execução é retrospectiva e não demonstra shadow ao vivo ou sustentação contínua.

[contrato_rampa.json](contrato_rampa.json) explicita a definição já protocolada; [rampas.csv](rampas.csv) preserva as 695 previsões; as três tabelas `metricas_*_rampa.csv` e o [resultado.json](resultado.json) registram as métricas. O [método](metodo_ajuste.md) detalha treino e referências. Implementação, execução e revisão foram fornecidas com assistência de Codex, sem atribuir desempenho independente ao usuário.
