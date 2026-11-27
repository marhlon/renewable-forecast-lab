# M04-02 — parecer do contrato de geração

25/11/2026 · Preparação e análise assistidas: Codex. Revisão e cadastro ainda cabem ao responsável pela retomada; não há nova resposta independente do aluno.

A consulta confirmou apenas parte do contrato. O [dicionário ONS](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/DicionarioDados_GeracaoPorUsina.pdf) sustenta o campo de referência e MWmed; o [portal](https://dados.ons.org.br/dataset/geracao-usina-2) admite revisão dos valores publicados. Fuso físico, interpretação das bordas horárias e publicação histórica não ficaram comprovados no material consultado.

`contrato_geracao.json` mantém esses campos desconhecidos, em vez de preenchê-los com a hipótese usada pelo código. Localizar um relógio ingênuo em `America/Sao_Paulo` e convertê-lo a UTC pode produzir uma tabela internamente coerente, mas não autentica o significado físico atribuído ao relógio.

O critério C1 permanece incompleto. A restrição operacional de C2 foi mantida explicitamente. A decisão recomendada é **bloqueado por fonte externa**, até obter documentação primária suficiente. As perguntas estão em `fontes.md`; nenhum contato foi enviado.

Esta auditoria não alterou séries, metadados aceitos, protocolos ou hipóteses históricas, nem refez a preparação ou o treino.
