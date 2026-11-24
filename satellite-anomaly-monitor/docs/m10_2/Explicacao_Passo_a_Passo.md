# M10.2: por que três escores podem discordar

A rodada compara três maneiras de ordenar instantes suspeitos nos canais
50, 51 e 52. A parte implementada é o erro de reconstrução do PCA em
[m10_2_pca_autoral.py](../../notebooks/m10_2_pca_autoral.py). A execução Windows
`20261119T101049Z_253ff59f` produziu os resultados citados neste guia;
o [recibo](../../reports/m10_2/20261119T101049Z_253ff59f/resultado.json)
identifica código, versões e dados.

## 1. Aprender no passado e aplicar uma referência fixa

O ajuste usa 2004–2007; o desenvolvimento, 2008–2010, com fins exclusivos
em 01/01/2008 e 01/01/2011. O período posterior permanece fora desta rodada.
A grade é de 15 minutos, com retenção da última amostra de até 180 segundos
no próprio período. Grade e cadência de chegada são grandezas distintas.

Mediana, MAD, PCA e Isolation Forest são ajustados somente no passado.
A curadoria do ajuste exclui intervalos anotados retrospectivamente como
`Anomaly`, `Rare Event` ou `Communication Gap`. Portanto há informação
retrospectiva nessa seleção histórica, embora IDs e categorias não entrem
nas três features numéricas. A aplicação no desenvolvimento conserva os
parâmetros; recalculá-los ali mudaria a referência durante o diagnóstico.

No Windows, foram usados 136.202 instantes de ajuste. O ranking comparou
105.042 instantes de desenvolvimento, com 3.909 positivos anotados e oito
IDs de anomalia. As mesmas linhas foram usadas pelos três escores.
No ranking, `Anomaly` é positivo e sem anotação é negativo provisório.
`Rare Event` e `Communication Gap` ficam fora, inclusive em sobreposições.
Ausência de anotação não comprova normalidade física.

## 2. Os shapes e os dois centros

| Objeto da função PCA | Shape | Significado |
|---|---|---|
| `x` | `[n,p]` | n instantes já padronizados, p canais |
| `centro` | `[p]` | Centro aprendido pelo PCA |
| `componentes` | `[k,p]` | k direções ortonormais, uma por linha |
| Coordenadas retidas | `[n,k]` | Projeções nessas direções |
| Reconstrução | `[n,p]` | Retorno ao espaço dos canais |
| Escore | `[n]` | Um erro quadrático por instante |

Aqui, p=3 e k=2. Antes do PCA, cada canal é transformado por
`z=(valor-mediana)/(1.4826*MAD)`, usando o ajuste. O MAD é a mediana das
distâncias absolutas à mediana. Uma escala nula precisa ser diagnosticada.

O centro do PCA é a **média dos dados já padronizados**, diferente da
mediana original. Centralizar pela mediana não faz a média necessariamente
zerar. No run Windows, esse centro foi aproximadamente
`[0.222492,0.235589,0.282568]`. A função recebe esse vetor pronto; não
recalcula média, mediana ou componentes.
Essa distinção entre centralização e escala também está na
[interface do PCA do scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html).

## 3. As quatro operações implementadas

```python
centrado = x - centro
coordenadas = centrado @ componentes.T
reconstruido = coordenadas @ componentes + centro
escores = np.square(x - reconstruido).sum(axis=1)
```

Primeiro movemos a origem para o centro fornecido. Depois,
`[n,p] @ [p,k]` produz `[n,k]`: os componentes entram transpostos porque
estão nas linhas. A multiplicação seguinte volta a `[n,p]`, e somar o
centro recoloca o plano no lugar original. Por fim, somamos os resíduos
quadráticos sobre os canais, `axis=1`.

O retorno não é média dos erros, escore global ou uma coluna por sensor.
As entradas são válidas pelo contrato e são preservadas, inclusive somente
para leitura. O código não faz `fit`. A maior diferença observada para
`transform`/`inverse_transform` do scikit-learn foi `3,730349362740526e-14`.

## 4. Transferência: quando reconstruir tudo elimina o sinal

Considere centro zero e duas direções:
`w1=(1,1,1)/sqrt(3)` e `w2=(1,-1,0)/sqrt(2)`.
A conta abaixo é uma derivação analítica para os pontos propostos.

