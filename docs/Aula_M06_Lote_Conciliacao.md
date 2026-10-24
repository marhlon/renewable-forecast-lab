# M06.2 — Da previsão isolada ao registro avaliável

Marlon Alves Bomfim · 05/10/2026 · P1/Renewcast

## Entrega anterior aceita

Sua API calculou p_event=0,2046538537 a partir de 32 features, manteve a resposta após inversão da ordem das entradas e rejeitou feature ausente/probabilidade injetada. A inferência não fez novo ajuste. Os cinco arquivos recebidos são coerentes; o hash do pedido confere. O binário do modelo não foi recebido nesta rodada: a identidade registrada foi reconciliada entre os arquivos, não recalculada a partir desse binário.

Sua função escalar_vento está correta para os cenários executados: cópia sem mutação, fator nas quatro features lineares, fator³ na média dos cubos e preservação das demais entradas. O log mostra 32,6645%, 20,4654% e 15,8862% nos fatores 0,8/1/1,2. Isso é sensibilidade local, não calibração nem efeito causal. A versão revisada avulsa exige as cinco features e rejeita complexos usando numbers.Real; não é necessário repetir a atividade aceita. O ZIP novo não substitui seu notebook autoral.

## O que esta entrega acrescenta

Um serviço que devolve JSON não guarda automaticamente o que foi previsto, não detecta reexecuções e não sabe quando pode calcular erro. Esta unidade acrescenta:

- Um lote de 24 emissões com o mesmo estimador congelado.
- SQLite com previsões, identidade do lote e avaliações separadas.
- Reexecução idempotente: o mesmo pedido reutiliza o registro anterior, sem nova previsão.
- Transação: falha no meio cancela as inserções daquela execução.
- Conciliação temporal: o rótulo só entra nas métricas quando sua disponibilidade é <= ao relógio simulado.
- Consulta SQL sobre o produto que você construiu, recuperando a competência pendente de M01.

O objetivo é engenharia do ciclo de vida da previsão. Este lote é uma simulação histórica de desenvolvimento com política escolhida retrospectivamente; não é shadow ao vivo, novo holdout ou evidência de promoção operacional.

## Por que existe outro artefato

O modelo h24_event_api_v1 foi ajustado no corte 01/08/2026 05 UTC. Usá-lo em emissões de 31/07 violaria sua fronteira temporal. Por isso preservamos esse artefato e criamos h24_event_batch_v1 no corte **31/07/2026 06 UTC**, com 694 linhas e 168 eventos. O último rótulo de treino fica disponível às 05 UTC desse dia.

As emissões vão de 31/07 06 UTC a 01/08 05 UTC. Os alvos ficam 24h depois; os rótulos ficam disponíveis mais 2h depois, sob a hipótese do projeto. O alvo é o valor no instante final, não qualquer queda ocorrida durante as próximas 24 horas. A comparação com a referência y(t−2) envolve 26h entre a referência e o alvo.

## Executar no Windows

Salve renewcast_m06_lote_20261005.zip na raiz C:\renewable-forecast-lab. O pacote não contém modelos treinados nem modifica seu artefato/API anterior. Acrescenta código do lote, notebook SQL, testes e documentos; atualiza o roteiro.

```powershell
cd C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m06_lote_20261005.zip -DestinationPath . -Force
.\scripts\run_m06_lote.ps1
```

O script para no primeiro erro. Não exige API aberta, reinstalação, nova coleta ou alteração de PYTHONPATH. Se sua política do PowerShell bloquear scripts, não altere a política: execute os comandos Python abaixo diretamente. O script PowerShell foi revisado, mas não executado em Windows no ambiente do professor; os comandos Python equivalentes foram executados com os dados reais.

### Comandos individuais equivalentes

```powershell
python -m renewable_forecast.event_artifact --input-dir data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development --policy reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json --output-dir models/CJU_BA5EIGT/h24_event_batch_v1 --forecast-origin 2026-07-31T06:00:00Z --threads 2

python -m renewable_forecast.event_batch emit --input-dir data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development --model-dir models/CJU_BA5EIGT/h24_event_batch_v1 --policy reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json --origin-start 2026-07-31T06:00:00Z --origin-end 2026-08-01T05:00:00Z --threads 2

python -m renewable_forecast.event_batch emit --input-dir data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development --model-dir models/CJU_BA5EIGT/h24_event_batch_v1 --policy reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json --origin-start 2026-07-31T06:00:00Z --origin-end 2026-08-01T05:00:00Z --threads 2

python -m renewable_forecast.event_batch reconcile --input-dir data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development --as-of 2026-08-01T12:00:00Z

python -m renewable_forecast.event_batch reconcile --input-dir data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development --as-of 2026-08-02T07:00:00Z
```

Todos usam o mesmo banco padrão: reports/service/CJU_BA5EIGT/h24_event_batch_v1/ledger.sqlite.

## Resultados estruturais esperados

