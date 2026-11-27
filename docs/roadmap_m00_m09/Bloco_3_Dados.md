# Bloco 3 — engenharia de dados e modelo global

Protocolos anteriores a execução, código/modelos fixos e dados reais preservados. Soluções fornecidas e executadas por Codex; sem exigir provas do usuário ou certificar autonomia pessoal.

## M07-01 — camadas

Execução atribuída a Codex, não a resposta independente do usuário. Bronze preservou os 4,629,118 bytes e SHA256 original; silver tem 389,304 linhas, quarentena 148,080, gold 2,976. Duplicatas inteiras, ids ausentes, MW negativos/não finitos e horários inválidos não recebem imputação. A linhagem usa source_row na bronze e joins exatos de série/tempo na gold.

Segunda construção de silver/quarentena/gold efetivamente executada; hashes lógicos e físicos iguais registrados em resultado.json. A disponibilidade t+2h é hipótese de estudo, não fonte histórica. Contraprova sintética separada testa rejeição. Aceite técnico local dos critérios C1/C2; sem Delta distribuído nem aprovação operacional.

Dos 537.384 registros brutos, 389.304 passaram pelo contrato; 87.048 ficaram em quarentena por id_ons ausente e 61.032 por geração não finita/ausente. A soma fecha o inventário. Nenhuma chave substituta foi inventada para agregados sem id, nem ausência de geração virou zero. As regras de negativo, duplicata e hora inválida foram exercitadas nos testes pequenos; não foram observadas nesses grupos reais.

Bronze é escrita uma vez por contrato de aplicação em caminho endereçado por hash, e uma reutilização confere novamente os bytes. Não há proteção WORM de armazenamento nem proibição de escrita fora do programa. Os hashes publicados detectam uma alteração posterior; não são uma política de acesso do sistema operacional.


## M07-02 — escala local real

Foram executados 18 trials (dois motores × três coortes reais × três repetições), em processos separados. Coortes são prefixos determinísticos de id_ons; nenhuma linha foi replicada para ampliar artificialmente volume. O cronômetro cobre leitura de silver, filtro, LAG por série com guarda de intervalo exato de uma hora, agregação, Parquet e hash. Importação/startup e EXPLAIN ANALYZE ficam fora do tempo reportado.

As nove comparações pareadas de saída tiveram equivalência numérica com tolerância 1e-10, chaves e contagens exatas. Os planos observados mostram scan/filtro, WINDOW e agregação do DuckDB local. Não demonstram AQE, Spark ou cluster. Recursos: DuckDB threads=1 e memory_limit 512MB; pandas com threadpool=1 e RSS amostrado (sem limite rígido de SO). RSS, CPU, tempo, bytes e hashes estão preservados. Cache de SO não foi limpo; três medições curtas não permitem inferência causal de arquitetura ou extrapolação a big data.

- duckdb coorte 1: 149,568 linhas, mediana 0.3261s, CPU 0.1562s, pico RSS 116.1 MiB.
- duckdb coorte 2: 266,664 linhas, mediana 0.2501s, CPU 0.2188s, pico RSS 122.8 MiB.
- duckdb coorte 3: 389,304 linhas, mediana 0.2228s, CPU 0.2188s, pico RSS 128.9 MiB.
- pandas coorte 1: 149,568 linhas, mediana 0.2472s, CPU 0.2031s, pico RSS 147.9 MiB.
- pandas coorte 2: 266,664 linhas, mediana 0.3969s, CPU 0.3125s, pico RSS 158.3 MiB.
- pandas coorte 3: 389,304 linhas, mediana 0.2151s, CPU 0.2344s, pico RSS 148.9 MiB.

Aceite aplicado C1/C2 sob o recorte local real. O motor mais rápido neste arquivo pequeno não é uma recomendação para dados distribuídos.

### Alcance da medição

As coortes selecionam 212, 424 e 635 ids do cadastro bruto. Depois do contrato silver, materializam 149.568, 266.664 e 389.304 linhas. Cada motor lê o mesmo arquivo silver de 6.403.871 bytes e filtra sua lista de ids dentro do cronômetro: crescem as linhas que passam para janelas e agregações, mas os ensaios não usam três arquivos físicos com tamanhos diferentes. Não é um ensaio de aumento de armazenamento/I/O. A entrada bruta de origem tem 537.384 registros e 4.629.118 bytes; as 148.080 linhas em quarentena não participam do benchmark.

