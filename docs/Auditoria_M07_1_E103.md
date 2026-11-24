# E103 — conferência da tabela temporal e do treino recebido

Data da revisão: 27/10/2026, America/Sao_Paulo. O log do Spark usa 28/10 em UTC.

**Resultado: entrega técnica aceita.** Os dois arquivos Parquet recebidos foram abertos e comparados por todas as linhas e colunas. A seleção de treino corresponde exatamente à regra de disponibilidade estrita. Não é necessário repetir o laboratório M07.1.

| Verificação | Resultado |
|---|---:|
| Tabela completa | 8.760 linhas |
| Origens únicas e consecutivas, por hora | 8.760 |
| Origens com features válidas | 8.753 |
| Features válidas e alvo preenchido | 8.729 |
| Alvos ausentes no fim da série | 24 |
| Treino recebido | 7.485 linhas |
| Linhas extras ou faltantes contra a seleção de referência | 0 / 0 |
| Seleção incorreta usando apenas origem anterior ao corte | 7.511 linhas |
| Linhas indevidas que essa seleção acrescentaria | 26 |

A comparação usa `EXCEPT ALL` nos dois sentidos: igualdade de contagens, sozinha, não excluiria substituições ou duplicidades. Não houve divergências. Os schemas também coincidem.

O treino começa na origem 01/09/2025 07h e termina em 10/07/2026 03h. A maior disponibilidade de alvo selecionada é 11/07/2026 05h, estritamente anterior ao corte de 11/07 às 06h.

| Origem | Disponibilidade do alvo | Geração alvo (MWmed) | Elegível |
|---|---|---:|---|
| 10/07 02h | 11/07 04h | 74,3265 | Sim |
| 10/07 03h | 11/07 05h | 75,4365 | Sim |
| 10/07 04h | 11/07 06h | 59,4750 | Não |
| 10/07 05h | 11/07 07h | 62,2775 | Não |

## Consistência dos resultados

- Todas as linhas satisfazem `history_end = origem - 2h`, `target_time = origem + 24h` e `target_available_at = origem + 26h`.
- As 36 linhas de `amostra.csv` coincidem com as primeiras 36 linhas do Parquet completo, preservando os campos vazios como ausência e as flags booleanas.
- A contraprova de lacuna devolve 129 sem grade e NULL com grade. A contraprova de futuro preserva as features 130 e 127,5, enquanto o alvo muda de 156 para 1.156.
- Os valores de geração repetidos nas colunas de histórico e alvo foram alinhados pelos respectivos timestamps. As sobreposições são coerentes e permitem reconstruir internamente 8.760 valores. Com eles, as janelas foram recalculadas independentemente em Python. Diferença máxima de média: 5,684341886080802e-14 MWmed, compatível com arredondamento de ponto flutuante.
- Esse último recálculo verifica consistência interna dos resultados. O Parquet bruto original não foi recebido; não é uma auditoria independente contra a fonte ONS.

## O que o plano demonstra

O plano anexo contém leitura Parquet, mínimo/máximo para formar a grade, `Generate`, `BroadcastHashJoin LeftOuter`, ordenação e `Window`. Os frames da janela são -2/-2 para a geração na hora-limite, -7/-2 para a média e +24/+24 para o alvo. `InMemoryRelation` decorre do cache solicitado pelo código.

O `Exchange SinglePartition` exibido serve à agregação global de mínimo/máximo. A série única e o plano não demonstram distribuição eficiente entre máquinas. `isFinalPlan=false` identifica um plano adaptativo ainda não final; o arquivo não fornece latência, memória ou benchmark Spark versus DuckDB.

## Decisão e limite

A autoria recebida de `selecionar_treino` está implementada corretamente e foi executada com sucesso no Windows. O bloqueio de integração está encerrado. A próxima prática é M07.2: versões Delta, correção simulada e reprodução da tabela anterior.

A interpretação autoral do laboratório continua separada do aceite de execução; não se inventa domínio integral de Spark ou percentual de curso. O atraso de duas horas e a semântica temporal da fonte continuam hipóteses declaradas. Não houve treino ou avaliação de um novo modelo nesta etapa.

## Identificação dos arquivos

- Tabela completa: `part-00000-be7eab36-1fa7-42a8-9c69-6f844635045d-c000.snappy.parquet`.
- Treino: `part-00000-1e27d39b-3b07-47a4-bb68-d2255698dd71-c000.snappy.parquet`.
- Controles: `resumo.json`, `amostra.csv`, `contraprova_lacuna.csv`, `contraprova_futuro.csv` e `plano_temporal.txt`.
- Detalhes verificáveis e hashes dos sete arquivos: `Auditoria_M07_1_E103.json`, no mesmo pacote.
