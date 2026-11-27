**Renewcast — execução, resultados e cobertura das pendências de M01 a M09**

Estado consolidado em 26/11/2026. Este documento reúne as implementações já aceitas, as correções e execuções dos três blocos da retomada e as limitações que continuam abertas. A consolidação usa os relatórios e recibos existentes; não corresponde a outro treinamento ou teste dos modelos.

No recorte solicitado, **M01–M09, há 34 itens validados e dez bloqueados, entre 44 itens auditáveis**. O cadastro completo também inclui M00, preparação: por isso os relatórios gerais apresentam **35 validados e dez bloqueados, entre 45 itens**. Esses números contam itens do cadastro, não horas de trabalho, domínio pessoal, unidades de toda a formação ou percentual de prontidão para produção.

| Módulo | Itens validados / total | Cobertura obtida em relação às lacunas anteriores |
| --- | ---: | --- |
| M01 — Dados e SQL | 2/2 | Diagnóstico em outro mês, janelas SQL, calendário, nulos, duplicidades e fronteira do LAG aplicados e reconciliados |
| M02 — Fundamentos quantitativos | 8/8 | Probabilidade, estimação, hipóteses, regressão, pressupostos, perdas, bootstrap implementado e executado e análise em outro horizonte |
| M03 — ML clássico | 4/4 | Seleção temporal por grupos de atributos, explicação local Shapley por grupos, defesa técnica e avaliação reservada retrospectiva |
| M04 — Meteorologia e horizontes | 1/5 | Correção E51, origem das previsões e mecanismos temporais documentados; quatro comprovações externas continuam bloqueadas |
| M05 — Incerteza e classificação | 5/5 | CQR, calibração de classe, política com orçamento, rampa de uma hora, LightGBM/CatBoost e modelo global próprio executados |
| M06 — Engenharia e MLOps | 3/9 | Registro local auditado, CI remoto e MLflow Registry demonstrados; drift, segurança e capacidade com demonstração local parcial |
| M07 — Dados em escala | 4/4 | Medallion local, pipeline incremental multissérie, recuperação, medições reais e interpretação corrigida do plano |
| M08 — Deep Learning | 3/3 | Brutos Windows auditados, decisão GRU/HGB e adaptação de janela/batching/estado executadas |
| M09 — Transformers e pré-treino | 4/4 | Artefatos auditados, composição e máscaras em outro contexto, comparação Chronos e decisão integrada documentadas |

Os aceites são de engenharia no escopo descrito. A assistência está registrada nos documentos de origem; as soluções fornecidas não certificam execução ou defesa independente do usuário. As condições operacionais permanecem vinculadas aos itens correspondentes.

**M01 — Dados e SQL.** A base anterior já continha a série ONS em Parquet, contratos temporais, consultas com JOIN, agrupamentos, tratamento de nulos e uma reconciliação orientada do LAG. A retomada acrescentou a aplicação completa a outro mês e a explicação das fronteiras das janelas.

Foi fixado novembro de 2025 e executado o diagnóstico em SQLite, com comparação integral em pandas. As consultas conferiram granularidade, chaves, duplicidades, valores válidos, zeros, ausências, médias e cobertura diária. O calendário foi preservado por LEFT JOIN; somente contagens ausentes recebem zero. Uma média desconhecida continua nula. Nos casos controlados de chave duplicada ambígua, todas as cópias vão para quarentena: não se escolhe uma medição arbitrária.

| Medida em novembro/2025 | Resultado |
| --- | ---: |
| Horas esperadas / registros encontrados | 720 / 720 |
| Dias / medições válidas | 30 / 720 |
| Zeros informados pela fonte | 49 |
| Nulos / horas sem registro | 0 / 0 |
| Duplicidades / quarentena | 0 / 0 |
| Cobertura diária | 100% |
| Média mensal | 28,2609791667 MWmed |

Os 49 zeros foram preservados como valores da fonte; não vieram de preenchimento de lacunas nem permitem determinar uma causa física. Em 15/11, a soma de 1.479,44 dividida por 24 resultou em média de 61,6433333333 MWmed. A diferença máxima entre as médias diárias SQL/pandas foi 8,88×10⁻¹⁶, compatível com ponto flutuante.

O primeiro diagnóstico tinha 719 pares LAG dentro do mês. O primeiro nulo era uma fronteira da consulta, pois o recorte não incluía a hora anterior. O suplemento passou a ler também 31/10 às 23h, calcular a janela e só então filtrar novembro. Continuaram existindo 720 horas, agora com **720 pares LAG/delta**. O primeiro delta foi `10,381 − 55,438 = −45,057 MWmed`. As duas saídas foram preservadas para tornar observável o efeito do contexto.

Isso cobre a lacuna de aplicação das janelas SQL e transferência do diagnóstico para outro mês. Também deixa explícito que LAG de uma linha só representa uma hora quando a grade e a entidade garantem essa relação.

Evidência detalhada: [diagnóstico aplicado](Diagnostico_SQL_Aplicado.md), [relatório do bloco 1](Relatorio_Engenharia_Bloco1.md) e pastas `reports/fechamento_m00_m09/bloco1_engenharia/M01-01` e `M01-02`.

**M02 — Fundamentos quantitativos.** Antes da retomada já existiam resíduos, métricas, comparação temporal, incerteza, gradiente em M08 e uma clínica de perda e decisão. O bloco que faltava foi organizado em probabilidade e distribuições, estimação, testes de hipóteses, regressão e pressupostos, dependência temporal, bootstrap e decisão sob custos.

