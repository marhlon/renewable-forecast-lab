# Diagnóstico SQL aplicado — novembro de 2025

As consultas foram executadas sobre o conjunto CJU_BA5EIGT. O mês tem **720 horas válidas em 720 esperadas**, 49 valores iguais a zero, nenhuma lacuna, duplicata ou medição nula. Os 30 dias têm cobertura de 100%. A média dos 720 valores é **28,260979166666665 MWmed**.

Esta é a referência ativa da solução técnica de M00-01, M01-01, M01-02 e M07-04, fornecida com assistência Codex. O trabalho entregue inclui código, execução, dados de saída, comparação pandas e explicação. Não depende de professor, exame ou resposta independente. Os antigos `docs/data_card.md`, `docs/learning/checkpoint.md` e templates de resposta são preparação histórica preservada, **não requisitos atuais desta entrega de engenharia**.

## Fonte, recorte e rastreabilidade

A fonte é o Parquet manifestado em `dist/databricks/CJU_BA5EIGT/m07_3/geracao.parquet`: 8.760 registros e SHA-256 `bf3a58b37a2857951eba280452b622db4f541ad13b2c663c2fd5c54c94ec7104`. O recorte de novembro, de 01/11 00h inclusive a 01/12 00h exclusivo, e a data de conta manual 15/11 foram registrados antes da consulta nova.

O mês já estava preparado no projeto. Isso é uma aplicação de diagnóstico, não escolha de novo teste preditivo. Não houve aquisição de dados, treino, inferência, Spark ou Docker. O rótulo temporal original foi preservado sem atribuir UTC; os contratos externos M04 continuam separados.

A execução usa SQLite em memória e uma implementação pandas independente. Foram comparadas todas as linhas e colunas, com chaves, contagens e máscaras de nulos exatas. Para valores de ponto flutuante, o protocolo fixou tolerâncias absoluta de 1e-10 e relativa de 1e-12. O maior desvio foi **8,881784197001252e-16** na tabela diária; nas tabelas horária, de quarentena e LAG esparso foi zero.

## Percurso da consulta

A chave é `(id_ons, din_instante)`: uma observação por hora de referência e entidade. Primeiro conto as repetições da chave. Todas as linhas de uma chave duplicada entram em quarentena, preservadas com identificador de ingestão; a consulta não escolhe silenciosamente uma cópia nem faz média entre versões conflitantes.

Depois faço LEFT JOIN do calendário com a fonte limpa. Isso mantém as posições esperadas mesmo sem registro. O indicador `registro_presente` distingue uma hora sem linha de uma linha cujo valor é NULL. Só após obter essa grade aplico LAG por entidade e timestamp.

| Campo | O que conta ou calcula |
| --- | --- |
| `horas_esperadas` | Posições do calendário na exposição pedida |
| `linhas_fonte` | Linhas brutas, inclusive duplicatas |
| `chaves_duplicadas` / `linhas_quarentena` | Quantas chaves conflitam e quantas linhas foram retiradas integralmente |
| `horas_presentes` | Registros únicos preservados, mesmo com valor NULL |
| `horas_validas` | Valores conhecidos depois da quarentena |
| `horas_nulas_presentes` | Registro existe, mas a geração é desconhecida |
| `horas_sem_registro` | Posição esperada sem registro limpo |
| `horas_zero` | Valores conhecidos iguais a zero |
| `media_geracao_mwmed` | AVG dos valores conhecidos, incluindo zeros |
| `cobertura_valida` | Horas válidas / horas esperadas |
| `delta_1h` | Valor atual menos o valor da hora anterior, quando ambos são conhecidos |

COUNT(*) na grade mede calendário, não medições. COUNT(valor) ignora NULL. Preencher o valor desconhecido com zero mudaria a média e ocultaria a falha; COALESCE é aplicado às contagens ausentes. Os 49 zeros deste mês permanecem nas 720 observações da média.

## Os 30 dias observados

A tabela abaixo arredonda apenas a apresentação. O CSV e os recibos guardam a precisão numérica da execução.

| Dia de novembro | Válidas/esperadas | Zeros | Média MWmed |
| --- | ---: | ---: | ---: |
| 01 | 24/24 | 0 | 38,027333 |
| 02 | 24/24 | 0 | 54,460750 |
| 03 | 24/24 | 0 | 28,044875 |
| 04 | 24/24 | 0 | 8,899042 |
| 05 | 24/24 | 0 | 14,399917 |
| 06 | 24/24 | 1 | 8,748958 |
| 07 | 24/24 | 0 | 21,627875 |
| 08 | 24/24 | 0 | 4,775167 |
| 09 | 24/24 | 0 | 5,216667 |
| 10 | 24/24 | 0 | 41,445000 |
| 11 | 24/24 | 0 | 54,971083 |
| 12 | 24/24 | 0 | 45,277917 |
| 13 | 24/24 | 0 | 58,439833 |
| 14 | 24/24 | 0 | 64,620917 |
| 15 | 24/24 | 0 | 61,643333 |
| 16 | 24/24 | 0 | 51,348750 |
| 17 | 24/24 | 0 | 46,118708 |
| 18 | 24/24 | 2 | 20,402333 |
| 19 | 24/24 | 7 | 3,439167 |
| 20 | 24/24 | 4 | 18,142333 |
| 21 | 24/24 | 0 | 32,897833 |
| 22 | 24/24 | 9 | 14,023833 |
| 23 | 24/24 | 1 | 22,673333 |
| 24 | 24/24 | 10 | 7,071750 |
| 25 | 24/24 | 10 | 1,064417 |
| 26 | 24/24 | 2 | 1,950250 |
| 27 | 24/24 | 0 | 51,291417 |
| 28 | 24/24 | 0 | 27,035292 |
| 29 | 24/24 | 1 | 36,661000 |
| 30 | 24/24 | 2 | 3,110292 |

