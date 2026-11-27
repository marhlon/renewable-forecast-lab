# M05-03 — rampa de uma hora, com alvo próprio

25/11/2026 · modelos ajustados e congelados; avaliação ainda não executada

A variável deste estudo é a queda entre duas horas adjacentes: `rampa(t)=geração(t)−geração(t+1h)`. Valores positivos indicam queda; valores negativos, aumento. O evento binário é `rampa(t)>=22,77 MWmed`. Isso corrige o escopo de interpretação de eventos entre extremidades separadas por 26 horas: aquele rótulo não valida detecção de uma rampa de uma hora.

As entradas continuam respeitando atraso assumido de duas horas. Na origem `t`, o modelo conhece no máximo a geração de `t−2h`, e a rampa alvo só fica disponível em `t+3h`. Nem `geração(t)` nem `geração(t+1h)` entram como atributos. O alvo é conhecido apenas depois, para treino histórico ou avaliação.

Foram usadas as 28 variáveis de geração e calendário já escolhidas no estudo M03-03. Os parâmetros HGB ficaram fixados no protocolo integrado: 60 iterações e demais valores iguais aos outros estudos do bloco. Há dois modelos distintos: um regressor de erro quadrático para o valor da rampa, e um classificador para a probabilidade do evento. Eles foram ajustados sobre 7.244 origens, com rótulo de rampa disponível estritamente antes de 01/07/2026. O número difere do treino h24 porque o relógio de disponibilidade do alvo é de três horas, em vez de 26.

A regressão será comparada com rampa zero e com a última rampa efetivamente observada: `geração(t−3h)−geração(t−2h)`. Essa referência não consulta o valor atual ainda indisponível. O classificador será comparado com a frequência do evento no treino. O corte de classe é 0,5; para as saídas de regressão, a comparação de evento usa a queda de 22,77 MWmed. Não existe calibração Platt ou escolha de corte neste item. O orçamento de seis alarmes por dia pertence à política h24/26h de M05-02, e não será introduzido silenciosamente na rampa.

A avaliação terá as mesmas 695 origens dos outros dois estudos M05. Serão registrados MAE, RMSE e viés da rampa, além de Brier, log loss, AP e as contagens de acertos/falsos positivos/falsos negativos dos alarmes. As métricas por semanas fixas e a parte final de 23 horas ficarão separadas. Uma baixa frequência de eventos pode tornar o alarme em 0,5 silencioso mesmo com alguma ordenação probabilística útil; os números da avaliação é que permitirão verificar isso.

Código, fonte, seleção de variáveis, parâmetros e dois modelos foram congelados antes da obtenção do arquivo de avaliação. Os comandos de preparo e ajuste terminaram com código 0. O ajuste foi limitado a uma thread, sem usar seus tempos como comparação com o M03. Nenhum resultado reservado foi consultado até este ponto.

O estudo é retrospectivo e usa uma fonte publicada/revisada conforme consulta atual. Não demonstra disponibilidade histórica efetiva do ONS, fuso físico, operação contínua ou shadow ao vivo. A assistência técnica foi fornecida por Codex e está registrada, sem atribuição de autonomia ao usuário.
