# M05-01 — cobertura alta demais também é um resultado ruim

25/11/2026 · avaliação retrospectiva executada · entrega de engenharia

A rotina congelada foi aplicada uma vez ao arquivo de outubro depois da liberação do selo conjunto. O contrato passou: 744 horas únicas e finitas do CJU_BA5EIGT, de 01/10 a 31/10, com 695 origens comuns de 02/10 às 01h até 30/10 às 23h. O comando terminou com código 0. O SHA-256 da série filtrada é `aecb3a89ff306b93fa694d800b9659aa7d4d551763930589b5abad70931a87ab`.

## Resultado observado

| Intervalo | Alvos cobertos | Cobertura | Largura média — MWmed | Interval score | Pinball média |
| --- | ---: | ---: | ---: | ---: | ---: |
| P10–P90 ordenados | 679/695 | 97,6978% | 72,920623 | 76,989183 | 5,508005 |
| Expansão CQR congelada | 686/695 | 98,7050% | 103,168575 | 104,578288 | 6,427642 |

O alvo nominal era 80%, não 100%. A cobertura bruta já ficou 17,70 pontos percentuais acima desse alvo. A expansão de 15,123976 MWmed de cada lado, estimada em julho, acrescentou aproximadamente 30,247952 MWmed à largura média para incluir apenas sete alvos adicionais. O interval score, que penaliza largura e violações, piorou: quanto menor, melhor. A Pinball Loss também piorou após usar as extremidades expandidas. Portanto, a expansão não deve ser descrita como melhoria geral deste teste. Ela aumentou a cobertura de intervalos que já estavam excessivamente largos para o nominal observado.

A avaliação não alterou a expansão nem escolheu outro valor. A passagem de cobertura de 70,19% para 80,45% na calibração de julho não se transferiu como cobertura próxima de 80% em outubro. O achado é uma falha de estabilidade da calibração, sem identificação da causa física ou estatística específica.

## Estabilidade e incerteza

| Período fixo | Origens | Cobertura bruta | Cobertura CQR | Alerta de desvio de 80% |
| --- | ---: | ---: | ---: | --- |
| Semana 1 | 168 | 99,4048% | 100% | Sim, ambas |
| Semana 2 | 168 | 100% | 100% | Sim, ambas |
| Semana 3 | 168 | 94,0476% | 96,4286% | Sim, ambas |
| Semana 4 | 168 | 97,0238% | 98,2143% | Sim, ambas |
| Parte final | 23 | 100% | 100% | Não julgado: menos de 48 origens |

As fronteiras dessas semanas foram fixadas antes de consultar a fonte, ancoradas em 02/10 às 01h. São intervalos de 168 horas, não semanas de calendário. O alerta é bilateral: tanto cobertura abaixo de 70% quanto acima de 90% se afastam mais de dez pontos do nominal. A parte final tem 23 horas e permanece separada.

O bootstrap circular pareado de blocos de 24 horas, com 2.000 reamostragens e semente 17, produziu intervalos percentis condicionais de 95%:

- Cobertura bruta: **94,8201% a 99,8561%**.
- Cobertura CQR: **96,8345% a 100%**.
- Diferença CQR menos bruta: **0,1439 a 2,3022 pontos percentuais**, com estimativa central de 1,0072 ponto.

Os mesmos índices foram usados para os dois intervalos. Esses limites quantificam a variabilidade sob o recorte e o esquema de blocos fixados. Não garantem cobertura futura, independência das horas ou validade conformal sob dependência temporal.

## Decisão e evidência

O código, o ajuste, os relógios, os arquivos e a interpretação estão conferidos. O modelo de intervalo não fica aprovado para operação: neste recorte, a calibração nominal não se manteve. A ação concreta é preservar o resultado e exigir outro experimento temporal, planejado antes de seus dados, para avaliar estabilidade e alternativas de calibração. Ajustar a expansão agora para atingir 80% no mesmo outubro invalidaria a separação entre desenvolvimento e avaliação.

A fonte é um snapshot obtido em 25/11/2026, após o freeze de código e modelos. Ela pode conter revisões e não comprova qual valor estava publicado em cada origem de outubro. Também permanecem as hipóteses de fuso e atraso de duas horas. A execução é retrospectiva; não demonstra shadow ao vivo ou produção.

O [método de ajuste](metodo_ajuste.md) detalha treino, rank CQR e parâmetros. As evidências são [cobertura_por_periodo.csv](cobertura_por_periodo.csv), [incerteza_cobertura.csv](incerteza_cobertura.csv), [predicoes_avaliacao.csv](predicoes_avaliacao.csv) e [resultado.json](resultado.json). Implementação, execução e revisão fornecidas com assistência de Codex, sem atribuição de desempenho independente ao usuário.
