# Parecer Técnico de Engenharia — Reprodução e Escala no Databricks (M07.3)

Este parecer documenta a validação da pipeline de transformação temporal de geração e treino migrada para a infraestrutura Serverless do Databricks Unity Catalog, confrontando o plano de execução, os resultados numéricos e a tomada de decisão de arquitetura.

---

## 1. Portabilidade e Rastreabilidade de Metadados

### Identidades Gravadas em Unity Catalog
A execução fixou e registrou as seguintes identidades únicas de tabelas Delta gerenciadas:

* **Tabela de Origem (Geração):**
  * **Nome FQDN:** `` `workspace`.`renewcast_m07`.`geracao_m073_f66e094498ef` ``
  * **Table ID (UUID):** `e3c3dc5d-912c-4933-a14e-a7b476bbb374`
  * **Versão Consultada:** `0`
  * **Volume de Origem:** 8.760 registros horários ($0\text{ nulos}$, $0\text{ divergências}$)

* **Tabela de Treino (Seleção Temporal Elegível):**
  * **Nome FQDN:** `` `workspace`.`renewcast_m07`.`treino_m073_f66e094498ef` ``
  * **Table ID (UUID):** `f0f6f4fa-3879-4e07-8f5c-3c89b9f2e128`
  * **Versão Consultada:** `0`
  * **Volume Elegível:** 7.485 linhas ($0\text{ divergências}$ em relação à referência local)

### Insuficiência da Referência Apenas por "Versão 0"
Dizer isoladamente que um experimento consome a "versão 0" é uma declaração ambígua e insuficiente para auditoria. O número de versão é um ponteiro relativo dentro do log de transações (`_delta_log`) de uma tabela específica. A versão `0` da tabela de geração identifica um conjunto de arquivos totalmente diferente da versão `0` da tabela de treino, bem como de tabelas recriadas em schemas ou workspaces distintos. Rastreabilidade determinística exige o par unívoco **`Table ID` (UUID) + `Version`**.

### Reprodução de Dataset Fixado vs. Revisões Posteriores
* **Reprodução de Benchmark Fixado (Snapshot Histórico):** Exige a leitura explícita via `VERSION AS OF 0` vinculada ao `Table ID` do experimento original. Garante que qualquer auditor reexecute exatamente os mesmos dados históricos sobre os quais as métricas do modelo foram aferidas.
* **Experimentos Novos com Revisão Posterior:** Quando medições antigas são retificadas pela ONS (como a revisão analisada em M07.2), o dado corrigido entra em um novo commit (`VERSION AS OF 1` em diante). Um modelo inédito pode ser treinado sobre o snapshot atualizado para aproveitar o ganho de qualidade estatística, mas isso constitui uma nova linhagem de treino. Essa revisão não pode sobrescrever a versão `0` nem alterar retroativamente o dataset do benchmark anterior.

---

## 2. Análise do Plano de Execução Físico e Particionamento

### Trecho do Plano Físico (Photon Engine)
A operação de janelamento temporal (`WindowSpec`) para cálculo dos *lags* e da média móvel de 6 horas gerou os seguintes operadores físicos no mecanismo Photon:

```text
(10) PhotonShuffleExchangeSink
Input [3]: [din_instante#10720, val_geracao#10721, registro_presente#10725]
Arguments: SinglePartition

(15) PhotonSort
Input [3]: [din_instante#10734, val_geracao#10721, registro_presente#10736]
Arguments: [din_instante#10734 ASC NULLS FIRST]

(16) PhotonWindow
Input [3]: [din_instante#10734, val_geracao#10721, registro_presente#10736]
Arguments: [din_instante#10734, val_geracao#10721, registro_presente#10736, 
            lag(val_geracao#10721, -2, null) windowspecdefinition(din_instante#10734 ASC NULLS FIRST, specifiedwindowframe(RowFrame, -2, -2)) AS geracao_em_history_end#10740, 
            count(val_geracao#10721) windowspecdefinition(din_instante#10734 ASC NULLS FIRST, specifiedwindowframe(RowFrame, -7, -2)) AS horas_validas_historico#10742L, 
            avg(val_geracao#10721) windowspecdefinition(din_instante#10734 ASC NULLS FIRST, specifiedwindowframe(RowFrame, -7, -2)) AS media_parcial#10745]
```

