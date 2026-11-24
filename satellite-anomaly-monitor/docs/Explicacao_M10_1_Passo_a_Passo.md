# M10.1: como os canais entram na mesma grade de decisão

A unidade prepara uma tabela temporal antes de treinar um detector.
A [função implementada](../notebooks/m10_sincronizacao_autoral.py),
`sincronizar_causal`, escolhe para cada decisão a última amostra disponível
de cada canal e registra sua idade. O [parecer](../reports/parecer_m10_1.md)
reúne os resultados da execução real e seus limites.

## 1. Medição, grade e tolerância têm papéis diferentes

Uma medição pertence ao relógio do sensor. A grade contém os instantes
em que queremos tomar uma decisão conjunta. A tolerância determina até
quando uma amostra anterior pode ser utilizada.

O protocolo prescreve grade de 90 segundos para 2007, com início em
01/01/2007 e fim exclusivo em 01/01/2008: 350.400 instantes. A tolerância
é 180 segundos, escolhida para exploração do contrato. Ela não representa
um SLA operacional nem foi ajustada para favorecer os rótulos.

Uma medição pode atender mais de um instante da grade. Por isso a quantidade
de linhas utilizáveis pode superar a de medições brutas. Isso é retenção
limitada da amostra, sem criação de novas observações ou novos casos
estatisticamente independentes.

## 2. O que a função recebe e devolve

As entradas são um dicionário de canais, uma grade temporal e uma duração:

```python
sincronizar_causal(tabelas, grade, tolerancia)
```

Cada nome de canal deve ser um identificador textual válido. Seu DataFrame
deve conter exatamente `timestamp` e `value`. O dicionário não pode estar
vazio. A grade precisa ser não vazia, crescente e sem instantes duplicados.
A tolerância é convertida para `pandas.Timedelta` e deve ser não negativa,
sem valor temporal ausente.

O resultado conserva uma linha por instante da grade. `timestamp` vem
primeiro; para cada canal, seguem quatro colunas:

| Coluna | Informação |
|---|---|
| `<canal>_value` | Valor permitido pelo contrato, ou `NaN` |
| `<canal>_sample_time` | Timestamp da última amostra encontrada |
| `<canal>_age_seconds` | Distância entre decisão e amostra, em segundos |
| `<canal>_usable` | Se a amostra pode ser utilizada nessa decisão |

A ordem dos canais segue a do dicionário. O laboratório acrescenta depois
`all_channels_usable`, combinando as flags dos canais; essa coluna não é
calculada dentro do sincronizador.

## 3. Por que padronizar timestamps e copiar as fontes

`_instantes_utc` exige timestamps com fuso explícito, sem `NaT`. Um relógio
ingênuo é recusado em vez de receber UTC silenciosamente. Instantes com
fusos diferentes são convertidos ao mesmo eixo UTC, preservando o instante.
A resolução final é `datetime64[ns, UTC]`, comum à grade e aos canais.
Isso evita incompatibilidades entre chaves temporais com tipos ou resoluções
diferentes durante o `merge_asof`.

No executor, pandas 3.0.5 produziu a grade UTC em microssegundos, enquanto
o sincronizador a devolveu em nanossegundos. Os instantes coincidiam, mas
a guarda com `.equals` reprovou essa diferença de resolução. O ajuste
padronizou também a grade criada por `pd.date_range` com
`.astype("datetime64[ns, UTC]")` antes da comparação. Os timestamps, a
cadência e os valores permanecem os mesmos; a execução final e seus
resultados são identificados pelos recibos correspondentes.

Cada fonte é copiada antes da conversão e ordenação. Os valores passam por
conversão numérica e são armazenados como float. Infinidades são recusadas;
`NaN` é preservado como ausência. Zero continua sendo uma medição válida.
Timestamps duplicados por canal são rejeitados, pois a escolha entre duas
medições no mesmo instante exigiria uma regra adicional.

A função ordena a cópia de cada fonte, sem alterar a tabela original ou
seu índice. A grade fora de ordem é rejeitada, preservando o contrato de
saída. Cada canal é procurado separadamente, permitindo relógios diferentes.

## 4. Buscar primeiro; avaliar o frescor depois

Para cada canal, o núcleo executa:

```python
pd.merge_asof(
    resultado, dados,
    left_on="timestamp", right_on=amostra,
    direction="backward", allow_exact_matches=True,
)
```

`backward` escolhe a última chave anterior ou igual à decisão.
`allow_exact_matches=True` permite uma medição no próprio instante,
com idade zero. Essa é a semântica descrita na
[documentação do pandas](https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html).

Não há `tolerance` nessa busca. Isso é deliberado: queremos conservar
qual era a última amostra, mesmo que esteja expirada. Aplicar a tolerância
já no encontro temporal apagaria seu timestamp das linhas sem correspondência.

Depois calculamos:

```text
idade = timestamp_da_decisão - timestamp_da_amostra
usable = amostra encontrada E idade entre 0 e limite E valor preenchido
```

