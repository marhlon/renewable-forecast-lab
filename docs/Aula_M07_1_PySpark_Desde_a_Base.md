# M07.1 — entender a transformação antes de analisar o plano

19/10/2026 · Retomada após `Texto colado(10).txt` · Marlon Alves Bomfim

**Objetivo desta retomada:** conseguir ler uma transformação PySpark simples e dizer o que cada linha faz aos dados. A tarefa de comparar `Exchange`, shuffle e partições fica adiada até essa compreensão. O log de infraestrutura não é a aula de PySpark.

## O que aconteceu e quais arquivos faltaram

As duas execuções do log iniciaram Spark 4.0.1, mas falharam ao carregar `libzstd-jni` em `/tmp`, durante a primeira coleta do resultado. A mensagem decisiva foi `failed to map segment from shared object`. A leitura inicial já havia encontrado 8.760 registros e 365 datas; isso não significa que a transformação foi concluída.

A falha é compatível com restrição de execução na montagem temporária usada pelo contêiner. Zstd é o codec de compressão do Parquet normalizado: ele precisa carregar uma biblioteca nativa. A correção explicita `exec` na montagem de `/tmp` e imprime/verifica a presença de `noexec` antes de iniciar Spark. O log recebido não contém a tabela de montagens; a causa de montagem é um diagnóstico sustentado pelo erro e pela configuração, não uma inspeção direta do Docker no seu PC.

| Arquivo | Para que serve | Como aparece |
| --- | --- | --- |
| `scripts/executar_m07_spark.py` | Abre o contêiner e coordena a execução | Código entregue pelo professor |
| `tools/m07_transformacao.py` | Lê dados, transforma e compara resultados | Código entregue pelo professor |
| `notebooks/transformacao_spark.py` | Sua SQL e função de classificação | Arquivo que você editou |
| `results/real/qualidade_diaria.csv` | Uma linha por dia, incluindo qualidade | Gerado após a classificação passar |
| `results/real/plano_spark_sql_autoral.txt` | Explica como Spark pretende executar sua SQL | Gerado quando o programa chega à sua SQL |
| `reports/scale_comparison.md` | Seu texto interpretando a comparação | Seria escrito por você; nunca foi geração automática |

Os dois primeiros resultados acima ficam dentro de uma pasta de execução em `reports/scale/CJU_BA5EIGT/m07_1/<run_id>/`. As tentativas `20261019T172422Z_877bd8f9` e `20261019T174519Z_9fe0bb39` falharam antes desses resultados. Podem conter planos parciais da implementação DataFrame, mas não o plano autoral solicitado nem um recibo final aprovado. Você não precisa procurar um resultado que o programa não alcançou.

## 1. A tarefa de dados, sem ferramentas

Considere esta miniatura didática. Ela não substitui seu Parquet real:

| din_instante | val_geracao |
| --- | ---: |
| 2026-01-01 00:00 | 0 |
| 2026-01-01 01:00 | NULL |
| 2026-01-01 02:00 | 12 |

Queremos resumir por dia. Em 01/01 há três registros, dois valores conhecidos e média `(0 + 12) / 2 = 6`. O NULL não é convertido em zero e não entra no denominador da média. Zero entra: é uma medição conhecida.

O calendário também contém 02/01, mesmo sem registros. O resultado diário deve conservar esse dia com zero presentes, zero válidas e média NULL. Esse é o problema que as operações abaixo resolvem.

## 2. Quatro nomes que estavam aparecendo sem explicação suficiente

| Nome | Significado nesta aula |
| --- | --- |
| Spark | Motor que executa as transformações de dados |
| PySpark | Interface Python usada para dar instruções ao Spark |
| `spark` | Objeto `SparkSession`: ponto de entrada para ler dados e executar SQL |
| DataFrame | Tabela com colunas e tipos, associada a um plano de computação; suas linhas não precisam estar todas materializadas na memória do Python |

`horaria`, `resumo` e `diario` são nomes de variáveis escolhidos no programa. Não são palavras especiais da biblioteca. No projeto, a função demonstrada recebe `horaria` e `dias` como argumentos; o controlador já leu o Parquet e construiu o calendário.

Os trechos seguintes explicam esse contexto. Não devem ser colados isoladamente no PowerShell: `horaria` depende de uma sessão e de uma leitura já existentes. O comando de execução completo está no fim.

