# Plano fixado antes de gerar as diferenças

Responsável: Codex. Dados sintéticos, sem treino ou seleção de benchmark. O protocolo JSON é o registro de hipóteses e parâmetros.

Estimando: μ_d = E[perda_A−perda_B], em unidades de perda sintética. Positivo favorece B. Para cada um dos quatro candidatos, H0: μ_d ≤ 1; H1: μ_d > 1. A melhoria mínima relevante é 1. Não testar somente μ_d=0 e depois chamar uma melhoria menor que 1 de suficiente.

Desenho: 10 blocos independentes, com 24 leituras cada. Um deslocamento normal compartilhado gera dependência dentro do bloco; blocos e ruídos são independentes pelo gerador. O teste principal usa as 10 médias de blocos. O teste ingênuo com 240 horas é apenas uma contraprova de pseudorreplicação e não define a decisão.

Família congelada: quatro hipóteses unilaterais; alpha familiar 0,05, Bonferroni 0,0125 por teste. Reportar todos os resultados. Rejeitar H0 apenas se p de blocos < 0,0125. O IC unilateral inferior correspondente usa 98,75% por teste, não 95%. O resultado é exploratório/didático, sem operação.

Um p-valor não é P(H0|dados). Não rejeitar H0 não demonstra equivalência nem ausência de efeito. Significância não corrige um desenho inválido. Em dados reais, a independência dos blocos precisaria de defesa; blocos arbitrários não a garantem. Nenhum ajuste após o resultado desta rodada.
