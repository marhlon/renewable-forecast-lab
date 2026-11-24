# Aula 02 — Ablação que responde uma pergunta

A pergunta é: *qual diferença faz retirar um canal, se eu continuar a avaliar as mesmas origens e os mesmos IDs?* Isso não pode ser respondido removendo uma coluna de um vetor já esperado por um modelo de três entradas. Ajustamos uma nova floresta de duas entradas. Mantemos as mesmas 136.202 linhas elegíveis de 2004–2007, escolhas da floresta, centragem e escala de cada canal calculadas no ajuste. Repetimos a comparação em três sementes pré-declaradas, 17, 29 e 41. A referência original (três canais, 17) usa os escores já persistidos.

### Por que não liberar mais instantes ao retirar um canal?

Se o canal retirado estava ausente, a floresta de duas entradas poderia atender mais instantes. Isso seria uma hipótese diferente, sobre **cobertura do serviço**. Para isolar o efeito do conjunto de entradas, exigimos nesta rodada os três canais utilizáveis para todos os modelos e preservamos a grade. O rótulo agrupa as anotações dos três canais, inclusive do canal retirado; do contrário a definição de sucesso mudaria junto com o modelo. Uma medição distinta para disponibilidade deve contar explicitamente os novos instantes e IDs cobertos.

### Corte e ranking medem coisas diferentes

O escore da floresta é uma medida de raridade do modelo; 0,72 não significa 72% de chance de anomalia. Com menos canais ou outra semente, o escore muda de escala. Usamos o quantil .9995 com a regra `higher` no desenvolvimento particular de cada variante. Isso escolhe um valor da amostra; **não garante que 0,05% dos pontos passem**. No desenvolvimento da referência, **2.787 dos 2.822 pontos** acima ou no limiar estavam exatamente no valor do corte. A série também tem dependência temporal, então número de pontos no corte e número de inícios não são proporcionais. Um orçamento comum precisa ser conferido com a taxa medida, mesmo com o mesmo quantil.

| Variante, semente 17 | AP dev | IDs dev | Corte | Pontos no corte, 2011–2013 | S2 em 2011–2013 | IDs 2011–2013 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Três canais | 0,758149 | 3/8 | 0,719944 | 0 | 0,638230 | 0/8 |
| Sem 50 | 0,745271 | 2/8 | 0,748468 | 0 | 0,693513 | 0/8 |
| Sem 51 | 0,738713 | 2/8 | 0,722118 | 2 | 0,689846 | 0/8 |
| Sem 52 | 0,746365 | 3/8 | 0,720127 | 4 | 0,691564 | 0/8 |

“Pontos no corte” inclui os que passaram. Sem 51 e sem 52 conseguiram picos mas nenhum par acima do corte; no original nem o pico passou. Essa diferença de mecanismo não é recuperação. Para detectar com uma leitura nessas ablações, ainda seria necessário verificar **onde** os picos caem, além da carga gerada.

A AP ordena **instantes**, mede qualidade do ranking sem fixar uma regra de alarme e depende da prevalência. No desenvolvimento a referência tem AP=0,758149 e prevalência de instantes positivos anotados de 3,72%. Em 2011–2013, AP=0,000756 contra prevalência de 0,0528% (AP do escore constante). Isso documenta que o ranking também ficou pouco útil neste recorte. As anotações têm duração e representatividade diferentes; uma queda de AP entre períodos não estima, sozinha, o efeito de uma mudança física. Os IDs são oito em ambos os períodos, mas ocupam quantidades muito diferentes de slots.

### Onde há evidência de diferença de canais?

Abra `perfil_canais_ano.csv`, que conserva a escala do ajuste, e `associacao_canais_ano.csv`. Exemplo na coorte utilizável sem anotação: a mediana normalizada do canal 51 passa de **0,2531** em 2009 para **0,8434** em 2012. O P90 do mesmo canal cai de 1,8552 para 1,3493. A correlação de postos entre 50 e 51 passa de cerca de 0,9676 para 0,9535. Há mudança de forma e associação neste recorte; não temos regime físico, unidades ou causa da mudança. Os anos de desenvolvimento também são distintos: na coorte sem anotação, a mediana do escore em 2010 (0,6781) já destoava de 2009 (0,4816).

Compare os mesmos IDs com `mudancas_por_id.csv`. Retirar 50 perdeu `id_145` no desenvolvimento nas três sementes. Retirar 51 perdeu esse ID em duas, mas preservou o resultado na 41. Retirar 52 preservou todos os três na 17 e na 29, porém perdeu `id_18` na 41. Isso é evidência de sensibilidade do **sistema de detecção** a entradas e sementes, não uma atribuição da origem física da anomalia. Três sementes no mesmo período não simulam novos anos nem criam intervalo de confiança amostral.
