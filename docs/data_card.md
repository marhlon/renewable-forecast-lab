# Data card — recorte de transferência SQL M01-02

Preparação assistida em 25/11/2026. Diagnóstico independente: **pendente**.

Fonte: `dist/databricks/CJU_BA5EIGT/m07_3/geracao.parquet`, pacote M07.3,
série `CJU_BA5EIGT`. São 8760 registros na fonte preservada,
de `2025-09-01T00:00:00` a `2026-08-31T23:00:00`. O SHA-256 é
`bf3a58b37a2857951eba280452b622db4f541ad13b2c663c2fd5c54c94ec7104`; o manifesto identifica sua linhagem.
É um recorte já preparado do projeto, não uma nova aquisição dos brutos ONS.

O exercício usa `[2025-11-01T00:00:00, 2025-12-01T00:00:00)`,
o terceiro mês civil completo conforme a regra fixada antes do filtro.
Foram exportadas 720 linhas e 720
posições esperadas de calendário. Esses são metadados da preparação, não uma
consulta ou resposta atribuída ao aluno.

| Campo | Contrato |
|---|---|
| id_ons | Identidade da série, adicionada a partir do manifesto |
| din_instante | Rótulo temporal original, sem atribuição silenciosa de fuso |
| val_geracao | Geração média em MWmed, valores preservados |
| Chave pretendida | (id_ons, din_instante), uma posição por hora |
| Ausências e zero | Não imputados; zero observado continua zero |
| Duplicidade | Deve ser diagnosticada antes de JOIN/janela; nenhuma cópia é eliminada na exportação |

Arquivos: [fonte do exercício](../reports/fechamento_m00_m09/M01-02/recorte_real.csv),
[calendário](../reports/fechamento_m00_m09/M01-02/calendario_exercicio.csv) e
[protocolo concreto](../reports/fechamento_m00_m09/M01-02/protocolo_recorte.json).
A fonte original e o calendário permanecem separados. Não foram injetadas falhas.
O laboratório não executa a SQL independente nem classifica a qualidade do mês.

Fuso físico, início/fim do intervalo, versão histórica publicada e disponibilidade
real continuam não verificados. O pacote M07.3 usa atraso de geração assumido e
snapshot fixado; isso não demonstra disponibilidade point-in-time da fonte.
Não é teste preditivo novo nem autorização operacional.

`diagnostico.csv` é a referência assistida **sintética A/B**; não é a análise do
recorte real. A resposta e a consulta próprias continuam nos templates pendentes.
