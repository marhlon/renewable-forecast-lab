# M07.1 — a mesma transformação em DuckDB, PySpark e Spark SQL

**Objetivo:** construir uma tabela diária de qualidade da série ONS e demonstrar que a mudança de motor preservou datas, contagens, nulos e estatísticas. Depois, explicar o que o plano de execução precisou fazer. A entrada é a série já existente: `data/interim/CJU_BA5EIGT_hourly.parquet`.

Esta é a primeira unidade prática de M07. Usaremos o recorte pequeno para tornar os erros verificáveis antes de ampliar volume. Spark em `local[2]` usa a máquina local; este exercício não representa execução em um cluster nem prova de escala. Delta e Databricks permanecem nas unidades seguintes.

## 1. Entrega e divisão de trabalho

| Parte | Responsável | Arquivo |
| --- | --- | --- |
| Validação da entrada, DuckDB, PySpark DataFrame, comparação e planos | Professor; já implementado | `tools/m07_transformacao.py` |
| Ambiente isolado e execução Docker com recibo | Professor; já implementado | `scripts/executar_m07_spark.py` |
| Consulta equivalente em Spark SQL | Aluno | `SQL_AUTORAL` em `notebooks/transformacao_spark.py` |
| Classificação da cobertura com expressões PySpark | Aluno | `classificar_cobertura` no mesmo arquivo |
| Explicação do plano e da alteração de particionamento | Aluno | `reports/scale_comparison.md` |

A infraestrutura compara valores, mas não certifica autoria independente. Você pode consultar a implementação DataFrame e as referências. Registre ajuda recebida e explique as escolhas com suas palavras.

## 2. Contrato antes do código

A série contém um único conjunto, com chave `din_instante` única, valores horários e `val_geracao` numérica. Nulos na geração são permitidos e contados. Timestamp nulo, repetido, fora da hora inteira, geração infinita/NaN explícito ou tipo incompatível são recusados. O script não interpola nem remove linhas para fazer a conferência passar.

Os rótulos de tempo existentes são preservados **sem atribuir UTC**. Spark usa `TIMESTAMP_NTZ`. A configuração de sessão UTC não transforma esses rótulos em instantes UTC comprovados. O calendário esperado tem 24 posições horárias por data; não é uma reconstrução de dias físicos com mudanças de horário de verão. Datas de borda também são avaliadas contra 24 posições. O fuso e a semântica início/fim do intervalo ONS continuam com os limites já registrados.

O nome do conjunto é conferido em `id_ons_conjunto` quando essa coluna existe. Sem a coluna, fica registrado como declaração, não como identificação demonstrada pelo nome do arquivo.

Para cada data entre a mínima e a máxima, inclusive dias sem nenhuma linha:

| Coluna | Definição |
| --- | --- |
| `dia` | Data do rótulo de referência |
| `horas_esperadas` | 24 |
| `horas_presentes` | Número de linhas daquela data |
| `horas_validas` | Número de valores de geração não nulos; zero conta |
| `horas_nulas` | Presentes − válidas |
| `horas_ausentes` | 24 − presentes |
| `cobertura` | Válidas / 24, em ponto flutuante |
| `geracao_media_mwmed` | Média apenas dos valores observados; NULL se nenhum |
| `geracao_min_mwmed` | Mínimo observado; NULL se nenhum |
| `geracao_max_mwmed` | Máximo observado; NULL se nenhum |

A média parcial continua parcial: 6 MWmed em duas horas não representa a média comprovada de todo o dia. Não multiplicamos essa média por 24 para inventar energia diária.

Há duas identidades úteis: `presentes + ausentes = 24` e `validas + nulas = presentes`. Elas não bastam para provar correção, mas ajudam a localizar erros.

## 3. Primeiro execute a demonstração

