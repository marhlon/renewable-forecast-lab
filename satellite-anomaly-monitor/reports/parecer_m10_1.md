# M10.1 — sincronização causal da telemetria

O sincronizador associa os canais 50, 51 e 52 a uma grade comum de decisões,
sem consultar amostras posteriores. A grade cobre 2007, tem passo de 90 s e
tolera idade de até 180 s, inclusive. Essa tolerância é uma regra exploratória
da unidade; não representa um compromisso operacional da missão.

## Regra implementada

Para cada canal e instante `g`, a função escolhe a última amostra com
`sample_time <= g`. Calcula `age_seconds = g - sample_time` e considera o
valor utilizável somente quando há amostra, sua idade está entre zero e a
tolerância e o valor está preenchido. A busca usa `backward`, com igualdade
permitida. Essa é a semântica descrita na
[documentação do pandas](https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html).

A expiração é aplicada depois da busca: somente `value` vira `NaN`.
`sample_time` e `age_seconds` permanecem para indicar qual amostra expirou.
Sem passado disponível, ficam `NaT`, `NaN` e `usable=False`. Um zero observado
continua sendo um valor válido. Um `NaN` na última medição não permite buscar
um valor mais antigo conveniente.

As fontes são copiadas antes de ordenar ou converter valores. A grade deve
estar crescente, sem repetições; timestamps duplicados por canal são rejeitados.
Timestamps devem informar fuso e são convertidos para UTC em nanossegundos.
Não se atribui UTC silenciosamente a uma entrada sem fuso.

## Por que há mais linhas utilizáveis que medições

As contagens têm denominadores diferentes:

| Medida por canal | Quantidade |
|---|---:|
| Medições brutas | 348.901 |
| Decisões na grade | 350.400 |
| Decisões com valor utilizável | 350.346 |
| Decisões sem valor utilizável | 54 |
| Medições distintas usadas nas decisões utilizáveis | 348.870 |
| Medições usadas em dois instantes utilizáveis | 1.476 |
| Medições brutas não usadas nas decisões utilizáveis | 31 |

Uma medição pode servir a duas decisões enquanto estiver dentro do limite.
O campo `sample_time` identifica essa reutilização, mesmo quando medições
diferentes possuem valores numéricos iguais. Neste recorte, por canal:

```text
350.346 linhas utilizáveis = 348.870 medições distintas usadas + 1.476 reutilizações
350.346 - 348.901 = 1.476 reutilizações - 31 medições não usadas = 1.445
```

Um exemplo real do canal 50 é a medição de **14/04/2007 às
08:12:31,416 UTC**, valor `0,7427392601966857`:

| Decisão UTC | `sample_time` UTC | Idade | Utilizável |
|---|---|---:|---|
| 14/04/2007 08:13:30 | 14/04/2007 08:12:31,416 | 58,584 s | Sim |
| 14/04/2007 08:15:00 | 14/04/2007 08:12:31,416 | 148,584 s | Sim |

Não foram criadas duas observações físicas. A mesma amostra sustenta duas
linhas da grade. A fração utilizável de 99,9846% mede atendimento à regra de
frescor nessa grade, não taxa de chegada original nem funcionamento normal.
A idade é relativa à decisão histórica de 2007, não ao tempo decorrido até hoje.

Das 54 decisões inválidas por canal, uma não tem amostra anterior: a grade
começa em 01/01 às 00h, antes da primeira medição, às 00:00:31,428 UTC.
As outras 53 apresentam amostra expirada. Não há valores brutos `NaN` neste
recorte; esse caso foi verificado nas contraprovas pequenas.

## O problema de consultar o futuro aos 07 segundos

Na contraprova sintética há valores `(00s, 0)` e `(10s, 10)`, com tolerância de 5 s:

| Decisão | Última amostra disponível | Idade | Saída causal |
|---|---|---:|---:|
| 02s | 00s | 2 s | 0 |
| 07s | 00s | 7 s | `NaN` |
| 12s | 10s | 2 s | 10 |

Em 07s, `nearest` escolheria a amostra de 10s, distante apenas 3 s. Isso
introduziria uma mudança antes de sua disponibilidade e poderia antecipar
artificialmente uma detecção. A avaliação de atraso deixaria de representar
uma decisão possível naquele instante. Já reter 0 sem limite esconderia
a expiração. Alterar o valor de 10s deve mudar a linha de 12s, preservando
as linhas de 02s e 07s. Essa contraprova é sintética, não um evento ESA observado.

## Lacunas medidas e anotações não são a mesma coisa

