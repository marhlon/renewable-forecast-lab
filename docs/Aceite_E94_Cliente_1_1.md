# E94 — cliente Windows 1.1 aceito no protocolo local

Marlon Alves Bomfim · 17/10/2026 UTC · execução `20261017T002410Z_7f76e51f`

Os oito anexos foram lidos: recibo de verificação, cinco recibos de consulta e dois logs. Os sete hashes de saída registrados no recibo coincidem com os bytes anexados. Foram aprovadas 32 conferências, detalhadas em `Conferencia_E94_Cliente_1_1.json`.

| Situação | HTTP | Saída do executável | Resultado conferido |
| --- | --- | --- | --- |
| Reprodução histórica | 200 | 0 | `no_alarm`; probabilidade 0,20465385372296466 |
| Mesmo pedido em modo operacional | 200 | 7 | `target_elapsed`; `response=null`, resposta preservada em `audit_response` |
| Pedido inválido | 422 | 2 | Rejeição apresentada como falha |
| Identidade divergente | 200 | 4 | Contrato recusado pelo hash do modelo |
| API encerrada | sem resposta HTTP | 3 | Indisponibilidade registrada em recibo novo |

A comparação entre o recibo permitido e o bloqueado confirma o mesmo pedido, o mesmo contrato e a mesma resposta de inferência. O que muda é a autorização para apresentá-la como previsão atual. A resposta HTTP 200 confirma processamento; a validade temporal pertence a uma regra adicional do produto. A ausência de alarme em um pedido vencido não é uma informação operacional atual.

O executável foi declarado `frozen=true`, fora do projeto, com `conda_active=false` e `pythonpath_present=false` em todos os recibos. O controlador corresponde ao arquivo entregue em E93. Os logs da API registram três respostas 200 e uma 422 para os POSTs esperados. A diferença de probabilidade é zero.

**Aceite:** M06.5 encerrado no escopo local demonstrado, incluindo a evolução 1.1. Não é necessário repetir build, benchmark, inferência ou implantação do cliente para começar M07.1. O inventário P1 permanece com 8/10 entregas técnicas; esta evolução qualifica o item 9 já aceito.

**Limites:** esta revisão inspecionou os anexos, sem executar novamente o `.exe` ou o Docker no computador do aluno. A cópia externa foi testada no mesmo PC; não prova suporte a toda instalação Windows. `operational_policy_approved=false` permanece correto. CI remoto, shadow ao vivo e monitoramento contínuo são entregas distintas de M06, não bloqueios adicionais para a unidade seguinte.

**Próxima competência:** portar uma transformação da geração ONS para Spark, preservar sua semântica e justificar o custo de particionar/agrupar. Entrega M07.1 em `Aula_M07_1_Spark_DuckDB.md`.
