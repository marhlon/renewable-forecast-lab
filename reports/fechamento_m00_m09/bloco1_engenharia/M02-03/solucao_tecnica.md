# Solução técnica assistida — M02-03

Responsável pela implementação e execução: Codex. Aplicação solicitada pelo usuário; não é resposta independente atribuída ao aluno.

## M02-03 — efeito relevante, blocos e multiplicidade

### Teste sobre as seis médias fornecidas

O ganho é `perda_A−perda_B`: positivo favorece B. O alvo é μ_d, sua média populacional. O efeito mínimo relevante foi fixado em 0,5; portanto H0: μ_d≤0,5 e H1: μ_d>0,5. Os números `[0.2,1.4,0.9,1.8,1.2,1.0]` já são **médias de seis blocos independentes**, não seis horas selecionadas de uma série.

```text
soma(d) = 6,5
média = 13/12 = 1.083333333333
s² entre blocos = 869/3000 = 0.289666666667
SE = sqrt(s²/6) = 0.219722046636
t = (média−0,5)/SE = 2.654869378222; graus de liberdade = 5
p unilateral = 0.022580683718
limite inferior95%, usando t dado=2,015048
             = 0.640582862704
```

O t exato da biblioteca foi 2.015048373333; o limite correspondente é 0.640582780675. A diferença está dentro do arredondamento previsto. O limite inferior é maior que 0,5 e o p é menor que 0,05; **rejeitamos H0 no teste nominal especificado**, sob normalidade e independência dessas médias. Há evidência, nesse desenho, de ganho médio superior ao mínimo relevante. Não se demonstrou superioridade de um modelo Renewcast real, causalidade ou transferência para outro período.

### Por que não usar automaticamente as 144 horas

Para o teste t IID aplicado a 144 valores, seria necessário justificar independência e a distribuição/condições apropriadas desses valores. Horas do mesmo bloco podem compartilhar estado, regime ou erro; a contagem de linhas não é uma justificativa. A alternativa é tratar a estrutura de covariância ou manter uma unidade de inferência adequada, como as médias de blocos independentes assumidas na questão. Como as 144 observações originais não foram fornecidas, não foram replicadas artificialmente as médias para produzir uma falsa série horária nem calculado um teste “horário” sem dados.

### Outra família de três hipóteses

Esta é uma pergunta separada: os p-valores fornecidos são 0,009; 0,03; 0,4. Com alpha familiar de 5% e três testes, Bonferroni fixa `0,05/3 = 0.016666666667` por teste. **Somente H1, com p=0,009, passa**. H2 e H3 não passam. A família e o denominador são três; não se escolhe apenas o menor p e depois se declara que só houve um teste. Não é necessário assumir independência entre os três para o limite Bonferroni, mas os p-valores individuais precisam ser válidos.

O teste das seis médias e essa família de p-valores foram mantidos distintos porque o enunciado diz “em outra família”. Nenhum p-valor adicional foi inventado para completar uma comparação.

### Não rejeição e equivalência

Não rejeitar H0 não demonstra equivalência: pode refletir pouca precisão ou baixa potência. Uma pergunta de equivalência exige margem inferior/superior relevante, hipóteses próprias e um procedimento como dois testes unilaterais ou intervalo compatível, escolhidos antes do resultado. Também exige unidade, exposição e dependência apropriadas. O p-valor não é P(H0|dados), e significância não corrige um desenho inválido.
