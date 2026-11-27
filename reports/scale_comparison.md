# Parecer Técnico de Engenharia — Reprodução e Escala no Databricks (M07.3)

Este parecer documenta a validação da pipeline de transformação temporal de geração e treino migrada para a infraestrutura Serverless do Databricks Unity Catalog, confrontando o plano de execução, os resultados numéricos e a tomada de decisão de arquitetura.

Reconciliação documental em 24/11/2026 com as correções de E108: revisão simulada, janela temporal, escopo do cronômetro e limites da leitura do plano. As tabelas e métricas abaixo permanecem as do ensaio recebido; não houve nova execução de Databricks nesta revisão. A defesa independente está prevista em M07-04 do roadmap.

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
* **Reprodução de Benchmark Fixado (Snapshot Histórico):** Exige a leitura explícita via `VERSION AS OF 0` vinculada ao `Table ID` do experimento original e à preservação dos arquivos. Isso identifica o snapshot; reprodução também depende do código, das versões e dos contratos usados.
* **Experimentos Novos com Revisão Posterior:** A alteração de M07.2 foi simulada; o laboratório não demonstrou uma retificação publicada pelo ONS. Uma correção entra em outro commit e constitui uma nova linhagem de dados. Sua utilidade para o modelo precisa ser avaliada. Ela não pode substituir silenciosamente o snapshot do benchmark anterior nem provar quando a informação teria ficado disponível historicamente.

---

## 2. Análise do Plano de Execução Físico e Particionamento

### Trecho do Plano Físico (Photon Engine)
O plano recebido contém operadores Photon, incluindo ordenação e janela. O `Exchange 10` prepara o lado de broadcast do `JOIN`; não identifica sozinho a distribuição da janela nem comprova uma otimização adaptativa. O trecho preservado foi:

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
* **Chave Temporal:** O recorte contém uma única série, `CJU_BA5EIGT`. Ao ampliar para várias séries, a janela deve separar a identidade da série e ordenar por `din_instante`; observações de usinas distintas não podem se misturar. `SinglePartition` no trecho do `JOIN` não prova, por si, como todos os operadores de janela foram distribuídos.
* **Risco de Reparticionar por Dia:** Uma janela lógica particionada por dia perde o acesso ao histórico anterior à meia-noite. Às **03h**, com atraso de **2h** e janela de **6h**, entram medições das **20h do dia anterior à 01h do dia corrente**, inclusive. A grade horária completa torna esse frame de seis posições equivalente às seis horas; lacunas exigem tratamento explícito antes da janela.

---

## 3. Medição Experimental de Desempenho e Mitos de Escala

### Resultados Medidos no Ensaio

| Configuração solicitada (`shuffle.partitions`) | Transformação e comparação (`comparison_seconds`) | Linhas de Treino Comparadas | Linhas Divergentes (`mismatched_rows`) | Maior Diferença Absoluta (MWmed) |
| :--- | :--- | :--- | :--- | :--- |
| **2 Partições** | **3,6916 s** | 7.485 | **0** | **0,0** |
| **4 Partições** | **2,9938 s** | 7.485 | **0** | **0,0** |

Ambas as execuções resultaram em $100\%$ de equivalência numérica (tolerância de $10^{-9}\text{ MWmed}$).

### Fatores que Impedem Interpretar a Diferença como Superioridade Técnica
A redução do tempo de $3,69\text{s}$ para $2,99\text{s}$ na configuração de 4 partições **não prova** que 4 partições é uma configuração superior. O ensaio não isolou causas de desempenho:

1. **Ordem, aquecimento e cache:** A configuração de 4 partições foi executada depois da de 2. Aquecimento, cache e variação de agendamento são hipóteses; sua contribuição não foi medida isoladamente. Photon usa execução nativa C++, portanto não cabe atribuir o resultado a “Java/Photon compilado por JIT”.
2. **Escopo do cronômetro:** O tempo inclui transformação, `FULL JOIN` de validação em `comparar_frames` e cálculo das diferenças. O cronômetro termina **antes** de `explain()`; a captura do plano fica fora da duração apresentada.
3. **Recorte pequeno:** Foram usadas 8.760 linhas de uma série. O ensaio não mediu pico de memória nem separou o tempo de cálculo, rede e agendamento; não estabelece o ponto em que processamento distribuído se torna vantajoso.
4. **Otimização Adaptativa (AQE):** O plano inicial não comprova que partições foram coalescidas. Seriam necessários plano final e métricas da execução. Duas configurações solicitadas não equivalem a duas distribuições efetivas já demonstradas.

---

## 4. Decisão de Arquitetura e Engenharia

### Onde Manter a Exploração Cotidiana
A exploração rotineira de dados, prototipagem de *features* e testes locais para uma única usina ($8.760\text{ linhas/ano}$) deve ser mantida **em ambiente local** (Python com DuckDB ou PySpark local em Docker).
* **Justificativa:** Evita provisionar um cluster para este recorte e permite trabalho offline quando ambiente e dados estão disponíveis. Hardware, energia, preparação e manutenção locais continuam tendo custo; este ensaio não mediu economia nem latência total de desenvolvimento.

### Quando o Databricks / Unity Catalog Passa a se Justificar
A migração da pipeline local para o Databricks justifica sua complexidade e custos quando o projeto atinge necessidades empresariais concretas:

1. **Escala de Ativos (Multi-Usina e Terabytes):** Ingestão paralela de centenas de parques eólicos/solares distribuídos geograficamente, onde o volume de telemetria excede a memória RAM e a capacidade de disco de uma estação de trabalho individual.
2. **Governança Unificada (Unity Catalog):** Necessidade de controle de acesso granular (*row/column level security*), auditoria de leitura/escrita, catálogo centralizado de metadados e rastreabilidade automática de linhagem (*data lineage*) de ponta a ponta.
3. **Engenharia Colaborativa e Produção:** Ambiente multi-usuário com execução de *jobs* Serverless agendados, controle de concorrência na escrita de tabelas Delta, integração nativa com registro de modelos via MLflow e orquestração industrial sem risco de colisão entre desenvolvedores.
