# M08.3: como a GRU processa as 24 medições

O laboratório compara uma GRU com MLP, regressão linear, HGB e persistência,
usando as mesmas origens de previsão. A função
[`passo_gru`](../notebooks/m08_gru_autoral.py) abre o cálculo de uma célula:
recebe uma medição, um estado anterior e os pesos; devolve as portas e o novo
estado. Os resultados medidos no Windows e a decisão sobre os modelos estão
no [parecer da unidade](../reports/parecer_m08_gru.md).

## 1. A previsão continua respeitando os horários

Para emitir uma previsão na origem `o`, o atraso assumido de duas horas
permite usar medições até `o−2h`. A janela contém 24 valores, do mais antigo
em `o−25h` ao mais recente em `o−2h`. Suas pontas distam 23 horas. O alvo é
a geração em `o+24h`, disponível em `o+26h` sob essa hipótese.

Na origem de 03/07/2026 às 04h, a janela começa em 02/07 às 03h e termina
em 03/07 às 02h. O alvo é de 04/07 às 04h e fica disponível às 06h.
Os timestamps preservam o eixo da entrada, sem fuso físico validado.

A divisão herdada de M08.2 contém 7.079 exemplos de ajuste, 168 de seleção
e 168 de avaliação. Há 52 exclusões por disponibilidade nas duas fronteiras
e 18 por contexto inicial incompleto. Médias e desvios são calculados somente
no ajuste, por posição da janela; o alvo também usa escala estimada no ajuste.
Seleção e avaliação reutilizam essas escalas.

O treino embaralha as origens somente dentro do ajuste. Os 24 instantes de
cada janela permanecem ordenados. Janelas vizinhas podem compartilhar
medições; embaralhá-las não elimina sua dependência temporal.

## 2. O caminho dentro da rede

O modelo reutilizável está em
[`neural_gru.py`](../src/renewable_forecast/neural_gru.py). Ele possui uma GRU
unidirecional, uma camada recorrente e estado de 16 coordenadas:

| Objeto | Shape | O que representa |
|---|---|---|
| Entrada | `[B,24,1]` | B origens, 24 medições, uma variável |
| Entrada de um passo | `[B,1]` | Uma posição temporal por origem |
| Estado de um passo | `[B,16]` | Memória calculada para cada origem |
| Sequência de estados | `[B,24,16]` | Estado após cada medição |
| `hidden` | `[1,B,16]` | Estado final da única camada e direção |
| `hidden[-1]` | `[B,16]` | Estado final da camada escolhida |
| Previsão | `[B,1]` | Um valor padronizado por origem |

`hidden[-1]` seleciona a última camada, preservando todos os exemplos do lote.
`batch_first=True` organiza entrada e sequência de saída; o estado final
conserva a dimensão de camada na frente. A cabeça aplica Dropout 0,1 e uma
transformação linear de 16 coordenadas para um número. A transformação inversa
do alvo devolve esse número a MWmed.

Os pesos da célula somam `48 + 768 + 48 + 48 = 912` parâmetros: entrada,
estado e dois vieses. A cabeça acrescenta 16 pesos e um intercepto, chegando
a **929**. A MLP tem 833 e o linear tem 25. Essa contagem descreve os modelos;
não determina sozinha seu custo ou sua qualidade.

## 3. O contrato da função NumPy

A função representa um passo e aceita dimensões gerais:

| Argumento | Shape |
|---|---|
| `x` | `[B,I]` |
| `h` | `[B,H]` |
| `weight_ih` | `[3H,I]` |
| `weight_hh` | `[3H,H]` |
| `bias_ih`, `bias_hh` | `[3H]` cada |

`B` é o tamanho do lote; `I`, o número de variáveis de entrada; `H`, o tamanho
do estado. A função não fixa 24 ou 16. Converte as entradas para arrays
float64, verifica dimensões positivas e compatíveis e recusa valores não
finitos. O retorno é um dicionário com exatamente `r`, `z`, `n` e `h`, todos
arrays `[B,H]`. As operações criam resultados sem escrever nas entradas,
inclusive quando estas estão somente para leitura.

