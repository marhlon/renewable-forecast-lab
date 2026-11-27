# Revisão técnica assistida — bloco 1

25/11/2026 · etapas 1–3 · responsável: Codex, agente principal, com revisão separada das implementações delegadas.

Esta revisão cobre código, artefatos e delimitação de evidências. Não é aceite do professor, resposta independente do aluno ou aprovação operacional. As execuções históricas foram preservadas.

## Itens tecnicamente aprovados no escopo declarado

| Item | Evidência conferida | Decisão e limite |
| --- | --- | --- |
| M04-01 | Chaves exatas em `validate_wind_geometry`, validação finita, tolerância, geometria com `hypot`; 38 contraprovas e 38 testes sobre os mesmos casos; pedido real sem fit/recarga de modelo | Correção E51 aprovada tecnicamente. Não comprova contratos de fuso/disponibilidade |
| M02-05 | Retorno do bootstrap por fold e agregado ponderado por n; circularidade interna, deltas pareados, RNG local e CLI; 59 testes aprovados | Implementação reconstruída aprovada. Não se declara identidade do RNG com a rotina histórica perdida; a execução em previsões reais M02-08 fica no bloco 2 |
| M06-01 | Oito hashes do registro conferidos fora do sandbox contra `versions.csv`, todos coincidentes; dentro dele a leitura encontrou acesso negado | Inventário reconciliado como limitação de acesso no contexto observado. Nenhum arquivo restaurado e nenhum modelo desserializado |
| M08-01 | Saídas e entradas dos runs fixados preservadas; arquivo autoral M08.1 atual difere do histórico | Auditoria de preservação e divergência de versão aprovada. Não certifica reprodução integral com a árvore atual, retenção ou autoria independente |
| M09-01 | Blocos e saídas dos dois runs M09.2 preservados; runner/verificador atuais têm outras identidades | Auditoria aprovada com a divergência documentada. Composição e persistência não são treino ou desempenho preditivo |
| M09-03 | Manifesto, model card e três artefatos congelados conferidos; escopo dos dados de pré-treino explicitamente desconhecido | Delimitação aprovada: `pretraining_overlap_verified=false` permanece. Nenhuma ausência de contaminação ou avaliação futura foi certificada |

Os detalhes, comandos e hashes estão nos diretórios de cada ID em `reports/fechamento_m00_m09/`. O código de auditoria trata modelos como bytes. Não foi iniciado Docker, Spark, serviço remoto ou novo benchmark neural.

## Itens que continuam esperando resposta e avaliação

M00-01, M01-01, M01-02, M02-01, M02-02, M02-03, M02-04 e M07-04.

Os laboratórios SQL e fundamentos foram construídos e executados com assistência. O recorte SQL real contém 720 horas de novembro/2025, escolhido pela regra prévia do terceiro mês completo da fonte. Sua consulta e interpretação não foram preenchidas pelo assistente. Os casos de fundamentos também permanecem sem respostas novas; as demonstrações resolvidas têm outros números.

Nenhum resultado numérico da demonstração será atribuído como solução independente do aluno. O estado `aguarda_revisao` neste cadastro inclui a espera da resposta humana indicada no parecer do item.

## Itens bloqueados por comprovação externa

M04-02, M04-03, M04-04 e M04-05.

A auditoria confirmou coerência interna de 126 rodadas arquivadas e dos relógios de 744 origens do h24, sob as hipóteses registradas. Ela não encontrou horários observados de publicação histórica. A documentação consultada não fechou fuso/borda do intervalo ONS nem as versões cadastrais conhecidas no passado.

O mecanismo bitemporal foi construído e passou em seis testes. Foram exportados 15 registros com a data de conhecimento efetivamente documentada. A vigência física histórica permanece nula/não comprovada e esses registros são excluídos da seleção operacional. Não se inventou vigência para encerrar o item.

## Observação sobre apresentação do recibo E51

O recibo original contém caracteres `?` literais no lugar de alguns acentos em descrições. Esse defeito está restrito aos metadados textuais; os nomes de campos, valores, hashes, comandos e resultados numéricos foram conferidos. O recibo foi preservado, e esta revisão fornece a descrição legível sem fingir uma nova execução.

## Regra de continuidade

Aprovar a entrega técnica dos seis itens não encerra o bloco: faltam oito avaliações humanas e quatro comprovações de fonte. O verificador com `--bloco 1 --exigir-fechamento` deve retornar código 1 enquanto essas pendências existirem. Não avançar para executar o bootstrap real ou escolher modelos como se o bloco estivesse formativamente fechado.
