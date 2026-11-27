# Solução técnica assistida — M02-01

Responsável pela implementação e execução: Codex. Aplicação solicitada pelo usuário; não é resposta independente atribuída ao aluno.

## M02-01 — taxa-base, unidade e distribuição

### Conta executada

Das 20,000 oportunidades didáticas, 2% correspondem a 400 eventos e 19.600 a situações sem evento. A sensibilidade de 85% produz 340 positivos entre os eventos e 60 negativos. A taxa de falso positivo de 3% produz 588 positivos entre os 19.600 sem evento; restam 19.012 negativos.

| Sinal | Evento | Sem evento | Total |
| --- | ---: | ---: | ---: |
| Positivo | 340 | 588 | 928 |
| Negativo | 60 | 19.012 | 19.072 |
| Total | 400 | 19.600 | 20.000 |

```text
P(evento | positivo) = 340 / 928 = 85 / 232
                    = 0.366379310345 = 36.637931%
P(positivo | evento) = 340 / 400 = 85%
```

A primeira condição pergunta quantos positivos são eventos; a segunda pergunta quantos eventos geram um positivo. A taxa-base de 2% afeta a primeira. Sensibilidade alta não impede que a maioria dos positivos seja falsa quando o evento é raro e o falso positivo incide sobre uma população maior.

### As oito horas não são oito eventos independentes

Se uma mesma ocorrência dura oito horas, seus indicadores horários compartilham informação e duração. Não se justifica uma Binomial(24,p) apenas porque há 24 linhas: seriam necessários ensaios independentes e p constante. A unidade pode ser uma hora positiva ou o início de um episódio; são alvos diferentes. Para avaliar episódios, é preciso identificar início, fim, exposição observável e regra de agrupamento, preservando a informação temporal. Não foi estimada aqui uma probabilidade operacional de um detector real.

### Distribuições e condições de rejeição

Um indicador isolado 0/1 pode ser descrito marginalmente por Bernoulli(p); isso não torna a sequência IID nem mantém p estável entre regimes. Uma contagem por exposição fixa pode motivar Poisson(λ), se a taxa e os incrementos independentes forem defensáveis; agrupamento de episódios ou sobredispersão pode invalidar essa forma simples. Um erro contínuo pode motivar Normal(μ,σ²), mas assimetria forte, caudas pesadas ou variância que muda com o estado exigiriam outra avaliação. Se o objeto for geração não negativa, o suporte negativo da normal é outro ponto a examinar.

### População, amostra e outro ano

Os 20.000 casos e seus totais são uma tabela construída a partir das porcentagens fornecidas, não 20.000 medições coletadas pelo programa. Numa amostra real, as contagens flutuariam e a inclusão/ausência de dados precisaria ser descrita. A população-alvo deve definir período, equipamentos e unidade. Uma prevalência de outro ano pode não se transferir; sensibilidade e taxa de falso positivo também podem mudar. Inserir uma taxa-base antiga na fórmula não comprova disponibilidade, calibração ou validade operacional atuais.
