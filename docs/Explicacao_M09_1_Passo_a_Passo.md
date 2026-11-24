# M09.1: como a atenção consulta uma janela

O laboratório calcula atenção sobre uma janela histórica do Renewcast e
exporta os pesos usados em cada consulta. A função
[`atencao_escalada`](../notebooks/m09_atencao_autoral.py) implementa a conta
com NumPy. O [parecer](../reports/parecer_m09_atencao.md) reúne os resultados
locais e a defesa dos acessos permitidos. Esta unidade não ajusta parâmetros
nem calcula desempenho de previsão.

## 1. O papel de Q, K e V

Q contém as consultas; K contém as chaves usadas para calcular compatibilidades;
V contém os valores que serão combinados. O produto entre uma consulta e
cada chave produz um score. Os scores viram pesos, e os pesos combinam V.

| Objeto | Shape | Significado |
|---|---|---|
| Q | `[B,L,D]` | B exemplos, L consultas, D coordenadas |
| K | `[B,S,D]` | S chaves em cada exemplo |
| V | `[B,S,Dv]` | Um vetor de conteúdo por chave |
| Scores e pesos | `[B,L,S]` | Uma linha de chaves por consulta |
| Saída | `[B,L,Dv]` | Uma representação por consulta |

Q e K compartilham D para permitir o produto interno. V pode ter outra
dimensão final. L pode diferir de S: com Q `[2,4,3]`, K `[2,6,3]` e
V `[2,6,2]`, temos pesos `[2,4,6]` e saída `[2,4,2]`.
Cada exemplo do batch é processado separadamente. B não representa tempo
nem permite consultar medições de outro exemplo.

Na janela real, B=1, L=S=24, D=4 e Dv=1. As quatro coordenadas de entrada
são construídas a partir da geração padronizada e da codificação posicional.
Projeções fixas produzem Q e K; V guarda a geração histórica em sua escala
original. Essas projeções não foram treinadas.

## 2. O que a função verifica antes de calcular

As entradas são convertidas para float64. Q, K e V precisam ter três
dimensões positivas, o mesmo batch, D compatível entre Q/K e a mesma
quantidade S de chaves e valores. Valores NaN ou infinitos são recusados.

A máscara opcional deve ser booleana, exatamente `[L,S]`. A convenção é
**True = acesso permitido**. A mesma máscara vale para todos os exemplos.
Sem máscara, todas as S chaves ficam disponíveis. Uma consulta com todas
as chaves bloqueadas gera `ValueError`: não existe distribuição definida
sobre um conjunto vazio neste contrato.

A função não escreve em Q, K, V ou máscara. Por isso aceita arrays somente
para leitura. Também transforma falhas de faixa numérica em `ValueError` e
confere a finitude da representação final.

## 3. As cinco operações e seus eixos

Primeiro, calculamos os produtos consulta–chave:

```python
scores = np.matmul(q, k.swapaxes(-1, -2)) / np.sqrt(dimensao)
```

`swapaxes(-1,-2)` troca somente os últimos eixos de K: `[B,S,D]` vira
`[B,D,S]`. Assim, `[B,L,D] @ [B,D,S]` produz `[B,L,S]`, conservando o batch.
Uma transposição que invertesse todos os eixos mudaria essa organização.

A segunda operação divide por `sqrt(D)`, a raiz da dimensão comparada.
Essa escala modera o crescimento dos produtos quando aumentamos suas
coordenadas; sua motivação depende de hipóteses sobre a distribuição delas.

A terceira operação aplica o bloqueio antes da normalização:

```python
scores = np.where(permitidas[None, :, :], scores, -np.inf)
```

O eixo acrescentado permite compartilhar `[L,S]` com os B exemplos.
A exponencial de `−inf` é zero. A chave proibida deixa de participar também
do denominador, preservando toda a massa nas chaves permitidas.

A quarta operação é o softmax estável, **sobre S**:

```python
scores = scores - np.max(scores, axis=-1, keepdims=True)
exponenciais = np.exp(scores)
pesos = exponenciais / np.sum(exponenciais, axis=-1, keepdims=True)
```

O máximo é calculado para cada consulta de cada exemplo. Subtraí-lo não
altera a distribuição, pois o fator comum cancela na divisão. Isso evita
exponenciar scores positivos enormes. `keepdims=True` mantém um eixo final
unitário para alinhar máximo e denominador com cada linha.

