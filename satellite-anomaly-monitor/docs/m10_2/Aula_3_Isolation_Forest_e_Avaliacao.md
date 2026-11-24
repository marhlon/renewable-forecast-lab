# Aula 3 — Isolation Forest e julgamento do experimento

**Problema.** O detector robusto procura extremos marginais; o PCA procura distância a um plano. O que fazer quando o conjunto habitual tem vários agrupamentos e relações que um plano único não explica? Usaremos árvores de isolamento para uma terceira maneira de ordenar suspeitas. Depois vamos confrontar essa ordem com as mesmas anotações e explicar quando o ranking engana.

## 1. Isolar um ponto é diferente de reconstruí-lo

Uma árvore de isolamento escolhe uma coluna e um corte aleatório dentro da faixa dos valores no nó. Um ponto em região esparsa tende a ficar sozinho com menos cortes. Em uma região densa, em média são necessários mais cortes. Várias árvores reduzem a dependência de uma escolha aleatória específica. A normalização pela profundidade esperada para o tamanho da subamostra permite comparar profundidades.

Uma forma de ver a direção do escore original é \(2^{-\overline h/c}\), com profundidade média \(\overline h\) e constante positiva \(c\) dependente da subamostra. Por exemplo, para \(c=8\), profundidade 3 dá aproximadamente 0,77 e profundidade 12 dá 0,35. A transformação é monotônica decrescente. Estes números explicam o sinal; não são probabilidades ou uma calibração de risco.

No código, fixamos 128 árvores, subamostras de 256, a semente 17 e três canais padronizados. A API `score_samples` do scikit-learn usa orientação inversa à suspeita que adotamos. Por isso `-floresta.score_samples(z)` ordena com **maior = mais suspeito**. `contamination="auto"` define o deslocamento usado pelo método de decisão da biblioteca; este laboratório usa apenas escores brutos e não chama `predict` para produzir alarmes. A floresta ainda pode errar em regiões pouco representadas e seus cortes alinhados aos eixos não resolvem todas as geometrias.

| Escore | Que desvio enfatiza | O que pode deixar passar |
| --- | --- | --- |
| Máximo robusto | Um canal individual longe de sua referência | Combinação incomum com valores marginais comuns |
| Erro PCA | Quebra das relações lineares retidas | Ponto distante sobre o plano ou regime normal curvo |
| Isolation Forest | Observação que se separa cedo nas partições aleatórias | Subgrupo raro mas denso, regime nominal pouco representado, mudanças estritas de tempo |

Os três são **pontuais**: recebem uma linha, sem sequência anterior na feature. Uma mudança anormal que só se revela pela duração ou pela velocidade pode escapar deles. Isso é uma limitação mensurável e indica quando acrescentar janelas, em vez de escolher mais uma arquitetura por catálogo.

## 2. Avalie no mesmo conjunto e entenda o denominador

Em `scripts/executar_m10_2.py`, `fit_ok` seleciona só o ajuste. `eval_ok` estabelece a coorte comum no desenvolvimento. Todos os escores avaliam os mesmos instantes; os rótulos entram apenas depois da chamada de pontuação. Na avaliação, veja **Average Precision (AP)** como a soma das precisões ponderada pelo aumento de recall à medida que se inclui mais itens do ranking. Sem empates, dá para calcular como a média da precisão nas posições dos positivos.

**Conta manual:** para ranking `[positivo, negativo, positivo, negativo, negativo]`, a precisão nos dois positivos é 1/1 e 2/3. AP = \((1+2/3)/2=5/6\). O escore constante tem AP = 2/5, a prevalência. Com empates, a biblioteca avança em blocos de escore; ordenar empates arbitrariamente por timestamp faria a conta manual significar outra métrica. Uma AP de 0,76 não é 76% de recall, 76% de precisão em uma regra específica, nem 76% dos eventos detectados.

## 3. Resultado real e a mudança que importa

Na execução de referência, dos 105.216 instantes de desenvolvimento, **51** não foram pontuados pela falta de pelo menos um canal utilizável. Outros **123** tiveram escore, mas ficaram fora da comparação por categoria de anotação. Sobram **105.042** instantes no ranking e **3.909** positivos anotados.