### Chave de Particionamento e Integridade Temporal
* **Chave Obrigatória:** O agrupamento da janela deve ser mantido estritamente em `Window.partitionBy("serie")` com ordenação por `din_instante`. Como o dataset compreende a usina/conjunto `CJU_BA5EIGT`, o otimizador direciona todas as 8.760 horas para uma única partição executora (`Arguments: SinglePartition`).
* **Risco de Reparticionar por Dia:** Se a janela fosse particionada por data de calendário (`partitionBy("dia")`), o Spark quebraria o contínuo temporal na virada da meia-noite (00:00h). Recursos dependentes de instantes anteriores — como a média móvel das 03:00h da manhã que consulta medições das 21:00h às 02:00h da noite anterior — perderiam o acesso aos dados da partição do dia antecedente. Isso geraria janelas incompletas, falsos `NULL` e corromperia as *features* do modelo nas primeiras horas de cada dia.

---

## 3. Medição Experimental de Desempenho e Mitos de Escala

### Resultados Medidos no Ensaio

| Configuração (`shuffle.partitions`) | Duração Total (`comparison_seconds`) | Linhas de Treino Comparadas | Linhas Divergentes (`mismatched_rows`) | Maior Diferença Absoluta (MWmed) |
| :--- | :--- | :--- | :--- | :--- |
| **2 Partições** | **3,6916 s** | 7.485 | **0** | **0,0** |
| **4 Partições** | **2,9938 s** | 7.485 | **0** | **0,0** |

Ambas as execuções resultaram em $100\%$ de equivalência numérica (tolerância de $10^{-9}\text{ MWmed}$).

### Fatores que Impedem Interpretar a Diferença como Superioridade Técnica
A redução do tempo de $3,69\text{s}$ para $2,99\text{s}$ na configuração de 4 partições **não prova** que 4 partições é uma configuração superior. O resultado é afetado por vieses de medição locais e de plataforma:

1. **Aquecimento de JVM e JIT Compilation:** A execução de 4 partições rodou sequencialmente após a de 2 partições no mesmo processo Spark Serverless, beneficiando-se do código Java/Photon já compilado via JIT e do cache de metadados dos arquivos Parquet.
2. **Custo de Auditoria vs. Processamento:** O tempo cronometrado inclui I/O de controle em Python, execução do `FULL JOIN` de validação em `comparar_frames`, cálculo de diferenças máximas e geração de strings do `explain()`, e não apenas a computação da transformação.
3. **Escala Irrisória dos Dados:** O volume total da série (8.760 linhas) ocupa menos de $1\text{ MB}$ em memória. Para volumes tão pequenos, a variação do agendamento de threads do sistema operacional e latências de rede do driver superam o tempo real de cálculo do Photon Engine.
4. **Otimização Adaptativa (AQE):** O Spark Adaptive Query Execution reavalia e une partições pequenas durante a execução física, anulando na prática a alteração manual da variável de shuffle quando os dados são pequenos.

---

## 4. Decisão de Arquitetura e Engenharia

### Onde Manter a Exploração Cotidiana
A exploração rotineira de dados, prototipagem de *features* e testes locais para uma única usina ($8.760\text{ linhas/ano}$) deve ser mantida **em ambiente local** (Python com DuckDB ou PySpark local em Docker).
* **Justificativa:** Proporciona ciclos de feedback instantâneos (latência zero de subida de cluster), custo financeiro de nuvem zero, funcionamento offline e simplicidade operacional sem overhead de rede ou gerenciamento de credenciais.

### Quando o Databricks / Unity Catalog Passa a se Justificar
A migração da pipeline local para o Databricks justifica sua complexidade e custos quando o projeto atinge necessidades empresariais concretas:

1. **Escala de Ativos (Multi-Usina e Terabytes):** Ingestão paralela de centenas de parques eólicos/solares distribuídos geograficamente, onde o volume de telemetria excede a memória RAM e a capacidade de disco de uma estação de trabalho individual.
2. **Governança Unificada (Unity Catalog):** Necessidade de controle de acesso granular (*row/column level security*), auditoria de leitura/escrita, catálogo centralizado de metadados e rastreabilidade automática de linhagem (*data lineage*) de ponta a ponta.
3. **Engenharia Colaborativa e Produção:** Ambiente multi-usuário com execução de *jobs* Serverless agendados, controle de concorrência na escrita de tabelas Delta, integração nativa com registro de modelos via MLflow e orquestração industrial sem risco de colisão entre desenvolvedores.