Na probabilidade foram trabalhadas população, unidade amostral, evento, independência, probabilidade condicional, esperança, variância, CDF e quantis. Bernoulli, Binomial, Poisson, Normal e t de Student foram apresentadas com seus parâmetros, suporte e condições de uso. As demonstrações são cenários numéricos e simulações, sem apresentá-las como observações reais do ONS.

Uma conta executada usou 20.000 oportunidades, prevalência de 2%, sensibilidade de 85% e falso positivo de 3% entre não eventos. Produziu 340 verdadeiros positivos, 60 falsos negativos, 588 falsos positivos e 19.012 verdadeiros negativos. Assim, `P(evento | sinal positivo) = 340/(340+588) = 36,637931%`. A conta mostra concretamente por que sensibilidade de 85% não significa que 85% dos sinais sejam eventos.

Na estimação, para `[18,20,22,24]`, foram calculados média 21, variância amostral 20/3 e erro-padrão 1,29099445. Sob Normal IID, o IC de 95% da média foi `[16,89147988;25,10852012]`, enquanto o intervalo de uma nova observação foi `[11,81306973;30,18693027]`. A diferença decorre da variabilidade adicional de uma nova observação. Um cenário AR(1) de 72 leituras, com correlação assumida de 0,6, deu tamanho efetivo aproximado de 18 e cálculo finito de 18,48128342. Essa correlação não foi atribuída à série ONS.

Nos testes de hipóteses, seis médias de blocos fornecidas tiveram média 1,08333333. Contra efeito mínimo de 0,5, o teste unilateral retornou t=2,65486938, p=0,02258068 e limite inferior nominal de 0,64058286. A conclusão depende dos pressupostos declarados para as médias de blocos. Em uma família separada de três p-valores, Bonferroni fixou 0,05/3=0,01666667: somente 0,009 passou. Foram diferenciados significância, tamanho de efeito, potência, equivalência e ausência de rejeição.

Na regressão, o exemplo `x=[−2,0,2]`, `y=[0,1,5]` teve matriz com intercepto de shape `(3,2)` e coeficientes `(2,)`. OLS retornou `[2;1,25]`. Ridge, com MSE dividida por n, λ=1/3 e intercepto não penalizado, retornou `[2;10/9]`. O gradiente inicial foi `[−4;−20/3]`: subtrair um gradiente negativo aumenta inicialmente os coeficientes. Com taxa 0,1, a MSE caiu de 8,6667 para 3,9674; com taxa 1, subiu para 82,7407. Para essa quadrática específica, a faixa estrita de convergência é `0<taxa<0,375`.

Acrescentar a coluna 2x gerou três colunas e posto 2: diferentes coeficientes produzem as mesmas previsões. Foram explicitados colinearidade, exogeneidade, autocorrelação, variância e a diferença entre inferência sobre coeficientes e previsão. Regularização não transforma uma associação em efeito causal.

O bootstrap que terminava incompleto em `rows=[]` foi reconstruído como versão identificada, com CLI, resumo, parâmetros, versões e hashes. A implementação preserva pares de alvo/previsões, sorteia blocos circulares dentro de cada fold e pondera o agregado pela quantidade de origens. Foram aprovados 59 testes de construção. Na contraprova com três ganhos iguais a 1 e cinco iguais a 3, o agregado correto é 2,25, em vez da média simples 2 das duas médias de folds.

A função foi depois executada sobre previsões meteorológicas preservadas, sem novo treino: h+24 e h+6, contra HGB histórico e persistência. Cada horizonte usa 504 origens em três semanas de 168, blocos de 6/24/48 horas, 5.000 réplicas e semente 42. Ganho positivo significa redução de erro absoluto pela alternativa com vento.

| Horizonte | Referência | Ganho médio — MWmed | IC nominal 95%, bloco de 24h |
| --- | --- | ---: | --- |
| h+24 | HGB histórico | 9,3841 | [5,2595;13,6790] |
| h+24 | Persistência | 0,5963 | [−7,2504;9,1035] |
| h+6 | HGB histórico | 6,2904 | [2,7851;9,4984] |
| h+6 | Persistência | 33,8080 | [23,8023;43,1542] |

O vento melhorou o HGB histórico no agregado h+24, mas a comparação contra persistência não demonstrou ganho convincente nesse horizonte. O h+6 foi interpretado por seus próprios resultados. Foram conferidos 48 resumos e seus pareamentos; as diferenças na recomputação dos ganhos/MAEs ficaram em até 7,11×10⁻¹⁵. Esses intervalos são condicionais às previsões e recortes; não incluem novo ajuste, outro regime ou revisão da fonte. As réplicas individuais não foram persistidas, e a auditoria dos resumos não foi chamada de reprodução independente dos sorteios.

A ligação entre previsão e decisão também foi executada: a clínica recalculou 36 perdas sobre 168 origens antigas e, separadamente, 66 linhas de custos FP/FN em 504 origens. Sob perda linear assimétrica, o quantil de decisão é `c_sub/(c_sub+c_super)`. Custos iguais favoreceram Chronos P50, perda 31,340738; subestimação quatro vezes mais cara favoreceu P80, 58,740425; superestimação quatro vezes mais cara favoreceu P20, 54,573165. São razões hipotéticas de custo, sem conversão para reais.

