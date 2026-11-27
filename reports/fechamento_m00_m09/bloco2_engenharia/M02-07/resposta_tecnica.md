# M02-07 — resposta técnica fornecida: transferência para h+6

Autoria: Codex, 25/11/2026. Solução integral de engenharia com assistência declarada; não é resposta independente do usuário.

O recorte principal M02-08 é h+24; a transferência M02-07 aplica o mesmo estimando a h+6 usando outro CSV de previsões históricas salvas. O protocolo h+6 foi gravado às 16:20:13.842474 UTC, antes dos cálculos. A semente, réplicas, blocos, estratificação e regra de sinal são idênticos. Mudam o alvo temporal e os ajustes históricos já salvos; não houve novo ajuste.

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

Em h+24, o ganho contra história é 9,3841 MWmed e o ganho contra persistência é 0,5963 MWmed, com ICs deste último incluindo zero. Em h+6, a comparação contra história é menor, 6,2904, mas contra persistência é muito maior, 33,8080. Isso mostra por que a referência faz parte da pergunta: o HGB história tem MAE 38,1821 contra persistência 29,3943 em h+24; em h+6, os respectivos MAEs são 32,7444 e 60,2620.

A decisão fornecida é manter a evidência h+6 como melhoria condicional do erro agregado contra as duas referências, com ressalva de heterogeneidade. Para h+24, a evidência de melhoria frente ao HGB história é positiva, mas a vantagem frente à persistência não está estabelecida de modo estável. Nenhuma dessas frases se estende a dados futuros ou sustenta uma aprovação operacional. Não se subtraiu IC de h+6 do de h+24, nem se testou superioridade entre alvos distintos.

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

As tabelas completas estão em `analise_tecnica.md` e a conferência dos artefatos em `auditoria_final.json`.