As fronteiras são inclusivas: com limite de 180 segundos, idade 180 ainda
é permitida. Somente `value` vira `NaN` quando `usable` é falsa.
`sample_time` e idade permanecem para distinguir amostra velha de ausência
de histórico. Sem nenhuma amostra anterior, o timestamp é `NaT` e a idade
é desconhecida.

## 5. A conta dos 2, 7 e 12 segundos

Considere amostras `(00s, valor 0)` e `(10s, valor 10)`, com limite de cinco
segundos:

| Decisão | Amostra encontrada | Idade | `usable` | Valor |
|---|---|---:|---|---:|
| 02s | 00s | 2s | True | 0 |
| 07s | 00s | 7s | False | `NaN` |
| 12s | 10s | 2s | True | 10 |

Em 07s, `nearest` preferiria 10s: distância de três segundos, contra sete
até 00s. Usaria uma medição posterior à decisão e poderia antecipar uma
mudança que ainda não estava observável. Retenção sem limite devolveria
0, escondendo a expiração. Nosso resultado mantém 00s e idade sete como
evidência, mas recusa seu valor para uso.

Alterar o valor dos 10s deve mudar a decisão dos 12s, preservando 02s e
07s. Essa contraprova examina acesso temporal, além de conferir números.

## 6. Por que o último `NaN` não deve desaparecer

Se a última medição encontrada tem valor `NaN`, sua linha continua sendo
a amostra mais recente. A função não remove essa linha antes da busca,
não busca outra mais antiga preenchida e não usa uma posterior.
`sample_time` e idade são preservados; `usable` fica falsa.

Pular esse `NaN` criaria uma política diferente: faria um valor antigo
parecer a informação atual. Qualquer recuperação assim precisaria ser
uma transformação declarada e avaliada, não um preenchimento escondido.

## 7. Rótulos e IDs ficam fora das medições

O sincronizador recebe somente timestamps e valores. As anotações são
retrospectivas e ficam em tabela separada. `Anomaly`, `Rare Event` e
`Communication Gap` permanecem categorias distintas. Ausência de anotação
recebe `unannotated`, sem comprovar normalidade física.

Um ID pode aparecer em vários canais e intervalos. Assim, as 33 linhas
de anotação e os dez IDs documentados no recorte não representam 33
falhas independentes. Uma lacuna medida pelo intervalo entre amostras
também não desaparece por faltar o rótulo `Communication Gap`.

A associação à grade usa intervalos fechados, incluindo início e fim.
Um evento pontual pode não coincidir com a grade; ele continua na tabela
de eventos. Não prolongamos anotações para forçar coincidências. IDs,
categorias e flags retrospectivas não entram como features de um detector.

## 8. Como conferir e executar

Na raiz `C:\renewable-forecast-lab`, com o ambiente existente ativo, confira
o contrato sem ler o ano completo:

```powershell
python satellite-anomaly-monitor/scripts/executar_m10_1.py --autoria satellite-anomaly-monitor/notebooks/m10_sincronizacao_autoral.py --verificar
```

Para aplicar a mesma função ao recorte real:

```powershell
python satellite-anomaly-monitor/scripts/executar_m10_1.py --autoria satellite-anomaly-monitor/notebooks/m10_sincronizacao_autoral.py
```

Os testes pequenos, sem o ano ESA, são executados com:

```powershell
python -m unittest discover -s satellite-anomaly-monitor/tests -p test_m10_sincronizacao_autoral.py -v
```

O modo autoral confronta a grade real inteira com a referência. Cada
execução recebe pasta própria em `reports/m10_1`; o recibo, perfil dos
canais e relatório identificam os resultados. Nenhum detector é treinado.

## 9. O alcance da causalidade deste contrato

A busca evita amostras posteriores no relógio adotado. Sua causalidade
depende da hipótese de que timestamp de medição é também disponibilidade.
Não há registro de chegada ao solo que comprove essa latência.

O eixo original das medições não informa fuso; a interpretação conjunta
em UTC foi assumida na preparação do recorte. Unidades e subsistemas são
anonimizados, portanto valores não podem ser chamados de temperatura,
tensão ou severidade física. A tabela fornece rastreabilidade temporal
para a próxima etapa; não demonstra operação normal, falha física ou
desempenho de detecção.

## 10. Resultado da aplicação local

A execução Windows `20261118T203614Z_7e13daae` foi concluída usando a função
autoral. Passaram os cinco grupos, os dez testes adicionais e a comparação
integral da tabela com a referência. A auditoria independente por
`searchsorted` também confirmou os arquivos completos.

O [parecer](../reports/parecer_m10_1.md) responde às quatro perguntas da
atividade e mostra uma reutilização real de `sample_time`, além das
contagens e limitações. O
[resultado](../reports/m10_1/20261118T203614Z_7e13daae/resultado.json),
o [perfil](../reports/m10_1/20261118T203614Z_7e13daae/perfil_canais.csv)
e o [relatório HTML](../reports/m10_1/20261118T203614Z_7e13daae/relatorio.html)
ficam preservados na mesma pasta.