| Escore | AP completa | AP retirando `id_134` |
| --- | ---: | ---: |
| Constante (prevalência da coorte) | 0,037214 | 0,009539 |
| Robusto | 0,716427 | **0,356114** |
| PCA | 0,502013 | 0,017142 |
| Isolation Forest | **0,758149** | 0,324910 |

O ID `id_134` responde por 2.935/3.909 = **75,08% dos pontos positivos**. O diagnóstico retira suas linhas da avaliação, preservando o ajuste e os escores. A ordem entre robusto e floresta se inverte. Prevalência e composição mudam: comparamos os métodos **dentro de cada coluna**. O resultado completo não fica “errado”; responde como os métodos ordenam **instantes** que incluem aquele episódio longo. O resultado de sensibilidade mostra quanto essa resposta depende de um episódio. Nenhuma das duas tabelas estima desempenho em uma nova missão.

No M10.3 o problema muda: a operação responde a episódios e tem capacidade limitada para investigar. A avaliação terá de distinguir quantos eventos foram sinalizados, quantos alarmes foram disparados em períodos sem anotação, tempo até o primeiro alarme e casos não observáveis. Conseguir 100 alertas no mesmo evento longo não equivale a detectar 100 eventos. O período posterior ainda não foi usado para escolher detector, limiar ou janela.

**Use `casos_reais.csv`.** Uma das linhas anotadas aparece perto do percentil 98 no escore robusto e abaixo do percentil 1 no PCA. Isso é compatível com um deslocamento conjunto perto do plano. Outra linha é muito suspeita para a floresta e não tem anotação: ela é um caso a inspecionar, sem prova de falha física ou de erro do detector. Os casos de divergência foram selecionados para explicar os mecanismos; não estimam a frequência com que os mecanismos ocorrem.

## 4. Agrupamento responde a outra pergunta

O K-means, com três grupos fixados, ajusta centros que reduzem a soma das distâncias quadráticas das linhas até o centro atribuído. O código ajusta centros só no passado e associa linhas de desenvolvimento a um centro existente. `contextos.csv` descreve a fração anotada e as medianas dos escores por grupo. Um grupo pode se concentrar em outra faixa de amplitude e carregar mais anotações; isso sugere investigar regimes, não dá nome físico aos grupos. O ID do grupo é arbitrário e não entra na definição de normalidade nem escolhe a política desta rodada.

## 5. Entrega e correção

Rode o comando da seção 4 do [guia](../COMECE_M10_2.md) com sua função PCA. Use a tabela de casos, a sensibilidade e a cobertura no relatório. Devolva sua função e as três respostas de [Resposta_M10_2.md](Resposta_M10_2.md). A correção usa estes critérios:

**Caso novo de transferência.** Um sistema tem três sensores já padronizados, centro zero e retém duas direções: \(w_1=(1,1,1)/\sqrt{3}\) e \(w_2=(1,-1,0)/\sqrt{2}\). Para \(A=(3,3,3)\) e \(B=(1,1,-2)\), calcule as coordenadas retidas e os dois escores por reconstrução. Agora acrescente \(w_3=(1,1,-2)/\sqrt{6}\) como terceira direção. Como muda a capacidade de destacar B? A conta pode ser feita à mão; conferi-la com sua função não requer reajustar nem executar de novo o laboratório.

| Critério | Evidência que eu vou conferir |
| --- | --- |
| Implementação | Projeta com o centro fornecido; devolve um escore por linha; concorda com as contas e a reconstrução real. |
| Diagnóstico | Seleciona um timestamp real, lê dois percentis corretamente e explica uma hipótese geométrica sem declarar causa física. |
| Julgamento | Reconhece o peso de `id_134`, a inversão do ranking e a diferença entre decisão por instante e por evento. Especifica o que congelaria antes do teste posterior. |
| Transferência | Usa produtos internos para distinguir A de B na base dada, calcula os escores e explica o que muda com a base completa. |

Se algum critério falhar, a revisão aponta a conta, a interpretação ou o contrato que precisa mudar; só a parte afetada é refeita. O registro distingue execução, tentativa e transferência. Concluir a comparação de desenvolvimento não promove um detector a serviço operacional.

Referências de interface: [Isolation Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html) e [Average Precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html). Os números e casos desta aula foram medidos no recorte do projeto.
