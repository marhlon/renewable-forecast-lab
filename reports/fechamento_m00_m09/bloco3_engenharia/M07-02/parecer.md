# Parecer de engenharia — escala local real

Foram executados 18 trials (dois motores × três coortes reais × três repetições), em processos separados. Coortes são prefixos determinísticos de id_ons; nenhuma linha foi replicada para ampliar artificialmente volume. O cronômetro cobre leitura de silver, filtro, LAG por série com guarda de intervalo exato de uma hora, agregação, Parquet e hash. Importação/startup e EXPLAIN ANALYZE ficam fora do tempo reportado.

As nove comparações pareadas de saída tiveram equivalência numérica com tolerância 1e-10, chaves e contagens exatas. Os planos observados mostram scan/filtro, WINDOW e agregação do DuckDB local. Não demonstram AQE, Spark ou cluster. Recursos: DuckDB threads=1 e memory_limit 512MB; pandas com threadpool=1 e RSS amostrado (sem limite rígido de SO). RSS, CPU, tempo, bytes e hashes estão preservados. Cache de SO não foi limpo; três medições curtas não permitem inferência causal de arquitetura ou extrapolação a big data.

- duckdb coorte 1: 149,568 linhas, mediana 0.3261s, CPU 0.1562s, pico RSS 116.1 MiB.
- duckdb coorte 2: 266,664 linhas, mediana 0.2501s, CPU 0.2188s, pico RSS 122.8 MiB.
- duckdb coorte 3: 389,304 linhas, mediana 0.2228s, CPU 0.2188s, pico RSS 128.9 MiB.
- pandas coorte 1: 149,568 linhas, mediana 0.2472s, CPU 0.2031s, pico RSS 147.9 MiB.
- pandas coorte 2: 266,664 linhas, mediana 0.3969s, CPU 0.3125s, pico RSS 158.3 MiB.
- pandas coorte 3: 389,304 linhas, mediana 0.2151s, CPU 0.2344s, pico RSS 148.9 MiB.

Aceite aplicado C1/C2 sob o recorte local real. O motor mais rápido neste arquivo pequeno não é uma recomendação para dados distribuídos.

## Alcance da medição

As coortes selecionam 212, 424 e 635 ids do cadastro bruto. Depois do contrato silver, materializam 149.568, 266.664 e 389.304 linhas. Cada motor lê o mesmo arquivo silver de 6.403.871 bytes e filtra sua lista de ids dentro do cronômetro: crescem as linhas que passam para janelas e agregações, mas os ensaios não usam três arquivos físicos com tamanhos diferentes. Não é um ensaio de aumento de armazenamento/I/O. A entrada bruta de origem tem 537.384 registros e 4.629.118 bytes; as 148.080 linhas em quarentena não participam do benchmark.

| Linhas após filtro | pandas mediana [mín.; máx.] s | DuckDB mediana [mín.; máx.] s |
| ---: | ---: | ---: |
| 149.568 | 0,2472 [0,2328; 0,4155] | 0,3261 [0,1705; 0,6261] |
| 266.664 | 0,3969 [0,3169; 0,4792] | 0,2501 [0,2456; 0,2728] |
| 389.304 | 0,2151 [0,2103; 0,2956] | 0,2228 [0,1825; 0,2876] |

Não houve crescimento monotônico do tempo nem vantagem consistente de um motor. A maior coorte chegou a ser mais rápida que coortes menores. Cache de SO, custos de filtro/conversão e ruído do host compartilhado impedem atribuir isso a uma propriedade de escala. O host não foi reservado e não houve afinidade exclusiva de CPU; os limites de threads são por motor. Os 18 resultados são preservados, inclusive os mais lentos. Nenhum trial foi repetido para melhorar a comparação.

Os picos RSS amostrados variaram, por coorte, de 147,9 a 158,3 MiB no pandas e de 116,1 a 128,9 MiB no DuckDB. Todos ficaram abaixo de 512 MiB. O limite rígido de memória é configuração do DuckDB; no pandas foi apenas verificado o RSS observado, sem impor um limite de SO. O baseline foi coletado antes de abrir a conexão DuckDB; consequentemente o delta de RSS inclui setup que está fora do cronômetro. Compare os picos absolutos e não trate o delta como memória exclusiva da consulta. A amostragem de 5 ms pode perder picos mais curtos.

As saídas têm as mesmas chaves e contagens. A maior diferença numérica entre motores foi 3,1833e−12, compatível com ordem de soma em ponto flutuante e inferior à tolerância prévia. Os hashes físicos diferem por codificação/valores de arredondamento; equivalência numérica não foi confundida com identidade de bytes.