Há **41 intervalos entre medições maiores que 180 s por canal**, com máximo
de 1.170 s. Isso é calculado nos timestamps da telemetria. Há **zero anotações
`Communication Gap` no recorte**; isso descreve a tabela de anotações. A
ausência dessa categoria não apaga os intervalos medidos nem demonstra que
as anotações esgotam todas as interrupções. Tampouco cada intervalo longo
comprova, sozinho, uma falha de comunicação. Os relógios dos três canais
coincidem neste recorte; somar as contagens não cria 123 eventos independentes.

As **33 linhas de anotação** identificam pares canal/intervalo associados a
**dez IDs distintos**. São sete linhas de `Anomaly`, com três IDs, e 26 de
`Rare Event`, com sete IDs. O mesmo ID pode aparecer em vários canais ou
intervalos. Portanto 33 linhas não equivalem a 33 falhas independentes,
e os dez IDs também não são dez falhas físicas comprovadas.

As categorias permanecem distintas. Um instante sem anotação recebe
`unannotated`, sem declaração de normalidade física. Os intervalos são
fechados nesta unidade; uma anotação pontual sem coincidência com a grade
continua preservada na tabela de eventos. Features e rótulos retrospectivos
ficam em arquivos separados; ID e categoria não entram no sincronizador.

## Limites e compatibilidade

O timestamp da medição é tratado como disponibilidade, mas não há registro
de chegada ao solo para comprovar isso. O índice original das medições não
informava fuso; sua interpretação no mesmo eixo UTC das anotações é hipótese
de trabalho. Converter timestamps com fuso na função não valida essa hipótese
na origem. Os identificadores `subsystem_6` e `physical_unit_3` são anonimizados:
não permitem interpretar valores como temperatura, tensão ou severidade física.

A execução encontrou uma diferença de resolução no pandas 3.0.5: a grade
era criada em microssegundos e a saída em nanossegundos. Os instantes eram
iguais, mas `Series.equals` rejeitava os dtypes diferentes. O executor foi
ajustado para criar a grade explicitamente em UTC/ns. Datas, cadência,
tolerância e valores foram preservados; o código anterior e o log da falha
ficaram em `docs/evidencias_m10_1_local`.

A identidade dos CSVs derivados pode ser conferida pelos SHA-256 de
[`source.json`](../data/reference/esa_mission1_2007/source.json). Isso não
comprova o MD5 do ZIP público completo de 3,8 GB: o fornecimento registra
explicitamente que essa verificação não foi feita. A atribuição e a licença
declaradas na fonte foram mantidas. Esta unidade prepara o contrato dos dados;
não mede a qualidade de um detector nem autoriza uso operacional.

## Código e explicação

[Função implementada](../notebooks/m10_sincronizacao_autoral.py),
[testes adicionais](../tests/test_m10_sincronizacao_autoral.py) e
[explicação passo a passo](../docs/Explicacao_M10_1_Passo_a_Passo.md).

## Execução Windows e evidências

A execução autoral **`20261118T203614Z_7e13daae`** terminou com código zero,
no ambiente existente: Python 3.12.13, NumPy 2.5.3 e pandas 3.0.5.
Passaram os cinco grupos de conferência, os dez testes adicionais e a
comparação integral da grade autoral com a referência. O recibo registra
o SHA-256 do arquivo autoral efetivamente fornecido ao executor.

O resultado local totalizou 1.046.703 medições, 350.400 instantes na grade
e 350.346 instantes com os três canais utilizáveis. Houve 5.732 linhas de
grade anotadas como `Anomaly` e 3.303 como `Rare Event`, em união entre
canais; essas frequências não são contagens de eventos independentes.

Arquivos da execução:
[resultado.json](m10_1/20261118T203614Z_7e13daae/resultado.json),
[perfil_canais.csv](m10_1/20261118T203614Z_7e13daae/perfil_canais.csv),
[grade de features](m10_1/20261118T203614Z_7e13daae/grade_features.csv.gz),
[rótulos separados](m10_1/20261118T203614Z_7e13daae/rotulos_grade.csv.gz),
[cobertura dos eventos](m10_1/20261118T203614Z_7e13daae/cobertura_eventos.csv)
e [relatório HTML](m10_1/20261118T203614Z_7e13daae/relatorio.html).

A [auditoria independente](../docs/evidencias_m10_1_local/auditoria_resultados.json)
terminou com `verified=true`: reconstruiu por `searchsorted` os 350.400
instantes dos três canais, sem importar a função autoral ou a referência.
Conferiu timestamps, idades, valores, flags, perfis, rótulos, eventos e hashes.
Seu [script](../docs/evidencias_m10_1_local/auditar_resultados.py) permite
repetir a conferência nos arquivos preservados:

```powershell
python satellite-anomaly-monitor/docs/evidencias_m10_1_local/auditar_resultados.py
```