Para A=(3,3,3), os produtos internos são `3*sqrt(3)` e zero.
A reconstrução é exatamente A; o escore teórico é zero.
Para B=(1,1,-2), ambos os produtos são zero. A reconstrução é a origem,
e o escore é `1²+1²+(-2)²=6`.

Acrescente `w3=(1,1,-2)/sqrt(6)`. A coordenada de A nessa direção é zero;
a de B é `sqrt(6)`, que reconstrói B por inteiro. Os dois escores ficam
zero, salvo arredondamento numérico.

As três direções formam uma base de todo o espaço R³. A projeção completa
vira identidade: o erro de reconstrução perde a capacidade de destacar B.
Isso não transforma B em fisicamente normal; mostra o efeito de escolher
a dimensão retida.

## 5. Três geometrias de suspeita

O escore robusto `max(abs(z))` enfatiza o canal mais distante de sua
referência marginal. Para A ele vale 3; para B, 2. Pode deixar passar
combinações incomuns de valores individualmente moderados.

O PCA mede distância à estrutura linear retida. Detecta B no exemplo,
mas pode atribuir erro baixo a um ponto muito distante sobre o plano.
Variância retida alta não equivale a boa detecção.

A Isolation Forest procura pontos que se isolam cedo por partições
aleatórias. O código usa `-score_samples`, orientando maior como mais
suspeito. Regiões raras mas densas ou regimes pouco representados podem
confundir essa geometria. Os três métodos são pontuais: duração e velocidade
de mudança não aparecem automaticamente nessas três features.
A orientação de `score_samples` está documentada na
[API da Isolation Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html).

## 6. AP mede ranking de instantes

Average Precision combina precisão e aumentos de recall ao percorrer os
escores, conforme a
[definição de AP do scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html).
No ranking `[positivo,negativo,positivo,negativo,negativo]`, sem
empates, AP é `(1+2/3)/2=5/6`. Um escore constante dá a prevalência, 2/5.

AP não é probabilidade de anomalia, precisão de um limiar escolhido ou
percentual de eventos detectados. Percentis dos escores também são posições
relativas na coorte, sem interpretação automática de risco.

Na execução Windows:

| Escore | AP completa | AP sem `id_134` |
|---|---:|---:|
| Constante | 0,037214 | 0,009539 |
| Robusto | 0,716427 | 0,356114 |
| PCA | 0,502013 | 0,017142 |
| Isolation Forest | 0,758149 | 0,324910 |

`id_134` concentra 2.935 dos 3.909 positivos, ou 75,083141%.
A sensibilidade retira suas linhas da avaliação, mantendo ajuste e escores
fixos. Mudam composição e prevalência da coorte; comparamos métodos dentro
de cada coluna. A inversão entre floresta e robusto mostra dependência
desse episódio longo, sem demonstrar desempenho em um período novo.

## 7. O que precisa ficar definido antes do próximo período

No M10.3 será necessário congelar detector, transformações, limiar e regra
de comparação, além da política que agrega pontos em alarmes: persistência
mínima, agrupamento de disparos e tratamento de ausências. A capacidade de
investigação e o custo de alarmes precisam orientar essa escolha antes de
examinar o período posterior.

Também devem ficar definidos os períodos de calibração e teste, a coorte,
o tratamento de IDs e as métricas por evento: eventos observáveis sinalizados,
alarmes por tempo acompanhado e atraso até o primeiro disparo. Muitos
alertas no mesmo ID não significam muitos eventos detectados.

A comparação atual examina rankings de desenvolvimento. Unidades anonimizadas,
disponibilidade e interpretação UTC continuam limitando afirmações físicas
e operacionais. A função e os resultados sustentam a revisão; a justificativa
e a transferência continuam sendo avaliadas pelos critérios das aulas.

## 8. Ler e conferir a entrega

A [resposta preenchida](Resposta_M10_2.md) reúne a função e os três itens
pedidos. Para conferir os arquivos sem repetir o ajuste:

```powershell
python -m unittest discover -s satellite-anomaly-monitor/tests -p test_m10_2_pca_autoral.py -v
python satellite-anomaly-monitor/docs/evidencias_m10_2_local/auditar_resultados.py
```

Passaram oito testes adicionais e as onze verificações do
[auditor independente](../evidencias_m10_2_local/auditoria_resultados.json).
O laboratório completo foi executado uma vez com `--autoria`; a conferência
posterior usa seus arquivos persistidos.
