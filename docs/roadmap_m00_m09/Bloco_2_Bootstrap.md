# Bootstrap horário aplicado — bloco 2

25/11/2026 · M02-08 e M02-07 · portão de engenharia.

## Resultado e decisão técnica

A história+meteorologia reduz o MAE agregado contra o HGB história nos dois horizontes salvos. A referência muda a decisão: em h+24, a vantagem sobre persistência é pequena e incerta; em h+6, o ganho agregado contra persistência é maior, com heterogeneidade por semana. O aceite aqui é a execução e interpretação corretas, sem exigir ganho positivo ou aprovar implantação.

## Recorte e relógios

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

## Método e interpretação da incerteza

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

### h+24: métricas e efeito

MAE de persistência: **29.3943 MWmed**; HGB história: **38.1821 MWmed**; HGB história+meteorologia: **28.7980 MWmed**.

#### Ganho contra HGB história

| Bloco (h) | Ganho (MWmed) | IC percentil nominal 95% (MWmed) | Fração ≤ 0 |
| ---: | ---: | --- | ---: |
| 6 | 9.3841 | [5.8353; 13.0925] | 0.0000 |
| 24 | 9.3841 | [5.2595; 13.6790] | 0.0000 |
| 48 | 9.3841 | [4.7548; 14.0363] | 0.0000 |

Todos os folds, sem escolher o bloco pelo sinal:

| Fold | Bloco (h) | Ganho (MWmed) | IC percentil nominal 95% (MWmed) | Fração ≤ 0 |
| --- | ---: | ---: | --- | ---: |
| 1 | 6 | 7.0894 | [0.3566; 14.1856] | 0.0188 |
| 2 | 6 | 11.9949 | [5.7103; 18.3859] | 0.0000 |
| 3 | 6 | 9.0680 | [3.3877; 15.3282] | 0.0008 |
| 1 | 24 | 7.0894 | [-1.8701; 16.6467] | 0.0686 |
| 2 | 24 | 11.9949 | [6.4911; 17.8848] | 0.0000 |
| 3 | 24 | 9.0680 | [3.0749; 15.5100] | 0.0006 |
| 1 | 48 | 7.0894 | [-3.4766; 17.1595] | 0.1008 |
| 2 | 48 | 11.9949 | [5.9222; 18.3418] | 0.0000 |
| 3 | 48 | 9.0680 | [2.8858; 16.8048] | 0.0000 |

#### Ganho contra persistência — suplemento

| Bloco (h) | Ganho (MWmed) | IC percentil nominal 95% (MWmed) | Fração ≤ 0 |
| ---: | ---: | --- | ---: |
| 6 | 0.5963 | [-5.3247; 6.4924] | 0.4312 |
| 24 | 0.5963 | [-7.2504; 9.1035] | 0.4596 |
| 48 | 0.5963 | [-7.8656; 8.8676] | 0.4278 |

Todos os folds, sem escolher o bloco pelo sinal:

| Fold | Bloco (h) | Ganho (MWmed) | IC percentil nominal 95% (MWmed) | Fração ≤ 0 |
| --- | ---: | ---: | --- | ---: |
| 1 | 6 | -7.7185 | [-22.6962; 7.1376] | 0.8400 |
| 2 | 6 | 4.2482 | [-2.8299; 11.2105] | 0.1260 |
| 3 | 6 | 5.2591 | [-0.9471; 11.5194] | 0.0490 |
| 1 | 24 | -7.7185 | [-28.8645; 14.4169] | 0.7560 |
| 2 | 24 | 4.2482 | [-2.7587; 11.4667] | 0.1218 |
| 3 | 24 | 5.2591 | [-2.4408; 12.7995] | 0.0950 |
| 1 | 48 | -7.7185 | [-31.0459; 14.2196] | 0.7192 |
| 2 | 48 | 4.2482 | [-2.0309; 9.9432] | 0.0862 |
| 3 | 48 | 5.2591 | [-2.9931; 13.2680] | 0.1100 |

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

### h+6: métricas e efeito

MAE de persistência: **60.2620 MWmed**; HGB história: **32.7444 MWmed**; HGB história+meteorologia: **26.4540 MWmed**.

#### Ganho contra HGB história

| Bloco (h) | Ganho (MWmed) | IC percentil nominal 95% (MWmed) | Fração ≤ 0 |
| ---: | ---: | --- | ---: |
| 6 | 6.2904 | [3.7394; 8.9650] | 0.0000 |
| 24 | 6.2904 | [2.7851; 9.4984] | 0.0000 |
| 48 | 6.2904 | [2.5634; 9.5396] | 0.0004 |

Todos os folds, sem escolher o bloco pelo sinal:

