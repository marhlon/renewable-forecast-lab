# M05-02 — probabilidades e orçamento causal de alarmes

25/11/2026 · ajuste e política congelados; avaliação ainda não executada

O evento deste item é `última geração disponível − geração alvo >= 22,77 MWmed`. A última geração é a de `t−2h`; o alvo é `t+24h`. Portanto, as duas extremidades ficam separadas por 26 horas. O rótulo não mede uma rampa horária. A tarefa de uma hora foi separada em M05-03.

Um HGB classificador foi ajustado sobre as 7.221 origens com alvo disponível estritamente antes de 01/07/2026. Os parâmetros e as 28 variáveis históricas são os mesmos fixados no protocolo integrado e no bundle M03-03. Este experimento usa somente geração passada e calendário; não reutiliza como se fossem iguais os classificadores meteorológicos de um estudo anterior.

Em uma amostra separada de 312 origens de 01/07 até 14/07 exclusivo, o HGB produziu probabilidades. Essas probabilidades foram limitadas ao intervalo `[1e−6, 1−1e−6]` apenas para calcular seu logit finito. Uma regressão logística com `C=1`, `max_iter=200` e semente 17 foi ajustada ao logit, contra os eventos reais. Esse é o calibrador Platt congelado. Sua existência não garante melhora de Brier, log loss ou confiabilidade em outro período. A frequência de positivos do treino é mantida como referência constante.

A política foi escolhida em outra amostra: 360 origens de 16/07 até 31/07 exclusivo. Os últimos rótulos dessa seleção tornam-se disponíveis, sob o relógio assumido, em 01/08 às 01h. Os protocolos e os selos são de novembro; não se afirma que a política estivesse pronta antes de esses rótulos existirem.

Foram comparados os cortes 0,05; 0,1; 0,2; 0,3; 0,4; 0,5; 0,6; 0,7; 0,8; 0,9; 1, além de nunca alarmar. Os custos hipotéticos são FP=1 e FN=4. O orçamento é executável: a cada dia do relógio de laboratório, somente os seis primeiros casos elegíveis em ordem cronológica podem gerar alarme. Não se olha o restante do dia para ordenar seus escores e escolher retrospectivamente os seis melhores.

O desempate escolhe menor custo, depois menos alarmes, depois maior corte. A política escolhida usa **corte 0,3 e seis alarmes por dia**. Na seleção, produziu 90 alarmes, 46 verdadeiros positivos, 44 falsos positivos e 43 falsos negativos. O custo foi `44 + 4×43 = 216`, ou 0,6 por origem. Isso é desempenho de seleção, não de outubro. A política está em `politica_congelada.json` e todos os candidatos em `candidatos_politica.csv`.

Antes da avaliação ficaram fixadas quatro regras, todas com o mesmo orçamento causal: HGB bruto em 0,5; calibrado em 0,5; frequência do treino em 0,5; e a política calibrada selecionada. As três fontes de probabilidade serão comparadas por Brier, log loss, AP e dez faixas fixas de confiabilidade. Os alarmes serão comparados por TP/FP/FN/TN, precisão, revocação, custo e utilização diária. Serão mantidos tanto os agregados quanto as semanas fixas.

Os arquivos de treino, o código, o calibrador e a política têm hashes no `freeze.json`. Não haverá reajuste de corte ou calibrador depois de ler a avaliação. O orçamento funciona nesta avaliação retrospectiva de arquivos; isso não comprova um serviço ao vivo. Os custos são relativos e hipotéticos, sem conversão financeira. A fonte de outubro, quando liberada, será um snapshot consultado agora, sem comprovar a versão publicada em cada origem histórica.

O ajuste foi executado com uma thread e terminou com código 0. Não é uma comparação de latência com o estudo M03. A implementação, a execução e a interpretação foram fornecidas com assistência de Codex; não certificam desempenho independente do usuário.
