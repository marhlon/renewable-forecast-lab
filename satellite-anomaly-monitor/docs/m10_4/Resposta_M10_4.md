# Devolutiva M10.4 — estabilidade e ablação

Execução Windows: **`20261124T152509Z_3878d5e2`**. Foram reutilizadas as
rodadas M10.2 `20261119T101049Z_253ff59f` e M10.3
`20261123T195301Z_332fb306`, com a política original preservada.

A [função implementada](../../notebooks/m10_4_limite_autoral.py) percorre a
grade sem retirar lacunas. Para cada fim com pelo menos `k` posições
utilizáveis consecutivas, calcula o mínimo dos últimos `k` escores; só
substitui o melhor resultado quando encontra um valor estritamente maior.
Assim mantém o primeiro fim em empate e admite escores negativos. Sem
janela válida, devolve `None` nos dois campos.

No exemplo da Aula 01, para `k=2`, o resultado é:

```python
{"limiar_maximo": 0.88, "indice_confirmacao": 5}
```

Para `k=1`, é `0.90`, no índice 2. A saída informa um limite matemático
de alcance da regra, não recomenda recalibrar o limiar por esse valor.

## 1. Rastrear a falha no corte

Na semente 17, em **2011–2013, tratado como diagnóstico retrospectivo**:

| Medida | `tres_canais` | `sem_52` |
|---|---:|---:|
| Corte próprio da variante | 0,7199442558 | 0,7201268845 |
| S1: maior escore utilizável | 0,7164359651 | 0,7541511975 |
| S2: maior mínimo dos pares utilizáveis | 0,6382295271 | 0,6915642217 |
| Pontos com escore **≥ corte** | 0 | 4 |
| Pontos exatamente iguais ao corte | 0 | 0 |
| IDs detectados / observáveis | 0/8 | 0/8 |

Em `tres_canais`, **S1 < corte**: nem uma leitura consegue atravessar o
limiar. S2 também fica abaixo, com margem `S2 - corte = -0,0817147288`.
Em `sem_52`, **S1 > corte, mas S2 < corte**: surgem picos, porém nenhum
par consecutivo inteiramente utilizável sustenta duas confirmações; a
margem do melhor par é `-0,0285626628`.

Como S2 é menor que o corte, os quatro pontos altos de `sem_52` não podem
ser adjacentes entre si em uma sequência utilizável. Com uma confirmação,
admitiriam **quatro inícios isolados** neste recorte. Essa é uma dedução
dos limites e da contagem, sem executar outra política.

Quatro inícios globais não significam quatro IDs detectados: é preciso
saber se cada início cai dentro de um intervalo elegível, se a categoria
é ignorada e se o ID já recebeu crédito. A contagem não mostra essas
posições. Da mesma forma, S2 calculado dentro de um ID não garante novo
alarme nele: a sequência pode ter começado antes, ou o crédito pode ter
sido atribuído a outro ID.

As outras ablações também falharam na semente 17: `sem_50` ficou com
S1=0,6940221356 abaixo do corte 0,7484678621; `sem_51` teve dois pontos
≥0,7221181150, mas S2=0,6898463770 abaixo desse corte. Assim se distinguem
ausência de cruzamento e cruzamentos sem confirmação. Todas as 12
combinações de quatro variantes e três sementes terminaram com 0/8 no
diagnóstico; nenhuma retirada de canal recuperou a detecção nessa regra.

## 2. Defender o desenho da ablação

Escolhi **`id_145` no desenvolvimento**. A referência de três canais o
detectou nas sementes 17, 29 e 41; `sem_50` o perdeu nas três. Retirar 51
também o perdeu nas sementes 17 e 29, mas preservou a detecção na 41;
`sem_52` preservou esse ID nas três sementes. Essa comparação está em
[`mudancas_por_id.csv`](../../reports/m10_4/20261124T152509Z_3878d5e2/mudancas_por_id.csv).