Isso cobre o bloco aplicado de fundamentos, a execução do bootstrap e a transferência para outro horizonte. Não equivale a cobrir toda a estatística ou comprovar estabilidade operacional futura. Referências: [fundamentos aplicados](Fundamentos_Aplicados_Resultados.md), [bootstrap](Bloco_2_Bootstrap.md) e [decisão e risco](Bloco_2_Decisao_Risco.md).

**M03 — ML clássico.** A base anterior já tinha persistência, Ridge/HGB, ajustes de parâmetros, cortes temporais, holdout e ablações. A retomada acrescentou seleção sistemática documentada, explicação local equivalente a SHAP por grupos e uma avaliação final com decisão previamente definida.

O contrato novo prevê `geração(origem+24h)` usando informação até `origem−2h`. O universo teve 33 atributos: 24 lags, cinco resumos e quatro coordenadas cíclicas de calendário. Foram fixados oito candidatos, comparados na mesma coorte: persistência, Ridge24 e seis combinações HGB por grupos. Três folds expansivos de junho tiveram 168 origens cada. O treino foi purgado pela disponibilidade do rótulo; o StandardScaler da Ridge foi ajustado somente no treino de cada fold.

| Candidato no desenvolvimento | Atributos | MAE — MWmed |
| --- | ---: | ---: |
| HGB — lags + calendário | 28 | 29,537623 |
| Ridge — 24 lags | 24 | 30,304103 |
| HGB — todos | 33 | 30,461331 |
| HGB — 24 lags | 24 | 30,721118 |
| HGB — lags + resumos | 29 | 30,737428 |
| HGB — 6 lags | 6 | 34,051992 |
| Persistência | 1 | 37,908555 |
| HGB — resumos | 5 | 39,329777 |

O HGB com 28 atributos foi escolhido por MAE de desenvolvimento e ajustado em 7.221 linhas, com última disponibilidade de rótulo em 30/06 às 23h. Em outubro, nas 695 origens reservadas daquela rodada, teve MAE 19,520624 e RMSE 24,989582. A persistência teve MAE melhor, 19,218456, e RMSE pior, 31,732297. O HGB reduziu erros grandes, mas perdeu 0,302168 MWmed em MAE; não foi retunado com esse teste.

A explicação local foi implementada por Shapley interventional exato em três grupos: seis lags recentes, 18 anteriores e calendário. Oito coalizões cobrem as combinações. Em seis origens de julho, foram comparados fundos de 16 e oito observações do treino. `base+contribuições` reproduziu a previsão com erro máximo de 7,11×10⁻¹⁵. Trocar o fundo alterou contribuições em até 19,782388 MWmed, mesmo sem inverter sinais nos 18 pares. Essa explicação é por grupos e depende do fundo; não é atribuição individual de cada lag nem causalidade física.

A avaliação final congelou 29 arquivos antes de obter setembro, comparou 14 variantes em 671 origens e exigiu ganho mínimo de 2 MWmed e limite inferior do IC de ganho positivo para o HGB candidato. Seu MAE foi 40,160344, contra 35,616479 da persistência. O ganho foi −4,543865, IC `[−10,208299;1,388840]`: os dois requisitos falharam. A decisão foi manter a persistência como referência de MAE e não promover o HGB.

Isso cobre seleção temporal sistemática por grupos, explicação local equivalente, defesa técnica e transferência retrospectiva. A seleção não foi busca exaustiva de todos os subconjuntos individuais nem seleção completa de atributos meteorológicos. A avaliação foi de snapshot retrospectivo; não comprova desempenho futuro ao vivo. Referências: [bloco 2](Relatorio_Engenharia_Bloco2.md), [bloco 3](Relatorio_Engenharia_Bloco3.md) e [model card](../model_card.md).

**M04 — Meteorologia, disponibilidade e horizontes.** A geração histórica e os alvos vêm do conjunto ONS Geração por Usina em Base Horária, campo `val_geracao`, em MWmed. A previsão de vento vem de NOAA GFS, acessado por Open-Meteo Single Runs: modelo `gfs_global`, velocidade e direção a 100 m, velocidade em m/s e relógio solicitado em UTC. Cadastro, capacidades e coordenadas usam ONS e SIGA/ANEEL. A geração prevista, os quantis e a probabilidade de queda são calculados pelos modelos Renewcast.

Foram rastreadas 126 rodadas meteorológicas, 124 usadas no estudo h24, com hashes das respostas coincidentes com os recibos. Os 15 pares de coordenadas representam cinco células de grade, e não 15 previsões meteorológicas independentes. Uma rodada normalizada tem 48 horas × 15 localizações = 720 linhas.

A capacidade total das 15 usinas é 227,7 MW. Ela fornece os pesos espaciais para velocidade média, dispersão, componentes médias u/v e média do cubo da velocidade. A direção meteorológica é convertida com `u=−velocidade×sen(direção)` e `v=−velocidade×cos(direção)`. O termo cúbico não é potência em MW. Os estudos meteorológicos usam cinco atributos de vento mais 27 históricos/calendário, totalizando 32. As redes MLP/GRU e o Chronos dos estudos históricos usam geração, sem essas cinco entradas GFS.

A correção E51 foi aplicada: `validate_wind_geometry` deixou de localizar campos por fragmentos de nome e ordem do dicionário e passou a exigir as chaves exatas de velocidade, u e v. Exige valores finitos, velocidade não negativa e `hypot(u,v)−velocidade<=1e−8`. O caso velocidade 12, u=30 e v=0 é rejeitado mesmo com chaves reordenadas. Componentes negativas legítimas são aceitas. Passaram 38 casos, incluindo integração com JSON real, sem retreinar o estimador.

