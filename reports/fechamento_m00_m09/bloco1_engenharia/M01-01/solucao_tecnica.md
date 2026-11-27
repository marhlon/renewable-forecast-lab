# M01-01 — JOIN, nulos, duplicatas e LAG resolvidos

Solução técnica fornecida com assistência Codex. As consultas foram executadas e comparadas integralmente com pandas; não há etapa de exame ou resposta independente pendente nesta entrega de engenharia.

## Contrato do caso C

A chave é (id_ons, din_instante), com uma medição por hora de referência. A fonte tem seis linhas entre 10/02/2027 22h e 12/02/2027 00h, inclusive. A chave 11/02 02h aparece duas vezes, com valores 7 e 9. As duas linhas ficam preservadas em quarentena. Não há autoridade para escolher uma delas nem substituir a ambiguidade pela média 8.

Depois dessa política restam quatro linhas: 5 às 22h, zero às 23h, uma medição desconhecida às 01h e 4 às 00h do último dia. O calendário tem 27 posições horárias.

| Dia | Horas do recorte | Linhas brutas | Quarentena | Presentes limpas | Válidas | Média MWmed | Cobertura válida |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10/02 | 2 | 2 | 0 | 2 | 2 | 2,5 | 100% |
| 11/02 | 24 | 3 | 2 | 1 | 0 | NULL | 0% |
| 12/02 | 1 | 1 | 0 | 1 | 1 | 4 | 100% |

O denominador é a exposição solicitada: 2, 24 e 1 horas. Os 100% dos dias parciais não significam 24 horas observadas. Se a pergunta fosse cobertura do dia civil inteiro, seria necessário outro calendário e outro denominador.

## JOIN e nulos

O LEFT JOIN parte do calendário e conserva suas 27 horas. A presença é marcada pela existência da chave da fonte limpa. COUNT(*) depois desse JOIN mede posições esperadas; COUNT(val_geracao) mede valores conhecidos; a soma do indicador de presença mede registros que existem, incluindo aqueles com valor NULL.

Na agregação diária, LEFT e INNER conservam três dias neste caso: todos têm alguma linha limpa, inclusive 11/02 com valor NULL. Na grade horária, INNER conserva quatro horas e LEFT conserva 27. Não é correto dizer que INNER remove todo dia com média NULL.

O controle separado D tem três dias esperados e um único registro de zero no primeiro. Nele, INNER diário conserva um dia e LEFT conserva três; as médias dos dois dias sem registros continuam NULL. O zero observado do primeiro dia permanece conhecido e entra na média.

COALESCE preenche somente contagens ausentes. Trocar geração desconhecida por zero alteraria média, cobertura e interpretação. Zero é uma medição, não um marcador de falha.

## LAG e passagem de dia

Na fonte limpa esparsa, antes de 11/02 01h aparece 10/02 23h, valor zero: LAG de uma linha percorre duas horas. Na grade, a posição anterior é 11/02 00h, sem registro; o LAG do valor é NULL e o indicador anterior é zero.

Na própria posição 11/02 00h, o LAG consulta 10/02 23h e encontra zero. Particionar por dia perderia esse contexto. A janela usa PARTITION BY id_ons e ORDER BY din_instante, após tratar a duplicidade da chave.

A única diferença horária com dois valores conhecidos no caso C é 0 - 5 = -5. A fonte não inventa diferenças nas horas desconhecidas.

## Arquivos e verificação

consultas.sql contém quatro SELECTs identificados: diário, grade horária com LAG/delta, quarentena e LAG esparso. diagnostico.csv contém o resultado diário; horario.csv expõe cada posição; lag_esparso.csv evidencia o salto de relógio; quarentena.csv preserva as duas linhas conflitantes.

As quatro tabelas coincidiram com a implementação pandas, incluindo máscaras NULL e cardinalidades. O executor e o registro das verificações ficam em ../M01-02/. A fonte simulada é identificada como C e não foi confundida com o mês real de novembro.
