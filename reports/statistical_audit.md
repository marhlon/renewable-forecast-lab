# Auditoria estatística aplicada — M02-07 e M02-08

25/11/2026 · Codex · assistência integral declarada.

Este relatório é a síntese da análise de bootstrap em previsões de desenvolvimento já examinadas. Não registra novo benchmark nem uma resposta independente do usuário.

São 504 previsões salvas por horizonte para CJU_BA5EIGT, com origens
horárias de 11/07/2026 06:00 a 01/08/2026 05:00, conforme timestamps do CSV
interpretados como UTC. Fold 1 vai até 18/07 05:00; fold 2, de 18/07 06:00
a 25/07 05:00; fold 3, de 25/07 06:00 a 01/08 05:00. O rótulo
`july_development` não implica que todos os alvos estejam em julho.
Foi conferido `target_time − forecast_origin = horizonte` em todas as linhas,
e `target_available_at − target_time = 2h`. Isso verifica a coerência interna
dos relógios gravados; o significado físico do fuso e a disponibilidade
histórica operacional continuam sujeitos aos limites M04.

Os dois conjuntos já haviam sido examinados e usados no desenvolvimento.
O protocolo novo fixa a análise da incerteza; não transforma esses dados em
holdout novo. As origens/folds coincidem, mas os alvos h+6 e h+24 ocorrem em
instantes diferentes e os cortes de treino históricos também diferem.
Portanto, a comparação entre horizontes é descritiva. Não foi calculado
intervalo da diferença entre horizontes, teste de superioridade de horizonte
ou efeito causal da meteorologia.

O estimando principal é a média dos deltas pareados
`|alvo − HGB história| − |alvo − HGB história+meteorologia|`, em MWmed.
O suplemento troca apenas a referência por persistência. Ganho positivo favorece
o candidato história+meteorologia; ganho contra um HGB fraco não implica ganho
contra a persistência.

Os protocolos foram registrados em 25/11/2026, às 16:20:13 UTC, antes das quatro
execuções, concluídas entre 16:22:39 e 16:24:38 UTC. Fixaram 5.000 réplicas,
semente 42, blocos 6/24/48 horas e quantis lineares 2,5%/97,5%. Cada réplica
reamostra blocos consecutivos **dos deltas pareados**, com retorno circular
restrito ao mesmo fold, até obter 168 horas; o último bloco é truncado.
Nenhum bloco atravessa a fronteira de um fold. Os três folds observados ficam
fixos, com 168 horas cada; não se sorteiam folds como unidades independentes.
O agregado usa a média ponderada por n das três médias de cada réplica, e
calcula seus quantis a partir dessas 5.000 médias agregadas. Não se faz média
das pontas dos intervalos. Como os folds têm o mesmo n, os pesos são 1/3.

Os fluxos locais usam `SeedSequence([42, comprimento_do_bloco, fold])`.
Os três comprimentos foram fixados antes do cálculo e todos são publicados,
independentemente do sinal. Um bloco de 6 horas não é o horizonte h+6:
o primeiro é uma escolha de dependência na reamostragem; o segundo identifica
o alvo da previsão.

O intervalo é percentil, nominalmente de 95%, **condicional às previsões
salvas, aos folds e à família de blocos escolhida**. Não é intervalo de
predição de uma observação futura, garantia de cobertura futura ou correção
da seleção histórica de modelos. A fração de réplicas com ganho ≤ 0 é um
resumo descritivo da distribuição bootstrap, sem centralização sob uma
hipótese nula; **não é p-valor**, probabilidade de a hipótese nula ser verdadeira
ou probabilidade de o modelo perder no futuro. Fração zero significa zero
ocorrências nas 5.000 réplicas, sem provar impossibilidade de perda.

O método preserva dependência local dentro do tamanho do bloco, sob uma
aproximação de repetição temporal dentro de cada fold. O retorno do final
para o início de uma semana é uma aproximação; a distribuição real pode
conter mudanças de regime e dependência além de 48 horas. A escolha de blocos
não elimina isso. Não foi usado bootstrap IID como evidência temporal, nem
inferida independência dos folds ou dos três comprimentos. Os intervalos
publicados são pontuais; não há ajuste de comparações múltiplas nem alegação
de cobertura simultânea de todas as linhas.

## h+24

O ganho principal é 9,3841 MWmed (24,5773% do MAE do HGB história).
Os três intervalos agregados ficam acima de zero. Isso sustenta uma redução
condicional do erro nesse desenvolvimento em relação ao HGB de história
congelado. No fold 1, porém, os intervalos de blocos 24h e 48h incluem zero,
enquanto o de 6h fica pouco acima de zero. Os folds 2 e 3 têm intervalos
positivos nas três escolhas. A média agregada não torna uniforme a evidência
de cada semana.

A persistência já tem MAE 29,3943 MWmed, menor que os 38,1821 do HGB história.
Contra ela, o ganho do candidato é apenas 0,5963 MWmed (2,0285%); os três
intervalos agregados incluem zero. O fold 1 apresenta ganho pontual
**negativo de −7,7185**, contraposto a +4,2482 e +5,2591 nos outros folds.
Logo, esta análise não estabelece melhoria estável sobre a persistência.
Escolher apenas o contraste contra história ou apenas o bloco de 6h ocultaria
essa conclusão prática. Não há limiar econômico de benefício registrado
neste protocolo; MAE e IC por si só não encerram uma decisão de operação.

### Referência HGB história

