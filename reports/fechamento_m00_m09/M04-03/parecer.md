# M04-03 — parecer de disponibilidade histórica

25/11/2026 · Preparação e auditoria assistidas: Codex. Sem atribuição de autonomia ao aluno.

A auditoria distingue inicialização, validade, disponibilidade assumida e coleta. `disponibilidade.csv` contém uma linha por rodada local, as faixas de validade, o horário de consulta, a hipótese de latência e as comparações de hashes e tabelas normalizadas.

Foram conferidas 126 rodadas e 90.720 linhas normalizadas; 124 rodadas pertencem à coorte h24 fixada. Todas usam seis horas assumidas. As verificações de hashes, grade temporal e normalização não encontraram divergências. Os metadados registram zero horários de publicação histórica observada. As coletas vão de 23 a 29/09/2026; as inicializações vão de 01/07 a 01/09/2026.

A documentação [Single Runs](https://open-meteo.com/en/docs/single-runs-api) e [Model Updates](https://open-meteo.com/en/docs/model-updates) sustenta essa distinção. Não fornece, nesta consulta, recibos das publicações usadas nas origens históricas do projeto.

O cache registra uma consulta bem-sucedida em setembro para rodadas de julho. Isso comprova a coleta registrada e os bytes preservados na conferência, não o primeiro horário de publicação. Também não prova indisponibilidade em julho. A seleção `available_at <= origem` é coerente sob a hipótese, mas a própria coluna `available_at` foi construída com seis horas assumidas.

C1 tem a separação documental dos relógios, porém falta a publicação histórica observada. C2 não pode ser concluído com latências observadas porque essa evidência não foi localizada. A decisão recomendada é **bloqueado por fonte externa**. O resultado não transforma o desconhecido em confirmação nem em acusação de vazamento.

Não houve download de novas previsões, alteração dos caches ou execução de modelos. Os protocolos existentes foram preservados.
