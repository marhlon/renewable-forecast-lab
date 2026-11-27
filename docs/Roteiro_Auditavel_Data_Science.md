# Do ferro ao pró — roteiro auditável de aprendizagem

Marlon Alves Bomfim · versão didática 1.66 · 17 de novembro de 2026 (America/Sao_Paulo)

> **Retomada local de 24/11/2026:** este arquivo conserva a versão 1.66 e seu histórico; o painel abaixo não incorpora todas as entregas posteriores. Para o fechamento M00–M09, consultar o [roadmap reconciliado](ROADMAP_M00_M09.md) e o [cadastro de pendências](../config/roadmap_m00_m09.json). Há evidências locais M10.1–M10.4 e M11.1–M11.2 posteriores a este painel. A retomada não altera retroativamente aceites, não certifica autonomia e não equivale a uma nova versão didática emitida pelo professor.

**Objetivo:** desenvolver autonomia para formular problemas de Ciência de Dados, construir soluções, avaliar evidências, explicar escolhas e manter entregas utilizáveis. A trilha terá ferramentas, fundamentos e provas práticas. Concluir a trilha fornece evidências de competência; o nível de cargo também depende da atuação profissional.

Este documento mantém o estado atual do produto, as evidências de aprendizagem e o histórico das sessões. O painel da formação e o checkpoint no início são a referência para decidir a próxima ação. O inventário de entregas do P1 é secundário e não mede a conclusão da formação. As notas históricas conservam o estado da data em que foram escritas; uma pendência antiga pode ter sido resolvida em evidência posterior. A versão didática é independente da tag de software `v0.2.0`.

**Como usar:** começar pelo painel da formação e pelo checkpoint atuais abaixo; consultar a matriz M00–M14 e a unidade ativa; depois localizar a evidência pelo ID. Os identificadores permanecem estáveis. Conteúdo demonstrado é reconhecido; não repetir preparação do ambiente ou entregas já aceitas.

**Painel principal — formação completa, atualizado em 17/11/2026**

A formação contém **14 marcos, M01–M14, mais o preparatório M00**. O primeiro produto, Renewcast/P1, tem um inventário próprio de dez entregas técnicas. Esses denominadores têm significados diferentes: uma entrega do produto não equivale a um marco de formação, e vários itens do P1 pertencem ao mesmo marco.

**Estado da formação:** M01–M06 têm trabalho aplicado registrado. E103 aceita M07.1; E105/E106 encerram a entrega técnica M07.2. E108 aceita M07.3 pela exportação Databricks: 8.760 registros de origem, 7.485 linhas de treino, duas configurações sem divergências e tabelas Delta identificadas. O parecer autoral sustenta manter o recorte local; leitura do plano e causalidade receberam revisão orientada. M07 encerra o escopo dessas três unidades, sem certificação de escala ou produção. Não repetir Spark/Delta/Databricks. E110 aceita M08.1: função NumPy e parecer recebidos com autoria assistida explicitamente declarada; gradiente conferido nesta revisão e resultados Windows relatados coerentes com a referência. Arquivos brutos dessas execuções Windows não foram recebidos. E112 aceita a função de avaliação e o parecer M08.2 recebidos em texto, com assistência declarada e relato Windows de 05/11. A função foi executada nesta revisão; arquivos Windows não anexados. E114 aceita a execução Windows M08.3, a célula NumPy e os cinco testes recebidos. Nove anexos auditados, oito hashes e 27 métricas reconciliados; código confrontado com PyTorch. A defesa da decisão pelo aluno ainda pode ser consolidada na próxima unidade, sem repetir treino. E116 aceita o código de atenção recebido, seis casos e comparação PyTorch executados nesta revisão, além dos logs Windows do modo normal. E117 reconhece a composição Transformer M09.2 relatada em Windows, com runner/verificador recebidos e revisados; o módulo dos blocos e os artefatos completos não foram anexados. E118 entrega M09.3 executável: Chronos-Bolt Tiny com revisão fixa e previsões nas mesmas168 origens; controlador/ambiente privado executados em Linux. E119 aceita a execução Windows M09.3 normal, onze hashes, trinta métricas e alinhamento autoral executado nesta revisão. Os recibos auxiliares de uma segunda rodada permanecem distintos; parecer próprio não anexado. E120 inicia M10.1 com pacote real ESA e laboratório completo executado em Linux: execução do aluno pendente. M11–M14 posteriores. Não há percentual global validado.

**Correção do indicador:** os “70%” anteriormente destacados eram somente 7/10 itens do inventário do primeiro produto, contados com pesos iguais e escopos exploratórios. Apresentá-los como andamento geral da formação foi inadequado. Esse valor sai do painel principal. Os marcos pendentes continuam pendentes; nenhuma alteração documental os torna aprendidos ou entregues.

| Marco da formação | Evidência atual | Estado e trabalho restante |
| --- | --- | --- |
| M00 — Preparação e diagnóstico | Ambiente, fluxo e contratos temporais usados | Parcial; transferência independente do diagnóstico ainda a avaliar |
| M01 — Dados e engenharia | Série ONS, pandas/NumPy, Parquet, contratos e SQL autoral em E71/E72 | JOIN, GROUP BY, CASE, NULLIF e nulos demonstrados no registro. E82/E83: tentativa com LAG revisada e saída corrigida reconciliada; explicação e transferência independentes ainda pendentes |
| M02 — Estatística e experimentação | Métricas, resíduos, comparação e interpretação de incerteza | Abordado; álgebra/otimização da regressão, diagnóstico de dependência e transferência ainda sem fechamento integral |
| M03 — ML clássico e avaliação temporal | Baselines, HGB, tuning, cortes, calibração, holdout e ablações | Abordado com entregas técnicas demonstradas; defesa independente e consolidação das provas ainda pendentes |
| M04 — Meteorologia e horizontes | HTTP/cache, seleção as-of, pesos espaciais, h6/h24 e inferência por artefato | Abordado com entregas técnicas demonstradas; correção autoral E51 e verificação operacional dos contratos temporais pendentes |
| M05 — Incerteza e eventos | Quantis, calibração, classificação, custos e seleção autoral | Núcleo técnico concluído no desenvolvimento; consolidação de aprendizagem e transferência ainda a avaliar |
| M06 — Entrega e MLOps | E71–E93: inferência, lote, monitor, registro, distribuição, concorrência e cliente; E94: oito anexos do cliente 1.1 auditados | M06.5 encerrado no protocolo local: sete hashes e 32 conferências aprovadas. CI remoto, shadow ao vivo, monitoramento contínuo e Registry MLflow permanecem entregas separadas |
| M07 — Dados em escala | E103/E106: temporal/Delta aceitos; E108: notebook Databricks com saídas e parecer recebidos | Unidades M07.1–M07.3 encerradas no escopo demonstrado. Decisão local/cloud aceita; plano e medição receberam revisão orientada. Escala real e operação não demonstradas |
| M08 — Deep learning temporal | E110/E112/E114: autograd, MLP e GRU executados e implementações recebidas aceitas; assistência anterior declarada | Entregas técnicas M08.1–M08.3 aceitas. Defesa M08.3 e transferência/retomada independentes ainda a consolidar; não repetir treino ou código aceito |
| M09 — Transformers | E116/E117: atenção e composição; E119: previsão pré-treinada Windows, resultados e função de alinhamento conferidos | M09.3 técnica aceita no escopo recebido. Defesa integrada própria ainda não anexada; não repetir inferência para avançar |
| M10 — Telemetria e anomalias | E120: recorte ESA Mission1, canais50–52, contrato temporal e eventos; referência Linux executada | M10.1 ativa: sincronização causal com idade máxima e auditoria de anotações. Execução/autoria do aluno pendentes; M10.2–M10.4 posteriores |
| M11 — LLMs e IA generativa | Planejamento do P3 | Não iniciado na prática: tokenização, geração estruturada, avaliação e adaptação delimitada |
| M12 — RAG | Planejamento do P3 | Não iniciado na prática: recuperação, embeddings, índice e respostas com evidências |
| M13 — Agentes e LLMOps | Planejamento do P3 | Não iniciado na prática: ferramentas tipadas, estado, limites e avaliação |
| M14 — Defesa e pesquisa | Ablações e decisões anteriores como preparação | Não iniciado como entrega final: reprodução delimitada, defesa e portfólio dos três produtos |

“Não iniciado nesta trilha” descreve a ausência de entrega registrada aqui; não é uma afirmação sobre todo o conhecimento prévio do aluno. “Abordado” reconhece prática, mas não equivale a concluir todas as unidades nem a comprovar autonomia. Cabe ao professor planejar e registrar as provas faltantes sem apagar as entregas já aceitas ou bloquear indefinidamente a progressão.

**Inventário secundário — entregas técnicas do P1/Renewcast**

**8 de 10 itens encerrados no critério declarado; item 8 em andamento e item 10 com execução aceita, aguardando a defesa prevista para o fechamento.** É uma contagem de artefatos/experimentos do primeiro produto, sem estimativa de esforço ou prazo e sem equivalência a conclusão do curso. E71 confirma lote SQLite, idempotência e conciliação pelo aluno; E72 reconhece SQL autoral, regra de dados e falha simulada. E74 confirma a reprodução do monitor nos quatro cenários. E80 encerra a reprodução do diagnóstico HTTP corrigido. E83 aceita a reprodução do registro local, ativação, rollback e saída SQL corrigida do aluno, após o desbloqueio de E82. O parecer independente segue pendente. Shadow ao vivo e monitoramento contínuo continuam pendentes. E51 e as hipóteses de tempo/disponibilidade/cadastro permanecem registradas.

| Entrega técnica do P1 | Estado atual | Evidência e limite |
| --- | --- | --- |
| 1. Série de geração e qualidade do recorte | Concluída no recorte | E03: 8.760 horas; E39 confirma seu uso na junção recebida |
| 2. Baseline, treino e previsão h+1 | Concluída; execução histórica registrada | E04/E07; não implica superioridade estatística ou serviço em produção |
| 3. Desenvolvimento h+6, validação, tuning e calibração | Concluída no protocolo executado | E16–E23: disponibilidade, cortes, busca, diagnóstico e calibração causal |
| 4. Avaliação reservada e emissão h+6 sem alvo | Concluída no escopo local | E24/E25: MAE 25,325 MWmed no período reservado, previsão e registro reconciliados |
| 5. Meteorologia real e experimento integrado | Concluída no escopo exploratório | E27–E41: fluxo real reproduzido, 31 dias integrados, três semanas de validação e comparação pareada auditada. E42 quantifica incerteza condicional. Fuso, intervalo, latências e cadastro histórico permanecem hipóteses; validação operacional continua pendente |
| 6. h+24 e comparação de horizontes | Concluída no escopo exploratório e replay local | E46–E50: comparação, artefato e inferência sem alvo reproduzidos pelo aluno. E51 exige correção localizada da validação de vento; não desfaz a entrega técnica aceita. Superioridade operacional sobre persistência continua não estabelecida |
| 7. Quantis e previsão de eventos | Concluída no escopo exploratório | E53–E62: quantis, calibração e eventos reproduzidos. E63: seleção autoral sob capacidade implementada corretamente. Validação operacional segue separada |
| 8. Serviço/lote, shadow e monitoramento | Em andamento | E69/E71: inferência e lote; E72: SQL; E74/E76: monitor/parecer; E80: diagnóstico HTTP; E83: registro/rollback e SQL corrigido; E85/E87: empacotamento e Docker. E89: lógica de escolha aceita com dados do console, sem recálculo de P95 a partir de requests.csv. CI remoto, shadow ao vivo e telemetria contínua ainda não demonstrados |
| 9. Utilitário Windows distribuível | Concluída a versão 1.1 no protocolo local | E94: cinco cenários com saídas 0/7/2/4/3, cópia externa sem Conda/PYTHONPATH, paridade de probabilidade zero; oito anexos auditados, sete hashes coincidentes. Escopo: mesmo PC, API Docker; não aprovação operacional |
| 10. Comparação neural/fundacional | Execução e implementação aceitas; fechamento documental parcial | E119: comparação Windows e função de alinhamento aceitas. Parecer/decisão própria exigidos para o encerramento ainda não anexados. Não repetir a execução técnica |

**Correspondência entre o inventário do P1 e os marcos da formação**

| Item técnico do P1 | Marcos diretamente envolvidos |
| --- | --- |
| 1. Série e qualidade | M01 |
| 2. Baseline, treino e previsão h+1 | M02/M03 |
| 3. Desenvolvimento h+6, tuning e calibração | M02/M03 |
| 4. Avaliação reservada e emissão h+6 | M03 |
| 5. Meteorologia e experimento integrado | M02/M03/M04 |
| 6. h+24 e comparação de horizontes | M03/M04 |
| 7. Quantis e eventos | M05, apoiado em M02/M03 |
| 8. Serviço, shadow e monitoramento | Parte de M06 |
| 9. Utilitário Windows | Outra parte de M06 |
| 10. Comparação neural/fundacional | Partes de M08/M09 |

As sete primeiras entregas se concentram em M01–M05. M06 já avançou dentro do item 8, ainda aberto; E91 aceita a versão 1.0 do utilitário Windows no item 9 com base nos logs fornecidos, elevando o inventário a oito entregas técnicas. E92 aceita a regra temporal autoral; E93 integra essa regra na versão 1.1 e E94 aceita sua reprodução Windows após auditoria dos anexos. E95 iniciou a entrega M07.1; E96 registra tentativa e autoria recebidas, e E97 entrega correção orientada. A falha de infraestrutura e sua correção não contam como unidade concluída. M07, o produto P2 em M10, o produto P3 em M11–M13 e a defesa M14 não são contabilizados nesses sete itens. Tampouco o item 10, quando executado, provará automaticamente todas as competências de M08/M09. Isso explica por que o inventário do P1 podia marcar 7/10 enquanto boa parte da formação permanecia por iniciar.

**Regra de acompanhamento a partir desta versão:** informar o marco ativo, a entrega aceita e a próxima competência; manter os escopos formação/produto/autonomia explícitos. Não publicar um percentual global sem critérios de fechamento e um denominador estável de unidades aceitas. Nenhum peso arbitrário de 50% será atribuído a um marco “parcial”. O currículo e seus IDs permanecem os mesmos.

**Checkpoint atual — próxima ação técnica**

| Campo | Estado atual |
| --- | --- |
| Projeto e ambiente | P2 — satellite-anomaly-monitor, subpasta própria em C:\renewable-forecast-lab; ambiente renewable-forecast existente. P1 preservado com pendências operacionais separadas |
| Última entrega do aluno conferida | E119: execução20261117T212230Z_965de3d1, onze hashes e30 métricas;1.512 previsões de baseline preservadas; cinco grupos do alinhamento autoral executados. Recibos de213329Z são de outra execução, sem resultado completo anexado |
| Retomada atual | M10.1 — produto P2 satellite-anomaly-monitor, dados reais ESA, sincronização, frescor e anotações. A decisão M09.3 do aluno pode ser consolidada sem bloquear esta prática |
| Último resultado do professor | E120:1.046.703 medições ESA em2007;350.400 instantes na grade,350.346 utilizáveis; cinco contraprovas e auditoria independente NumPy. Sem detector ou treinamento; execução Linux |
| Unidade ativa | M10.1 — contrato multicanal, busca causal e identidade dos eventos; M10.2 posterior com recorte ampliado antes de comparar detectores |
| Próxima ação | Extrair renewcast_m10_1_telemetria.zip na raiz e executar python satellite-anomaly-monitor/scripts/executar_m10_1.py. Dados reais já incluídos, sem instalação/Docker/treino. Ler satellite-anomaly-monitor/docs/Aula_M10_1_Contrato_Telemetria.md e implementar sincronizar_causal conforme seção7 |
| O que permanece pendente | Fuso e semântica início/fim da geração, disponibilidade meteorológica histórica e versões cadastrais; autonomia/transferência didática ainda exigem provas próprias |
| Avaliação reservada anterior | Encerrada em E24; não reutilizar como novo teste final intocado |

**Correção documental registrada na versão 1.23.** Até a versão 1.22, a matriz principal ainda mostrava estados da auditoria inicial (por exemplo, M04 como demonstração sintética), enquanto o diário já registrava execução real. A manutenção do documento estava inconsistente. Na versão 1.23, foram reconciliados o painel, o quadro de produto, a matriz M00–M14, o registro de aprendizagem e o checkpoint. As evidências antigas permanecem no diário histórico. “Pendente” descreve trabalho ainda sem entrega nesta trilha; não significa ausência de conhecimento prévio do aluno.

**Base e limites desta auditoria.** Foram relidos o histórico visível desta conversa, os trechos anteriores recuperáveis, o roteiro original completo, os três registros de execução enviados, a CLI entregue, o laboratório meteorológico e as três propostas de pesquisa. A recuperação das conversas antigas fornece trechos e resumos, não uma transcrição integral garantida de todas as mensagens. Essa limitação é preservada nos estados abaixo. O repositório privado atual não foi inspecionado nesta tarefa.

**Autorização para arquivos do projeto — 02/10/2026:** o aluno autorizou expressamente salvar o pacote e atualizar o roteiro na biblioteca do ChatGPT, com a resposta “sim, para todo o projeto desta pasta”. A autorização vale para criação e atualização dos arquivos deste projeto na pasta `/Do ferro ao pró - Data Science` e deve ser preservada nas próximas sessões. A atualização preparada1.31 foi bloqueada antes da gravação por revisão automática; esta1.32 reúne esse conteúdo e as novas evidências após a autorização.

**Complemento curricular aprovado em 12/10/2026:** a curadoria seletiva de IA generativa/agêntica permanece vinculada aos marcos M11–M14, conforme Complemento_Curricular_IA_Agentic_2026-10-12(1).md. P1 continua ativo; P4/OpsLens é apenas opção futura. A decisão curricular não representa execução nem eleva o progresso. A referência daquele complemento à execução Windows pendente de E84 foi superada pelo aceite E85 em 13/10.

**Compromissos recuperados do histórico**

| Compromisso | Aplicação neste roteiro |
| --- | --- |
| Formação guiada em Ciência de Dados, com atuação de professor | Explicação curta, tentativa do aluno, revisão, alteração autônoma e retomada registrada |
| Dados e problemas reais; portfólio próprio | ONS e telemetria ESA; exemplos sintéticos apenas para isolar conceitos, sempre identificados |
| Fundamentos matemáticos e estatísticos | Cada ferramenta se liga a uma hipótese, cálculo, pressuposto e análise de resultado |
| Implementação modular, testes, experimentos e executáveis | Código reutilizável em `src/`, verificações relevantes, relatórios, serviço e utilitário Windows |
| Três produtos, um ativo por vez | Renewcast → monitor de anomalias em telemetria → assistente operacional |
| Python, SQL, MLOps, Spark/Databricks, deep learning, Transformers, LLMs, RAG e agentes | Marcos explícitos na sequência; uso de biblioteca não equivale a competência demonstrada |
| 8–12 horas por semana e computador Windows com 24 GB RAM/MX110 2 GB | 8 horas essenciais; CPU e recortes pequenos como base; recursos adicionais dependem do experimento |
| Acelerar o percurso | Dispensar o que for demonstrado, reaproveitar código e reduzir alternativas; preservar avaliações |

O roteiro de 09/09 orçava 270–385 horas. Depois apareceram estimativas de 18–22 semanas e 16 semanas, sem reestimativa suficiente do escopo e da aprendizagem. Não há base para manter uma promessa única de duração. As próximas estimativas devem usar as horas reais das primeiras unidades avaliadas. Também ficam retiradas as estimativas anteriores de “20–25% implementado” e “menos de 15% aprendido”: não tinham denominador nem avaliações que as sustentassem.

**Evidências consultadas**

| ID | Fonte | O que ela permite afirmar |
| --- | --- | --- |
| E01 | `Do-ferro-ao-pro-Data-Science.md`, versão 0.2, 09/09/2026, leitura integral | Escopo original, três projetos, carga horária e escala N/0/1/2/3; é planejamento |
| E02 | `Texto colado.txt`, registro de instalação | Ambiente Python e bibliotecas instalados naquela execução |
| E03 | `Texto colado(1).txt`, relatório de validação | 12 arquivos; diferenças de schema; série CJU_BA5EIGT com 8.760 horas, sem target ausente, cobertura de 100% no recorte |
| E04 | `Texto colado(2).txt`, execução de 16/09 | 16 testes aprovados; tuning, treino HGB com 8.592 linhas, persistência do modelo, previsão h+1 e erro posterior ao abrir MLflow com outro backend |
| E05 | `cli_complete.py`, leitura integral | Interfaces de validação, preparação, backtest, avaliação, tuning, treino, previsão, calibração e governança; não certifica a integração atual de todos os módulos |
| E06 | Mensagens visíveis do usuário com a saída do push | Envio de `main` e `v0.2.0`; não certifica conteúdo ou funcionamento atual de todo o repositório |
| E07 | Histórico recuperado de 17/09 e resultados citados na conversa | Relato de 22 testes, calibração, bootstrap e aprovação para shadow; relatório bruto final não foi relido nesta auditoria |
| E08 | `renewcast_weather_point_in_time_lab.py` e execução do assistente registrada | Demonstração sintética executada pelo assistente; não comprova execução, compreensão ou integração pelo aluno |
| E09 | `Projeto Doutorado - Marlon.pdf`, 7 páginas | Direção de previsão probabilística, comparação de modelos e decisão sob incerteza |
| E10 | `Propuesta Premiliminar de Tesis Doctoral Estadistica.pdf`, 11 páginas | Validação temporal e por evento, calibração, explicabilidade e generalização em telemetria |
| E11 | `Propuesta Premiliminar de Tesis Doctoral.pdf`, 14 páginas | Telemetria, API, MLOps e assistente restrito com evidências |
| E12 | Pedidos e correções visíveis nesta conversa | Necessidade de continuidade didática, prática autoral, clareza sobre onde trabalhar e verificação das entregas |
| E13 | `Texto colado(3).txt`, enviado pelo aluno como `modeling`, 17/09/2026 | Leitura integral do módulo e análise sintática; função `predict_next` inspecionada. Nenhum treino ou inferência executado nesta leitura |
| E14 | `supervised.py`, `test_supervised.py` e log enviados pelo aluno, 17/09/2026 | Função e seis funções de teste, totalizando 11 casos pela parametrização; execução relatada `11 passed in 1.31s`; revisão do professor e contraprova com timestamps textuais ausentes registradas abaixo |
| E15 | Log de `tests/test_supervised.py` enviado pelo aluno, 18/09/2026 | `13 passed in 4.16s`; execução relatada no ambiente `renewable-forecast`, após proposta de dois casos de regressão; conteúdo atualizado dos arquivos não reenviado |
| E16 | `test_supervised.py`, `features.py` e log enviados pelo aluno, 18/09/2026 | `17 passed in 3.83s`; casos de atraso 0h/2h, disponibilidade ausente e origens fora de ordem; construtor de 27 features lido integralmente |
| E17 | `features.py`, `supervised.py`, `test_supervised.py` e logs enviados pelo aluno, 21/09/2026 | Extração do calendário e integração implementadas; arquivo de testes com 26 casos; execução em `(base)`, Python 3.13.13 incompatível, dependências ausentes e falhas de coleta; chave do teste de equivalência revisada |
| E18 | Confirmação do ambiente Python 3.12.13, `test_supervised.py` corrigido e `Texto colado(4).txt`, 21/09/2026 | Suíte executada em `renewable-forecast`: `1 failed, 47 passed in 8.50s`; única falha em `test_backtest_and_result_files`, por `KeyError: 'hour'`; os testes supervisionados passaram. Correção do contrato de saída indicada, ainda sem execução posterior |
| E19 | Log enviado pelo aluno, 21/09/2026 | `python -m pytest -q`: `48 passed in 14.76s`; regressão do backtest resolvida na suíte atual. A nova integração da busca apresentada nesta rodada ainda aguarda aplicação e execução pelo aluno |
| E20 | Log de pytest e primeiro tuning h+6 enviados pelo aluno, 22/09/2026 | `50 passed in 32.89s`; busca real com 7.911 linhas, cinco folds, atraso assumido de 2h e corte em 04/08/2026. MAE HGB 27,37796 versus persistência 51,78369; redução relativa 47,1301%; seleção reprovada pelo critério de viés absoluto médio de 3,10523 > 2. Holdout não avaliado |
| E21 | Interpretação do aluno e log de `horizon_diagnostics`, 22/09/2026 | Run `c9f73918630644f688cfd7f6a26e58fa`, oito candidatos inelegíveis e cinco folds com ganhos de MAE positivos. Viés com sinal OOF 2,2036878086567198, sinais alternados por fold; artefatos gravados e MLflow executado. Interpretação dos sinais e ganhos correta; rejeição geral de offset constante refinada pelo professor |
| E22 | Coleta explícita e suíte completa enviadas pelo aluno, 22/09/2026 | Dois casos de `test_horizon_diagnostics.py` coletados; `52 passed in 10.69s`. O diagnóstico e seus testes estão integrados. A causa exata da contagem anterior de 50 não foi estabelecida pelo log |
| E23 | Log e interpretação do aluno, 22/09/2026 | Dois testes de calibração aprovados (`2 passed in 1.49s`); run `57d9408018bf45279962da8fa30e6b68`; média causal aprovada no desenvolvimento: MAE 26,756, viés absoluto médio 1,706, ganho de MAE em cinco folds. Procedimento escolhido para avaliação reservada; holdout ainda não executado |
| E24 | Log de avaliação reservada enviado pelo aluno, 22/09/2026 | Run `d401657267524b528120f2c0ca7ea184`; 666 emissões avaliadas e seis finais sem alvo; HGB calibrado com MAE 25,325, ganho de 53,582% contra persistência e 2,450% contra bruto, viés do período 0,101. Três critérios globais atendidos; viés semanal entre −5,144 e +7,724 e RMSE ligeiramente pior que o bruto. Avaliação concluída; inferência sem alvo entregue em seguida, ainda sem execução real do aluno |
| E25 | Execução e três arquivos enviados pelo aluno, 22/09/2026 | Previsão h+6 sem alvo conhecido, emitida em 01/09/2026 01h para 07h: HGB 57,0496014, offset 11,8111658 e previsão calibrada 68,8607672 MWmed. JSON, CSV de 27 features e registro reconciliados pelo professor; quarta macroentrega demonstrada |
| E26 | Fontes públicas consultadas e módulo executado pelo professor, 22/09/2026 | Relação ONS, capacidade ONS e SIGA diário cruzados por CEG normalizado: 15 usinas, 27 registros de capacidade, 227,7 MW e coordenadas completas; capacidades ONS e ANEEL coincidem por usina. Código e snapshot entregues; reprodução e explicação do aluno ainda pendentes |
| E27 | Execução de asset_registry, CSV e metadados enviados pelo aluno, 22/09/2026 | Cadastro reproduzido: 15 usinas, 27 registros de capacidade ONS, 227,7 MW, pesos somando 1 e CEGs únicos. Arquivos lidos pelo professor; hashes das três fontes coincidem com E26. Explicação e alteração autônoma ainda sem nova avaliação |
| E28 | Documentação oficial e consulta real GFS executada pelo professor, 22/09/2026 | weather_runs.py consultou 15 pontos para a rodada 01/09/2026 00 UTC: 48 horas por usina, 720 linhas, cinco pontos de grade distintos, vento a 100 m em m/s e graus. JSON, cache, correspondência espacial e seleção temporal conferidos. Reprodução pelo aluno pendente; disponibilidade histórica assumida e fuso da geração não confirmado |
| E29 | Log de weather_runs, código inspecao_grade.py e grid_weights.csv enviados pelo aluno, 23/09/2026 | Coleta real de 720 linhas e cinco pontos de grade reproduzida, com horário informado 2026-09-23T16:47:56.074419+00:00. Agrupamento implementado: 5 grupos, 15 usinas, soma de pesos 0,9999999999999991; tabela conferida contra a referência, diferença máxima 5,55e-17. Novo incremento aplicado pelo aluno; explicação e retenção ainda sem avaliação |
| E30 | Segunda rodada real e seletor weather_asof executados pelo professor, 23/09/2026 | GFS 01/09 06 UTC coletado; duas rodadas/1.440 linhas usadas para nove emissões h+6. Saída com 135 decisões, 120 seleções e 15 ausências explícitas. Troca de rodada às 12 UTC sob latência assumida de 6h; invariância a vento indisponível, atraso simulado e publicação fora de ordem conferidos. Reprodução pelo aluno pendente |
| E31 | Logs e código atraso_meteorologico.py enviados pelo aluno, 24/09/2026 | Falhas iniciais de importação no Python base; depois coleta GFS 06 UTC concluída, 720 linhas, e simulação em cópia executada. Para Amescla, rodada00 até13h e rodada06 a partir14h, conforme atraso adicional de2h; NaT às05h coerente. Execução da CLI normal com cobertura gravada e retorno ao ambiente do projeto ainda não demonstrados |
| E32 | Logs enviados pelo aluno, 24/09/2026 | Ambiente renewable-forecast e importação confirmados; seleção normal executada para 05–15 UTC (165 decisões) e depois 05–13 UTC (135), no mesmo diretório. Coleta reutilizou cache. Simulação repetiu a troca às14h. Código do seletor grava CSVs antes do resumo; aluno relata não localizar o arquivo. Notebook de simulação somente imprime; orientada gravação explícita e localização da saída normal |
| E33 | coverage.csv, weather_asof.csv, metadata(1).json e log do aluno, 24/09/2026 | Arquivos normais recebidos e conferidos: 9 emissões, 135 decisões, 120 seleções e 15 ausências; hash do CSV corresponde ao metadado. Horizonte, disponibilidade, chaves, pesos e cobertura coerentes. Log confirma gravação da simulação Amescla; seu CSV não foi anexado. Reprodução de M04.3 concluída neste recorte |
| E34 | weather_features.py e referência calculada sobre os anexos E33 pelo professor, 24/09/2026 | Agregação meteorológica produz 9 linhas e 5 features; 8 emissões completas e 1 ausente. Conferidas componentes, cobertura parcial e equivalência entre 15 usinas e 5 pontos de grade. Implementação entregue; execução e transferência pelo aluno pendentes |
| E35 | weather_features.csv, metadata(2).json, código e execução de inspecao_vento.py, 28/09/2026 | Agregação reproduzida:9 linhas,8 completas; hash do CSV conferido e cinco atributos equivalentes à referência. Script do aluno verifica constância do vento por grade e demonstra equivalência15usinas→5pontos. Separadas explicitamente as pastas h6_sample (entrada por usina) e h6_spatial_sample (saída agregada) |
| E36 | weather_history.py e coleta histórica do professor, 28/09/2026 | Orquestra coleta, seleção e agregação existentes. Duas rodadas reais de01/07/2026 geraram12 emissões completas. Plano semanal01/07 06h→08/07 05h UTC prevê28rodadas,168emissões e2520decisões. Semana completa pelo aluno e junção com geração ainda pendentes |
| E37 | coverage(1).csv, metadata(3).json, weather_asof(1).csv, weather_features(1).csv e metadata(4).json enviados pelo aluno, 28/09/2026 | Piloto semanal completo: 28 rodadas registradas, 168 emissões, 2.520 decisões e 168 linhas agregadas completas. Hashes, horizonte, disponibilidade, chaves, pesos e cinco atributos recalculados e conferidos pelo professor |
| E38 | weather_training.py entregue e verificado pelo professor, 28/09/2026 | Integra 27 entradas históricas/calendário e 5 meteorológicas por emissão/alvo em UTC, preservando calendário no fuso declarado. Verificação com meteorologia real de E37 e geração explicitamente sintética; execução com o Parquet real do aluno ainda pendente. Fuso e semântica do intervalo continuam hipóteses |
| E39 | model_frame.csv e metadata(5).json enviados pelo aluno, 28/09/2026 | Junção real:168linhas,55colunas,32entradas e alvo separado. SHA256, fontes meteorológicas, coerência de tempos e calendário conferidos. Lags/alvos permitem reconstituir343referências horárias e recalcular as27features; isso verifica consistência interna, não uma leitura independente do Parquet original |
| E40 | weather_ablation.py e execução do professor sobre E39, 28/09/2026 | Dois HGB com27/32entradas, mesmos parâmetros e folds purgados, sem calibração;72previsões reais de validação. MAE histórico36,3130; histórico+vento43,0246; piora18,4827%. Experimento exploratório; reprodução do aluno e ampliação para31dias pendentes |
| E41 | Texto colado(5).txt, predictions.csv, fold_metrics.csv, folds.csv, summary.csv, protocol.json, metadata(6).json e interpretação do aluno, 28/09/2026 local | Piloto reproduzido; 124 rodadas e 744 linhas integradas declaradas no log; 504 previsões pareadas recebidas e métricas/hashes recalculados. MAE histórico 32,7444 e com vento 26,4540 MWmed, redução 19,2106%. Números do aluno corretos; alegações causais/mecânicas excedem os dados. Persistência no maior ganho erra apenas 0,0915 MWmed |
| E42 | weather_gain_uncertainty.py e análise do professor sobre predictions.csv de E41, 28/09/2026 local | Bootstrap circular pareado, estratificado por fold, 5.000 réplicas e blocos 6/24/48h, semente42. Ganho médio 6,2904; IC percentil nominal95% agregado [3,7394;8,9650], [2,7851;9,4984], [2,5634;9,5396] MWmed. Condicional/exploratório, não corrige seleção prévia nem comprova causalidade; reprodução/interpretação do aluno pendentes |
| E43 | Parecer do aluno e dois reenvios de seis arquivos com sufixos(1)/(2), 30/09/2026 | Decisão de manter candidato em desenvolvimento e leitura do extremo corretas. Anexos idênticos byte a byte a E41. IC[2,56;9,54] pertence ao agregado com48h; Fold2 cruza zero com6h, Fold3 com24/48h. Não foi recebida nova evidência de execução do bootstrap |
| E44 | Fontes ONS consultadas e adaptação/verificação do professor, 30/09/2026 | Dicionário não esclarece fuso/início-fim; portal avisa revisão dos dados. Orquestrador suporta h6/h24 e --cache-only; seleção h24 executada com duas rodadas reais e12emissões. Plano mensal744origens/124rodadas, treino214/382/550; modelo mensal h24 ainda não ajustado pelo aluno |
| E45 | Log do aluno e pacote de retomada conferido pelo professor, 01/10/2026 | CLI executada rejeita as opções h24/cache, sem saída para as etapas seguintes. Versão 2026.10.01-h24 e retomar_h24.py entregues com backup, identificação do módulo e interrupção por falha. Seleção real de 12 emissões e controle de falha verificados em Linux; execução mensal no Windows pendente |
| E46 | Texto colado(6).txt e seis artefatos h24 com sufixos(3)/(9), 01/10/2026 | Versão/caminho corretos e três etapas concluídas; 744 linhas declaradas, 504 previsões auditadas. MAE persistência/histórico/vento 29,3943/38,1821/28,7980; ganhos de vento 24,5773% vs histórico e 2,0285% vs persistência. Hashes e plano 214/382/550 conferidos |
| E47 | Reamostragem do professor sobre predictions(3).csv de E46, 01/10/2026 | Bootstrap circular pareado por fold, 5.000 réplicas, seed42, blocos6/24/48h. Ganho agregado vs histórico positivo nos três ICs; vs persistência os três ICs incluem zero. Análise condicional/exploratória, sem refit, sem promoção e sem nova prova autônoma do aluno |
| E48 | model_frame(1).csv e metadata(10).json enviados pelo aluno, 01/10/2026 | Hashes coincidem com o protocolo h24;744linhas/55colunas/32entradas; completude, relógios, calendário, deltas e janelas reconciliados. Geração reconstruída internamente de lags/alvos, sem nova leitura do Parquet bruto |
| E49 | weather_artifact.py, aula e execução do professor sobre E48, 01/10/2026 | Corte01/08 05UTC admite717linhas/exclui27; modelo salvo e recarregado em outro processo; previsão152,7141273MWmed no ambiente do professor, pedido sem alvo. Inferência sem acesso ao treino e fit proibido conferidos. Reprodução no Windows e autoria do aluno pendentes |
| E50 | prediction.json, request.json, manifest.json e model.joblib enviados pelo aluno, 02/10/2026 | Hashes conferidos; dataset de origem e 32 features reconciliados; 717 linhas elegíveis e 27 excluídas; previsão registrada 143,6473739986 MWmed. Binário não recarregado pelo professor devido à diferença sklearn 1.9.0/1.8.0. Sexta macroentrega técnica aceita no escopo histórico |
| E51 | Código em Markdown colado.md e contraprova do professor, 02/10/2026 | np.hypot, tolerância e ponto de chamada adequados; busca de chaves por substring usa cubed como velocidade/componente ao mudar a ordem. Pedido impossível passa na ordem reversa. Correção com nomes exatos conferida; aplicação/explicação do aluno pendentes |
| E52 | weather_quantiles.py e execução do professor na tabela real E48, 02/10/2026 | Três folds 214/382/550 de treino e 168 de validação; 504 emissões por método. HGB P10/P50/P90: cobertura 52,58%, largura 57,16, pinball média 8,2821; baseline de resíduos: 88,49%, 139,56 e 10,4514. Sem calibração adicional, promoção ou validação independente; reprodução do aluno pendente |
| E53 | folds(4).csv, metadata(20261002-214217).json, predictions(4).csv, protocol(4).json, summary(4).csv e fold_metrics(4).csv, 02/10/2026 | Execução probabilística reproduzida: 1.008 linhas, 504 emissões por método, cortes 214/382/550. Todos os hashes e métricas reconciliados; HGB cobertura 55,36%, largura 57,6128, pinball média 8,077151; 152/504 alvos acima do P90 |
| E54 | Código inspecao_quantis.py colado pelo aluno, 02/10/2026, e revisão do professor | Fórmula NumPy correta; main procura model/q_XX, enquanto o CSV exige method/pXX. Reprodução da falha gera média zero falsa. Correção explícita executada sobre anexos confere os dois métodos com tolerância 1e-10; aplicação/interpretação do aluno pendentes |
| E55 | Log de inspecao_quantis.py e interpretação enviados pelo aluno, 02/10/2026 | Quatro perdas coincidem com summary.csv para cada método. Distinção frequência/magnitude correta; corrigidos requisito de exatamente10%, atribuição de compressão ao otimizador e garantia irrestrita de conformal. Decomposição P90 conferida nos anexos E53 |
| E56 | weather_interval_calibration.py, aula e execução do professor sobre E48, 02/10/2026 | Nove ajustes; treino140/308/476, calibração48/48/48, avaliação168/168/168. CQR adaptada para expansão não negativa, rank40, duas fronteiras temporais; cobertura57,14%→79,37%, interval score125,5090→117,5757. Reprodução/autoria do aluno pendentes; sem promoção |
| E57 | Log de weather_interval_calibration e segunda execução de inspecao_calibracao enviados pelo aluno, 02/10/2026 | Nove ajustes e cortes140/308/476,48 e168 relatados; cobertura51,3889%→77,1825%, largura60,679278→89,870200, interval score129,852982→120,022226. Correções19,693951/0,619147/23,473284MWmed; CSVs novos não anexados nesta rodada |
| E58 | Código inspecao_calibracao.py, interpretação autoral e revisão/contraprovas do professor, 02/10/2026 | Rank40 e ordenação corretos para48 escores; vazio→zero, truncamento de k e comparação exclusiva de origens identificados. Script corrigido com contrato explícito/duas disponibilidades; executado na referência e contraprovas, aplicação do aluno pendente |
| E59 | Log de inspecao_calibracao.py enviado pelo aluno, 03/10/2026 | Três correções coincidem: 19,693951/0,619147/23,473284; n48/k40, escores zero16/38/31, duas fronteiras verdadeiras. Inspeção do plano exportado concluída; métricas preservadas e nenhum novo ajuste |
| E60 | weather_events.py, aula e execução do professor sobre E48, 03/10/2026 | Evento de queda >=22,77MWmed frente a y(t−2), alvo y(t+24); 3 métodos ×504 emissões,113 positivos. Brier 0,174640/0,132262/0,112417 para frequência/logística/HGB. Calibração probabilística apenas diagnosticada; reprodução e decisão autoral do aluno pendentes |
| E61 | Oito arquivos de eventos, código e logs do aluno, 03/10/2026 | Sete hashes de saídas/protocolo, duas fontes e hash do código conferem. 744 rótulos, 504 emissões, 113 positivos; 3 resumos, 9 métricas por fold e 60 bins reconciliados. HGB Brier 0,111142; estimadores não reajustados na auditoria |
| E62 | inspecao_decisoes.py autoral e tabela do aluno; revisão executada nos anexos, 03/10/2026 | 24 linhas reconciliadas; exemplo autoral TP=FP=FN=TN=1/custo5 correto. HGB: 0,2 reduz custo191→158 recuperando16 positivos e acrescentando31FP; Fold2 piora. Corrigidos caminho, domínio, pareamento e razão indefinida; sensibilidade entregue, política sob capacidade é próxima autoria |
| E63 | threshold_metrics.csv, cost_sensitivity.csv, hgb_tradeoffs.csv, metadata(20261003-171749).json, código e log do aluno,03/10/2026 | Três hashes de saídas e hash da fonte conferem;24/120/4 linhas recalculadas. Função autoral escolhe HGB/0,5,109 alarmes,custo191 entre alternativas viáveis; decisão ainda de desenvolvimento |
| E64 | Política JSON, decision_api.py, consultar_api_decisao.py, aula e verificações do professor,03/10/2026 | Pydantic/FastAPI/Uvicorn; API aplica regra a probabilidade histórica. CLI de módulo e cliente executados em processos separados;200 para pedido real,422 para entrada inválida. Reprodução do aluno pendente; não carrega estimador nem limita alarmes acumulados |
| E65 | Seis JSONs, duas capturas e log do aluno, 03/10/2026 | Replay HTTP reconciliado: p=0,16175954827073333, alarme falso, HTTP 200; p=1,2 rejeitado com HTTP 422. Hash da fonte confere; hash de política informado coincide com a referência serializada em CRLF. Arquivo original da política não recebido. Execução do aluno aceita; nenhuma nova inferência ou estimativa de desempenho |
| E66 | decision_api.py, pedido_limiar_m06.json e verificação do professor, 03/10/2026 | Exemplo genérico do Swagger rejeitado por método incompatível; limiar físico e horários também divergem do contrato. Exemplos OpenAPI passaram a derivar da política. Replay do aluno e rejeições reproduzidos; exemplo p=0,5 aceito com alarme verdadeiro. Correção documental entregue; regra de decisão preservada |
| E67 | Pedido JSON e crítica do aluno; auditoria do roteiro versão 1.36, 04/10/2026 | Corpo compatível com a política; resposta dessa chamada não enviada. Auditoria distingue 14 marcos M01–M14 mais M00 de dez itens técnicos do P1. Seis marcos abordados, oito sem entrega prática. Percentual de 70% retirado do painel da formação; entregas existentes preservadas e mapeadas |
| E68 | event_artifact.py, decision_api.py release3, cliente, aula, exercício e verificações do professor, 04/10/2026 | 744 linhas reais; treino717/eventos170; corte01/08 05UTC e último rótulo04UTC. Artefato salvo; HTTP em processos separados sem tabela de treino; 32 features produzem p=0,2017918883. Rejeições e ordem conferidas; fit impedido na inferência. Reprodução/autoria do aluno pendentes; integração histórica com política retrospectiva, sem novo desempenho ou promoção |
| E69 | Cinco JSONs do aluno, log de inferência e função/cenários de vento, recebidos04/10 e conferidos05/10/2026 | HTTP200, p=0,2046538537; ordem invariante e duas rejeições422. Hash do pedido confere. Escala linear/cúbica e preservação aceitas; cenários relatados por log. Binário/manifesto do modelo e CSV dos cenários não anexados nesta rodada |
| E70 | event_batch.py, SQLite, script, notebook SQL e execução do professor,05/10/2026 | Artefato separado com corte31/07 06UTC,694linhas/168eventos.24emissões; repetição24reutilizadas. Snapshots5/19 e24/0 observadas/pendentes. Sete testes de contrato e integração real com fit proibido. Execução e autoria SQL do aluno pendentes; não é avaliação independente nem shadow ao vivo |
| E71 | Log do lote no Windows e consulta SQL do aluno, 05/10/2026 | Execução completa: 694 linhas/168 eventos, 24 previsões e repetição idempotente. Consulta retorna 5/19 e 24/0, FN 0/4 e custo 0/16. Brier do aluno 0,080300/0,132603; métricas do professor não substituem esses resultados |
| E72 | SQL com data_status, saída normal e CTE de falha orientada, 05/10/2026 | Autor de JOIN/GROUP BY/CASE/NULLIF e alerta por ausência devida. Espera permanece OK. Falha controlada produz 4/20 e 23/1, um missing_observation e investigate; custo16 e média0,695652. CTE fornecida pelo professor; execução reconhecida sem atribuir autoria independente dessa CTE |
| E73 | event_monitor.py, regras JSON, HTML/JSON e aula completa, 05/10/2026 | Quatro cenários em dados reais; integridade/dados/desempenho separados. Referência168/694 do treino; mínimo168 e tolerância10% são didáticos. Normal com24 resultados mantém insufficient_evidence. Execução/autoria independente do aluno pendentes |
| E74 | Log do aluno executando event_monitor --exercise, 05/10/2026 | Normal → collect_evidence; falta de observação → investigate_data; probabilidade alterada e avaliação ausente → repair_record. Reprodução do monitor aceita por log; JSONs e banco atuais não anexados |
| E75 | Código do parecer, parecer.csv/md e suas cópias idênticas; revisão e execução do professor, 05/10/2026 | Brier0,281875/Skill−0,502830 calculados em fallback sintético: parecer inválido para o lote. Correção usa ledger.sqlite, manifesto do lote, corte único e métricas JSON obrigatórias. Dez verificações dirigidas passaram na réplica real. Execução corrigida e transferência pelo aluno ainda não recebidas |
| E76 | Parecer(2).csv/md, auditoria.json e log recebidos05/10/2026 |24 observações; cinco confrontos aprovados, máximo1,11e-16; código entregue identificado por hash; quatro cenários coerentes. Correção técnica encerrada, sem atribuir autoria independente ao texto gerado |
| E77 | Middleware ASGI, carga HTTP, aula e verificação do professor,05/10/2026 |45 requisições conciliadas por request_id, com422/500 e atraso identificados; artefato preservado. Seis contratos verificados e fluxo real comfit proibido. Execução e diagnóstico autoral do aluno pendentes |

| E78 | Código diagnostico_servico.py, cinco arquivos da execução, incidentes.csv e log do aluno, 05/10/2026 | Quatro hashes válidos, 46 chamadas cliente/servidor com um aquecimento e 45 medidas. Dez incidentes exatos; métricas normal/incident e prioridade dos 5xx corretas. Indefinidos tratados como zero, hash procurado em qualquer campo e causa de 500 mal atribuída identificados |
| E79 | Notebook revisado, revisão didática e execução do professor sobre cópias dos anexos, 05/10/2026 | 33 comparações com summary.csv, dez IDs e quatro hashes aprovados. Caminho/ponteiro exatos, NaN, hash por arquivo e decisão vinculada à injeção. Contraprovas dirigidas aprovadas; nenhuma chamada nova ou treino. Aplicação da correção pelo aluno pendente |
| E80 | Quatro arquivos e log da inspeção corrigida recebidos em 07/10/2026 | Três hashes de saídas e cinco fontes conferem; 33 comparações e dez IDs reconciliados. Código corresponde ao entregue; NaN e causa da injeção tratados corretamente. Unidade de diagnóstico encerrada no escopo demonstrado |
| E81 | Registro local, serviço por alias, exercício HTTP, aula, inspeção e testes do professor, 07/10/2026 | Duas versões reais existentes, três commits, controle de geração e recuperação observada. 13 tentativas HTTP e cinco probes; quatro testes dirigidos sem skip. Fit proibido no fluxo; execução/autoria do aluno pendentes |

| E82 | Log e SQL autoral enviados em 09/10/2026; revisão orientada executada sobre o registro real E81 | Ambiente base impede o exercício e causa ausência do ponteiro. Consulta usa coluna agregada inexistente na fonte, não trata a primeira linha nem a continuidade. Revisão conferida em três gerações e contraprova em memória; execução corrigida do aluno pendente |

| E83 | Log e 13 anexos do aluno, recebidos em 09/10/2026; recálculo independente do professor | Ponteiro e dez hashes aprovados; três gerações, 13 POST/5 GET e recuperação v1/g3 reconciliados; 21 células da saída SQL corretas. Reprodução técnica aceita; parecer independente pendente; iniciador Windows entregue sem execução local observada |
| E84 | Pacote de empacotamento, aula e verificação do professor em 09/10/2026 | Snapshot do runtime em wheel, dependências capturadas com hashes e instalação offline em ambiente novo; resposta HTTP reproduzida na réplica Linux. Execução Windows, transporte pelo aluno e autoria ainda pendentes; nenhuma nova aprovação estatística |
| E85 | Nove anexos, código e log do orçamento do aluno, recebidos em 13/10/2026 | Reprodução Windows e cálculo aceitos: seis hashes, 26 wheels/68,6819 MiB, top5 96,2425%, probabilidade preservada. Parecer/fallback e vínculo entre ponteiros exigem revisão; transporte externo não demonstrado |
| E86 | Pacote Docker/CI e aula preparados em 13/10/2026 | Captura Linux mantendo versões/modelo, contexto, digest da base e comparador HTTP; componentes Python verificados na réplica. Docker/PowerShell/CI remoto não executados; material entregue, não concluído pelo aluno |
| E87 | Nove anexos Docker e interpretação do aluno, 13/10/2026 | Migração Linux aceita: ponteiro e sete hashes, 26 versões, modelo/política e resposta inteira reconciliados com Windows. Uma entrada não cobre qualquer plataforma/carga |
| E88 | Pacote de concorrência, aula e prova do professor, 13/10/2026 | Cliente 1/4/8, três rodadas e recursos fixos; verificação nativa na réplica e falhas dirigidas. Execução Docker do aluno, decisão autoral e interpretação pendentes |
| E89 | Console, função autoral e parecer do aluno; revisão em 14/10/2026 | Escolha de quatro clientes correta sob o contrato do carregador; ganho entre medianas 63,25%, diferença da terceira rodada −1,79%. Código executado com valores arredondados transcritos e contraprovas sintéticas; sem novo recibo/CSV anexado. Recomendação experimental aceita, ressalvas registradas |
| E90 | Cliente Windows, build, controlador, aula e prova do professor em 14/10/2026 | Cliente Python verificado em HTTP contra réplica existente com fit proibido. PyInstaller e execução Windows ainda pendentes; autoria de lançador com caminhos portáveis/exit code proposta. Material entregue não equivale a executável aprovado |
| E91 | Anexo Texto colado(8).txt e logs/recibos do aluno em 14/10/2026 | Build e verificação externa do cliente 1.0 informados; lançador corrigido exibiu p=0,20465385372296466/exit0 e indisponibilidade/exit3 em recibos distintos. Aceite local pelos registros; sem revalidação independente de todos os hashes do aluno |
| E92 | Código e cinco resultados de politica_atualidade.py em 14/10/2026 | Regra autoral aprovada no contrato UTC do exercício: histórico permitido, alvo vencido, atual, origem antiga e origem futura. Relógio explícito; prioridade das regras correta |
| E93 | Pacote de integração e Verificacao_E93_Professor.json em 14/10/2026 | Cliente 1.1 com regra promovida, modo explícito, recibo v2, saída7 para bloqueio e audit_response. Cinco cenários HTTP na réplica nativa e fronteiras conferidas, sem treino. Execução Windows 1.1 ainda pendente |
| E94 | Oito anexos do aluno; run 20261017T002410Z_7f76e51f | Cliente 1.1 aceito: sete hashes e 32 conferências; saídas 0/7/2/4/3, paridade zero, sem Conda/PYTHONPATH no processo. Fecha M06.5 local |
| E95 | Pacote/aula M07.1 e Verificacao_E95_Professor.json em 17/10/2026 UTC | Transformação diária DuckDB/PySpark, contrato e autoria SQL/classificação. Professor executou núcleo em dados sintéticos; execução Docker/Parquet real/autoria do aluno ainda pendentes |
| E96 | Texto colado(9).txt e transformacao_spark.py enviados pelo aluno, 19/10/2026 | Build e preflight concluídos; Spark falhou com user.home/Ivy relativo e hostname não resolvido. Classificação correta; três expressões de contagem incorretas em dados com lacunas/nulos. Não há recibo de transformação concluída |
| E97 | renewcast_m07_correcao_20261019.zip e Verificacao_E97_Professor.json | Correção orientada do usuário Docker, cache/endereço Spark e SQL; caso manual executado no Linux nativo com user.home=? e cinco discrepâncias anteriores demonstradas. Execução Docker/Windows corrigida e explicação do aluno pendentes |
| E98 | Texto colado(10).txt e relato do aluno, 19/10/2026 | Dois runs iniciam Spark e falham em libzstd-jni ao coletar o primeiro resultado. Não alcançam o plano SQL autoral. O aluno relata falta de compreensão de PySpark; a progressão didática anterior foi prematura |
| E99 | renewcast_m07_base_20261019.zip e Aula_M07_1_PySpark_Desde_a_Base.md | Correção localizada de montagem, detecção de noexec e explicação por operações/SQL. Professor executa exemplo em Linux nativo e lê Zstd; Docker e aprendizagem do aluno permanecem pendentes |
| E100 | Dezesseis anexos do run 20261019T230058Z_cf2fe669 e resposta conceitual do aluno, 19/10/2026 | Quinze hashes de anexos e três de código conferidos; 365 datas e 8.760 presentes reconciliados; DataFrame/SQL/DuckDB equivalentes. Exercício NULL→6 aceito. Próxima autoria: calendário e preenchimento seletivo; M07.1 ainda em aprendizagem |
| E101 | Código colado, aula_calendario.csv e plano_resumo.txt de 25/10/2026 | Calendário/classificação e plano conferidos; soma declarada fora de agg, ausente no CSV/plano. Correção orientada e laboratório temporal completo entregues. Conclusão pelo aluno ainda pendente |
| E102 | Logs reais de 27/10/2026, autoria selecionar_treino e falha com corte | Tabela e contraprovas executadas; autoria correta. Cópia montada ainda tinha NotImplementedError. Correção de entrega incorporada; execução Windows com corte pendente |
| E103 | Log Windows e sete arquivos de dados/plano de 27/10/2026 local | 21 conferências aprovadas; Parquets8.760/7.485 e seleção integral exata; bloqueio encerrado |
| E104 | Aula, script e verificação M07.2 Delta | Correção simulada+12, versões0/1, sete origens e duas linhas do treino; snapshot0 reproduz o Parquet. Núcleo Linux executado; Windows/autoria pendentes |
| E105 | Log Windows Delta e planejador autoral enviados em29/10; chamada de conferência entregue | Reprodução técnica M07.2 aceita pelo log; código autoral correto nas dependências, validação de fuso orientada e informada como aplicada. Arquivos desta execução Windows não recebidos; chamada no CSV e defesa conceitual a consolidar |
| E106 | Log de planejar_recalculo_temporal.py,29/10 | Quatro conjuntos iguais ao CSV da execução Windows; histórico1,média6,alvo1,união7; duas origens no treino. Não houve novo Spark/MERGE. Aceite técnico M07.2 |
| E107 | Pacote, notebook e aula M07.3 Databricks; teste local do professor | Preparador de três arquivos e notebook com tabelas gerenciadas, ID/versão, confronto integral, duas configurações e recibo. Núcleo aprovado localmente; criação de volume/UI/serverless e execução do aluno ainda pendentes |
| E108 | Notebook Databricks exportado e scale_comparison.md, 29/10 | Sete células iguais ao distribuído; 8.760/7.485 linhas, zero divergências; tabelas/versões e fronteiras conferidas. Reprodução aceita, parecer revisado; JSON do recibo separado não recebido |
| E109 | Aula, script e verificação M08.1 Autograd | Gradiente, modelo afim, exclusão temporal, curva, taxa e recarregamento testados em Linux/CPU na entrega original. O aceite posterior do aluno com assistência está registrado em E110 |
| E110 | Função gradiente_mse e parecer M08.1 recebidos em texto, 04/11 | Aceite com autoria assistida; função transcrita/testada e interpretação conferida. Resultados Windows relatados, sem arquivos brutos nesta mensagem. M07.3 reapresentado era a versão anterior, correção E108 preservada |
| E111 | Aula, código e verificação M08.2 Dataset/MLP | Três sementes em Linux/CPU, comparação com linear nas mesmas janelas, seleção temporal e 15 conferências aprovadas. Pendência original do aluno posteriormente encerrada no escopo de E112 |
| E112 | Função avaliar_lotes e parecer M08.2, relato de 05/11; registro15/11 | Aceite com assistência declarada. Função executada nas contraprovas; decisões, divisões e métricas relatadas conferidas. Arquivos Windows não anexados |
| E113 | Pacote, aula e referência M08.3 GRU,15/11 | Nove variantes pareadas, portas/estado e checkpoints conferidos em Linux. Execução/célula do aluno posteriormente aceitas em E114; defesa ainda a consolidar |
| E114 | Execução Windows M08.3, nove anexos, célula NumPy e cinco testes,15/11 | Oito hashes e27 métricas reconciliados; cinco testes e comparação PyTorch aprovados. Aceite técnico; defesa do aluno ainda não recebida |
| E115 | Aula/laboratório M09.1 atenção escalada,15/11 | Q/K/V, máscara, posição e janela real; oito grupos conferidos em Linux, sem treino. Entrega posterior do aluno reconhecida em E116 |
| E116 | Atenção autoral, seis casos e logs Windows recebidos | Função e casos transcritos/executados; seis aprovados e oito grupos PyTorch. Erro --autoria é argumento faltante; código aceito |
| E117 | Runner/verificador Transformer anexados e logs Windows,17/11 | Dois arquivos compilam e foram revisados;13 grupos relatados. Módulo dos blocos/artefatos completos não anexados; alcance da revisão preservado |
| E118 | Pacote/aula M09.3 e benchmark Chronos-Bolt Tiny,17/11 | Controlador/ambiente privado e inferência executados em Linux, snapshot fixado, alinhamento26 passos e métricas auditados. Execução do aluno pendente |
| E119 | Execução Windows M09.3, função e anexos,17/11 | Onze hashes e30 métricas da rodada212230Z conferidos;1.512 baselines preservados, alinhamento executado e aceito. Recibos da rodada213329Z são distintos; parecer próprio não anexado |
| E120 | P2/M10.1: contrato ESA real,17/11 | Pacote completo offline,1.046.703 medições,350.400 instantes, cinco contraprovas e auditoria independente. Referência Linux executada; aluno pendente. Nenhum detector treinado |

E09–E11 são propostas de pesquisa, não experimentos executados. Referências bibliográficas contidas nesses documentos não foram todas verificadas; elas não constituem resultados do projeto.

**Estado atual do produto e da aprendizagem — 14/10/2026**

| Área | Estado técnico atual | Evidência de aprendizagem e limite |
| --- | --- | --- |
| Ambiente, pacote e CLI | E83 confirma ativação e execução completa do registro no Windows | Bloqueio E82 resolvido. Iniciador de dois cliques entregue; sua execução Windows ainda não foi observada |
| Série ONS e contratos | Série real de 8.760 horas preparada; validações e transformações executadas | Pareamento e cenários de erro apresentados; SQL autoral aceito em E71/E72. E83: saída SQL corrigida reconciliada em 21 células, após tentativa autoral E82. Autonomia, parecer e transferência a outro conjunto ainda pendentes |
| Features, tuning e horizontes | h+1/h+6 executados; ablação h24 e inferência por artefato reproduzidas em E46/E50 | Aluno explicou disponibilidade, alvo, horizonte e sinais de viés; E51 aplica validação física, com falha de contrato identificada; defesa independente da comparação h24 ainda pendente |
| MLflow e rastreabilidade | Runs de diagnóstico, calibração e holdout registrados; hashes e logs presentes; E81 entrega registro SQLite local | Tracking aplicado; E83 aceita reprodução do registro/rollback local pelo aluno. Administração do MLflow Model Registry e promoção operacional não estão demonstradas |
| Calibração e critérios | Média causal escolhida no desenvolvimento e avaliada no holdout | Interpretação do benefício e da instabilidade temporal apresentada pelo aluno; não foi demonstrada estabilidade semanal universal |
| Cadastro e meteorologia | Cadastro real, 124 rodadas no desenvolvimento mensal, 744 emissões com cobertura integral declarada no log E41 | Aluno executou pesos, atraso, equivalência espacial e ampliação; disponibilidade histórica ainda assumida |
| Junção geração/vento | E48: tabela mensal h24 recebida e conferida diretamente,744linhas/55colunas/32entradas. E39 cobre o piloto h6; E41 documenta a ampliação h6 | Relógios e coerência interna das features reconciliados; fuso, semântica do intervalo e versões históricas permanecem hipóteses |
| Ablação meteorológica | E41/E46: h6 e h24 com 504 previsões cada; ganhos vs histórico 19,21%/24,58%, vs persistência 56,10%/2,03%. E47 recalcula incerteza h24 | E43 registra interpretação h6 do aluno. Resultado h24 executado; distinção entre ganho de features e superioridade sobre baseline apresentada pelo professor, ainda sem defesa independente |
| Quantis, eventos, API/shadow e monitoramento | E71/E72: lote/SQL; E74/E76: monitor/parecer; E80: diagnóstico HTTP corrigido encerrado; E81: registro/rollback entregue | Núcleo autoral anterior reconhecido e revisão reproduzida. E83: fluxo e saída da revisão orientada conferidos nos anexos do aluno, com resposta 200 e hash da recuperação identificados. Parecer independente ainda pendente. Shadow ao vivo, monitoramento contínuo e cota não concluídos |
| Distribuição e concorrência | E85–E94: distribuição, concorrência e cliente 1.1 aceitos nos respectivos protocolos | E94 fecha M06.5 com evidências anexadas; atualidade separada do sucesso HTTP. Limites operacionais permanecem explícitos |
| Transformação em Spark, Delta e Databricks | E100–E108: tabela temporal e seleção, planejador de revisões e reprodução Databricks conferidos | M07 concluído no escopo das unidades. Parecer de versões/local-cloud aceito; Exchange/broadcast, AQE, janela e cronômetro revisados pelo professor, sem nova prova independente dessas correções |
| DL, Transformers, LLMs, RAG e agentes | E114:GRU; E116/E117:atenção/composição; E119:pré-treinado Windows e alinhamento aceitos | Defesa integrada M09.3 própria não anexada; E120 entrega M10.1. M11–M14 posteriores. Operação, retenção e autoria independente não certificadas |
| Telemetria e defesa final | Planejadas | Propostas de pesquisa são escopo, não experimentos concluídos |

**Aprendizagem:** há evidências aplicadas e notas em cenários específicos; uma competência sem prova suficiente fica como “não avaliada”, sem apagar o trabalho já realizado.

O último resultado relatado para h+1 compara MAE de aproximadamente 10,709 na persistência e 10,403 no HGB calibrado, com intervalo do ganho cruzando zero. Isso sustenta investigação adicional, não superioridade estatística comprovada nem produção. Os números de validação em E04 pertencem a outra etapa/protocolo e não devem ser misturados com os de E07.

O cadastro atual de parques, capacidades e coordenadas foi cruzado com fontes oficiais e reproduzido (E26/E27); versões históricas desse cadastro continuam não verificadas. A latência meteorológica de seis horas e o atraso de geração de duas horas permanecem hipóteses explícitas. A correção histórica do laboratório continua registrada: 66 origens × 3 horizontes = 198 decisões, não 210. As entregas reais posteriores estão descritas em E29–E42; não são mais somente aquele laboratório sintético.

**Produtos principais a entregar**

| Produto | Entregas essenciais | Evidência de conclusão |
| --- | --- | --- |
| P1 — Renewcast | Dados rastreáveis; baseline e avaliação h+1; meteorologia e h+1/h+6/h+24; quantis; análise de eventos; serviço, lote e monitoramento; utilitário Windows; comparação neural/fundacional | Fluxo reproduzível do dado à previsão; relatório de desempenho e limites; falhas tratadas; aluno explica e modifica as partes essenciais |
| P2 — Monitor de anomalias em telemetria | Recorte ESA documentado; baselines; limiares; métricas por evento e atraso; análise de erros e de canais; inferência reutilizável | Nova janela produz escore e evidências; limiar escolhido fora do teste; resultados reproduzidos pelo aluno |
| P3 — Assistente operacional | Aplicação GenAI estruturada; corpus versionado; busca/RAG com citações; ferramentas de consulta; agente com limites; avaliação e rastros | Respostas e números verificáveis; tratamento de ausência de evidência; recuperação e geração avaliadas separadamente; falhas de ferramentas testadas |
| Evidência transversal | Experimento PySpark/Delta/Databricks; decisões técnicas; vocabulário aplicado; defesa e estudo de reprodução/ablação | Relatórios ligados a dados, código, configuração, execução e avaliação de autonomia |

Cada produto começa localmente e reutiliza as competências anteriores. Cloud é uma unidade delimitada de entrega; contratação e gasto não são pressupostos. Um resultado negativo bem sustentado pode concluir um experimento. Ganhar do baseline não é condição artificial para aprender ou concluir a comparação.

**Sequência fixa de marcos e ferramentas — M00 preparatório + 14 marcos M01–M14**

Estados técnicos atuais: **demonstrado no escopo** = entrega executada com evidência; **parcial/em andamento** = parte do marco executada; **pendente** = sem entrega correspondente nesta trilha. A coluna de evidência informa o limite. Esses estados descrevem entregas técnicas dentro dos marcos; não certificam conclusão integral da formação. O painel principal explicita as partes faltantes. A avaliação de autonomia aparece no registro didático, adiante.

| ID | Marco | Ferramentas e operações | Estado técnico atual | Evidência e próximo ponto |
| --- | --- | --- | --- | --- |
| M00 | Fluxo e diagnóstico do projeto | VS Code, Python, chamadas, contratos e Git | Parcial; diagnóstico temporal aplicado | E13–E19; M00.2 ainda exige transferência independente |
| M01 | Dados e engenharia | pandas, NumPy, DuckDB/SQL, SQLite, PyArrow, pytest, joins e janelas | Série, contratos e agregação SQL autoral demonstrados | E71/E72: JOIN, CASE, agrupamento e nulos aceitos. E83: saída LAG corrigida aceita após recálculo independente. Autonomia e transferência a outro conjunto pendentes |
| M02 | Estatística e experimentação | Resíduos, MAE/RMSE/viés, comparação pareada, reamostragem temporal | Parcial; decisão apoiada em ganho e incerteza | E43: interpretação do extremo e decisão adequadas; confusão fold/bloco corrigida. Cruzar zero não prova dependência. Retenção/transferência e execução própria do bootstrap ainda pendentes |
| M03 | ML clássico e avaliação temporal | scikit-learn, Ridge/HGB, cortes, tuning, MLflow | h+1/h+6 e ablações h6/h24 demonstrados no escopo executado | E04/E07, E20–E25, E40/E41/E46; métricas e cortes h24 auditados. Defesa autônoma e avaliação independente futura pendentes |
| M04 | Meteorologia e múltiplos horizontes | HTTP/JSON/cache, UTC, as-of, pesos espaciais, pandas | h6/h24 comparados e inferência h24 reproduzida | E50 encerra a sexta macroentrega; E51 registra validação física autoral parcial e correção de nomes exatos. Contrato temporal operacional continua não verificado |
| M05 | Incerteza e eventos | Quantis, pinball, cobertura, classificação, Pipeline, Brier/AP, calibration bins e custo | Núcleo técnico e seleção autoral concluídos no desenvolvimento | E63: política correta sob capacidade120; aprendizagem continua por revisão de limites, sem reabrir a entrega técnica |
| M06 | Entrega e MLOps | CLI/MLflow Tracking, joblib, JSON, FastAPI/Uvicorn, SQLite, ASGI, wheel, pip, venv, Docker, PyInstaller, PowerShell e política temporal | E69–E94: entregas locais e cliente 1.1 aceitos; M06.5 encerrado | Registry MLflow, shadow ao vivo, CI remoto e monitoramento contínuo seguem separados; não reabrir entregas aceitas para impedir M07 |
| M07 | Dados em escala | PySpark, Spark SQL, Delta, Databricks | E103/E106/E108: três unidades executadas e conferidas | Escopo das unidades encerrado; plano/medição revisados. JSON do recibo separado não recebido, embora sua gravação conste da exportação; não bloqueia a progressão |
| M08 | Deep learning temporal | PyTorch, DataLoader, autograd, nn.Module, GRU | E110/E112/E114: três unidades técnicas aceitas; cinco testes do aluno e célula GRU conferidos | Consolidar defesa da decisão GRU/HGB no parecer seguinte; preservar limites de autoria e evidência. Não reabrir treino ou implementação aceitos |
| M09 | Transformers | Atenção NumPy/PyTorch, encoder–decoder, Chronos-Bolt Tiny | E119: execução Windows e alinhamento recebidos e auditados; E117 composição relatada | Consolidar parecer próprio, sem refazer experimentos. Técnica recebida permite iniciar M10.1; corpus de pré-treino/overlap e operação não certificados |
| M10 | Telemetria e anomalias | PCA, IsolationForest, métricas por evento | E120: M10.1 preparada/executada pelo professor, aluno pendente | Produto P2 iniciado pela entrega do contrato ESA; comparação de detectores e avaliação ainda não executadas |
| M11 | LLMs e IA generativa | Tokenização, geração, JSON/Pydantic, PEFT/LoRA | Pendente | Aplicação generativa avaliada ainda sem entrega |
| M12 | RAG | TF-IDF, embeddings, Qdrant, reranking | Pendente | Recuperação e resposta avaliadas separadamente ainda sem entrega |
| M13 | Agentes e LLMOps | Ferramentas tipadas, SQL parametrizado, estado, LangGraph | Pendente | Produto P3 com ferramentas e avaliação ainda sem entrega |
| M14 | Defesa, pesquisa e decisão | Reprodução, ablação, otimização e relatório | Pendente | A ablação de M03/M04 é prática preparatória; defesa final não realizada |

Dependências: M00 → M01 → M02 → M03 → M04 → M05 → M06 → M07 → M08 → M09 → M10 → M11 → M12 → M13 → M14. A ordem conserva um projeto ativo e reaproveita dados, avaliação e infraestrutura. O professor pode reconhecer equivalência de uma unidade já dominada, registrando a prova, sem renumerar a trilha. Revisões de retenção continuam durante marcos posteriores.

**Unidades, entregas e provas de autonomia**

Os destinos abaixo são relativos à raiz de cada projeto. Esta seção define o currículo; o estado de execução está na matriz atual e nas evidências. Caminhos de entregas futuras não significam arquivos já criados. Em módulos existentes, apontar para a função real antes de solicitar edição.

**M00 — recuperar o fluxo, sem reiniciar o ambiente.**

- **M00.1:** seguir uma previsão h+1 da CLI até `predict_next`; identificar arquivo de entrada, instante da previsão, variáveis, modelo e saída. Ferramentas: navegação do VS Code, leitura de Python e metadados do modelo.
- **M00.2:** explicar uma função e adaptar um caso pequeno sem solução pronta. Registrar o apoio utilizado. Resultado: `docs/learning/checkpoint.md`, referenciando evidências existentes.
- **Prova:** mostrar onde verificar o horizonte e como descobrir se o último valor da geração já seria conhecido. A dúvida vira unidade de ensino; não se cria uma nota zero por ausência de registro.
- **Léxico:** módulo, função, argumento, entrada, artefato, execução, evidência.

**M01 — preparar dados que possam ser defendidos.**

- **M01.1:** escrever uma consulta SQL de cobertura e unicidade; comparar com uma transformação pandas. Aprender `SELECT`, `WHERE`, `GROUP BY`, `JOIN`, `LAG/OVER`, chaves, granularidade, tipos e nulos.
- **M01.2:** usar `data_contract` existente para compreender schema drift, normalização de nomes/tipos e leitura Parquet; separar problema do dataset bruto de problema da série selecionada. Examinar filtro de linhas/colunas e plano de consulta quando relevante.
- **M01.3:** extrair uma transformação para função, parametrizar caminho/identificador, tratar entrada inválida e escrever teste com resultado calculado independentemente. Reexecutar sem duplicação silenciosa.
- **Entrega:** série horária existente revalidada, `docs/data_card.md` e relatório em `reports/data_quality/`.
- **Prova:** aplicar o contrato a outro mês ou identificador, explicar discrepâncias e diagnosticar uma duplicidade ou ausência real. A dificuldade é justificar o tratamento, além de rodar a consulta.
- **Léxico:** schema, chave, granularidade, dtype, null, join, window, idempotência.

**M02 — ligar os números às conclusões.**

- **M02.1:** calcular resíduos, MAE, RMSE e viés com NumPy; identificar unidades e efeito de erros extremos; produzir gráfico temporal e análise de autocorrelação com statsmodels.
- **M02.2:** relacionar álgebra linear e otimização à regressão: forma de X/y, produto matricial, erro quadrático, gradiente e regularização. Comparar um cálculo pequeno com a biblioteca.
- **M02.3:** formular hipótese e estimativa de ganho; fazer comparação pareada respeitando dependência temporal, estudar bootstrap em blocos e sensibilidade ao tamanho do bloco. SciPy fornece componentes estatísticos, mas chamar um bootstrap genérico não resolve dependência temporal automaticamente.
- **M02.4:** distinguir associação de causalidade, intervalo para uma estatística de intervalo preditivo e exploração de teste confirmatório. Definir separação de desenvolvimento/validação/teste antes da próxima seleção.
- **Entrega:** `reports/statistical_audit.md`, gráfico de erros e protocolo com hipótese, recorte e limitações.
- **Prova:** explicar por que MAE menor e intervalo do ganho cruzando zero não bastam para concluir superioridade; reanalisar outro período sem mudar a hipótese depois de ver o resultado.
- **Léxico:** população, amostra, estimador, resíduo, viés, dependência, intervalo de confiança, hipótese, efeito.

**M03 — compreender e reproduzir a avaliação temporal h+1/h+6.**

- **M03.1:** reconstruir lags, janelas e calendário a partir de uma tabela temporal; documentar a convenção do timestamp e a disponibilidade de cada atributo.
- **M03.2:** comparar persistência, referência sazonal, Ridge e HGB; usar `Pipeline` para ajustar transformações somente no treino. Um modelo estatístico com statsmodels pode ser acrescentado como comparação justificada, não como coleção de algoritmos.
- **M03.3:** implementar ou auditar rolling-origin, tuning separado do teste, métricas por fold/mês e ablação de grupos de features. Ajustar cortes ao instante em que rótulos de treino estão disponíveis.
- **M03.4:** examinar a correção prequential, importar o resultado de governança e rastrear parâmetros, dados, métricas e artefatos no MLflow. Interpretar importância de atributos e sua instabilidade sob correlação; SHAP fica como aprofundamento se responder a uma pergunta concreta.
- **Entrega:** benchmark existente reproduzido em `reports/backtest/` e decisão em `docs/model_card.md`, com referência ao run e à versão dos dados.
- **Prova:** remover um grupo de variáveis, prever o efeito, executar o experimento e defender a conclusão. Se o histórico já orientou muitas escolhas, ele não deve ser reapresentado como teste intocado.
- **Léxico:** baseline, persistência, feature, lag, fit, predict, pipeline, fold, holdout, ablação.

**M04 — dataset meteorológico real e multi-horizonte.**

- **M04.1:** confirmar vínculo entre conjunto e parques, coordenadas, capacidade, unidade e vigência cadastral; documentar qualquer aproximação espacial. Fechar uma pequena amostra real da fonte de forecasts antes de prometer o ano completo. Conferir cobertura, variáveis, granularidade, acesso e limites vigentes.
- **M04.2:** consultar uma rodada com um cliente HTTP; compreender parâmetros, JSON, status, timeout, retry e cache. Preservar resposta original, provedor/modelo, inicialização, validade, coleta e disponibilidade observada ou estimada.
- **M04.3:** construir a chave `(conjunto, issue_time, horizon)` para h+1/h+6/h+24. Selecionar a rodada elegível mais recente por parque/modelo/horário válido; verificar cardinalidade, duplicidades e ausência. Uma junção as-of exige as chaves corretas, além da desigualdade temporal.
- **M04.4:** produzir componentes u/v e agregações por capacidade, inclusive dispersão espacial. Documentar unidades e aproximação da densidade do ar; calcular o proxy físico por parque antes de agregar quando essa for a definição escolhida.
- **Entrega:** `data/reference/` com cadastro e proveniência, previsões normalizadas em `data/interim/` e `data/processed/model_table_multihorizon.parquet`; módulos e testes integrados ao pacote existente.
- **Prova:** inserir, em um teste isolado, uma rodada publicada depois da emissão; ela deve ser rejeitada. Alterar latência, retirar um parque e explicar seleção, cobertura espacial e política de dados ausentes.
- **Regras:** `weather_available_at <= issue_time`; cada atributo de geração também deve estar disponível; `valid_time = issue_time + horizon`. A inicialização do modelo meteorológico, sozinha, não prova disponibilidade. Reanálise e meteorologia futura realizada recebem escopo retrospectivo próprio.
- **Léxico:** issue time, valid time, model initialization, available at, horizonte, lead time, as-of, latência, point-in-time.

**M05 — probabilidades, intervalos e eventos.**

- **M05.1:** treinar HGB para P10/P50/P90 e avaliar pinball loss, cobertura, largura e cruzamento de quantis. Calibração utiliza apenas dados anteriores elegíveis; a mediana P50 não é a moda.
- **M05.2:** comparar por horizonte: persistência, autorregressivo, meteorologia média e meteorologia espacial, sob os mesmos cortes e amostras comparáveis. Descrever o recorte que sobra por ausência de meteorologia.
- **M05.3:** formular evento de queda com limiar físico explícito no desenvolvimento; primeiro contrato aplicado em E60 compara y(t+24) com o último disponível y(t−2), sem chamá-lo de rampa horária ou ocorrência em qualquer ponto da janela. Comparar regressão logística e um challenger com precision, recall, Average Precision, Brier e diagnóstico de calibração. Separar limiar do evento de limiar de decisão; não selecionar uma regra operacional no teste.
- **Entrega:** `reports/probabilistic/`, previsões por linha e experimento de eventos. LightGBM/CatBoost são candidatos de aprofundamento; não são pré-requisitos simultâneos.
- **Prova:** explicar o custo de aumentar recall e a diferença entre bom intervalo e intervalo excessivamente largo. Três quantis não determinam, sozinhos, uma probabilidade exata de queda maior que 40 MW.
- **Léxico:** quantil, mediana, pinball loss, cobertura, largura, threshold, precision, recall, calibração.
- **Checkpoint E63:** seleção autoral implementada e aceita; revisão da distinção entre limite amostral e cota futura prossegue em M06. A função atende ao cenário120 alarmes sem reinterpretar o resultado como aprovação operacional.

**M06 — entregar e observar o produto.**

- **M06.1:** artefato e inferência aceitos em E69. **M06.2:** lote, idempotência e conciliação reproduzidos em E71; SQL autoral e falha orientada aceitos em E72. **M06.3/E74–E76:** monitor e recálculo corrigido reproduzidos; revisão encerrada no escopo demonstrado. **E80:** diagnóstico HTTP corrigido reproduzido; unidade encerrada no escopo demonstrado. **E81:** registro SQLite, ativação, concorrência, readiness e rollback entregues; **E82:** tentativa autoral com LAG recebida; correção de contrato/granularidade/cadeia entregue e conferida na réplica. **E83:** retomada, registro/rollback e saída SQL corrigida aceitos nos anexos; parecer independente pendente. E85 aceita execução Windows e orçamento autoral de E84; revisão do parecer é localizada. E87 aceita migração Linux executada pelo aluno e conferida pelos nove anexos; não reabre a execução de compatibilidade. E88 entregou concorrência; E89 aceita a autoria de seleção e registra o console do aluno com limites de inferência. E91 aceita a execução do cliente Windows e o lançador 1.0; E92 aceita a regra temporal autoral. E93 entregou a integração e E94 aceita a reprodução Windows 1.1 após auditoria dos oito anexos. CI remoto continua pendente. Aceites locais não equivalem a operação ao vivo.
- **M06.2:** executar previsão em lote e persistir entradas/saídas; registrar os resultados observados quando disponíveis. Operar em shadow significa registrar previsões sem substituir a decisão vigente.
- **M06.3:** rastrear no MLflow dados, código e modelo; compreender tracking versus registry, promover uma versão por critérios explícitos e ensaiar retorno à anterior.
- **M06.4:** containerizar com Docker e verificar mudanças com GitHub Actions; entender imagem, container, volume, variável de ambiente, job e artefato. Medir falhas, latência e erro posterior; investigar drift sem concluir automaticamente perda de qualidade.
- **M06.5/E90–E94:** unidade local encerrada. E94 aceita cliente 1.1 no Windows: replay/0, pedido vencido/7, inválido/2, identidade/4, API ausente/3, sete hashes coincidentes e diferença de probabilidade zero. Implantação cloud e operação ao vivo permanecem entregas separadas. Próxima unidade efetiva: M07.1.
- **Entrega:** API, tarefa em lote, relatório de shadow, monitoramento, instrução de recuperação, CI e utilitário. O teste do `.exe` deve ocorrer em Windows; sucesso em Linux não o substitui.
- **Prova:** reproduzir a previsão, recuperar versão anterior, identificar uma falha pelos logs e demonstrar entrada inválida tratada. Aprovação para shadow e shadow executado têm evidências distintas.
- **Léxico:** schema de API, endpoint, validação, serialização, run, registry, imagem, container, CI, shadow, drift, rollback.

**M07 — aprender a decidir quando distribuir o processamento.**

- **M07.1/E95–E103 — entrega técnica aceita:** tabela real, calendário, plano, janelas e seleção por disponibilidade executados. E103 compara os Parquets e confere todas as linhas. A defesa pendente pode ser consolidada na interpretação de revisões em M07.2, sem novos bloqueios de calendário ou contagem.
- **M07.2/E104–E106 — entrega técnica encerrada:** Delta reproduzido no Windows e planejador autoral confrontado com impacto real do CSV; sete origens e duas linhas do treino. Código autoral reconhecido; chamada de conferência escrita pelo professor. Interpretação de versões consolidada no parecer M07.3, sem repetir execuções ou adicionar outro exercício separado.
- **M07.3/E107–E108 — encerrada no escopo demonstrado:** notebook Databricks exportado e parecer recebidos. Código das sete células igual ao distribuído, 8.760/7.485 linhas e zero divergências em 2/4 partições solicitadas; tabelas/versões e limites temporais registrados. Interpretação de snapshots e decisão local/cloud aceitas; Exchange 10/broadcast, janela das 03h, duração, JIT/Photon e AQE corrigidos por revisão orientada. Recibo separado não recebido; exportação registra sua gravação. Não exigir repetição do ambiente nem do experimento.
- **Entrega:** código da transformação, resultado comparável e `reports/scale_comparison.md`.
- **Prova:** explicar um shuffle no plano, modificar o particionamento e discutir por que Spark pode ser mais lento no recorte pequeno. Execução local de Spark não certifica uso de Databricks.
- **Léxico:** lazy evaluation, action, partition, shuffle, execution plan, transaction, Delta, job.

**M08 — aprender o treinamento de uma rede.**

- **M08.1/E109–E110 — aceita com assistência:** função NumPy e parecer recebidos; fórmula, shapes, preservação de entradas e diferenças finitas conferidos. O relato Windows distingue convergência, instabilidade e viés; autoria assistida declarada. Arquivos brutos das três execuções Windows não recebidos. Não repetir a unidade nem certificar independência por igualdade numérica.
- **M08.2/E111–E112 — aceita no escopo assistido:** avaliar_lotes e parecer recebidos; ponderação por exemplos, eval/no_grad, modos mistos e exceções conferidos por execução. Relato Windows de 05/11: divisão7.079/168/168, exclusões52+18, seleção de época e todas as sementes; MAE medianoMLP33,159788 contra linear33,678664 MWmed. Decisão de manter linear como referência aceita. Arquivos Windows não anexados; não alegar auditoria de hashes ou autoria independente. Não repetir esta unidade.
- **M08.3/E113–E114 — execução e implementação aceitas:** runWindows20261115T164955Z_5e435b09, nove arquivos recebidos; oito hashes,27 métricas,partições/curvas reconciliados. Célula NumPy e cinco testes executados e aprovados; comparação GRUCell/24passos em float64 aprovada. HGB localMAE32,323956, diferente da referência Linux por causa não isolada. Seis recarregamentos zero constam do recibo, sem pesos Windows anexados. Defesa da decisão pelo aluno ainda não recebida; pode ser consolidada com atenção, sem repetição de treino.
- **Entrega:** modelo reproduzível em `src/` e curva de treino/validação em `reports/neural/`.
- **Prova:** explicar batch, shape, gradiente e diferença entre `train()` e `eval()`; diagnosticar sobreajuste, erro de dimensão e vazamento na normalização.
- **Léxico:** tensor, shape, batch, forward, loss, gradient, backward, optimizer, epoch, checkpoint.

**M09 — atenção e modelo fundacional.**

- **M09.1/E115–E116 — execução e implementação aceitas no escopo recebido:** modos normais Windows relatados, código NumPy e seis casos executados nesta revisão; comparação PyTorch oito grupos aprovada. CLI antiga --autoria exige caminho do arquivo; erro de argumento não invalida a função. Interpretação pode integrar o parecer M09.3, sem repetir código.
- **M09.2/E117 — composição recebida e reprodução relatada:** runner/verificador anexados compilam e foram revisados; logs Windows de13 grupos, encoder[1,24,16], decoder[1,6,16],11.200 parâmetros e deltas zero de prefixo/reload. Módulo dos blocos não anexado; sem auditoria completa ou reexecução independente. Os slots são sintéticos, não previsões; nenhum fit. Avançar para pesos pré-treinados.
- **M09.3/E118–E119 — execução e alinhamento aceitos:** Chronos-Bolt Tiny congelado,26 passos para h24/d2. Execução Windows normal20261117T212230Z_965de3d1: onze hashes e30 métricas conferidos,1.512 previsões anteriores preservadas; função em texto passou cinco grupos e seleção no NPZ real. MAE31,340738 versusHGB32,323956, ganho3,041763%; RMSE piora2,619649%. Parecer próprio citado mas não anexado. Segunda rodada213329Z tem recibos auxiliares, sem resultado completo recebido. Não repetir inferência para avançar; registrar esses limites.
- **Entrega:** cálculo de atenção explicado e relatório comparativo em `reports/transformer/`.
- **Prova:** explicar o efeito de uma máscara errada e adaptar contexto/horizonte sem misturar dados futuros. Uso de pesos pré-treinados não comprova ausência de sobreposição com dados de pré-treino desconhecidos.
- **Léxico:** attention, query, key, value, embedding, position, mask, encoder, decoder, pretrained.

**M10 — transferência para telemetria satelital.**

- **M10.1/E120 — ativa, referência entregue e executada:** satellite-anomaly-monitor com recorte ESA Mission1v2/2007, canais50–52. Busca causal, idade máxima180s, grade90s, anotações preservadas e separadas das features. Cinco contraprovas e busca independente NumPy no recorte real aprovadas em Linux. Execução/autoria do aluno pendentes. Recorte exploratório com três IDs de anomalia: não é benchmark oficial nem evidência de detector.
- **M10.2:** comparar um escore estatístico robusto, PCA por reconstrução e Isolation Forest; usar agrupamento apenas como investigação de contextos, sem assumir significado físico dos clusters.
- **M10.3:** selecionar limiares na validação, medir precisão/recall por evento, falsos alarmes por tempo, atraso e desempenho por canal. Separar eventos e janelas para evitar contaminação entre partições.
- **M10.4:** investigar contribuições de canais, estabilidade e uma ablação. Incluir rede temporal ou autoencoder somente após a comparação dos baselines.
- **Entrega:** detector reutilizável, data/model card e relatório de erros/eventos; aproveitar o padrão de serviço já aprendido.
- **Prova:** adaptar o detector a outro canal, justificar limiar e explicar por que escore, probabilidade, severidade e diagnóstico físico são grandezas diferentes.
- **Léxico:** anomaly score, reconstruction error, threshold, event, prevalence, false alarm, detection delay, attribution.

**M11 — LLMs e IA generativa como unidade explícita.**

- **M11.1:** inspecionar tokenização e embeddings; executar geração com um modelo compatível com os recursos, controlando contexto, parâmetros e orçamento. Estudar quantização com uma comparação medida quando tecnicamente viável.
- **M11.2:** produzir um relatório estruturado a partir de métricas fornecidas; validar JSON e campos com Pydantic; avaliar fidelidade numérica, informação omitida e afirmações sem evidência. Comparar prompts sobre conjunto de desenvolvimento, com teste reservado.
- **M11.3:** realizar uma pequena adaptação com PEFT/LoRA quando houver pares de treino e tarefa delimitada; comparar com modelo sem ajuste e com prompting. QLoRA fica como extensão condicionada a hardware e orçamento; registrar explicitamente caso ainda não executada.
- **Entrega:** aplicação estruturada, conjunto de avaliação, saídas e comparação em `operations-evidence-assistant`.
- **Prova:** escolher entre prompting, recuperação e ajuste de pesos para uma necessidade concreta; explicar por que JSON válido não assegura conteúdo verdadeiro.
- **Léxico:** token, context window, decoding, temperature, structured output, hallucination, quantization, fine-tuning, LoRA.

**M12 — recuperação e respostas com evidências.**

- **M12.1:** versionar um corpus dos próprios projetos; criar perguntas com referências corretas, casos sem resposta, fontes conflitantes e documentos desatualizados. Separar desenvolvimento e teste por família/documento quando necessário.
- **M12.2:** comparar busca lexical TF-IDF e embeddings Sentence Transformers; armazenar vetores e metadados em Qdrant local; implementar filtro, top-k, combinação das buscas e uma avaliação de reranking.
- **M12.3:** gerar respostas com trechos citados; medir recuperação separadamente da geração, incluindo recall@k, correção das citações, sustentação das afirmações e recusa por falta de evidência.
- **Entrega:** corpus e índice identificáveis, pipeline RAG e relatório de avaliação. A busca lexical deste marco não é o método léxico de estudo descrito adiante.
- **Prova:** mostrar se uma resposta errada veio da busca ou da geração, corrigir uma causa e reavaliar casos reservados; alterar chunking sem perder a referência ao documento original.
- **Léxico:** corpus, chunk, overlap, embedding, retrieval, top-k, reranking, grounding, citation.

**M13 — agentes, ferramentas e LLMOps.**

- **M13.1:** implementar ferramentas tipadas para consultar previsões, métricas e documentos; validar argumentos e usar consultas parametrizadas com permissões restritas.
- **M13.2:** comparar um fluxo determinístico em Python com agente de estado explícito em LangGraph; estabelecer limites de passos/tempo/custo e condições de revisão humana.
- **M13.3:** registrar chamadas, versões, saídas, falhas e custo/latência; testar indisponibilidade, argumento inválido, documento com instruções indevidas e repetição de chamadas. Usar rastreamento já adotado quando suficiente.
- **Entrega:** agente de consulta, conjunto reservado de tarefas e relatório de sucesso/falhas. Nenhuma ação física em equipamentos faz parte do escopo.
- **Prova:** reproduzir uma falha pelo rastro, impedir ciclo sem término e justificar quando o fluxo determinístico é suficiente. O agente deve manter os números retornados pelas ferramentas.
- **Léxico:** tool call, schema, state, transition, checkpoint, trace, timeout, retry, human-in-the-loop.

**M14 — defender a solução e avaliar decisão sob restrições.**

- **M14.1:** reproduzir um método/artigo delimitado e executar uma ablação. Documentar recorte, hipótese, protocolo, recursos e diferenças em relação ao estudo original.
- **M14.2:** formular um pequeno problema de decisão com regra ou otimização, usando SciPy optimize quando adequado; explicitar objetivo, restrições, cenários de incerteza e hipótese sobre custos. Cenários simulados permanecem identificados.
- **M14.3:** entregar relatório técnico, instrução de reprodução e defesa: alternativas, falhas, custo, limites causais e evidência necessária para uso real. Registrar uma avaliação de uso e uma melhoria decorrente dela.
- **Entrega:** `reports/final_report.md`, experimento reproduzível, estudo de decisão e portfólio dos três produtos.
- **Prova:** responder a um novo recorte ou restrição, adaptar a solução e defender a decisão com evidências. Um artigo aceito ou um título de cargo não é requisito inventado para encerrar a aprendizagem.
- **Léxico:** reproduction, ablation, sensitivity, objective, constraint, scenario, external validity, trade-off.

**Profundidade e limites do conjunto de ferramentas**

A base a dominar é Python, SQL, NumPy/pandas, validação estatística, scikit-learn, teste/depuração e comunicação. A autonomia aplicada se estende a MLflow, APIs, containers, processamento distribuído e entrega. Deep learning, Transformers e GenAI formam a especialização posterior. Não será necessário aprender Kubernetes, múltiplas clouds ou vários frameworks de agentes para cumprir esse escopo.

Novas bibliotecas entram somente com operação concreta, entrada, saída e exercício definidos. A versão instalada é conferida antes de fornecer código executável. Nenhum marco exige atualização indiscriminada do ambiente. Git registra o trabalho; acesso remoto do professor ao GitHub não é pré-requisito didático.

**Método léxico de fixação — definição operacional adotada**

Não foi localizada no histórico uma definição sua mais específica para esse método. Neste roteiro, ele significa construir vocabulário técnico em português/inglês conectado à operação, à decisão e ao erro. Essa organização é uma proposta didática; não é apresentada como um método científico padronizado com esse nome.

Cada termo ganha uma ficha curta com sete campos:

| Campo | Conteúdo obrigatório |
| --- | --- |
| Nome | Termo em inglês e equivalente/explicação em português |
| Significado próprio | Uma ou duas frases escritas pelo aluno |
| Problema que resolve | Quando usar e qual decisão permite tomar |
| Operação | Função, argumento, consulta ou trecho real do projeto |
| Evidência | Arquivo, função, saída e teste que demonstram o conceito |
| Confusão e contraexemplo | Um uso aparentemente correto que produz erro conceitual |
| Recuperação e transferência | Pergunta sem consulta e uma variação ainda não resolvida |

Os pares de contraste fazem parte do vocabulário: `fit/predict`, `treino/teste`, `issue_time/valid_time`, `model_init/available_at`, `parâmetro/hiperparâmetro`, `IC/intervalo preditivo`, `escore/probabilidade`, `imagem/container`, `retrieval/generation`, `workflow/agent`. O aluno deve explicar uma consequência prática da distinção.

**Ciclo de fixação por unidade**

1. **Nomear e reconhecer:** identificar até cinco termos centrais na documentação e no código real.
2. **Explicar:** dar a definição com palavras próprias e localizar entrada/saída; o professor corrige imediatamente o entendimento.
3. **Aplicar:** escrever ou modificar a operação essencial antes de receber a solução completa.
4. **Distinguir:** analisar um contraexemplo e dizer qual resultado denunciará o erro.
5. **Recuperar:** fechar a referência e reconstruir a ideia, a sequência lógica e um caso pequeno. Consultar assinatura de biblioteca é permitido na etapa profissional, com registro; a ficha lexical é respondida inicialmente de memória.
6. **Transferir:** resolver outra janela, usina, variável, restrição ou tipo de documento e justificar a adaptação.

Recuperação ativa e estudo espaçado têm suporte em pesquisas sobre retenção. O uso específico deles nesta trilha de programação é uma adaptação didática; não se deduz uma garantia de domínio profissional desses estudos. Referências: [Roediger e Karpicke, 2006](https://pubmed.ncbi.nlm.nih.gov/16507066/) e [Cepeda et al., 2008](https://pubmed.ncbi.nlm.nih.gov/19076480/).

Revisões sugeridas: **ao final da aula, após 1, 3, 7, 14 e 30 dias**. Esses intervalos são uma convenção inicial ajustável, não uma agenda universal validada. Em caso de erro, corrigir e reapresentar um caso diferente na próxima sessão; em caso de acerto com aplicação, alongar o intervalo. O tempo de revisão está dentro da carga semanal. Não acumular dívida de dezenas de cartões.

| Revisão | Evidência esperada |
| --- | --- |
| Final da aula | Explicação própria e operação realizada |
| D+1 | Recuperar significado e um erro comum, sem abrir a resposta |
| D+3 | Reconstruir a operação essencial e prever sua saída |
| D+7 | Resolver um caso diferente sem solução pronta |
| D+14 | Explicar uma escolha entre alternativas e sua limitação |
| D+30 | Reusar o conceito em outra parte do projeto e registrar retenção |

**Ficha preenchida como exemplo, ainda sem nota atribuída ao aluno**

| Campo | `available_at` — instante de disponibilidade |
| --- | --- |
| Significado | Momento a partir do qual uma informação pode ser usada pela previsão operacional |
| Problema | Simular somente a informação acessível na origem da decisão |
| Operação | Filtrar `available_at <= issue_time` antes de selecionar a rodada elegível mais recente |
| Confusão | Uma rodada inicializada às 06h pode estar disponível apenas às 12h |
| Contraexemplo | Usá-la numa decisão às 10h porque 06h é anterior a 10h |
| Teste | Ao adicionar uma rodada ainda indisponível, o resultado selecionado para a decisão antiga permanece igual |
| Pergunta | “Foi inicializada às 06h e publicada às 12h. Posso usá-la às 10h? Qual campo decide?” |
| Transferência | Aplicar a mesma regra à publicação atrasada ou à revisão do dado de geração |

Exemplo manual para `issue_time = 10h`, horizonte de 6h e `valid_time = 16h`:

| Rodada | Disponível às | Previsão para | Elegível às 10h? |
| --- | --- | --- | --- |
| 00h | 06h | 16h | Sim |
| 06h | 12h | 16h | Não |

Se a geração das 09h só foi publicada às 11h, ela também não pode ser atributo dessa emissão. A última geração elegível pode ser a das 08h. Uma hipótese de disponibilidade imediata precisa estar explícita e ser tratada como limitação.

**Primeiras fichas para fixação**

| Termo | Pergunta de recuperação | Ação que demonstra compreensão |
| --- | --- | --- |
| Granularidade | O que exatamente uma linha representa? | Definir chave e detectar duplicidade sem confundir duas usinas |
| Schema | Qual diferença de tipo/nome pode mudar uma transformação? | Normalizar um caso documentado e preservar significado |
| Lag | A defasagem é por linha ou por hora? | Construir um lag e tratar o caso em que falta uma hora |
| Rolling window | Quais timestamps entram nesta média? | Listar os pontos e comparar com o resultado calculado |
| Baseline | Qual regra simples representa a referência desta decisão? | Reproduzir persistência com o último valor elegível |
| Leakage | Qual informação ainda não existia quando a previsão seria feita? | Encontrar e testar um caso de uso de informação futura |
| Fit | Qual informação é aprendida nesta chamada? | Mostrar em que partição a transformação é ajustada |
| Holdout | Este período já influenciou uma decisão? | Identificar contaminação por reutilização do teste |
| Intervalo de confiança | Qual estimativa e repetição estão sendo representadas? | Interpretar o intervalo do ganho sem confundi-lo com faixa de geração |
| Quantil | O que muda ao prever P10 e P90? | Associar perda, assimetria e cobertura observada |
| Shadow | O que o candidato faz sem substituir o modelo vigente? | Recuperar uma previsão registrada e compará-la ao realizado |
| Embedding | Que objeto o vetor representa e como será comparado? | Recuperar um trecho e avaliar relevância com referência humana |

**Formato de cada aula**

Uma unidade pode ocupar mais de um bloco. O formato de 40 minutos organiza atenção; não obriga que treinamento, transferência e retenção sejam concluídos em uma única sessão.

| Minutos | Responsabilidade do professor | Trabalho do aluno | Registro |
| --- | --- | --- | --- |
| 0–5 | Retomar a unidade e perguntar sobre o último conceito | Recuperar a ideia sem olhar a solução | Resposta e apoio necessário |
| 5–12 | Explicar o conceito e um exemplo curto com ligação ao projeto | Prever o resultado e formular dúvida | Hipótese escrita |
| 12–30 | Propor tarefa delimitada e dar pistas progressivas | Escrever, depurar ou modificar a parte central | Código e execução |
| 30–36 | Introduzir uma variação ou contraexemplo | Justificar o resultado e corrigir raciocínio | Explicação e teste |
| 36–40 | Dar feedback específico e atualizar o checkpoint | Registrar a ficha lexical e o que falta | Evidência e próxima ação |

A tarefa sempre informa **objetivo, pré-requisito, arquivo/função real, trecho a trabalhar, saída esperada e critério de aceitação**. A parte mecânica pode vir pronta; o algoritmo ou decisão alvo da aula deve conter trabalho autoral do aluno. Se pedir a solução completa, ela será fornecida, mas a autonomia continua pendente até uma variação independente.

Feedback obrigatório: o que está correto; qual erro ocorreu e por quê; qual evidência sustenta a correção; e qual tentativa vem em seguida. Problema do material do professor é registrado como correção do material, sem reduzir a nota do aluno. Antes de instruir execução, conferir interface, dependências e ambiente; distinguir verificação local de validação em Windows.

**Auditoria de aprendizagem**

Mantém-se a escala do roteiro original:

| Nível | Evidência exigida |
| --- | --- |
| N | Competência ainda não avaliada/documentada |
| 0 | Após explicação e tentativa válida, ainda não realiza o objetivo mesmo com apoio |
| 1 | Realiza com orientação, exemplo ou pistas substanciais |
| 2 | Explica e realiza com autonomia, podendo consultar documentação de referência |
| 3 | Adapta a uma situação nova e justifica escolhas e limitações |

Cada unidade recebe notas separadas de **explicação**, **implementação/uso**, **validação/diagnóstico** e **transferência**. Documentação consultada, sugestões e código gerado por IA são registrados. Zero só é usado após observação de uma tentativa; N não é convertido em zero.

Critério de avanço: artefato reproduzível; nota pelo menos 2 em explicação, implementação e validação; nenhuma falha crítica de entendimento temporal/estatístico; e tentativa de transferência corrigida. Critério de consolidação: transferência demonstrada em nível 3 e retomada independente em D+7. D+30 verifica retenção e pode reabrir a competência. As tarefas seguintes podem começar enquanto a revisão espaçada fica agendada.

Falha crítica aqui significa um erro que invalida a conclusão central, como treinar com futuro, ajustar no teste ou confundir saída do modelo com evidência observada. Se ocorrer, retomar o conceito e reavaliar com outro caso. Isso não exige reiniciar o projeto.

**Registro atual de aprendizagem — separado da entrega técnica**

| Marco | Evidência aplicada já registrada | O que ainda precisa de avaliação |
| --- | --- | --- |
| M00 | Explicação 2, implementação 2 e validação 2 nos cenários temporais E14–E19 | Transferência M00.2 e retomada independente |
| M01 | Pareamento temporal, pandas e série preparada; E71/E72: consulta SQL autoral e tratamento correto de nulos | Janelas SQL, transferência para outro recorte/conjunto e diagnóstico independente |
| M02 | E43: decisão de manter candidato em desenvolvimento, correção do extremo com persistência e necessidade de confrontar NWP com observação | Retomar mapeamento fold/bloco e significado de cruzar zero; distinguir observação meteorológica de atribuição exclusiva do erro ao NWP; transferência independente |
| M03 | Busca, folds, calibração, holdout, emissão e ablação E41 reproduzidos com orientação | Defesa dos cortes/seleção e decisão com incerteza; parâmetros congelados vieram de desenvolvimento que já incluiu julho |
| M04 | Pesos, atraso, equivalência espacial, ablações h6/h24 e artefato h24 reproduzidos; função geométrica entregue em E51 | Corrigir busca por substring para nomes exatos, explicar invariância à ordem e desigualdade vetorial; contrato temporal operacional ainda pendente |
| M05 | E55–E59: pinball/calibração; E61/E62: classificação e custos; E63: seleção autoral sob capacidade correta | Explicar por que109<=120 no desenvolvimento não garante cota futura; retomada de estabilidade/custos e transferência independente |
| M06 | E71/E72: lote/SQL; E74/E76: monitor/parecer; E80: diagnóstico HTTP corrigido reproduzido | E81 propõe transferência para controle de versões: alias versus processo, geração, atomicidade e recuperação. E83: execução do aluno recebida e saída da consulta orientada reconciliada; parecer independente ainda pendente. Telemetria contínua, Registry MLflow, CI e distribuição posteriores |
| M07 | E103/E106/E108: temporal, revisão Delta e reprodução Databricks; parecer de snapshots/local-cloud recebido | Escopo das unidades concluído. Interpretação de plano/medição corrigida pelo professor; transferência autônoma a múltiplas séries/escala não demonstrada |
| M08–M09 | E114/E116/E117/E119: redes, atenção, composição e transferência pré-treinada recebidas no alcance documentado | Execução e alinhamento M09.3 aceitos; defesa própria integrada ainda não anexada. Não repetir unidades técnicas aceitas. Autoria independente/retomada não certificadas |
| M10–M14 | E120 prepara e executa referência M10.1; M11–M14 seguem sem entrega prática | Aluno executa contrato ESA no P2; detectores, LLMs, RAG, agentes e defesa final posteriores |

Não se atribui uma nota global por marco sem observar suas provas. A ausência de avaliação de transferência não transforma uma entrega técnica executada em “não iniciada”.

Modelo de registro de tentativa, a preencher apenas depois da prática:

| Campo | Valor a registrar |
| --- | --- |
| Data, unidade, tentativa e minutos | Quando ocorreu; por exemplo M04.3, tentativa 1 |
| Pergunta e resultado previsto pelo aluno | Antes de executar |
| Evidência de produto | Arquivo/função, versão ou hash local, dados, configuração e saída; commit quando disponível |
| Apoio utilizado | Documentação, pista, trecho fornecido ou solução de IA |
| Resultado observado | Valor/saída ou erro real, sem reescrever retroativamente a hipótese |
| Explicação / implementação / validação / transferência | N ou 0–3, com uma frase de justificativa para cada nota |
| Termos lexicais | Até cinco, ligados às operações realizadas |
| Feedback e correção | Causa do erro; evidência; alteração e resultado |
| Revisão | Data prevista/real, pergunta e resultado em D+1/D+3/D+7/D+14/D+30 |
| Próxima ação | Entregar uma unidade completa com problema, teoria, implementação, experimento, autoria e critério de conclusão; consultar o checkpoint atual |

As tentativas anteriores permanecem no registro. Nota melhor não apaga dificuldade anterior; alteração de material do professor recebe motivo e data. Conclusões históricas ficam ligadas à versão que foi realmente executada.

O progresso será informado como **unidades avaliadas**, **unidades consolidadas** e **entregas aceitas**, sempre com denominador e evidências. Contagem de arquivos, bibliotecas instaladas, commits ou páginas lidas não mede aprendizagem. Não existe percentual auditável de “senioridade”.

**Ritmo, continuidade e retomada**

- **Ajuste de condução em 25/10/2026:** organizar aulas em problemas completos, com todos os passos disponíveis no início e encerramento definido. Exemplos mínimos servem para esclarecer uma dificuldade dentro da unidade; não serão apresentados como sucessivos avanços de marco. Revisões já demonstradas serão incorporadas ao trabalho aplicado. Este ajuste não acrescenta marcos nem certifica domínio por execução de código fornecido.

- Reserva inicial: 12 blocos de 40 minutos = 8 horas semanais, distribuídos em conceito/recuperação, implementação/investigação e revisão. Até quatro horas adicionais são opcionais.
- O tempo restante será reestimado após três unidades realmente avaliadas. Domínio demonstrado gera dispensa; uma lacuna abre trabalho focalizado.
- Antes de cada aula, ler o checkpoint e a última tentativa. Começar pela unidade ativa, preservando o objetivo e as decisões já registradas.
- Uma mudança de ferramenta registra problema, motivo e impacto. Ela não substitui silenciosamente os marcos nem apaga o trabalho concluído.
- Se uma conexão ou instalação impedir a ferramenta, trabalhar na parte independente da unidade e registrar a parte técnica pendente. Não declarar a ferramenta aprendida por uma simulação.
- Contratação de GPU/API/cloud é uma decisão posterior com necessidade e orçamento explícitos. O escopo inicial permanece executável em CPU e dados delimitados.





**Diário histórico das sessões — leia cada estado na data do registro.** As expressões “próximo passo”, “pendente” e os percentuais abaixo descrevem aquela sessão; o painel e o checkpoint no início concentram o estado atual. Evidências posteriores podem encerrar as pendências antigas.

M00.1 tem uma saída concreta: apontar a chamada da CLI e a função `predict_next` referenciada em E05, e explicar **entrada → instante da decisão → atributos elegíveis → modelo → saída**. O professor usa essa explicação para dispensar ou localizar as partes necessárias de M01–M03. Não há comando de instalação ou recomeço do projeto nesta retomada. A leitura do módulo enviado já iniciou essa unidade. O aluno explicou corretamente disponibilidade temporal, target e horizonte e entregou a função de pareamento com testes. Explicação = 2; implementação = 2 e validação = 2 nos cenários entregues; transferência = N. Em 18/09/2026, o aluno apresentou 17 casos passando. Em 21/09/2026, entregou o calendário extraído, o adaptador de treinamento e 26 casos de teste. A falha inicial de coleta no ambiente base foi resolvida por ativação do ambiente existente com Python 3.12.13. O teste de equivalência passou a comparar por `target_time` e exigir cobertura completa. A execução seguinte registrou 47 testes aprovados e uma falha no backtest por ausência de `hour`; os casos supervisionados passaram. A execução seguinte, E19, confirmou 48 testes aprovados em 14,76s, encerrando essa regressão. A continuidade técnica passa a M03.3, já prevista no roteiro, para executar a busca e interpretar seus resultados. M00.2 permanece sem prova de transferência. Em 22/09/2026, E20 registrou 50 testes aprovados e o primeiro resultado real h+6 no desenvolvimento. O ganho de MAE foi 47,13%, com reprovação pelo critério atual de viés. Isso ainda não certifica desempenho no período reservado, retenção ou autonomia.

**Sessão M00.1 — iniciada em 17/09/2026**

- Evidência inicial recebida: E13, módulo enviado pelo aluno; no momento da abertura, ainda não havia tentativa resolvida.
- Trecho de estudo: `predict_next`, linha futura com target ausente, `build_feature_frame`, seleção de `FEATURE_COLUMNS` e `model.predict`.
- Constatações da leitura: a função carrega um modelo salvo; ordena o histórico; fixa o próximo timestamp em uma hora; acrescenta target `NaN`; solicita features sem exigir target; seleciona uma linha; calcula a previsão e aplica piso zero; retorna também persistência e diferença.
- Limite: `features.py` ainda não foi recebido. O deslocamento efetivo dos lags e as regras de remoção de linhas não foram verificados. Não há certificação de ausência de leakage.
- Léxico desta leitura: inferência, feature, target, horizonte.
- Exercício proposto: avaliar se trocar apenas `pd.Timedelta(hours=1)` por `pd.Timedelta(hours=6)` é suficiente para transformar o modelo em um previsor h+6; justificar pela relação entre horário, atributos e treinamento. Sem alterar o projeto nesta tentativa de raciocínio.
- Critério de revisão: localizar a mudança temporal, relacioná-la à construção da entrada e ao significado do modelo treinado, e apontar o que ainda depende de inspeção. O retorno do professor deve corrigir a justificativa, não só classificar a resposta como sim/não.
- Avaliação na abertura: N nas quatro dimensões; estado anterior à primeira resposta, preservado neste registro.
- Ação prevista na abertura: ler a justificativa do aluno, dar feedback específico e decidir o próximo trecho da mesma unidade. Executada no registro da tentativa 1 abaixo.

**M00.1 — tentativa 1 e feedback, 17/09/2026**

- Resposta do aluno, preservada literalmente:

> Se a parametrização para encontrar os melhores coeficientes estiver funcionão, sim, não deverá gerar outras demandas, mas não seria, pois a previsão para 6 horas deverá levar em conta seus prórpios momentos tais como, o resultado de especulação de ventos nas regioes

- Evidência de compreensão: o aluno associou o horizonte maior a condições futuras relevantes e sugeriu informação sobre vento.
- Lacuna identificada: a resposta ainda mistura otimização do modelo com definição do horizonte e não explicita quais informações estariam disponíveis no instante da previsão. A formulação é tentativa, não uma conclusão inequívoca de que tuning basta.
- Correção ensinada: no HGB deste módulo, a busca seleciona hiperparâmetros. Alterar o timestamp em `predict_next` não redefine o treinamento do modelo carregado. Para a estratégia direta, o exemplo didático compara atributos disponíveis às 10h → geração das 11h (h+1) com atributos disponíveis às 10h → geração das 16h (h+6). Essa comparação descreve o alinhamento necessário, sem afirmar que a implementação atual foi verificada.
- Disponibilidade temporal: uma previsão de vento válida para 16h pode ser uma entrada se já estiver disponível às 10h. Vento observado às 16h não estaria disponível nessa emissão. Meteorologia pode ajudar, mas não é condição obrigatória para produzir h+6.
- Limite técnico mantido: `features.py` não foi inspecionado. Não se afirma como seus lags são calculados nem que o treinamento ou a inferência estejam livres de vazamento. Se um atributo exigir geração das 15h para emitir às 10h, ele não poderá usar a observação futura.
- Avaliação da evidência atual: explicação = 1 (parcial, com orientação); implementação/uso = N; validação/diagnóstico = N; transferência = N. M00.1 permanece em andamento. O feedback do professor não conta como correção demonstrada pelo aluno.
- Fixação lexical: **feature** = entrada elegível no instante da emissão; **target** = valor que se quer prever; **horizonte** = distância entre emissão e horário previsto; **tuning** = busca de hiperparâmetros para uma tarefa já definida. O aluno aplicará esses termos ao caso seguinte.
- Próximo exercício: emissão às 10h para prever geração às 16h. A é previsão de vento para 16h, disponível desde 9h. B é previsão de vento para 16h, disponível apenas às 11h. Responder em uma frase qual pode entrar como feature e por quê, qual é o target e qual é o horizonte.
- Ação prevista após a tentativa 1: revisar a resposta ao mesmo caso e localizar o trecho necessário de construção de features. A resposta foi revisada na tentativa 2; a prática abaixo permite aplicar o conceito sem presumir o conteúdo de `features.py`.
- Duração e revisão espaçada: tempo gasto não registrado; nenhuma revisão espaçada realizada ou agendada automaticamente.

**M00.1 — tentativa 2 e passagem à aplicação, 17/09/2026**

- Resposta técnica do aluno, preservada literalmente:

> Posso usar **A** como feature, porque **ela já está disponível no momento da emissão da previsão (10h, tendo sido lançada às 9h), respeitando a linha do tempo do modelo e evitando o vazamento de dados do futuro (*****lookahead bias*****)**. Meu target é **a geração de energia das 16h** e meu horizonte é **h+6 (6 horas)**.

- Avaliação: resposta correta. Demonstrou o critério de disponibilidade no instante da emissão e identificou target e horizonte. Explicação = 2, restrita a esse caso; implementação/uso, validação/diagnóstico e transferência = N. Não houve teste de retenção. Não repetir exercícios de completar frases sobre o conceito já demonstrado.
- Feedback sobre o ensino: o aluno considerou as duas iterações simples e sem incremento prático, ressaltando custo de tokens. O professor reconheceu a inadequação do nível do exercício. A resposta subsequente exige aplicação ao código, contrato de dados e teste adversarial; não há novo roteiro ou certificado de competência ampla.
- Incremento proposto: `build_horizon_pairs(series, horizon_hours=6)`, tabela de emissão e alvo pelo horário exato. A saída possui `forecast_origin`, `target_time` e `target_generation`. Trata uma única série, como CJU_BA5EIGT. Ela ainda não é uma tabela completa de features nem um modelo h+6 treinado.
- Ligação com o módulo recebido: `train_final_model` usa `frame[FEATURE_COLUMNS]` e `frame["val_geracao"]`; a semântica temporal depende de `build_feature_frame`, ainda não inspecionado. O pareamento explícito prepara o alvo h+6 sem modificar o modelo existente.
- Ferramentas em aplicação: `pandas.to_datetime`, `Timedelta`, `merge` com validação de cardinalidade; `pytest` para casos que distinguem tempo real de posição da linha.
- Conceito adicional: `shift(-6)` desloca seis posições; só representa seis horas com uma grade horária adequada. Um join pelo horário exato não substitui um alvo ausente pela próxima observação.
- Destino proposto no computador do aluno: `C:\renewable-forecast-lab\src\renewable_forecast\supervised.py`. Testes: `C:\renewable-forecast-lab\tests\test_supervised.py`. Os arquivos no computador do aluno não foram criados pelo professor.

Núcleo demonstrado pelo professor, para uma entrada válida com uma única série e horizonte positivo:

```python
import pandas as pd


def build_horizon_pairs(series, horizon_hours=6):
    observed = series[["din_instante", "val_geracao"]].copy()
    observed["din_instante"] = pd.to_datetime(
        observed["din_instante"], errors="raise"
    )
    origins = observed[["din_instante"]].rename(
        columns={"din_instante": "forecast_origin"}
    )
    origins["target_time"] = (
        origins["forecast_origin"] + pd.Timedelta(hours=horizon_hours)
    )
    targets = observed.rename(columns={
        "din_instante": "target_time",
        "val_geracao": "target_generation",
    })
    return (
        origins.merge(
            targets, on="target_time", how="left", validate="one_to_one"
        )
        .sort_values("forecast_origin")
        .reset_index(drop=True)
    )
```

- Responsabilidade do aluno: adicionar recusa de timestamps ausentes e horizonte que não seja inteiro positivo (incluindo `bool`); provar a recusa de timestamps duplicados; escrever testes dos casos abaixo. O núcleo já usa `validate="one_to_one"` para impedir chaves repetidas. Ainda é preciso tratar timestamps nulos: o merge do pandas pode associar chaves nulas.
- Dados dos testes: 12 observações, de 01/01/2026 00h a 11h, com geração 100, 101, …, 111. Para a emissão de 00h e h+6: série completa → alvo 106; retirar 03h → alvo continua 106, enquanto `shift(-6)` apontaria 107; retirar 06h → alvo ausente. Cada retirada parte novamente da série completa.
- Evidência do professor: o núcleo foi executado com esses três cenários sintéticos, incluindo seis alvos finais ausentes na série regular. Resultados confirmados. Isso valida a demonstração sob suas hipóteses; não conta como implementação ou domínio do aluno e não usa dados reais.
- Critério de aceite da próxima entrega: função com contrato explícito, testes passando e saída do comando `python -m pytest tests/test_supervised.py -q`, executado na raiz `C:\renewable-forecast-lab`, no ambiente existente. O aluno enviará a função e os testes para revisão de causa, comportamento e generalização.
- Vínculo lexical: **forecast origin** → emissão; **target alignment** → pareamento com alvo no horário correto; **cardinality** → unicidade verificada pelo join; **label availability** → momento em que o alvo poderia ser conhecido no treino. A fixação será feita pela defesa do código e dos testes, sem nova atividade de completar frases.
- Próxima integração: ler o construtor real de features para associar somente entradas elegíveis à emissão. A validação temporal de h+6 também precisará excluir rótulos ainda indisponíveis na origem de validação; por exemplo, treino emitido às 9h com alvo das 15h não poderia usar esse alvo para um modelo disponível às 10h. O `TimeSeriesSplit` atual, sem `gap` explícito, não garante sozinho essa condição para a futura tabela h+6. Não se diagnosticou um vazamento no h+1 existente sem a inspeção restante.
- Referências verificadas: [pandas — merge](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html), [pandas — shift](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.shift.html), [scikit-learn — TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html).
- Estado ao encerrar este registro: exercício técnico proposto; nenhum treino h+6 executado; nenhuma alteração no repositório do aluno; M00.1 em andamento.

**M00.1 — tentativa 3: implementação entregue e revisão, 17/09/2026**

- Evidência recebida: E14. O aluno apresentou `build_horizon_pairs` com anotações de tipo; rejeição de horizonte booleano, não inteiro ou não positivo; checagens de nulos e duplicados antes de `pd.to_datetime`; pareamento pelo timestamp exato. Apresentou seis funções de teste: série completa, lacuna intermediária, lacuna no alvo, duplicidade, seis horizontes inválidos e timestamp ausente.
- Execução relatada pelo aluno: `python -m pytest tests/test_supervised.py -q` → `11 passed in 1.31s`. O tempo é da execução dos testes, não da aprendizagem. O professor não executou pytest no computador do aluno.
- Evidência de avanço: implementação e testes concretos entregues. O caso sem 03h distingue o join temporal de uma mutação por `shift(-6)`; o caso sem 06h exige ausência, impedindo substituição silenciosa pela hora seguinte. A proteção de horizonte contempla a particularidade de `bool` em Python.
- Avaliação delimitada: explicação 2 (evidência anterior); implementação 2 e validação 2 nos cenários entregues. Não há evidência de transferência independente ou retenção. Uma falha de robustez descoberta na revisão permanece pendente de aplicação pelo aluno; não invalida os resultados dos cenários já cobertos.
- Achado reproduzido: as strings `""` e `"NaT"` não são nulas na coluna textual, mas se convertem em `NaT` mesmo com `errors="raise"`. A validação anterior à conversão não as rejeita. No exemplo sintético do aluno, substituir o timestamp da terceira observação por cada uma dessas strings produz uma linha com `forecast_origin=NaT`, `target_time=NaT` e `target_generation=102.0`.
- Causa: o pandas pode associar chaves nulas entre si no merge. `validate="one_to_one"` verifica unicidade, não presença ou validade temporal. Logo, a chave nula única não é barrada pela cardinalidade.
- Ajuste recomendado: manter a validação do horizonte; substituir o bloco que começa nas validações de timestamp e termina na conversão por este trecho, dentro da função, antes de `origins`:

```python
    observed = series[["din_instante", "val_geracao"]].copy()
    observed["din_instante"] = pd.to_datetime(
        observed["din_instante"], errors="raise"
    )

    if observed["din_instante"].isna().any():
        raise ValueError("A coluna 'din_instante' contém valores ausentes ou nulos.")

    if observed["din_instante"].duplicated().any():
        raise ValueError("A coluna 'din_instante' contém timestamps duplicados.")
```

- O posicionamento da checagem de duplicados também passa a comparar instantes normalizados. A checagem anterior comparava representações; por exemplo, strings com `00:00:00` e `0:00:00` podem representar o mesmo instante. O merge já rejeitava essas duplicatas após a conversão, mas a checagem explícita passa a emitir a mensagem do contrato.
- Teste de regressão proposto para acrescentar ao arquivo existente, reutilizando a fixture do aluno:

```python
@pytest.mark.parametrize("missing_timestamp", ["", "NaT"])
def test_missing_timestamp_after_parsing_raises_error(
    synthetic_series, missing_timestamp
):
    df = synthetic_series.astype({"din_instante": "string"})
    df.loc[2, "din_instante"] = missing_timestamp

    with pytest.raises(ValueError, match="ausentes ou nulos"):
        build_horizon_pairs(df)
```

- Valor do teste: cobre o estado intermediário criado pela conversão e exige a mensagem da rejeição de nulos; não basta uma exceção genérica por outro motivo. São dois casos novos, levando a suíte apresentada de 11 a 13 casos após a inclusão.
- Verificação local do professor: pandas 2.2.3; falha reproduzida com a implementação enviada e ambos os valores textuais. Após reposicionar as checagens, os 11 cenários originais e os dois cenários novos foram verificados com `assert`/`try-except`, sem pytest. A mutação por `shift(-6)` retorna 107 no caso sem 03h, em vez de 106, confirmando o valor do teste do aluno. Esses resultados não são uma execução da suíte no ambiente do aluno e não provam que ele já aplicou a correção.
- Referências consultadas: [pandas — merge, inclusive associação de chaves nulas](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html); [pandas — to_datetime](https://pandas.pydata.org/docs/reference/api/pandas.to_datetime.html).
- Léxico aplicado: **normalização** transforma a representação textual em um instante; **invariante** exige timestamp presente e único após a transformação; **teste de regressão** reproduz a falha descoberta para impedir seu retorno. A fixação usa a causa do erro no código revisado, sem questionário elementar.
- Próxima ação do aluno: aplicar o ajuste, adicionar o teste parametrizado, executar o mesmo comando de pytest e enviar o resultado junto de `C:\renewable-forecast-lab\src\renewable_forecast\features.py`, incluindo `FEATURE_COLUMNS` e `build_feature_frame`.
- Próxima ação do professor: revisar o resultado e o construtor real; definir a associação entre as features disponíveis na emissão e a tabela de pares h+6. Não presumir que o timestamp de cada linha atual seja a origem: ele pode representar o horário-alvo do h+1. Inspecionar lags, janelas e variáveis de calendário antes de instruir a integração.
- Estado: pareamento e testes entregues; correção orientada pendente de confirmação pelo aluno; features e integração ao treinamento ainda não verificadas. A sequência permanece na aplicação da M00.1, preparando a evolução técnica já prevista.

**M00.1 — validação do incremento de pareamento, 18/09/2026**

- Evidência recebida: E15, execução relatada de `python -m pytest tests/test_supervised.py -q` na raiz `C:\renewable-forecast-lab`, com resultado `13 passed in 4.16s`.
- Decisão: encerrar a rodada de correção e testes do pareamento nos cenários previstos. Não solicitar repetição de testes nem novo questionário sobre esse trecho. Não há nova execução pelo professor nesta resposta.
- Limite da evidência: o log informa a aprovação de 13 casos; os arquivos atualizados não foram reenviados. Não inferir cobertura integral do sistema nem atribuir execução ou implementação ao professor.
- Próximo incremento: associar features elegíveis na emissão aos pares de alvo h+6. Antes de definir o join, inspecionar o significado temporal das linhas, lags e janelas no construtor atual.
- Arquivo necessário: `C:\renewable-forecast-lab\src\renewable_forecast\features.py`, incluindo `FEATURE_COLUMNS` e `build_feature_frame`. Seu conteúdo ainda não foi recebido.
- Próxima ação do aluno: colar o conteúdo do arquivo; pode obtê-lo com `Get-Content .\src\renewable_forecast\features.py` no PowerShell que já está aberto na raiz do projeto.
- Próxima ação do professor: ler esse arquivo e orientar a integração concreta, mantendo a construção de features compatível com o instante de emissão. O alvo `target_generation` não deve ser tratado como uma entrada do modelo.
- Estado: incremento de pareamento validado nos casos previstos; integração das features e treino h+6 ainda pendentes. M00.1 permanece em andamento até completar a leitura e aplicação do fluxo existente.

**M00.1 — aplicação dos pares h+6 à validação temporal, 18/09/2026**

- Continuidade: o pareamento validado é a entrada da avaliação temporal. A construção do corte pode avançar com as colunas já definidas, enquanto a integração das features ainda requer o construtor real. Os marcos e os resultados anteriores permanecem preservados.
- Base no código recebido: `build_temporal_search` usa `TimeSeriesSplit(n_splits=5, test_size=24 * 28)`, sem `gap` explícito. Ao aplicar esse corte diretamente a uma tabela indexada pela origem e com alvo h+6, algumas linhas finais do treino podem conter alvos ainda não conhecidos no início da validação. Isso é uma análise da futura tabela h+6, não um diagnóstico completo do h+1 existente.
- Política do exercício: modelo treinado antes da primeira emissão do bloco de validação. Um rótulo de treino precisa estar disponível **estritamente antes** dessa emissão. Igualdade com o corte é excluída deliberadamente.
- Três instantes distintos: `forecast_origin` é a emissão; `target_time` é o horário previsto; `target_available_at` é quando a geração observada correspondente ficou disponível para o sistema. Esta última coluna deve vir de evidência de disponibilidade real na aplicação. Atrasos fixos de 0h e 2h são hipóteses dos testes sintéticos, não fatos sobre os dados ONS.
- Exemplo: para validação começando às 10h, uma linha emitida às 09h com alvo das 15h não pode fornecer essa geração ao treinamento anterior às 10h. Alvos futuros podem ser usados posteriormente para medir o erro da validação; não podem informar o ajuste anterior à emissão.
- Incremento proposto: acrescentar `purged_time_series_splits` ao `C:\renewable-forecast-lab\src\renewable_forecast\supervised.py` e importar `TimeSeriesSplit` nesse módulo. A função usa posições relativas ao mesmo `frame` que originará `X` e `y`; não reordenar ou filtrar esses objetos separadamente após definir os cortes.

```python
from sklearn.model_selection import TimeSeriesSplit


def purged_time_series_splits(frame, *, n_splits=5, test_size=24 * 28):
    origins = pd.to_datetime(frame["forecast_origin"], errors="raise")
    available = pd.to_datetime(frame["target_available_at"], errors="raise")

    if origins.isna().any() or available.isna().any():
        raise ValueError("Origem e disponibilidade do alvo devem estar preenchidas.")
    if not origins.is_monotonic_increasing or not origins.is_unique:
        raise ValueError("As origens devem estar ordenadas e ser únicas.")

    cv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size)
    for train_idx, valid_idx in cv.split(frame):
        cutoff = origins.iloc[valid_idx[0]]
        eligible = available.iloc[train_idx] < cutoff
        train_idx = train_idx[eligible.to_numpy()]

        if train_idx.size == 0:
            raise ValueError("Nenhum exemplo de treino disponível antes deste corte.")
        yield train_idx, valid_idx
```

- Conceito lexical aplicado: **purging** = exclusão, em cada corte, de exemplos cujos rótulos ainda não atendem à política de disponibilidade. **Cutoff** = fronteira de informação usada para aquele treinamento. A invariante é `max(target_available_at no treino) < min(forecast_origin na validação)`.
- Ensaio local do professor: 48 observações horárias sintéticas de 01/01/2026 00h a 02/01/2026 23h, geração 100…147, h+6; 42 pares com alvo observado. `n_splits=2`, `test_size=6`. Cortes às 06h e 12h de 02/01/2026; treino original de 30 e 36 linhas; validação de seis linhas por bloco.
- Resultados confirmados por execução local: disponibilidade em `target_time` → treino elegível de 24 e 30 linhas; disponibilidade em `target_time + 2h` → 22 e 28 linhas. As posições de validação foram preservadas. Com atraso de duas horas, apenas `gap=6` ainda deixa duas linhas que não atendem à política por bloco. A invariante também foi verificada após remover uma observação próxima à fronteira.
- Limite: ensaio sintético com pandas/scikit-learn, sem treinamento de modelo e sem dados reais do usuário. Não há certificação de ausência de vazamento nas features nem confirmação da disponibilidade real da geração.
- Entrega do aluno: no mesmo `C:\renewable-forecast-lab\tests\test_supervised.py`, criar dois casos parametrizados, para atrasos 0h e 2h. Gerar 48 observações horárias, chamar `build_horizon_pairs(..., 6)`, remover somente pares sem `target_generation`, definir `target_available_at` conforme o atraso de teste, e materializar os cortes com `list(purged_time_series_splits(..., n_splits=2, test_size=6))`. Verificar tamanhos de treino esperados (24/30 ou 22/28), seis validações em cada bloco e a invariante temporal em ambos os blocos.
- A ordem é importante: o frame utilizado no split já deve ter as linhas elegíveis ao experimento; no treinamento integrado, as posições de `X`, `y` e metadados temporais precisam corresponder exatamente. A remoção de alvos ausentes pertence à preparação para treino/avaliação, não à função geral de pareamento, que continua preservando essas linhas.
- Próxima ação do aluno: enviar os dois testes e o resultado de `python -m pytest tests/test_supervised.py -q`, além do conteúdo de `C:\renewable-forecast-lab\src\renewable_forecast\features.py` para realizar a integração com conhecimento da implementação real.
- Próxima ação do professor: revisar os testes de corte e o construtor de features; estabelecer a tabela final de treinamento e conectar os índices temporais ao `GridSearchCV` existente, mantendo consistência entre features, alvo, disponibilidade e baseline do horizonte.
- Estado: regra e implementação de referência demonstradas pelo professor; aplicação e testes do aluno ainda não recebidos. Não ampliar a avaliação de aprendizagem com base apenas nesta demonstração.

**M00.1 — E16: cortes entregues e integração das features, 18/09/2026**

- Evidência do aluno: log de 17 casos passando em 3,83s; testes parametrizados dos tamanhos de treino e da desigualdade de disponibilidade em ambos os blocos, mais testes de datas ausentes e ordem inválida. Os `pytest.raises` materializam o gerador com `list`, fazendo as validações efetivamente executarem. A avaliação continua limitada aos comportamentos demonstrados.
- Construtor real: oito lags (1, 2, 3, 6, 12, 24, 48, 168), seis estatísticas móveis (média/desvio de 6, 24, 168h), 12 componentes de calendário e uma diferença recente: 27 features. Verifica frequência horária sem lacunas, tornando os deslocamentos por linhas equivalentes aos atrasos horários sob esse contrato.
- Semântica inspecionada: em uma linha com `din_instante=R`, `lag_1h=y(R-1h)`; as janelas terminam em R−1h; o calendário representa R. Para h+1, o `predict_next` anterior acrescenta a linha R=t+1h e usa histórico até t. Uma ligação ingênua da linha R=t+6h ao alvo h+6 usaria geração até t+5h e seria indevida para emissão em t. Apenas mudar o timestamp futuro também quebraria a checagem de grade horária do construtor atual.
- Decisão de integração: preservar as definições das features existentes e registrar seu relógio de referência. Extrair somente lags, janelas e `recent_delta_1h` do construtor; usar `history_end=history_reference_time−1h` e `forecast_origin=history_end+availability_delay`. Calcular o calendário independentemente em `target_time`. Não carregar a coluna `val_geracao` nem o calendário da linha histórica para X.
- Semântica dos nomes: `lag_1h` permanece uma hora antes de `history_reference_time`, e representa a última geração disponível na emissão sob a hipótese de atraso usada. A referência fica explícita na tabela; os metadados temporais não fazem parte de `FEATURE_COLUMNS`.
- Contrato do atraso: `availability_delay_hours` é um inteiro não negativo fornecido explicitamente. Nesta construção ele modela a latência fixa tanto das observações históricas quanto do alvo. Os valores 0 e 2 são cenários de teste; a disponibilidade operacional e eventuais revisões da geração ainda precisam de evidência real. Atraso não é um hiperparâmetro a escolher por melhor erro.
- Trabalho do aluno em `C:\renewable-forecast-lab\src\renewable_forecast\features.py`: extrair as fórmulas de calendário para `build_calendar_features(timestamps: pd.Series) -> pd.DataFrame`. A função retorna exatamente `CALENDAR_FEATURES`, na ordem declarada e com o mesmo índice recebido. Reutilizar as fórmulas existentes (inclusive mês−1). Depois das colunas auxiliares `hour`, `day_of_week` e `month`, substituir o bloco de senos/cossenos no construtor original por `data[CALENDAR_FEATURES] = build_calendar_features(data["din_instante"])`.
- Adaptador de referência para acrescentar ao `C:\renewable-forecast-lab\src\renewable_forecast\supervised.py`; pressupõe a extração anterior do calendário:

```python
from renewable_forecast.features import (
    CALENDAR_FEATURES,
    FEATURE_COLUMNS,
    build_calendar_features,
    build_feature_frame,
)


def build_horizon_training_frame(
    series, horizon_hours, *, availability_delay_hours
):
    if (
        isinstance(availability_delay_hours, bool)
        or not isinstance(availability_delay_hours, int)
        or availability_delay_hours < 0
    ):
        raise ValueError("O atraso deve ser um inteiro não negativo.")

    data = series.copy()
    data["din_instante"] = pd.to_datetime(data["din_instante"], errors="raise")
    data["val_geracao"] = pd.to_numeric(data["val_geracao"], errors="raise")
    pairs = build_horizon_pairs(data, horizon_hours)

    historical_columns = [
        c for c in FEATURE_COLUMNS if c not in CALENDAR_FEATURES
    ]
    history = build_feature_frame(data, require_target=False)
    history = history[["din_instante", *historical_columns]].rename(
        columns={"din_instante": "history_reference_time"}
    )
    delay = pd.Timedelta(hours=availability_delay_hours)
    history["history_end"] = (
        history["history_reference_time"] - pd.Timedelta(hours=1)
    )
    history["forecast_origin"] = history["history_end"] + delay

    frame = pairs.merge(
        history, on="forecast_origin", how="inner", validate="one_to_one"
    )
    frame[CALENDAR_FEATURES] = build_calendar_features(frame["target_time"])
    frame["target_available_at"] = frame["target_time"] + delay
    frame = (
        frame.dropna(subset=[*FEATURE_COLUMNS, "target_generation"])
        .sort_values("forecast_origin")
        .reset_index(drop=True)
    )
    if frame.empty:
        raise ValueError("Dados insuficientes para montar o treino deste horizonte.")
    return frame
```

- Escopo: tabela de treinamento retrospectivo com alvo conhecido; não é a função de emissão operacional de h+6. Histórico inicial sem features completas é excluído, assim como alvos ausentes. X será selecionado exclusivamente por `FEATURE_COLUMNS`; y por `target_generation`; os cortes usam o mesmo frame e a mesma ordem de linhas.
- Demonstração executada pelo professor: reconstrução funcional do construtor enviado e adaptador acima, com um helper de calendário local. Série sintética de 240 horas desde 01/01/2026 00h, geração 100…339. Para origem 09/01/2026 10h e h+6: atraso 0h → referência histórica 11h, histórico até 10h, `lag_1h=302`, `rolling_mean_6h=299.5`; atraso 2h → referência 09h, histórico até 08h, `lag_1h=300`, média6h=297.5. Em ambos, target das 16h = 308, `hour_sin_1=-sqrt(3)/2` e `hour_cos_1=-0.5`; disponibilidade do alvo às 16h ou 18h. Tabelas resultantes com 67 e 65 linhas, respectivamente.
- Verificação de informação indisponível: multiplicar por 100 a geração de todos os timestamps posteriores a `history_end` preservou as 27 features da origem escolhida, nos dois atrasos, enquanto o alvo mudou de 308 para 30800. A alteração começa após o último dado disponível, não necessariamente após a emissão; com atraso 2h, observações das 09h e 10h já estão incluídas na perturbação.
- Verificação de compatibilidade: com h+1 e atraso zero, 72 linhas, todas as 27 features e o alvo coincidiram numericamente com o construtor original, após alinhar por `target_time`. Nenhum modelo foi treinado e nenhum dado real do projeto foi processado nesta demonstração.
- Entrega do aluno: helper de calendário, adaptador integrado e testes da tabela, incluindo valores esperados nos dois atrasos e invariância de X ao alterar dados indisponíveis. A fixture deve ter pelo menos 169 observações para as features existentes; usar as 240 definidas acima. As fixtures de 12 e 48h continuam pertinentes aos testes anteriores, mas não bastam para este construtor.
- Verificação no projeto: executar `python -m pytest -q` na raiz, pois a extração do calendário modifica uma função usada pelo h+1 e exige verificar regressões existentes, além dos testes novos. Solicitar o helper, os novos testes e o resultado; não confundir a demonstração do professor com implementação ou execução pelo aluno.
- Léxico aplicado: **relógio de referência** define o significado dos lags; **disponibilidade** limita as observações usadas; **calendário do alvo** é conhecido antecipadamente; **invariância** exige que mudanças em informação indisponível não alterem X naquela emissão.
- Próximo passo: usar essa tabela no `GridSearchCV` existente, alinhando X/y/cortes e a persistência baseada em `lag_1h`, além de registrar horizonte e hipótese de disponibilidade nos metadados. Avaliação e inferência operacionais ainda precisam ser integradas e verificadas; não declarar modelo h+6 pronto.

**M00.1 — E17: integração entregue e recuperação do ambiente, 21/09/2026**

- Entrega recebida: helper de calendário preservando o índice e a ordem das 12 colunas; construtor de features reutilizando o helper; adaptador h+6 com seleção de histórico e disponibilidade explícita; testes dos valores esperados, invariância no atraso 2h, equivalência h+1 e cinco atrasos inválidos. `test_supervised.py` contém 26 casos contando parametrizações.
- Evidência de execução: o terminal está em `(base)` e usa `C:\Users\marhl\Miniconda3\python.exe`, Python 3.13.13. O instalador informa que o projeto requer `>=3.12,<3.13`. NumPy, pandas e o pacote do projeto não foram encontrados nesse ambiente. As seis falhas relatadas são de coleta; os testes novos não chegaram a executar. Não interpretar esse resultado como seis falhas de lógica nem como perda das evidências anteriores.
- Diagnóstico: os comandos passaram a usar o ambiente base depois da reinicialização. O ambiente que executou os 17 testes anteriores se chamava `renewable-forecast`. Os logs não confirmam que esse ambiente foi removido. A primeira ação é reativá-lo, sem alterar o requisito de Python do projeto.
- Comandos propostos no PowerShell, na raiz do projeto: `conda activate renewable-forecast`; `python --version`; `python -c "import sys; print(sys.executable)"`. Espera-se Python 3.12.x e um executável no ambiente `renewable-forecast`.
- Instalação somente se ainda necessária no ambiente correto: `python -m pip install -e ".[dev]"`. O argumento `-e` exige um caminho; o ponto indica o projeto atual, e o extra `dev` solicita as dependências de desenvolvimento declaradas. `--no-deps` não contorna a restrição de versão do Python e não instala as dependências ausentes.
- Se a ativação não encontrar o ambiente, obter `conda env list` para localizar os ambientes existentes; não inferir a necessidade de recriar ou apagar um ambiente sem esse resultado.
- Achado independente no código: `test_equivalence_h1_delay0_with_original_constructor` une `base_frame.din_instante` a `horizon_frame.forecast_origin`. No construtor original, `din_instante` é o horário-alvo; a chave correspondente no adaptador é `target_time`. No h+1/atraso zero, a origem é uma hora anterior a esse horário.
- Correção em `C:\renewable-forecast-lab\tests\test_supervised.py`, dentro do teste de equivalência:

```python
    merged = base_frame.merge(
        horizon_frame,
        left_on="din_instante",
        right_on="target_time",
        how="inner",
        validate="one_to_one",
        suffixes=("_base", "_horizon"),
    )
    assert len(merged) == len(base_frame) == len(horizon_frame)
```

- As comparações das features e do alvo que vêm depois do merge permanecem pertinentes. A nova asserção exige cobertura completa do pareamento; não basta validar apenas a interseção de linhas.
- Reprodução local delimitada: no alinhamento da fixture de 240h, o join por `forecast_origin` forma 71 pares com lag e alvo deslocados em uma hora; o join por `target_time` forma 72 pares com lag e alvo iguais. Verificado com pandas e NumPy, sem executar a suíte pytest do usuário ou acessar seu computador.
- Próxima ação do aluno: reativar o ambiente, aplicar a correção do teste e executar `python -m pytest -q` na raiz. A validação completa continua necessária porque a extração do calendário alterou um construtor utilizado pelo h+1. Não há novo treino solicitado nesta rodada.
- Retorno necessário: versão/caminho do Python e resultado da suíte; em caso de falha de ativação, resultado de `conda env list`. Os arquivos enviados já foram recebidos; não pedir novamente todo o código sem necessidade.
- Léxico aplicado: **ambiente** seleciona intérprete e bibliotecas; **coleta** importa módulos e identifica testes antes da execução; **equivalência temporal** compara registros referentes ao mesmo horário-alvo.
- Estado: implementação entregue, correção pontual indicada, execução no ambiente apropriado ainda não confirmada. A próxima integração com `GridSearchCV` permanece a mesma; nenhuma competência é apagada pela falha de ambiente e nenhum resultado novo é inventado.

**M00.1 — E18: testes supervisionados aprovados e contrato do backtest, 21/09/2026**

- Evidência recebida: o aluno confirmou Python 3.12.13 em `C:\Users\marhl\Miniconda3\envs\renewable-forecast\python.exe`; o ambiente existente foi recuperado. O erro posterior ao executar um trecho de caminho como comando não representa perda desse ambiente.
- O arquivo de testes reenviado contém o merge por `target_time`, com `validate="one_to_one"` e asserção de cobertura. O anexo `Texto colado(4).txt` registra `python -m pytest -q` com `1 failed, 47 passed in 8.50s`. A única falha listada está em `tests/test_features.py::test_backtest_and_result_files`; portanto, os 26 casos do módulo supervisionado foram aprovados nessa execução.
- Diagnóstico: `run_backtest`, em `backtest.py`, executa `.groupby("hour")["target_delta"]`. O construtor original entregava `hour`, `day_of_week` e `month`; a versão extraída passou a entregar apenas as codificações cíclicas. O helper produz corretamente as 12 colunas cíclicas, mas o contrato do DataFrame consumido pelo backtest perdeu `hour`. É uma regressão entre módulos, não uma nova falha de ambiente.
- Correção proposta em `C:\renewable-forecast-lab\src\renewable_forecast\features.py`, dentro de `build_feature_frame`: substituir a atribuição atual de `CALENDAR_FEATURES` pelo bloco abaixo. As três colunas auxiliares retomam o contrato anterior; `FEATURE_COLUMNS` continua com as 27 entradas existentes.

```python
    # Colunas auxiliares utilizadas pelo fluxo existente.
    data["hour"] = data["din_instante"].dt.hour
    data["day_of_week"] = data["din_instante"].dt.dayofweek
    data["month"] = data["din_instante"].dt.month

    data[CALENDAR_FEATURES] = build_calendar_features(data["din_instante"])
```

- Referência temporal preservada: as colunas auxiliares pertencem ao construtor original, cujo `din_instante` é o horário-alvo do h+1. No adaptador h+6, a seleção de `historical_columns` não inclui essas três colunas e o calendário cíclico continua sendo recalculado a partir de `target_time`.
- Verificação solicitada: executar `python -m pytest -q` na raiz. A mesma suíte tem 48 casos; critério de aceite: todos aprovados, inclusive o backtest existente. Não foi adicionada uma nova bateria nem executada a suíte do computador do aluno pelo professor. A correção ainda não possui resultado posterior confirmado.
- Léxico aplicado: **contrato de saída** é o conjunto de colunas e significados exigidos pelos consumidores; **regressão** é a perda de comportamento existente após uma alteração; **teste de integração** exerce a passagem dos dados entre construtor, backtest e resultados. `FEATURE_COLUMNS` define X, não todas as colunas permitidas no DataFrame.
- Continuidade: após fechar a regressão, conectar `build_horizon_training_frame` e `purged_time_series_splits` ao `GridSearchCV` do `modeling.py` já recebido. X, y e cortes devem usar o mesmo frame e a mesma ordem. Treino final, inferência h+6 e meteorologia operacional permanecem pendentes; a aprovação de testes sintéticos não comprova precisão do modelo nem a latência real de publicação.

**M03.3 — E19: base validada e integração da busca temporal, 21/09/2026**

- Evidência do aluno: `48 passed in 14.76s` na suíte completa do projeto. A correção do contrato do calendário e os testes supervisionados estão aprovados nos cenários cobertos. A passagem a M03.3 corresponde à unidade já planejada de tuning temporal e separação do teste; não declara os demais módulos concluídos.
- Fontes de implementação: módulo `modeling.py` previamente enviado como `Texto colado(3).txt`, incluindo oito candidatos, cinco scorers e `constrained_refit`; CLI já recebida. Nenhum novo arquivo do aluno foi solicitado para repetir essa leitura.
- Entrega proposta no arquivo `C:\renewable-forecast-lab\src\renewable_forecast\modeling.py`: importar `build_horizon_training_frame` e `purged_time_series_splits`; permitir `build_temporal_search(*, cv=None, param_grid=None)`; acrescentar `fit_horizon_search(series, *, horizon_hours, availability_delay_hours, n_splits=5, test_size=672, param_grid=None)` retornando a busca ajustada e o frame auditável. A função forma X, y e os índices a partir da mesma tabela, usando `target_generation`.
- A fábrica continua aceitando a chamada existente sem argumentos. Na nova função, `cv` sempre recebe os cortes filtrados por disponibilidade. Uma grade reduzida pode ser fornecida aos testes sem alterar os oito candidatos da grade original.
- Protocolo do estimador: `early_stopping=False`, deixando o orçamento de árvores sob `max_iter` e a escolha de hiperparâmetros sob a validação temporal externa. A configuração automática do HGB pode ativar uma validação interna quando a amostra cresce; essa configuração deve ser preservada na futura integração do treino final.
- Teste de integração proposto em `tests/test_modeling_horizon.py`: série sintética de 360 horas, geração `100 + t`, horizonte 6h, atrasos 0h e 2h; dois candidatos pequenos, dois folds de 24 observações; verificar 27 features, finitude das métricas, quantidade de candidatos, MAE da persistência de 6 e 8 e disponibilidade estritamente anterior ao começo de cada validação. Esperam-se 50 casos na suíte atual após acrescentar os dois casos parametrizados, ainda sem log do aluno para essa versão.
- Verificação executada pelo professor: reprodução local das funções de features e supervisão fornecidas pelo aluno, com grade/scorers/refit extraídos literalmente do arquivo enviado. Execução real do GridSearchCV com scikit-learn 1.8.0 e pandas 2.2.3; não foi uma execução de pytest no computador do aluno. Atraso zero: 187 linhas, treinos de 133/157 e baseline MAE 6; atraso 2h: 185 linhas, treinos de 129/153 e baseline MAE 8. Ambos os candidatos tiveram os valores esperados; as invariantes temporais foram verificadas. Nenhum dado real ou MLflow foi executado nessa reprodução.
- Experimento real proposto: ler `data/interim/CJU_BA5EIGT_hourly.parquet`, reservar os últimos 28 dias pelo tempo, usar atraso 2h como hipótese didática explícita e admitir no desenvolvimento apenas observações cujo timestamp mais atraso seja estritamente anterior ao corte. Executar os oito candidatos com cinco folds e imprimir parâmetros e `_validation_metrics(search)`. Esses resultados serão evidência de seleção no desenvolvimento, não avaliação final no período reservado.
- Verificação do recorte, apenas em timestamps sintéticos reproduzindo o intervalo anteriormente informado: 8.760 horas de 01/09/2025 a 31/08/2026, corte em 04/08/2026 00h; 8.086 observações admitidas, frame com 7.911 linhas, treinos dos cinco folds com 4.543/5.215/5.887/6.559/7.231 exemplos e 672 observações de validação por fold. Nenhum rótulo disponível no corte ou depois dele foi admitido. Contagens condicionadas à mesma série completa; valores reais de geração não foram processados.
- Interpretação necessária: `cv_results_` registra as avaliações por candidato e fold; `constrained_refit` escolhe o índice e o GridSearchCV reajusta o modelo escolhido em todo o desenvolvimento. A existência de `best_estimator_` não prova superioridade à persistência. O seletor ainda escolhe uma alternativa quando nenhum candidato cumpre os limites; examinar `selection_approved` e as métricas retornadas. A RampMAE herdada mede grandes diferenças entre o alvo e a última observação disponível; com h+6 e atraso 2h, esse intervalo é de 8h, distinto do usado no h+1.
- Léxico aplicado: **hiperparâmetro** controla como o estimador aprende; **fold** é uma separação de treino/validação; **purga** exclui rótulos ainda indisponíveis; **refit** reajusta o candidato escolhido no desenvolvimento; **holdout** é o período reservado para avaliação após a seleção. Fixação por uso no código, diagnóstico e interpretação das métricas; não por perguntas de completar lacunas.
- Próxima evidência: implementação aplicada, resultado dos testes e saída do primeiro experimento. A seguir, analisar o desempenho e integrar a função à CLI/MLflow com horizonte, disponibilidade e protocolo registrados; treino final, inferência h+6, avaliação no período reservado e meteorologia real seguem pendentes. Os comandos `renewcast train/predict` recebidos ainda pertencem ao fluxo h+1.

**M03.3 — E20: primeiro resultado real h+6 e diagnóstico, 22/09/2026**

- Execução do aluno: `50 passed in 32.89s`. A busca recebeu 7.911 exemplos, horizonte 6h e atraso fixo assumido de 2h. Foram usados cinco folds com 672 exemplos de validação cada; tamanhos de treino 4.543, 5.215, 5.887, 6.559 e 7.231. O período reservado começa em 04/08/2026 00h.
- Parâmetros selecionados: `l2_regularization=1.0`, `learning_rate=0.03`, `max_iter=250`, `max_leaf_nodes=15`, `min_samples_leaf=20`. O estimador da fábrica usa `early_stopping=False` e `random_state=42`.
- Métricas recebidas: MAE 27,377963696240805; RMSE 34,916169057056415; RampMAE 37,05744152206798; média dos vieses absolutos dos folds 3,1052273654631293; MAE da persistência 51,7836875. Flags: MAE aprovado, viés reprovado e seleção reprovada.
- Cálculo do professor a partir do log: redução absoluta do MAE de 24,405723803759194 MWmed e relativa de 47,1301388178646%. O teto de MAE do seletor é 1,02 × 51,7836875 = 52,81936125 MWmed; o teto de viés é 2 MWmed. Esses valores são de seleção no desenvolvimento, sem conclusão sobre o holdout nem significância estatística.
- Inferência da implementação recebida: como `constrained_refit` escolhe primeiro entre candidatos elegíveis, a reprovação do escolhido indica que nenhum dos oito candidatos satisfez simultaneamente as duas restrições e que o caminho alternativo de seleção foi usado. A tabela dos oito candidatos será exportada para confirmar diretamente essa leitura.
- Diagnóstico ainda não disponível: `validation_absolute_bias` é a média dos valores absolutos dos vieses de cada fold; não preserva o sinal e não equivale necessariamente ao valor absoluto do viés global. Faltam as métricas individuais para saber se o ganho é estável e se o modelo subestima, superestima ou muda de direção conforme o período. Não decidir uma correção de 3,105 MWmed a partir desse agregado.
- Progresso demonstrado: pareamento temporal, 27 features com relógios separados, cortes por disponibilidade, integração da busca e primeiro benchmark h+6 real. A CLI operacional recebida continua h+1; meteorologia real, h+24, quantis, teste final e serviço h+6 não têm entrega concluída. A aprendizagem registrada é prática guiada; executar código fornecido não comprova sozinho transferência autônoma.
- Próximo incremento entregue pelo professor: `horizon_diagnostics.py`, a instalar em `src/renewable_forecast/`, e `test_horizon_diagnostics.py`, a instalar em `tests/`. O módulo fornece `evaluate_selected_folds`, `candidate_metrics` e um comando `python -m renewable_forecast.horizon_diagnostics`. Reutiliza a busca existente e a configuração MLflow do projeto; não substitui o treinamento operacional h+1.
- Procedimento de diagnóstico: clonar o estimador selecionado sem carregar seu ajuste; ajustar cada clone somente no treino permitido daquele fold; prever a validação; aplicar o mesmo piso zero; registrar resíduos `observado - previsto`. O estimador reajustado em todo o desenvolvimento não pode fornecer previsões fora do treino sobre esse mesmo desenvolvimento. Os hiperparâmetros continuam escolhidos nos folds atuais: a análise é diagnóstica, não uma avaliação final independente.
- Artefatos previstos por execução: `search.joblib`, `development_frame.parquet`, `cv_results.csv`, `candidate_metrics.csv`, `validation_metrics.json`, `metadata.json`, `oof_predictions.parquet` e `fold_metrics.csv`, dentro de uma pasta identificada pelo run. O metadata registra horizonte, hipótese de atraso, corte, restrições, parâmetros completos, ordem de features, versões, hash do Parquet, convenção do viés e ausência de avaliação do holdout. MLflow recebe parâmetros, métricas e arquivos.
- Limitação corrigida no procedimento anterior: o processo `python -` foi encerrado sem salvar o objeto de busca. A execução proposta refaz a busca uma vez e a persiste antes de calcular o diagnóstico. Ela inclui cinco novos ajustes do candidato selecionado para reconstruir as previsões de validação; esses ajustes não constituem uma nova seleção de hiperparâmetros.
- Verificação local do professor: os dois casos parametrizados de teste foram executados diretamente por asserções, com tendência positiva e negativa. Eles comprovam que as previsões correspondem à média do treino do fold e diferem das previsões do estimador ajustado no conjunto inteiro. Uma execução HGB sintética confirmou que MAE, RMSE, viés absoluto, RampMAE e MAE da persistência reconstruídos reproduzem os scorers da busca. Código compilado. MLflow não está instalado no ambiente do professor; integração do registro e dados reais não foram executados localmente. A validação no projeto do aluno permanece necessária.
- Próxima execução do aluno: `python -m pytest -q`, com 52 casos esperados na suíte inalterada acrescida dos dois novos casos; em seguida, `python -m renewable_forecast.horizon_diagnostics --input data/interim/CJU_BA5EIGT_hourly.parquet --output-dir reports/tuning/h6_d2 --horizon-hours 6 --availability-delay-hours 2`. A saída informa as tabelas dos candidatos e dos folds e o caminho dos resultados. O holdout continua reservado.
- Tarefa de interpretação: identificar se o viés tem direção persistente ou muda entre períodos, em quantos folds o MAE supera a persistência e se uma correção constante tem justificativa. Qualquer calibração posterior deve ser aprendida em dados anteriores ao período avaliado, considerando também quando os resíduos se tornam disponíveis.
- Léxico aplicado: **resíduo** = observado menos previsto; **viés com sinal** = média dos resíduos; **OOF** = previsões obtidas sem ajustar os parâmetros do estimador nas linhas previstas; **clone** = novo estimador com os mesmos hiperparâmetros e sem ajuste; **artefato** = resultado salvo e ligado a uma execução. A escolha dos hiperparâmetros usou os folds, ressalva preservada ao falar em OOF.
- Continuidade após o diagnóstico: decidir a intervenção a partir dos resíduos; consolidar protocolo e registro; avaliar o candidato congelado no período reservado; integrar a emissão h+6 e avançar para forecasts meteorológicos reais. Não reabrir os testes de pareamento já aprovados sem uma regressão concreta.

**M03.3 — E21/E22: diagnóstico concluído e experimento de correção, 22/09/2026**

- Execução confirmada: `horizon_diagnostics` registrou o run `c9f73918630644f688cfd7f6a26e58fa` e salvou os arquivos em `C:\renewable-forecast-lab\reports\tuning\h6_d2\c9f73918630644f688cfd7f6a26e58fa`. O aluno apresentou depois coleta explícita de dois casos novos e `52 passed in 10.69s`. A contagem anterior de 50 não deve mais bloquear a continuidade; sua causa exata não foi identificada pelos logs.
- Diagnóstico do candidato 0: folds 1–5 com ganhos de MAE de 33,180%, 38,682%, 47,367%, 53,644% e 55,254%; vieses com sinal +0,035, +6,980, −2,070, −0,184 e +6,257 MWmed. Média dos vieses absolutos 3,1052273654631293; viés global com sinal 2,2036878086567198. Todos os oito candidatos falharam no limite de viés. Candidato 2 teve o menor viés absoluto médio, 2,165, também acima do limite. Nenhum resultado do holdout foi apresentado.
- Interpretação do aluno: identificou corretamente direção variável do viés e melhoria contra persistência nos cinco folds. Argumentou contra um offset global por prejudicar períodos com viés negativo ou próximo de zero. Feedback: a alternância de sinais justifica investigação, mas não prova que toda correção constante piora o MAE; uma média de resíduos positiva tampouco garante redução do MAE ao somar esse valor. A função de perda e a distribuição dos resíduos precisam entrar na decisão.
- Incremento proposto: comparar HGB original, correção pela média recente e correção pela mediana recente, usando o arquivo OOF já salvo. Reutiliza as previsões; não repete o GridSearchCV nem ajusta novos HGBs. Os hiperparâmetros originais foram selecionados nesses folds, portanto a comparação permanece exploratória no desenvolvimento.
- Código anterior inspecionado: `apply_prequential_calibration` no módulo h+1 fornecido no bundle acumula resíduos de folds anteriores, sem verificar `target_available_at`. Para h+6 e atraso explícito, excluir apenas o fold atual não basta para controlar a chegada dos últimos rótulos do fold anterior. O incremento cria funções próprias para o schema h+6, preservando o fluxo h+1.
- Protocolo fixado antes do resultado: janela de 168 horas medida pelo relógio de disponibilidade, com limites `[forecast_origin - 168h, forecast_origin)`; mínimo de 48 resíduos; offset zero no aquecimento; histórico de resíduos do HGB original; atualização em cada emissão; histórico continua entre folds; piso zero na previsão corrigida. O atraso de 2h continua uma hipótese do experimento de origem, não uma latência comprovada.
- Regra de decisão previamente declarada: para considerar uma das correções, exigir MAE médio dos folds não superior ao HGB original e média dos vieses absolutos dos folds ≤ 2 MWmed. RMSE e RampMAE também serão relatados para avaliar trade-offs. Nenhuma escolha é promovida automaticamente a produção; resultado negativo pode encerrar o experimento e preservar o original como referência.
- Entrega de referência: `horizon_calibration.py`, para `src/renewable_forecast/`, com `apply_available_offsets`, `summarize_offsets` e CLI; `test_horizon_calibration.py`, para `tests/`, com dois casos que verificam janela/disponibilidade/aquecimento e invariância a alvos indisponíveis. Os arquivos são apoio didático fornecido pelo professor, não evidência de implementação autônoma do aluno.
- Exemplo para fixação: resíduos históricos disponíveis [1, 2, 30]. Offset zero: viés 11 e MAE 11. Offset pela média, 11: viés 0 e MAE 38/3 ≈ 12,667. Offset pela mediana, 2: viés 9 e MAE 29/3 ≈ 9,667. É uma demonstração no histórico usado para o ajuste; não estima o desempenho futuro da calibração nem inclui o piso zero.
- Verificação local do professor: dois testes executados diretamente por asserções, sem pytest instalado; resumo conferido com folds de tamanhos diferentes para preservar a agregação de médias por fold. Em cenário sintético horário de 3.360 emissões, h+6 e atraso 2h, houve 56 emissões de aquecimento e 3.304 com correção ativa; nenhuma correção usou resíduo disponível no instante da emissão ou depois dele. Dados reais e gravação MLflow desta nova etapa não foram executados localmente.
- Saídas previstas: novo run `renewable-h6-calibration`, com vínculo `source_run_id`; subpasta `calibration/<run_id>` no experimento de origem; `calibrated_predictions.parquet`, `fold_metrics.csv`, `summary.csv` e `metadata.json`. O metadata registra janela, mínimo, clock e limites, aquecimento, origem dos resíduos, regra de decisão, escopo de avaliação, hash do OOF e período reservado ainda não avaliado.
- Próxima ação do aluno: instalar os dois arquivos, executar `python -m pytest tests/test_horizon_calibration.py -q` e depois `python -m renewable_forecast.horizon_calibration --run-dir reports/tuning/h6_d2/c9f73918630644f688cfd7f6a26e58fa --window-hours 168 --min-history 48`. Enviar as tabelas Resumo e Resultados por fold, interpretando se alguma correção reduziu o viés sem piorar o MAE e se o resultado é consistente entre períodos.
- Léxico aplicado: **calibração** é a correção da saída do modelo; **prequential** avalia cada previsão com atualização usando resultados já observados; **janela móvel** define quais resíduos recentes participam; **média/mediana** representam objetivos e sensibilidades diferentes; **aquecimento** é o período anterior ao histórico mínimo. A limitação de seleção prévia dos hiperparâmetros continua explícita.
- Continuidade: decidir a partir dos resultados, congelar o procedimento escolhido e avaliar o período reservado; depois integrar emissão h+6 e acrescentar meteorologia real. Não repetir tuning, instalação do ambiente ou diagnóstico de coleta já resolvido.

**M03.3 — E23: método escolhido e avaliação reservada preparada, 22/09/2026**

- Execução do aluno: `python -m pytest tests/test_horizon_calibration.py -q` retornou `2 passed in 1.49s`. A última execução integral comprovada continua sendo a de 52 casos; não se declara uma suíte de 54 executada sem o respectivo log. Não há necessidade de repetir a suíte para prosseguir nesta etapa.
- Run de calibração: `57d9408018bf45279962da8fa30e6b68`, filho do diagnóstico `c9f73918630644f688cfd7f6a26e58fa`, salvo em `reports/tuning/h6_d2/c9f73918630644f688cfd7f6a26e58fa/calibration/57d9408018bf45279962da8fa30e6b68`. Houve 3.304 correções ativas em 3.360 emissões, com 56 emissões de aquecimento.
- Resultados recebidos, médias dos folds: HGB bruto MAE 27,378, RMSE 34,916, RampMAE 37,057, viés absoluto 3,105; média causal MAE 26,756, RMSE 34,833, RampMAE 36,931, viés absoluto 1,706; mediana causal MAE 26,409, RMSE 35,161, RampMAE 36,988, viés absoluto 4,316. Ganhos contra o MAE bruto: 2,271% e 3,537%, respectivamente. A média ganhou nos cinco folds; a mediana, em quatro.
- Decisão com a regra previamente declarada: selecionar `hgb_mean` para avaliação reservada. Não ampliar a janela de busca nem substituir o critério por MAE isolado após observar os resultados. A mediana não segue para seleção no holdout. Persistência e HGB bruto serão controles do relatório, sem seleção posterior de vencedor nesse período.
- Interpretação do aluno: identificou corretamente a média como única correção elegível e a melhoria de MAE em todos os cinco folds. Complemento necessário: os vieses da média nos folds 3 e 4 são −3,007 e +2,990 MWmed; ambos excedem 2 em módulo. O limite aprovado é a média dos vieses absolutos, não um teto em cada fold. Ganhar na média de cinco janelas não implica ganhar em cada emissão. O viés global da mediana, 0,124, mascara vieses de sinais opostos entre períodos; não substitui o critério de 4,316.
- Incremento entregue: `horizon_holdout.py` para `src/renewable_forecast/`. Carrega `search.joblib` e utiliza `best_estimator_`, já ajustado sobre o desenvolvimento. Reutiliza as features e a função causal de correção existentes. Não chama `fit` nem reexecuta GridSearchCV. Compara persistência, HGB bruto e o procedimento previamente escolhido.
- Procedimento da avaliação: manter HGB, features, h+6, atraso assumido de 2h, janela de 168h, mínimo de 48 resíduos, piso zero e disponibilidade estrita da calibração. Inicializar a correção com resíduos OOF disponíveis na semana anterior ao corte. Acrescentar resíduos do holdout somente quando sua disponibilidade anteceder a emissão seguinte. Não gerar resíduos retrospectivos de treino com o HGB final. O modelo fica fixo; o estado da correção evolui pela regra pré-fixada.
- O uso de resíduos passados do próprio holdout faz parte de uma avaliação sequencial de um procedimento adaptativo declarado antes das métricas. Não é uma avaliação de correção estática nem permite mudar a regra após olhar resultados. O primeiro resíduo h+6/delay2 da avaliação estará disponível em origem +8h e, pelo limite estrito e emissões horárias, participará a partir de origem +9h.
- Identidades verificadas pelo módulo: hash do Parquet original, hash das previsões OOF, relação entre os runs, protocolo, lista de features, versão do scikit-learn e disponibilidade dos rótulos do desenvolvimento. `frozen_protocol.json` é escrito antes das métricas. O atraso de 2h continua hipótese experimental, sem validação de publicação real do ONS.
- Holdout definido pelas origens a partir de `2026-08-04 00:00:00`. Com a série horária completa até `2026-08-31 23:00:00`, são esperadas 666 emissões avaliáveis, terminando em `2026-08-31 17:00:00`; as seis últimas origens não têm alvo h+6 observado. A contagem efetiva é registrada e eventuais outras exclusões são explicitadas. Janelas semanais de diagnóstico esperadas: 168, 168, 168 e 162 linhas.
- Critério registrado antes da execução: no período reservado completo, MAE da média ≤ MAE bruto, MAE ≤ 1,02 × persistência e módulo do viés do período ≤ 2 MWmed. Esta é uma janela de avaliação; o módulo de seu viés não é a média de vieses de cinco folds. Diagnósticos semanais, RMSE e RampMAE expõem limitações e não introduzem uma nova regra de seleção. Aprovação de produção não é automática. Resultado desfavorável continua sendo uma avaliação concluída e deve ser relatado sem reajustar a escolha nesse holdout.
- Saídas: novo run `renewable-h6-holdout`, subpasta `holdout/<run_id>` no diagnóstico; `frozen_protocol.json`, `predictions.parquet`, `summary.csv`, `weekly_metrics.csv`, `metadata.json`, `initial_calibration_seed.parquet` e `model.joblib` com o mesmo estimador utilizado. O modelo salvo isoladamente ainda não constitui um serviço de inferência h+6.
- Verificação do professor em dados sintéticos: reproduziu o calendário de 8.760 horas, 666 emissões, 168 resíduos iniciais e quatro semanas de 168/168/168/162 linhas; verificou a ausência de reajuste, agregação global de MAE/RMSE, disponibilidade estrita e invariância das previsões anteriores à adulteração de dados ainda indisponíveis. Não foram executados os dados reais nem a gravação real no MLflow do aluno. Não há novo arquivo de testes solicitado ao aluno nesta etapa.
- Ação prática: salvar o módulo, executar a CLI com o Parquet e os dois identificadores já conhecidos, apresentar o resumo do holdout e o diagnóstico semanal. Encerrada essa avaliação, seguir para emissão h+6 sem depender do alvo futuro; meteorologia real permanece em M04.
- Léxico aplicado: **artefato ajustado** = objeto que contém o ajuste aprendido e é recuperado com joblib; **procedimento congelado** = modelo e regra definidos antes de observar o resultado; **estado** = resíduos disponíveis que mudam durante a operação; **avaliação prequential** = emitir, esperar a disponibilidade do resultado e atualizar o estado; **holdout** = intervalo reservado para avaliar a escolha previamente feita.

**M03.3 — E24: avaliação concluída e primeira emissão sem alvo preparada, 22/09/2026**

- Execução real recebida: `horizon_holdout` criou o run `d401657267524b528120f2c0ca7ea184`, com 666 emissões e seis origens finais sem alvo observado. Arquivos em `reports/tuning/h6_d2/c9f73918630644f688cfd7f6a26e58fa/holdout/d401657267524b528120f2c0ca7ea184`. Modelo e regra vieram do desenvolvimento; não houve novo tuning no holdout.
- Métricas globais recebidas, MWmed: persistência MAE 54,559, RMSE 68,668, viés −0,549, RampMAE 128,566; HGB bruto MAE 25,961, RMSE 32,101, viés +3,386, RampMAE 33,674; HGB com média MAE 25,325, RMSE 32,288, viés +0,101, RampMAE 33,630. Foram 67 eventos na definição de rampa utilizada. Ganho de MAE calibrado de 53,582% contra persistência e 2,450% contra o bruto. O procedimento atende aos três limites globais declarados.
- Limites da conclusão: não houve dominância em todas as métricas. RMSE subiu 0,187 MWmed após a calibração. Vieses semanais do calibrado: −5,144, +1,732, +7,724 e −4,055; três de quatro semanas excedem 2 em módulo. O viés mensal próximo de zero resulta de compensação temporal. O critério mensal não mede estabilidade semanal e não deve ser reescrito depois de observado o teste. O ganho é observado nesta janela, sem intervalo de confiança ou generalização universal demonstrados. Avaliação aprovada não equivale a serviço em produção.
- Decisão: encerrar a avaliação desta configuração e manter o resultado e as limitações no registro. Não ajustar a janela, os hiperparâmetros ou o método usando esse holdout. Mudanças futuras exigirão novo protocolo e período de avaliação. A próxima prática aplica o artefato avaliado a uma emissão cujo alvo não está no arquivo.
- Incremento entregue: `horizon_predict.py`, para `src/renewable_forecast/`, com `build_prediction_row`, `available_mean_correction` e CLI. Usa o `model.joblib` do holdout, sem `fit`. Não depende de `build_horizon_training_frame`, porque esse construtor exige alvos de treino observados.
- Contrato de features em operação: para emissão t e atraso d, exigir observações horárias completas até `history_end = t-d`; usar 168 horas de histórico. Acrescentar uma linha de referência com `val_geracao=NaN` em `history_end+1h` para reutilizar `build_feature_frame(require_target=False)`. O NaN não é geração simulada nem alvo conhecido. Recalcular calendário em `target_time=t+h`. Entregar ao modelo exclusivamente `FEATURE_COLUMNS`. Esta transformação preserva a semântica do treino e rejeita histórico recente incompleto.
- Contrato de estado da calibração: recuperar as previsões OOF iniciais e as previsões do holdout; incorporar posteriormente as novas emissões registradas. Para cada origem, selecionar apenas disponibilidades no intervalo `[origem-168h, origem)`. Juntar os alvos históricos às observações atuais para formar resíduos `observado - previsão bruta`. Excluir observações ausentes, registrar sua contagem e aplicar offset zero se houver menos de 48 resíduos. O resultado da previsão atual nunca é exigido. O atraso fixo continua sendo hipótese experimental; revisões retroativas da fonte não são modeladas por este contrato.
- Emissão proposta: `2026-09-01 01:00:00`, usando geração até `2026-08-31 23:00:00`, referência de cálculo `2026-09-01 00:00:00`, alvo `2026-09-01 07:00:00`, disponibilidade esperada do alvo `2026-09-01 09:00:00`. É uma emissão no relógio do conjunto de dados, não uma previsão em tempo real para o dia da conversa. O alvo deve estar ausente no arquivo apresentado. Pela regra estrita, o novo resíduo poderá ser utilizado a partir da emissão horária das 10h.
- Registro de operação local: JSON por emissão, CSV com a linha de features e `prediction_log.csv`, em `reports/forecasts/h6_d2/<holdout_run_id>/`. O JSON contém previsão bruta e calibrada, persistência, offset, número de resíduos, último instante disponível, horários, hipótese de latência, identificador e hash do modelo. O registro guarda previsões brutas para calcular resíduos quando novas observações chegam. Emissões duplicadas ou anteriores à última registrada são rejeitadas; a CLI é serial e não constitui serviço concorrente nem coleta automática.
- Verificação do professor: paridade das 27 features com o construtor de treino em três origens usando somente histórico disponível, inclusive timestamps em outra resolução; invariância a geração futura; duas execuções da CLI em dados sintéticos com HGB real, serialização joblib e escrita/leitura real de JSON e CSV; segunda emissão incorporou o resíduo recém-observado da primeira somente no instante permitido. Não há engine Parquet no ambiente do professor; a leitura Parquet foi substituída por DataFrames sintéticos nessa verificação. O usuário possui leitura Parquet demonstrada no holdout. Nenhum dado real ou valor de previsão real do aluno foi calculado pelo professor nesta etapa.
- Aprendizagem: log recebido comprova execução do holdout; não se atribui nova nota de autonomia ou domínio a partir do log. Operações focais para leitura do aluno: recorte por disponibilidade, referência das defasagens, calendário do alvo, entrada exclusiva de X em `predict` e atualização do estado por resultados antigos.
- Léxico aplicado: **inferência** é aplicar um modelo ajustado a uma entrada; **paridade de features** mantém a transformação de treino na emissão; **estado da calibração** reúne resíduos elegíveis; **registro de previsões** conserva o que foi emitido para avaliação futura.
- Próxima ação do aluno: salvar o módulo e executar a CLI com o diretório real do run de holdout e origem `2026-09-01 01:00:00`; enviar o JSON exibido. O aceite desta parte requer alvo ausente (`target_observed_in_input=false`), previsão finita, histórico até 31/08 23h e estado causal rastreável. Confirmada a execução, fecha-se a quarta macroentrega do painel (4/10); até lá permanece 3/10 demonstradas com a quarta parcialmente concluída. Em seguida, avançar para meteorologia real de M04.

**E25 — emissão sem alvo entregue e reconciliada, 22/09/2026**

- O aluno executou `horizon_predict` com origem `2026-09-01 01:00:00` e alvo `2026-09-01 07:00:00`, usando o artefato do run `d401657267524b528120f2c0ca7ea184`. Anexos recebidos: `features_20260901T010000.csv`, `forecast_20260901T010000.json` e `prediction_log.csv`. Foram lidos diretamente como arquivos fornecidos pelo aluno, sem alterações.
- Saída: previsão bruta 57,04960141851238 MWmed, correção média +11,81116575073311 e previsão final 68,86076716924549. Persistência 126,7295 MWmed. A redução projetada frente à última geração é de aproximadamente 45,66%; é uma previsão, sem observação do alvo para calcular seu erro. O modelo atual usa geração histórica e calendário, ainda sem meteorologia.
- Histórico disponível até 31/08 23h, referência de cálculo em 01/09 00h. Correção ativa com 168 resíduos, sem observações elegíveis ausentes e último resíduo disponível às 00h, anterior à emissão das 01h. Alvo esperado para disponibilidade às 09h, sob atraso assumido de 2h. `target_observed_in_input=false`; `model_retrained=false`.
- Hash do modelo informado: `eb148981d50c736de6b6fb4dbf2fa3adf2bae1bb746419a83abe021fc8319e79`. O hash foi recebido no JSON; o professor não teve acesso ao binário para recalculá-lo nesta etapa.
- Conferência do professor: uma linha no CSV de features, com 27 features e quatro timestamps; uma emissão no registro; chaves e previsões coincidentes com o JSON; soma previsão bruta + offset conferida; `lag_1h` igual à persistência; `recent_delta_1h = lag_1h - lag_2h = -17,3305`; quatro harmônicos de hora conferidos para as 07h. Datas e disponibilidade coerentes. Essa conferência não recalcula todas as estatísticas de janela, pois a série original não foi anexada.
- Aceite: quarta macroentrega técnica demonstrada. Painel passa de 3/10 a 4/10, mantendo o mesmo denominador e a distinção entre produto e aprendizagem. Não se atribui nova nota de autonomia apenas por executar o código de referência. A avaliação h+6 permanece encerrada; continuidade em M04.1.

**M04.1 — E26: cadastro real de parques, capacidade e localização**

- Objetivo prático: sair do identificador agregado `CJU_BA5EIGT` para uma tabela com uma linha por usina, coordenadas e pesos de capacidade. Essa tabela define onde consultar previsões de vento e permite posteriormente agregar informações espaciais. Não foi utilizada uma coordenada aproximada da cidade como substituta dos parques.
- Fontes oficiais lidas: [ONS — relação entre conjuntos e usinas](https://dados.ons.org.br/dataset/usina_conjunto), [ONS — capacidade instalada](https://dados.ons.org.br/dataset/capacidade-geracao) e [ANEEL — SIGA diário](https://dadosabertos.aneel.gov.br/pt_BR/dataset/siga-sistema-de-informacoes-de-geracao-da-aneel/resource/2f65a1b0-19b8-4360-8238-b34ab4693d55). CSVs originais baixados pelo professor, incluindo dicionário ONS de relacionamentos. O diretório de saída do módulo conserva respostas originais, URL, horário UTC de coleta, Last-Modified quando presente, ETag quando presente e SHA-256.
- Resultado real do cruzamento para vínculos informados como vigentes em 01/09/2026: 15 usinas, 27 registros ONS de capacidade e 227,7 MW totais. Não se interpreta o número de registros ONS como contagem de aerogeradores. As capacidades por usina coincidem com a potência fiscalizada do SIGA convertida de kW para MW; diferença máxima observada zero. Quinze coordenadas cadastrais completas e pesos que somam 1.
- Usinas e capacidades MW: Amescla 13,5; Angelim 21,6; Barbatimão 16,2; Cedro 12,0; Facheio 16,2; Imburana Macho 8,1; Jataí 16,2; Juazeiro 18,9; Manineiro 13,8; Mulungu 13,5; Pau D'Água 18,0; Quina 10,8; Sabiu 13,5; Umbuzeiro 18,9; Vellozia 16,5. Todos os vínculos selecionados informam início em 30/10/2024 e fim ausente na cópia consultada. Isso não comprova, sozinho, quais dados estavam publicados em 2024/2025.
- Problema real encontrado: a junção literal entre `ceg` ONS e `CodCEG` SIGA retornou zero correspondências, pois o primeiro utiliza sufixo `.01` e o segundo `.1`. Exemplo: `EOL.CV.BA.032090-0.01` versus `EOL.CV.BA.032090-0.1`. `canonical_ceg` normaliza apenas os zeros à esquerda do sufixo numérico, preservando todos os componentes e o valor do sufixo. O vínculo não foi inferido por similaridade de nomes nem por coincidência de potência.
- Segundo problema tratado: o cadastro de capacidade ONS tem vários registros por usina. O módulo agrega potência por CEG antes de juntar à tabela de usinas e ao SIGA. Usa `validate="one_to_one"`, indicador de correspondência e rejeição de ambiguidades. Não elimina duplicatas arbitrariamente. Uma usina sem correspondência, capacidade ou coordenada válida impede a produção de um cadastro aparentemente completo.
- Entrega: `asset_registry.py`, a salvar em `src/renewable_forecast/`. CLI com `--conjunto CJU_BA5EIGT --as-of 2026-09-01 --output-dir data/reference/CJU_BA5EIGT`. Produz `asset_registry.csv`, `metadata.json` e cache original em `raw/`. Reutiliza o cache em novas execuções; `--refresh` é uma atualização explícita que conserva os bytes anteriores. Bibliotecas: urllib da biblioteca padrão para HTTP, pandas para normalização/agrupamento/junções, NumPy para finitude, hashlib/JSON para proveniência. Nenhum novo treino ou instalação de dependência foi solicitado.
- Evidência do professor: executou a CLI completa contra as três fontes públicas, com download real, transformação, escrita e resumo. Confirmou as 15 correspondências, 27 registros agregados, capacidade total e pesos. Uma duplicação deliberada de CEG no SIGA foi rejeitada. São evidências de funcionamento do material de referência, não de reprodução/autoria do aluno.
- Limite temporal explícito: os arquivos consultados são cópias coletadas agora. A relação ONS contém datas de início/fim, embora o portal informe ausência de histórico de versões. `--as-of` filtra os vínculos e as datas de operação informados no cadastro atual; não recupera uma cópia antiga. Coordenadas e capacidades historicamente publicadas ainda não foram verificadas; `historical_snapshot_verified=false`. Manter essa hipótese visível antes de usar o cadastro em backtests históricos.
- Fonte meteorológica em investigação para a próxima unidade: [Open-Meteo Single Runs API](https://open-meteo.com/en/docs/single-runs-api), que preserva rodadas por inicialização UTC. A documentação consultada informa ECMWF IFS HRES desde março de 2024 e outros modelos desde abril de 2026. Foi consultada a documentação, mas nenhuma resposta meteorológica foi baixada nesta etapa. Inicialização não equivale a publicação; a disponibilidade observada/estimada e o fuso da geração precisam ser definidos antes do join. O histórico contínuo de forecasts não substitui automaticamente rodadas selecionadas pelo relógio de emissão.
- Próxima ação do aluno: executar o módulo cadastral, enviar o resumo e a tabela; explicar por que as linhas de capacidade foram agregadas antes da junção e qual chave final deve ser única. A continuidade imediata é consultar uma rodada meteorológica real para os pontos cadastrais, preservando inicialização, validade, coleta e disponibilidade.
- Léxico aplicado: **granularidade** é o que cada linha representa; **chave canônica** é uma representação padronizada do identificador; **cardinalidade** é a multiplicidade permitida na junção; **vigência** indica quando a relação é informada como válida; **coleta** indica quando obtivemos aquela cópia. Não confundir as duas datas.
- Checkpoint reproduzível: `m04_cadastro_fontes.zip` reúne o resultado do professor e as três respostas originais com seus metadados. Hashes: relação ONS `052776ef1c78beebf0d8c1947d4e3cdec5d5bb6c0587f8613be6714a8572b689`; capacidade ONS `afab94be2941e8534a9ba01ebe89a2bd2876baf240f7141548c38d64d28310a4`; SIGA diário `a617d47068df726aa58a22fe3d4d1b0456958654f8d97e0776d577eed459032f`. Atribuições e transformações constam nos metadados do checkpoint.

**M04.1/M04.2 — E27/E28: cadastro reproduzido e primeira rodada meteorológica real**

- Evidência do aluno (E27): `asset_registry.csv` com 15 linhas e 30 colunas e `metadata.json`, coletados em 22/09/2026. Soma de capacidade 227,70000000000002 MW, soma de pesos 0,9999999999999993 (representação de ponto flutuante), CEG único e coordenadas completas. Os três hashes de fonte coincidem com E26. O cadastro foi reproduzido; a explicação da agregação e uma alteração autônoma continuam sem avaliação nova.
- Objetivo atual: obter previsões meteorológicas reais para esses locais com os metadados necessários à futura junção por disponibilidade. Entrega `src/renewable_forecast/weather_runs.py`; o aluno não precisa reinstalar o pacote, repetir a busca HGB ou reexecutar a suíte inteira para esta coleta.
- Fonte escolhida para a amostra: [Open-Meteo Single Runs API](https://open-meteo.com/en/docs/single-runs-api), modelo explícito `gfs_global`, uma rodada de 01/09/2026 00 UTC, 48 horas, `wind_speed_100m` em m/s e `wind_direction_100m` em graus. [Documentação GFS](https://open-meteo.com/en/docs/gfs-api) consultada para variáveis, unidades e grade. O acesso usado é o endpoint público sem credencial, para este laboratório de aprendizagem.
- Limite de cobertura: o arquivo de rodadas GFS dessa API começa em 02/04/2026, segundo a documentação. Não cobre todo o ano da série de geração. A documentação do ECMWF IFS de 9 km menciona hindcasts do ciclo 49R1 desde março de 2024 e mudança de ciclo em maio de 2026; a data inicial do arquivo, sozinha, não prova que toda essa meteorologia existia operacionalmente em cada emissão histórica. Nenhuma rodada ECMWF foi usada neste incremento.
- Verificação HTTP real encontrou duas particularidades não resolvidas pela tabela genérica de parâmetros: Single Runs rejeita `start_hour`; o recorte foi solicitado com `forecast_hours=48`. Para quinze coordenadas, `elevation=nan` deve ter quinze entradas. A resposta omite `location_id` para o primeiro ponto (zero) e informa 1–14 para os demais. A implementação já contempla as três particularidades e valida a associação com IDs estáveis de usina.
- Evidência do professor (E28): executou a CLI completa, com consulta HTTP real, conversão JSON/pandas, gravação dos CSVs e metadados. Foram 15 objetos, 48 horas cada, 720 linhas completas e cinco pontos distintos de grade. Validade de 01/09/2026 00 UTC a 02/09/2026 23 UTC; velocidades finitas e não negativas, direções entre 0 e 360, chave usina/modelo/rodada/validade única. A consulta inicial de um ponto também foi conferida contra a coleta completa: Amescla, lead 0, 8,85 m/s.
- Correspondência espacial: cinco usinas compartilham um ponto GFS com peso de capacidade 0,320158; sete compartilham outro com peso 0,475626; Cedro, Pau D'Água e Vellozia têm um ponto cada, pesos 0,052701, 0,079051 e 0,072464. Coordenadas solicitadas e retornadas são preservadas em `grid_mapping.csv`; não se declara que cada usina tem uma previsão espacial independente. `cell_selection=nearest` e `elevation=nan` explicitam a seleção da grade e desativam downscaling por altitude.
- Contrato de tempo: `weather_run_time` é inicialização UTC, `weather_valid_time` é a hora prevista, `lead_hours` é validade menos inicialização. `weather_available_at = weather_run_time + 6h` é uma hipótese de latência, registrada com `availability_is_assumed=true` e `historical_availability_verified=false`. `weather_fetched_at` registra a coleta real em 22/09/2026. [Documentação de atualizações](https://open-meteo.com/en/docs/model-updates) distingue inicialização, conversão e disponibilidade; seu status atual não comprova publicação de uma rodada histórica.
- Exemplo conferido: emissão didática em 01/09 06 UTC, horizonte energético 6h, validade meteorológica em 01/09 12 UTC e rodada de 00 UTC. O lead do GFS é 12h, embora o horizonte da previsão energética seja 6h. Sob a hipótese de latência, as 15 linhas dessa validade são elegíveis às 06h; nenhuma linha dessa rodada seria elegível às 05h59. Amescla nessa validade: 5,80 m/s e 44 graus. A geração ONS ainda não foi unida a esta tabela.
- Verificações adicionais limitadas a riscos concretos: alteração deliberada de `location_id` para produzir ambiguidade foi rejeitada; reutilização do cache ocorreu com a função de rede impedida de executar; horário original de coleta foi preservado. Não foram solicitados novos testes artificiais nem repetição da suíte ao aluno.
- Arquivos: `response.json`, `metadata.json`, `weather_forecasts.csv` e `grid_mapping.csv`. O metadado vincula SHA-256 do cadastro, parâmetros, IDs na ordem do pedido, SHA-256 da resposta, horário UTC e hipóteses. Resposta desta execução: SHA-256 `d0310340f2403eb4d1a1f077a288752a1fddb11a2b72dd886cf7633cd2f69da2`, coleta `2026-09-22T22:55:32.579988+00:00`. Tempos internos de processamento podem alterar os bytes de outra resposta equivalente; não se exige o mesmo hash numa nova consulta.
- Limites atuais: os horários de geração continuam sem fuso confirmado. O dicionário JSON ONS consultado descreve `din_instante` como data de referência, sem esclarecer o fuso. Manter esta amostra em UTC e confirmar a convenção antes de juntar as fontes. Vento a 100 m é um nível do modelo, não uma medição na altura comprovada do rotor. Pesos cadastrais históricos ainda são hipótese.
- Próxima prática: salvar o módulo no pacote, executar o comando entregue, enviar o resumo, `weather_forecasts.csv`, `grid_mapping.csv` e `metadata.json`. Exercício autoral curto: agrupar `grid_mapping.csv` por latitude/longitude da grade, contar usinas e somar os pesos; interpretar por que deduplicar a grade sem somar pesos altera a representação espacial do conjunto. A unidade seguinte selecionará a rodada mais recente elegível para cada usina e validade, com exemplo de duas rodadas.
- Continuidade do experimento: nenhum treino foi refeito e a previsão h+6 anterior permanece uma referência sem meteorologia. O holdout anterior já foi consumido; melhorias meteorológicas exigirão protocolo de desenvolvimento e nova avaliação final independente. Painel P1 segue 4/10 macroentregas demonstradas, quinta em andamento. Aprendizagem prática guiada e autonomia permanecem registradas separadamente.
- Léxico para fixação: **rodada/run** → `weather_run_time`; **validade/valid time** → `weather_valid_time`; **antecedência/lead** → diferença entre esses dois campos; **latência** → intervalo inicialização/disponibilidade; **coleta/fetch** → obtenção desta cópia; **grade/grid** → ponto meteorológico retornado; **proveniência** → parâmetros, hashes e datas que permitem rastrear a tabela.

**M04.2/M04.3 — E29/E30: pesos por grade e seleção de rodadas elegíveis**

- Evidência do aluno: execução de `weather_runs` para GFS 01/09/2026 00 UTC, 48 horas por usina, 720 linhas, cinco pontos distintos de grade. Coleta informada em 23/09/2026 16:47:56 UTC. Código `notebooks/inspecao_grade.py` e `grid_weights.csv` recebidos. O professor leu o CSV localmente, sem alterar o anexo.
- Conferência: cinco grupos, contagens 1, 1, 1, 7, 5 somando 15, pesos totais 0,9999999999999991. Comparação pelas coordenadas com a referência resultou em cinco correspondências 1:1 e diferença máxima de peso 5,55e-17. Variações apenas de ponto flutuante. A soma dos pesos foi preservada ao reunir usinas com a mesma grade.
- Revisão do código do aluno: `groupby` com agregações nomeadas está correto para esta entrada. `count` sobre nomes conta valores preenchidos, e os nomes recebidos estão preenchidos. Orientação pontual: preferir `id_ons_usina` para contar usinas distintas e manter o arquivo ao lado do `grid_mapping.csv` que o originou, pois os pesos agrupados dependem da grade/modelo e podem mudar entre fontes. As duas cópias em `data/reference/` não são evidência adicional. Nenhuma exclusão de arquivos foi solicitada.
- Entrega ativa: `src/renewable_forecast/weather_asof.py`. Leitor de coletas locais, seletor reutilizável e CLI. Produz `weather_asof.csv`, `coverage.csv` e `metadata.json` com hashes das entradas, política, contagens e hash da saída. Não faz HTTP nem treina modelos; a segunda rodada é coletada pelo `weather_runs` já existente.
- Segunda rodada real conferida pelo professor: GFS 01/09/2026 06 UTC, 48 horas, válida até 03/09/2026 05 UTC, cinco pontos de grade e 720 linhas. Coleta em 23/09/2026 17:39:02.483393 UTC. Disponibilidade assumida em 01/09 12 UTC, conforme latência meteorológica de seis horas.
- Política do seletor: construir todas as decisões usina/modelo/emissão; calcular alvo como emissão + horizonte; juntar por usina/modelo/validade exata; filtrar `weather_available_at <= forecast_origin`; ordenar por inicialização e manter a rodada mais recente elegível. A junção inicial tem cardinalidade 1:m para horizonte fixo e origens únicas; a tabela final é 1:1 por decisão. A disponibilidade é filtrada antes da seleção da rodada.
- Escolha técnica: utiliza igualdade de validade mais filtro temporal e ordenação. A inicialização mais recente elegível pode diferir da publicação mais recente quando há atrasos fora de ordem. O algoritmo não supõe equivalência entre esses dois critérios. O recorte de 1.440 linhas é apropriado para esta implementação explícita; otimização para grande arquivo é uma etapa posterior.
- Resultado real do professor: nove emissões horárias de 01/09 05 UTC a 13 UTC, horizonte energético 6h, 135 decisões. Às 05h, as 15 decisões têm `not_available_at_origin` entre as duas rodadas carregadas; isso não afirma inexistência de uma rodada anterior no provedor. Às 06–11h, seleciona a rodada de 00h; às 12–13h, a de 06h. Total 120 seleções, 15 ausências preservadas. Não preenche ausência com vento zero nem usa rodada futura.
- Exemplo Amescla: emissão 06h/alvo12h/rodada00h/lead12/vento5,80m/s; emissão11h/alvo17h/rodada00h/lead17/vento3,81m/s; emissão12h/alvo18h/rodada06h/lead12/vento4,52m/s; emissão13h/alvo19h/rodada06h/lead13/vento4,78m/s. O horizonte permanece 6h e a antecedência meteorológica depende da idade da rodada.
- Contraprovas do professor, sem solicitar nova suíte ao aluno: aumentar em 1.000 m/s o vento da rodada de 06h em uma cópia não alterou seleções/vento anteriores às 12h; atrasar sua disponibilidade para14h adiou a troca para14h; publicar a rodada antiga às13h não substituiu a rodada mais nova já disponível às12h. Os cenários alterados são simulações identificadas; as respostas originais permaneceram intactas.
- Leitor valida fuso explícito, chaves, completude das horas de cada rodada, modelo, conjunto de usinas, hipótese temporal e consistência da versão cadastral. Confere o hash do JSON original e registra os hashes dos CSVs e metadados lidos; não afirma reconstruir cada valor do CSV a partir do JSON nesta função. A normalização foi executada por `weather_runs`.
- Prática seguinte do aluno: coletar a rodada de06h em outro diretório, executar o seletor com as duas entradas e enviar `coverage.csv` e `weather_asof.csv`. Aplicação autoral: copiar a tabela em memória, atrasar apenas a disponibilidade da rodada de06h para14h e repetir o seletor com emissões até15h; registrar a mudança da troca de rodada. Alterar a cópia preserva o histórico coletado.
- Limites preservados: disponibilidade meteorológica histórica continua assumida; cadastro histórico não verificado. O PDF oficial do dicionário ONS também foi lido nesta rodada e descreve `din_instante` como data de referência, sem especificar fuso ou alinhamento do intervalo. Nenhuma conversão de geração ou associação ao horário meteorológico foi feita. A amostra opera integralmente em UTC.
- Léxico aplicado: **as-of** significa o que seria elegível naquele instante; **cardinalidade1:m** representa várias rodadas candidatas para uma decisão; **elegibilidade** aplica o corte de disponibilidade; **cobertura** conta decisões com meteorologia; **ausência explícita** mantém a decisão mesmo sem candidato utilizável; **invariância temporal** impede alterações em dados indisponíveis de afetarem emissões anteriores.
- Estado: M04.2 reproduzida no recorte; agrupamento do aluno conferido. M04.3 demonstrada pelo professor e entregue, reprodução pendente. A quinta macroentrega continua em andamento, painel P1 4/10. Resultado não constitui novo desempenho preditivo nem conclusão de senioridade.

**M04.3 — E31: diagnóstico de ambiente e simulação do aluno**

- Evidências recebidas em 24/09/2026: duas falhas iniciais de `python -m renewable_forecast...`, código completo de `notebooks/atraso_meteorologico.py`, coleta posterior da rodada GFS 06 UTC concluída e saída do exercício para Amescla. O professor revisou o código e o log; não executou comandos no computador do aluno.
- Diagnóstico observado: o prompt era `(base)` e o erro identificou `C:\Users\marhl\Miniconda3\python.exe`. Aquele processo não encontrou `renewable_forecast`. O ambiente anteriormente validado era `renewable-forecast`, com Python 3.12.13 e pacote editável instalado. A pasta de trabalho e o ambiente ativo são escolhas independentes.
- O aluno acrescentou `src` ao `sys.path` dentro do script e declarou `$env:PYTHONPATH="src"` no terminal. Ambos alteram caminhos de importação; o interpretador continua sendo o escolhido pelo ambiente. A execução posterior da coleta ocorreu ainda sob prompt base, mas o log não mostra qual alteração a tornou importável antes daquele comando. Não se atribui causalidade específica sem evidência.
- Orientação: ativar `renewable-forecast`, remover o PYTHONPATH temporário desta sessão, conferir `sys.executable` e a importação de `renewable_forecast.weather_asof`. Depois remover apenas `import sys` e a chamada `sys.path.append` do notebook, preservando Path/pandas/imports do projeto. Nenhuma reinstalação, criação de ambiente ou novo download meteorológico necessário foi prescrito.
- Coleta real do aluno: rodada 01/09/2026 06 UTC, 15 usinas, 5 pontos, 48 horas/usina, 720 linhas, validade até 03/09 05 UTC; coleta informada `2026-09-24T16:51:30.027191+00:00`. Disponibilidade original assumida 12 UTC.
- Código da simulação: carrega as duas rodadas, usa `weather.copy()`, identifica a rodada de 06 UTC por timestamp com fuso e soma 2h apenas a `weather_available_at`. Constrói origens de 05 a15 UTC, mantém horizonte 6h e imprime Amescla. Não grava a alteração nas coletas originais. Sugestão pontual: filtrar exclusivamente `id_ons_usina == BAEAMC`, usando a chave estável já conhecida.
- Resultado recebido: às 05h aparecem NaT para rodada/disponibilidade, pois nenhuma das duas rodadas carregadas está elegível; das 06h às 13h seleciona rodada 00 disponível 06h; às 14h e 15h seleciona rodada 06 com disponibilidade simulada 14h. Às 14h o alvo é 20h, coerente com h+6. A troca foi corretamente deslocada de 12h para 14h sob a nova hipótese. Esse comportamento não mede acurácia preditiva nem comprova latência histórica real.
- Aprendizagem demonstrada neste incremento: implementação da alteração em cópia, filtro por rodada, uso de Timedelta e execução do seletor; resultado conferido. Não se atribui domínio completo ou consolidação apenas pela execução; a interpretação é explicitada no retorno do professor.
- Artefato ainda necessário para a próxima unidade: a tentativa mostrada de CLI normal `weather_asof` falhou; nenhuma execução normal bem-sucedida ou coverage.csv foi enviada nesta rodada. Orientar a execução normal com as duas coletas existentes, emissões05–15 UTC (mesmo intervalo da simulação), h+6 e saída `data/interim/weather/CJU_BA5EIGT/h6_sample`. Expectativa derivada do intervalo: 11 emissões, 165 decisões, 150 seleções e 15 ausências. Execução no ambiente corrigido e esses arquivos ainda pendentes de confirmação do aluno.
- Continuidade: M04.3 tem a simulação executada, com consolidação da saída normal pendente. M04.4 permanece o próximo incremento, para componentes e agregação espacial do vento. Painel P1 mantém 4/10 macroentregas; nada foi replanejado nem retreinado.
- Léxico aplicado: **ambiente** reúne interpretador/dependências; **caminho de importação** indica onde procurar módulos; **NaT** representa timestamp ausente; **disponibilidade** governa quando a rodada pode ser usada; **cópia** permite simulação sem alterar os dados de origem.

**M04.3 — E32: execução normal confirmada e localização dos CSVs**

- Ambiente comprovado pelo aluno: `C:\Users\marhl\Miniconda3\envs\renewable-forecast\python.exe` e `Importacao OK`, após ativação e remoção do PYTHONPATH temporário. O aluno depois declarou novamente PYTHONPATH; isso não é necessário para a importação que já foi demonstrada.
- Primeira execução normal: origens05–15 UTC, 11 emissões, 165 decisões, 150 selecionadas e15 ausentes. Segunda execução: origens05–13 UTC, 9 emissões, 135 decisões, 120 selecionadas e15 ausentes. Ambas usam `data/interim/weather/CJU_BA5EIGT/h6_sample`; pela implementação entregue, a segunda gravação substitui os arquivos desse diretório.
- Saídas normais: `weather_asof.csv` contém uma linha por usina/emissão; `coverage.csv` contém uma linha por emissão/modelo. Para a última execução bem-sucedida, esperam-se respectivamente135 e9 linhas de dados. A implementação local do professor foi inspecionada: ambas as chamadas `to_csv` e a escrita de metadata.json antecedem o resumo `Arquivos:`. Os arquivos do Windows não foram inspecionados remotamente; a evidência recebida é o log de conclusão.
- A chamada final `python .\src\renewable_forecast\weather_asof.py` não forneceu os argumentos obrigatórios. O parser encerrou antes de carregar dados ou gravar arquivos. Essa falha não apaga as saídas das execuções anteriores.
- O código recebido de `notebooks/atraso_meteorologico.py` termina em `print`, sem `to_csv`; por isso a simulação não gerava um CSV próprio. Orientação pontual: logo após criar `result_baeamc`, dentro de `main`, acrescentar o bloco abaixo. O novo caminho identifica a simulação e não substitui o resultado normal.

```python
    output_dir = Path("data/interim/weather/CJU_BA5EIGT/h6_delay_simulation")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "amescla_delay_2h.csv"
    result_baeamc.to_csv(output_file, index=False)
    print(f"CSV salvo: {output_file.resolve()}")
```

- Execução orientada a partir da raiz do projeto: `python notebooks/atraso_meteorologico.py`. Resultado esperado: 11 linhas de dados para Amescla, origens05–15 UTC e troca da rodada às14h; gravação pelo aluno ainda não confirmada.
- Verificação prática orientada: `Get-ChildItem` na pasta absoluta da saída normal e `Invoke-Item` para abri-la no Explorer. Nenhum novo download, treino ou ampliação da suíte solicitado.
- Fixação lexical aplicada: `print` exibe; `to_csv` grava; `--output-dir` determina a pasta; argumento obrigatório é uma entrada que a CLI exige; repetir o mesmo caminho de saída substitui o conteúdo por padrão neste módulo. A atividade é localizar o artefato real e relacionar seu número de linhas à granularidade.
- Continuidade preservada: seleção normal e simulação de M04.3 executadas. Próximo conteúdo M04.4: componentes do vento e agregação espacial por capacidade. Permanecem as hipóteses de disponibilidade e a pendência do fuso da geração.

**M04.3 — E33: arquivos recebidos e etapa reproduzida no recorte**

- Anexos efetivamente lidos: `weather_asof.csv` (135 linhas,28 colunas), `coverage.csv` (9 linhas,8 colunas) e `metadata(1).json`. A cópia do metadado foi renomeada no upload; no projeto chama-se metadata.json. A listagem do aluno mostra 51150,1189 e1668 bytes respectivamente para seleção, cobertura e metadado.
- SHA256 recalculado da seleção: `65b2fb4717ccde442faaaaa487d8b600ed96d3c9107cc9a46ddba2de7c8bbbbd`, idêntico ao `output_sha256` registrado. Cobertura: `168b5a2d542e6300ad001e9a6cb42c5c25e1c99f5e70e708a155887aaa22c2b6`. A verificação demonstra correspondência entre estes arquivos, não autenticidade independente de toda a cadeia de fontes.
- Nove origens05–13 UTC em01/09/2026,15 usinas cada. Às05h nenhuma selecionada; de06h a13h todas selecionadas. Cento e vinte decisões com meteorologia,15 sem. Chaves sem duplicidades; alvo exatamente origem+6h; validade meteorológica igual ao alvo; disponibilidade selecionada menor ou igual à origem; pesos somam1 por emissão; resumo de cobertura corresponde à seleção.
- O aluno mostrou a gravação de `h6_delay_simulation/amescla_delay_2h.csv` e a tabela com troca às14h. O conteúdo desse CSV específico não foi anexado; confirma-se a execução pelo log, preservando essa distinção de evidência.
- Conclusão técnica restrita: M04.3 reproduzida no recorte entregue. Permanecem sem comprovação a disponibilidade histórica real e o fuso/intervalo da geração; o metadado mantém ambas as verificações como falsas.

**M04.4 — E34: construção de atributos meteorológicos por conjunto**

- Entrega: `weather_features.py`, destino `C:\renewable-forecast-lab\src\renewable_forecast\weather_features.py`. A função `weighted_wind_features` contém o núcleo numérico; `build_weather_features` controla chaves, disponibilidade e cobertura. A CLI lê a pasta produzida por weather_asof, verifica o hash da seleção e grava weather_features.csv e metadata.json em outra pasta.
- Comando do aluno, na raiz: `python -m renewable_forecast.weather_features --input-dir data/interim/weather/CJU_BA5EIGT/h6_sample --output-dir data/interim/weather/CJU_BA5EIGT/h6_spatial_sample`.
- Granularidade final: uma linha por `(forecast_origin, target_time, id_ons_conjunto, weather_model)`. Neste recorte:9 linhas,8 completas. Às05h mantém a emissão, cobertura0 e featuresNaN. Cobertura parcial também produz featuresNaN; não se transforma um subconjunto de usinas em100% do conjunto por renormalização.
- Cinco candidatos de entrada: média ponderada da velocidade, desvio padrão espacial ponderado populacional, médias das componentes u e v e média ponderada das velocidades locais elevadas ao cubo. As quatro primeiras estão em m/s; a última em m³/s³. O desvio espacial não mede turbulência temporal; o termo cúbico não é previsão de potência elétrica.
- Convenção: direção informa de onde vem o vento, medida a partir do norte no sentido horário. Com ângulo em radianos: `u = -speed*sin(angle)`, `v = -speed*cos(angle)`. Referência primária consultada: https://confluence.ecmwf.int/spaces/CKB/pages/133262398/ERA5+How+to+calculate+wind+speed+and+wind+direction+from+u+and+v+components+of+the+wind . A referência documenta a convenção; os dados continuam sendo as previsões GFS arquivadas do projeto.
- Ponderação: os pesos presentes no seletor já representam capacidade por usina. Não se multiplicam novamente pelos pesos da grade. Quando várias usinas compartilham exatamente a mesma previsão, é equivalente somar seus pesos e agregar uma vez por ponto de grade. Conferida essa identidade para os cinco atributos na emissão06h.
- Resultado06h→12h: velocidade média4,242121m/s; desvio espacial1,078481m/s; u médio−3,289537m/s; v médio−2,468008m/s; média dos cubos92,036133m³/s³. Elevar apenas a velocidade média ao cubo dá76,339484m³/s³: a ordem das operações muda o atributo.
- Resultado12h→18h: velocidade média4,059921m/s; desvio0,731058m/s; u3,922520m/s; v0,796784m/s; média dos cubos73,476662m³/s³.
- Verificação do professor, com os anexos reais: função principal/argumentos e gravação executados em pandas2.2.3/NumPy2.3.5;9 linhas lidas,8 completas. Componentes verificadas com vento norte e ventos opostos; cobertura parcial ao retirar Cedro reduz o peso para0,9472990777338598 e mantém features ausentes; disponibilidade futura rejeitada; agregação por15usinas e5pontos equivalente. Não se afirma execução no ambiente Windows do aluno nem aumento da contagem de pytest.
- Referência: `m04_agregacao_vento_referencia.zip` contém os três anexos de entrada com nomes de projeto, resultado e metadado, além do README. SHA256 da saída de referência: `56dedb23834c01834e7f4fff325a7924ef18a418cac84d30e19033913548d6da`. A comparação entre ambientes deve usar valores/timestamps e tolerância numérica, não presumir identidade dos bytes CSV.
- Atividade de transferência: criar `notebooks/inspecao_vento.py`; ler a seleção e filtrar a emissão06h UTC; agregar por coordenadas de grade somando capacity_weight, após confirmar que velocidade e direção são únicas em cada ponto; chamar `weighted_wind_features` antes e depois da agregação; comparar os cinco resultados com tolerância. Não usar média simples das cinco células nem aplicar pesos duas vezes. Enviar o script e o resultado junto da saída do módulo.
- Léxico em operação: **componente** = projeção vetorial (`sin`/`cos`); **ponderação** = contribuição por capacidade (`np.average`); **dispersão espacial** = diferenças entre locais no mesmo alvo; **granularidade** = entidade representada por cada linha (`groupby`); **cobertura** = fração da capacidade com previsão elegível.
- Continuidade: demonstração entregue, reprodução do aluno pendente. Este recorte de setembro não se sobrepõe à série de geração conhecida, encerrada em31/08/2026. Um experimento com meteorologia exige histórico sobreposto, definição explícita do fuso e nova avaliação final; o holdout h+6 anterior continua encerrado. Ainda não há evidência de ganho de MAE por meteorologia.

**M04.4 — E35: agregação reproduzida pelo aluno e papéis das pastas**

- O aluno enviou `weather_features.csv` (9linhas,18colunas), `metadata(2).json` e código/saída de `notebooks/inspecao_vento.py`. O metadado registra execução em28/09/2026 21:04:36 UTC. O CSV contém8emissões completas e a emissão05h ausente, preservada com atributosNaN.
- SHA256 recalculado do CSV: `e10de4adea5dd51f5f6e30f45de3a33ad658153d0c277fd34a09543f4467bc2f`, igual ao metadado. As cinco colunas meteorológicas correspondem à referência do professor com tolerância1e-12, preservando timestamps, horizonte6h e disponibilidade menor ou igual à emissão.
- O hash de código relatado, `de95c4e5df99b5be8843f9bebf1664ed42368640329dd6d8b9c194741a86bd61`, coincide com o módulo entregue quando suas quebras de linhaLF são convertidas paraCRLF. A diferença de hash frente à cópia Linux foi explicada sem atribuir alteração semântica ao código.
- Revisão da atividade: selecionou15usinas às06h UTC; verificou `nunique` de velocidade e direção por coordenada; somou `capacity_weight`; preservou os valores constantes com `first`; comparou os cinco atributos por `np.allclose`. Resultado15→5linhas e diferenças impressas0 em todos os atributos. Implementação e verificação dessa equivalência demonstradas; não se infere domínio geral de estatística ou retenção a partir disso.
- Convenção esclarecida, sem renomear arquivos: `h6_sample/weather_asof.csv` contém a seleção por usina e serve de entrada ao exercício; `h6_spatial_sample/weather_features.csv` contém a agregação por conjunto e é a saída de weather_features. O script do aluno leu o arquivo correto. O professor reconhece que a distinção deveria ter sido explicitada ao orientar os caminhos.
- Ajuste pontual de robustez sugerido: após calcular is_equivalent, lançar AssertionError caso sejaFalse, para impedir que uma falha seja apenas impressa. Não é solicitado repetir coleta ou suíte de testes por esse ajuste.
- Próximo incremento preserva o planejamento: ampliar a construção meteorológica para datas dentro da série de geração. Amostra de setembro encerrada como demonstração da transformação; não é conjunto de treinamento avaliado.

**M04 — E36: piloto de histórico meteorológico em julho**

- Entrega: `weather_history.py`, destino `C:\renewable-forecast-lab\src\renewable_forecast\weather_history.py`. Reutiliza as funções principais de weather_runs, weather_asof e weather_features, comhorizonte6h,latência assumida6h e48horas previstas por rodada. Nenhum código de modelagem ou parâmetros do HGB é alterado.
- Lógica central: construir emissões horárias inclusivas; subtrair6h de disponibilidade; arredondar para baixo ao ciclo de6h UTC; deduplicar as inicializações. Isso determina as rodadas00/06/12/18 necessárias sob a hipótese existente. O coletor preserva respostas originais e reutiliza cache com verificação do protocolo.
- Plano semanal do aluno: origens01/07/2026 06UTC a08/07/2026 05UTC,168emissões. Inicializações01/07 00UTC a07/07 18UTC,28rodadas. Alvos01/07 12UTC a08/07 11UTC. Quinze usinas resultam em2520decisões de seleção e168linhas agregadas se a coleta estiver completa.
- Justificativa temporal: julho está dentro da série de geração conhecida e antecede o holdout que começou em04/08. A documentação Single Runs API consultada em28/09/2026 mantém arquivo dos modelos excetoIFS a partir de02/04/2026: https://open-meteo.com/en/docs/single-runs-api . São previsões de inicializações específicas; a disponibilidade histórica real continua não verificada.
- Comando: `python -m renewable_forecast.weather_history --registry data/reference/CJU_BA5EIGT/asset_registry.csv --origin-start 2026-07-01T06:00:00Z --origin-end 2026-07-08T05:00:00Z --run-root data/external/weather/CJU_BA5EIGT --output-dir data/interim/weather/CJU_BA5EIGT/july_pilot`.
- Caminhos fixos desse piloto: coletas em `data/external/weather/CJU_BA5EIGT/gfs_YYYYMMDDTHHMMZ`; seleção em `data/interim/weather/CJU_BA5EIGT/july_pilot/h6_sample/weather_asof.csv`; atributos em `data/interim/weather/CJU_BA5EIGT/july_pilot/h6_spatial_sample/weather_features.csv`. O diretório july_pilot também recebe plan.json. Os arquivos da amostra de setembro permanecem em seus caminhos anteriores.
- Verificação efetiva do professor: execução do fluxo comHTTP real para inicializações01/07 00UTC e06UTC,48horas/usina/rodada,15usinas. Origens06–17UTC,12emissões completas,180decisões,0ausências. Seleção e agregação gravadas. O planejamento da semana foi conferido quanto aos168instantes e28rodadas; não se afirma execução da semana inteira.
- Referência durável: `m04_historico_julho_referencia.zip` contém as duas coletas reais, respostas originais, metadados, produtos derivados e README com a delimitação da execução do professor.
- Ferramentas e léxico aplicados: **backfill** = preenchimento de dados históricos; **orquestração** = executar etapas existentes em ordem; **retomada** = reaproveitar rodadas já coletadas após interrupção; `date_range`, operações vetoriais em timestamps e funçõesPython ligam o plano temporal à coleta.
- Próximo aceite: aluno envia resumo final e weather_features.csv/metadata.json de july_pilot/h6_spatial_sample. Em seguida, construir a associação com a geração. Fuso e intervalo de referência da geração continuam pendentes; a nova busca em fontesONS não estabeleceu esse contrato. O cadastro segue sem versões históricas verificadas e a disponibilidade é assumida. Nenhuma dessas hipóteses deve ser marcada como comprovada pelo sucesso da coleta.
- O período piloto prepara dados, não demonstra ganho preditivo ou substitui avaliação fora do desenvolvimento. O holdout anterior permanece encerrado; um experimento com meteorologia exige protocolo de comparação e nova avaliação final.

**M04 — E37: piloto semanal recebido e reconciliado**

- Arquivos recebidos: coverage(1).csv com 168 linhas; weather_asof(1).csv com 2.520 linhas e 28 colunas; weather_features(1).csv com 168 linhas e 18 colunas; metadados das duas transformações. As 28 rodadas estão listadas na proveniência; o professor não repetiu as 28 consultas HTTP.
- Emissões de 01/07/2026 06h UTC a 08/07/2026 05h UTC; alvos de 01/07 12h a 08/07 11h UTC. Todas as emissões contêm 15 usinas, cinco pontos de grade e cobertura de capacidade igual a 1. Não há decisões sem meteorologia no piloto.
- Conferências: validade igual ao alvo h+6; disponibilidade menor ou igual à emissão; rodada selecionada igual a floor6h(origem−6h); chaves usina/emissão únicas; soma dos pesos igual a 1. Os cinco atributos foram recalculados das decisões por usina e coincidem com o agregado enviado dentro de tolerância 1e−12.
- Hashes SHA256: seleção `7e62017a98dea976ca5dc561bb822d05a010a32c15c0a37988615c0649ced7e8`; metadado da seleção `977620169e90cbd4bacfa60c7910316b8d76a8c9fbb0f80eaf0e99fbe2292b70`; atributos `96ef667d36b184fd16bc2c796d17712ef62f911326843187eea0d2f506fc3f86`. A cadeia registrada no metadado da agregação confere.
- Aceite: coleta, seleção e agregação semanal reproduzidas pelo aluno. Isso conclui o aceite solicitado em E36. Não constitui avaliação de um modelo meteorológico de geração nem verifica retrospectivamente a disponibilidade real das rodadas.

**M04 — E38: tabela integrada de geração e vento, sob hipótese explícita de fuso**

- Entrega: `weather_training.py`, a salvar em `C:\renewable-forecast-lab\src\renewable_forecast\weather_training.py`. Reutiliza `build_horizon_training_frame` e as listas de features existentes; não altera os construtores anteriores.
- Entrada meteorológica fixa: `data/interim/weather/CJU_BA5EIGT/july_pilot/h6_spatial_sample/weather_features.csv`, acompanhada de seu metadata.json. `h6_sample` continua sendo a seleção por usina; não é a entrada desse módulo.
- Entrada de geração: `data/interim/CJU_BA5EIGT_hourly.parquet`, lida com todo o histórico necessário aos lags de até 168h. Conjunto verificado na coluna id_ons_conjunto quando presente; quando ausente, o identificador informado na CLI é registrado como declaração, sem alegar identificação comprovada pelo nome do arquivo.
- Hipótese de trabalho: timestamps ingênuos da geração são localizados em America/Sao_Paulo. O calendário continua sendo calculado no relógio local do alvo; as chaves são depois convertidas para UTC. Timestamps já cientes são convertidos ao fuso declarado antes da construção. Isso preserva, para a entrada ingênua conhecida, os valores do calendário do baseline anterior.
- Limite explícito: America/Sao_Paulo não foi confirmado pelo contrato da fonte. Também não se estabeleceu se din_instante marca início ou fim de intervalo. O módulo mantém o rótulo de referência fornecido, sem inventar deslocamento de uma hora, e registra `generation_timezone_verified=false` e `generation_interval_semantics=original_reference_label; interval_start_or_end_unverified`. Uma conclusão física de ganho meteorológico exige resolver ou delimitar essas hipóteses no protocolo.
- Junção central: `merge(on=["forecast_origin", "target_time"], how="left", validate="one_to_one", indicator="generation_match")`. O lado esquerdo contém as emissões meteorológicas. Uma origem sem histórico/alvo elegível permanece no resultado, com join_status explícito e model_row_complete=false. O comando grava o diagnóstico e encerra com erro se houver qualquer linha incompleta.
- Contrato do resultado: MODEL_FEATURE_COLUMNS contém 27 features históricas/calendário + 5 de vento, totalizando 32. target_generation é o alvo e não está nessa lista. Timestamps, disponibilidade, estado da junção e nomes de conjunto/modelo são colunas de auditoria, não entradas automáticas do estimador. model_row_complete significa somente completude numérica sob as hipóteses declaradas.
- Exemplo de relógio em 01/07/2026: emissão06UTC=03local; history_end04UTC=01local, com atraso de geração assumido de2h; alvo12UTC=09local; disponibilidade do alvo14UTC=11local. Calendário representa09h locais; vento tem validade12UTC. Igualar03h local a03hUTC associaria outro instante.
- Comando: `python -m renewable_forecast.weather_training --generation data/interim/CJU_BA5EIGT_hourly.parquet --weather-dir data/interim/weather/CJU_BA5EIGT/july_pilot/h6_spatial_sample --conjunto CJU_BA5EIGT --generation-timezone America/Sao_Paulo --horizon-hours 6 --availability-delay-hours 2 --output-dir data/interim/modeling/CJU_BA5EIGT/h6_d2_july_pilot`.
- Saídas: model_frame.csv e metadata.json em `data/interim/modeling/CJU_BA5EIGT/h6_d2_july_pilot`. Metadados registram entradas, alvo, contagens, período, hipóteses, proveniência meteorológica, hashes dos dados e módulos, e training_performed=false.
- Verificação efetiva do professor: meteorologia real E37 + geração sintética horária de15/06 a10/07, com valor100+i, usando o contrato dos construtores de features/supervised compartilhados pelo aluno. Foram obtidas168linhas completas; primeira linha tem lag485 e alvo493, valores exclusivamente sintéticos. Conferidos equivalência do calendário ao baseline, chavesUTC/local, equivalência de timestamps já cientes, invariância das32entradas após adulterar a geração futura, preservação de linha sem alvo e rejeição de chaves duplicadas/disponibilidade futura. Fluxo de escrita da CLI verificado substituindo apenas o leitor de Parquet por geração sintética. O Parquet real e os módulos atuais no Windows não estavam acessíveis; sua execução não é afirmada.
- Ferramentas/léxico aplicados: **localizar** atribui um fuso a um relógio sem fuso; **converter** representa o mesmo instante em outro fuso; **cardinalidade um para um** impede a multiplicação acidental das linhas; **junção à esquerda** conserva as emissões, inclusive as sem correspondência. Estudo focalizado nessas operações e no contrato X/y do módulo, sem uma nova suíte de testes solicitada ao aluno.
- Próximo aceite: executar a CLI no ambiente existente e enviar o resumo, as três primeiras linhas e os dois arquivos gerados. Esperam-se168linhas completas e32entradas, condicionado à série real manter o contrato informado. Em seguida, ampliar o histórico para um experimento de ablação temporal: mesmas emissões, alvos, cortes e orçamento, com e sem meteorologia. Uma semana é um piloto de integração; o holdout anterior não se torna novamente reservado.

**M04 — E39: junção real recebida e verificada**

- Metadados de execução do aluno:28/09/2026 23:32:51 UTC;8.760linhas de geração lidas;168emissões entre01/07 06UTC e08/07 05UTC; todas com geração e meteorologia completas. CSV tem55colunas, das quais32são entradas numéricas e uma é o alvo.
- SHA256 do CSV recalculado:`a07439d686bc1ce8727abccc2f14c9f34c3e5b616289021adcff4be5e4c3123f`, igual ao metadado. CSV meteorológico e seu metadata.json correspondem aos hashes de E37. O código declarado coincide com a versão CRLF do módulo entregue. Hash do Parquet é informação declarada pela execução; o Parquet original não foi anexado.
- Verificações:chaves únicas/horárias; alvo=origem+6h; history_end+2h=origem; target_available_at=alvo+2h; meteorologia disponível até a emissão;32entradas finitas; alvo fora de X; atributos meteorológicos iguais ao arquivo anterior. Foi possível reconstituir343referências de geração a partir dos lags/alvos repetidos; valores sobrepostos coincidem e as27features históricas/calendário foram recalculadas com concordância numérica.
- Primeira linha real:origem01/07 06UTC=03local; histórico até04UTC=01local; alvo12UTC=09local; lag_1h157,556MWmed; geração-alvo48,043MWmed; vento médio9,537128m/s. Estes valores substituem o exemplo sintético na evidência atual, sem alterar seu registro histórico.
- Aceite:integração real do piloto demonstrada. Permanecem explícitas a hipótese America/Sao_Paulo, a semântica início/fim do intervalo não verificada, a disponibilidade histórica assumida e as versões cadastrais não verificadas.

**M03.3/M04 — E40: primeira ablação meteorológica real e ampliação definida**

- Arquivo entregue:`weather_ablation.py`, destino`C:\renewable-forecast-lab\src\renewable_forecast\weather_ablation.py`. Lê model_frame.csv e metadata.json, confere hash e contrato, usa o purged_time_series_splits existente e treina do zero em cada fold.
- Pergunta:com as mesmas emissões, alvos, cortes, parâmetros e orçamento, acrescentar as cinco features meteorológicas melhora o HGB? Braços:hgb_history(27entradas) e hgb_history_weather(32). Persistência usa lag_1h como referência adicional. Ambos HGB sem offset, early_stopping=False e previsões com piso zero.
- Parâmetros congelados:loss=squared_error,learning_rate0,03,max_iter250,max_leaf_nodes15,min_samples_leaf20,l2_regularization1,random_state42. Vieram do desenvolvimento anterior que já incluiu julho; este experimento não é teste final independente nem nova otimização.
- Piloto:168linhas,3folds de24h; treino elegível88/112/136linhas. Rótulos de treino devem estar disponíveis estritamente antes da primeira emissão do fold. Validações começam05/07,06/07 e07/07 às06UTC, total72previsões. Pesos do estimador ficam fixos dentro de cada bloco; cada linha usa as entradas elegíveis em sua própria emissão.
- Resultado agregado sobre as72previsões: persistência MAE66,3076/RMSE79,4914/viés−3,1505; HGB histórico MAE36,3130/RMSE46,7280/viés12,9874; HGB histórico+vento MAE43,0246/RMSE52,6891/viés9,0680 MWmed. A meteorologia piorou o MAE em18,4827% neste piloto.
- MAE por fold(historico→historico+vento):41,2002→58,9134;40,4313→38,7454;27,3075→31,4150. Melhora em um fold, piora em dois. delta_absolute_error=abs(y−pred_histórico)−abs(y−pred_histórico_vento); média−6,7116MWmed. Valor negativo indica piora com vento.
- Limites:apenas três dias validados, treino pequeno, hipóteses temporais ainda abertas e hiperparâmetros originados no desenvolvimento prévio. Os números não são diretamente comparáveis ao holdout de666emissões do modelo anual. Não concluir inutilidade geral da meteorologia ou superioridade estatística de um método; não promover modelo. O resultado negativo é evidência válida do experimento.
- Saídas:protocol.json gravado antes do ajuste; predictions.csv com previsões pareadas e diferença de perdas;fold_metrics.csv;summary.csv;folds.csv com tamanhos/cortes/disponibilidade;metadata.json com hashes. Versões Python/NumPy/pandas/sklearn e hipóteses do dataset preservadas no protocolo.
- Execução do professor usa o CSV real anexado; nenhuma geração sintética é usada na ablação. O contrato do splitter foi reconstruído a partir da função compartilhada na conversa porque o repositório Windows não está disponível. A CLI entregue importa a função existente do projeto do aluno. Versões do ambiente do professor ficam no protocolo; execução no Windows ainda pendente.
- Referência entregue:m04_ablacao_piloto_referencia.zip, com entradas recebidas, módulo, tabelas do experimento, protocolo, metadados e instruções. Permite inspecionar cada previsão que gerou o resumo.
- Reprodução do piloto:`python -m renewable_forecast.weather_ablation --input-dir data/interim/modeling/CJU_BA5EIGT/h6_d2_july_pilot --output-dir reports/weather_ablation/CJU_BA5EIGT/july_pilot --n-splits 3 --test-size-hours 24`.
- Ampliação definida antes de observar seus resultados:origens01/07/2026 06UTC→01/08/2026 05UTC,744emissões e124rodadas;28rodadas já coletadas são reutilizáveis,96adicionais sob cache íntegro. Pasta meteorológica`july_development`, pasta integrada`h6_d2_july_development`, relatório`reports/weather_ablation/CJU_BA5EIGT/july_development`. Parâmetros HGB mantidos;3folds de168h,504previsões, treinos elegíveis232/400/568linhas se a cobertura for integral. Validações começam11/07,18/07 e25/07 às06UTC. Continua sendo desenvolvimento; o holdout anterior não é reaberto.
- Comandos da ampliação, em ordem:
  1. `python -m renewable_forecast.weather_history --registry data/reference/CJU_BA5EIGT/asset_registry.csv --origin-start 2026-07-01T06:00:00Z --origin-end 2026-08-01T05:00:00Z --run-root data/external/weather/CJU_BA5EIGT --output-dir data/interim/weather/CJU_BA5EIGT/july_development`
  2. `python -m renewable_forecast.weather_training --generation data/interim/CJU_BA5EIGT_hourly.parquet --weather-dir data/interim/weather/CJU_BA5EIGT/july_development/h6_spatial_sample --conjunto CJU_BA5EIGT --generation-timezone America/Sao_Paulo --horizon-hours 6 --availability-delay-hours 2 --output-dir data/interim/modeling/CJU_BA5EIGT/h6_d2_july_development`
  3. `python -m renewable_forecast.weather_ablation --input-dir data/interim/modeling/CJU_BA5EIGT/h6_d2_july_development --output-dir reports/weather_ablation/CJU_BA5EIGT/july_development --n-splits 3 --test-size-hours 168`
- Trabalho autoral de interpretação:comparar o sinal e a magnitude do delta por fold, localizar emissões de maior benefício/prejuízo em predictions.csv e formular uma hipótese verificável para a variação. Separar fato observado de hipótese sobre causa; não escolher novo fuso ou hiperparâmetro para favorecer o resultado sem um protocolo próprio.
- Léxico aplicado:**ablação**=alterar um grupo de entradas mantendo as condições de comparação;**comparação pareada**=avaliar duas previsões sobre o mesmo alvo/instante;**purga temporal**=retirar treino com rótulo ainda indisponível;**ganho incremental**=efeito observado de acrescentar o grupo;**generalização**=resultado em situações além do recorte examinado, ainda não demonstrado por este piloto.

**M03.3/M04 — E41: ablação mensal executada e interpretação auditada**

- O aluno reproduziu o piloto E40 e executou a ampliação previamente definida. Log:124 rodadas, 28 reutilizadas e 96 adicionais;744 emissões;11.160 decisões usina/emissão;32 entradas completas no desenvolvimento. Origens de01/07/2026 06UTC a01/08/2026 05UTC. Protocolo criado em29/09/2026 00:26:56 UTC, correspondente a28/09 local. A tabela integrada de744linhas não foi anexada: sua completude provém do log e dos metadados, não de recálculo independente de todas as entradas.
- Recebidos e conferidos:504 previsões, três folds de168horas, treinos elegíveis232/400/568, métricas e protocolos. Hashes dos cinco artefatos e do protocolo reconciliados; hash de código corresponde à versão CRLF entregue. Recalculados erros por linha, deltas, MAE/RMSE/viés por fold e agregado. Emissões únicas/horárias, alvo+6h, disponibilidade+2h e purga estrita antes da primeira validação conferidos. O hash declarado do Parquet permaneceu o mesmo.
- SHA256 de predictions.csv:`291e9aec32608505b4ec7423de814401e372cf3411fcefad001ffeb4a0f7df76`; do protocolo:`c1dfc390bd73ab6658525f8f6e47a453da13200ba1d914fff2f66d24d024d0b4`. O protocolo preserva os hiperparâmetros anteriores e as hipóteses temporais; não há calibração por offset nos dois braços.

| Método | MAE | RMSE | Viés com sinal y−previsão | Viés absoluto médio por fold |
| --- | ---: | ---: | ---: | ---: |
| Persistência | 60,2620 | 75,3058 | 1,4126 | 1,4126 |
| HGB histórico | 32,7444 | 44,1718 | 2,7636 | 10,2382 |
| HGB histórico + vento | 26,4540 | 34,0055 | −1,1720 | 7,0739 |

- Ganho incremental médio:6,2904MWmed, redução relativa de MAE19,2106%;319/504 emissões com menor erro absoluto (63,2937%). Ganhos por fold:11,8074;2,5007;4,5631MWmed. Frações positivas:74,4048%;63,6905%;51,7857%. Esses percentuais são frequência de benefício pareado, não acurácia de classificação.
- O viés do modelo com vento é−12,3689;+2,3317;+6,5212MWmed nos três folds. O quase equilíbrio global esconde deslocamentos semanais. Não se declara aprovação operacional a partir da redução de MAE; o protocolo atual é de ablação e não contém uma nova regra de promoção.
- Maior ganho:emissão11/07 16UTC→alvo22UTC, y49,9555; HGB histórico160,674456 e com vento103,032524; delta+57,641932. Porém persistência50,047, erro0,0915MWmed. Sob o atraso assumido, a geração mais recente às14UTC já estava baixa. Esse registro contradiz a interpretação de que o exemplo comprova antecipação de queda invisível ao histórico. Demonstra redução de uma grande superestimação do HGB histórico; ambos HGB foram piores que a persistência nessa emissão.
- Maior prejuízo:23/07 04UTC→10UTC, y124,935; histórico118,807007, com vento73,181546; delta−45,625461. Persistência174,763, mostrando queda de49,828MWmed em relação ao último valor conhecido. Sem inspecionar a rodada selecionada e vento observado, não se conclui que o NWP previu desaceleração errada: erro na relação aprendida e condições operacionais também são hipóteses. CSV de previsões de geração não mede erro meteorológico.
- Avaliação formativa:extração e síntese numérica corretas. Termos “causal”, “indispensável” e “ruído do NWP” não foram sustentados. Desvio padrão do delta mede variabilidade da diferença de perdas; não mede incerteza do NWP. A ablação sustenta ganho preditivo condicional deste procedimento no recorte, não identifica mecanismo físico/operacional de cada falha.
- O resultado mensal positivo não invalida o piloto negativo. Tanto os tamanhos de treino quanto as datas de validação mudaram; não se atribui a diferença exclusivamente a mais dados. Também não se compara diretamente o MAE mensal bruto ao holdout anual calibrado E24.
- Aceite técnico:quinta macroentrega do P1 demonstrada como experimento integrado exploratório. Painel passa a5/10 por entregas, sem converter isso em50% de senioridade. Fuso, semântica do intervalo, latências assumidas e cadastro histórico seguem delimitados e exigem verificação para homologação operacional.

**M02.3/M02.4 — E42: incerteza do ganho e alcance da conclusão**

- Pergunta:quão sensível é a estimativa média de ganho à composição temporal das perdas observadas? Estimador:d_t=|y_t−h_t|−|y_t−w_t| e média de d_t. Reamostrar o delta mantém cada par de previsões ligado ao mesmo alvo.
- Procedimento definido antes de calcular os intervalos:bootstrap circular com blocos fixos de6,24 e48horas;5.000 réplicas, semente42; sorteios independentes dentro de cada fold; preservar168linhas por fold e pesos observados no agregado. Os blocos mantêm horas consecutivas e retornam do fim ao começo do mesmo fold. Intervalos percentis2,5% e97,5%, nominais95%.

| Escopo | Ganho médio | IC95% bloco6h | IC95% bloco24h | IC95% bloco48h |
| --- | ---: | --- | --- | --- |
| Fold1 | 11,8074 | [5,9084;17,7790] | [3,3783;19,5228] | [2,4449;19,2527] |
| Fold2 | 2,5007 | [−0,3898;5,1690] | [0,9496;3,9353] | [1,0240;3,8615] |
| Fold3 | 4,5631 | [0,3122;9,1198] | [−0,8234;9,9701] | [−1,0396;10,3612] |
| Agregado | 6,2904 | [3,7394;8,9650] | [2,7851;9,4984] | [2,5634;9,5396] |

- Todos os intervalos agregados ficam acima de zero nesta análise. A sustentação por semana depende da convenção de bloco:Fold2 cruza zero em6h, Fold3 em24/48h. Não escolher o tamanho de bloco pelo resultado mais conveniente. Blocos maiores não precisam produzir intervalos monotonicamente mais largos: o resultado depende da estrutura temporal das perdas.
- Limites estatísticos:pressupõe dependência curta e estabilidade aproximada dentro do fold; a costura circular é artificial; não modela dependência entre folds adjacentes. Condiciona-se aos estimadores já ajustados, divisões, pesos, hiperparâmetros e contrato temporal. Não incorpora incerteza de retreino, seleção anterior dos hiperparâmetros ou generalização a regimes inéditos. Três semanas não representam todas as condições do parque. Intervalo da média do ganho não é intervalo preditivo de geração nem p-valor.
- Implementação entregue:`weather_gain_uncertainty.py`, destino`C:\renewable-forecast-lab\src\renewable_forecast\weather_gain_uncertainty.py`. Usa somente NumPy/pandas já presentes. Funções:load_predictions confere pares e frequência; circular_means sorteia blocos; summarize agrega os folds. Não treina modelos, consulta fontes ou usa MLflow.
- Execução:`python -m renewable_forecast.weather_gain_uncertainty --predictions reports/weather_ablation/CJU_BA5EIGT/july_development/predictions.csv --output-dir reports/weather_ablation/CJU_BA5EIGT/july_development/uncertainty --block-hours 6 24 48 --repetitions 5000 --seed 42`.
- Saídas:gain_intervals.csv, extreme_cases.csv, bootstrap_protocol.json e manifest.json. O protocolo é escrito antes dos sorteios e registra hashes, versões, semente e limites. Referência entregue:m04_incerteza_julho_referencia.zip, com dados recebidos, código, resultados e instruções. Verificação do professor:execução nos504pares, invariante de série constante, reprodução da semente e identidade entre ganho médio e diferença de MAEs. Não foi solicitada nova suíte de pytest ao aluno.
- Trabalho autoral seguinte:escrever um parecer curto que (1) decida se os resultados justificam manter o vento como candidato, (2) use ganho agregado e sensibilidade dos folds2/3 como evidência, (3) corrija o argumento do maior ganho confrontando persistência e HGB, e (4) proponha qual observação adicional permitiria investigar a hipótese de falha meteorológica. A resposta precisa distinguir o que foi observado do que ainda é hipótese; não basta repetir “há limitações”.
- Léxico aplicado:pareamento=mesmo alvo/instante; bloco=horas consecutivas reamostradas juntas; estimando=média do ganho que se quer quantificar; intervalo condicional=incerteza sob este protocolo fixo; atribuição causal=exige evidência sobre mecanismo e alternativas além do delta. Retomar estes termos na decisão técnica, sem exercício de completar frases.
- Próxima fronteira de produto após esta interpretação:verificar o contrato temporal na fonte e definir avaliação futura independente antes de novas escolhas. O período reservado E24 permanece encerrado; não rebatizá-lo como teste intocado para a variante meteorológica.

**M02 — E43: decisão técnica do aluno e revisão focalizada**

- O aluno decidiu manter o modelo com vento na esteira de desenvolvimento, citando ganho médio6,29MWmed/19,21%, heterogeneidade semanal e necessidade de vento observado. Reinterpretou corretamente o maior ganho: persistência quase exata, vento apenas reduzindo a superestimação do HGB histórico. Essa resposta demonstra avanço sobre a atribuição causal de E41.
- Ajustes:intervalo agregado[2,56;9,54] corresponde ao bloco48h, não é o mesmo intervalo para6/24h. No Fold2, cruzamento de zero ocorre com6h[−0,39;5,17];24/48h são positivos. No Fold3 ocorre com24h[−0,82;9,97] e48h[−1,04;10,36]. Cruzar zero expressa incerteza quanto ao sinal do ganho médio sob aquele procedimento; não é, isoladamente, demonstração de dependência temporal. Dependência pode ser investigada pela sequência de perdas/autocorrelação e requer interpretação própria.
- Confrontar NWP com anemometria alinhada é uma evidência relevante, com altura, local, intervalo e qualidade compatíveis. Erros de NWP e do modelo de geração podem coexistir; não se trata necessariamente de uma alternativa exclusiva. O reconhecimento dessa observação necessária é aceito como resposta à atividade; não se exige acesso a dados proprietários de usina para prosseguir no experimento exploratório.
- Os doze anexos reenviados nesta sessão correspondem aos mesmos seis arquivos de E41, byte a byte, incluindo protocolo e timestamps. Nenhum novo treino, nova amostra ou execução independente do bootstrap é inferido desses anexos. gain_intervals.csv e bootstrap_protocol.json da execução local do aluno não foram enviados. A interpretação pode avançar sem repetir treino/ablação h6.
- Parecer aceito com as correções pontuais acima; não se atribui domínio global de M02 nem se transforma leitura de resultado fornecido em implementação autônoma. Painel técnico permanece5/10; esta sessão avança evidência de aprendizagem e inicia a sexta entrega.

**M04 — E44: contrato temporal delimitado e início de h+24**

- Fonte primária consultada: [Geração por Usina em Base Horária — ONS](https://dados.ons.org.br/dataset/geracao-usina-2) e [dicionário oficial, páginas1–3](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/DicionarioDados_GeracaoPorUsina.pdf). O dicionário chama din_instante de data de referência, fornece formato DATETIME sem fuso e define val_geracao emMWmed; não explicita fuso nem início/fim do intervalo. O portal informa que valores publicados podem ser revisados. Não foi encontrada nesses documentos confirmação para marcar o fuso/intervalo como verificados. Atribuir atraso fixo ao dado retrospectivo não demonstra disponibilidade histórica de sua versão revisada.
- Decisão de escopo: manter America/Sao_Paulo, atrasos2h/6h e rótulo original como hipóteses já registradas; não selecionar novo alinhamento pelo melhor MAE. A continuação h24 é experimento exploratório sob o mesmo contrato. Homologação operacional requer evidência adicional. O holdout anterior continua encerrado.
- Pergunta nova: o ganho incremental da meteorologia permanece em previsão direta h+24, usando a mesma programação de emissões? Para uma emissão às10h, o histórico disponível com atraso2h termina às08h em ambos horizontes; o alvo é16h no h6 e10h do dia seguinte no h24. O calendário e o vento previsto seguem o novo alvo. Não se deslocam arbitrariamente os lags para24horas atrás, nem se reutilizam os pesos do estimador h6.
- Alteração em weather_history.py: acrescentados --horizon-hours com opções6/24 (padrão6) e --cache-only; diretórios derivados do horizonte. Antes de iniciar a seleção, cache-only exige response.json e metadata.json de todas as rodadas. A validação de protocolo/hash existente permanece em weather_runs. A escolha de rodada continua função da emissão/latência, independente do horizonte. Os arquivos de48horas cobrem o maior lead requerido no h24:24+6+5=35horas após a inicialização.
- Alteração em weather_training.py: somente mensagem de erro da pasta meteorológica, agora informa h{horizonte}_spatial_sample. O construtor e a CLI já aceitavam horizonte variável. weather_ablation.py já lê o horizonte dos metadados, aplica a purga e ajusta novos HGB; não exige outro módulo de modelagem.
- Destinos dos dois arquivos entregues: C:\renewable-forecast-lab\src\renewable_forecast\weather_history.py e C:\renewable-forecast-lab\src\renewable_forecast\weather_training.py. Aplicar essas versões antes do comando com a nova opção.
- Verificação executada pelo professor: duas rodadas GFS reais01/07/2026 00/06UTC em cache,15usinas,12emissões06–17UTC,180decisões sem ausência; alvos02/07 06–17UTC, todas as disponibilidades elegíveis. A chamada de rede foi bloqueada no processo de verificação e nenhuma consulta ocorreu. Conferidos plano mensal e tamanhos do splitter a partir dos relógios; não houve treino h24 mensal; a seleção usa meteorologia real e a purga foi verificada sobre uma grade de relógios, sem inventar geração observada.
- Escopo mensal: mesmos744horários de emissão01/07 06UTC→01/08 05UTC e124rodadas já baixadas. Agora os alvos são02/07 06UTC→02/08 05UTC. Esperadas744linhas completas se a série de geração informada mantiver cobertura. Validação: três folds de168emissões,504previsões. Rótulo disponível em origem+24h+2h: treinos elegíveis214/382/550. No h6 eram232/400/568; diferença18linhas por corte. Regra estrita:target_available_at<primeira_emissão_da_validação.
- Configuração dos estimadores permanece congelada para esta comparação: HGB com27entradas históricas/calendário versus32 com vento, mesmas regras e parâmetros do desenvolvimento h6 anterior, sem offset. Treinam-se novos pesos para alvo h24 em cada fold. Isso não estabelece hiperparâmetros ótimos de h24 e não constitui avaliação final independente.
- Caminhos únicos: `data/interim/weather/CJU_BA5EIGT/july_development_h24/h24_sample` guarda decisões por usina; `.../h24_spatial_sample` guarda agregação. Tabela integrada: `data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development`. Resultado: `reports/weather_ablation/CJU_BA5EIGT/july_development_h24`.
- Comandos sequenciais, executados na raiz C:\renewable-forecast-lab com renewable-forecast ativo; só seguir quando cada etapa concluir sem erro:
  1. `python -m renewable_forecast.weather_history --registry data/reference/CJU_BA5EIGT/asset_registry.csv --origin-start 2026-07-01T06:00:00Z --origin-end 2026-08-01T05:00:00Z --run-root data/external/weather/CJU_BA5EIGT --output-dir data/interim/weather/CJU_BA5EIGT/july_development_h24 --horizon-hours 24 --cache-only`
  2. `python -m renewable_forecast.weather_training --generation data/interim/CJU_BA5EIGT_hourly.parquet --weather-dir data/interim/weather/CJU_BA5EIGT/july_development_h24/h24_spatial_sample --conjunto CJU_BA5EIGT --generation-timezone America/Sao_Paulo --horizon-hours 24 --availability-delay-hours 2 --output-dir data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development`
  3. `python -m renewable_forecast.weather_ablation --input-dir data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development --output-dir reports/weather_ablation/CJU_BA5EIGT/july_development_h24 --n-splits 3 --test-size-hours 168`
- Próxima entrega do aluno: summary.csv, fold_metrics.csv e folds.csv do diretório h24, mais protocolo/metadados para identificar o horizonte. Analisar o ganho de vento dentro de cada horizonte, incluindo sinal por fold. Comparar apenas MAE bruto h6 versus h24 mistura dificuldade dos alvos, período-alvo e tamanhos de treino; o par histórico/vento continua comparável dentro do horizonte.
- Métrica de fixação: ganho relativo incremental=100×(MAE_histórico−MAE_histórico+vento)/MAE_histórico. Não antecipar que o ganho de h24 será maior. Léxico aplicado: horizonte=distância emissão→alvo; lead meteorológico=alvo−rodada; modelo direto=treino específico para y(t+h); cache=reuso da mesma rodada arquivada; purga=exclusão de rótulos ainda indisponíveis no corte.

**M00/M04 — E45: interface executada divergente e retomada da cadeia h24**

- Evidência recebida em 01/10/2026: ambiente renewable-forecast ativo; weather_history rejeita --horizon-hours 24 e --cache-only. weather_training não encontra h24_spatial_sample/metadata.json, e weather_ablation não encontra h24_d2_july_development/metadata.json. A primeira etapa não produziu suas saídas; os demais erros decorrem dessa interrupção. O log não prova se a divergência surgiu no download, destino de substituição ou resolução do módulo.
- Responsabilidade da entrega: faltou conferir a interface efetivamente carregada antes da sequência. A cópia conferida do módulo contém as opções desde E44; a versão distribuída nesta sessão acrescenta RELEASE=2026.10.01-h24 e --version com o caminho do arquivo executado. A parametrização e as pastas de E44 são preservadas.
- Pacote renewcast_h24_20261001.zip: retomar_h24.py na raiz e h24_20261001/weather_history.py como fonte conferida. O script exige Python 3.12, confere os caminhos dos três módulos, valida o hash do módulo entregue, salva a cópia anterior em backups/h24_20261001 e substitui somente weather_history.py. Depois confere --version/--help no mesmo interpretador e executa as etapas existentes com interrupção ao primeiro retorno de erro. weather_training.py e weather_ablation.py existentes são reutilizados.
- Verificação do professor, em Linux: parser reconhece as novas opções; seleção real h24 com duas rodadas arquivadas produz 12 emissões completas, sem chamada de rede. Backup preserva os bytes anteriores. Subprocessos controlados demonstram que falha na etapa 1 impede etapas 2/3, e falha na etapa 2 impede etapa 3. O caminho bem-sucedido das três chamadas foi verificado com módulos mínimos; isso não é treino mensal real nem execução no Windows.
- Próxima ação única: extrair o pacote na raiz C:\renewable-forecast-lab e executar python .\retomar_h24.py no ambiente existente. O programa usa as mesmas datas, hipóteses, hiperparâmetros e saídas de E44. Esperadas 744 linhas completas e 504 previsões por método; nenhuma dessas quantidades foi confirmada por uma nova execução do aluno nesta sessão.
- Léxico aplicado: interface = argumentos aceitos pelo módulo carregado; causa primária = rejeição dos argumentos antes de produzir dados; erro em cascata = consumidor procura uma saída que a etapa anterior não criou. Identificar o caminho/versão executados é parte do diagnóstico, não evidência de domínio autônomo já demonstrado.
- Estado: painel permanece 5/10 = 50%; sexta macroentrega em andamento. Nenhum novo MAE, ganho, bootstrap ou aprovação de modelo é atribuído à correção operacional. Resultados h6 e avaliação reservada anterior permanecem como evidência histórica.

**M03/M04 — E46: experimento mensal h24 executado e auditado**

- Recebidos Texto colado(6).txt, fold_metrics(3).csv, folds(3).csv, metadata(9).json, predictions(3).csv, protocol(3).json e summary(3).csv. Protocolo iniciado em 2026-10-01T20:29:22.930515+00:00 e concluído em 20:29:26.559450+00:00, conforme metadados. O log confirma versão 2026.10.01-h24, backup e três etapas completas no ambiente renewable-forecast.
- Log/metadados declaram 124 rodadas em cache, 744 emissões, 11.160 decisões e 744 linhas integradas completas. Foram recebidas as 504 previsões e seu plano; o model_frame.csv com as 744 entradas não foi anexado. Essa distinção delimita a auditoria de entrada.
- Hashes dos quatro CSVs e do protocolo coincidem com metadata(9).json. MAE, RMSE, viés, erros absolutos por linha, deltas e ganhos percentuais recalculados; divergências inferiores a 1e-10. O hash do módulo de ablação corresponde à cópia de referência com finais de linha Windows.
- Relógios: 504 origens únicas e horárias, três folds de168, alvo=origem+24h, disponibilidade=alvo+2h. Plano de treino214/382/550, última disponibilidade exatamente1h antes do início de validação; purga26h consistente. Isso confere o plano recebido; não equivale a reexecutar ajuste com as 744 entradas ausentes.
- Comparabilidade: listas de27/5atributos, hiperparâmetros e hash declarado da geração iguais a E41. Persistência coincide nas504origens comuns. Valores observados coincidem nos486alvos comuns. Os horizontes usam alvos deslocados18h e quantidades de treino distintas.
- Métricas h24: persistência MAE29,39425694/RMSE43,74178151; histórico MAE38,18211778/RMSE51,26261368; vento MAE28,79800081/RMSE36,53653028. Vento reduz MAE histórico em9,38411697MWmed (24,5773%), e persistência em0,59625613MWmed (2,0285%). No h6, ganhos eram19,2106% e56,1017%, respectivamente. O ganho incremental maior contra histórico não implica superioridade operacional maior.
- Folds1/2/3: ganhos absolutos do vento contra histórico +7,0894/+11,9949/+9,0680MWmed; contra persistência −7,7185/+4,2482/+5,2591. Histórico perde para persistência nos três folds; vento vence em dois. Vento tem menor erro que persistência em220/504emissões (43,65%), mas menor MAE agregado: tamanho dos ganhos/perdas também importa.
- Viés com sinal do vento global+1,5335; folds−16,1503/+11,3100/+9,4407; média absoluta dos vieses12,3003. O agregado próximo de zero compensa erros entre períodos e não demonstra calibração temporal.
- A persistência usa a mesma última geração conhecida para cada origem h6/h24; a verificação elimina uma troca silenciosa desse baseline entre arquivos. Possível papel de ciclos diários na diferença de erro é hipótese para investigação, não explicação causal comprovada por estas métricas.
- Aceite: treino e comparação h24 concluídos no desenvolvimento. A sexta macroentrega ainda exige artefato salvo/recarregado e emissão sem alvo. Próxima entrada necessária: C:\renewable-forecast-lab\data\interim\modeling\CJU_BA5EIGT\h24_d2_july_development\model_frame.csv; hash esperado d142dbaf75a0e18fb203b77dfea8d8377c6d3b1d2c9fc1fc5908b1a50a9a6635. O protocolo já contém seus metadados. Não repetir coleta, ablação ou pytest para entregar esse arquivo.

**M02/M04 — E47: ganho de features e comparação com baseline são perguntas diferentes**

- Reutilizada a função summarize de weather_gain_uncertainty.py sobre E46. Delta recalculado para cada referência: abs(y−referência)−abs(y−vento). Bootstrap circular pareado dentro do fold, pesos fixos pelas contagens, 5.000réplicas, seed42 e blocos6/24/48h. Execução feita pelo professor; não registrar como bootstrap implementado ou executado autonomamente pelo aluno.
- ICs percentis nominais95% agregados vs histórico:6h[5,8353;13,0925],24h[5,2595;13,6790],48h[4,7548;14,0363]MWmed. Contra persistência:6h[−5,3247;6,4924],24h[−7,2504;9,1035],48h[−7,8656;8,8676]. Ganho médio0,5963vs persistência continua observado, mas sua positividade não fica estabelecida por esses intervalos condicionais.
- Limites mantidos: estabilidade aproximada/dependência curta dentro do fold, junção circular fim/início, independência da reamostragem entre folds; não inclui refit, seleção anterior de hiperparâmetros ou incerteza dos contratos temporais. Não é intervalo da geração individual nem teste final independente.
- Decisão técnica do professor: manter candidato h24 com vento em desenvolvimento, preservar persistência e prosseguir à engenharia da inferência. Salvar um artefato para emitir previsões não é promovê-lo a produção; o protocolo permanece model_promotion=false.
- Fixação lexical: ablação mede contribuição das cinco features ao HGB escolhido; baseline mede valor frente a alternativa simples; skill é ganho relativo a uma referência explicitamente nomeada. Interpretação independente do aluno desta nova comparação ainda pendente.
- Relatório: Auditoria_h24_20261001.md, com métricas, intervalos, hipóteses, hashes e próximo arquivo necessário. Estado do produto continua5/10 por blocos inteiros, com treino/comparação da sexta entrega agora demonstrados.

**M04/M06 — E48/E49: artefato h24 e contrato de inferência com autoria**

- E48: CSV real recebido com744linhas e55colunas;32entradas numéricas completas. SHA-256 d142dbaf75a0e18fb203b77dfea8d8377c6d3b1d2c9fc1fc5908b1a50a9a6635 e hash dos metadados coincidem com protocol(3).json. Metadados são iguais ao source_dataset do protocolo.
- Conferência adicional: alvos e lags fornecem937timestamps únicos de geração em uma reconstrução interna; valores repetidos concordam. Janelas6/24/168h, deltas e calendário no fuso declarado foram recalculados e coincidem com o arquivo. Essa reconciliação não é leitura independente do Parquet bruto nem validação da versão histórica dos dados.
- Emissão escolhida para a reprodução:01/08/2026 05UTC; alvo02/08 05UTC; fim do histórico01/08 03UTC; meteorologia disponível01/08 00UTC. Pelo corte estrito de rótulos,717linhas entram e27ficam fora. Última origem de treino31/07 02UTC; último alvo de treino disponível01/08 04UTC.
- Módulo novo weather_artifact.py, release2026.10.01-artifact-1: fit salva o HGB e manifesto; predict recebe JSON sem alvo, valida contrato, recarrega e prevê; replay prepara a reprodução e invoca predict em um processo novo. Reusa HGB_PARAMS e load_model_frame de weather_ablation. Não repete busca ou calibração.
- Artefatos produzidos: model/model.joblib, model/manifest.json, request.json e prediction.json. Manifesto inclui ordem das32features, conjunto, horizonte, atraso, parâmetros, versões, hashes e corte de treino. Pedido contém as features e relógios, exclui target_generation. Uma pasta com outro ajuste é recusada; mesmo contrato/código/dados permite reutilizar o ajuste existente.
- Execução real do professor em Linux/Python3.12.14/sklearn1.8.0: previsão152,7141272748169MWmed; persistência188,294. Novo processo repetiu a previsão com CSV de treino fora do caminho e fit explicitamente proibido. Alterar os27rótulos excluídos não altera o treino selecionado. Alvo no pedido, feature ausente e meteorologia futura são recusados; reordenar chaves do JSON preserva X. O modelo no ambiente do aluno será ajustado com suas bibliotecas (último protocolo:sklearn1.9.0), sem exigir igualdade numérica entre versões.
- Escopo: replay histórico sobre uma linha cujo alvo existe na tabela retrospectiva, mas não é passado ao processo previsor e não está elegível no ajuste. A construção operacional contínua das features a partir de novas fontes é outra camada. Não houve novo cálculo de desempenho, seleção, holdout intocado ou promoção; flags de hipóteses temporais permanecem.
- Ferramentas e operação ensinadas: joblib.dump/load, subprocesso com sys.executable, contrato JSON, nomes/ordem de atributos, corte do conhecimento e manifesto. Fonte primária consultada: [scikit-learn — Model persistence](https://scikit-learn.org/stable/model_persistence.html), especialmente fluxo de recarga e compatibilidade de ambiente.
- Exercício autoral proposto em Aula_Artefato_h24.md: implementar validate_wind_geometry(features), chamada em validate_request antes de montar X. Recusar velocidade média negativa e norma das componentes médias superior à velocidade média escalar+1e-8; aceitar u/v negativos. Norma calculada com np.hypot. Relação deriva da desigualdade triangular para pesos positivos normalizados. Pedido real tem velocidade12,6802767 e norma12,6489974m/s; caso12m/s,u30,v0 deve ser recusado. A solução não foi implementada pelo professor no módulo entregue; é a contribuição do aluno nesta rodada.
- Critério técnico para encerrar a sexta macroentrega: execução do aluno com717linhas,32features, pedido sem alvo, modelo salvo/recarregado, prediction.json e manifesto coerentes. A prova de autoria é avaliada separadamente e não altera retroativamente o critério técnico. Próxima unidade após reprodução:M05, quantis e eventos. Painel permanece5/10 enquanto a reprodução não chega; não se atribui competência nova apenas por receber os arquivos.
- Entrega ao aluno: pacote renewcast_h24_artifact_20261001.zip, contendo src/renewable_forecast/weather_artifact.py e docs/Aula_Artefato_h24.md. Comando replay usa a pasta h24_d2_july_development já existente, origem01/08/2026 05UTC e saída reports/inference/CJU_BA5EIGT/h24_replay_20260801T0500Z. Retorno solicitado:request.json,prediction.json,model/manifest.json e função autoral; binário não necessário.

**M04/M06 — E50/E51: artefato reproduzido e revisão da implementação do aluno (02/10/2026)**

- Arquivos recebidos: prediction.json, request.json, manifest.json, model.joblib e Markdown colado.md. Os arquivos JSON foram lidos integralmente; o código foi revisado removendo apenas escapes e espaços de formatação da transcrição. Não se afirma identidade byte a byte entre a transcrição e o arquivo .py original.
- Hash do modelo: 882942af410ef5674f2083a27556dc0ec02f6970b983a854c26da0a615c99aa9, igual ao manifesto e à previsão. Hash do pedido: 0dfd81cb79f9916097f12023b8c0f5981488bf69424d181f9a2c1fdbb9886d08, igual à previsão. Hashes do dataset e metadados coincidem com E48.
- Conferidos contra a tabela real: origem 01/08/2026 05 UTC, alvo 02/08 05 UTC, histórico até 01/08 03 UTC, disponibilidade meteorológica 01/08 00 UTC, 32 features e seleção de 717 linhas/27 excluídas. Último rótulo disponível no treino: 01/08 04 UTC.
- Previsão registrada: 143,6473739986 MWmed; persistência 188,294. O modelo recebido foi produzido em sklearn 1.9.0 e não foi recarregado pelo professor em sklearn 1.8.0. A diferença em relação aos 152,714 da demonstração anterior não foi atribuída conclusivamente a uma causa. A auditoria confirmou arquivos e contratos; não foi uma reprodução binária em ambiente idêntico.
- E51: o aluno implementou np.hypot, verificação de velocidade negativa, tolerância e chamada após validação numérica. A seleção por substring introduz dependência de ordem e mistura potencial de m/s com m³/s³: a letra u também existe em cubed. Na contraprova, inverter as chaves faz o caso inválido V=12,u=30,v=0 ser aceito e o pedido real ser rejeitado.
- Correção localizada entregue: acessar wind_speed_mean_ms, wind_u_mean_ms e wind_v_mean_ms por nomes exatos. A correção foi conferida com ambas as ordens, velocidade negativa e caso impossível. Aplicação pelo aluno e explicação da invariância pendentes. Usar predict para conferir o contrato corrigido; replay em pasta antiga pode recusar a assinatura de código alterada.
- Decisão: sexta macroentrega concluída conforme critério fixado em E49. Produto P1: 6/10 = 60%. A revisão da autoria segue separada, com implementação parcial reconhecida e sem nota de domínio inventada.

**M05.1 — E52: quantis, cobertura e baseline probabilístico (02/10/2026)**

- Módulo weather_quantiles.py, release 2026.10.02-quantiles-1, usa o dataset h24 já existente e os mesmos cortes da ablação: treino 214/382/550, validação 168 por fold. Ajusta nove HGB: P10/P50/P90 por fold, mesmas 32 entradas, parâmetros anteriores com loss=quantile e tau correspondente, sem tuning adicional.
- Baseline: última geração disponível mais quantis empíricos dos resíduos de persistência no treino elegível. Nenhum alvo da validação entra nesses quantis. Pesos e offsets ficam fixos durante cada fold; features respeitam a emissão de cada linha.
- Modelos quantílicos independentes podem cruzar. Valores brutos e incidência preservados; piso zero e ordenação por linha definidos no protocolo antes da avaliação. Essa operação não garante cobertura. Métricas: pinball por quantil/média, cobertura, erros nas caudas, largura, MAE P50 e interval score 80%.
- Execução real do professor: 504 emissões por método, 1.008 linhas no arquivo longo. HGB cobre 265/504=52,5794%, largura 57,1624 MWmed, pinball média 8,2821, interval score 120,5798; 53 cruzamentos brutos. Baseline cobre 446/504=88,4921%, largura 139,5632, pinball 10,4514, interval score 166,5230.
- Cobertura HGB por fold: 60,7143%, 53,5714%, 43,4524%. Menores perdas agregadas coexistem com cobertura inferior à nominal de 80%; não apresentar o intervalo como risco já calibrado. Nenhum método foi promovido; dados de julho permanecem desenvolvimento exploratório e o holdout antigo segue consumido.
- Entrega: renewcast_m05_quantis_20261002.zip com o módulo novo e Aula_M05_Quantis_h24.md. Pasta de saída definida: reports/probabilistic/CJU_BA5EIGT/h24_d2_july_quantiles_v1. Produz predictions.csv, fold_metrics.csv, summary.csv, folds.csv, protocol.json e metadata.json.
- Prática autoral: notebooks/inspecao_quantis.py com pinball_manual via NumPy, sem mean_pinball_loss, recalculando os três quantis da própria execução; decisão sustentada por cobertura, largura e desempenho semanal. Reprodução, cálculo e interpretação do aluno ainda pendentes. Próxima unidade: calibração temporal, depois previsão de eventos; a macroentrega 7 continua em andamento.

**M05.1 — E53/E54: reprodução probabilística e auditoria da inspeção (02/10/2026)**

- Seis arquivos recebidos, lidos localmente: folds(4).csv, metadata(20261002-214217).json, predictions(4).csv, protocol(4).json, summary(4).csv e fold_metrics(4).csv. Hashes do protocolo, quatro tabelas e duas fontes conferidos. Hash de código compatível com a versão entregue em LF/CRLF. Ambiente do aluno: Python 3.12.13, sklearn 1.9.0, NumPy 2.5.3, pandas 3.0.5.
- 1.008 linhas = 504 emissões por dois métodos. Chaves únicas, saídas finitas, piso/ordenação, incidência de cruzamento, contagens e disponibilidade estrita dos rótulos conferidos. Todas as métricas por fold e agregadas recalculadas a partir das previsões, sem retreinar.
- HGB: pinball P10/P50/P90 = 4,9330386903 / 12,7575013996 / 6,5409139772; média 8,0771513557. Identidade pinball P50 = MAE P50/2 confirmada. Cobertura 279/504=55,3571%, largura 57,6128 MWmed, interval score 114,7395. Abaixo de P10: 73/504=14,4841%; acima de P90: 152/504=30,1587%; cruzamentos brutos: 65/504=12,8968%.
- Coberturas HGB por fold: 60,7143%, 58,3333%, 47,0238%. No Fold 3, 80/168=47,6190% dos alvos estão acima de P90. A diferença entre as caudas indica que uma análise apenas da largura agregada perde informação; não atribuir mecanicamente a causa ao NWP.
- Baseline: cobertura 88,4921%, largura 139,5632, pinball média 10,4513977745, interval score 166,5230. Menor perda do HGB não demonstra calibração em 80%; seu intervalo permanece subcobrindo no recorte. Dados de julho continuam desenvolvimento exploratório.
- E54: pinball_manual apresentada pelo aluno está matematicamente correta nos vetores finitos recebidos. O main procura model em vez de method e q_10/q_50/q_90 em vez de p10/p50/p90. Na ausência dessas colunas, atribui NaN às perdas, deixa o acumulador em zero e divide por três, gerando falsa pinball média 0. Também deixa de separar os dois métodos. Apenas imprimir o resumo não testa equivalência.
- Correção do professor preserva a fórmula; exige contrato explícito, agrupa por method, mapeia níveis aos nomes reais e compara as quatro perdas de cada método com np.testing.assert_allclose. Verifica contagens, nomes e entradas finitas; não aceita NaN como concordância. Script corrigido executado nos anexos com diferenças abaixo de 1e-10. O código foi colado duas vezes na mensagem; se isso ocorreu no arquivo, deve permanecer uma única cópia.
- Entrega: inspecao_quantis.py para C:\renewable-forecast-lab\notebooks. Comando python notebooks/inspecao_quantis.py lê os resultados existentes; nenhum novo treino é necessário. A explicação autoral da cobertura ainda não foi recebida. Próxima prática definida: calibrar intervalos usando exclusivamente rótulos disponíveis antes da emissão, preservando avaliação posterior. Quantis reproduzidos não encerram a macroentrega 7, que inclui calibração e eventos; painel permanece 60%.

**M05.1 — E55/E56: interpretação da perda e calibração temporal (02/10/2026)**

- E55: execução do aluno confirma pinball média HGB8,0771513557 e baseline10,4513977745, com todas as quatro métricas por método reconciliadas. A integração do script corrigido está reproduzida; não continua pendente no painel atual.
- A explicação autoral separa corretamente contagem e magnitude. Refinamentos:10% é nível nominal, não contagem exata em cada amostra (504×0,1=50,4); HGBs quantílicos são ajustados separadamente, sem objetivo explícito de comprimir largura; a minimização populacional da pinball estima quantis. Recalibração é uma intervenção útil a avaliar, não obrigação universal nem garantia de80% em toda semana.
- Decomposição sobre E53: HGB apresenta152 estouros do P90, excesso médio14,9575 e contribuições médias4,0599 dos estouros +2,4810 das folgas =6,5409. Baseline:30 estouros, excesso médio26,8818, contribuições1,4401 +7,9577 =9,3978. Há suporte numérico para o balanço de distâncias neste recorte; a causa do erro do estimador não foi isolada.
- E56: módulo novo weather_interval_calibration.py, release2026.10.02-interval-calibration-1. Entrada única já existente: data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development. Saída do aluno fixada: reports/probabilistic/CJU_BA5EIGT/h24_d2_july_calibration_v1. Não altera arquivos anteriores, coleta ou parâmetros de busca.
- Plano: últimas48 linhas elegíveis antes da avaliação reservadas para calibrar; treino restringido a rótulos disponíveis antes da primeira origem de calibração. Folds com140/308/476 linhas para ajuste,48 para calibração e168 para avaliação. Duas fronteiras estritas e26 linhas de intervalo em cada uma para h24+d2. A janela48h é escolha de piloto anterior a esta execução, não hiperparâmetro ótimo demonstrado.
- Nove HGB ajustados; mesmos estimadores nas previsões de calibração e avaliação, sem refit entre ambas. Piso zero e ordenação preservados. Escore=max(P10−y,y−P90,0); correção=40º menor de48 escores, ceil(49×0,8)=40. Limites lower_80=max(0,P10−correção), upper_80=P90+correção; P50 permanece igual. Correção fixa por semana, apenas expansão. Método inspirado em CQR; não é aplicação automática da garantia sob intercambialidade à série dependente.
- Execução real do professor em Python3.12.14/sklearn1.8.0/NumPy2.3.5/pandas2.2.3. Correções por fold19,693951/0/22,465060MWmed. Cobertura agregada288/504=57,1429%→400/504=79,3651%; largura60,760927→88,866934; interval score125,509003→117,575741; MAE P50 inalterado27,099671.
- Cobertura posterior por fold88,0952%/67,2619%/82,7381%. Fold2 tem40 escores zero em48 casos de calibração e, por isso, expansão zero; o desempenho não se conserva integralmente na semana seguinte. Caudas agregadas após correção:3,5714% abaixo e17,0635% acima. Cobertura central próxima de80% não implica10% por cauda.
- Comparação válida da intervenção: braços sem/com expansão dos mesmos modelos nesta execução. Os55,36% de E53 vêm de outro tamanho de treino e ambiente; comparar diretamente com79,37% confundiria mudanças. Julho continua desenvolvimento exploratório, parâmetros anteriores já viram o período e holdout E24 continua consumido. Nenhuma promoção ou promessa operacional.
- Verificações executadas: tamanhos/cortes, escore manual e rank40, métricas por cálculo independente, medianas iguais/limites apenas expandidos, hashes. No primeiro fold, substituir y da avaliação por100.000 preservou suas previsões e sua correção. Helper de splits reconstruída do código já fornecido pelo aluno; não houve acesso ao repositório Windows completo.
- Entrega: renewcast_m05_calibracao_temporal_20261002.zip, módulo novo, Aula_M05_Calibracao_Temporal_h24.md e sete relatórios de referência mais verification.json. Prática autoral: correcao_manual sem np.quantile/importar a solução; ler escores por fold, reconciliar40º valor e relógios, explicar a semana de menor cobertura com largura e caudas. Reprodução/implementação do aluno pendentes. Em seguida, previsão probabilística de eventos de rampa; não varrer janelas retrospectivas para maximizar julho.
- Progresso:60% por6/10 macroentregas; M05 avança internamente sem encerrar a macroentrega7, que inclui eventos. Registro didático reconhece o resultado do aluno sem atribuir nota global de domínio.

**M05.1 — E57/E58: calibração reproduzida e revisão da auditoria (02/10/2026)**

- E57: log do aluno confirma calibração temporal com ajuste140/308/476, calibração48 e avaliação168. Cobertura51,3889%→77,1825%; largura60,679278→89,870200MWmed; interval score129,852982→120,022226, redução aproximada7,57%; MAE da mediana inalterado26,0864. São resultados relatados; não foram recebidos novos CSVs para uma auditoria completa por hashes/previsões nesta rodada.
- Correções conferidas no log por implementação manual:19,693951/0,619147/23,473284MWmed. Coberturas posteriores88,10%/59,52%/83,93%. Números de referência do professor, como Fold2 com correçãozero e cobertura67,26%, não descrevem esta execução. Diferenças de ambiente existem, mas sua responsabilidade exata pela divergência não foi isolada.
- E58: aluno reconhece a necessidade de intercambialidade e propõe mecanismos para falha temporal. Refinamentos: garantia é marginal; independência é suficiente mas mais forte que intercambialidade; n48 não invalida por si só a garantia em amostra finita; k40 é fixo e varia o valor do40º escore. A frente fria e baixa volatilidade são cenários hipotéticos, não diagnóstico observado; autocorrelação dos erros atuais ainda não foi medida.
- O código autoral usa corretamente sorted, ceil e índice k−1 no caso48. O primeiro KeyError por coluna score foi resolvido na segunda execução com score_mwmed. Retornar0 em amostra vazia e truncar índices encobre erro de domínio: para n3/alpha0,2, k4 não existe, mas o código retornava o máximo observado. Ausência de calibração não significa correçãozero.
- As duas condições do aluno calib_start<eval_start e calib_end<=eval_start verificam origens. Não verificam rótulos de treino e não demonstram disponibilidade de rótulos de calibração. As condições corretas são latest_fit_label_available_at<calibration_origin_start e latest_calibration_label_available_at<validation_origin_start, conforme o protocolo já fixado.
- Script inspecao_calibracao.py mantém o cálculo manual e acrescenta domínio, contrato exato, contagens, fuso, assert_allclose, reconciliação da disponibilidade dos escores com folds.csv e duas fronteiras estritas. Saída inclui zero_scores,rank_k,manual_expansion,reported_expansion e duas condições booleanas. Usa os relatórios existentes, sem treino.
- Verificação do professor: execução aprovada nos relatórios de referência; oito entradas inválidas rejeitadas; contraprovas das duas disponibilidades detectadas. Em uma delas, origens permaneceram iguais e as verificações antigas passariam, mas a disponibilidade no instante do corte viola o protocolo. A auditoria do treino usa o plano exportado, sem reexecutar o estimador. Aplicação do script atualizado pelo aluno pendente.
- Entregas: inspecao_calibracao.py e Revisao_M05_Calibracao.md; pacote/aula da rodada anterior preservados. Próxima execução: python notebooks/inspecao_calibracao.py. Após a conferência, formular evento de queda em h24; comparar geração t+24 com último dado disponível t−2 representa26h entre observações, não rampa horária.
- Progresso técnico permanece6/10 porque a macroentrega7 inclui previsão de eventos. A calibração já executada e o cálculo manual válido são reconhecidos; a inspeção temporal corrigida é a pendência localizada, sem reiniciar o marco.

**M05.1/M05.3 — E59/E60: inspeção concluída e classificação de eventos (03/10/2026)**

- E59: aluno executou a inspeção corrigida sobre seus relatórios. Folds com 48 escores, posição 40, escores zero 16/38/31 e correções manuais iguais às registradas: 19,693951/0,619147/23,473284 MWmed. As duas desigualdades de disponibilidade são verdadeiras nos três folds. Inspeção do plano exportado concluída; não se afirma nova auditoria dos estimadores ou recebimento de novos CSVs completos. Os Ctrl+C aparecem após retorno ao prompt e não anulam a execução concluída.
- E60: módulo weather_events.py, release 2026.10.03-events-1. Define evento positivo por lag_1h−target_generation>=22,77MWmed. O lag remapeado corresponde à última geração em t−2; o alvo é t+24. São 26h entre observações, horizonte de previsão h24. O contrato descreve extremos, não rampa horária nem qualquer queda durante toda a janela. Disponibilidade do rótulo permanece target_available_at.
- Limiar físico fixado antes dos resultados: 22,77MWmed, referência didática de 10% do cadastro227,7MW. É hipótese de desenvolvimento, sem validação econômica ou comprovação da capacidade histórica de julho. Limiar probabilístico inicial0,5 é separado da definição do evento e não foi otimizado na avaliação.
- Três métodos com mesmas 32features/cortes: proporção de eventos do treino elegível; Pipeline(StandardScaler,LogisticRegression C1); HGB classificador com loss=log_loss e parâmetros estruturais anteriores. Nenhuma reamostragem, peso de classe ou recalibração adicional. Scaler ajustado apenas no treino da logística. Seis ajustes, modelos congelados dentro de cada semana.
- Folds: treino214/382/550, positivos52/94/139; avaliação168 cada, positivos38/43/32. Total504 origens,113 eventos, prevalência22,4206%; predictions.csv tem1512 linhas. Tamanho volta ao treino total elegível porque esta comparação de probabilidades não reserva uma terceira partição para recalibrá-las.
- Referência do professor: Brier frequência0,174640, logística0,132262, HGB0,112417; redução relativa do HGB35,6293% contra a frequência. AP média dos folds0,224206/0,674682/0,751761, distinguida de AP pooled0,214277/0,590969/0,681781. AP usa average_precision_score, não integração trapezoidal da PR.
- Em limiar0,5: frequência sem alarmes, FP0/FN113/precision indefinida; logística TP53/FP28/FN60, precision65,43%, recall46,90%; HGB TP74/FP34/FN39, precision68,52%, recall65,49%. Logística tem Brier menor no Fold2 (0,1275 vs0,1431). Log loss da logística0,5362 não supera frequência0,5341; HGB0,4025. Não declarar dominância universal nem calibração comprovada por menor Brier.
- Relatórios: event_labels, predictions, folds, fold_metrics, summary, probability_bins, protocol e metadata. Bins fixos de largura0,2, por fold e agrupados, com contagens; diagnóstico de probabilidades sem ajuste. Protocolo inclui versões, hashes, parâmetros, definição e escopo exploratório. Julho já foi examinado; não há holdout independente ou promoção de alarme operacional.
- Verificações executadas: classe e inclusão do limite; origens idênticas; disponibilidade estrita; frequência só do treino; Brier/matriz reconciliados; scaler ajustado em214 linhas; probabilidades do primeiro fold invariantes à adulteração dos seus alvos futuros; hashes. Helper de splits reproduz código já fornecido, sem acesso ao repositório Windows completo.
- Entrega: renewcast_m05_eventos_20261003.zip com módulo, Aula_M05_Eventos_h24.md e oito relatórios de referência mais verification.json. Entrada data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development; saída reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1. Comando íntegro na aula; nenhuma coleta ou reinstalação necessária.
- Autoria proposta: avaliar_limiar(y,p,threshold,cost_fp=1,cost_fn=4) em notebooks/inspecao_decisoes.py. Calcular TP/FP/FN/TN, precision/recall e custo para0,2/0,5 por método/fold. Cenário didático, sem custos reais fornecidos: alertar custa (1−p) e omitir custa4p; regra teórica0,2 depende da adequação das probabilidades e dos custos. Analisar resultados existentes não os transforma em validação operacional independente.
- Progresso: permanece6/10 macroentregas enquanto o aluno reproduz eventos e defende a decisão. Quantis, calibração e inspeção estão concluídos no protocolo e não permanecem como não iniciados ou pendentes. A aprendizagem em classificação será registrada após a implementação/explicação do aluno.

**M05.3 — E61/E62: classificação reproduzida e decisão por custo (03/10/2026)**

- E61: recebidos folds(5).csv, metadata(20261003-141200).json, predictions(5).csv, probability_bins.csv, protocol(5).json, summary(5).csv, event_labels.csv e fold_metrics(5).csv. Hashes das sete saídas/protocolo correspondem; fonte model_frame.csv d142dbaf75a0e18fb203b77dfea8d8377c6d3b1d2c9fc1fc5908b1a50a9a6635 e metadata da fonte conferem. Código weather_events.py coincide em bytes com o SHA registrado. Isso identifica o material; não substitui execução instrumental dos estimadores nesta auditoria.
- Rótulos744 e previsões1512 (3 métodos ×504 emissões),113 positivos. Todas as definições de queda e relógios h24/d2 conferem; treino214/382/550 e positivos52/94/139 reconstruídos a partir da disponibilidade. Três métodos usam os mesmos alvos/origens; frequência histórica coincide com proporção elegível de cada treino.
- Resumo e métricas por fold recalculados, incluindo Brier, log loss, AP pooled e AP média dos folds;60 bins reconciliados. Resultado próprio do aluno: Brier frequência0,174640/logística0,132262/HGB0,111142; skill HGB36,3594%. Não substituir pelos números anteriores do professor. HGB não domina a logística em todos os folds: Fold2 Brier0,141459 versus0,127503.
- E62: implementação autoral avaliar_limiar preserva a lógica correta de TP/FP/FN/TN e FP+4FN. As24 linhas mostradas coincidem. Toycase enviado y=[1,0,1,0],p=[0.8,0.3,0.1,0.05] produz1/1/1/1,custo5; não confundir com exemplo anterior de probabilidades diferentes. Print rotulado como teste não é uma asserção automática, mas o resultado está correto.
- Os dois erros de caminho foram resolvidos pelo aluno antes desta revisão. Risco remanescente: busca recursiva pode escolher outro experimento ou ignorar caminho explícito errado. Notebook revisado usa um único padrão reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/predictions.csv, opcional explícito, e valida contrato/pareamento; sem busca global. Acrescenta domínio vetorial, razões indefinidas como NaN, custo por emissão e exportação rastreável. Verificado nos anexos e nas contraprovas de forma/valores/caminho/pareamento, sem retreino.
- HGB/0,5: TP74,FP35,FN39,TN356,109 alarmes,custo191. HGB/0,2: TP90,FP66,FN23,TN325,156 alarmes,custo158. Queda de17,2775% no custo assumido e recall65,4867%→79,6460%; precisão67,8899%→57,6923%. São unidades relativas por decisão horária, não dinheiro nem episódios independentes.
- Sensibilidade: ao baixar o limiar, delta de custo normalizado=31−16r; equilíbrio r=1,9375 entre essas duas regras no conjunto observado. Por fold, deltas sob r4 são−31,+4,−6. No Fold2,16 FP adicionais evitam3 FN, equilíbrio r=16/3; logística/0,2 custa72 contra80 do HGB/0,2. Não selecionar retrospectivamente o vencedor de cada semana para alegar política prospectiva.
- Distinção teórica: corte probabilístico C_FP/(C_FP+C_FN)=0,2 sob custos1/4 e probabilidades condicionais adequadas; razão empírica1,9375 compara custos de regras fixas e não é limiar de probabilidade. Menor Brier não comprova calibração. Julho permanece desenvolvimento examinado, sem teste independente de alarme.
- Entrega técnica7 reconhecida: quantis, calibração, classificador e cálculo autoral de decisão reproduzidos. Painel70% por7/10 macroentregas; defesa de decisão, domínio amplo e operação continuam separados. Isso evita tornar detalhes de robustez ou revisão de retenção uma reabertura infinita da entrega técnica.
- Próxima autoria: selecionar_politica(tabela,max_alarms) no mesmo notebook. Cenário didático FP1/FN4, orçamento120 alarmes nas504 emissões; considerar apenas Geral, filtrar capacidade, ordenar custo/alarmes/método/limiar, erro se nenhum viável. Devolver regra e defender o compromisso; não escolher por fold. Política candidata prepara M06, serviço/lote e shadow. Capacidade120 é hipótese pedagógica, não restrição obtida de operação real.
- Pacote renewcast_m05_decisoes_20261003.zip contém notebook, revisão, roteiro atualizado e evidências recalculadas. Fonte de eventos não é modificada. E51 continua pendente; verificação histórica de fuso/intervalo, disponibilidade e cadastro permanece necessária para homologação.

**M05.3/M06.1 — E63/E64: política autoral aceita e primeiro serviço HTTP (03/10/2026)**

- E63: recebidos cost_sensitivity.csv,hgb_tradeoffs.csv,metadata(20261003-171749).json e threshold_metrics.csv. Três hashes de saídas conferem, assim como fonte predictions SHA578ed553c87ef484432bde665f35f5d864a50e5bc2af43b9c47d711d62422e44. Recalculadas24 linhas de decisões,120 de sensibilidade e4 trocas. O metadata informa SHA20eeba1caf42d80d7d13965e1795a82bfa8ca1f9b1b01947d499139593adff6d do notebook; seus bytes originais não foram anexados, portanto não se declara reconciliação desse hash a partir do texto colado.
- Função autoral selecionar_politica filtra Geral,impõe alarms<=max_alarms,ordena custo/alarmes,lança erro quando não existe viável e retorna os campos pedidos. Núcleo aprovado. Sob capacidade120,frequência/0,5 custa452 com0 alarmes; logística/0,5 custa268 com81; HGB/0,5 custa191 com109. HGB/0,2 custa158,mas156 alarmes inviabilizam essa alternativa. Troca aceita custo33 maior no recorte para respeitar a restrição.
- A função recebeu ajustes de integração sem apagar sua autoria: max_alarms inteiro não negativo,desempate por método/limiar e NaN→None antes de JSON estrito. Contraprova concreta: capacidade0 admite frequência/0,5,cuja precisão é indefinida; float(NaN) viola json.dumps(allow_nan=False). Resultado impresso não era artefato de política persistido nos quatro arquivos recebidos.
- Capacidade120 é hipótese didática nas504 emissões;109 observado não garante<=120 em outro período. Política estática p>=0,5 não possui contador/janela/estado. Docstring passa de operacional a candidata de desenvolvimento. A explicação independente dessa diferença é retomada na prática HTTP, sem atrasar o aceite da implementação.
- E64: inspecao_decisoes.py passa a conferir protocolo/metadata do experimento e exportar policy.json em reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions. Documento contém identificação,statusdevelopment,evento/horizonte/atraso,custos,capacidade de seleção,504 linhas,hash da fonte e regra. Metadados incluem hash do novo artefato.
- decision_api.py define SelectedRule/DecisionPolicy/DecisionRequest/DecisionResponse em Pydantic; tipos de probabilidade finita em[0,1],tempos com fuso e campos extras proibidos. Regra pura decidir valida método selecionado,queda22,77,h24 e referência emt−2. FastAPI expõe GET/health,GET/policy e POST/decisions; Uvicorn escuta somente127.0.0.1. Política carregada uma vez; resposta inclui hash e modo development_replay,capacity_enforced_at_runtime=false.
- Escopo delimitado: serviço recebe p_event já calculado. Nenhum estimador é carregado,ajustado ou chamado; não é inferência integral com geração/meteorologia nova. Registrar essa separação impede apresentar replay como shadow ao vivo. Integração do classificador e monitoramento permanecem próximas etapas.
- consultar_api_decisao.py usa biblioteca padrão,confere a fonte por hash e envia a primeira emissão cronológica do método escolhido. Recebeu HTTP200,p0,16175954827073333,limiar0,5,alarmefalso; contraprova p1,2 recebeu422. Pedido não contém alvo realizado. Resultados salvos em reports/service/CJU_BA5EIGT/h24_event_policy_v1.
- Verificação do professor: APIs em memória e via servidor/cliente em processos separados; CLI python -m validada e caminhos padrão testados em projeto temporário. Probabilidades0/0,4999/0,5/1 e igualdade inclusiva conferidas; rejeitados booleano,NaN/Inf,pfora do domínio,data sem fuso,alvo/histórico incompatível,método/queda divergente e alvo realizado como campo extra. Offsets equivalentes normalizam para UTC. Nenhum teste adicional de modelo executado.
- Dependências verificadas: FastAPI0,142.2,Uvicorn0,54.0,Pydantic2,13.5,Starlette1,7.0 em Python3.12. Ambiente temporário isolado; requirements_m06_api.txt entregue. Tentativa inicial com cliente síncrono ficou bloqueada no ambiente de execução; verificação concluída com endpoints assíncronos/ASGI e servidor real separado. Isso não é falha na execução enviada pelo aluno.
- Pacote renewcast_m06_api_decisao_20261003.zip contém notebook atualizado,módulo da API,cliente,requirements,aula,roteiro e evidências. Orientação de dois terminais evita interpretar servidor aguardando pedidos como comando travado. Execução do aluno ainda pendente. Painel permanece7/10; M06 em andamento e E51/hipóteses históricas preservadas.

**M06.1 — E65/E66: replay aceito e contrato explícito no Swagger (03/10/2026)**

- Evidência recebida: request(1).json, decision.json, invalid_request.json, invalid_response.json, verification.json, response_1791070084511.json e duas capturas. O cliente do aluno recebeu HTTP 200 para uma probabilidade histórica real e HTTP 422 para p_event=1,2. A execução da API está aceita; não há obrigação de repetir o cliente.
- O pedido válido refere-se à origem 11/07/2026 06 UTC, histórico até 04 UTC, alvo 12/07/2026 06 UTC, método hgb_weather_classifier e queda de 22,77 MWmed. Probabilidade 0,16175954827073333 é inferior ao limiar 0,5, portanto alarme falso. A fonte de previsões confere com o SHA-256 578ed553c87ef484432bde665f35f5d864a50e5bc2af43b9c47d711d62422e44.
- Swagger enviou outro pedido: historical_frequency, três timestamps iguais e queda 1. A mensagem recebida aponta a primeira incompatibilidade: método diferente da política. O pedido também viola o limiar físico e as relações temporais. O schema genérico aceitava representar vários valores individualmente, mas não explicava sua compatibilidade conjunta com a política carregada.
- Corrigido o exemplo, preservado o contrato: release 2026.10.03-decision-api-2 inclui exemplos OpenAPI nomeados gerados a partir da política. Corpo obrigatório, validações e comparação p >= threshold mantidos. Conferências executadas: respostas reais do aluno reproduzidas, rejeição original reproduzida, exemplo no limiar aceito com alarme verdadeiro e exemplo inválido rejeitado. Nenhum estimador executado.
- Identidade: o hash informado pelo serviço, 309906646dabc7a998a05071982b56dfad1fda140b45383e7b5e3b02d41decb7, coincide exatamente com a referência do professor serializada com quebras CRLF. O JSON de referência preserva o conteúdo; a diferença de bytes explica a diferença de hash LF/CRLF. O arquivo original policy.json do aluno não foi recebido e não foi declarado como inspecionado.
- Entrega localizada: renewcast_m06_swagger_20261003.zip substitui somente o módulo de API e acrescenta revisão, exemplo, evidências e roteiro atual. Não exige reinstalação nem treino. O aluno pode usar imediatamente o corpo JSON correto no Swagger existente; aplicar o pacote e reiniciar o servidor atualiza a documentação.
- Fixação lexical: contrato valida forma e relações; exemplo mostra um pedido concreto; replay reutiliza uma probabilidade histórica; inferência executa o estimador; política converte probabilidade em decisão. capacity_enforced_at_runtime=false continua explícito: o limite observado de 120 alarmes não é uma cota imposta ao serviço.
- Continuidade: M06.1 reproduzida. Próxima entrega é persistência/carregamento do classificador com contrato de features e predict_proba conectado à decisão. Shadow contínuo, monitoramento e avaliação operacional ainda pendentes. Painel permanece 7/10 = 70% pela contagem de macroentregas; o avanço dentro da oitava fica registrado sem arredondamento arbitrário.

**Auditoria de escopo — E67: formação completa versus entregas do P1 (04/10/2026)**

- A crítica do aluno procede: o objetivo contratado é a formação completa; destacar 70% podia sugerir uma conclusão muito mais ampla que a evidência. A versão 1.36 continha duas escalas — dez entregas do P1 e M00–M14 — sem dar prioridade adequada ao estado da formação. O problema de comunicação e medição é do material do professor.
- Contagem conferida: M00 é preparatório; M01–M14 são os 14 marcos substantivos. Há trabalho aplicado em M01–M06. M07–M14 seguem sem entrega prática correspondente. A maior parte das sete entregas do P1 recai repetidamente sobre M02/M03/M04; não são sete marcos curriculares concluídos. A aplicação de Pydantic na API também não conclui o marco de LLMs que utilizará essa ferramenta.
- Correção documental: formação completa passa a abrir o documento, com estado e lacunas de todos os marcos; inventário do P1 fica secundário, com tabela de correspondência. Os antigos percentuais no diário são registros históricos e deixam de orientar o progresso global. Não foi inventado percentual substituto nem foram convertidos estados parciais em créditos arbitrários. Nenhuma competência sem prova passou a concluída.
- A mensagem atual contém o pedido Swagger com método HGB, queda 22,77, histórico duas horas antes, alvo 24 horas depois e p_event=0,5. Esses valores atendem à política descrita. O professor já havia verificado esse corpo em E66. Nesta mensagem não há resposta do servidor; não se registra uma execução nova do aluno. O replay real de E65 continua aceito.
- Orientação precisa: enviar pelo botão Execute em POST /decisions na página /docs. O hyperlink do endpoint sozinho é uma navegação, não o POST com JSON. A colagem tem escapes de formatação; não é apresentada como um comando PowerShell pronto. Esperado para o corpo correto: HTTP 200, threshold=0,5, alarm=true, pela comparação >=.
- Próxima competência de produto preservada: integrar o classificador persistido à decisão, calculando a probabilidade a partir das features. Revisões de autonomia nos marcos anteriores devem usar alterações reais desse fluxo, sem repetir instalações, testes aprovados ou substituir ensino por coleção de execuções.

**M06 — E68: classificador persistido, inferência HTTP e sensibilidade autoral (04/10/2026)**

- A solicitação do aluno foi avançar a entrega já prometida. O professor preparou código executável completo para o fluxo de inferência, sem exigir novo envio dos dados que já estavam disponíveis. A API de decisão anterior permanece compatível; a nova rota POST /predict-decision aceita features e calcula a probabilidade.
- Entrada real: model_frame.csv h24 mensal recebido anteriormente,744 linhas/55 colunas/32 features, SHA-256 d142dbaf75a0e18fb203b77dfea8d8377c6d3b1d2c9fc1fc5908b1a50a9a6635. Política HGB/0,5 já selecionada em E63. CLASSIFIER_PARAMS e a definição de evento foram reutilizados; não houve nova busca de hiperparâmetros.
- Ajuste do professor:717 linhas com forecast_origin e target_available_at estritamente anteriores a01/08/2026 05UTC;170 rótulos positivos. Último rótulo disponível04UTC. Criados model.joblib,manifest.json e example_request.json. O pedido contém as32 features e metadados; não inclui alvo ou probabilidade pronta.
- Resultado verificado: POST /predict-decision retornou HTTP200,p_event=0,20179188830321645,threshold0,5,alarm=false,estimator_executed=true,model_retrained=false. Referência recente188,294 MWmed; evento no alvo <=165,524 MWmed, às02/08 05UTC. Esse evento é de extremidade temporal, não qualquer queda dentro da janela.
- Verificação de integração: servidor e cliente em processos distintos, iniciados no mesmo ambiente de verificação; o diretório da tabela de treino ficou indisponível durante inicialização e chamadas. Cliente conferiu invariância à ordem e rejeição de feature ausente/probabilidade injetada. Outras contraprovas concretas rejeitaram meteorologia futura, emissão antes do corte do modelo, alvo incompatível, alvo injetado, feature textual/booleana/adicional, bytes de modelo alterados e política diferente. Inferência e reutilização de artefato executadas com fit proibido. Rota /decisions anterior preservada.
- Ambiente do professor:Python3.12.14,sklearn1.8.0,pandas2.2.3,numpy2.3.5,joblib1.5.3. O pacote entrega fontes, não um estimador binário para carregar em versão diferente no Windows. O aluno ajustará e servirá no mesmo ambiente renewable-forecast; manifesto registra as versões. Igualdade do número entre ambientes distintos não é critério de aceite.
- Autoria delimitada: notebooks/inspecao_cenarios_evento.py fornece transporte e relatório; aluno implementa escalar_vento sem alterar a entrada. Sob escala s das velocidades locais, média/desvio/componentes escalam por s; média dos cubos por s³. As27 features históricas/calendário ficam fixas. Cenários0,8/1,0/1,2 investigam sensibilidade da probabilidade e alarme, com hashes fixos. Função de referência do professor verificou o programa; a função entregue ao aluno está explicitamente marcada para implementação e não é necessária ao cliente principal.
- Referência docente de sensibilidade: p0,383815/0,201792/0,163667 para fatores0,8/1,0/1,2, todos abaixo do limiar0,5. Resultado hipotético e condicional ao modelo; não é efeito causal nem evidência de qualidade da previsão NWP. O HGB não foi restringido a monotonicidade; o exercício não impõe uma ordem de probabilidades como condição de sucesso.
- Escopo: parâmetros e política foram escolhidos retrospectivamente no desenvolvimento que inclui julho. A simulação histórica serve para conferir a engenharia, não para alegar nova avaliação causal, holdout ou política disponível naquela data. As hipóteses temporais/cadastrais permanecem. Serviço ainda não calcula features a partir das fontes brutas nem monitora operação ou impõe cota acumulada.
- Entrega: renewcast_m06_inferencia_20261004.zip; Aula_M06_Inferencia_Classificador.md; artefato/contratos, API, cliente e exercício autoral. Aceite técnico seguinte exige prediction.json/verification.json da nova rota. Autonomia requer a função,cenários e interpretação. M06 continua em andamento; M07–M14 não avançam por esta entrega.

**Referências de ferramenta, para consulta na unidade correspondente**

São referências de operações, não uma lista de cursos a completar antes de praticar. O código de cada aula deve corresponder à versão efetivamente instalada.

| Marco | Referência oficial e uso |
| --- | --- |
| M02 | [Bootstrap circular — arch](https://bashtage.github.io/arch/bootstrap/generated/arch.bootstrap.CircularBlockBootstrap.html): blocos de comprimento fixo com retorno circular; aplicação didática em NumPy registrada em E42 |
| M03 | [TimeSeriesSplit — scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html): estudar separação temporal e `gap`; confirmar adequação ao horizonte e à disponibilidade dos rótulos |
| M04 | [AsOf Join — DuckDB](https://duckdb.org/docs/current/guides/sql_features/asof_join): estudar junção por igualdade e ordenação temporal |
| M05 | [HistGradientBoostingRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html): perda quantílica e parâmetros do estimador |
| M03/M06 | [MLflow Tracking](https://mlflow.org/docs/latest/ml/tracking/): runs, parâmetros, métricas e artefatos |
| M06 | [FastAPI — tutorial](https://fastapi.tiangolo.com/tutorial/): contratos e serviço; [PyInstaller — funcionamento](https://pyinstaller.org/en/stable/operating-mode.html): empacotamento e restrições da plataforma |
| M07 | [Spark SQL](https://spark.apache.org/docs/latest/sql-getting-started.html) e [Delta Lake no Databricks](https://docs.databricks.com/aws/en/delta/): DataFrames, SQL e tabelas Delta; a segunda documentação usa o contexto AWS, sem implicar escolha dessa cloud para o projeto |
| M08 | [PyTorch — Learn the Basics](https://docs.pytorch.org/tutorials/beginner/basics/intro.html): dados, modelo, autograd, otimização e persistência |
| M09/M11 | [Hugging Face — LLM Course](https://huggingface.co/learn/llm-course/chapter1/1) e [PEFT](https://huggingface.co/docs/peft/en/index): Transformers, tokenização e ajuste eficiente |
| M12 | [Qdrant — início local](https://qdrant.tech/documentation/quickstart/): vetores, payloads e busca |
| M13 | [LangGraph — visão geral](https://docs.langchain.com/oss/python/langgraph/overview): execução com estado, persistência e intervenção humana |

**Histórico deste roteiro:** versão 1.0, 17/09/2026 — consolidação do material recuperável, estados de evidência separados de aprendizagem, marcos M00–M14, provas de autonomia e método léxico aplicado. O roteiro original permanece como registro do escopo anterior.

Versão 1.1, 17/09/2026 — evidência E13 recebida; M00.1 iniciada; trecho, limites da leitura, exercício e próxima ação registrados. Nenhuma nota de aprendizagem atribuída.

Versão 1.2, 17/09/2026 — primeira resposta do aluno preservada; compreensão parcial e lacuna registradas; feedback sobre horizonte, hiperparâmetros e disponibilidade temporal; exercício seguinte definido na mesma M00.1. Unidade permanece em andamento.

Versão 1.3, 17/09/2026 — segunda resposta correta registrada; dificuldade do ensino ajustada ao desempenho demonstrado; aplicação com pareamento h+6 por timestamp e testes adversariais definida. Demonstração do professor validada em dados sintéticos, separadamente da aprendizagem do aluno.

Versão 1.4, 17/09/2026 — evidência E14 recebida: função e 11 testes entregues; revisão reproduziu nulos gerados pela conversão; ajuste e dois casos de regressão definidos; próxima integração vinculada ao `features.py` real. Implementação, testes relatados e verificação local do professor mantidos como evidências distintas.

Versão 1.5, 18/09/2026 — evidência E15: 13 testes passando no ambiente do aluno; rodada de pareamento encerrada nos cenários previstos; continuidade definida na inspeção e integração do `features.py`.

Versão 1.6, 18/09/2026 — aplicação dos pares h+6 ao corte temporal: disponibilidade explícita do rótulo, exclusão de exemplos incompatíveis com cada emissão e ensaio sintético verificado. Exercício de implementação e testes definido; integração das features continua vinculada ao arquivo real.

Versão 1.7, 18/09/2026 — evidência E16: 17 testes e construtor real recebidos; referência temporal das features auditada; integração por emissão com calendário no alvo e atraso explícito demonstrada. Valores, invariância a dados indisponíveis e equivalência h+1 verificados em dados sintéticos; aplicação do aluno pendente.

Versão 1.8, 21/09/2026 — evidência E17: calendário, integração e testes recebidos; falha de coleta diagnosticada no ambiente base/Python 3.13; correção do join de equivalência para `target_time` reproduzida. Próxima ação: ambiente 3.12 e execução da suíte; conexão ao GridSearchCV preservada como continuidade.

Versão 1.9, 21/09/2026 — evidência E18: ambiente recuperado e teste de equivalência corrigido; execução registra 47 aprovações e uma regressão no backtest pela coluna `hour`. Restauração do contrato de saída indicada, com critério de aceite na suíte existente; integração da busca temporal mantida como próximo incremento.

Versão 1.10, 21/09/2026 — E19 registra 48 testes aprovados. Continuidade técnica em M03.3: integração da busca temporal demonstrada em dados sintéticos e primeiro experimento real orientado com reserva dos últimos 28 dias. Aplicação do aluno e métricas h+6 ainda pendentes.

Versão 1.11, 22/09/2026 — E20 registra 50 testes e tuning real h+6 com ganho de MAE de 47,13% no desenvolvimento, reprovado pelo critério de viés. Diagnóstico por fold, persistência de resultados e registro MLflow entregues para a próxima prática; teste final e meteorologia real continuam pendentes.

Versão 1.12, 22/09/2026 — E21/E22 registram diagnóstico h+6 no MLflow, interpretação do aluno e 52 testes aprovados. Experimento de média/mediana de resíduos com disponibilidade estrita entregue; janela e regra de decisão fixadas antes de observar o resultado.

Versão 1.13, 22/09/2026 — E23 registra calibração causal aprovada no desenvolvimento. Média selecionada, protocolo do holdout definido e módulo de avaliação entregue; painel P1 com denominador de dez macroentregas e três demonstradas. Avaliação real reservada e emissão operacional h+6 ainda pendentes.

Versão 1.14, 22/09/2026 — E24 registra avaliação reservada h+6 aprovada pelos três critérios globais, com viés semanal instável e pequeno aumento de RMSE documentados. Emissão sem alvo e registro de previsões entregues e verificados em cenário sintético; execução real do aluno ainda pendente.

Versão 1.15, 22/09/2026 — E25 encerra a quarta macroentrega com emissão h+6 e arquivos reconciliados; painel 4/10. E26 inicia M04.1 com cadastro real ONS/ANEEL executado pelo professor, identificação de 15 usinas e 227,7 MW, código e snapshot entregues. Reprodução do cadastro pelo aluno e consulta meteorológica real ainda pendentes.

Versão 1.16, 22/09/2026 — E27 registra cadastro reproduzido pelo aluno. E28 registra coleta real GFS do professor, 720 linhas e cinco pontos de grade, com módulo e snapshot entregues. Checkpoint ativo atualizado para M04.2; disponibilidade histórica permanece assumida e fuso da geração pendente. Painel 4/10 preservado; próxima integração as-of em M04.3.

Versão 1.17, 23/09/2026 — E29 registra coleta meteorológica e agregação de pesos executadas pelo aluno; E30 entrega seletor as-of conferido em duas rodadas reais. Unidade ativa M04.3, reprodução pendente; próxima agregação espacial e integração temporal com a geração. Painel P1 4/10 preservado.

Versão 1.18, 24/09/2026 — E31 registra falha de importação no base, coleta posterior e simulação de atraso executada pelo aluno. Troca para 14h conferida; retorno ao ambiente renewable-forecast e gravação da seleção normal orientados. Próxima unidade M04.4 preservada.

Versão 1.19, 24/09/2026 — E32 confirma ambiente e seleção normal; registra substituição do recorte05–15h pelo05–13h no mesmo diretório e esclarece execução sem argumentos. Orientadas localização dos CSVs existentes e gravação explícita da simulação em pasta própria. Próxima unidade M04.4 preservada; painel P1 4/10.

Versão 1.20, 24/09/2026 — E33 encerra reprodução de M04.3 neste recorte com arquivos recebidos e conferidos. E34 entrega e verifica agregação de vento por capacidade, com cinco atributos e cobertura explícita. Unidade ativa M04.4; atividade de equivalência por usina/grade proposta. Integração ao modelo e nova avaliação final permanecem pendentes; painel P1 4/10.

Versão 1.21, 28/09/2026 — E35 confirma agregação e atividade de equivalência pelo aluno; papéis de h6_sample e h6_spatial_sample explicitados. E36 entrega orquestração de piloto histórico, conferida com duas rodadas reais de julho. Próximo passo168emissões na semana e associação temporal à geração; hipóteses e painel4/10 preservados.

Versão 1.22, 28/09/2026 — E37 confirma o piloto semanal do aluno:168emissões completas,2.520decisões e cadeia de hashes reconciliada. E38 entrega a tabela de32entradas com junção temporal, preservação do calendário e hipóteses explícitas de fuso/intervalo. Verificação do professor usa geração sintética identificada; execução com o Parquet real permanece o próximo aceite. Painel P1 mantém4/10 macroentregas, sem converter contagem técnica em percentual de domínio.

Versão 1.23, 28/09/2026 — auditoria documental:matrizes iniciais substituídas por estado atual com evidências; painel/checkpoint movidos ao início; diário histórico explicitamente delimitado. E39 confirma junção real de168linhas/32entradas. E40 registra primeira ablação real executada pelo professor, piora de18,4827% do MAE com meteorologia no piloto, e protocolo de ampliação para744emissões/3semanas de validação. Autonomia e entrega técnica seguem separadas;P1 mantém4/10macroentregas.

Versão 1.24, 28/09/2026 local — E41:ablação mensal reproduzida pelo aluno,504previsões auditadas,ganho de19,2106% no MAE e revisão do alcance da interpretação. Quinta entrega técnica reconhecida no escopo exploratório; painel5/10. E42:bootstrap pareado em blocos executado pelo professor,intervalos e limites entregues. Painel,checkpoint,matrizes e registro de aprendizagem atualizados; interpretação estatística do aluno e verificação temporal operacional continuam pendentes.

Versão1.25,30/09/2026 — E43:parecer técnico recebido,interpretação do extremo aceita e mapeamento dos intervalos corrigido; reenvios idênticos identificados. E44:fonte ONS revisada sem confirmação de fuso/intervalo; extensão h24 com cache preparada e verificada em12emissões meteorológicas reais. Sexta macroentrega em andamento,treino mensal do aluno pendente; painel5/10. Matrizes e checkpoint atualizados.

Versão 1.26, 01/10/2026 — E45 registra bloqueio real da execução h24, distingue causa primária de falhas em cascata e entrega pacote com versão/caminho verificáveis, backup e parada automática. Painel, checkpoint, matriz e aprendizagem atualizados; 5/10 preservado; execução mensal do aluno pendente.

Versão 1.27, 01/10/2026 — E46 confirma execução mensal h24 e resolve E45. E47 distingue ganho de features de superioridade sobre persistência, com incerteza condicional recalculada. Painel, checkpoint, matrizes e aprendizagem atualizados; próxima entrega é artefato/inferência sem alvo, condicionada ao recebimento do model_frame.csv já produzido.

Versão 1.28, 01/10/2026 — E48 confirma a tabela mensal real; E49 entrega e executa artefato/inferência h24 em processo separado. Aula inclui autoria de uma validação física das features. Painéis e registros atualizados; reprodução do aluno pendente, sem promoção e sem nota de domínio inventada.

Versão 1.29, 02/10/2026 — E50 encerra a sexta macroentrega técnica e atualiza o painel para 60%. E51 registra autoria parcial e erro de seleção de nomes por substring com correção localizada. E52 inicia quantis h24 com baseline, métricas e resultados do professor. Checkpoint, matriz e registro de aprendizagem reconciliados; reprodução probabilística e revisão autoral do aluno pendentes.

Versão 1.30, 02/10/2026 — E53 confirma o experimento probabilístico do aluno, com todas as métricas reconciliadas. E54 reconhece a fórmula pinball e corrige falha silenciosa de schema/média zero. Painel, checkpoint e aprendizagem atualizados; próxima prática de calibração temporal preservada, sem nova promoção ou alteração da contagem de 60%.

Versão 1.31, 02/10/2026 — E55 encerra a reprodução da inspeção pinball e registra interpretação/refinamentos. E56 entrega calibração cronológica executada com resultados, limites e prática autoral. Painel, checkpoint, matriz e registro de aprendizagem atualizados;6/10 macroentregas, reprodução da calibração e eventos pendentes.

Versão 1.32, 02/10/2026 — E57 registra a execução do aluno com métricas próprias; E58 reconhece o cálculo manual e corrige domínio/fronteiras de disponibilidade. Painel, checkpoint, matriz e aprendizagem reconciliados. Autorização permanente para os arquivos desta pasta registrada.

Versão 1.33, 03/10/2026 — E59 encerra a inspeção da calibração pelo aluno; E60 inicia eventos h24 com alvo explícito, três referências/modelos, avaliação probabilística e tarefa autoral de decisão por custo. Painel, checkpoint, matriz e registro reconciliados; reprodução da classificação pendente.

Versão 1.34, 03/10/2026 — E61 confirma a classificação do aluno; E62 reconhece autoria da matriz/custo e reconcilia 24 linhas. Sétima macroentrega técnica concluída, painel70%; notebook revisado, sensibilidade e política sob capacidade preparam M06. Painel, checkpoint, estado do produto, matriz e registro de aprendizagem atualizados; nenhuma promoção operacional.

Versão 1.35,03/10/2026 — E63 aceita seleção autoral sob capacidade e confere quatro arquivos. E64 inicia M06.1: política persistida,contratos e API local de decisão,replay em processos separados verificado pelo professor. Painel70% preservado; matrizes e checkpoint atualizados; reprodução do serviço pelo aluno pendente.

Versão 1.36, 03/10/2026 — E65 aceita a reprodução HTTP do aluno e reconcilia pedidos, respostas e identidade da fonte. E66 corrige exemplos do Swagger ligados à política, com pedido no limiar verificado. Painel, checkpoint, matriz e registro de aprendizagem atualizados; API replay concluída, integração da inferência do classificador como próxima entrega. 70% preservado.

Versão 1.37, 04/10/2026 — E67: escopos de progresso corrigidos. Painel principal passa a mostrar 14 marcos de formação mais M00, com seis abordados e oito sem entrega prática. Inventário 7/10 do P1 torna-se secundário e recebe correspondência explícita com o currículo. Pedido Swagger reconhecido como correto sem presumir resposta não enviada; próxima entrega de M06 preservada.

Versão 1.38, 04/10/2026 — E68: integração do classificador com artefato e HTTP entregue e executada pelo professor. Aula inclui comandos verificados e autoria por cenários de vento; reprodução/autonomia do aluno pendentes. Painéis e checkpoint atualizados sem alterar o escopo da formação ou atribuir novo percentual global.

Versão 1.39, 05/10/2026 — E69 aceita a integração e a transformação autoral do aluno. E70 entrega lote SQLite e conciliação por disponibilidade, verificados com dados reais. Painel, checkpoint, inventário, matriz e aprendizagem atualizados; M06 em andamento, sem mudar o estado de M07–M14 ou atribuir percentual global.

### E69 — aceite da inferência e autoria de sensibilidade

O pedido recebido tem SHA256 2d13524f017fccd9319922b2a646107b7775f2e085e2d59fa68a88aa3e441b33, coerente com verification(1).json. A resposta identifica modelo7ab0a5cbc45a47df62b3ce44166f090b0ab686481aa37872d25e7c6353a1e17d e política309906646dabc7a998a05071982b56dfad1fda140b45383e7b5e3b02d41decb7. A probabilidade0,2046538537 fica abaixo de0,5; alarme falso. Clocks, referência188,294 e limite165,524 são coerentes. Essa conferência reconcilia documentos, não recalcula o hash do binário não recebido.

A função autoral escalar_vento preserva a entrada e modifica corretamente quatro termos lineares e um cúbico. Log: fator0,8 → p0,326645; fator1 → p0,204654; fator1,2 → p0,158862. Nenhum alarme; sensibilidade hipotética local, não causalidade/calibração. Revisão localizada da versão avulsa: numbers.Real para não aceitar complexos e exigência das cinco features para não ignorar ausências. Não se reabre o exercício aceito. Cenários completos não foram recebidos como arquivos nesta rodada.

### E70 — registro e avaliação diferida de um lote

Foi criado um novo artefato com corte anterior ao lote, preservando h24_event_api_v1. Treino694linhas/168eventos, último rótulo31/07 05UTC; lote31/07 06UTC a01/08 05UTC. EventRuntime executa24previsões semfit. Registro SQLite de configuração/previsões/assessments; transações e idempotência por origem/pedido; banco separado por contrato de lote. Observações não entram nos pedidos.

Às01/08 12UTC há5rótulos elegíveis e19pendentes; às02/08 07UTC há24elegíveis. No ambiente do professor: TP/FP/FN/TN=1/0/0/4 no primeiro corte;2/0/4/18 no segundo, Brier0,114562 e custo16. Não confundir métricas parciais com avaliação de todo o lote. Sete testes passaram; integração real adicional impediufit, impediu recalcular duplicatas, confirmou snapshots e preservação das previsões, e rejeitou artefato ajustado depois do início do lote. Script PowerShell revisado, não executado em Windows; comandos Python equivalentes executados.

Entregáveis: renewcast_m06_lote_20261005.zip, event_batch.py, run_m06_lote.ps1, inspecao_lote_sql.py, test_event_batch.py e Aula_M06_Lote_Conciliacao.md. Banco/modelo são gerados no ambiente do aluno, não distribuídos no ZIP. Notebook de vento do aluno não é sobrescrito pelo pacote.

Próxima autoria: SQL_AUTORAL comJOIN/GROUP BY/SUM/CASE WHEN, duas linhas por corte comobserved,pending,fn,cost_total; defender denominador elegível. Aceite dessa consulta comprova aplicação localizada de SQL, não encerra automaticamente M01. M06 ainda exige monitoramento contínuo, registry/rollback, CI/distribuição; não houve novo holdout, validação causal ou promoção operacional.

### E71/E72 — lote e SQL demonstrados; falha de dados reproduzida

O aluno executou o pacote no Windows: 694 exemplos/168 eventos no ajuste, 24 previsões inseridas e 24 reutilizadas na repetição. Os cortes produziram 5 observados/19 pendentes e 24 observados/0 pendentes. O custo foi 0 e 16; FN foi 0 e 4. Brier do aluno: 0,08030010221150352 e 0,13260301577839723. Os logs confirmam a execução do PowerShell; o ruído de acentuação da mensagem final foi corrigido na versão mantida.

A consulta autoral usa JOIN por origem, GROUP BY por corte, agregações condicionais, NULLIF no denominador e SUM/AVG preservando ausência. A extensão distingue awaiting_label e missing_observation e retorna OK nos dois cortes normais. Foram recebidos o código e as saídas; o banco atual do aluno não foi anexado, portanto não se declara nova verificação byte a byte dele.

A CTE de falha foi fornecida pelo professor; a execução orientada pelo aluno devolveu 4 observados/20 pendentes e 23 observados/1 pendente, ambos investigate, com uma ausência devida. Brier 0,094178/0,137291; custo final 16/23 = 0,695652. Alterar a composição da amostra não demonstra drift. Essa contraprova encerra o exercício; não se exige repeti-lo.

Aceite: SQL aplicado a este registro demonstrado; execução do lote e distinção temporal reconhecidas. Janelas SQL e transferência para outro conjunto continuam sem comprovação. As pequenas alterações anteriores foram excessivamente fragmentadas; a próxima unidade passa a reunir ferramenta, experimento e autoria independente em uma entrega completa.

### E73 — monitor executável e unidade integrada de diagnóstico

Entregues event_monitor.py, config/monitoring_h24_v1.json, Aula_M06_Monitoramento.md, seis testes de contratos e pacote renewcast_m06_monitoramento_20261005.zip. O monitor lê SQLite/modelo/manifesto sem alterações e sem desserializar o estimador. Confere identidade, cobertura de emissões/avaliações, pedido/resposta, fronteiras temporais, rótulos, Brier e custos.

Execução do professor em dados reais: normal → collect_evidence; ausência de observação devida em cópia → investigate_data; probabilidade divergente e avaliação desaparecida → repair_record, com métricas bloqueadas. Banco original preservado. As seis verificações sintéticas cobrem as decisões de triagem, espera legítima, uso precoce de rótulo, identidade e aplicação da regra de desempenho.

Baseline fixo: frequência dos eventos de treino, 168/694. Brier da referência no lote final: 0,187562806766936. O skill descritivo calculado a partir do Brier relatado pelo aluno é aproximadamente 0,293021. Sem novo teste independente, garantia de calibração ou promoção. Regra didática: mínimo 168 observados e revisão se o Brier exceder a referência em mais de 10%; ambos os parâmetros são explícitos e não equivalem a significância estatística.

O painel HTML separa integridade, dados, desempenho e serviço HTTP não medido. Não é monitoramento contínuo, drift detector, quota operacional nem shadow ao vivo. Próxima autoria: notebooks/parecer_monitoramento.py sem importar o monitor, recálculo de baseline/Brier/Skill, parecer.csv dos quatro cenários e parecer.md fundamentando prioridade e limites. Isso reúne SQL, Python, probabilidade e decisão; não há nova tarefa de substituir apenas uma expressão.

Versão 1.40, 05/10/2026 — E71/E72 registram execução/autoria/contraprova recebidas; SQL autoral deixa de constar como não demonstrado nas matrizes atuais. E73 entrega monitor de lote com contratos, referência fixa e triagem. Painel, checkpoint, produto e aprendizagem reconciliados. M06 segue em andamento; M07–M14 inalterados e nenhum percentual global atribuído.

### E74 — reprodução do monitor pelo aluno

O log recebido mostra a execução de event_monitor --exercise no Windows e os quatro relatórios: normal com integridade pass, dados ok, desempenho insufficient_evidence e collect_evidence; missing_observation com investigate_data; changed_probability e missing_assessment com integridade fail, métricas blocked e repair_record. Essa reprodução é aceita. Não foram recebidos o banco e os quatro monitor.json atuais; o aceite se refere ao log de execução.

### E75 — parecer com fonte inválida e correção do contrato de auditoria

Foram lidos integralmente o código anexado em Markdown e os pareceres CSV/MD enviados. Cada par de pareceres é idêntico em bytes. SHA256 do CSV: aa6cb56e8308d6314d30a76ece9748b3a2176ee6ac7e08591596477d37d20171; do Markdown: a0e71eb2799142ed2a1dfd8fb6dab76983ebefd1f2f0698b6d7524b9452b3839. Os originais foram preservados.

A sequência de execução documenta um caminho inicial incorreto, seleção indevida de mlflow.db, procura por extensão .db que não incluía ledger.sqlite e criação de uma base sintética como fallback. O parecer publicou Brier0,281875/Skill−0,502830 e confronto N/A. Esses resultados não auditam o lote. A fórmula de Brier estava correta, mas o programa não assegurava identidade da fonte, corte temporal ou comparação obrigatória antes de declarar sucesso.

Outras falhas: manifesto h24_event_api_v1 em vez do modelo h24_event_batch_v1; tentativa de ler nomes não contratados e fallback fixo de frequência; consulta observed sem as_of, que no ledger normal soma29 linhas de dois snapshots em vez de24 emissões finais; métricas buscadas fora de performance.metrics; tabela de cenários preenchida por constantes; afirmações de representatividade/concept drift não sustentadas pelo mínimo didático168.

A correção preserva a abordagem NumPy e limita a intervenção ao parecer. Usa ledger.sqlite em mode=ro, manifesto do lote com identidade conferida, as_of2026-08-02T07:00:00Z, campos exatos e confronto absoluto1e-9. Não importa event_monitor, não usa a.brier como resposta e não treina. Ausência/incompatibilidade/divergência reprovam antes da publicação. Skill é null quando o Brier de referência é zero. Os quatro cenários são lidos dos relatórios, com conferência de identidade e corte. Saída segregada em parecer_validado preserva os pareceres inválidos anteriores para rastreabilidade.

Verificação do professor: execução na réplica real com24 observações e métricas coincidentes; Brier0,11456217343445767, referência0,18756280676693604 e Skill0,3892063388835312. São valores da réplica do professor, não resultados novos do aluno. Dez verificações dirigidas aprovadas cobrem seleção de snapshot, rejeição de fonte/manifesto/cenário incorretos, métrica ausente/divergente, erro CLI sem publicação, zero/null e preservação do banco. Não houve execução no Windows do aluno nesta revisão.

Os logs anteriores do aluno continuam sendo a evidência de Brier0,13260301577839723 no lote final; com6eventos/24observações e p0=168/694, a referência é0,187562806766936 e o Skill descritivo aproximadamente0,293021. O código não insere esses números: deverá recalculá-los e confrontar os arquivos atuais do aluno. O falso resultado sintético não é atribuído a deriva ou flutuação amostral.

Entrega: renewcast_m06_parecer_20261005.zip com notebook revisado, explicação da revisão, roteiro1.41 e registro de verificação. A implementação corrigida é orientada pelo professor; não recebe crédito de autoria independente do aluno. A próxima ação é executar o parecer e verificar o contrato. Após resolver esse bloqueio localizado, seguir para telemetria HTTP prevista em M06, sem repetir treino ou exercícios encerrados. M07–M14 permanecem inalterados.

Versão 1.41, 05/10/2026 — E74 aceita reprodução do monitor; E75 documenta parecer inválido por fallback sintético e entrega correção de linhagem/contrato verificada pelo professor. Painel, checkpoint, matriz e registro de aprendizagem reconciliados. M06 em andamento; nenhum novo percentual global ou aprovação operacional atribuído.


### E76 — aceite do parecer corrigido e encerramento do bloqueio

Os três arquivos recebidos foram lidos localmente e confrontados com o log:24 observados, Brier0,13260301577839723, referência0,18756280676693604, p0=168/694 e Skill0,2930207322863929. A maior diferença registrada foi1,1102230246251565e-16, abaixo de1e-9. inspection_code_sha256 corresponde ao código entregue em E75; synthetic_fallback_used=false e input_hashes_unchanged=true. Os quatro cenários e ações no CSV coincidem com o Markdown e o log.

A conferência aceita a execução orientada e a coerência dos artefatos. O banco e os JSONs originais do monitor não foram anexados; não se afirma nova leitura direta deles. O parecer gerado pelo código revisado não é contado como texto autoral independente. O bloqueio técnico está encerrado; não é necessário reenviar síntese ou repetir o exercício.

### E77 — telemetria HTTP e análise de incidentes

Entregues http_telemetry.py, service_exercise.py, run_m06_telemetria.ps1, test_http_telemetry.py, Aula_M06_Telemetria_HTTP.md e renewcast_m06_telemetria_20261005.zip. A instrumentação envolve a API existente sem mudar o modelo, a política ou os módulos anteriores. JSONL por requisição inclui ID gerado no servidor, duração, status, conclusão da resposta e identidade do artefato.

Fluxo em HTTP real no ambiente do professor:1 aquecimento separado;20 respostas200 normais;5 rejeições422 de campo proibido;20 requisições de incidente,18 respostas200 (3 com750ms adicionais) e2 falhas500 injetadas. Cliente e servidor conciliados1:1. Seis testes relevantes passaram; a integração foi executada comfit proibido e confirmou artefatos preservados. As38 respostas200 medidas conservaram a probabilidade do mesmo pedido. Na réplica, normalP95≈4,80ms; incidenteP95≈756,62ms e mediana≈3,63ms. Esses tempos não são metas para o computador do aluno.

Regra didática declarada: investigar taxa5xx>1% entre2xx+5xx ouP95 de respostas200>250ms.4xx são contabilizados separadamente. Com zero elegíveis, taxa/P95 ficam indefinidos. A carga é sequencial, repetida e com falhas marcadas; não constitui benchmark de concorrência, uptime, shadow ao vivo ou avaliação de qualidade do modelo.

Próxima entrega autoral: notebooks/diagnostico_servico.py lê requests.csv da execução explícita, verifica identidade, calcula indicadores por fase sem importar summarize, identifica requisições problemáticas e fundamenta decisão comrequest_id. Entregas esperadas: código, diagnostico.csv, incidentes.csv, decisao.md e verification.json da execução. Critérios e caminhos estão definidos na aula. Revisar o conjunto completo, sem novas tarefas fragmentadas sobre o parecer anterior.

Versão1.42,05/10/2026 — E76 aceita a conferência corrigida; E77 entrega o próximo bloco deM06 com ferramenta, experimento, autoria e critério de conclusão explícitos. Matrizes, checkpoint e registro reconciliados. M06 permanece em andamento; M07–M14 sem alteração; nenhum percentual global atribuído.


### E78 — telemetria executada e núcleo autoral do diagnóstico reconhecido

Recebidos em 05/10/2026: diagnostico_servico.py colado, client_requests.csv, server_requests.jsonl, requests.csv, summary.csv, verification.json, incidentes.csv e log. Run 1c51054df97b439fa22c7d2dcc9f6edd. Os quatro SHA-256 conferem com os campos exatos do manifesto. Cliente e servidor contêm 46 chamadas, uma de aquecimento; as 45 medidas têm IDs únicos e correspondência exata. Campos de fase, status e duração coincidem nos registros relacionados.

Normal: 20 sucessos, taxa 5xx zero, mediana 36,02250 ms e P95 43,845195 ms. Invalid_payload: cinco rejeições, sem chamadas elegíveis ou latência de sucesso. Incident: 18 sucessos, duas falhas, taxa 0,1, mediana 35,30995 ms e P95 800,7413 ms. Os dez incidentes selecionados pelo aluno são exatamente cinco rejeições, três sucessos lentos e duas falhas. Nas 38 respostas bem-sucedidas, a probabilidade permanece igual para o mesmo pedido e modelo. Isso não avalia acurácia.

Aceite autoral: máscaras de classe HTTP, contagens, denominador 2xx + 5xx, mediana/P95 quando existe amostra, seleção dos dez registros e prioridade dos 5xx. Revisão necessária: 0/0 e percentil vazio transformados em zero; hash aceito em qualquer texto JSON; busca recursiva escolhe UUID por ordem lexicográfica; falhas deliberadas descritas como exceções não tratadas. O notebook não gravava diagnostico.csv nem decisao.md.

### E79 — revisão localizada de contrato e decisão

Entregues diagnostico_servico.py, Revisao_M06_Diagnostico_Servico.md e renewcast_m06_diagnostico_20261005.zip. Entrada por --run-dir ou latest_run.json; nenhum fallback. Hash comparado a output_sha256[nome]; colunas e unidades explícitas. Métricas indefinidas preservam NaN; incidente conserva ID, fase e marca. Trinta e três comparações com o resumo são obrigatórias; saídas em run_id/autoria incluem diagnostico.csv, incidentes.csv, decisao.md e conferencia.json.

As falhas 2edffe09155646bfbb27d5e43ecaf82f e 4fb0af4d1177493a9c1472605e844cb9 duraram 0,4430 e 0,7331 ms, marcadas error, sem error_type. O código do exercício retorna 500 antes do estimador; não há exceção espontânea comprovada. Atrasos marcados slow explicam a cauda deste exercício. A fase normal é anterior, não prova de recuperação posterior. Probabilidade repetida é repetibilidade localizada, não calibração ou desempenho preditivo.

Verificação do professor nas cópias dos anexos reais: 33 confrontos aprovados, dez IDs iguais, entradas preservadas. Contraprovas rejeitaram zero onde indefinido, hash correto no campo errado, caminho explícito inexistente e ID duplicado; ponteiro correto aceito. Nenhuma API chamada, nenhum fit, nenhum Windows executado. Não se atribui autoria independente do aluno ao notebook e texto revistos pelo professor. Próxima ação: aplicar a revisão e retornar log/conferencia.json; próxima competência prevista: registry/rollback. M06 em andamento; M07–M14 inalterados.

Versão 1.43, 05/10/2026 — E78 aceita execução HTTP e núcleo autoral; E79 fecha a verificação da correção nos anexos, com aplicação do aluno pendente. Painel, checkpoint, inventário, matriz e aprendizagem reconciliados. Sem novo percentual global ou promoção operacional.


### E80 — aceite do diagnóstico corrigido

Em 07/10/2026 o aluno enviou conferencia.json, decisao.md, diagnostico.csv, incidentes.csv e o log da execução no Windows. Run 1c51054df97b439fa22c7d2dcc9f6edd. Três hashes de saída conferem; as cinco fontes registradas correspondem aos anexos recebidos anteriormente; hash do código identifica a revisão entregue. Recálculo independente confirmou as 33 métricas/ações e os dez IDs. Invalid_payload conserva taxa e latências indefinidas; o parecer identifica as falhas como injetadas.

Aceite: aplicação da revisão encerrada. Autoria anterior reconhecida em E78; implementação e texto orientados não são convertidos em autoria independente. Não há nova tarefa sobre o parecer ou a mesma carga HTTP.

### E81 — registro de versões e rollback com recuperação observada

Entregues event_registry.py, registry_service.py, registry_exercise.py, inspecao_registry.py, test_event_registry.py, Aula_M06_Registro_Rollback.md e renewcast_m06_registry_20261007.zip. Registro local SQLite com cópias de modelo, manifesto, pedido e política; identificador imutável pelo contrato da aplicação, hashes, alias e histórico. Não é a implementação do MLflow Model Registry.

Dois artefatos existentes: h24_event_batch_v1, corte 31/07/2026 06 UTC, e h24_event_api_v1, corte 01/08/2026 05 UTC. Pedido comum é o exemplo do segundo artefato, compatível com ambos os cortes. Registro repetido é idempotente; tentativa de trocar bytes sob o mesmo identificador é recusada. Não há novo treino ou avaliação independente de desempenho.

Ativação e histórico são confirmados na mesma transação BEGIN IMMEDIATE. A geração esperada protege contra leitura antiga; a geração continua crescendo no rollback. API distingue estado desejado de versão carregada, recusa novas inferências quando desatualizada e exige reinício neste desenho. Saúde do processo e readiness são separados. A checagem é na entrada; chamadas já admitidas não são canceladas.

Fluxo verificado do professor: v1/g1 → v2/g2 → v1/g3. Treze tentativas HTTP: três sucessos iniciais, uma recusa 503 após trocar alias, três sucessos na v2, duas falhas 500 injetadas, uma recusa 503 após rollback e três sucessos restaurados. Cinco consultas GET de readiness separadas. As duas falhas entram como request_ids no motivo do rollback. Modelo e probabilidade da v1 reaparecem após reinício; artefatos de origem preservados. Na réplica: p(v1)=0,411681 e p(v2)=0,201792; valores não são metas de reprodução nem prova de superioridade.

Quatro verificações dirigidas passaram sem skip: falha na segunda escrita desfaz alias/histórico; operadores concorrentes não confirmam a mesma geração; adulteração de bytes bloqueia ativação; retorno ABA não torna um processo antigo pronto automaticamente. Fluxo completo executado com fit proibido. Python/Linux executado; Windows/PowerShell não executado pelo professor.

Autoria solicitada: SQL_AUTORAL no notebook de inspeção, com LAG por alias/geração, CTE de contagem e JOIN por activation_id. Sete colunas relacionam cadeia de transições, modelo e sucessos servidos; parecer curto cita uma resposta de recuperação e distingue incidente injetado de qualidade estatística. Notebook abre o SQLite em modo somente leitura e usa cópias em memória. Execução e autoria do aluno pendentes.

M06 segue em andamento; inventário técnico do P1 permanece 7/10 no escopo anterior, item 8 em curso. M07–M14 não mudam. Próxima competência após esta prática: empacotamento e reprodução em ambiente isolado, mantendo operação contínua e promoção operacional como entregas distintas.

Versão 1.44, 07/10/2026 — E80 encerra a inspeção corrigida; E81 entrega um bloco integrado de registro, transação, concorrência, serviço e auditoria SQL. Painel, checkpoint, matriz, estado do produto e aprendizagem atualizados, sem percentual global arbitrário.


### E82 — desbloqueio de ambiente e revisão da consulta de transições

09/10/2026. O aluno extraiu o pacote e executou registry_exercise no ambiente base. O interpretador C:\Users\marhl\Miniconda3\python.exe não encontrou renewable_forecast. As duas inspeções seguintes falharam antes da execução do SQL porque latest_run.json ainda não existia. Não há evidência de registro concluído ou de perda dos artefatos anteriores. O ponteiro é uma saída da execução concluída; não deve ser criado manualmente.

A consulta autoral usa LAG, CASE, JOIN, GROUP BY, ordenação e as sete colunas solicitadas. Reconhece-se a tentativa aplicada. Há quatro correções: requests contém uma linha por chamada e não a coluna calls do resumo; a geração inicial exige IS NULL; continuidade exige geração anterior + 1; a relação prescrita usa activation_id. As janelas ficam particionadas por alias. A contagem é agregada antes do JOIN, preservando uma linha por transição.

Verificação dirigida sobre a execução real da réplica 676b1a1a5391492cbc16304d4232c5cb, com entradas arquivadas somente para leitura: consulta recebida falha com no such column: r.calls; trocar apenas r.calls por 1 deixa chain_ok=[0,1,1]. Revisão completa devolve gerações [1,2,3], chain_ok=[1,1,1], successes_2xx=[3,3,3] e mesmo hash do modelo nas gerações 1 e 3. Alterar somente a cópia em memória para gerações [1,2,4] produz chain_ok=[1,1,0], mantendo a contagem por activation_id. Nenhum retreino, novo servidor ou execução Windows foi realizado nesta revisão.

Entregues inspecao_registry.py revisado e Revisao_M06_SQL_Registry.md, com preservação da consulta recebida, explicação, comando PowerShell que interrompe no primeiro erro e resultado esperado. O roteiro passa a registrar janelas SQL como tentativa recebida/em revisão, não como ausência de tentativa nem como domínio concluído. A consulta corrigida é orientada pelo professor. A aplicação e o parecer do aluno continuam pendentes. Não há novo exercício lateral; o objetivo segue encerrar a auditoria do registro/rollback.

Versão 1.45, 09/10/2026 — E82 registra causa primária, falhas em cascata, autoria recebida e verificação da revisão. Painel, checkpoint, matrizes e aprendizagem reconciliados; M06 em andamento, M07–M14 inalterados.


### E83 — reprodução do registro/rollback aceita; iniciador do ambiente

09/10/2026. O aluno ativou renewable-forecast e executou o fluxo. Treze anexos da execução 51cb4456d07d4f01b8b20f32e4ed1f78 foram recebidos. O log final da mensagem está truncado, mas os anexos permitem fechar a conferência. O ponteiro referencia o hash correto de verification.json. Os dez artefatos recebidos cobertos por output_sha256 coincidem com seus hashes, incluindo as cópias renomeadas pelo upload.

Recálculo independente: 13 POST, nove respostas 200, duas falhas 500 injetadas e duas recusas 503 esperadas; cinco GET de readiness. IDs entre cliente, servidor, respostas e probes reconciliados. Três transições v1/g1, v2/g2 e v1/g3. As duas falhas aparecem nas evidências do rollback. A tabela SQL recebida foi reconstruída em Python: 21 células coincidem, chain_ok=[1,1,1] e successes_2xx=[3,3,3].

Modelo restaurado: 8ecd88cd427ac822fe0e72f853680e3987764c2b30b646c5a2cab9d89b73a94a. p(v1) antes/depois = 0,2697810532292007. Ativação restaurada 734c3a91dc524c0392b61d5d3eb8e16b, diferente da inicial. Uma inferência de recuperação HTTP 200 tem request_id f07564a1c5df4ae3a4bed70b70bed884. O bloqueio E82 está resolvido.

Aceite: reprodução técnica do registro/rollback e saída SQL corrigida encerradas. Banco SQLite, modelos binários e código da inspeção executada não foram reenviados; seus bytes não foram auditados nesta conferência. Não foi recebido parecer_rollback.md; defesa independente segue pendente e não é substituída pelo texto do professor. A saída correta não é convertida em autoria independente.

A pedido do aluno, entregue Abrir_Renewcast.cmd para salvar na Área de Trabalho. Abre PowerShell na pasta do projeto, inicializa Conda nessa sessão, ativa renewable-forecast e confere Python/importação. Não modifica perfis nem política de execução, não treina e não repete o registro. Arquivo ASCII/CRLF e comandos revisados pela documentação oficial; Windows/PowerShell não executado pelo professor. Manual e aceite em Aceite_M06_Registry_20261009.md; evidência estruturada em aceite_E83.json.

Próxima unidade prática prevista: empacotamento/reprodução isolada do serviço. Operação contínua, Registry MLflow, Docker/CI e distribuição continuam pendentes. M06 em andamento; M07–M14 inalterados. Inventário P1 continua 7/10, item 8 em curso; nenhum percentual global atribuído.

Versão 1.46, 09/10/2026 — E83 aceita os anexos do aluno e encerra o bloqueio de ambiente; painel, checkpoint, matrizes e aprendizagem reconciliados.


### E84 — empacotamento e reprodução isolada: nova unidade entregue

**09/10/2026.** O aluno cobrou avanço prático, aula, autoria, análise e coerência do indicador de progresso. Esta unidade avança do registro/rollback aceito em E83 para distribuição do serviço, sem repetir seus testes ou treinar modelos. O inventário técnico continua 7/10 no escopo experimental; a entrega de material pelo professor não eleva esse número nem conclui um marco de formação.

**Artefatos:** renewcast_m06_empacotamento_20261009.zip, scripts/empacotar_servico.py, scripts/reproduzir_servico.py, scripts/run_m06_empacotamento.ps1, docs/Aula_M06_Empacotamento.md e docs/Verificacao_E84_Professor.json. Os caminhos usam dist/event_service para distribuições, venvs/m06_package para ambientes e reports/packaging/CJU_BA5EIGT/h24_event_v1 para recibos. Não são introduzidos caminhos alternativos de experimento.

**Ferramentas e competência:** construir wheel com pyproject.toml/setuptools; percorrer Requires-Dist; capturar versões de inferência e hashes dos wheels; instalar por --no-index/--require-hashes; executar Python isolado e verificar a origem do módulo; comparar referência e resposta HTTP sem retrain. Separar as identidades do modelo, da política, do código e do ambiente. A aula explica limites de plataforma, do venv e da prova de compatibilidade.

**Verificação do professor:** execução em Linux/Python 3.12.14 com a réplica já existente. Capturadas 24 dependências mais o pacote do serviço. Modelo da réplica com hash bfb7c6315caeb2d56485411e06c4d90a8cfe32c7273868966297cee131fb0a8f. A referência 0,20179188830321645 foi reproduzida em HTTP 200, com diferença zero; requisição incompleta recebeu 422. Uma cópia adulterada do pedido foi recusada pela integridade antes da instalação. Os dados da réplica não são apresentados como execução ou resultado do modelo Windows do aluno.

**Demanda do aluno:** executar no Windows; transportar o release para uma pasta independente e recriar o ambiente; escrever notebooks/orcamento_distribuicao.py usando biblioteca padrão, total em MiB, participação de todos os wheels e top 5; salvar CSV na pasta da reprodução; defender em parecer a removibilidade de dependências, a compatibilidade de Python e os limites da aprovação. Fixação lexical liga wheel, dependência transitiva, lock, wheelhouse, isolamento e reprodutibilidade a arquivos reais e explicação de memória.

**Critério de conclusão:** recibo de reprodução e ambiente, evidência do destino independente, código autoral, CSV e parecer coerente. Estado atual: material entregue e verificado pelo professor; execução Windows e aprendizagem do aluno ainda não avaliadas. A sequência técnica prevista é Docker/CI reaproveitando esta distribuição; executável Windows e promoção operacional permanecem entregas distintas.

Versão 1.47, 09/10/2026 — unidade ativa, checkpoint, matriz de ferramentas e evidência E84 atualizados; os 14 marcos e os dez itens técnicos mantêm seus denominadores.


### E85 — reprodução Windows e orçamento aceitos; parecer em revisão localizada

**13/10/2026.** Recebidos nove anexos, código de notebooks/orcamento_distribuicao.py e saída da execução. Run 20261010T231840Z_388ee417; release 20261010T231817Z_2aeba29a. Conferidos hash do recibo pelo ponteiro e cinco hashes dos arquivos de saída. Instalação --no-index/--require-hashes, pip check, isolamento e importação da API pelo novo site-packages registrados. Modelo 7ab0a5cbc45a47df62b3ce44166f090b0ab686481aa37872d25e7c6353a1e17d e política preservados; p=0,20465385372296466, diferença zero e HTTP 200/422. Aceite limitado à evidência recebida; binários Windows não reexecutados pelo professor.

**Autoria aceita:** biblioteca padrão, soma, percentuais, ordenação e CSV completo. Recalculados 26 wheels, 72.018.219 bytes, 68,6819257736206 MiB; top5 96,2424660904%; SciPy e NumPy concentram 68,3523%; os outros 21 wheels somam 2,5807 MiB. O código do serviço representa 0,014% do volume. Não há indicação de que diminuir seu wheel seja uma otimização relevante sem problema de tamanho medido.

**Revisões necessárias:** o código presume sucesso quando falta verification.json, atribui diferença zero e troca hash do modelo pelo hash de release; dois ponteiros latest podem apontar para experimentos diferentes. Nesta execução eles coincidem e o recibo existe, portanto o resultado aceito não veio do fallback. O parecer generaliza incorretamente incompatibilidade de qualquer wheel compilado diante de qualquer mudança de Python; devem ser considerados tags, ABI, Requires-Python e a validação do modelo persistido. NumPy é um dos dois maiores e deve ser explicado explicitamente. Transporte a pasta independente não foi evidenciado.

Entregue auditar_distribuicao.py como referência de verificação que interrompe em evidência ausente e extrai METADATA real, preservando parecer/código originais. A revisão do aluno é localizada; não exige repetir cálculo já aceito. Evidência estruturada: Aceite_E85_Evidencias.json.

### E86 — Docker e CI: material executável preparado, execução pendente

**13/10/2026.** Pacote renewcast_m06_docker_20261013.zip e Aula_M06_Docker_CI.md entregues. Preservam as versões científicas, modelo/política e pedido de referência; obtêm binários Linux, criam lock com hashes Linux e verificam inferência pelo ID da imagem. O Dockerfile usa estágios, usuário numérico sem privilégios e bind local no host. O controlador fixa a imagem base por digest, guarda logs e só cria recibo aprovado depois de conferir versões, identidade e HTTP 200/422. Não treina, publica ou promove o modelo.

**Verificado pelo professor:** auditoria da réplica, leitura de dependências dos wheels, preparação do contexto, recálculo de lock Linux com arquivos existentes; ausência de recibo e mistura de ponteiros recusadas; comparador recusa mudança de modelo/probabilidade e NaN. **Não executado aqui:** Docker indisponível, portanto pull da imagem solicitada, build, rede do contêiner e compatibilidade das versões Windows no Linux permanecem pendentes. PowerShell e CI remoto também não executados. O workflow é um exemplo desativado em ci_examples, com requisito de contexto revisado presente no checkout.

**Aprendizagem:** distinguir pacote, ambiente, ABI, contexto de build, imagem, contêiner, tag e digest; sustentar migração com controle de variáveis e critérios de falha; diferenciar recibo de compatibilidade, desempenho estatístico e aprovação operacional. Autoria: parecer_container.md comparando identidades, versões, locks, previsão e tamanho da imagem, com decisão fundamentada. O complemento curricular de 12/10 permanece preservado para as unidades posteriores.

Versão 1.48, 13/10/2026 — estados de execução Windows atualizados, orçamento reconhecido, revisões do parecer delimitadas e próxima unidade concreta registrada. Inventário P1 permanece 7/10, item 8 em andamento; nenhum percentual global de domínio foi criado.


### E87 — migração Windows/Linux executada e conferida

**13/10/2026.** Recebidos nove anexos e conclusão autoral. Run 20261013T185650Z_ffc01dd8, release 20261010T231817Z_2aeba29a, contexto 20261010T231817Z_2aeba29a_01430e3a. Hash do recibo corresponde ao ponteiro; sete hashes de saídas correspondem aos anexos. Controlador executado corresponde ao entregue em E86. Ambiente Linux/amd64, Python 3.12.13 e 26 versões iguais ao Windows; lock Linux coincide com as versões instaladas. Logs registram wheels manylinux, instalação com hashes e pip check sem dependências quebradas.

Imagem sha256:ec1b7b36cf72f6a7610389c6c27cc7b4a1500a0d03d669d9472317f2e45f8c52, tamanho Docker 228.996.849bytes/218,3884MiB. Modelo 7ab0a5cbc45a47df62b3ce44166f090b0ab686481aa37872d25e7c6353a1e17d e política 309906646dabc7a998a05071982b56dfad1fda140b45383e7b5e3b02d41decb7 preservados. Resposta inteira coincide com Windows: p=0,20465385372296466,diferença 0,alarme false. HTTP 200 válido e 422 por lag_1h ausente. Usuário 10001:10001, raiz de leitura e publicação localhost constam dos arquivos.

**Aceite:** compatibilidade neste pedido e nesses ambientes. Sem reexecução Docker pelo professor, imagem/binário anexado, cobertura de qualquer entrada/plataforma, carga, CI remoto ou promoção operacional. A interpretação distingue corretamente artefato e wheel nativo, mas garantir a mesma matemática em qualquer plataforma extrapola a evidência. Versões e bytes preservados não dispensam comparar identidade, contrato, probabilidades e decisões. Correção registrada sem repetir a execução aceita. Evidência: Aceite_E87_Container.json.

### E88 — concorrência: experimento, aula e autoria entregues

**13/10/2026.** Entregues renewcast_m06_concorrencia_20261013.zip, scripts/medir_concorrencia.py, notebooks/analise_concorrencia.py, Aula_M06_Concorrencia.md e Verificacao_E88_Professor.json. Reutiliza imagem aprovada sem build/download/fit; limite 2 CPU-equivalentes/1 GiB, porta local aleatória, encerramento do próprio contêiner. Carga fechada:1/4/8 clientes,três rodadas em ordem rotacionada,120 tentativas/fase,1080 medidas e 8 aquecimentos separados. Registra duração, status/transporte e correção da resposta inteira. Falha de transporte impede seguir para outra fase com trabalho de estado desconhecido.

**Prova do professor:** cliente HTTP real na réplica nativa HGB,216 respostas corretas nas nove fases, fit proibido. Réplica com modelo bfb7c6315caeb2d56485411e06c4d90a8cfe32c7273868966297cee131fb0a8f e p=0,20179188830321645; não são resultados do aluno. Servidor sintético identificado testa concorrência real do cliente e discriminação de 200 incorreto/422/500. Nove P95 recalculados independentemente com NumPy; fonte misturada recusada. Docker/PowerShell da nova unidade não executados pelo professor.

**Autoria:** implementar escolher_concorrencia no notebook. Elegível se nenhuma das três rodadas falhar e todos os P95 corretos<=250ms; escolher menor concorrência cuja mediana de vazão útil alcance 95% da melhor elegível. Sem candidato: None fundamentado. Limites didáticos definidos antes dos resultados; escolha não configura cota de admissão. Parecer até 25 linhas liga fila/vazão/latência e distingue async, threads científicas e processos. Fonte da API é extraída da imagem; bloqueio síncrono é hipótese de mecanismo, não diagnóstico de CPU saturada sem medição.

**Estado:** E87 encerra execução Docker de compatibilidade. E88 é material entregue e parcialmente verificado; execução do aluno e autoria pendentes. CI remoto continua separado e não executado; shadow ao vivo e utilitário Windows pendentes. M00+M01–M14 e dez itensP1 mantidos; sem percentual global de formação. Complemento curricular de 12/10 preservado.

Versão 1.49, 13/10/2026 — painel, checkpoint, matriz, aprendizagem e evidências reconciliados com o aceite Docker e a unidade de concorrência.


### E89 — escolha autoral de concorrência aceita e limites do parecer

**14/10/2026.** Recebidos console do run 20261014T000751Z_15fe13d2, implementação de escolher_concorrencia e parecer. O console informa 1080/1080 respostas corretas. Medianas úteis por nível: 1→20,49, 4→33,45 e 8→30,46 req/s; piores P95:80,30/219,64/392,36ms. Os níveis1/4 são elegíveis; alvo0,95×33,45=31,7775req/s; escolha4. A função cumpre a regra sob o carregador que já valida as nove fases. Aceite de autoria registrado em Revisao_E89_Concorrencia.md/json; cópia normalizada do código mantém a lógica do aluno.

**Prova e escopo:** execução da função com os valores arredondados do console e quatro casos sintéticos: menor concorrência retendo95%, nenhum elegível, P95 ausente e fronteira250ms. Todos com saída esperada. Não recebidos nesta mensagem CSVs/recibo/decisao.json do run; não há nova conferência de hashes ou recálculo dos P95 por tentativa. Salvar --autoria é registro local, não pedido para repetir benchmark.

**Revisão do parecer:** +63,25% é razão entre medianas; por rodada, diferenças4vs1 são+74,86%,+35,77%,−1,79%. PioresP95 aumentam2,735vezes, não exatamente3. Chamada síncrona dentro de async é consistente com o código, mas não comprova saturação de CPU; um processo pode usar threads nativas. Latência cliente não isola fila. A decisão é experimental e não configura cota de admissão, workers ou política operacional. Não há motivo demonstrado para alterar o servidor nesta etapa.

### E90 — cliente Windows e lançador de uso: M06.5 iniciada

**14/10/2026.** Pacote renewcast_m06_cliente_windows_20261014.zip, tools/renewcast_client.py, scripts/criar_cliente_windows.py, scripts/verificar_cliente_windows.py e Aula_M06_Cliente_Windows.md. Cliente de biblioteca padrão; API/modelo externos. PyInstaller em venv de build exclusivo, onedir, versões/wheels/hashes registrados. Verificador copia a pasta completa para TEMP externo, remove Conda/PYTHONPATH do filho e limita PATH às pastas Windows; consulta imagem Docker aprovada pelo ID, sem novo treino/build da imagem. Recibos distinguem200 válido,422,200 com identidade divergente e API encerrada. Falha não produz decisão e não sobrescreve sucesso antigo.

**Professor:** cliente Python em processos separados executado contra réplica HGB nativa, modelo bfb7c6315caeb2d56485411e06c4d90a8cfe32c7273868966297cee131fb0a8f, p0,20179188830321645, fit proibido. Conferidos preservação da resposta,422,identidade divergente,alarme inconsistente,indisponibilidade e preservação de saída existente. Não executados build PyInstaller Windows, Docker nem PowerShell; esses resultados dependem da reprodução do aluno. Não se atribuem ao aluno números da réplica.

**Autoria e saída:** implementar tools/Consultar_Renewcast.ps1, receber pedido/URL, resolver recursos por PSScriptRoot, gerar recibo exclusivo, capturar LASTEXITCODE e apresentar previsão só com código0. Copiar ao lado do .exe e chamar de outra pasta, com API ativa e depois encerrada. Demonstrar independência de Conda no cliente e distinguir dependência de serviço de dependência de ambiente. Não se conclui implantação cloud, CI remoto, shadow ou M06 integralmente. Item9 do P1 passa a em andamento; itens8/9 ainda abertos; sete entregas técnicas demonstradas no escopo anterior, sem percentual global de formação.

Versão 1.50, 14/10/2026 — autoria de concorrência reconhecida; painel, checkpoint, matriz e registro atualizados; M06.5 recebe uma entrega executável e demanda definida, com limites de verificação explicitados.

### E91 — cliente Windows e lançador 1.0 aceitos

**14/10/2026.** O anexo Texto colado(8).txt informa a construção 20261014T182138Z_d3f59ba1 e duas verificações externas (20261014T182236Z_99227dfc e 20261014T193054Z_58a9fdc4), com 200/exit0, 422/exit2, identidade divergente/exit4 e API encerrada/exit3. Depois da correção dos argumentos PowerShell, os recibos colados às21:38:31Z e21:38:57Z registram no_alarm/0/p0,20465385372296466 e unavailable/3/response=null. Diretório externo e nomes UUID distintos. O Conda ativo no ensaio manual não deve ser confundido com a prova anterior de ambiente filho limpo.

**Aceite:** item9/P1, cliente1.0 no mesmo Windows e protocolo de desenvolvimento. Evidência recebida como logs/texto; não se afirma auditoria de todos os arquivos de release do aluno nem funcionamento em outro PC. Inventário passa a8/10, sem percentual de formação. Modelo e política preservados conforme identidade informada. O executável não gera dados atuais nem opera sem API.

### E92 — autoria da política de atualidade aceita

**14/10/2026.** Código de avaliar_atualidade e cinco saídas recebidos. Valida fuso/modo/duração/relação origem-alvo; prioriza histórico, origem futura, alvo vencido e idade excedida; retorno exato de quatro campos. Reconhecida autoria no contrato UTC tipado. Duas horas são o limite hipotético de apresentação, distinto do atraso de disponibilidade da geração. Aceite não promove o modelo para produção.

### E93 — regra integrada ao cliente 1.1

**14/10/2026.** Pacote renewcast_m06_atualidade_20261014.zip. Módulo tools/politica_atualidade.py preserva as decisões do aluno e normaliza UTC antes da comparação, com tipos explícitos. Cliente exige presentation-mode, lê relógio real após o HTTP e não permite override de now na CLI. Recibo v2 registra a regra; HTTP200 antigo pode resultar em presentation_blocked/exit7/response=null, com audit_response para conferência. Falhas HTTP/contrato continuam prioritárias. Lançador com BOM, modo explícito e código6 para falha própria; build inclui regra e lançador. Notebook original e releases anteriores preservados.

**Verificação do professor:** cinco cenários HTTP com réplica HGB nativa existente, modelo bfb7c6315caeb2d56485411e06c4d90a8cfe32c7273868966297cee131fb0a8f e p0,20179188830321645. Fit proibido. Verificados replay, bloqueio temporal,422,identidade divergente,indisponibilidade,modo obrigatório e preservação de saída. Dezessete verificações do domínio/fronteiras/precedência. Windows/PyInstaller/PowerShell/Docker não executados pelo professor nesta evolução. Números da réplica não são os do aluno.

**Próxima ação e fim da unidade:** construir cliente1.1 e executar controlador em Windows. Enviar saída e verification.json; aceite por evidência. Em seguida M07.1: transformação do Renewcast com PySpark e Spark SQL, equivalência com DuckDB, plano de execução e shuffle. Não acrescentar novas condições de operação ao vivo/CI para prolongar esta unidade; pendências permanecem registradas.

Versão1.51, 14/10/2026 — aceites E91/E92 e integração E93; painel, inventário, checkpoint, matriz e registro reconciliados. Oito entregas técnicas do produto aceitas no escopo; nenhum percentual global de formação declarado.


### 17/10/2026 UTC — E94 aceita cliente1.1; E95 inicia M07.1

- E94: anexos verification(6).json, valid.json, blocked.json, rejected.json, wrong_identity.json, unavailable.json, pipeline(2).log e server(2).log auditados. Sete hashes de saída coincidem; 32 conferências aprovadas. O código do controlador corresponde ao entregue emE93.
- Reprodução histórica HTTP200/exit0; mesmo pedido operacional HTTP200/exit7 com target_elapsed e resposta somente em audit_response; regressões422/2, identidade divergente200/4 e indisponibilidade/3. Probabilidade0,20465385372296466, diferença0. Processo frozen fora do projeto, Conda/PYTHONPATH ausentes nos recibos. Escopo: mesmoPC, API Docker; não aprovação operacional.
- Aceite M06.5 encerrado; não solicitar reconstrução do cliente/modelo nem repetir benchmark para avançar. Item9 segue concluído, agora na versão1.1. InventárioP1 permanece8/10; não há percentual global da formação validado.
- E95 entrega M07.1: tabela diária de qualidade da série ONS existente. Contagens preservam zero real, nulo e ausência; calendário inclui dias vazios. TimestampNTZ conserva os rótulos existentes, sem confirmar fuso/semântica do intervalo. Média parcial não vira energia diária.
- Professor implementa infraestrutura, DuckDB e DataFrame; aluno implementa SQL_AUTORAL e classificar_cobertura em notebooks/transformacao_spark.py, executa --autoria com2/4partições e redige reports/scale_comparison.md. Contratos, tarefas e comandos estão em Aula_M07_1_Spark_DuckDB.md.
- Verificação efetiva do professor: PySpark4.0.1/DuckDB1.4.1/Java17 em Linux nativo, 8.760linhas sintéticas/365dias, caso manual de4datas e5recusas de entradas inválidas. SQL de referência e DataFrame equivalentes; classificação conferida. Docker/Windows/Parquet real do aluno não executados pelo professor. Não atribuir a demonstração à autoria do aluno.
- Próxima ação: python scripts/executar_m07_spark.py. Conclusão de M07.1 depende da execução real e da autoria/explicação recebidas; M07.2Delta e M07.3Databricks continuam na sequência original.


### 19/10/2026 UTC — E96 tentativa Spark recebida; E97 correção localizada

- E96: log anexado mostra build Docker concluído e preflight da entrada com 8.760 linhas, 365 datas e zero valores nulos. Run falho: 20261019T163754Z_f578df8e. O erro fatal foi `basedir must be absolute: ?/.ivy2.5.2/local`, antes de executar a SQL; também houve UnknownHostException. O Dockerfile entregue pelo professor usava UID numérico sem cadastro. A tentativa não deve ser atribuída a erro de instalação Conda do aluno.
- A autoria recebida agora contém SQL preenchida; o log de comandos anteriores --autoria registra leitura de arquivo vazio/ausente. Não há evidência suficiente para determinar se era outra versão salva ou uma execução anterior. O runner passa a mostrar o caminho exato.
- Revisão da autoria: preservar o LEFT JOIN antes do GROUP BY é válido. COUNT(din_instante) conta linhas reais, inclusive geração nula; a diferença COUNT(din_instante)-COUNT(val_geracao) conta valores nulos sem contar a linha artificial de um dia ausente. A classificação PySpark nativa está correta no contrato; removido apenas raise após return.
- E97 entrega correção de usuário/grupo Docker e cache Ivy absoluto em /tmp, hostname local e driver em loopback. Camada nova após as dependências permite reaproveitar o cache. Não exige reinstalar Conda ou alterar dados reais. A tentativa do aluno deve ser copiada antes de extrair o ZIP.
- Verificação executada pelo professor: Linux nativo, Spark4.0.1/DuckDB1.4.1/Java17; Java user.home=? deliberado. Inicialização passou; DataFrame, SQL revisada e DuckDB coincidiram no exemplo manual de quatro dias; classificação passou. A SQL original apresentou cinco células divergentes. Docker e execução com UID10001 não disponíveis aqui; Parquet real do aluno não recebido nesta revisão. Esses limites impedem declarar o contêiner já corrigido por prova de execução no destino.
- Próxima ação: --autoria com o pacote corrigido, depois --shuffle-partitions 4 se passar. Concluir a explicação em reports/scale_comparison.md usando os planos exportados. Sem novas rodadas opcionais de instalação/treino. M07.2 Delta segue depois do fechamento dessa entrega.
- Roteiro1.53: painel, checkpoint, matriz e aprendizagem reconciliados. M07.1 em andamento; E94/M06.5 preservado. P1 continua8/10 itens técnicos, sem percentual global de formação. A revisão SQL orientada não é creditada como solução independente do aluno.


### 19/10/2026 — E98 falha Zstd e relato de incompreensão; E99 retomada de base

- E98: anexo Texto colado(10).txt, runs 20261019T172422Z_877bd8f9 e 20261019T174519Z_9fe0bb39. Ambos reutilizam o build, leem inicialmente 8.760 linhas/365 datas/zero nulos e iniciam Spark4.0.1. A primeira coleta DataFrame falha ao carregar libzstd-jni em /tmp com failed to map segment from shared object. O erro Ivy/usuário anterior não se repete.
- As chamadas não chegam à SQL autoral, cuja explicação é gerada depois da comparação DataFrame/DuckDB. Portanto, não há plano SQL autoral nem resultados finais dessas tentativas para o aluno analisar. Os arquivos de plano DataFrame/DuckDB podem ser parciais. reports/scale_comparison.md sempre seria escrito pelo aluno, não gerado pelo pipeline; isso foi esclarecido.
- O diagnóstico mais provável é a restrição de execução na montagem temporária, compatível com o erro e a configuração entregue. O anexo não contém inspeção das flags efetivas. E99 explicita exec,nosuid,nodev no /tmp e acrescenta leitura/recusa de noexec antes de Spark. A autoria e os dados não são substituídos; imagem/dependências permanecem as mesmas. Nenhuma promessa de execução Windows concluída.
- Aluno: “não to entendendo nada, uma linha sequer de pyspark”. A resposta pedagógica é retomar as operações de dados, explicando cada expressão com SQL e um exemplo 0/NULL/12; suspender agora a exigência de analisar Exchange e repetir partições. A classificação sintaticamente correta de E96 permanece reconhecida, mas não certifica domínio.
- Professor: leitura real do codec Zstd e exemplo de DataFrame, agregação, calendário, cobertura e when executados em Linux nativo; resultado3/2/6 para o primeiro dia e 0/0/NULL no dia vazio. Docker e falha noexec não reproduzidos neste ambiente; registro em Verificacao_E99_Professor.json.
- Próxima ação limitada: aplicar E99, executar --autoria uma vez, explicar a mudança no exemplo se NULL virar6. Não repetir --shuffle-partitions4 até a leitura básica estar entendida. A unidade conserva o objetivo; Delta continua posterior, sem avançar o marco por mais um pacote criado.
- Roteiro1.54: painel, checkpoint, matrizes e aprendizagem atualizados. Corrigida também uma instrução antiga de M06 indevidamente inserida no modelo genérico de registro de tentativa. Aceites anteriores preservados; sem percentual global.


### 19/10/2026 — E100 reprodução Spark aceita e primeira interpretação conceitual correta

- Execução recebida: 20261019T230058Z_cf2fe669, modo autoria. Imagem sha256:4493611d28044f61634426ee70efb3a410b649510261ae10ebd1a839a4e0e0d9. Host, log e recibo interno confirmam conclusão; /tmp sem noexec. Encerrado o bloqueio anterior para esta execução. Não solicitar nova instalação ou build para responder à próxima prática.
- Auditoria em Verificacao_E100_Spark.json: 30 verificações estruturais/de integridade e três comparações numéricas de CSV. Quinze hashes de anexos conferidos, sendo três encadeados pelo recibo do host e doze saídas do manifesto; mais três hashes de código compatíveis com controlador, núcleo e autoria corrigida entregues. Dos 21 outputs declarados, 12 foram recebidos; os nove resultados do caso didático não foram anexados. O sucesso do caso didático vem do recibo conferido, não de recálculo dos seus CSVs nesta revisão.
- CSVs reais: 365 datas de 2025-09-01 a 2026-08-31; todas com 24 horas presentes/válidas, zero nulas/ausentes e classificação completo; soma 8.760. Diferença DataFrame/DuckDB zero; SQL/DuckDB máxima 4,263256414560601e-14, dentro das tolerâncias do protocolo. Comparações diretas de 3.285 células numéricas em cada par. Não se declara ausência de diferenças de bytes entre todas as implementações.
- Limites: Parquets anexados conferidos por hash, sem decodificação/reagregação nesta auditoria; original completo não anexado, preservação informada pelo controlador. Identidade do conjunto declarada sem checagem em coluna pelo pipeline; timestamps mantêm rótulos sem fuso. Hashes demonstram consistência com manifestos, não atestação externa assinada. Sem rodada com quatro partições ou prova de cluster.
- Aprendizagem: aluno explica corretamente a troca de NULL por 6: presentes 3, válidas 3, nulas 0, ausentes 21, cobertura 0,125 e parcial. Média permanece 6; reconhecida distinção entre zero, nulo e ausência, sem inferir domínio integral de PySpark a partir dessa resposta.
- Próxima prática restrita e concreta: completar_calendario(dias,resumo) com LEFT JOIN e fillna apenas nas contagens. Explicar a diferença entre dia sem registros e dia com 24 registros nulos e o efeito do INNER JOIN. Material Revisao_E100_Spark.md. Código pode ser enviado no chat; não requer alterar a autoria já validada nem reexecutar Docker. Planos/partições depois da base; M07.2 Delta continua na sequência.
- Roteiro 1.55: painel, checkpoint, matriz, aprendizagem e evidência atualizados. M07.1 em andamento com reprodução técnica aceita. P1 permanece 8/10 entregas técnicas; sem percentual global de formação.

### 25/10/2026 — E101: crítica à fragmentação, revisão dos anexos e laboratório temporal

- O aluno relata tarefas simples, repetitivas e desconectadas do objetivo profissional. A crítica procede quanto à condução: executar infraestrutura e adicionar uma expressão isolada não constituem progressão suficiente. A sequência passa a unidades completas, com aula, problema aplicado, autoria e fechamento previamente definidos.
- Os quatro casos de calendário/classificação estão corretos no CSV recebido. O plano mostra partial_count/partial_avg, Exchange por dia em duas partições e agregação final; é um plano inicial, isFinalPlan=false. Isso não permite afirmar medição de escala, paralelismo efetivo ou domínio independente da ferramenta.
- O código anexado cria geracao_observada_mwh como expressão Python, não a inclui em agg e depois tenta selecioná-la. O CSV não contém essa coluna; o plano não contém partial_sum. Código e resultados representam versões diferentes. Corrigida a inclusão da expressão em agg; a definição da variável por si só não altera o DataFrame.
- Material entregue: renewcast_m07_laboratorio_temporal.zip, com correção do calendário, laboratorio_temporal_spark.py, Aula_M07_Laboratorio_Temporal.md e verificação do professor. O laboratório usa a série real já existente no computador do aluno, a imagem Spark já registrada e saídas próprias em reports/scale/CJU_BA5EIGT/laboratorio_temporal.
- Teoria aplicada: grade completa para que lag/lead representem horas; janelas inclusivas -7/-2 para atraso2/janela6; completude do histórico; features separadas de alvo; rótulos disponíveis estritamente antes do corte de treino. Contraprovas sintéticas identificadas: lacuna que desloca lag e alteração de futuro que preserva features.
- Autoria: selecionar_treino(tabela,corte), seguida de parecer técnico de uma página. A entrega inteira é especificada no material, sem nova lista indefinida de exercícios de contagem. A seleção será conferida pelo conjunto de linhas, incluindo a igualdade ao corte.
- Restrições preservadas: atraso assumido; eixo de timestamps original sem validar fuso/intervalo físico; nenhuma declaração de novo teste reservado, desempenho de modelo ou adequação operacional. M07.2 Delta e M07.3 Databricks continuam posteriores; M08–M14 não são marcados como iniciados por este pacote.
- Roteiro1.56: painel, checkpoint, matriz, registro didático e ritmo atualizados. O diário anterior permanece histórico. Sem novo percentual global.


### 27/10/2026 — E102: autoria recebida, falha de integração e correção do laboratório

- Evidência do aluno: duas execuções sem corte mostram 8.760 horas na grade/presentes, 8.753 origens com features, 8.729 com features e alvo e 24 alvos sem valor. Ambas executam as contraprovas de lacuna e futuro. Os Parquets reais não foram anexados; os números são reconhecidos como logs recebidos.
- A função selecionar_treino enviada combina features_validas, alvo preenchido e disponibilidade estritamente anterior ao corte. Está correta; não solicitar sua reimplementação nem tratar essa falha como desconhecimento de PySpark.
- A tentativa com --corte-treino chega à linha 73 do arquivo montado e executa NotImplementedError. O caminho de montagem no comando aponta para notebooks/laboratorio_temporal_spark.py do projeto. Portanto, a cópia em execução ainda é o esqueleto inicial. Os registros não permitem afirmar se a alteração não foi salva ou se uma nova extração a substituiu. CalledProcessError é a propagação do mesmo erro ao processo Windows.
- Correção entregue: arquivo completo com a implementação recebida e banner 20261027-selecao-incorporada. Validação do corte ocorre antes do Spark; conferência da seleção ocorre antes da substituição de resultados. Resumo registra primeira/última origem e última disponibilidade de alvo. A gravação dos vários arquivos não foi transformada em transação atômica; Delta continua tópico posterior.
- Retomada exata: substituir somente o script do laboratório; não reextrair o pacote inicial, não criar novas cópias em notebooks, não reinstalar dependências. Executar o comando com corte 2026-07-11 06:00:00. Para série completa com início 2025-09-01 00:00, a expectativa é 7.485 linhas, primeira origem 2025-09-01 07:00 e última 2026-07-10 03:00; disponibilidade máxima 2026-07-11 05:00. A igualdade ao corte é excluída.
- Material anterior preservado; pacote e aula atualizados para não redistribuir a função vazia. A evidência de aprendizagem inclui a autoria efetivamente enviada. Corrigir um arquivo entregue não aumenta o progresso do currículo. M07.2 permanece como próxima unidade após o fechamento delimitado do laboratório, sem inserir novas microtarefas.
- Verificação desta correção pelo professor: execução integral da CLI com corte em Linux/PySpark4.0.1/Java17, série sintética explícita de8.760 horas; 7.485 linhas gravadas em Parquet, limites de origem/disponibilidade e demais contagens conferidos. Contraprovas passaram no mesmo fluxo. Corte com fuso foi recusado antes de iniciar Docker/Spark. A execução Windows com os dados reais continua pendente.


### 27/10/2026 — E103: laboratório temporal e arquivos reais aceitos

- Log Windows com banner 20261027-selecao-incorporada e corte 2026-07-11 06:00:00. 8.760 horas, 8.753 origens com features, 8.729 com features/alvo, 24 alvos ausentes e 7.485 linhas de treino. A falha NotImplementedError está encerrada.
- Dois Parquets, resumo, amostra, duas contraprovas e plano efetivamente abertos; originais preservados. EXCEPT ALL nos dois sentidos mostra igualdade integral entre treino e filtro correto. Schemas, origens consecutivas e relações temporais conferidos em todas as linhas; amostra de36 linhas coincide.
- Primeira origem2025-09-01 07h, última2026-07-10 03h, maior disponibilidade2026-07-11 05h. A origem10/07 04h é excluída pela igualdade ao corte. Filtrar apenas origem anterior admitiria7.511 linhas,26 indevidas.
- Contraprovas recebidas:129 versusNULL; features130/127,5 invariantes e alvo156→1.156. Valores do histórico/alvo alinhados permitiram recálculo interno das janelas, diferença máxima5,684341886080802e-14. O bruto ONS não foi recebido; não se apresenta essa consistência interna como auditoria da fonte.
- Plano contém Generate, LEFT broadcast join, Sort, Window e cache; frames -2/-2,-7/-2,+24/+24. isFinalPlan=false não mede desempenho. Evidências/hashes em docs/Auditoria_M07_1_E103.json e parecer técnico no mesmo pacote.
- Decisão: aceite técnico M07.1 e autoria da seleção reconhecida. Não repetir laboratório/instalação. Defesa conceitual consolidável na nova atividade, sem bloquear a próxima aula.

### 27/10/2026 — E104: Delta e reprodução após correção simulada

- Aula completa e script de referência integralmente implementado. Pacote renewcast_m07_delta_reproducao.zip acrescenta arquivos; não substitui a autoria anterior nem contém função vazia no fluxo executado.
- Spark4.0.1 existente mais dois JARs oficiais Delta4.0.1, hashes fixados; download7.809.994 bytes. Sem build novo ou PySpark no Conda Windows. Contêiner sem rede. Saída reports/scale/CJU_BA5EIGT/m07_2_delta; execução concluída e íntegra pode ser reutilizada.
- Experimento: Delta0 igual ao Parquet; treino reproduzido e snapshot fixado; rejeição de lote duplicado/schema extra; MERGE simulado +12 em10/07/2026 01h; Delta1; análise do impacto; reabertura de0; reenvio sem alterar dados.
- Professor executou núcleo em Linux/Spark4.0.1/Delta4.0.1/Java17 usando geração reconstruída dos anexos e comparando ao treino real enviado. Valor165,522→177,522; sete origens afetadas; duas linhas de treino alteradas; snapshot0 reproduz7.485 linhas. Rejeições e idempotência conferidas. Leitura independente do log Delta e Parquet confirma exatamente uma medição alterada. Docker Windows ainda não foi executado aqui.
- Distinções: instante medido, disponibilidade original, disponibilidade de revisão e commit são relógios diferentes. Snapshot criado hoje não prova histórico ONS de julho. Time travel depende de retenção de log/dados; VACUUM não é limpeza genérica. Idempotência dos dados não exige em todo motor ausência de novo commit.
- Autoria: notebooks/planejar_recalculo_temporal.py, função planejar_recalculo(instantes, horizonte, atraso, janela), conjuntos de origens afetadas por histórico/média/alvo e união. Uma correção:h24/d2/w6 gera1/6/1/7; duas horas adjacentes geram2/7/2/9. Comparar caso simples ao CSV e explicar escolha de snapshot. Não reexecutar treino nem criar novas microtarefas de contagem.
- Próxima unidade segue M07.3 Databricks. M08–M14 e limitações operacionais preservados. Não houve treino de modelo nem novo percentual de conclusão.


### 29/10/2026 — E105: Delta executado no Windows e planejador autoral revisado

- Log recebido: Spark4.0.1/Delta4.0.1, completed=true, 8.760 horas,7.485 linhas de treino, versões original0/corrigida1/após reenvio1. Medição simulada em10/07/2026 01h:165,522→177,522 MWmed. Sete origens alteradas, duas pertencentes ao treino; versão0 reproduzida; reenvio não altera dados; schema e duplicidade rejeitados. Aceite técnico com base no log; arquivos brutos dessa execução Windows não anexados nesta mensagem.
- Planejador enviado anteriormente pelo aluno calcula histórico=t+d, média=t+d…t+d+w−1 e alvo=t−h com união de conjuntos. Conferência do professor aprovou1/6/1/7 e2/7/2/9, duplicatas, entrada vazia e h6/d0/w1. Faltava rejeitar datetime com fuso; correção orientada, e aluno informou ter feito. Não foi recebida nova cópia do código corrigido.
- Executar um arquivo que apenas define funções pode terminar com sucesso sem saída: o corpo não é chamado. Não se interpreta silêncio como execução do planejamento nem como falha de Spark.
- Entrega localizada: planejar_recalculo_temporal.py preserva a lógica autoral, incorpora validação de fuso e acrescenta conferência escrita pelo professor. main chama a função e compara os quatro conjuntos com os deltas de impacto_correcao.csv; usa parâmetros de snapshot_treino.json e correção de conclusao.json. Caminhos explícitos, leitura apenas, nenhuma nova pasta de relatórios/backup. O aluno salva no mesmo arquivo e usa o mesmo comando.
- Verificação dessa chamada no ambiente do professor: coincide com o CSV da execução E104; imprime sete origens e duas no treino. Contraprova de fuso e casos de sobreposição/duplicação/vazio aprovados. Não se apresenta isso como execução no Windows do aluno.
- Interpretação do impacto: alvo na origem09/07 01h recebe+12; histórico em10/07 03h recebe+12; médias em10/07 03–08h recebem+2. No treino entram09/07 01h e10/07 03h;10/07 04h tem target_available_at igual ao corte11/07 06h e é excluída pelo critério estrito.
- O plano é conservador para revisões múltiplas: valores podem se compensar. A igualdade exata com mudanças numéricas é exigida aqui para a única correção positiva do laboratório.
- Versão0 reproduz a base fixada no experimento; versão1 representa o dataset corrigido para uma execução deliberadamente nova. Hora da medição não estabelece quando a revisão ficou conhecida; snapshots locais não provam publicação histórica ONS. Interpretação autoral ainda não recebida.
- Próxima unidade curricular: M07.3 Databricks. Não solicitar nova execução M07.1/Delta nem novos microexercícios de contagem. O roadmap não marca Databricks executado nem altera percentual global.


### 29/10/2026 — E106: conferência do planejador recebida e M07.2 técnico encerrado

- Aluno executou notebooks/planejar_recalculo_temporal.py. Quatro conjuntos coincidem com impacto_correcao.csv: histórico1, média6, alvo1, união7. Origens09/07 01h e10/07 03h pertencem ao treino;10/07 04–08h não pertencem.
- Evidência recebida por log; não se afirma auditoria independente dos arquivos Windows não anexados. A lógica autoral foi revisada e a chamada de leitura foi fornecida pelo professor.
- Decisão: entrega técnica M07.2 encerrada. Não pedir outro Spark, MERGE, backup ou contagem. A defesa conceitual de snapshots é consolidada em scale_comparison.md da próxima unidade.

### 29/10/2026 — E107: Databricks como reprodução verificável

- Aula completa e notebook IPYNB com16 células. Caminho de referência: Databricks Free Edition/serverless; documentação oficial consultada. Não exige trial pago, JAR, PySpark local novo ou cluster clássico. Workspace do aluno não acessado pelo professor.
- Preparador lê a geração original e o treino aceito, verifica parâmetros, consolida dois Parquets e um manifesto em dist/databricks/CJU_BA5EIGT/m07_3. Reenvio do mesmo pacote é conferido; entrada original preservada. A geração corrigida simulada de M07.2 não é a entrada desta reprodução.
- Notebook usa catálogo/schema/volume, hashes pós-upload, tabelas Delta gerenciadas criadas uma vez, propriedades do pacote, ID e versão consultados, leitura versionAsOf e comparação por FULL JOIN de todas as colunas. Não há overwrite, DROP, VACUUM ou treino de modelo.
- Verificação local identificou risco de literal temporal: datetime ingênuo6h virou9h em sessão UTC com Python no fuso local, admitindo7.488 linhas. Corte convertido explicitamente de texto para timestamp_ntz restaurou7.485 sem mudar o contrato. Correção incorporada antes da entrega e explicada na aula. Não invalida os artefatos M07.1/M07.2 já comparados; é uma adaptação da portabilidade.
- Professor executou células de entrada, transformação, publicação e confronto em Linux/Spark4.0.1/Delta4.0.1. Usou geração reconstruída dos anexos E103 e treino real recebido, não o bruto ONS. Ambas as configurações2/4 reproduziram7.485 linhas com zero divergências; tabela relida igual; reuso sem novo commit de dados; valores adulterados e finalidade incompatível rejeitados. Notebook válido e preparador idempotente.
- Não executados pelo professor: criação do volume Unity Catalog/UI, conta cloud/serverless, recibo no volume e comando Windows. O relatório Verificacao_M07_3_Professor.json explicita esse limite. Tempos locais não são publicados como desempenho Databricks.
- Autoria delimitada: reports/scale_comparison.md com identidade/versões, Exchange/Window e chave, escopo dos dois tempos e escolha justificada de ambiente. Exportar notebook com saídas e recibo. Aula preserva distinção entre zero custo medido e custo não medido.
- Próxima unidade curricular após essa entrega: M08/PyTorch. M07.3 continua não executado pelo aluno até a evidência chegar. Percentual global e inventário P1 não alterados por criação de pacote.


### 29/10/2026 — E108: Databricks executado e parecer revisado

- Entradas recebidas: m07_3_reproducao.ipynb e scale_comparison.md. Inspeção offline de 13 condições; sete células de código coincidem com a distribuição, sem outputs de erro. Não houve reexecução cloud nem acesso ao workspace pelo professor.
- Fonte: workspace.renewcast_m07.geracao_m073_f66e094498ef, ID e3c3dc5d-912c-4933-a14e-a7b476bbb374, versão0, 8.760 linhas. Treino: workspace.renewcast_m07.treino_m073_f66e094498ef, ID f0f6f4fa-3879-4e07-8f5c-3c89b9f2e128, versão0, 7.485 linhas. Fronteiras reproduzem 2025-09-01 07h / 2026-07-10 03h; último alvo disponível 2026-07-11 05h.
- Configurações solicitadas2/4: 3,691632100s / 2,993797549s; zero divergências e diferenças double máximas zero. Duração inclui comparação integral e termina antes do explain. Um ensaio por configuração não prova ganho causal de particionamento.
- Parecer: decisão de manter exploração local aceita. Correções orientadas: alteração M07.2 era simulada, não retificação ONS demonstrada; Exchange10 é lado de broadcast do JOIN; média emitida03h/d2/w6 usa20h–01h; Photon não é código Java/Photon compilado por JIT; plano inicial/isFinalPlan=false não prova coalescência AQE; memória e custos não medidos. Revisão não é nova autoria independente.
- Exportação registra recibo_20261029T232749Z_4848481e.json no volume; JSON separado não anexado. Código/saídas documentados, sem autenticação independente do workspace. Aceite delimitado preserva essa limitação e não exige repetir o experimento.
- M07.1–M07.3 encerrados no escopo executado. Próxima unidade M08.1, sem novos exercícios Spark ou promoção operacional.

### 29/10/2026 — E109: tensores, autograd e otimização com o treino real

- Entrega renewcast_m08_autograd.zip: notebooks/laboratorio_autograd.py, docs/Aula_M08_1_Autograd.md e verificação do professor. Execução normal completa; autoria opcional explicitamente separada, sem função vazia bloqueando a primeira execução.
- Entrada: treino M07.3 consolidado de7.485 linhas; duas features históricas h24/d2/w6. Ajuste7.291, exclusão por disponibilidade26, validação de desenvolvimento168. Normalização somente no ajuste; semana já explorada, sem novo holdout intocado.
- Teoria/código: shapes [n,2]/[2,1]/[n,1], regra da cadeia do MSE, forward/backward/step, gradientes acumulados, broadcasting indevido, diferenças finitas e limite de estabilidade da quadrática. Caso manualMSE2,5→1,305 após um passo de taxa0,1.
- Professor executou Python3.12/PyTorch2.7.1+cpu em Linux: gradiente conferido, recarregamento com diferença0, gap para mínimos quadrados2,63e-8. Taxa0,8 acima do limite≈0,550817 produziu perda≈1,78e16 após30passos. Os dois cenários foram definidos como demonstrações de estabilidade, sem tuning pelo erro futuro.
- No padrão, validação de desenvolvimento: MAE≈37,036 versus persistência≈37,992 MWmed, mas viés observado−previsto≈+22,460 MWmed. Resultado ilustra que minimizar bem o erro de ajuste não garante boa previsão. Não comparar diretamente com HGB/vento em outros protocolos nem promover este modelo.
- Autoria: função NumPy gradiente_mse e parecer de shapes, sinal, taxa, otimização e generalização. Windows e aprendizagem do aluno ainda pendentes. M08.2/M08.3/M09–M14 permanecem posteriores. Inventário P1 sem mudança e nenhum percentual global atribuído.

Versão1.61,29/10/2026 — E108 aceita a reprodução Databricks e revisa conclusões; E109 entrega a próxima unidade completa. Painel, checkpoint, matriz, evidências e aprendizagem reconciliados.


### 04/11/2026 — E110: gradiente e parecer M08.1 aceitos com assistência

- Recebidos no texto: m08_gradiente_autoral.py e parecer de três execuções Windows (20261104T131859Z_8f277a44, 20261104T132027Z_d5a8612c e 20261104T132133Z_97eada41). Código e redação declarados assistidos por Codex. Não foram recebidos os arquivos de resultado/curva dessas execuções.
- Gradiente conferido nesta revisão: caso manual dw=[[-1],[-2]], db=-3; MSE 2,5→1,305. Diferenças finitas em 17 exemplos com diferença máxima 1,263e-10; entradas somente para leitura preservadas; cinco shapes inválidos rejeitados.
- Parecer distingue broadcasting, backward/step/zero_grad, convergência versus generalização, taxa instável com perda finita e evidência de desenvolvimento. Limite quadrático corretamente delimitado. Aceite M08.1 no escopo assistido, sem certificar solução independente.
- Relato: taxa0,05 termina em0,6346101118839145; taxa0,8 em1,7769091784326462e16; MAE37,035713 e viés+22,459944 MWmed. Consistente com referência anterior; não foi recalculado dos arquivos Windows nesta revisão.
- Hash do laboratório informado coincide com o distribuído. O hash do treino Windows foi apenas relatado, diferente do professor; sem afirmação de identidade binária. Texto M07.3 reapresentado era anterior à revisão E108; parecer corrigido preservado.

### 04/11/2026 — E111: próxima unidade completa, Dataset/DataLoader e MLP

- Entrega renewcast_m08_2_dataset_mlp.zip: script completo notebooks/laboratorio_mlp.py, aula com leitura de código/álgebra/protocolo/autoria, verificação e figura das curvas do professor. Usa ambiente renewable-forecast existente e os três arquivos M07.3. Não instala pacotes nem exige reexecução Spark/Databricks.
- Janela por timestamps exatos, 24 valores de o−25h a o−2h; alvo o+24h; disponibilidade o+26h. MLP 24→32→1, 833 parâmetros, CPU/float32, AdamW, Dropout0,1, até60épocas, paciência8, sementes17/29/41. Nenhuma semente escolhida pela avaliação.
- Ajuste7079, seleção168, avaliação168, exclusões por disponibilidade52 e por janela inicial18. Escalas apenas no ajuste. A semana de avaliação (03/07 04h a10/07 03h) já foi examinada; não é novo holdout intocado.
- Referência Linux/Python3.12.14/PyTorch2.7.1+cpu: MAE persistência37,991646; linear24h33,678664; MLP17=32,724828, MLP29=33,700811, MLP41=33,159788 MWmed. Viés continua positivo nas redes; MLP não supera linear em todas as sementes. Faixa entre seeds não é IC; sem promoção operacional.
- Quinze conferências aprovadas: janelas com lacuna, invariância a futuro, fronteiras estritas, avaliação ponderada 4+1, modos/gradientes, shapes, sementes, checkpoint, escalas, recarregamento, pareamento, métricas e hashes. Recarregamento com diferença zero. Professor executou sobre pacote local de conferência derivado dos dados anteriores; não atribuir esses resultados ao Windows do aluno.
- Autoria solicitada: avaliar_lotes(modelo, loader), preservando modo/pesos/gradientes e calculando SSE/n, e parecer 400–700 palavras com interpretação temporal, épocas, sementes e decisão. Modo normal completo; --autoria usa a função do aluno na seleção após contraprova. Prática do aluno ainda pendente.
- Painel, checkpoint, matriz, aprendizagem e inventário reconciliados. P1 permanece8/10 entregas; M08.2 ativo, M08.3/GRU posterior, M09–M14 sem avanço artificial. Sem percentual global de formação.

Versão1.62,04/11/2026 — E110 aceita M08.1 com assistência declarada; E111 entrega a próxima unidade executável e verificada.


### 15/11/2026 — E112: aceite da avaliação em lotes e do parecer M08.2

- Entrega referente a 05/11: função avaliar_lotes e parecer MLP, com implementação/redação assistidas por Codex declaradas. Registra-se o aceite persistente agora, sem alterar a data da execução relatada.
- Função transcrita e executada em PyTorch 2.7.1+cpu: MSE 20 no caso 4+1; modos mistos restaurados em sucesso/exceção; pesos/gradientes preservados; loader vazio, shape incorreto, NaN e overflow rejeitados. Subtração no dtype original e quadrado/redução em float64, conforme contrato.
- Relato Windows: 7.079 ajuste, 168 seleção, 168 avaliação, 52 exclusões por disponibilidade, 18 janelas incompletas. Sementes 17/29/41: MAE 32,724828/33,700811/33,159788; linear 33,678664. MLP 29 perde ligeiramente em MAE, embora as três melhorem RMSE. Mediana não é ensemble; faixa não é IC. Manter linear como referência simples e MLP candidata de estudo é decisão aceita.
- Arquivos brutos Windows, hashes e figura do aluno não anexados. Concordância byte a byte relatada permanece evidência declarada; não se certifica autoria independente. Revisão em docs/Revisao_M08_2.md. Não repetir M07, M08.1 ou M08.2 para avançar.

### 15/11/2026 — E113: M08.3 GRU executável, aula e comparação com HGB

- Pacote renewcast_m08_3_gru.zip; modelo src/renewable_forecast/neural_gru.py; laboratório notebooks/laboratorio_gru.py; aula docs/Aula_M08_3_GRU.md. Mesma entrada M07.3 e contratos temporais M08.2. Sem instalação, download, Docker ou função vazia bloqueando o modo normal.
- Referência Linux/Python 3.12.14/PyTorch 2.7.1+cpu/scikit-learn 1.8.0, CPU, dois threads: run 20261115T163556Z_bd3adefd. Pacote M07.3 do professor preservado; não declarado binariamente idêntico ao Windows. Escalas somente no ajuste; mesmas 168 origens; seis redes e três baselines; parâmetros registrados antes do treino; nenhuma busca para fazer a GRU vencer.
- GRU 929 parâmetros, uma camada/16 estados, estado reiniciado por janela, Dropout explícito na cabeça. MLP 833 no mesmo protocolo; linear 25, HGB fixo nos 24 lags sem vento, persistência. AdamW 0,001; até 60 épocas; paciência 8; sementes 17/29/41, todas reportadas.
- MAE HGB 31,846768; mediana MLP 33,159788; mediana GRU34,911227 MWmed. Todas as GRUs perdem MAE para linear/HGB; duas melhoram RMSE contra HGB. Semana já examinada; não é novo holdout e não promove modelo operacional.
- Onze grupos de contraprovas e nove de auditoria: portas/GRUCell, 24 passos, estado, lotes/shapes, avaliador recebido, fronteiras, normalização, métricas/pareamento, checkpoints, hashes e futuro/lacunas. Seis recarregamentos com diferença zero. Pico residente aproximadamente 454 MiB do processo inteiro; tempos registrados sem benchmark causal. PowerShell e coleta nativa de memória Windows não executados nesta sessão.
- Autoria: passo_gru em NumPy devolvendo r/z/n/h, sem importar a referência; conferir com --autoria notebooks/m08_gru_autoral.py --verificar, sem repetir treino. Parecer explica portas, shapes, estado, épocas, métricas e decisão. Encerramento pelo aceite dessa entrega, sem microtarefas retrospectivas.
- Painel, checkpoint, inventário, matriz e aprendizagem reconciliados. M08.2 aceito; M08.3 ativo, execução do aluno pendente. M09 posterior; M10–M14 inalterados. P1 permanece 8/10; nenhum percentual global inventado.

Versão 1.63, 15/11/2026 — E112 registra o aceite M08.2; E113 entrega M08.3 executável e verificada.


### 15/11/2026 — E114: execução Windows e célula GRU do aluno aceitas

- Recebidos nove anexos da execução 20261115T164955Z_5e435b09: resumo, previsões, curvas, partições, origens sem janela, normalização, protocolo, resultado e HTML. Oito arquivos possuem hashes internos e todos coincidem. Recalculados os 27 valores de MAE/RMSE/viés das nove variantes, nas mesmas 168 origens, 1.512 linhas.
- Divisão 7.079/168/168, 52 exclusões por disponibilidade e 18 janelas incompletas; fronteiras estritas e épocas/paciência conferidas. Código declarado coincide com quatro fontes distribuídas; Parquets e checkpoints Windows não anexados. Diferença zero em seis recarregamentos consta do recibo, sem nova execução independente do load.
- Função NumPy passo_gru e cinco testes recebidos em texto, transcritos e executados: cinco aprovados. Reset após transformação recorrente com viés, estado não nulo, inputs somente leitura, shapes, NaN e sigmoide estável em ±1000. Onze grupos da conferência PyTorch/24passos aprovados; maior diferença 2,22e-16. Código aceito, sem pedir alteração, reenvio ou novo treino. Autoria independente não certificada.
- MAE Windows: persistência 37,991646; linear 33,678664; HGB 32,323956; medianas MLP 33,159788 e GRU 34,911227 MWmed. HGB é a referência provisória por MAE neste recorte. GRU 41 vence RMSE mas perde erro absoluto em 96/168 origens; redução de soma quadrática não implica menor MAE ou menor viés. Tempos agregados MLP 47,54s e GRU 126,80s, sem benchmark causal.
- HGB Linux 31,846768 versus Windows 32,323956: versões scikit-learn 1.8/1.9 e pacotes binários de entrada distintos; normalizadores/partições/alvos avaliados iguais. Diferença máxima de previsão HGB 10,179216 MWmed. Causa não isolada; não chamar de arredondamento nem invalidar execução. Usar números locais; sem exigir troca de dependências.
- Material Revisao_M08_3.md e recibo verificacao.json. Execução/implementação M08.3 aceitas. Parecer decisório do aluno não recebido e pode integrar a próxima aula. M08 não equivale a domínio independente total ou operação aprovada; não repetir as entregas aceitas.

### 15/11/2026 — E115: M09.1 atenção, máscaras e posição, entrega executável

- Pacote renewcast_m09_1_atencao.zip, aula docs/Aula_M09_1_Atencao.md; núcleo NumPy em src/renewable_forecast/attention_math.py e laboratorio notebooks/laboratorio_atencao.py. Ambiente existente; sem instalação, treino, Docker ou download de pesos. Contrato M07.3 reutilizado do M08.3, sem substituir código autoral do aluno.
- Referência Linux/CPU/PyTorch2.7.1+cpu, run 20261115T215729Z_f462e113: oito grupos de contraprovas, delta PyTorch 4,44e-16. Janela real 02/07/2026 03h–03/07/2026 02h para origem 03/07 04h, mesmo eixo NTZ. Q/K [1,24,4], V [1,24,1], pesos [1,24,24]. Projeções fixas não treinadas; saídas são representações, não forecasts.
- Atenção livre no passado disponível distingue-se de máscara causal de prefixo. Última consulta igual na camada única; permutação sem posição preserva equivariância, posições fixas quebram essa equivalência de conteúdo. HTML com mapas, CSVs e recibo exportados. Não se declara Transformer completo ou comparação fundacional executada.
- Autoria: atencao_escalada NumPy com máscara True=permitido, softmax estável e contraexemplos; conferir sem dados/treino com --autoria ... --verificar. Parecer explica máscaras, dimensões e limites; pode integrar decisão M08.3 ainda pendente. Execução/autoria do aluno M09.1 pendentes. M09.2/M09.3 seguem o roteiro; M10–M14 inalterados.
- Painel, checkpoint, inventário, matriz e aprendizagem reconciliados. P1 continua 8/10 entregas técnicas, item 10 parcial e comparação fundacional pendente; nenhum percentual global atribuído.

Versão didática 1.64, 15/11/2026 — E114 aceita entrega técnica GRU do aluno; E115 prepara e verifica a próxima unidade de atenção.


### 17/11/2026 — E116: atenção autoral executada nesta revisão

- Código NumPy e seis casos recebidos em 16/11 foram transcritos e executados: seis aprovados. A função passou nos oito grupos PyTorch, delta 4,44e-16. Logs Windows normais 20261116T225653Z_d6086b39 e 20261117T150330Z_b5b7c30d reconhecidos; não se atribui a eles a execução autoral feita agora no professor.
- CLI da atenção exige --autoria notebooks/m09_atencao_autoral.py; sem esse caminho argparse rejeita antes do cálculo. Execução normal usa referência. A função não requer correção; não repetir a unidade para avançar. Defesa pode integrar M09.3; autoria independente não certificada.

### 17/11/2026 — E117: composição Transformer recebida

- Dois anexos, convertidos em laboratorio_transformer.py e m09_transformer_verificacao.py, compilam como Python. Revisão confirma orquestração de duas camadas encoder/decoder post-norm, conversão de máscara ao PyTorch, cross-attention, perturbação de prefixo com memória fixa, conectividade de gradientes sem optimizer.step e persistência.
- Logs Windows: run 20261117T154658Z_0897bf5a completa e 20261117T154706Z_6cd8d15b verificar; 13 grupos, delta 6,66e-16, 11.200 parâmetros, encoder [1,24,16],decoder [1,6,16], prefixo/reload zero. São representações não treinadas; seis slots não definem seis horizontes.
- transformer_blocks.py e resultados completos não anexados: não se afirma reexecução independente das 13 conferências nem auditoria de toda a implementação. Reprodução relatada e código recebido reconhecidos nesse escopo; não exigir outra rodada igual para começar M09.3. Revisao_M09_1_2.md registra os limites.

### 17/11/2026 — E118: previsão pré-treinada e comparação pareada

- Pacote renewcast_m09_3_pre_treinado.zip, aula Aula_M09_3_Pre_Treinado.md, controlador scripts/executar_m09_3.py e laboratório. Preparação em .venvs/m09_3_chronos, sem alterar Conda chamador. Dependências fixadas; primeira execução baixa componentes CPU e 33 MiB de pesos; sem API paga/GPU. Modo offline reutiliza ambiente/snapshot verificados.
- Chronos-Bolt Tiny, revisão a0e552de83495b5c28c14c71c374f3e33280b340, 8.652.672 parâmetros, model.safetensors SHA 75068728d376d2bec670379eeef4bfb4d24c0cfe24d957451f8d19b447030a32. Arquivos públicos e model card preservados/verificados; trust_remote_code=False e carga local safetensors.
- Contexto 24h bruto em MWmed; normalização interna do pré-treinado; P50 principal prescrito, P10/P90 brutos. H24/d2 exige 26 passos desde history_end, índice 25. Baselines congelados M08.3 reutilizados com hashes, mesmas 168 origens/alvos; sem retreino ou escolha de contexto após ver a avaliação.
- Professor Linux/CPU, dois threads/float32, controlador executado criando ambiente novo e depois reutilizando offline. Run final 20261117T160556Z_cc6dd09f. MAE 31,340739 contra HGB Linux 31,846768: ganho 1,59%; RMSE 45,380137 contra 44,051119; viés+2,962412. Cobertura 80,36%, largura 83,60, sem calibração/recorte. Não é garantia futura ou promoção operacional. Windows deve comparar com seu HGB local 32,323956 e seus próprios hashes.
- Oito grupos independentes de auditoria: hashes, dez variantes/30 métricas, 26 passos, contraprova passo 24, pinball/cobertura, repetição, reprodução em ambiente privado e snapshot. Maior divergência nas métricas 7,11e-15; inferência repetida idêntica. Wheels Windows/Python3.12 consultados; Windows não executado nesta sessão. Overlap de pré-treino não verificado.
- Autoria de alinhamento por timestamps e parecer integrado consolidam M08/M09; modo normal completo. Após aceite M09.3 segue M10. CI/shadow/monitoramento contínuo do P1 permanecem separados; inventário permanece 8/10 até execução/fechamento das entregas pendentes. Sem percentual global novo.

Versão didática 1.65, 17/11/2026 — E116/E117 reconhecem trabalho recebido; E118 entrega a próxima unidade aplicada e verificada.

### 17/11/2026 — E119: recebimento e revisão do pré-treinado Windows

- Rodada normal recebida:20261117T212230Z_965de3d1. Os onze hashes das saídas coincidem;30 métricas recalculadas, maior diferença7,11e-15. As1.512 previsões dos nove baselines coincidem com predictions anterior recebido, identificado no protocolo.
- Alinhamento autoral em texto transcrito e executado: cinco grupos aprovados e seleção deP10/P50/P90 igual ao NPZ real[168,9,26]. Lead26 e índice25 nas168 origens;4.368 trajetórias conferidas. O arquivo binário da função e o Parquet de geração com o hash declarado não foram anexados.
- ChronosMAE31,340738 contraHGB32,323956: ganho0,983218MWmed/3,041763%. RMSE45,380136 contra44,221683: piora2,619649%.95 vitórias/73 derrotas; quatro dos sete blocos de24 origens melhoram. Cobertura135/168,20 abaixo/13 acima, largura83,595237. Sem clipping ou recalibração.
- Auditoria/registro auxiliares referem213329Z_3b201a01. Seu resultado completo não foi recebido; protocolo/latência/HTML da rodada anexada têm outros hashes. Não fundir os recibos. O empacotador gera uma lista declarativa de comandos/exitcodes, sem executá-los; essa lista não comprova os dez testes citados. A função foi conferida por execução própria nesta revisão.
- Revisao_M09_3_Windows.md registra o aceite técnico e a decisão do professor de manterChronos/HGB no desenvolvimento. Parecer próprio do aluno citado no empacotador não anexado; pode consolidar interpretação em três parágrafos, sem outro treino. Item10 permanece parcial pelo critério de encerramento que exigia essa defesa. A pendência não bloqueia a práticaM10.1.

### 17/11/2026 — E120: início aplicado do P2, contrato de telemetria ESA

- Entrega renewcast_m10_1_telemetria.zip, aula completa e código normal funcional em satellite-anomaly-monitor. NumPy/pandas existentes, offline, sem Docker, instalação ou modelos.
- Fonte ESA Anomaly DatasetMission1v2, DOI10.5281/zenodo.15237121. Canais50–52 do grupo10, ano2007:348.901 medições por canal. Valores preservados; nomes/unidades anonimizados. Membros de origem obtidos por intervalos HTTP e CRC verificado; checksum do ZIP inteiro não foi verificado. Identidades de membros e CSVs derivados registradas.
- Protocolo exploratório: grade90s, idade máxima180s.350.400 instantes,350.346 utilizáveis por canal,54 não utilizáveis. Mediana90s, maior lacuna1.170s. Conferência por buscaNumPy independente do merge_asof reconciliou valores, idade, disponibilidade e união dos intervalos anotados.
-33 linhas de anotação, dezIDs: três deAnomaly e sete deRareEvent. Nenhuma anotaçãoCommunicationGap no recorte, embora existam41 intervalos de amostragem acima180s. Não confundir lacuna medida com categoria anotada; não chamar sem anotação de normalidade comprovada.
- Cinco contraprovas: expiração, preservação de entradas, relógios distintos, alteração do futuro e fronteiras/entradas inválidas. Nenhum detector ou treino executado. Fonte sem registro de chegada; leitura UTC dos instantes e disponibilidade ainda assumidas.
- Atividade: implementar sincronizar_causal, conferir contraprovas e tabela real, explicar grade versus medição/evento e as hipóteses restantes. M10.2 amplia e fixa o recorte antes dos detectores; M10.3 avalia eventos e limiares. Referência Linux encerrada; execução/autoria do alunoM10.1 pendentes.
- Painel, checkpoint, matriz, aprendizagem e inventário reconciliados. P1 mantém pendências operacionais e defesa documental separadas; não há percentual global ou certificação de senioridade por execução.

Versão didática1.66,17/11/2026 — E119 aceita a entrega técnica recebida e E120 entrega a próxima prática do P2, com referência executada.
