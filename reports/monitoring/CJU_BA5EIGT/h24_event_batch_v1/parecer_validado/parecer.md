# M06.3 — Parecer sobre o lote histórico

Corte: `2026-08-02T07:00:00Z`. Modelo: `CJU_BA5EIGT-h24-event-8ecd88cd427a`.

## Evidência recalculada

Foram usadas 24 emissões únicas do mesmo corte, com status observed.
Referência fixa: 168/694 rótulos do treino.

| Métrica | Recalculado | Relatório normal |
|---|---:|---:|
| brier | 0.132603016 | 0.132603016 |
| baseline_brier | 0.187562807 | 0.187562807 |
| baseline_probability | 0.242074928 | 0.242074928 |
| brier_skill | 0.293020732 | 0.293020732 |

Todas as comparações passaram com tolerância absoluta 1e-9. Banco aberto em modo somente leitura; hashes das entradas preservados.

## Cenários efetivamente lidos

| Cenário | Integridade | Dados | Desempenho | Ação | Observados | Sem observação |
|---|---|---|---|---|---:|---:|
| normal | pass | ok | insufficient_evidence | collect_evidence | 24 | 0 |
| missing_observation | pass | investigate | insufficient_evidence | investigate_data | 23 | 1 |
| changed_probability | fail | blocked | blocked | repair_record | 24 | 0 |
| missing_assessment | fail | blocked | blocked | repair_record | 23 | 0 |

## Condutas e limites

- **normal** — prioridade `info`: Continuar coletando resultados. Métricas disponíveis são descritivas; a regra mínima de observações ainda não foi atendida.
- **missing_observation** — prioridade `high`: Investigar chegada, extração e associação temporal da geração; produzir nova avaliação em outro corte após a correção.
- **changed_probability** — prioridade `critical`: Suspender o uso deste relatório para decisões; localizar a divergência e recuperar o registro confiável.
- **missing_assessment** — prioridade `critical`: Suspender o uso deste relatório para decisões; localizar a divergência e recuperar o registro confiável.

1. Falhas de integridade têm precedência: métricas de registros incoerentes não sustentam decisão sobre o modelo. A regra exportada não estabelece ordem adicional entre os dois incidentes críticos.
2. O mínimo de 168 observações é uma regra didática de triagem. Não prova independência, representatividade, concept drift ou segurança operacional. Este parecer não autoriza promoção ou retreino.
3. missing_observation conserva a avaliação e informa falta do resultado após target_available_at. missing_assessment significa que falta o próprio registro de avaliação. A causa e o tempo de recuperação precisam de investigação.

O recálculo é independente de event_monitor; os cenários são lidos dos relatórios exportados e não são reexecutados por este programa. A conferência não autentica medições físicas nem detecta toda adulteração coordenada.
O lote usa política retrospectiva e hipóteses de disponibilidade. Não é novo holdout, monitoramento contínuo ou evidência de funcionamento ao vivo.

Os arquivos gerados por uma execução anterior com fallback sintético não medem este lote e não devem integrar sua avaliação de desempenho.

Este texto foi gerado por uma implementação revisada com orientação. Sua execução valida o contrato técnico; não comprova, isoladamente, autoria independente ou domínio completo.