As médias diárias podem ser combinadas com peso no número de valores válidos. Aqui todos os dias têm 24, então seus pesos são iguais. Em recortes parciais ou com nulos, tirar a média simples das médias pode responder a outra pergunta.

## Conta manual de 15/11

A data foi escolhida no protocolo. Foram encontrados 24 valores conhecidos. Sua soma aritmética, calculada com `math.fsum`, foi **1.479,44**:

```text
média = 1479,44 / 24 = 61,64333333333334 MWmed
```

A conta coincide com a consulta. Os 24 valores estão em `verificacoes.json`. Essa soma é apoio aritmético da média, não uma nova medição física de energia ou uma conversão automática para MWh.

## LAG: fronteira do recorte e contexto anterior

Quando filtro novembro **antes** da janela, o primeiro registro não tem a hora anterior dentro da entrada: são **719 LAGs e 719 deltas**. Isso é uma fronteira do recorte, não um gap nas 720 horas de novembro. O arquivo `horario.csv` conserva esse resultado.

Foi registrado um adendo antes de uma segunda conferência, limitada ao contexto. Li também 31/10 23h, calculei a janela sobre 721 posições e só depois filtrei novembro. O arquivo `lag_com_contexto.csv` continua com 720 linhas, agora com **720 LAGs e 720 deltas conhecidos**. A comparação completa com pandas deu diferença zero.

| Versão, primeira hora de novembro | Valor | Instante anterior | Valor anterior | Delta |
| --- | ---: | --- | ---: | ---: |
| Recortar antes de LAG | 10,381 | NULL | NULL | NULL |
| Calcular LAG antes do recorte | 10,381 | 31/10 23h | 55,438 | -45,057 |

A ordem lógica é:

```sql
WITH janela AS (
    SELECT *,
           LAG(val_geracao) OVER (
               PARTITION BY id_ons ORDER BY din_instante
           ) AS valor_anterior
    FROM grade_com_contexto
)
SELECT *
FROM janela
WHERE din_instante >= '2025-11-01T00:00:00'
  AND din_instante <  '2025-12-01T00:00:00';
```

A consulta completa também contém calendário, quarentena, timestamps anteriores e estados do LAG. Não foi necessário repetir as agregações diárias nem substituir a saída original.

## Contraprovas que exercitam os caminhos ausentes no mês real

O caso C tem seis linhas, uma chave repetida com 7/9 e calendário parcial de 27 horas. As duas linhas conflitantes ficam em quarentena. As três médias são **2,5 / NULL / 4**, com denominadores **2 / 24 / 1** e cobertura válida **100% / 0% / 100%** da exposição pedida.

Nesse caso, INNER diário e LEFT diário mantêm os três dias: o dia de média NULL ainda tem registro. Na grade horária, INNER mantém quatro posições e LEFT mantém 27. Na fonte esparsa, o LAG de uma linha até 11/02 01h volta a 10/02 23h, duas horas antes; na grade, volta à meia-noite, que está sem registro.

Um controle com três dias e um único zero observado verifica os dias inteiramente ausentes: INNER diário retorna um dia; LEFT retorna três, preservando NULL nos dias sem registros. Outro controle com duas entidades impede mistura entre séries. Inverter a ordem das entradas não muda as quatro consultas. Esses testes mostram por que um mês completo não permite remover os controles.

## M00 e M07: soluções temporais fornecidas

Na emissão 04h com atraso 3h e janela 4h, o histórico vai de **22h do dia anterior a 01h**; o alvo h+12 é 16h. A medição de 02h só seria disponível às 05h pela hipótese e foi rejeitada. Na emissão 05h, o histórico vai de **23h a 02h**. SQL, pandas e as horas pré-declaradas coincidiram.

O rastreio de `renewcast predict` e os limites de adaptação do fluxo h+1 estão na solução M00. A análise de Exchange/broadcast, plano inicial/AQE, Photon nativo, cronômetro e desenho de medição está na solução M07. Não foram gerados novos tempos de cluster.

## Arquivos da entrega

- [M00: solução do fluxo e janela](../../reports/fechamento_m00_m09/bloco1_engenharia/M00-01/solucao_tecnica.md).
- [M01: caso C e semântica SQL](../../reports/fechamento_m00_m09/bloco1_engenharia/M01-01/solucao_tecnica.md).
- [M01: consultas reais](../../reports/fechamento_m00_m09/bloco1_engenharia/M01-02/consultas.sql), [diagnóstico dos 30 dias](../../reports/fechamento_m00_m09/bloco1_engenharia/M01-02/diagnostico.csv) e [LAG com contexto](../../reports/fechamento_m00_m09/bloco1_engenharia/M01-02/lag_com_contexto.csv).
- [M07: solução de plano e medição](../../reports/fechamento_m00_m09/bloco1_engenharia/M07-04/solucao_tecnica.md).

Os executores, SQLs, protocolos, adendo, recibos, versões e hashes estão nas pastas correspondentes. As saídas são desta execução registrada; os 23 arquivos históricos conferidos permaneceram preservados. Este fechamento técnico não encerra os bloqueios operacionais externos de tempo, publicação e cadastro.