| Fold | Bloco (h) | Ganho (MWmed) | IC percentil nominal 95% (MWmed) | Fração ≤ 0 |
| --- | ---: | ---: | --- | ---: |
| 1 | 6 | 11.8074 | [5.9084; 17.7790] | 0.0000 |
| 2 | 6 | 2.5007 | [-0.3898; 5.1690] | 0.0426 |
| 3 | 6 | 4.5631 | [0.3122; 9.1198] | 0.0164 |
| 1 | 24 | 11.8074 | [3.3783; 19.5228] | 0.0036 |
| 2 | 24 | 2.5007 | [0.9496; 3.9353] | 0.0006 |
| 3 | 24 | 4.5631 | [-0.8234; 9.9701] | 0.0494 |
| 1 | 48 | 11.8074 | [2.4449; 19.2527] | 0.0068 |
| 2 | 48 | 2.5007 | [1.0240; 3.8615] | 0.0000 |
| 3 | 48 | 4.5631 | [-1.0396; 10.3612] | 0.0624 |

#### Ganho contra persistência — suplemento

| Bloco (h) | Ganho (MWmed) | IC percentil nominal 95% (MWmed) | Fração ≤ 0 |
| ---: | ---: | --- | ---: |
| 6 | 33.8080 | [26.2586; 41.2516] | 0.0000 |
| 24 | 33.8080 | [23.8023; 43.1542] | 0.0000 |
| 48 | 33.8080 | [21.8947; 45.0661] | 0.0000 |

Todos os folds, sem escolher o bloco pelo sinal:

| Fold | Bloco (h) | Ganho (MWmed) | IC percentil nominal 95% (MWmed) | Fração ≤ 0 |
| --- | ---: | ---: | --- | ---: |
| 1 | 6 | 3.6740 | [-12.5998; 20.5450] | 0.3332 |
| 2 | 6 | 51.3050 | [41.3832; 61.5766] | 0.0000 |
| 3 | 6 | 46.4450 | [36.1718; 56.5295] | 0.0000 |
| 1 | 24 | 3.6740 | [-23.6343; 28.9793] | 0.4024 |
| 2 | 24 | 51.3050 | [41.9825; 60.7048] | 0.0000 |
| 3 | 24 | 46.4450 | [38.6538; 53.8237] | 0.0000 |
| 1 | 48 | 3.6740 | [-29.5059; 34.5652] | 0.3980 |
| 2 | 48 | 51.3050 | [40.1508; 62.5426] | 0.0000 |
| 3 | 48 | 46.4450 | [38.6986; 54.1071] | 0.0000 |

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

## Transferência aplicada entre os recortes

A adaptação de h+24 (M02-08) para h+6 (M02-07) conserva o estimando, a unidade MWmed, o pareamento, a estratificação e todos os parâmetros. Muda o CSV, o horizonte e o alvo; o protocolo identifica essa mudança antes da análise. A conclusão foi recalculada: o contraste com história fica positivo nos dois agregados; o contraste com persistência passa de pequeno/incerto em h+24 para grande nos agregados h+6. Essa mudança é resultado dos dados, não cópia de uma conclusão histórica. Não autoriza chamar h+6 de superior a h+24, pois os alvos diferem.

## Proveniência e verificações

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

Ambiente dos quatro recibos: Python 3.12.13, NumPy 2.5.3, pandas 3.0.5, Windows 11. Fonte congelada SHA-256 `f8c1dff888fb5796e5405b87761da038d73af4164435f829abd1f1cca078dc03`.

Comando conjunto efetivamente executado, preservado nos resultados:

```powershell
& 'C:\Users\marhl\miniconda3\envs\renewable-forecast\python.exe' reports\fechamento_m00_m09\bloco2_engenharia\M02-08\executar.py
```

O runner chamou a CLI quatro vezes com `--block-hours 6 24 48 --repetitions 5000 --seed 42`. As listas exatas de argumentos, stdout, stderr, horários e exit code 0 estão em `resultado.json`; cada chamada tem `cli_historia/receipt.json` ou `cli_persistencia/receipt.json`. O tempo externo conjunto foi 118,22 s, incluindo inicialização dos subprocessos; os tempos internos menores da CLI não representam todo o custo observado pelo runner.

| Item | Fonte das previsões | SHA-256 de predictions.csv |
| --- | --- | --- |
| M02-08 / h+24 | `reports/weather_ablation/CJU_BA5EIGT/july_development_h24` | `ae4c804e0e812c426ab5430868d5f482d5af5fd814e7eca3e64c32a9849ae022` |
| M02-07 / h+6 | `reports/weather_ablation/CJU_BA5EIGT/july_development` | `291e9aec32608505b4ec7423de814401e372cf3411fcefad001ffeb4a0f7df76` |

## Arquivos de saída

Em cada pasta `reports/fechamento_m00_m09/bloco2_engenharia/M02-08` e `M02-07`: protocolo e resultado preservados; `bootstrap.csv` principal; `bootstrap_vs_persistencia.csv`; CSV derivado e linhagem; dois recibos CLI; `analise_tecnica.md`, `parecer.md` e `auditoria_final.json`. M02-07 acrescenta `resposta_tecnica.md`, e `reports/statistical_audit.md` consolida a interpretação. O script `documentar_e_auditar.py` audita e documenta sem sortear novas réplicas. Seus arquivos são exclusivos: a repetição exige destinos novos para preservar esta rodada.

A decisão de cadastro e a revisão integrada do bloco cabem à consolidação do agente principal. Estes artefatos não encerram formação independente nem comprovações do portão operacional.
