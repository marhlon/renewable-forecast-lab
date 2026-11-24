# M07 — Da série horária à tabela de treino: tempo, lacunas e vazamento

**Problema da aula:** construir, com a série real CJU_BA5EIGT, uma tabela para prever a geração 24 horas à frente, supondo que cada medição demore duas horas para chegar. A tabela precisa continuar correta quando houver uma hora ausente. A seleção para treino deve respeitar quando cada alvo ficou disponível.

**Tempo de trabalho sugerido:** um bloco de 2–3 horas, ajustável ao seu ritmo. A entrega inteira está especificada aqui; não é necessário esperar outra mensagem para receber a próxima instrução.

**O que você produzirá:** tabela Parquet de features/alvos, inspeção do plano, duas contraprovas e uma função de seleção temporal escrita por você. O domínio desta aula é transformação de dados para ML; Delta e Databricks continuam nas próximas unidades do roteiro.

## 1. Revisão concreta da entrega de 25/10

O CSV recebido tem quatro datas e as classificações corretas. O plano recebido contém agregação parcial, `Exchange` e agregação final. Isso comprova a execução dessas operações no exemplo.

O código enviado também contém:

```python
geracao_observada_mwh = F.sum("val_geracao").alias("geracao_observada_mwh")
```

Essa instrução cria um objeto `Column`: uma expressão que descreve uma soma. Ela não adiciona uma coluna ao DataFrame. Para usar a expressão, é preciso entregá-la a uma transformação:

```python
resumo = com_dia.groupBy("dia").agg(
    F.count("*").alias("horas_presentes"),
    F.count("val_geracao").alias("horas_validas"),
    F.avg("val_geracao").alias("geracao_media_mwmed"),
    geracao_observada_mwh,
)
```

O `.select("geracao_observada_mwh")` não procura uma variável Python com esse nome: ele procura uma coluna do DataFrame. Sem a inclusão em `.agg`, a coluna não existe e a análise da consulta falha. Portanto, o código enviado e os resultados anexados não correspondem à mesma versão executada. Não é possível identificar, pelos anexos, qual arquivo estava salvo no momento do comando.

O pacote inclui a correção pontual em `notebooks/aula_calendario_spark.py`. A energia observada correta é 18, NULL, NULL e 240 MWh. Cada observação do exemplo representa a média de uma hora; com intervalos de outra duração, energia exige ponderação pela duração. Essa correção não será outra unidade isolada de aprendizagem.

## 2. O contrato temporal antes de escrever código

Use três instantes diferentes:

| Nome | Significado | Regra desta aula |
| --- | --- | --- |
| `forecast_origin` | Quando a previsão seria emitida | `o` |
| `history_end` | Última hora que já poderia ter chegado pelo atraso assumido | `o - 2 horas` |
| `target_time` | Hora cuja geração queremos prever | `o + 24 horas` |
| `target_available_at` | Quando o valor real do alvo poderia ser usado | `o + 26 horas` |

O atraso é uma hipótese do laboratório. Os timestamps mantêm o eixo de rótulos da série existente; esta aula não confirma o fuso nem se o registro físico representa início/fim de intervalo. Não acrescente `Z` ao corte de treino sem validar esse contrato.

Na origem 08h, com atraso de duas horas, a janela de seis horas contém **01h, 02h, 03h, 04h, 05h e 06h**. Não pode conter 07h ou 08h.

Para atraso `d` e janela de `w` horas, os limites relativos à origem são:

```text
primeira hora = o - (d + w - 1)
última hora   = o - d
```

Com `d=2` e `w=6`, os deslocamentos são **-7 até -2**, inclusive. Existem seis posições porque `(-2) - (-7) + 1 = 6`.

## 3. Por que uma lacuna pode estragar uma feature aparentemente correta

`lag(valor, 2)` significa duas linhas anteriores, na ordenação definida. Só equivale a duas horas quando a grade tem exatamente uma linha por hora.

Na contraprova, a origem é 02/01 às 08h. A observação das 06h foi retirada. As linhas anteriores passam a ser 07h e 05h. Um `lag(2)` aplicado diretamente nessa tabela devolve o valor das 05h, 129, como se fosse das 06h.

O calendário horário reinsere 06h com valor NULL. Agora o mesmo `lag(2)` aponta para a hora certa e devolve NULL.

Isso não significa que 129 seja uma medição inexistente. Ela é uma medição mais antiga. Usá-la como fallback exigiria outra regra, acompanhada da idade do dado. Aqui a feature `geracao_em_history_end` representa exatamente o valor na hora-limite e preserva sua ausência.

No código:

```python
grade = limites.select(
    F.explode(F.sequence("inicio", "fim", F.expr("INTERVAL 1 HOUR")))
    .alias("din_instante")
)
```

- `sequence` constrói a sequência de horas entre o início e o fim.
- `explode` transforma cada elemento dessa sequência em uma linha.
- O `left join` liga cada hora esperada à medição, quando ela existe.
- `registro_presente=False` identifica uma hora criada pelo calendário. A geração continua NULL.

O calendário cobre do menor ao maior timestamp observado. Para exigir cobertura fora desse intervalo, seria necessário fornecer início/fim esperados explicitamente.

## 4. Uma janela mantém as linhas; uma agregação diária reduz as linhas

Na aula anterior, `groupBy("dia").agg(...)` produzia uma linha por dia. Agora precisamos de uma linha por origem, com estatísticas do seu histórico. Usaremos uma janela:

```python
ordem = Window.partitionBy("serie").orderBy("din_instante")
historico = ordem.rowsBetween(-(atraso + janela - 1), -atraso)
```

`partitionBy("serie")` delimita séries independentes para a operação de janela. `orderBy` define a sequência dentro de cada série. `rowsBetween` delimita as posições usadas em cada cálculo. `.over(historico)` aplica a expressão a essa janela para cada linha.

```python
F.count("val_geracao").over(historico)
F.avg("val_geracao").over(historico)
```

A média ignora NULL. Por isso, calcular apenas `avg` seria insuficiente: uma média de duas horas disponíveis poderia ser apresentada como uma média de seis horas. O código calcula também a contagem e só libera a feature quando `horas_validas_historico == janela`.

`lead(valor, 24)` produz o alvo na tabela horária completa. A coluna do alvo serve para treino e avaliação posterior. Ela nunca entra em `FEATURES`, a lista explícita de entradas do modelo.

**Ponto de engenharia:** `partitionBy` da janela não significa gravar diretórios particionados no disco. Nesta entrada existe uma única série, portanto uma janela por série concentra seu processamento em um grupo. Aumentar `spark.sql.shuffle.partitions` não divide automaticamente essa única sequência em quatro janelas independentes. A decisão de usar Spark deve considerar volume, quantidade de séries e custo da infraestrutura; 8.760 linhas cabem facilmente em ferramentas locais.

## 5. Execução e arquivos exatos