O efeito não se resume à contagem de IDs: na semente 17, o atraso de
`id_134` passou de **26,82835 min** nos três canais para **36.221,82835 min**
em `sem_50`, embora o ID ainda conste como detectado. Por isso “dois IDs
detectados” não descreve sozinho a utilidade dessa variante.

A comparação mantém as mesmas **136.202 linhas de ajuste de 2004–2007**,
a transformação pela mediana/MAD originais de cada canal, a configuração
das florestas, as sementes 17/29/41 e os mesmos instantes e IDs de
avaliação. São 105.165 instantes utilizáveis no desenvolvimento e 105.212
no diagnóstico, exigindo os três canais disponíveis para todas as
variantes. Retirar uma entrada significa ajustar uma floresta de duas
entradas, não retirar uma coluna de um modelo que continua esperando três.

Cada variante recebe o quantil de desenvolvimento **0,9995, método
`higher`**, aplicado aos seus próprios escores; não se transporta o mesmo
valor numérico de corte entre modelos. O orçamento e a regra de duas
confirmações permanecem os mesmos, mas o quantil comum não garante taxas
empíricas iguais. Por exemplo, na semente 17 as taxas sem anotação no
desenvolvimento foram **0,0037969802/dia equivalente** para três canais e
**0,0056954703/dia equivalente** para `sem_52`.

Se a variante pudesse acrescentar horários em que o canal omitido estava
indisponível, mudariam cobertura, exposição e possivelmente IDs observáveis.
O resultado misturaria a mudança da representação com uma mudança da
população avaliada. A definição dos eventos também conserva as anotações
dos três canais, inclusive do canal retirado.

A perda de `id_145` mostra sensibilidade do sistema — representação,
floresta e corte obtido pela mesma regra — à retirada do canal 50.
**Não identifica a origem física da anomalia.** Faltam unidades e regime
de operação, e canais correlacionados podem carregar informação semelhante;
três sementes do mesmo recorte não são novos períodos nem um intervalo de
confiança sobre generalização.

## 3. Decidir e transferir

Recomendo manter a referência para diagnóstico e não promover nenhuma
variante: todas tiveram 0/8 em 2011–2013, de modo que a taxa zero de alarmes
sem anotação seria enganosa se lida sozinha.
Para um candidato com diferenças normalizadas entre canais, pré-registraria
um teste em um grupo de três canais de outra missão ainda não analisada,
escolhido exclusivamente por metadados antes de ler suas medições, com
60% iniciais do histórico para ajuste, 20% seguintes para desenvolvimento
e os 20% finais bloqueados como confirmação.
Contaria como ganho mais IDs observáveis detectados que o baseline nos
mesmos instantes, sob teto de **0,50 início sem anotação por dia equivalente**,
reportando também atrasos, repetições e ausência de observação, com método,
limiar, confirmação e critérios congelados antes de abrir o bloco final.
Não usaria 2011–2013 para confirmar essa alternativa porque esse período
já orientou o diagnóstico e a formulação da hipótese; uma melhora obtida
depois de consultá-lo continuaria exploratória.

## Arquivos e conferência

Entrega da rodada:
[função](../../notebooks/m10_4_limite_autoral.py),
[resultado.json](../../reports/m10_4/20261124T152509Z_3878d5e2/resultado.json)
e [metricas_ablacao.csv](../../reports/m10_4/20261124T152509Z_3878d5e2/metricas_ablacao.csv).
O [relatório HTML](../../reports/m10_4/20261124T152509Z_3878d5e2/relatorio.html)
mostra as tabelas completas.

Passaram as **sete contraprovas integradas**, a comparação da função nas
janelas reais e os **11 testes adicionais**. A
[auditoria independente](../evidencias_m10_4_local/auditoria_resultados.json)
conferiu os hashes e as tabelas pareadas e recalculou métricas e limites da
referência a partir dos escores persistidos. Para as 11 florestas novas,
os vetores de escores e checkpoints não foram salvos pelo laboratório:
a auditoria verifica coortes, identidades e coerência das tabelas, sem
afirmar que reproduziu essas florestas ou todos os seus escores.