| Etapa | Resultado |
|---|---|
| Primeira emissão | 24 inseridas; 0 reutilizadas |
| Repetição da emissão | 0 inseridas; 24 reutilizadas |
| Conciliação 01/08 12 UTC | 5 avaliáveis; 19 aguardando rótulo |
| Conciliação 02/08 07 UTC | 24 avaliáveis; 0 aguardando rótulo |

No ambiente do professor: primeiro corte TP=1, FP=0, FN=0, TN=4; segundo corte TP=2, FP=0, FN=4, TN=18, Brier=0,114562 e custo=16 (FP=1/FN=4). Probabilidades/métricas podem diferir entre versões do ambiente; as contagens de disponibilidade acima devem coincidir para a mesma tabela/cortes. O manifesto exige que cada artefato seja carregado no ambiente compatível com aquele em que foi ajustado.

**Ponto central:** custo zero em cinco emissões observadas não significa custo zero nas 24. As 19 restantes ainda não têm avaliação naquele corte. Não trate pendente como evento ausente, erro zero ou TN.

## Arquivos para abrir

Na pasta reports/service/CJU_BA5EIGT/h24_event_batch_v1:

- ledger.sqlite: registro relacional do lote.
- predictions.csv: 24 probabilidades/decisões, sem alvos observados.
- batch_manifest.json: modelo, política, fonte, período e limites.
- snapshots/20260801T120000Z/assessment.csv e summary.json: visão parcial.
- snapshots/20260802T070000Z/assessment.csv e summary.json: visão final do lote.

O banco mantém uma identidade de modelo/política/fonte/período por lote. Alterar essas escolhas exige outra saída, não sobrescrever este experimento. As rotinas não atualizam previsões já registradas. SQLite não é uma barreira contra edição manual maliciosa; esta é integridade de aplicação, não armazenamento inviolável.

As observações vêm da mesma tabela histórica já disponível, lidas somente no caminho de conciliação. A emissão usa usecols sem target_generation/event_drop. Isso separa o acesso do estimador, mas não transforma o histórico em coleta operacional independente. Disponibilidade de 2h continua assumida.

## Prática autoral — SQL aplicado à avaliação

Primeiro inspecione a visão parcial sem escrever nada:

```powershell
python notebooks/inspecao_lote_sql.py
```

Abra **notebooks/inspecao_lote_sql.py** e preencha somente **SQL_AUTORAL**. A infraestrutura já funciona. Escreva uma consulta que:

1. Una assessments AS a a predictions AS p por forecast_origin.
2. Agrupe por a.as_of.
3. Conte observados e pendentes separadamente com SUM(CASE WHEN ... THEN 1 ELSE 0 END).
4. Conte FN apenas quando status='observed', alarm=0 e event_drop=1.
5. Some a.cost, sem converter rótulos ausentes em zero.
6. Retorne as colunas as_of, observed, pending, fn, cost_total; ordene por as_of.

Execute:

```powershell
python notebooks/inspecao_lote_sql.py --autoria
```

Sua saída deve ter duas linhas: observed/pending = 5/19 e 24/0. FN/custo devem coincidir com os respectivos summary.json do seu ambiente, não com números preenchidos manualmente. Envie a consulta e sua saída. Explique em duas frases por que dividir o custo do primeiro corte por 24 distorce o custo por emissão já avaliada.

## Fixação lexical com a implementação aberta

| Termo | Significado neste projeto | Onde localizar |
|---|---|---|
| Artefato congelado | Mesmo modelo para todas as 24 emissões | EventRuntime; model_sha256 |
| Idempotência | Repetição não cria outro registro nem recalcula o pedido existente | Chave forecast_origin + request_sha256 |
| Transação | Ou grava todo o lote novo, ou desfaz a parte não confirmada | BEGIN IMMEDIATE / commit / rollback |
| Conciliação | Associar previsão registrada ao resultado liberado pelo relógio | reconcile; target_available_at <= as_of |
| Snapshot | Avaliação preservada para um corte específico | Chave (as_of, forecast_origin) |
| Denominador elegível | Somente observações já liberadas entram nas métricas | status='observed' |

SQLite é acessado pela biblioteca padrão sqlite3, sem servidor separado. Referência primária: https://docs.python.org/3.12/library/sqlite3.html (transações, parâmetros e conexões somente leitura).

## Critério de aceite e continuidade

Aceite técnico desta unidade: 24 registros únicos, reexecução idempotente, snapshots 5/19 e 24/0 e previsões preservadas. Aceite autoral: consulta SQL que reproduza os resumos e defesa do denominador temporal.

M06 segue em andamento. Esta entrega não conclui automaticamente monitoramento contínuo, controle de capacidade em runtime, registry/rollback, CI, Docker ou distribuição. Próxima unidade: transformar os sinais do registro em regras de monitoramento de dados/serviço, antes de discutir retreinamento. M07–M14 não mudam de estado por esta entrega.