| Linhas após filtro | pandas mediana [mín.; máx.] s | DuckDB mediana [mín.; máx.] s |
| ---: | ---: | ---: |
| 149.568 | 0,2472 [0,2328; 0,4155] | 0,3261 [0,1705; 0,6261] |
| 266.664 | 0,3969 [0,3169; 0,4792] | 0,2501 [0,2456; 0,2728] |
| 389.304 | 0,2151 [0,2103; 0,2956] | 0,2228 [0,1825; 0,2876] |

Não houve crescimento monotônico do tempo nem vantagem consistente de um motor. A maior coorte chegou a ser mais rápida que coortes menores. Cache de SO, custos de filtro/conversão e ruído do host compartilhado impedem atribuir isso a uma propriedade de escala. O host não foi reservado e não houve afinidade exclusiva de CPU; os limites de threads são por motor. Os 18 resultados são preservados, inclusive os mais lentos. Nenhum trial foi repetido para melhorar a comparação.

Os picos RSS amostrados variaram, por coorte, de 147,9 a 158,3 MiB no pandas e de 116,1 a 128,9 MiB no DuckDB. Todos ficaram abaixo de 512 MiB. O limite rígido de memória é configuração do DuckDB; no pandas foi apenas verificado o RSS observado, sem impor um limite de SO. O baseline foi coletado antes de abrir a conexão DuckDB; consequentemente o delta de RSS inclui setup que está fora do cronômetro. Compare os picos absolutos e não trate o delta como memória exclusiva da consulta. A amostragem de 5 ms pode perder picos mais curtos.

As saídas têm as mesmas chaves e contagens. A maior diferença numérica entre motores foi 3,1833e−12, compatível com ordem de soma em ponto flutuante e inferior à tolerância prévia. Os hashes físicos diferem por codificação/valores de arredondamento; equivalência numérica não foi confundida com identidade de bytes.


## M07-03 — incremento

Replay local fornecido/executado por Codex em quatro versões de estado, 2976 eventos reais de quatro séries. Um evento foi atrasado sinteticamente por sete dias; suas contribuições indisponíveis em origens anteriores permanecem nulas mesmo depois do reprocessamento. Não se infere chegada histórica do arquivo.

Falha sintética após materializar estágio e antes de trocar o ponteiro preservou o estado; nova instância recuperou e concluiu o lote. Repetições foram noop e conflito de mesma chave foi rejeitado. Gold incremental e referência compartilham SHA256 lógico 1990d7e5ebb72034fd5e6d18a5eebe1b8ec36c87e94b57c4f164d4776bbd8989; mutação de outra série não altera a primeira. Aceite técnico local C1/C2, sem comprovar serviço distribuído, broker ou shadow.

A referência usa os mesmos horários de disponibilidade da simulação, incluindo o atraso, e não uma referência ideal com chegada imediata. Em CEECVA, o evento 05/10 12h só ficou disponível em 12/10 14h. A feature lag2 da origem 05/10 14h continuou nula após o backfill: recomputar o histórico não torna o evento conhecido antes de sua chegada declarada. O target conserva separadamente seu próprio label_available_at.

O estado é um arquivo Parquet por versão e um ponteiro JSON trocado com os.replace. A demonstração reinicializa uma instância leitora depois da exceção injetada; não é um reinício de máquina/serviço. O desenho pressupõe um escritor e snapshot append-only com rejeição de correções conflitantes. Não demonstra fsync/power-loss, locking entre escritores, atualização retroativa ou durabilidade distribuída. Esses limites permanecem separados do aceite deste replay local.


## M05-05 — global multissérie

Solução fornecida, executada e analisada por Codex. Seleção prévia por metadata: CEECVA, CEEMAU, CEUCZ, CEUFM; 744 registros por série na origem. O mesmo outubro já estava no disco e uma outra série já fora examinada no bloco 2. Este é estudo retrospectivo exploratório novo nas quatro séries, não teste final intocado.

