# Devolutiva — M10.2

Execução Windows: **`20261119T101049Z_253ff59f`**. A função utilizada está em
[`m10_2_pca_autoral.py`](../../notebooks/m10_2_pca_autoral.py). Ela centraliza
com o centro recebido, projeta nas componentes, reconstrói e soma os resíduos
quadráticos por linha. Não ajusta o PCA nem modifica as entradas.

```python
import numpy as np

def erro_pca_por_amostra(x, centro, componentes):
    x = np.asarray(x, dtype=float)
    centro = np.asarray(centro, dtype=float)
    componentes = np.asarray(componentes, dtype=float)
    centrado = x - centro
    coordenadas = centrado @ componentes.T
    reconstruido = coordenadas @ componentes + centro
    residuo = x - reconstruido
    return np.square(residuo).sum(axis=1)
```

## 1. Um desacordo real

Escolhi **12/06/2009 às 16:00 UTC**, a linha `robusto_relativamente_alto` de
[`casos_reais.csv`](../../reports/m10_2/20261119T101049Z_253ff59f/casos_reais.csv).

| Escore | Valor | Percentil no ranking de desenvolvimento |
|---|---:|---:|
| Máximo robusto | 7,1669441805 | **98,2502237200** |
| Erro PCA | 0,000002282279553 | **0,8282401325** |

O robusto vê pelo menos um canal distante da mediana histórica em unidades
de MAD escalado. Ele considera os afastamentos marginais; não pergunta se
os três canais se deslocaram juntos. O PCA mede outra distância: quanto
ficou fora do plano de duas componentes aprendido no ajuste. Um ponto pode
estar longe do centro e continuar próximo desse plano. O desacordo é
compatível com um deslocamento conjunto que preserva a relação linear
retida; não há contradição entre os dois escores.

A linha está em intervalo anotado como **`Anomaly`, ID `id_134`**. Isso permite
afirmar a coincidência com a anotação do recorte. Não identifica o componente
físico que falhou, sua causa ou gravidade, nem comprova qual dos escores
serviria melhor a uma política de alarmes. As unidades são anonimizadas e
nenhum limiar foi escolhido. Percentil 98,25 significa posição relativa
nesse conjunto, não 98,25% de probabilidade de falha.

## 2. O peso do evento e a decisão seguinte

Foram usados **136.202 instantes no ajuste** e **105.042 na comparação de
desenvolvimento**, com 3.909 positivos anotados distribuídos por oito IDs.
Os modelos foram ajustados em 2004–2007; os rankings abaixo usam 2008–2010.

| Método | AP completa | AP sem `id_134`, com os escores fixos |
|---|---:|---:|
| Constante: prevalência da coorte | 0,037214 | 0,009539 |
| Robusto | 0,716427 | **0,356114** |
| PCA | 0,502013 | 0,017142 |
| Isolation Forest | **0,758149** | 0,324910 |

`id_134` ocupa **2.935 dos 3.909 instantes positivos**, ou **75,0831%**.
Na cobertura há 2.985 instantes de grade associados a esse ID; 50 não
entram no ranking porque não têm todos os canais utilizáveis. Os 2.935
pontos são a união temporal das anotações do ID, sem triplicar a contagem
por ele aparecer em três canais.

No conjunto completo, Isolation Forest lidera com AP 0,758149. Ao retirar
os pontos de `id_134` apenas da avaliação, restam 102.107 instantes, dos
quais 974 são positivos; o robusto lidera com 0,356114, seguido da floresta
com 0,324910. Não houve novo ajuste. A inversão mostra que a liderança é
sensível à composição dos episódios, em especial a um evento longo.

A prevalência também mudou. Portanto comparo os métodos dentro de cada
coluna; não interpreto a diferença entre as duas APs como uma perda causal
de desempenho. AP é uma medida de ranking por instante, não a fração de
eventos detectados. Um episódio longo fornece muitas linhas correlacionadas.

Para o M10.3, manteria robusto e Isolation Forest como candidatos a uma
comparação de políticas por evento, sem promover automaticamente o líder
da AP. Antes de observar o período posterior, congelaria:

