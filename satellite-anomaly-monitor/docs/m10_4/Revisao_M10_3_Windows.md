# Revisão M10.3 — Windows 20261123T195301Z_332fb306

**Aceita:** função e respostas da M10.3. Auditadas as onze saídas por SHA-256. O código Python colado reproduziu exatamente o hash registrado pelo laboratório. Recalculei os 33 cortes candidatos a partir dos escores originais de desenvolvimento; 29 passaram nos critérios. Uma implementação independente que detecta as fronteiras dos blocos concordou com todos os inícios do código autoral. Atribuição por ID, repetições, exposição e atraso também reconciliados. Nenhuma floresta precisou ser ajustada para esta revisão.

1. **Sequência:** índices 1, 5 e 8. O índice 3 inválido interrompe mesmo com escore finito, e o índice 6 reinicia por ficar abaixo do corte. Remover o slot 3 faz desaparecer o início original 5 e muda o significado de consecutividade.
2. **Exposição:** 101.133 slots equivalem a 1.053,46875 dias de 24 horas. 4/1.053,46875 = 0,00379698 inícios sem anotação por dia equivalente. Quinze inícios menos dois ignorados dão treze avaliáveis; três recebem primeiro crédito (23,08%). A mediana de 26,83 min descreve somente os três IDs detectados. Em teste (102.260 slots equivalentes a 1.065,20833 dias), a taxa fica em zero; precisão e atraso ficam indefinidos.
3. **0/8:** 0,716435965 < 0,719944256. Nenhum ponto passou. Alterar a confirmação para uma leitura não teria efeito. Diagnosticar distribuição e testar ablações é uma hipótese verificável. Escolher novo limiar em 2011–2013 impediria tratá-lo como teste intocado.

O laço mantém um único contador, é linear e marca o instante disponível da confirmação. A conversão para booleano funciona com as máscaras fornecidas pelo laboratório; num contrato mais amplo valide o tipo antes de converter, pois uma string não vazia como `"False"` se tornaria verdadeira. Isso não afeta as entradas auditadas.

[Auditoria em JSON](../evidencias_m10_4/Revisao_M10_3_Windows.json). O resultado permanece sem autorização operacional. A M10.4 reaproveita estes arquivos.
