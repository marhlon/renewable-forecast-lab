# Parecer da demonstração M02-02

Responsável: Codex, construção e execução assistidas. Dados exclusivamente sintéticos; protocolo anterior à geração.

O estimando é a média populacional μ; o estimador é a média amostral. Na amostra [8,10,12], média = 10.000000, s² = 4.000000, erro-padrão = 1.154701. Sob Normal IID, o IC de 95% da média é [5.031725, 14.968275]; o PI para uma nova observação é [0.063449, 19.936551]. A observação futura contém dispersão própria, por isso seu intervalo é maior. Confiança é uma propriedade de cobertura do procedimento, não probabilidade frequentista posterior do parâmetro fixo.

Em 2.000 amostras IID de tamanho 16, o viés Monte Carlo da média foi -0.003211; as médias dos estimadores de variância foram 3.748871 com divisor n e 3.998796 com divisor n−1. Os alvos teóricos são 3,75 e 4. O pequeno desvio de Monte Carlo não altera a identidade teórica; não se escolheu outra semente para melhorar a aparência.

Na simulação AR(1) estacionária com 48 observações e rho conhecido de 0,8, n_eff exato para a variância da média = 5.877538. A cobertura simulada do IC que ignora dependência foi 49.9500%; usando a covariância conhecida do gerador, 94.1500%. São 2.000 repetições; cobertura observada também tem erro Monte Carlo. Essa correção não foi estimada em dados reais e não substitui um bootstrap em blocos. O n_eff é específico desse estimando e desse modelo de covariância, não uma contagem universal de observações independentes.

Decisão: demonstração técnica executada; aguarda resposta e revisão humanas para fechamento formativo.