- **Dados e ajuste:** canais, grade, frescor, hipóteses de disponibilidade e
  fuso, cortes temporais, referência histórica, escalas e modelos ajustados.
- **Avaliação:** definição de evento por ID e união de intervalos, coorte,
  tratamento de linhas sem escore e de `Rare Event`/`Communication Gap`,
  além de recall por evento, atraso e alarmes em períodos sem anotação.
- **Política e critério:** candidatos a limiar, duração mínima, agrupamento
  de alarmes, intervalo de silêncio e regra de seleção sob uma capacidade
  de investigação definida com quem usa os alertas.

O limiar seria escolhido no desenvolvimento segundo esse critério, com
custos e capacidade declarados, e então congelado junto com a política
antes do período reservado de 2011–2013. Esses valores operacionais ainda
não foram fornecidos; não cabe inventá-los nem importar os custos hipotéticos
do Renewcast. Escore ou percentil não é probabilidade calibrada.

## 3. Transferência para três canais

O centro é zero. As direções retidas são
`w1 = (1,1,1)/sqrt(3)` e `w2 = (1,-1,0)/sqrt(2)`.

Para **A = (3,3,3)**:

```text
A · w1 = (3 + 3 + 3)/sqrt(3) = 3 sqrt(3)
A · w2 = (3 - 3)/sqrt(2) = 0
A_reconstruído = 3 sqrt(3) w1 = (3,3,3)
S_A = 0
```

Para **B = (1,1,-2)**:

```text
B · w1 = (1 + 1 - 2)/sqrt(3) = 0
B · w2 = (1 - 1)/sqrt(2) = 0
B_reconstruído = (0,0,0)
S_B = 1² + 1² + (-2)² = 6
```

Logo, com duas componentes, o erro de reconstrução destaca B. O máximo
robusto faria a ordem oposta nesses pontos já padronizados: A tem máximo
absoluto 3 e B, 2. Os métodos respondem a geometrias diferentes.

Ao acrescentar `w3 = (1,1,-2)/sqrt(6)`, temos `A · w3 = 0` e
`B · w3 = sqrt(6)`. A reconstrução de B passa a ser
`sqrt(6) w3 = (1,1,-2)`. Assim, **os dois escores ficam zero** em aritmética
exata, com possíveis resíduos de arredondamento na execução. As três
direções formam uma base ortonormal de R³: tudo é reconstruído, inclusive
pontos extremos. Acrescentar componentes reduz o resíduo, mas pode eliminar
justamente a diferença usada como sinal de suspeita.

## Conferência e arquivos

As duas contas geométricas do runner e a comparação de todos os resíduos
autorais com `transform`/`inverse_transform` passaram. A diferença máxima
foi **3,730349362740526 × 10⁻¹⁴**. Os oito testes adicionais também passaram.

As saídas estão preservadas no
[resultado.json](../../reports/m10_2/20261119T101049Z_253ff59f/resultado.json),
no [relatório HTML](../../reports/m10_2/20261119T101049Z_253ff59f/relatorio.html),
na [sensibilidade por evento](../../reports/m10_2/20261119T101049Z_253ff59f/sensibilidade_evento.csv)
e na [cobertura por ID](../../reports/m10_2/20261119T101049Z_253ff59f/cobertura_eventos.csv).
O [guia passo a passo](Explicacao_Passo_a_Passo.md) explica o código.
Esta é uma comparação de desenvolvimento; não houve escolha de limiar
ou uso do período reservado.

A [auditoria dos arquivos](../evidencias_m10_2_local/auditoria_resultados.json)
também terminou com `verified=true`. Ela recalculou a AP em NumPy respeitando
empates, reconstruiu as máscaras e conferiu PCA por uma projeção complementar,
sem reajustar os detectores. Os checkpoints da floresta e dos centros de
K-means não foram exportados pelo laboratório; para esses métodos a auditoria
confere escores, métricas e agregações persistidos, não reproduz o modelo.