## 3. Ler as primeiras linhas

```python
from pyspark.sql import functions as F

com_dia = horaria.withColumn(
    "dia",
    F.to_date("din_instante"),
)
```

`functions as F` importa as funções de Spark e lhes dá o apelido `F`. Não importa um conjunto de dados e não é um loop.

`F.to_date("din_instante")` constrói a expressão que extrai a data dessa coluna: `2026-01-01 02:00` passa a `2026-01-01` na nova coluna. O timestamp original permanece na tabela.

`withColumn("dia", expressão)` devolve outro DataFrame, acrescentando a coluna `dia`. Se esse nome já existisse, a coluna seria substituída no DataFrame devolvido. O nome `com_dia` recebe esse resultado; `horaria` não é modificada no lugar.

Em SQL, a ideia é:

```sql
SELECT *, CAST(din_instante AS DATE) AS dia
FROM geracao_horaria;
```

## 4. Agrupar e calcular

```python
resumo = com_dia.groupBy("dia").agg(
    F.count("*").alias("horas_presentes"),
    F.count("val_geracao").alias("horas_validas"),
    F.avg("val_geracao").alias("geracao_media_mwmed"),
)
```

Leia de fora para dentro: agrupar as linhas de `com_dia` pela coluna `dia`; para cada grupo, calcular as expressões dentro de `agg`.

- `groupBy("dia")` corresponde ao `GROUP BY dia` do SQL.
- `agg(...)` reúne as agregações que queremos calcular em cada grupo.
- `F.count("*")` conta as linhas. Aqui ainda não houve JOIN: as três linhas são observações reais, inclusive a de geração nula.
- `F.count("val_geracao")` conta valores não nulos: dois.
- `F.avg("val_geracao")` calcula a média dos valores não nulos: seis.
- `.alias("horas_presentes")` dá nome à coluna calculada. Corresponde a `AS horas_presentes`.

SQL equivalente sobre a tabela com a coluna `dia`:

```sql
SELECT dia,
       COUNT(*) AS horas_presentes,
       COUNT(val_geracao) AS horas_validas,
       AVG(val_geracao) AS geracao_media_mwmed
FROM geracao_com_dia
GROUP BY dia;
```

Até aqui o dia 02/01 não aparece: não há linhas dele para agrupar. Nenhum GROUP BY inventa sozinho o calendário faltante.

## 5. Conservar os dias vazios

```python
diario = dias.join(resumo, "dia", "left")
diario = diario.fillna(
    0,
    subset=["horas_presentes", "horas_validas"],
)
```

`dias` é um DataFrame com o calendário completo. `join(..., "dia", "left")` usa a coluna `dia` para relacionar as tabelas e preserva todas as linhas da tabela à esquerda: `dias`.

Em 02/01, o resumo não possui correspondência e suas colunas ficam NULL. `fillna` troca por zero **somente as duas contagens listadas**. A média permanece NULL, porque não sabemos a geração desse dia.

| dia | horas_presentes | horas_validas | geracao_media_mwmed |
| --- | ---: | ---: | ---: |
| 2026-01-01 | 3 | 2 | 6 |
| 2026-01-02 | 0 | 0 | NULL |

A implementação demonstrada agrega antes do JOIN. Sua SQL agrega depois do JOIN e, por isso, usa `COUNT(h.din_instante)` para distinguir linhas reais da linha artificial do dia vazio. As duas estratégias podem produzir o mesmo resultado; a posição da contagem muda o cuidado necessário.

## 6. Criar uma fórmula por linha

```python
diario = diario.withColumn(
    "cobertura",
    F.col("horas_validas") / F.lit(24.0),
)
```

`F.col("horas_validas")` referencia a coluna. Não busca um único número para o Python. `F.lit(24.0)` representa uma constante dentro da expressão Spark. A divisão é aplicada pelo motor às linhas resultantes.

Para 01/01, cobertura é `2 / 24 = 0,08333`, ou 8,33%. Para 02/01, é `0 / 24 = 0`. O contrato considera 24 posições horárias por data; não estamos resolvendo horário de verão nesta unidade.

## 7. Entender a função que você escreveu

