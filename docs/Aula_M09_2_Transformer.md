# M09.2 — compondo um Transformer encoder–decoder

Este é um laboratório local de composição preparado para revisão da M09.2,
com arquitetura e verificações definidas no projeto. Não corresponde a um
contrato distribuído anteriormente. A M09.3, sobre modelo temporal
pré-treinado, continua sendo outra etapa.

O objetivo é acompanhar representações através de atenção por cabeças,
posição, conexões residuais, normalização e rede feed-forward. O programa
usa CPU, float64 e modo `eval()` nas conferências matemáticas. Não realiza
treinamento, download de pesos ou instalação. Os resultados locais ficam no
[parecer](../reports/parecer_m09_transformer.md) e nos recibos de execução.

## 1. Arquivos e execução

O código reutilizável está em
[`src/renewable_forecast/transformer_blocks.py`](../src/renewable_forecast/transformer_blocks.py).
Ele separa atenção, bloco encoder, bloco decoder e composição completa.
O laboratório organiza as conferências e a passagem de uma janela real:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
python notebooks/laboratorio_transformer.py
```

Para executar somente as conferências, sem ler a série:

```powershell
python notebooks/laboratorio_transformer.py --verificar
```

Os testes específicos ficam em `tests/test_m09_transformer_blocks.py`.
Não é necessário repetir laboratórios anteriores. A execução normal lê os
arquivos existentes de `dist/databricks/CJU_BA5EIGT/m07_3`: manifesto,
geração e treino de referência.

## 2. O histórico real e as consultas sintéticas

A janela herdada contém 24 medições disponíveis, da origem menos 25 horas
à origem menos duas horas. Para 03/07/2026 às 04h, vai de 02/07 às 03h a
03/07 às 02h, sob atraso assumido de duas horas. Os timestamps preservam o
eixo da entrada, sem conversão implícita de fuso.

A normalização é estimada somente nas 7.079 janelas de ajuste, por lag.
A janela examinada reutiliza essas médias e desvios. As 168 origens de
seleção e as 168 de avaliação continuam separadas; não escolhemos parâmetros
ou épocas nesta unidade. As exclusões herdadas são 52 por disponibilidade
e 18 por contexto inicial incompleto.

O encoder recebe geração padronizada `[B,24,1]`. O decoder recebe seis
consultas sintéticas zeradas `[B,6,1]`. Esses zeros passam por uma projeção
afim com viés, portanto sua representação projetada pode ser não nula.
A posição acrescentada diferencia os seis slots.

As consultas não são seis horizontes futuros, medições posteriores ou alvos
deslocados para teacher forcing. São entradas artificiais para estudar o
fluxo do decoder. A saída tem 16 coordenadas por slot, sem unidade MWmed
ou cabeça de previsão.

## 3. Como as quatro cabeças são construídas

A configuração usa `d_model=16`, quatro cabeças e `d_head=4`. Três projeções
afins geram Q, K e V, inicialmente com 16 coordenadas. Cada resultado é
reorganizado para separar as cabeças:

```text
[B,L,16] → [B,L,4,4] → [B,4,L,4]
```

Dentro de cada cabeça, Q é comparado com K por produto interno. A escala é
`1/sqrt(d_head)`, aqui `1/2`. O softmax atua sobre as chaves, mantendo
consultas e exemplos separados. Os conteúdos V são combinados por esses pesos.

As quatro saídas voltam a `[B,L,4,4]`, são concatenadas em `[B,L,16]` e
passam por uma projeção de saída. Cada cabeça consulta o contexto em um
subespaço projetado; não são quatro modelos treinados separadamente. A
estrutura e a divisão da dimensão são descritas na
[MultiheadAttention do PyTorch 2.7](https://docs.pytorch.org/docs/2.7/generated/torch.nn.MultiheadAttention.html).

A implementação retorna probabilidades `[B,4,L,S]` antes do Dropout.
Elas somam um por consulta. Durante treino, o produto por V utilizaria
Dropout sobre essas probabilidades; em `eval()`, ele é desativado.
O laboratório mantém esse modo para comparar cálculos.

## 4. Posição, máscara e formas dos tensores

`sinusoidal_positions` calcula senos e cossenos dos índices da sequência,
em frequências diferentes. Essas coordenadas fixas são somadas à projeção
de entrada. A função usa o dtype e o dispositivo da entrada; não aprende
essa codificação.

| Etapa | Shape nesta configuração |
|---|---|
| Histórico | `[B,24,1]` |
| Projeção e posição do histórico | `[B,24,16]` |
| Pesos de self-attention do encoder | `[B,4,24,24]` |
| Memória final do encoder | `[B,24,16]` |
| Consultas sintéticas | `[B,6,1]` |
| Projeção e posição das consultas | `[B,6,16]` |
| Pesos de self-attention do decoder | `[B,4,6,6]` |
| Pesos de cross-attention | `[B,4,6,24]` |
| Representação final | `[B,6,16]` |

A máscara local é booleana: **True permite consultar**. Seu shape é
`[consultas,chaves]`, compartilhado pelos batches e cabeças. Cada consulta
precisa permitir pelo menos uma chave; linhas totalmente bloqueadas são
recusadas. Q/K/V também são validados quanto a dimensões, finitude, batch,
dtype e dispositivo.

A máscara do decoder é triangular inferior, com diagonal: a consulta i
acessa posições até i. A cross-attention pode acessar as 24 posições da
memória histórica. Esse acesso livre respeita o corte da origem porque
todo o contexto fornecido já deveria estar disponível nela.

## 5. Duas camadas de encoder: atenção, residual e FFN

Cada `EncoderBlock` executa:

```text
x → self-attention → soma com x → LayerNorm
  → Linear(16,32) → ReLU → Linear(32,16)
  → soma residual → LayerNorm