Foram comparados um HGB global, quatro HGB locais e persistência disponível t−2, nas mesmas origens e alvo t+1h. Treino só com label_available_at estritamente anterior a 16/10; maior disponibilidade admitida 2026-10-15 23:00:00. Não houve normalizador ou cadastro externo, ajuste em validação/teste ou promoção do P1. Coortes totais: {'train': 1332, 'validation': 576, 'test': 956}.

Erro em MW e viés são comparados por série e microagregado. Escalas diferentes tornam MAE agregado sensível ao porte das usinas. A comparação não mede generalização para séries nunca vistas, outras estações, fuso validado ou disponibilidade histórica. Ganho positivo não condiciona aceite de engenharia C1/C2. Métricas completas no CSV e resultado.json; operação continua separada.

### Interpretação dos resultados executados

As quatro séries são eólicas do Ceará. O código escolheu seus ids pela ordem lexicográfica e cobertura de timestamps, sem usar geração ou erro para ordenar candidatos. A cobertura 744 foi verificada no mês completo: é uma seleção retrospectiva de um universo com dados disponíveis, não prova de que esse cadastro/cobertura fossem conhecidos em 16/10. As quatro categorias efetivamente aparecem no treino. Nenhuma estatística de normalização, capacidade externa ou valor do alvo de teste entra nos atributos.

| Série ou agregado | N teste | MAE global MW | MAE local MW | MAE persistência MW |
| --- | ---: | ---: | ---: | ---: |
| CEECVA | 239 | 0,972872 | 0,987465 | 0,583297 |
| CEEMAU | 239 | 2,809614 | 2,713715 | 4,661912 |
| CEUCZ | 239 | 7,933634 | 8,631439 | 6,615253 |
| CEUFM | 239 | 12,206883 | 12,372471 | 20,393228 |
| Microagregado | 956 | 5,980751 | 6,176272 | 8,063423 |

O global reduz o MAE agregado em aproximadamente 25,8% frente à persistência e 3,2% frente aos locais. Esse resultado não é uniforme: a persistência vence em CEECVA e CEUCZ; o global vence em CEEMAU e CEUFM. Contra o local, o global vence em três séries, mas perde CEEMAU. Na validação, o agregado local (6,077012 MW) foi melhor que o global (6,198759 MW), outra razão para não escolher um vencedor universal a partir de poucos dias. Os hiperparâmetros foram mantidos em ambos os recortes.

O RMSE de teste é 9,902025 MW no global, 10,451806 no local e 15,262370 na persistência. O viés global agregado de −0,101754 MW esconde compensação entre CEUCZ (+2,030379 MW) e CEUFM (−2,508647 MW). Logo, viés agregado perto de zero não comprova ausência de erro sistemático por usina.

A persistência usa a última medição disponível t−2 para prever t+1; com a latência hipotética, são três horas entre a observação usada e o alvo. O treino removeu, em cada série, as origens 15/10 21h, 22h e 23h porque seus rótulos chegariam à meia-noite ou depois. Além das 24 primeiras origens necessárias à lag24, o último horário do mês foi excluído porque o alvo seria novembro. Restaram 333 origens de treino, 144 de validação e 239 de teste por série. O ajuste único consumiu 0,3919 s de parede no global e 0,6683 s somando os quatro locais; são medições curtas de fit, sem medir inferência ou custo sustentado.

O ganho observado justifica manter o global como alternativa para outro protocolo prévio em mais séries/meses. Não justifica substituir o modelo P1, misturar este alvo h+1 com o benchmark h+24 ou aprovar produção. Não foi estimada incerteza de generalização neste pequeno estudo.


Artefatos: reports/fechamento_m00_m09/bloco3_engenharia/{M07-01,M07-02,M07-03,M05-05}. Cada pasta tem protocolo, resultado, parecer e manifesto SHA256; a auditoria pós-execução está em M07-01. Os CSVs mantêm métricas, recursos e previsões pareadas. Cadastro e portões operacionais são conferidos na revisão integrada do bloco. Nenhum serviço externo foi ativado por esta trilha.