```python
diario_com_qualidade = diario.withColumn(
    "qualidade",
    F.when(F.col("horas_validas") == 24, "completo")
    .when(
        (F.col("horas_validas") >= 1)
        & (F.col("horas_validas") <= 23),
        "parcial",
    )
    .when(F.col("horas_validas") == 0, "sem_dados")
    .otherwise(None),
)
```

É o equivalente a `CASE WHEN ... THEN ... ELSE ... END`. Cada condição constrói uma expressão Spark. A primeira condição satisfeita determina o texto. `otherwise(None)` deixa NULL fora dessas faixas; neste contrato, as contagens válidas ficam de 0 a 24.

O `&` combina duas condições de coluna; cada comparação fica entre parênteses. O `and` comum do Python tentaria decidir a verdade dos objetos no próprio Python e não serve para essa combinação de expressões Spark.

A saída didática é `parcial` para 01/01 e `sem_dados` para 02/01. Você usou a API corretamente; agora a meta é conseguir explicar por quê.

## 8. Por que o erro só apareceu no collect?

As transformações anteriores constroem o que deve ser calculado. Spark pode analisar tipos e ler metadados antes, mas o cálculo das linhas ocorre quando uma action solicita o resultado.

| Operação | Efeito |
| --- | --- |
| `withColumn`, `groupBy(...).agg(...)`, `join` | Constroem transformações |
| `diario_com_qualidade.show()` | Executa o necessário para mostrar linhas no terminal; não salva CSV |
| `diario_com_qualidade.collect()` | Executa e traz todas as linhas do resultado para o Python do driver |
| `diario_com_qualidade.explain()` | Mostra o plano; não é a tabela de resultados |

O programa limita a coleta ao resultado diário pequeno. Não se deve trazer indiscriminadamente uma tabela enorme para o Python. Um plano pode ser impresso mesmo quando a leitura efetiva dos dados depois falha — exatamente a distinção observada no seu log.

## 9. Retomada técnica, uma execução

Salve `renewcast_m07_base_20261019.zip` na raiz do projeto. Ele atualiza os dois arquivos de infraestrutura e acrescenta esta aula; não inclui nem substitui `notebooks/transformacao_spark.py`. Requer que a correção anterior de usuário/cache já esteja aplicada, como confirmado no seu log.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    Set-Location C:\renewable-forecast-lab
    conda activate renewable-forecast
    Expand-Archive -LiteralPath .\renewcast_m07_base_20261019.zip -DestinationPath . -Force
    python scripts/executar_m07_spark.py --autoria
    if ($LASTEXITCODE -ne 0) {
        throw 'A execução ainda falhou. Preserve o erro; não execute a rodada de quatro partições.'
    }
}
```

O programa deve imprimir `montagem noexec=False` e, se concluir, `Concluído: autoria; entrada preservada; hashes conferidos.`. Essa confirmação ainda precisa vir do seu computador. Não solicitamos repetir a rodada com quatro partições agora. A imagem e as dependências não mudaram; o build pode aproveitar o cache existente.

**Sua pequena entrega agora:** sem mudar arquivos, suponha que a geração NULL de 01h seja corrigida para 6. Diga quantas horas presentes e válidas o resumo terá e qual será a média. Depois explique por que `F.count("*")` e `F.count("val_geracao")` agora coincidiriam. Essa resposta orienta a próxima explicação; não é mais uma bateria de testes.

## Fontes e limites

As operações foram executadas pelo professor em Spark 4.0.1 no Linux nativo, incluindo leitura Parquet com Zstd e os valores didáticos. Não foi possível executar Docker ou reproduzir uma montagem noexec neste ambiente. O novo código detecta essa condição no destino; não declaramos o Docker do aluno já aprovado.

Referências oficiais: [introdução a DataFrames e avaliação lazy](https://spark.apache.org/docs/4.0.1/api/python/getting_started/quickstart_df.html), [withColumn](https://spark.apache.org/docs/4.0.1/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.withColumn.html), [semântica de NULL](https://spark.apache.org/docs/4.0.1/sql-ref-null-semantics.html), [montagens temporárias Docker](https://docs.docker.com/engine/storage/tmpfs/), [relato e resposta do mantenedor sobre Zstd em noexec](https://github.com/luben/zstd-jni/issues/315).