Extraia o ZIP na raiz `C:\renewable-forecast-lab`. Ele contém dois scripts em `notebooks/` e esta aula em `docs/`. O novo laboratório usa o recibo da imagem Spark que já funcionou no projeto. Se esse recibo foi movido, `--run-dir` permite informar a pasta correta.

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
python notebooks/laboratorio_temporal_spark.py
```

Entrada real:

```text
data/interim/CJU_BA5EIGT_hourly.parquet
```

Saída, na raiz do projeto:

```text
reports/scale/CJU_BA5EIGT/laboratorio_temporal/
```

| Arquivo | Uso |
| --- | --- |
| `tabela_features.parquet/` | Tabela completa; é um diretório de arquivos Parquet produzido pelo Spark. |
| `amostra.csv` | Primeiras 36 origens, para inspecionar as bordas do histórico. |
| `resumo.json` | Contagens, parâmetros e escopo temporal. |
| `plano_temporal.txt` | Plano antes da materialização; procure `Window`, `Sort` e `Exchange`. |
| `contraprova_lacuna.csv` | Comparação sintética: `lag(2)` sem/com grade completa. |
| `contraprova_futuro.csv` | Comparação sintética: passado preservado, futuro alterado. |

Esses arquivos do laboratório são substituídos a cada execução no mesmo diretório. O Parquet original é montado somente para leitura. Para preservar outra configuração, informe outro `--output-dir`.

Se a entrada continuar com 8.760 horas, sem lacunas nem valores nulos, o resultado esperado com h24/d2/janela6 é:

| Medida | Esperado | Razão |
| --- | ---: | --- |
| Horas na grade | 8.760 | Uma origem por hora da série. |
| Origens com features | 8.753 | As sete primeiras ainda não têm a janela completa. |
| Linhas com features e alvo | 8.729 | Dessas, as últimas 24 não têm o alvo futuro no arquivo. |
| Alvos sem valor | 24 | Fim da série, sob a hipótese de nenhum nulo interno. |

Essas contagens são previsões condicionais ao conteúdo da entrada, não números para forçar no código. As últimas origens com features continuam úteis para inferência, mesmo sem alvo observado.

## 6. O que a contraprova de futuro demonstra

Na série sintética, o valor da hora `h` é `100+h`. Na origem de índice32, a última hora permitida é30, e o alvo h24 fica no índice56.

| Cenário | Geração na hora-limite | Média do histórico | Alvo |
| --- | ---: | ---: | ---: |
| Original | 130 | 127,5 | 156 |
| Somar 1.000 a valores após a hora-limite | 130 | 127,5 | 1.156 |

As features devem permanecer iguais. O alvo deve mudar. Se uma feature mudar, existe dependência indevida de informação posterior à hora-limite naquele exemplo. Essa contraprova valida uma propriedade específica da transformação; não demonstra disponibilidade histórica real do dado ou ausência de todos os tipos possíveis de vazamento.

## 7. Sua autoria: uma seleção de treino com fronteira temporal

Edite **somente a função `selecionar_treino(tabela, corte)`** em:

```text
notebooks/laboratorio_temporal_spark.py
```

Implemente as três condições, preservando todas as colunas:

1. As features estão válidas.
2. O alvo está preenchido.
3. `target_available_at < corte`.

Ferramentas necessárias: `tabela.filter(...)`, `F.col`, `F.lit`, `.isNotNull()`, `&` e `<`. Importe `functions as F` dentro da função, como nas outras funções do arquivo. Coloque cada condição entre parênteses; `and` do Python não combina expressões de coluna.

**Por que o corte é pela disponibilidade do alvo?** A origem pode ser anterior ao início da validação, enquanto a geração que servirá de rótulo só chegará depois. Incluir essa linha permitiria treinar com informação ainda desconhecida naquele instante. Para features, o laboratório aceita dado que chegou exatamente na origem; para preparar treino, segue a convenção conservadora já usada no projeto: rótulo estritamente anterior ao corte.

Depois de implementar, execute:

```powershell
python notebooks/laboratorio_temporal_spark.py --corte-treino "2026-07-11 06:00:00"
```

A conferência compara todas as linhas selecionadas com a regra de referência, incluindo casos na fronteira. Se passar, grava `treino_autoria.parquet/` e acrescenta a contagem em `resumo.json`.

Com h24/d2, para esse corte, a origem 10/07 às 04h tem alvo disponível exatamente no corte e deve ser excluída. A origem anterior, 10/07 às 03h, tem disponibilidade às 05h de 11/07 e pode entrar, se suas features/alvo estiverem preenchidos. Esses horários usam os rótulos existentes da série, sem declaração de UTC.

## 8. Decisão técnica e critério de conclusão

Escreva `reports/parecer_temporal_spark.md`, com no máximo uma página, respondendo:

- Qual erro surge se aplicarmos `lag(2)` diretamente numa série com lacuna? Use os valores da contraprova.
- Como os limites -7/-2 implementam seis horas disponíveis na origem?
- Por que uma linha anterior ao corte pode ser proibida no treino? Mostre os horários da fronteira acima.
- Nesta série única de 8.760 horas, você manteria a preparação principal em pandas/DuckDB ou justificaria Spark? Relacione custo de execução, quantidade de séries e integração com uma plataforma; não invente medições de desempenho.

A unidade fecha quando: a execução produz a tabela; a contraprova de futuro mantém as duas features; a seleção autoral coincide com a regra temporal; e seu parecer explica as decisões. Rodar mais vezes sem alterar uma hipótese não acrescenta evidência. Não haverá outra sequência de exercícios isolados de `count`, `fillna` e `sum` antes de avançar.

**Próxima unidade prevista no roteiro:** M07.2, tabela Delta com atualização de dados corrigidos, histórico de versões e leitura consistente; depois M07.3, execução delimitada no Databricks. O avanço para M08 tratará Dataset/DataLoader, treinamento e avaliação de uma rede temporal. A conclusão desta aula não equivale a domínio integral de Spark nem fecha automaticamente todo M07.

## Referências e verificação do material

- PySpark 4.0.1, DataFrame Quickstart: https://spark.apache.org/docs/4.0.1/api/python/getting_started/quickstart_df.html
- Spark 4.0.1, Window Functions: https://spark.apache.org/docs/4.0.1/sql-ref-syntax-qry-select-window.html
- Spark 4.0.1, Performance Tuning: https://spark.apache.org/docs/4.0.1/sql-performance-tuning.html

Os dados das contraprovas são sintéticos e identificados como tal. A validação do professor usa Linux/Java17/PySpark4.0.1 e uma série sintética de8.760horas para leitura/escrita Parquet; não substitui a execução no Docker Windows nem prova os números da série real que está no seu computador. O resultado efetivo da verificação está em `docs/Verificacao_Laboratorio_Temporal.json`.
