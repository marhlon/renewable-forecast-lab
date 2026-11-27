# M01-02 — parecer técnico

Novembro de 2025 foi fixado no protocolo antes da consulta. O executor leu o Parquet manifestado, preservou os 720 rótulos de hora e conferiu o recorte com a exportação histórica. SQLite e pandas reconciliaram as tabelas diária, horária, de quarentena e de LAG esparso, com mesmas cardinalidades e máscaras de nulos.

O mês tem 720 registros válidos em 720 posições esperadas, 49 zeros, nenhuma lacuna, duplicata ou medição nula e cobertura de 100% em todos os 30 dias. Há 719 LAGs conhecidos; o primeiro depende do contexto anterior ao recorte e permanece desconhecido, sem ser classificado como lacuna da fonte.

A média mensal é 28,260979166666665 MWmed. A conta escolhida previamente de 15/11 resulta em 1.479,44 / 24 = 61,64333333333334 MWmed. A maior diferença numérica SQL/pandas foi 8,881784197001252e-16 na tabela diária; nas tabelas horária, de quarentena e LAG esparso foi zero, dentro do critério declarado antes da execução.

O suplemento com adendo prévio adicionou apenas 31/10 23h ao contexto, calculou LAG antes do filtro e preservou 720 linhas de novembro. Assim obteve 720 LAGs e deltas conhecidos, com diferença SQL/pandas zero. A primeira diferença é 10,381 - 55,438 = -45,057. O arquivo original com 719 pares permanece intacto e identificado como cálculo após recortar o mês.

Os casos controlados confirmam que um mês completo não permite dispensar calendário, quarentena ou análise de nulos em outros dados. A solução técnica assistida está concluída. Não houve novo treino, inferência, aquisição de dados ou teste preditivo independente. Todos os recibos anteriores permaneceram preservados.
