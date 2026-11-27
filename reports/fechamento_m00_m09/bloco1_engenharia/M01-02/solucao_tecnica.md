# M01-02 — novembro de 2025 aplicado

Solução técnica fornecida com assistência Codex. A execução e a explicação estão entregues; não existe etapa pendente de exame ou resposta independente.

O protocolo fixou o conjunto CJU_BA5EIGT, novembro de 2025, a chave entidade/hora e a data 15/11 para conta manual. A fonte anual manifestada tem 8.760 registros; o filtro conserva 720, idênticos à exportação histórica. O calendário esperado contém as mesmas 720 posições, sem atribuir fuso físico aos rótulos.

consultas.sql implementa quatro consultas SELECT: diagnóstico diário, grade com LAG/delta, quarentena e LAG da fonte esparsa. executar.py prepara tabelas em memória, executa SQLite e compara cada linha, coluna, chave, máscara NULL e número com uma implementação pandas. As regras de duplicata e ausência são as mesmas explicitadas na solução M01-01.

O resultado real contém 30 dias de 24 valores conhecidos, cobertura de 100%, 49 valores zero, nenhum NULL, lacuna ou conflito de chave. A média mensal dos 720 valores é 28,260979166666665 MWmed. O maior desvio SQLite/pandas é 8,881784197001252e-16 na tabela diária, dentro da tolerância prévia; nas demais tabelas é zero.

Para 15/11, os 24 valores somam 1.479,44 e dão média 61,64333333333334 MWmed. Os valores individuais e a conta com math.fsum estão em verificacoes.json, como apoio ao AVG da consulta.

## A ordem do filtro muda o LAG da fronteira

horario.csv preserva a primeira execução: filtrar novembro antes da janela deixa a primeira linha sem contexto, com 719 LAGs/deltas conhecidos. Isso não significa falta de uma das 720 observações do mês.

O adendo_contexto.json fixou o contexto anterior antes da consulta suplementar. executar_contexto.py leu também 31/10 23h; lag_com_contexto.sql calcula a janela antes do filtro de novembro. A saída lag_com_contexto.csv tem 720 linhas e 720 LAGs/deltas. Sua comparação pandas é integral e tem diferença zero.

Na primeira hora de novembro: atual 10,381; anterior 55,438 em 31/10 23h; delta -45,057. O resultado de 719 pares foi preservado como outra operação corretamente identificada, não substituído silenciosamente.

## Leitura do resultado

Uma linha zero conhecida participa da média. Um NULL permanece desconhecido. Se faltasse um dia inteiro, o LEFT JOIN do calendário o conservaria com contagens zero e média NULL. Se houvesse duplicatas, ambas iriam para quarentena e a hora deixaria de ter observação limpa. O caso C e os controles de ausência, entidades e ordem verificam esses caminhos, embora a fonte de novembro não os apresente.

A tabela completa dos 30 dias, as colunas explicadas, os exemplos de LAG e o percurso das consultas estão em docs/roadmap_m00_m09/Diagnostico_SQL_Aplicado.md, referência ativa desta entrega. data_card.md e checkpoint.md antigos são preparação histórica preservada, não requisitos atuais.

Nenhum treino, modelo, Spark ou nova aquisição foi executado. O período já estava examinado no projeto; este diagnóstico não é um novo teste preditivo ou confirmação dos contratos operacionais externos M04.