```

Há Dropout nas probabilidades, nas saídas das subcamadas e entre as duas
projeções da FFN. Todos ficam desativados em `eval()`.

O residual soma uma transformação à representação que entrou naquela
subcamada. Os formatos precisam coincidir. A LayerNorm normaliza as 16
coordenadas de cada posição, sem combinar posições temporais ou exemplos.
Como vem depois da soma, o bloco é **pós-norma**.

A FFN aplica a mesma transformação a cada posição separadamente. A ReLU
introduz não linearidade. A atenção mistura informações entre posições;
a FFN transforma suas coordenadas. A composição corresponde às escolhas
`norm_first=False`, `activation="relu"` e `layer_norm_eps=1e-5` da
[TransformerEncoderLayer 2.7](https://docs.pytorch.org/docs/2.7/generated/torch.nn.TransformerEncoderLayer.html).

Dois blocos distintos são empilhados. A saída do primeiro alimenta o segundo;
os parâmetros não são compartilhados entre eles. O resultado é a memória
histórica usada pelo decoder.

## 6. Duas camadas de decoder: consultar o prefixo e a memória

Cada `DecoderBlock` possui três subcamadas:

1. Self-attention causal nas seis consultas, seguida de residual e LayerNorm.
2. Cross-attention à memória, seguida de residual e outra LayerNorm.
3. FFN/ReLU, seguida de residual e terceira LayerNorm.

Na cross-attention, Q vem do estado atualizado do decoder; K e V vêm da
memória do encoder. As seis consultas e as 24 chaves têm comprimentos
diferentes. A memória permanece fixa durante essa passagem; o decoder
não a sobrescreve. Essa organização corresponde à
[TransformerDecoderLayer 2.7](https://docs.pytorch.org/docs/2.7/generated/torch.nn.TransformerDecoderLayer.html).

Também há dois blocos distintos de decoder. Em ambos, a máscara causal
protege os prefixos internos. Isso não impede o acesso à memória histórica
completa: disponibilidade na origem e ordem interna das consultas são
restrições diferentes.

Não há LayerNorm extra após as pilhas. Esse detalhe importa ao comparar
com `nn.Transformer`, cuja construção padrão acrescenta normas finais.
A equivalência aqui é conferida por blocos com os mesmos parâmetros e
configuração; a arquitetura local está explicitamente descrita.

## 7. De onde vêm os 11.200 parâmetros esperados

| Componente | Cálculo | Parâmetros |
|---|---|---:|
| Uma atenção por cabeças | Quatro projeções de `16×16+16` | 1.088 |
| Uma FFN | `16×32+32 + 32×16+16` | 1.072 |
| Um encoder | Atenção + FFN + duas LayerNorm | 2.224 |
| Um decoder | Duas atenções + FFN + três LayerNorm | 3.344 |
| Duas projeções de entrada | Histórico e consultas: `2×(1×16+16)` | 64 |
| Composição | `2×2224 + 2×3344 + 64` | **11.200** |

Cada LayerNorm tem 16 escalas e 16 vieses. A posição fixa e o Dropout não
acrescentam parâmetros. A execução confere a contagem; a tabela apresenta
a quantidade esperada pela arquitetura, sem inferir qualidade ou custo.

## 8. O que as conferências precisam demonstrar

As comparações com PyTorch copiam os pesos e vieses para módulos equivalentes.
A mesma semente, sozinha, não garante inicializações idênticas entre códigos.
Os cálculos usam CPU/float64 e `eval()`.

No comparador, a máscara é invertida: MultiheadAttention e Transformer do
PyTorch interpretam **True como bloqueado**. A conversão é documentada pela
[API Transformer 2.7](https://docs.pytorch.org/docs/2.7/generated/torch.nn.Transformer.html).

Além da equivalência numérica, as verificações cobrem:

- **Prefixos:** alterar uma consulta posterior não deve mudar saídas anteriores
  do decoder, mantendo a memória fixa e a máscara causal.
- **Histórico livre:** uma posição do encoder pode consultar todo o contexto
  conhecido, inclusive posições posteriores dentro dessa janela.
- **Posição:** sem codificação, o encoder livre é equivariante à permutação;
  trocar conteúdos mantendo posições fixas muda o problema.
- **Gradientes:** uma sonda fixa não uniforme sobre a saída permite executar
  `backward()` e conferir caminhos de diferenciação, sem `optimizer.step()`.
- **Recarregamento:** pesos e configuração persistidos devem reproduzir as
  representações em `eval()`.

No teste de gradientes, autograd permanece habilitado, mesmo em `eval()`.
Os pesos não são atualizados. Essa demonstração não é treinamento nem perda
de previsão. Somar simplesmente todas as coordenadas seria uma sonda ruim,
pois a centralização da LayerNorm pode cancelar o sinal.

## 9. Saídas e alcance da entrega

Cada execução cria `reports/transformer/CJU_BA5EIGT/m09_2_transformer/<run_id>`:

| Arquivo | Conteúdo |
|---|---|
| `relatorio.html` | Fluxo e representações para inspeção |
| `resultado.json`, `conferencia.json` | Metadados e conferências medidas |
| `fluxo.csv` | Etapas percorridas pelos tensores |
| `representacoes_encoder.csv` | Coordenadas da memória histórica |
| `representacoes_decoder.csv` | Coordenadas dos seis slots |
| `pesos_atencao.csv` | Consultas por cabeça e camada |
| `config.json`, `preprocessing.json` | Arquitetura e escalas utilizadas |
| `estado_transformer.pt` | Estado persistido para recarregamento |

O módulo também expõe rastros das atenções, somas residuais, normalizações
e FFNs. Isso permite localizar uma divergência em vez de olhar somente a
saída final. Os resultados numéricos devem ser lidos no recibo e no parecer.

As representações têm 16 coordenadas abstratas. Projeções de saída,
residuais, normalizações e FFNs fazem com que o bloco completo não fique
limitado a uma média convexa da geração. Pesos de atenção tampouco provam
causalidade física. Esta composição não mede acurácia, não usa pesos
pré-treinados e não encerra a etapa de avaliação de modelos temporais.

## 10. Transformer, modelo de linguagem e esta prática

Transformer é uma arquitetura de processamento de representações, não um
sinônimo de modelo de linguagem. Aqui as entradas são números de geração.
Não há tokenizador, vocabulário de texto, distribuição sobre palavras ou
rotina de geração. Um modelo de linguagem acrescenta uma representação de
tokens, uma cabeça apropriada e treinamento para seu objetivo.

Há arquiteturas somente encoder, somente decoder e encoder–decoder. Esta
prática monta a terceira composição para tornar a cross-attention visível.
Ela não executa geração autorregressiva: os seis slots são processados juntos
com máscara causal e memória fixa. Em uma tarefa real, a construção das
consultas, os rótulos, a cabeça e a função de perda precisariam de contrato próprio.

## 11. Resultados locais e repetição

Na execução Windows de 17/11, os 13 grupos integrados e os 12 testes
independentes passaram. A maior diferença nas comparações foi
`6.661338147750939e-16`, abaixo de `1e-12`. O recarregamento e a perturbação
de consultas posteriores mantiveram diferença zero onde a igualdade era exigida.

```powershell
python -m unittest discover -s tests -p test_m09_transformer_blocks.py -v
```

O [relatório da janela real](../reports/transformer/CJU_BA5EIGT/m09_2_transformer/20261117T151609Z_61643ec2/relatorio.html)
contém o seletor das quatro cabeças e a tabela de fluxo. O
[diagrama](../reports/transformer/CJU_BA5EIGT/m09_2_transformer/fluxo_transformer_20261117.png)
resume a ligação entre encoder e decoder. O HTML e a lógica do seletor foram
verificados estruturalmente; a inspeção visual em navegador ficou indisponível
no ambiente. O [parecer](../reports/parecer_m09_transformer.md) registra os
limites e a leitura das conferências.