| Bloco (h) | Ganho (MWmed) | IC percentil nominal 95% (MWmed) | Fração ≤ 0 |
| ---: | ---: | --- | ---: |
| 6 | 9.3841 | [5.8353; 13.0925] | 0.0000 |
| 24 | 9.3841 | [5.2595; 13.6790] | 0.0000 |
| 48 | 9.3841 | [4.7548; 14.0363] | 0.0000 |

### Referência persistência

| Bloco (h) | Ganho (MWmed) | IC percentil nominal 95% (MWmed) | Fração ≤ 0 |
| ---: | ---: | --- | ---: |
| 6 | 0.5963 | [-5.3247; 6.4924] | 0.4312 |
| 24 | 0.5963 | [-7.2504; 9.1035] | 0.4596 |
| 48 | 0.5963 | [-7.8656; 8.8676] | 0.4278 |

## h+6

O ganho principal é 6,2904 MWmed (19,2106% do MAE do HGB história).
Os três intervalos agregados ficam acima de zero; as frações ≤ 0 são 0,
0 e 0,0004. A última corresponde a 2 de 5.000 réplicas, sem interpretação
de p-valor. A heterogeneidade semanal permanece: o fold 2 inclui zero
com bloco de 6h, mas tem intervalos positivos com 24h/48h; no fold 3
acontece a inversão. O fold 1 tem ganho maior, 11,8074 MWmed, com os três
intervalos positivos. Dependência serial e truncamento do último bloco
podem tornar a largura não monotônica; não se exige que todo bloco maior
gere todo intervalo maior, nem se escolhe a conclusão mais conveniente.

Contra persistência, o ganho é 33,8080 MWmed (56,1017%), com intervalos
agregados positivos em 6/24/48h. Ainda assim, o fold 1 tem ganho apenas
3,6740 e intervalos cruzando zero nas três escolhas, enquanto os folds 2 e 3
mostram ganhos de 51,3050 e 46,4450. O efeito agregado forte está ligado
a essas duas semanas; não é evidência de benefício uniforme em todo regime.

### Referência HGB história

| Bloco (h) | Ganho (MWmed) | IC percentil nominal 95% (MWmed) | Fração ≤ 0 |
| ---: | ---: | --- | ---: |
| 6 | 6.2904 | [3.7394; 8.9650] | 0.0000 |
| 24 | 6.2904 | [2.7851; 9.4984] | 0.0000 |
| 48 | 6.2904 | [2.5634; 9.5396] | 0.0004 |

### Referência persistência

| Bloco (h) | Ganho (MWmed) | IC percentil nominal 95% (MWmed) | Fração ≤ 0 |
| ---: | ---: | --- | ---: |
| 6 | 33.8080 | [26.2586; 41.2516] | 0.0000 |
| 24 | 33.8080 | [23.8023; 43.1542] | 0.0000 |
| 48 | 33.8080 | [21.8947; 45.0661] | 0.0000 |

## Conferência e decisão

Foram preservados a fonte congelada do bootstrap, os CSVs de origem,
os protocolos, metadados e métricas históricos, os quatro recibos CLI e os
dois resultados já concluídos. Esta retomada auditou os arquivos existentes;
não repetiu os sorteios, o treino, a inferência nem os 59 testes M02-05.
Os hashes da fonte e dos testes coincidem com o recibo de 59 casos aprovados,
cujo alcance continua sendo construção/verificação do método em casos
controlados. A execução nos dados reais salvos é evidência distinta, aqui
registrada nos recibos M02-08/M02-07.

A auditoria final reconcilia SHA-256 das entradas, protocolos, fonte,
recibos e saídas; verifica precedência temporal do protocolo, comandos e
exit codes 0, 504 linhas, grades horárias, folds, erros absolutos e deltas,
parâmetros, 12 linhas de resumo por comparação, estimativas pontuais e
ponderação por n, finitude e ordenação dos intervalos. As réplicas individuais
não foram persistidas pela CLI congelada: os quantis são os produzidos por
essa fonte, coberta pelos testes prévios. A revisão dos resumos não se
apresenta como recomputação independente de cada sorteio ou de seus quantis.

No suplemento, `pareado_persistencia.csv` é uma derivação declarada:
`hgb_history` recebe a coluna original `persistence` somente para reutilizar
o campo de referência exigido pela CLI; `original_hgb_history` preserva o
HGB original, e `reference_model=persistence` identifica a troca.
Origens, alvos, disponibilidade, folds e candidato foram preservados exatamente;
o delta foi recalculado para a nova referência. A coluna do resumo CLI chamada
`mae_history_mwmed` representa **MAE da persistência** nesse suplemento.
`linhagem_persistencia.json` registra fonte, derivação e hashes. Os recibos
brutos mantêm os nomes genéricos da CLI; a interpretação correta está nesta
linhagem e nos títulos das tabelas.

Toda solução, execução e interpretação são atribuídas ao Codex, com assistência
integral declarada. A revisão técnica assistida não certifica autonomia pessoal,
autoria independente, aprovação humana ou autorização de operação.

O efeito foi calculado por par de previsões, e a dependência recebeu a sensibilidade de três blocos previamente fixados. A decisão é técnica e condicional ao desenvolvimento: concluir a entrega de engenharia e preservar os limites de generalização e operação. Os detalhes por fold, comandos e hashes constam nas pastas M02-07/M02-08 do bloco 2 e em `docs/roadmap_m00_m09/Bloco_2_Bootstrap.md`.