Abra o Docker Desktop já utilizado em M06. Salve o ZIP na raiz do projeto e execute este bloco no PowerShell:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m07_spark_20261017.zip -DestinationPath . -Force
python scripts/executar_m07_spark.py
```

O primeiro build baixa Java 17, PySpark 4.0.1, Py4J 0.10.9.9 e DuckDB 1.4.1; o download do Spark tem centenas de MB. As versões desta unidade ficam isoladas do ambiente do modelo. Builds seguintes reutilizam cache. São usados 2 CPUs e 3 GiB no contêiner; nenhuma API precisa ficar aberta e nenhuma porta é publicada. A transformação roda sem acesso externo à rede após o build.

O arquivo original é montado somente para leitura. Uma cópia com duas colunas e timestamp em microssegundos é criada na execução para compatibilidade Parquet; isso não desloca horários. Os dois motores recebem exatamente essa cópia. O hash do original é conferido antes e depois.

O comando imprime a **pasta exata da execução**, sempre nova:

`reports/scale/CJU_BA5EIGT/m07_1/<run_id>/`

Dentro dela, `results/real/` contém `duckdb_diario.csv`, `spark_dataframe_diario.csv`, `comparacao.json`, `tempos.json`, `plano_duckdb.txt` e `plano_spark_dataframe.txt`. `results/verification.json` registra entrada, versões, parâmetros e hashes. `host_verification.json` registra imagem e conferência no Windows. `latest_run.json`, na pasta `m07_1`, aponta para a última execução aprovada.

Se ocorrer falha, o comando retorna código diferente de zero, preserva `pipeline.log`/`failure.json` e não promove a execução como aprovada. Use o erro concreto para diagnosticar. Não reinstale o projeto nem troque o arquivo de entrada por uma base inventada.

## 4. Ler o código como um plano

Abra `diario_dataframe` em `tools/m07_transformacao.py`:

1. `withColumn` extrai a data de cada rótulo horário.
2. `groupBy(...).agg(...)` define contagens e estatísticas por data.
3. `LEFT JOIN` parte do calendário completo, preservando datas sem observação.
4. `fillna` atinge somente as duas contagens. Preencher a média com zero inventaria geração.
5. `select` define o contrato final.

Essas expressões constroem um plano. O resultado é efetivamente materializado pela action `collect()` no controlador, depois da agregação e com limite de linhas. A leitura do schema ou metadados pode realizar I/O antes disso; “lazy” não significa ausência absoluta de trabalho até a action.

**Por que o agrupamento envolve troca de dados?** Linhas da mesma data podem estar em partições diferentes. Uma agregação parcial reduz dados localmente; um `Exchange` pode redistribuir as parcelas por chave; a agregação final reúne os resultados. Identifique no plano recebido qual `Exchange` pertence à agregação e se existe outro associado ao JOIN. Não atribua todos os `Exchange` ao mesmo operador.

**Partição não é CPU.** `spark.sql.shuffle.partitions` controla a quantidade de partições de shuffle das operações pertinentes. Não altera `local[2]` para quatro núcleos e não é o número de arquivos originais. Mais partições podem reduzir trabalho por tarefa, mas também criam overhead. O protocolo desliga AQE apenas para facilitar a comparação didática; não é uma recomendação de configuração de produção.

Spark SQL e DataFrame usam o mesmo motor Spark SQL. Resultados iguais podem vir de planos físicos muito parecidos. A comparação com DuckDB adiciona outra implementação; o caso manual evita que dois motores apenas repitam o mesmo erro lógico.

## 5. Sua programação

Edite somente `notebooks/transformacao_spark.py` nesta etapa.

**A. `SQL_AUTORAL`:** escreva uma consulta SELECT, podendo usar CTEs. Existem duas views: `geracao_horaria(din_instante, val_geracao)` e `calendario_dias(dia)`. Produza as dez colunas do contrato. Sugestões: `CAST(... AS DATE)`, `COUNT(*)`, `COUNT(val_geracao)`, `AVG`, `MIN`, `MAX`, `LEFT JOIN` e `COALESCE`. Para cobertura, use divisor `CAST(24 AS DOUBLE)`; um literal decimal pode produzir arredondamento diferente no Spark.

O detalhe importante é **onde contar**. Se você fizer primeiro um LEFT JOIN do calendário com as linhas horárias, `COUNT(*)` também contará a linha vazia criada pelo JOIN para um dia ausente. Agregar as observações antes do JOIN torna essa distinção mais clara. Explique isso no parecer.

**B. `classificar_cobertura`:** preserve todas as colunas e acrescente `qualidade` usando `withColumn`, `F.when` e `otherwise`: 24 válidas → `completo`; 1–23 → `parcial`; zero → `sem_dados`. Retorne um DataFrame. Não use UDF, pandas ou coleta para Python dentro da transformação.

Depois de salvar, execute:

```powershell
python scripts/executar_m07_spark.py --autoria
```

O modo autoral compara Spark SQL com DuckDB, confere sua classificação e garante que você não mudou as demais colunas. Acrescenta `spark_sql_diario.csv`, `qualidade_diaria.csv` e `plano_spark_sql_autoral.txt`. Não é necessário reconstruir manualmente a imagem para editar a autoria: os arquivos são montados em leitura.

## 6. Contraprova que sua solução precisa explicar

O programa também executa um exemplo sintético explícito. Ele serve para conferir semântica e não substitui a série real:

| Dia | Entrada | Presentes | Válidas | Nulas | Ausentes | Média | Qualidade |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 01/01 | 00h=0; 01h=NULL; 02h=12 | 3 | 2 | 1 | 21 | 6 | parcial |
| 02/01 | Nenhuma linha | 0 | 0 | 0 | 24 | NULL | sem_dados |
| 03/01 | 24 linhas, todas NULL | 24 | 0 | 24 | 0 | NULL | sem_dados |
| 04/01 | 24 linhas, todas 10 | 24 | 24 | 0 | 0 | 10 | completo |

No primeiro dia, cobertura = 2/24. Zero é uma medição válida. No terceiro, houve linhas sem valores; no segundo, faltaram as próprias linhas. Ambos têm qualidade `sem_dados`, mas as contagens preservam causas diferentes.

## 7. Uma alteração controlada e seu parecer

Após o modo autoral passar com duas partições, altere apenas o parâmetro:

```powershell
python scripts/executar_m07_spark.py --autoria --shuffle-partitions 4
```

Compare os dois `plano_spark_dataframe.txt` e `plano_spark_sql_autoral.txt`. Procure a quantidade em `hashpartitioning(..., 2)` e `hashpartitioning(..., 4)` quando esse operador estiver presente. O conteúdo da tabela deve continuar equivalente. Aumentar partições não autoriza mudar a lógica.

Escreva de 15 a 25 linhas em `reports/scale_comparison.md`, citando os dois `run_id`:

1. Explique a diferença entre `COUNT(*)` e `COUNT(val_geracao)` no caso 01/01.
2. Aponte a action e um shuffle real do seu plano, com o operador correspondente.
3. Diga o que mudou de 2 para 4 partições e o que permaneceu igual no resultado.
4. Interprete os tempos com os limites abaixo. Qual evidência faltaria para decidir distribuir o volume total?
5. Explique por que uma média diária com cobertura parcial não comprova a geração média de 24 horas.

Os tempos são instrumentação exploratória: uma passagem por motor, ordem fixa, caches e JIT sem controle. O início da JVM aparece separado. SQL executa depois do DataFrame no modo autoral, podendo aproveitar aquecimento. Não chame uma diferença observada de superioridade comprovada. O custo de coordenação pode dominar um recorte pequeno; o mérito profissional está em defender a ferramenta proporcional ao problema.

**Envie:** saída do modo autoral, `notebooks/transformacao_spark.py`, seu parecer e os arquivos `host_verification.json`, `results/verification.json` e os dois planos Spark da última execução. Isso encerra uma entrega de transformação com explicação, não uma nova rodada de treino do modelo.

**Depois:** M07.2 usará a transformação para estudar tabela Delta, versões e correção de dados. A escolha de ambiente Databricks pertence a M07.3; não é necessário contratar serviço para esta aula.

## 8. Verificação e referências

O professor executou o núcleo Spark/DuckDB em Linux nativo, com Java 17, em dados sintéticos identificados. O documento `Verificacao_E95_Professor.json` delimita os resultados efetivos. Docker Desktop/Windows e o Parquet real do aluno dependem da execução acima; não são declarados como já executados pelo professor.

Fontes primárias consultadas em 17/10/2026:

- [PySpark 4.0.1 — instalação e Java 17+](https://spark.apache.org/docs/4.0.1/api/python/getting_started/install.html).
- [PySpark DataFrame — avaliação lazy, actions e risco de collect](https://spark.apache.org/docs/4.0.1/api/python/getting_started/quickstart_df.html).
- [Spark SQL — partições de shuffle e AQE](https://spark.apache.org/docs/4.0.1/sql-performance-tuning.html).
- [DataFrame.explain](https://spark.apache.org/docs/4.0.1/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.explain.html).
- [DuckDB — leitura e escrita Parquet](https://duckdb.org/docs/current/data/parquet/overview).

As versões fixadas são escolhas de isolamento desta unidade, não afirmações de que sejam as versões mais recentes. A imagem efetivamente construída fica identificada no recibo.