Cada linha soma um; normalizar sobre L produziria outra operação. Finalmente,
`pesos @ v` combina os conteúdos e devolve `[B,L,Dv]`. A função retorna
exatamente `{"pesos": pesos, "saida": saida}`. A formulação e a convenção
booleana usadas no comparador constam da
[documentação SDPA do PyTorch 2.7](https://docs.pytorch.org/docs/2.7/generated/torch.nn.functional.scaled_dot_product_attention.html).

## 4. Duas contas pequenas para enxergar o efeito da máscara

Considere scores já escalados `[ln(3),0]` e valores `[10,30]`.
As exponenciais são proporcionais a `[3,1]`, resultando em pesos
`[0.75,0.25]`. A saída é:

```text
0.75 * 10 + 0.25 * 30 = 15
```

Se apenas a segunda chave for permitida, os pesos passam a `[0,1]` e a
saída é 30. A máscara muda o conjunto consultável, preservando os valores.

Agora use Q/K nulos e V `[0,6,12]`. Os scores são iguais, portanto os pesos
são uniformes entre as chaves permitidas:

| Consulta | Livre | Causal com diagonal |
|---|---:|---:|
| 0 | 6 | 0 |
| 1 | 6 | 3 |
| 2 | 6 | 6 |

A atenção livre produz `[6,6,6]`; a causal, `[0,3,6]`. Alterar o último
valor não afeta as duas primeiras saídas causais, porque essa chave está
bloqueada para elas.

## 5. Disponibilidade na origem e acesso ao prefixo

Na origem de 03/07/2026 às 04h, o contexto vai de 02/07 às 03h a 03/07
às 02h. Sob atraso assumido de duas horas, todas as 24 medições estão
disponíveis na origem. A atenção livre entre elas respeita esse corte.
Os horários preservam o eixo da entrada, sem fuso físico validado.

O prefixo interno faz outra pergunta. Se a representação da posição 5
deve usar somente as posições 0–5, consultar 6–23 viola esse acesso.
A máscara triangular inferior permite `chave <= consulta`, incluindo a
diagonal. Sua causalidade é uma regra de acesso dentro da sequência.

Na última consulta, ambas as máscaras permitem todas as chaves. Por isso
as saídas coincidem neste ensaio: uma camada, mesmos Q/K/V e sem Dropout.
Uma pilha de camadas pode receber representações intermediárias diferentes
e produzir outro resultado, mesmo na posição final.

## 6. O que a posição acrescenta

Na atenção livre sem posição, permutar Q/K/V conjuntamente apenas permuta
as saídas. Isso é equivariância. Fazer depois uma média das saídas daria
uma quantidade invariante à permutação. A conta funciona, mas não distingue
sozinha qual conteúdo ocupava cada horário.

O laboratório acrescenta senos e cossenos dos índices 0–23 antes das
projeções Q/K. Depois troca os conteúdos mantendo esses índices fixos.
A equivalência anterior deixa de valer: mudou qual conteúdo ocupa cada
posição. Permutar conteúdo e posição juntos seria outra operação.

Esse teste demonstra o papel da posição no cálculo. Não escolhe a melhor
codificação para prever geração. A máscara causal também introduz uma
estrutura de ordem; o teste de equivariância usa atenção livre.

## 7. O que os mapas mostram e como repetir a conferência

Cada mapa tem consultas nas linhas e horas consultadas nas colunas.
As cores são relativas ao máximo de cada painel; compare os CSVs para
examinar valores exatos. Como V contém geração histórica e cada linha de
pesos é uma distribuição, a saída escalar fica entre os extremos permitidos
daquele histórico. É uma representação ponderada.

Projeções não treinadas não demonstram capacidade preditiva. Um peso alto
também não comprova importância causal física daquela hora. O programa
não produz previsão h24, MAE ou RMSE, nem executa um Transformer completo.

Na raiz do projeto, com o ambiente existente ativo, confira a função sem
ler os Parquets:

```powershell
python notebooks/laboratorio_atencao.py --autoria notebooks/m09_atencao_autoral.py --verificar
```

Para usar a mesma função também na janela real:

```powershell
python notebooks/laboratorio_atencao.py --autoria notebooks/m09_atencao_autoral.py
```

Ambos gravam `conferencia.json`. O segundo acrescenta pesos, representações,
projeções, relatório HTML e `resultado.json` em uma pasta própria. O parecer
registra os números locais; o objetivo é conferir a operação e defender
quais informações cada consulta pode acessar.

## 8. Conferências desta entrega

Os oito grupos integrados passaram, com diferença máxima de
`4.440892098500626e-16` frente ao PyTorch, abaixo da tolerância de `1e-12`.
Os [seis testes adicionais](../tests/test_m09_atencao_autoral.py) conferem
a conta manual, a exclusão de chaves antes da normalização, prefixos,
lotes retangulares somente para leitura, scores grandes e entradas inválidas:

```powershell
python -m unittest discover -s tests -p test_m09_atencao_autoral.py -v
```

O [relatório local](../reports/transformer/CJU_BA5EIGT/m09_1_atencao/20261117T144205Z_917f4acf/relatorio.html)
permite examinar os pesos de cada célula. Os
[mapas em PNG](../reports/transformer/CJU_BA5EIGT/m09_1_atencao/mapas_atencao_20261116.png)
usam escalas próprias por painel e mostram em cinza as posições bloqueadas.
O [parecer](../reports/parecer_m09_atencao.md) identifica a janela, registra
os deltas e explica o alcance das representações.

A [conferência de 17/11](Conferencia_M09_1_20261117.md) documenta a execução
com `--autoria`, os seis testes e a formatação corrigida do HTML. O uso de
`float_format` aplica seis casas decimais às colunas float sem arredondar datas.
