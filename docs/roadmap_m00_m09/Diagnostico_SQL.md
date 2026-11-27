# Diagnóstico temporal com SQL e pandas

Esta prática prepara M00-01, M01-01, M01-02 e M07-04. O exemplo abaixo está
resolvido e foi preparado com assistência; as provas novas e a defesa própria
continuam pendentes. Não há treino, download, Docker ou repetição de Spark.

Na raiz, com o ambiente Python existente:

```powershell
python notebooks/laboratorio_diagnostico_sql.py --preparar
```

O programa usa SQLite em memória e pandas. Confere a demonstração com contas
manuais, exporta um mês real para o exercício e gera os recibos. Para conferir
somente a demonstração, sem exportar o recorte real:

```powershell
python notebooks/laboratorio_diagnostico_sql.py --verificar
```

## Exemplo resolvido: cada linha representa o quê?

A chave é `(id_ons, din_instante)`: uma observação horária de uma série.
As fontes sintéticas, de 01 a 04/01/2027, contêm:

| Série | Dia/hora | Valor MWmed |
|---|---|---:|
| A | 01/01 00h | 0 |
| A | 01/01 01h | 12 |
| A | 01/01 03h | NULL |
| A | 03/01 00h | 30 |
| A | 03/01 01h | 40 |
| A | 03/01 01h | 45 |
| A | 04/01 00h | NULL |
| A | 04/01 01h | NULL |
| B | 01/01 00h | 100 |
| B | 01/01 02h | 200 |
| B | 04/01 00h | 0 |

As duas cópias de A/03/01 01h vão **inteiramente para quarentena**. Não se
escolhe a última nem se calcula uma média para fabricar uma medição única.
A fonte de 11 linhas permanece intacta; a tabela limpa tem 9 linhas e a
quarentena conserva as duas cópias com seus identificadores de registro.
Essa é uma política conservadora da demonstração, sujeita a investigação
da origem; não prova qual das cópias seria a correta.

O calendário contém os quatro dias para as duas séries. Com a fonte limpa,
a conta diária é:

| Série/dia | Presentes | Válidas | Média MWmed | Cobertura válida |
|---|---:|---:|---:|---:|
| A/01 | 3 | 2 | 6 | 2/24 |
| A/02 | 0 | 0 | NULL | 0/24 |
| A/03 | 1 | 1 | 30 | 1/24 |
| A/04 | 2 | 0 | NULL | 0/24 |
| B/01 | 2 | 2 | 150 | 2/24 |
| B/02 | 0 | 0 | NULL | 0/24 |
| B/03 | 0 | 0 | NULL | 0/24 |
| B/04 | 1 | 1 | 0 | 1/24 |

Em A/01, `AVG` considera os valores conhecidos: `(0+12)/2 = 6`.
Substituir o valor desconhecido por zero produziria `4`, mudando a pergunta.
Em A/04 existem registros, mas nenhuma medição válida para calcular a média.
Já a média zero de B/04 é conhecida e observada. Os três estados não são iguais.

O `LEFT JOIN` conserva as oito combinações série/dia. O `INNER JOIN` conserva
as cinco com resumo, inclusive A/04, cuja média é desconhecida. Ele remove
os dias sem registros, não todos os dias cuja média é `NULL`.
`COALESCE` é aplicado só às contagens do resumo que faltou. Na grade horária,
`COUNT(*)` após o `LEFT JOIN` contaria as posições do calendário; isso não
equivale a contar medições presentes. Leia a
[SQL resolvida](../../reports/fechamento_m00_m09/M01-01/consultas.sql).

## LAG anda no resultado ordenado

Na fonte esparsa de A, a linha anterior a 01/01 03h é 01/01 01h, valor 12.
`LAG(...,1)` percorreu duas horas do relógio. A ausência de 02h não virou uma
linha por conta própria. Na grade horária completa, a linha anterior passa
a ser 02h: valor desconhecido e `registro_presente=0`. Às 03h há um registro,
mas seu valor é `NULL`; a coluna de presença conserva essa diferença.

`PARTITION BY id_ons` separa A de B. `ORDER BY din_instante` define a ordem.
Antes da janela, a chave precisa ser única; duplicatas produziriam posições
ambíguas ou aumentariam a cardinalidade do JOIN. Particionar por dia corta
o histórico na meia-noite e responde a outra pergunta.

## Exercício real: fonte fixada antes da consulta

O laboratório confere o manifesto e o Parquet M07.3 de 8.760 registros.
A regra previamente fixada escolhe o **terceiro mês civil completo** coberto
pela fonte, sem procurar um mês por qualidade ou resultado. Ler os limites
de data apenas concretiza essa regra; isto não é seleção de teste preditivo.
As datas e os hashes são gravados em `protocolo_recorte.json` antes do filtro.

Arquivos em `reports/fechamento_m00_m09/M01-02/`:

- `recorte_real.csv`: valores reais, sem imputação ou falhas injetadas;
- `calendario_exercicio.csv`: posições horárias esperadas do recorte;
- `consultas.sql`: **template pendente**, sem consulta resolvida;
- `diagnostico.csv`: referência assistida da demonstração sintética A/B, identificada por coluna; não é o diagnóstico do mês real;
- `resposta_independente.md`: expectativas, consulta, reconciliação e assistência, ainda a preencher.

O [data card](../data_card.md) distingue proveniência e hipóteses. O relógio
original não tem fuso certificado: o programa conserva os rótulos, sem
atribuir UTC silenciosamente. Zero observado permanece zero; ausência não
é corrigida automaticamente. Nenhum `treino_referencia.parquet` é refeito.

Depois de escrever sua consulta, você poderá executá-la contra os CSVs:

```powershell
python notebooks/laboratorio_diagnostico_sql.py --consultas-exercicio reports/fechamento_m00_m09/M01-02/consultas.sql
```

Essa rota cria tabelas temporárias `recorte` e `calendario`, permite apenas
consulta e grava `resultado_consulta_usuario.csv`. O template vazio é recusado.
O programa registra a execução; ele não transforma assistência em autonomia
nem aprova sua explicação. Não executamos essa rota na preparação.

## Perguntas novas, sem gabarito

1. **M00-01:** no caso com emissão 04h, atraso 3h, horizonte 12h e janela 4h, formule os relógios antes de programar. Identifique no fluxo h+1 existente quais hipóteses mudariam. Use o [template M00](../../reports/fechamento_m00_m09/M00-01/resposta_independente.md).
2. **M01-01:** o [novo caso C](../../reports/fechamento_m00_m09/M01-01/resposta_independente.md) atravessa a meia-noite e tem dias parciais. Preveja a conta e explique o denominador, o calendário e a quarentena antes da SQL.
3. **M01-02:** escolha previamente uma data do mês exportado para uma conta manual. Complete a consulta, compare com pandas e explique a política, mesmo se a fonte estiver completa. Não copie a tabela A/B como resultado da fonte real.
4. **M07-04:** responda ao [template de defesa](../../reports/fechamento_m00_m09/M07-04/defesa.md) sobre uma janela nova, alcance de Exchange/AQE e desenho da medição. O parecer anterior foi corrigido; essa defesa não exige nova execução Spark/Databricks.

O aceite exige resposta e revisão atribuídas a quem as realizou. Os recibos
de preparação usam `await_human`; nenhum deles certifica fechamento formativo.
