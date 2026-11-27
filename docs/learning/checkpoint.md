# Checkpoint M00-01 — percurso e prova pendente

Preparação didática assistida em 25/11/2026. Resposta independente do aluno:
**pendente**. Este mapa facilita a navegação; não é uma prova de autonomia.

## Percurso existente, sem executar inferência

1. Em `src/renewable_forecast/cli.py`, `build_parser` define `predict`, `--model` e `--input`.
2. `run_predict_command` encaminha esses caminhos a `modeling.predict_next`.
3. Em `src/renewable_forecast/modeling.py`, `predict_next` verifica metadados, prepara a linha do próximo instante e usa `features.build_feature_frame`.
4. Em `src/renewable_forecast/features.py`, lags usam `shift`; a linha alvo não pode entrar como atributo dela própria. A ordem vem das features declaradas.
5. A previsão e seu instante são devolvidos pela CLI. Esta preparação não carrega o artefato nem calcula uma nova previsão.

O fluxo inicial é h+1. Os laboratórios com atraso/horizonte explícitos usam
contratos próprios, incluindo `supervised.build_horizon_training_frame` e
`purged_time_series_splits`. Não presumir que todas as funções recebem os
mesmos relógios ou aplicam atraso de duas horas.

## Material pronto para estudar

- [Guia com conta resolvida](../roadmap_m00_m09/Diagnostico_SQL.md).
- [Laboratório executável](../../notebooks/laboratorio_diagnostico_sql.py).
- [Novo caso e resposta a preencher](../../reports/fechamento_m00_m09/M00-01/resposta_independente.md).

## Registro que depende do aluno e da revisão

| Campo | Estado |
|---|---|
| Hipótese e saída previstas antes do código | Pendente |
| Adaptação do caso novo | Pendente |
| Resultado observado e evidência | Pendente |
| Explicação do contrato e dos limites | Pendente |
| Assistência utilizada na tentativa | A declarar |
| Revisão atribuída, data e aceite | Pendentes |

O recibo M00-01 distingue execução da preparação e avaliação humana. Ambientes,
treinos, artefatos e aceites históricos permanecem preservados.