O mecanismo cadastral bitemporal também foi construído: separa a vigência física do registro do instante em que aquela versão passou a ser conhecida. Seis testes conferem o contrato, e os 15 registros foram exportados. Versões futuras não podem alterar seleções históricas. O mecanismo exclui vigências não comprovadas; não cria evidência cadastral faltante.

Quatro itens continuam bloqueados: M04-02, fuso físico e começo/fim do intervalo ONS; M04-03, publicação histórica efetiva da meteorologia; M04-04, versões históricas sustentadas de cadastro/capacidade/coordenadas; M04-05, homologação point-in-time que reúne essas provas. O atraso de geração de duas horas e `available_at=inicialização GFS+6h` continuam hipóteses de estudo. Hash íntegro comprova preservação dos bytes comparados, não o horário em que o provedor publicou o dado.

A E51 foi coberta, a origem das previsões foi esclarecida e os mecanismos foram implementados. M04 permanece com um item validado e quatro bloqueados. Referências: [origem dos dados e previsões](Origem_Dados_e_Previsoes.md), [fontes e limites](Fontes_e_Limites.md) e [bloco 1](Relatorio_Engenharia_Bloco1.md).

**M05 — Incerteza, classificação, rampas e modelos adicionais.** Os trabalhos anteriores já tinham P10/P50/P90, pinball loss, cobertura, largura, classificação de queda e custos. A retomada separou três contratos: intervalo de geração, probabilidade de classe e rampa horária. Também executou as famílias LightGBM/CatBoost e um modelo global próprio.

O treino terminou antes de julho. Foram separadas 312 origens para calibração, 360 para selecionar a política e 695 de outubro para avaliação. O calibrador e a política foram congelados antes da obtenção do snapshot de outubro; não foram refeitos para melhorar seus resultados.

Três HGB quantílicos geraram P10/P50/P90, ordenados por linha. O CQR calculou expansão de 15,123976 MWmed por lado. A cobertura na calibração passou de 70,19% para 80,45%. O comportamento no teste foi:

| Intervalo em outubro | Cobertura | Largura média — MWmed | Interval score |
| --- | ---: | ---: | ---: |
| P10–P90 ordenado | 97,6978% | 72,920623 | 76,989183 |
| Com CQR congelado | 98,7050% | 103,168575 | 104,578288 |

A meta nominal era 80%, com alerta fora de 70%–90%. Ambos acionaram alerta agregado e nas quatro semanas completas. O CQR ficou excessivamente largo e piorou o score naquele mês. Cobertura maior não significa intervalo melhor quando o custo da largura aumenta.

Para a classe antiga de queda, o evento é `geração(origem−2h)−geração(origem+24h)>=22,77 MWmed`: suas extremidades estão separadas por 26 horas. Foi ajustado HGBClassifier, com calibração Platt em período separado e baseline de frequência fixa do treino.

| Probabilidade em outubro, 117 positivos/695 | Brier | Log loss | AP |
| --- | ---: | ---: | ---: |
| Frequência fixa | 0,140752 | 0,455717 | 0,168345 |
| HGB bruto | 0,085677 | 0,250749 | 0,687644 |
| HGB + Platt | 0,083296 | 0,243630 | 0,687644 |

Platt melhorou Brier/log loss no agregado, preservando o ranking e a AP, mas não melhorou todas as semanas. A política escolhida no desenvolvimento usou corte 0,3 e no máximo seis alarmes por dia. O runtime aceita os primeiros seis elegíveis em ordem temporal; não escolhe retrospectivamente os maiores escores do dia. Em outubro produziu 126 alarmes, 48 TP, 78 FP e 69 FN, custo hipotético `FP+4FN=354`, contra 468 sem alarme. Precisão 38,10% e recall 41,03%. O comparador de corte 0,5 teve custo menor no teste, sem substituir a escolha congelada.

A lacuna de rampa horária recebeu outro alvo: `geração(origem)−geração(origem+1h)`. Com atraso assumido de duas horas, o rótulo chega em origem+3h. O treino específico teve 7.244 linhas. Em outubro o regressor teve MAE 6,974245, contra 7,572565 da rampa zero e 12,829047 da última rampa observada. Houve 39 eventos horários, distintos dos 117 eventos de 26h. O classificador horário teve AP 0,328758 e Brier 0,043731, mas no corte 0,5 **não emitiu alarmes e perdeu os 39 eventos**. A implementação e o ranking foram avaliados; uma política útil nesse corte não foi demonstrada.

LightGBM 4.6.0 e CatBoost 1.2.8 foram instalados isoladamente, preservando o Conda original. Duas configurações por família, 60/120 árvores, foram comparadas em três folds de junho com os 28 atributos comuns. O desenvolvimento escolheu 120 árvores em ambas. Em outubro exploratório, LightGBM teve MAE 18,058893 e CatBoost 18,421708, contra 19,218456 da persistência. Na avaliação final de setembro, seus MAEs foram 39,935226 e 40,853216, contra 35,616479 da persistência: a vantagem observada em outubro não se sustentou naquele outro mês.

