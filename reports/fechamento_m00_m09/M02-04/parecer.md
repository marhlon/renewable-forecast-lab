# Parecer da demonstração M02-04

Responsável: Codex, construção e execução assistidas. Dados sintéticos e parâmetros fixados antes da execução.

Na conta manual, X tem shape (3,2), y (3,) e beta (2,). OLS devolveu [2.333333333333, 1.500000000000], MSE=0.055555555556; o gradiente no mínimo tem norma 1.18e-15. Ridge com lambda=1/3 devolveu [2.333333333333, 1.000000000000]. O intercepto não é penalizado. Para esta definição de perda, a equação normal contém n×lambda; omitir n muda o problema. O gradiente em um ponto fora do mínimo diferiu das diferenças finitas em no máximo 1.46e-09.

Com colunas x e 2x, o design tem posto 2 para três parâmetros. Somar [0,2,−1] aos coeficientes não muda a previsão, com diferença máxima observada de 8.88e-16. A solução de norma mínima retornada pela SVD é uma convenção, não identificação de efeitos separados. Ridge regulariza essa ambiguidade; não cria identificação causal.

Resultados do desenho temporal sintético, com ajuste nas primeiras 160 linhas e avaliação descritiva nas 80 seguintes:

- OLS/ajuste: RMSE=0.964278; média residual=0.000000; correlação lag1=0.804124.
- OLS/posterior_sintetico: RMSE=1.104885; média residual=-0.125632; correlação lag1=0.865756.
- Ridge/ajuste: RMSE=0.999256; média residual=0.000000; correlação lag1=0.780011.
- Ridge/posterior_sintetico: RMSE=1.128576; média residual=-0.084247; correlação lag1=0.844138.

O gerador impõe erros AR(1) com rho=0,8 e x independente dos erros. A dependência aparece nos resíduos e invalida inferência que trate as 240 horas como observações IID. OLS pode manter ausência de viés dos coeficientes sob exogeneidade, mas a fórmula usual de erro-padrão IID não fica justificada. Não foram publicados p-valores ou intervalos ingênuos dos coeficientes. Média residual próxima de zero no ajuste com intercepto é uma propriedade algébrica; não comprova ausência de viés futuro. A coluna Durbin–Watson é descritiva, sem p-valor ou teste formal neste laboratório.

Nenhuma garantia de normalidade, homocedasticidade, exogeneidade ou causalidade é estabelecida apenas por um gráfico ou por RMSE. No caso real, investigar fonte, omissão de variáveis, dependência e mudança de regime é parte do contrato. Aqui não houve busca de lambda, treino de benchmark histórico nem decisão operacional.

Decisão: demonstração técnica executada. A prova nova e a revisão humana continuam pendentes; esta execução não valida autonomia.
