# Defesa técnica M03-01 — seleção temporal

Responsável: Codex, implementação e análise assistidas em 25/11/2026. Esta solução é fornecida integralmente e não certifica autonomia pessoal.

O problema novo é prever geração MW em t+24h usando apenas história até t−2h. O alvo só está disponível em t+26h. Não basta dividir por origem: em cada fold removemos todos os rótulos com disponibilidade maior ou igual ao início da validação. O último rótulo de treino precede estritamente o corte; o ajuste final usa disponibilidade anterior a 01/07/2026. O scaler da Ridge é ajustado de novo exclusivamente no treino de cada fold. As três validações semanais de junho têm 168 origens cada, com treino expansivo e a mesma coorte para os oito candidatos.

A persistência é y(t−2h), último valor disponível no contrato. É um comparador simples, sem treino e sem custo de inferência significativo, mas não sabe antecipar mudanças. A MAE mede desvio absoluto em MW, alinhado ao custo simétrico linear desta seleção. RMSE e viés são diagnósticos adicionais; eventos com custos assimétricos são avaliados separadamente. Selecionar o melhor fold premiaria uma semana favorável: agregamos as 504 origens, ponderando cada fold por seu tamanho. Quantidade de features e ordem prévia resolvem empates.

O vencedor foi **HGB_lags24_calendar**, MAE de desenvolvimento **29.537623 MW**. O melhor aprendido foi **HGB_lags24_calendar**. Se a persistência vencer, mantê-la como vencedora evita transformar o estudo explicativo do melhor aprendido em recomendação de promoção. Os grupos, hiperparâmetros, cortes e regra de seleção foram escritos antes do ajuste em `M03-03/protocolo.json`. Não houve busca no teste. O artefato e o ranking estão congelados; outubro continua fechado nesta fase.

Há dependência temporal, uma única série e sazonalidade. As semanas de junho não representam toda a variabilidade anual. Setembro/2025 a agosto/2026 é desenvolvimento já acessível; agosto já apareceu em estudos h6/h1 e não é holdout intocado. Fuso físico, latência efetiva e cadastro operacional permanecem hipóteses/limites; preencher uma grade horária com NaN e usar apenas coortes completas evita tratar falta como geração zero. Nenhum resultado desta análise autoriza produção.

Evidências: `M03-03/candidatos.csv`, `folds.csv`, `predicoes_folds.csv`, `selection_manifest.json` e `ajuste_receipt.json`. As novas execuções não substituem os runs históricos aceitos.