O modelo global usou quatro séries eólicas reais, CEECVA, CEEMAU, CEUCZ e CEUFM, escolhidas por regra de identificação/cobertura sem selecionar por desempenho. O problema foi h+1, com informação até origem−2h. Foram 1.332 linhas de treino, 576 de validação e 956 de teste, 239 por série. O MAE agregado foi 5,980751 no global, 6,176272 nos locais e 8,063423 na persistência. O global venceu a persistência em duas séries e perdeu nas outras duas; venceu três dos quatro modelos locais no teste, mas foi pior que os locais no agregado de validação. O estudo é retrospectivo em quatro séries conhecidas; não avaliou uma quinta série inédita nem pode ter seus MAEs h+1 comparados diretamente aos h+24 da série principal.

Em setembro, os intervalos também mudaram: cobertura/largura de 56,04%/104,964631 no HGB bruto, 76,15%/135,212583 no CQR e 67,51%/80,770920 no Chronos. O CQR melhorou a cobertura, porém excedeu o limite de largura de 100. No classificador de 26h, o Brier calibrado foi 0,256556, melhor que o bruto 0,295863 e pior que a frequência constante 0,202469. A política em 0,3 teve 160 alarmes, 62 TP, 98 FP e 119 FN: custo 574, contra 724 sem alarme. O teto diário foi respeitado, mas a probabilidade não mostrou calibração estável entre regimes.

Os cinco itens M05 foram cobertos em engenharia. A estabilidade prospectiva de intervalos e probabilidades continua explicitamente preservada como M06-05/C3 e C4, com sua origem em M05. Referências: [bloco 2](Relatorio_Engenharia_Bloco2.md), [bloco 3](Relatorio_Engenharia_Bloco3.md) e [modelo global e dados](Bloco_3_Dados.md).

**M06 — Engenharia, MLOps e operação.** A base já aceita incluía API com inferência do classificador, execução em lote, Docker local, telemetria HTTP, registro local, rollback e cliente Windows .exe 1.1. Esses aceites foram preservados. O serviço HTTP novo deste bloco carrega um HGB regressor de 28 atributos pelo MLflow; ele não deve ser confundido com a API histórica do classificador.

Oito arquivos das versões v1/v2 do registro local foram encontrados e tiveram seus hashes conferidos por leitura autorizada fora da restrição. O problema observado era de acesso naquele contexto, não perda dos arquivos; não houve restauração.

Foi executado Model Registry real em MLflow 3.16, com modelo registrado, assinatura, identidades, versões 1/2 e alias `active` passando por 1→2→1. As recargas reproduziram as 48 previsões com diferença máxima zero. As duas versões usam o mesmo artefato HGB congelado: demonstram registro, resolução e rollback de pacote, sem alegar novo modelo melhor. A falha inicial de compatibilidade skops foi preservada; o reparo autorizou somente o tipo interno necessário ao bundle de hash conferido.

O serviço abriu socket real em 127.0.0.1 com chave efêmera em memória, limite de 8.192 bytes incluindo corpo chunked, validação dos 28 atributos e rate limit. Oito contraprovas HTTP passaram, incluindo 401, 413, 422 e 429. O token não apareceu nos logs, e o processo foi encerrado ao final.

| Concorrência local | Requisições | p95 | Vazão | Erros | Pico RSS |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 240 | 18,18 ms | 70,89/s | 0 | 430,76 MiB |
| 4 | 240 | 79,37 ms | 61,93/s | 0 | 431,68 MiB |

Foram atendidos p95<=500 ms, erros<=1% e RSS<=2.048 MiB. A concorrência maior piorou latência e vazão nesse desenho. CPU e memória incluem runner, cliente, servidor e bibliotecas no mesmo processo. Os campos antigos rotulados MB usam divisão por 1024²; a unidade efetiva é MiB. Poucos segundos de carga não demonstram capacidade sustentada ou custo de produção.

O ledger registra origem, chegada, vintage, alvo, hash, modelo e rastreamento. Foram exercitadas 48 emissões e 48 reconciliações em replay, com rejeição de entradas futuras, vintages posteriores, duplicação e conciliação antecipada. O modo live sem contrato point-in-time é bloqueado. Foram demonstradas **zero horas de shadow ao vivo**.

O detector de drift distinguiu alteração da entrada, degradação de erro, falta de dados e atraso de rótulos em contraprovas controladas. Deslocamento de três desvios, aumento artificial de MAE, missing de 20% e atraso de 12h acionaram as categorias correspondentes. Não há retreino/promoção automática. A deduplicação operacional diária e a estabilidade da triagem ao vivo não foram demonstradas.

A pendência de CI remoto foi coberta com dois runs reais no GitHub Actions:

