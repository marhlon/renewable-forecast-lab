# M02-01 — contas resolvidas e aplicação

Demonstração assistida; avaliação independente pendente em `docs/roadmap_m00_m09/Avaliacao_Fundamentos.md`.

Em 10.000 oportunidades sintéticas: 90 verdadeiros positivos, 10 falsos negativos, 495 falsos positivos e 9405 verdadeiros negativos. Assim, P(evento|positivo) = 90/(90+495) = 0.153846153846. A sensibilidade de 90% é P(positivo|evento), outra condição.

Para X em {0,1,2} com probabilidades {0,5;0,3;0,2}: E[X] = 0×0,5+1×0,3+2×0,2 = 0.700000; E[X²] = 1,1; Var[X] = 1,1−0,7² = 0.610000.

Bernoulli descreve um indicador; Binomial(24,0,01) conta sucessos em 24 tentativas independentes com p constante (média 0,24; variância 0,2376); Poisson(0,24) seria outra hipótese para contagens raras sob taxa constante e incrementos independentes. Normal é uma hipótese possível para erro contínuo, sem garantir suporte não negativo para geração. Nenhuma distribuição é validada em dados ONS por esta conta. Sensores e horas correlacionadas não viram tentativas independentes por conveniência.

A população de 10.000 é uma tabela didática construída; uma amostra observada terá flutuação. A taxa-base usada aqui é conhecida por desenho. No uso real, é preciso estimá-la na população e no período pertinentes.