## 4. Por que calcular dois termos afins

O primeiro termo processa a medição atual; o segundo processa o estado anterior:

```python
termos_entrada = x @ weight_ih.T + bias_ih
termos_estado = h @ weight_hh.T + bias_hh
```

São transformações afins porque incluem multiplicação por pesos e soma de
viés. Os exemplos estão nas linhas. Por isso usamos os pesos transpostos:
`[B,I] @ [I,3H] → [B,3H]` e `[B,H] @ [H,3H] → [B,3H]`.
Cada viés `[3H]` é somado às linhas do lote.

Os parâmetros guardam três blocos na ordem **r, z, n**. `np.split(..., 3,
axis=1)` separa as colunas: `xr, xz, xn` vêm da entrada, enquanto `hr, hz, hn`
vêm do estado. Cada bloco passa a ter shape `[B,H]`.

## 5. As portas e o candidato, linha por linha

As portas são calculadas assim:

```python
r = _sigmoide(xr + hr)
z = _sigmoide(xz + hz)
n = np.tanh(xn + r * hn)
novo_estado = (1.0 - z) * n + z * h
```

A sigmoide transforma seus argumentos em valores entre zero e um. A função
auxiliar usa dois ramos equivalentes: para `v >= 0`, calcula
`1/(1+exp(-v))`; para `v < 0`, calcula `exp(v)/(1+exp(v))`.
Os expoentes utilizados são sempre não positivos, evitando exponenciar
números positivos muito grandes. O resultado mantém o formato da entrada.

`r`, a porta de reset, regula a contribuição recorrente ao candidato.
`hn` já contém a multiplicação do estado pelos pesos e a soma do viés.
Portanto, **`r` multiplica o termo afim inteiro, incluindo esse viés**.
Mover a porta para antes da matriz mudaria o cálculo: uma matriz pode
misturar coordenadas, enquanto `*` multiplica coordenadas correspondentes.