- [Falha controlada 45889419488](https://github.com/marhlon/renewable-forecast-lab/actions/runs/45889419488): o contrato temporal rejeitou lag2=29 quando deveria ser 28.
- [Correção 45889590759](https://github.com/marhlon/renewable-forecast-lab/actions/runs/45889590759): contrato normal, contraprova preservada e 16 testes aprovados em 2,50 s de pytest.

O ambiente remoto usou Ubuntu 26.04, Python 3.12.16 e PyTorch 2.7.1+cpu. A correção alterou somente a configuração do controle negativo. A branch `codex/bloco3-ci-20261126` permaneceu separada, sem merge, PR ou deploy. O workflow verifica os contratos selecionados; não executa o verificador documental completo do roadmap nem ativa proteção da main. Os mesmos 16 casos foram usados localmente, na cópia isolada e no Actions: repetição de ambiente não cria 48 casos independentes.

M06-01/02/03 estão validados. M06-04/05/06/07/08/09 continuam bloqueados, com aceite parcial local de drift, segurança e capacidade. Falta homologar o ambiente alvo, designar responsáveis e resposta a incidentes, operar a janela real e medir continuidade/custos. Há plano não executado de sete dias com mínimo de 144 emissões e posterior conciliação dos alvos. Segurança e capacidade continuam pré-condições do shadow. O plano cloud foi elaborado, mas não houve provisionamento ou implantação. Conta, região, orçamento e autorização ainda são necessários.

Referências: [operação local](Bloco_3_Operacao_Local.md), [revisão do CI remoto](Revisao_CI_Remoto_Bloco3.md) e [bloco 3](Relatorio_Engenharia_Bloco3.md). Os recibos anteriores à execução remota preservam o estado daquela fase; o estado atual de M06-02 está concluído.

**M07 — Dados em escala.** Os trabalhos anteriores já tinham PySpark, Spark SQL, Delta Lake, notebook Databricks e reprodução de duas configurações de particionamento. A reprodução comparou 8.760 registros de geração e 7.485 linhas elegíveis: houve zero divergência com duas e quatro partições solicitadas. Os tempos registrados de transformação/comparação foram 3,6916 s e 2,9938 s, em ordem fixa e sem isolamento causal dos fatores de desempenho.

A análise foi corrigida para separar resultado observado de hipótese sobre o motor: a alteração M07.2 era simulada; às 03h, com atraso de 2h e janela de 6h, entram as medições de 20h do dia anterior à 01h; o cronômetro terminava antes do explain; o Exchange 10 preparava o lado broadcast do JOIN; o plano inicial não provava coalescência AQE. Aquecimento/cache permaneceram hipóteses, sem atribuir o resultado a Java/Photon compilado por JIT.

A lacuna de medallion recebeu bronze, silver e gold locais. A bronze conserva o bruto e sua identidade; a silver aplica esquema/chaves/tempo/finitude/qualidade; a gold produz dados para os consumidores com junção exata por série e timestamp. O Parquet ONS de outubro tinha 537.384 registros. Foram aceitos 389.304 na silver e colocados 148.080 em quarentena: 87.048 sem identificador e 61.032 sem geração finita. A gold das quatro séries tem 2.976 linhas. A segunda construção reproduziu os hashes físicos e lógicos. A proteção de aplicação e os hashes não são armazenamento WORM.

O pipeline incremental exerceu quatro commits, replay sem efeito, conflito de payload, atraso e falha entre estágio e commit. A recuperação produziu a mesma gold da referência que usa as mesmas chegadas hipotéticas. O atraso de sete dias foi contraprova sintética separada: o backfill não fez o evento aparecer como conhecido antes de sua disponibilidade. A implementação usa um escritor local e troca de ponteiro; não comprova concorrência distribuída, fsync/power-loss, broker ou pipeline contínuo em cluster.

Foram realizadas 18 medições reais, dois motores × três coortes × três repetições em processos separados. Ambos leram a mesma silver física e filtraram volumes elegíveis diferentes. O tempo incluiu leitura, filtro, janela/agregação e materialização; startup e EXPLAIN ficaram fora.

| Linhas elegíveis | Mediana pandas | Mediana DuckDB |
| ---: | ---: | ---: |
| 149.568 | 0,247 s | 0,326 s |
| 266.664 | 0,397 s | 0,250 s |
| 389.304 | 0,215 s | 0,223 s |

Os nove pares tiveram as mesmas chaves/contagens e diferença numérica máxima de 3,18×10⁻¹². Os picos RSS amostrados ficaram abaixo de 512 MiB. Não houve crescimento monotônico de tempo nem vencedor consistente entre os motores; cache e host compartilhado limitam a leitura de tempos tão curtos. O plano novo é DuckDB local, não Spark/AQE.

Medallion, incremento multissérie e medição local real foram cobertos. Escala distribuída de produção continua fora da demonstração. Referências: [dados e modelo global](Bloco_3_Dados.md), [bloco 1](Relatorio_Engenharia_Bloco1.md) e [bloco 3](Relatorio_Engenharia_Bloco3.md).

**M08 — Autograd, MLP e GRU.** As três unidades já haviam sido executadas: gradiente NumPy/autograd/diferenças finitas, Dataset/DataLoader/MLP e GRU com célula NumPy conferida. A retomada localizou os brutos Windows, conferiu sua integridade e acrescentou reanálise e adaptação de contrato.

No autograd, o modelo afim usa `X[n,2]`, `w[2,1]` e previsão/alvo `[n,1]`. Um alvo `[n]` geraria broadcasting para `[n,n]`, mudando a perda. A derivada implementada foi `dw=(2/n)X.T@r` e `db=(2/n)sum(r)`. Com taxa 0,05, a MSE padronizada caiu de 1 para 0,634610 após 400 passos, perto do mínimo de mínimos quadrados. Com taxa 0,8, chegou a aproximadamente 1,78×10¹⁶ em 30 passos. A convergência do primeiro ajuste coexistiu com viés observado−previsto de +22,459944 MWmed na validação: otimizar a perda não garante boa generalização.

Na MLP, a divisão temporal antecedeu o embaralhamento dos exemplos de treino. A média e o desvio foram ajustados somente no treino, e o checkpoint foi escolhido em uma semana separada da avaliação. O avaliador soma perdas por exemplo e divide pela quantidade total, preservando o peso de lotes menores, além de restaurar os modos do modelo e preservar pesos/gradientes.

Nas 168 origens históricas, persistência teve MAE 37,991646; linear24, 33,678664; MLP17/29/41, 32,724828/33,700811/33,159788. A MLP não venceu o linear em todas as sementes. O HGB local teve MAE 32,323956 e RMSE 44,221683; as GRUs ficaram em:

| GRU histórica | MAE | RMSE |
| --- | ---: | ---: |
| Semente 17 | 35,675970 | 45,200733 |
| Semente 29 | 34,911227 | 43,816199 |
| Semente 41 | 34,573202 | 43,066020 |

As sementes 29/41 melhoraram RMSE frente ao HGB, porém nenhuma melhorou MAE. A reanálise preservou todas as sementes e mostrou a contribuição de erros grandes para essa discordância. Essa é a defesa técnica fornecida para GRU versus HGB naquele recorte, sem selecionar depois a melhor semente pelo teste.

A nova adaptação usou janela 12, hidden size 8, 273 parâmetros e 11 exemplos em lotes 4/4/3. Entrada `[B,12,1]`, saída recorrente `[B,12,8]`, estado `[1,B,8]` e previsão `[B,1]` foram escritos no protocolo antes da execução. A MSE correta foi 5,603784; a média simples das três perdas de lote daria 6,324716. Foram verificados modos mistos, pesos, gradientes, entradas, RNG, falhas e reinício do estado entre janelas. A célula NumPy coincidiu com PyTorch em até 2,22×10⁻¹⁶. Os pesos dessa adaptação são aleatórios: é demonstração de contrato e estabilidade do avaliador, não novo resultado de previsão.

A auditoria dos brutos M08.1/M08.2 confirmou as saídas históricas e registrou uma divergência do arquivo de gradiente atual em relação ao hash executado no passado. Isso encerra a lacuna de inspeção dos arquivos encontrados, preservando a diferença entre integridade histórica e reprodução com a árvore atual. Não houve repetição dos treinos antigos nesta auditoria.

Referências: [autograd](../../reports/parecer_m08_autograd.md), [MLP](../../reports/parecer_m08_mlp.md), [transferência neural](Bloco_3_Transferencia_Neural.md) e `reports/fechamento_m00_m09/M08-01/auditoria_brutos.json`.

**M09 — Atenção, Transformer e previsão com pesos pré-treinados.** Já existiam atenção NumPy, composição encoder–decoder e Chronos executado no Windows. A retomada auditou os artefatos M09.2 presentes no disco, aplicou a arquitetura a outro contrato de disponibilidade e produziu a comparação final integrada.

Os blocos abrangem Q/K/V, produto escalonado, softmax por chave, múltiplas cabeças, posição, residuais, LayerNorm e feed-forward. Na self-attention, Q/K/V vêm da mesma representação; na cross-attention, Q vem do decoder e K/V da memória do encoder. A auditoria confirmou a preservação das saídas antigas e identificou dois scripts atuais diferentes dos hashes dos runs, repetidos em quatro declarações de discrepância. Os arquivos atuais e a versão histórica não foram tratados como intercambiáveis.

O contrato novo usou contexto 12, cinco consultas, duas origens no batch, dimensão de representação 12 e três cabeças de dimensão 4. Os scores por cabeça são `Q@K.T/sqrt(4)`, com probabilidades nos shapes `[2,3,12,12]`, `[2,3,5,5]` e `[2,3,5,12]`. Foram reconstruídas numericamente projeções, máscaras, normalização, produto por V, concatenação, residuais, normas e FFN. As consultas são slots sintéticos, não cinco previsões horárias treinadas.

A contraprova mostrou vazamento indireto: mascarar somente a cross-attention deixou a primeira saída mudar 0,590814 quando o encoder livre já havia incorporado uma fonte posterior ao prefixo permitido. Restringir encoder e cross-attention resultou em diferença zero. No decoder, a máscara causal preservou o prefixo; o controle livre mudou 1,222385. Isso explica por que consultar todo um histórico já disponível na origem é diferente de reconstruir decisões de prefixos anteriores.

O Chronos-Bolt Tiny reutilizou pesos locais de revisão e hashes identificados, sem fine-tuning. Com contexto de 24 medições até origem−2h e alvo em origem+24h, precisa prever 26 passos após o fim da janela; o alvo é o índice 25. Os quantis foram associados aos alvos pelos timestamps. A possível sobreposição com dados de pré-treino continua desconhecida; a identidade do arquivo de pesos não prova ausência de contaminação.

Na execução histórica das 168 origens conhecidas, o Chronos P50 teve MAE 31,340738, RMSE 45,380136 e viés observado−previsto de +2,962412 MWmed. O intervalo P10–P90 cobriu 80,36% dos alvos, com largura média de 83,595237 MWmed. Os pesos têm 8.652.672 parâmetros. O recibo registra 0,1653 s de carga, 0,0250 s de aquecimento e 0,1873 s de inferência, com lotes de 16 e dois threads CPU. O pico de 434,23 MiB é do processo inteiro, incluindo bibliotecas, e não RAM isolada do modelo. Esses valores descrevem aquela execução; não são uma previsão de custo de produção.

Na comparação final, setembro foi obtido depois de congelar os 29 arquivos. Das 720 horas da série principal, restaram 671 origens comuns, após reservar histórico e alvos. Foram preservadas 9.394 previsões, 14 variantes × 671 origens. O Chronos executou offline em CPU e dois threads: carga de 0,2459 s, aquecimento de 0,0668 s e inferência de 0,8887 s para as 671 origens. Os tempos separam essas fases e não incluem download; ambientes distintos impedem usá-los como ranking estrito de eficiência entre famílias. Os modelos mantiveram seus próprios cortes/atributos declarados; mesmas origens não significa treinamento idêntico. O estudo é retrospectivo em snapshot recém-obtido, não shadow prospectivo.

Viés na tabela a seguir é **observado−previsto**: positivo indica subestimação média. Unidade de MAE/RMSE/viés: MWmed.

| Variante | MAE | RMSE | Viés |
| --- | ---: | ---: | ---: |
| Persistência | 35,616479 | 50,351806 | −0,118539 |
| Chronos P50 | 35,689509 | 47,649804 | +3,594809 |
| MLP 17 | 35,798434 | 46,331283 | +13,530202 |
| MLP 29 | 36,071127 | 46,324847 | +16,434027 |
| MLP 41 | 36,078965 | 46,057445 | +16,998245 |
| GRU 41 | 36,550595 | 45,015515 | +20,323878 |
| Linear antigo | 36,773465 | 46,863352 | +19,237325 |
| GRU 17 | 37,262908 | 46,370827 | +23,423832 |
| GRU 29 | 38,939038 | 47,425211 | +25,320816 |
| LightGBM | 39,935226 | 48,006647 | +23,808183 |
| HGB escolhido no bloco 2 | 40,160344 | 48,084892 | +27,001884 |
| CatBoost | 40,853216 | 48,483520 | +26,829121 |
| HGB quantílico P50 | 42,338754 | 51,419292 | +29,446851 |
| HGB antigo | 42,971842 | 52,854430 | +25,951265 |

A persistência teve o menor MAE; GRU41 teve o menor RMSE entre as variantes, com subestimação média relevante. O Chronos ficou próximo da persistência em MAE e reduziu RMSE, mas o ganho de MAE foi −0,073030, IC condicional `[−3,151100;2,969704]`. Os ICs finais usaram blocos circulares pareados de 24h, 2.000 réplicas e semente 31, definidos antes da obtenção do snapshot.

O critério primário foi mantido: o HGB candidato falhou, e não houve promoção automática. A análise integrou MAE/RMSE, viés, intervalos, probabilidades, custo e limites de execução. Com custo hipotético de subestimar quatro vezes maior, Chronos P80 teve perda 70,466801, contra 88,863390 da persistência; com custo simétrico, a persistência foi a menor perda. Uma escolha de negócio diferente exige protocolo próprio e outra confirmação, preservando esse teste como já examinado.

A execução final original retornou 1 por impressão CP1252 depois de salvar as previsões. O log e o recibo da falha foram preservados. A recuperação executou somente a síntese em UTF-8, com retorno 0, sem repetir inferência, ajuste ou seleção. Essa distinção preserva o histórico real de execução.

Referências: [transferência neural](Bloco_3_Transferencia_Neural.md), [avaliação final](Relatorio_Engenharia_Bloco3.md), `reports/fechamento_m00_m09/M09-01/auditoria_transformer.json` e `reports/fechamento_m00_m09/bloco3_engenharia/M09-04`.

**Condições que permanecem para operação.** Os dez itens bloqueados são M04-02/03/04/05 e M06-04/05/06/07/08/09. Exigem comprovação externa de fuso/intervalo, publicação e cadastro; ambiente alvo homologado em segurança/capacidade/custo; responsáveis e janela real de shadow; observação contínua de erro, cobertura, probabilidades, alarmes e drift; e implantação cloud delimitada quando autorizada. Abrir Docker não fornece essas comprovações. Nenhuma delas foi substituída por uma solução teórica ou por um replay.

**Como o trabalho ficou incorporado ao projeto.** O cadastro `config/roadmap_m00_m09.json` conserva IDs, dependências, critérios anteriores, evidências e revisões. Os snapshots registram o estado antes de cada migração. Protocolos, CSVs, hashes e recibos permanecem nas pastas dos três blocos em `reports/fechamento_m00_m09/`. O README apresenta a situação atual; AGENTS.md exige a conferência do escopo nas próximas mudanças. O .gitignore diferencia código/documentação/evidência leve de ambientes, brutos, modelos e bancos locais, sem apagar históricos.

Integridade pergunta se o artefato foi preservado; compatibilidade, se atende ao contrato; atualidade, se a previsão serve à decisão corrente. A auditoria separa essas três perguntas. Também preserva experimentos negativos, configurações que falharam e diferenças de versão, em vez de reclassificá-los como sucessos.

Para conferir o cadastro e as entregas existentes, sem repetir treinamentos:

```powershell
python scripts/verificar_roadmap.py
python scripts/verificar_roadmap.py --bloco 1 --gate engenharia
python scripts/verificar_roadmap.py --bloco 2 --gate engenharia
python scripts/verificar_roadmap.py --bloco 3 --gate engenharia
python scripts/conferir_bloco3.py
```

O fechamento irrestrito e o portão operacional continuam apontando as pendências. Esta consolidação foi elaborada com assistência técnica de Codex a pedido de Marlon A. Bomfim, a partir dos registros locais. Não altera os aceites, não constitui outro run e não promove modelos ou serviços.