O candidato `n` combina a informação atual com essa contribuição do passado
e aplica `tanh`. A porta `z` decide a mistura: valores maiores preservam
mais do estado anterior; valores menores dão mais peso ao candidato.
Essas operações seguem as equações da
[GRUCell do PyTorch 2.7](https://docs.pytorch.org/docs/2.7/generated/torch.nn.GRUCell.html).

Para uma coordenada com `h=0.8`, `n=-0.2` e `z=0.75`:

```text
h_novo = (1 - 0.75) * (-0.2) + 0.75 * 0.8
       = -0.05 + 0.60
       = 0.55
```

O estado mistura uma parte nova e uma parte preservada. Suas coordenadas
não têm interpretação direta como geração em MWmed ou média física.

## 6. A memória fica dentro de cada janela

A rede chama `self.gru(x)` sem fornecer `h_0`; cada janela começa com zeros.
As 24 medições constroem sucessivamente seu estado, reutilizando os mesmos
pesos em cada passo. A próxima chamada começa novamente com zeros.

Guardar o estado de um lote e levá-lo ao seguinte mudaria esse problema.
Com origens embaralhadas, a primeira linha do próximo lote não continua a
história da primeira linha anterior. Essa ligação criaria dependência da
ordem de processamento e poderia carregar informação posterior à origem.
O modelo não armazena esse estado entre chamadas.

O comportamento dos estados e do dropout entre camadas está documentado na
[GRU do PyTorch 2.7](https://docs.pytorch.org/docs/2.7/generated/torch.nn.GRU.html)
e no [código da versão 2.7.1](https://github.com/pytorch/pytorch/blob/v2.7.1/torch/nn/modules/rnn.py#L1086).
O dropout usado neste laboratório está explicitamente na cabeça; há somente
uma camada recorrente.

## 7. Quem calcula o gradiente e escolhe o checkpoint

O experimento treina `torch.nn.GRU` com autograd. A perda final depende dos
24 passos anteriores; `backward()` aplica a regra da cadeia por esse caminho.
Como os pesos são compartilhados, contribuições de vários passos chegam aos
mesmos parâmetros. Não se corta esse caminho com `detach()` dentro da janela.

A função NumPy calcula o forward para conferir o significado das portas.
Ela não substitui o treino, mesmo quando o comando inclui `--autoria`.

MLP e GRU usam sementes 17, 29 e 41, AdamW, taxa 0,001, weight decay 0,0001,
lotes de 128, até 60 épocas e paciência oito. O último lote menor é mantido.
A menor perda de seleção define o checkpoint de cada rede; empates preservam
a primeira época. O estado é copiado e depois recarregado, sem novo ajuste.
A avaliação ocorre após fixar todos os checkpoints. Todas as sementes são
reportadas, sem escolher uma pela avaliação.

## 8. Como conferir sem repetir o treinamento

Na raiz, com o ambiente existente ativo:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
python notebooks/laboratorio_gru.py --autoria notebooks/m08_gru_autoral.py --verificar
```

O verificador compara portas e estado com a referência, confronta o estado
com GRUCell e verifica uma sequência de 24 passos contra GRU. Usa float64
e tolerância absoluta `1e-12`. Também confere preservação das entradas,
reinício de estado, permutação e divisão do lote, shapes e o avaliador.
O recibo é `conferencia_sem_treino.json`, em uma pasta própria da execução.

Para executar novamente todo o laboratório:

```powershell
python notebooks/laboratorio_gru.py
```

Cada execução recebe uma pasta diferente. `protocol.json` registra regras
e versões; `curvas.csv` mostra ajuste e seleção; `predictions.csv` permite
examinar erros por origem. `resultado.json` registra conferências,
recarregamentos, tempos, memória e hashes.

## 9. Como interpretar a comparação

O linear, a MLP, a GRU e o HGB recebem os mesmos 24 lags de geração.
O HGB desta unidade não recebe vento. A persistência usa a última medição
disponível. Essa comparação permite avaliar modelos sob informação alinhada.

O MAE dá peso linear à distância do erro; o RMSE dá maior peso aos erros
grandes por meio do quadrado. Um modelo pode melhorar um e piorar o outro.
Selecionar épocas por MSE também não garante o menor MAE da semana seguinte.
Para explicar eventos específicos é preciso examinar as previsões individuais.

As curvas de ajuste e seleção usam pesos fixos e avaliação sem Dropout.
A perda online mistura pesos que mudam durante a época e Dropout ativo.
O intervalo entre sementes descreve variação do treino; não é intervalo
de confiança nem desempenho de um ensemble.

Os tempos incluem avaliações por época. O pico de memória pertence ao
processo inteiro, com bibliotecas e modelos anteriores; não mede a GRU
isoladamente. Tamanho de checkpoint e bytes dos parâmetros são medidas
separadas. Uma execução sequencial não estabelece um benchmark de arquitetura.

A semana final já foi examinada no desenvolvimento. Concluir o programa e
passar nas conferências verifica a implementação, sem aprovar uso operacional.
O parecer usa os resultados locais para discutir erro, viés, custo e a
referência provisória, mantendo esse limite.

## 10. Arquivos desta execução

O [relatório Windows](../reports/neural/CJU_BA5EIGT/m08_3_gru/20261115T170309Z_90a6625f/relatorio.html)
reúne os resultados e as curvas. A
[conferência da célula NumPy](../reports/neural/CJU_BA5EIGT/m08_3_gru/20261115T170409Z_592111fa/conferencia_sem_treino.json)
aprovou 11 grupos, com diferença máxima de `2.220446049250313e-16` frente
à GRUCell. O limite da conferência é `1e-12`.

Os [cinco testes adicionais](../tests/test_m08_gru_autoral.py) incluem o
exemplo escalar, entradas somente para leitura, reset depois do termo afim,
sigmoide saturada e rejeição de dimensões incompatíveis. Para repeti-los:

```powershell
python -m unittest discover -s tests -p test_m08_gru_autoral.py -v
```
