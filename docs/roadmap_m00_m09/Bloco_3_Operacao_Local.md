# Bloco 3 — registro, serviço e preparação operacional local

25/11/2026, 21:37 BRT (recibos em 26/11/2026, 00:37 UTC). Construção, execução e análise: Codex. Não há resposta independente do usuário atribuída a esta entrega.

## Escopo efetivamente executado

Foram construídos e executados um **MLflow Model Registry real local**, um serviço HTTP restrito a loopback com controles exercitados, um benchmark curto com limites prévios e um coletor de emissões/reconciliação com contraprovas em replay. O detector de mudanças separou entrada, qualidade/atraso e desempenho em casos controlados. Foi produzido um plano delimitado de cloud; nenhum recurso cloud foi criado.

Os códigos estão em [bloco3_ops.py](../../src/renewable_forecast/bloco3_ops.py), [bloco3_operacao_local.py](../../scripts/bloco3_operacao_local.py) e [bloco3_operacao_verificar.py](../../scripts/bloco3_operacao_verificar.py). A raiz de evidências é `reports/fechamento_m00_m09/bloco3_engenharia/M06-03` até `M06-09`. Cada ID possui protocolo, resultado e parecer. O [manifesto](../../reports/fechamento_m00_m09/bloco3_engenharia/M06-03/manifesto_operacao_local.json) registra os hashes das saídas desta rodada, incluindo os resíduos da primeira tentativa fracassada. A revisão integrada do agente principal e o cadastro determinam o aceite final; este documento não altera o cadastro.

| ID | Construção e execução desta rodada | Limite operacional preservado |
| --- | --- | --- |
| M06-03 | MlflowClient criou modelo registrado, versões, assinatura, tags de identidade, alias ativo e rollback com recarga/inferência | Sem Registry remoto, autenticação do servidor MLflow ou alta disponibilidade; duas versões do mesmo artefato |
| M06-04 | Ledger persistente e bloqueio do modo live sem PIT; 48 emissões/reconciliações em replay e rejeições causais | Zero emissões live; M04-05/CI e janela real não comprovados |
| M06-05 | Journal, conciliação, atraso/erro por previsão e teste de recuperação de estado | Zero horas de continuidade real; C1–C4 operacionais permanecem pendentes |
| M06-06 | Referência, limiares e triagem fixados antes; contraprovas separadas e resposta documentada | Sem resposta/plantão observado ao vivo; sem garantia probabilística de falsos alertas |
| M06-07 | Socket 127.0.0.1, chave efêmera, limite real de corpo, limite de taxa, validação de contrato e logs mínimos | Aceite restrito ao ensaio local; TLS, RBAC, exposição pública e permissões do SO não homologados |
| M06-08 | 480 requisições HTTP com CPU/RSS/latência/erros medidos, SLO e orçamento prévios | Ensaio curto; custo de produção e energia/depreciação local não medidos |
| M06-09 | Plano reviewable de conta/rede/identidade/custo/TTL/rollback/encerramento | Sem conta/região/teto aprovados; implantação, custo real e teardown não ocorreram |

## Protocolo, dados e reparo registrado

Os sete protocolos foram gravados às **00:34:22 UTC**, antes de iniciar as medições. O protocolo M06-03 possui SHA-256 `fe4d1c0976164d3a80ab60b9c455ae724ba60d62977c19af08c32a96471a5960`. Os parâmetros de carga, amostra, drift, disponibilidade e critérios estão ali congelados.

O modelo é o HGB `HGB_lags24_calendar` já produzido no bloco 2, com corte de treino em 01/07/2026 e 28 atributos: 24 lags e quatro componentes de calendário. O bundle preservado tem SHA-256 `369e7fd10ca50d8fa2128b9824a0ec0ca250fb86e87d535ec1bf5926bd3962d6`. Nenhum modelo, calibrador, intervalo ou política foi ajustado nesta rodada. A entrada de smoke/replay compreende as primeiras 48 linhas completas de junho/2026, um período já examinado no desenvolvimento. Não é uma nova avaliação intocada.

O arquivo de origem local é `dist/databricks/CJU_BA5EIGT/m07_3/geracao.parquet`, SHA-256 `bf3a58b37a2857951eba280452b622db4f541ad13b2c663c2fd5c54c94ec7104`. UTC e disponibilidade duas horas após o evento continuam hipóteses de estudo. O arquivo atual não demonstra que a mesma vintage estava disponível na origem histórica.

A primeira execução chegou à criação do banco MLflow e falhou ao serializar HGB. MLflow 3.16 usa skops por padrão e exige confiar explicitamente no tipo interno `sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor`. O artefato é o bundle local do bloco 2, com hash verificado; somente esse tipo específico foi incluído no parâmetro `skops_trusted_types`. Também foi corrigido o uso da API instalada de assinatura, `to_dict`. Nenhuma lista indiscriminada de tipos foi confiada. Banco e arquivos parciais foram preservados. O [recibo da falha](../../reports/fechamento_m00_m09/bloco3_engenharia/M06-03/falha_01.json) e o [adendo](../../reports/fechamento_m00_m09/bloco3_engenharia/M06-03/adendo_reparo_compatibilidade.json), criado antes da segunda execução, registram causa e código novo. A segunda execução usa `registry_run_02`; amostra, modelo, SLO e limiares não mudaram.

## Model Registry e rollback

Foi utilizado **MlflowClient.create_registered_model/create_model_version/set_registered_model_alias/get_model_version_by_alias**, com backend novo `registry_run_02/mlflow_registry.sqlite`. É o Model Registry do MLflow 3.16, não o registro de exercício `event_registry` nem apenas tracking de runs.

Modelo registrado: `renewcast_b3_frozen_hgb`. Run: `b694192dae75432e9efbc0ef7afa5aa1`. Versões criadas: **1 e 2**. A sequência real foi `active → 1`, `active → 2`, `active → 1` por rollback. Em cada transição, o alias foi consultado e `mlflow.pyfunc.load_model("models:/renewcast_b3_frozen_hgb@active")` recarregou o artefato. As 48 previsões coincidiram com o bundle original, diferença máxima **0.0**. A assinatura contém os 28 nomes/tipos double obrigatórios e saída float64; os tags preservam hashes do bundle, origem, assinatura e entrada. O CSV de entrada tem SHA-256 `d16eafd6d012a0da35aa7f68c4c4276c8b3770784a8a1514430109820e98bff9`.

As duas versões apontam o mesmo modelo congelado. A transição exercita resolução e rollback de implantação/empacotamento; não demonstra superioridade de outro modelo. O critério local de transição é integridade, contrato de entrada, paridade da inferência e execução no ambiente autorizado. Não é critério de aprovação de produção. O [recibo do Registry](../../reports/fechamento_m00_m09/bloco3_engenharia/M06-03/registry_mlflow.json) conserva timestamps/fontes/versões de cada transição.

## Serviço e contraprovas de segurança

O serviço carregou o modelo pelo alias resolvido e abriu um socket real **127.0.0.1 em porta efêmera**, encerrado ao final. O runtime rejeita peers diferentes de 127.0.0.1 e não confia em cabeçalhos de proxy. A chave tem 256 bits aleatórios e foi mantida somente em memória; não foi impressa, gravada no protocolo ou passada na linha de comando. A comparação usa `hmac.compare_digest`.

O corpo máximo é 8.192 bytes. O limite confere Content-Length e os bytes efetivamente recebidos, incluindo transferências chunked. A taxa da carga é limitada a 1.000 requisições/s no processo; uma instância separada com três requisições por 60 segundos exercitou a rejeição. Apenas o conjunto exato de 28 atributos numéricos finitos é aceito. Swagger/OpenAPI público foi desabilitado para este escopo.

| Contraprova HTTP real | Resultado |
| --- | --- |
| Chave ausente ou incorreta | 401 em ambos os casos |
| Entrada válida com chave | 200 e identidade da versão |
| Corpo declarado maior que o limite | 413 |
| Corpo chunked maior que o limite | 413 |
| Atributos inválidos ou JSON malformado | 422 em ambos os casos |
| Quarta chamada ao limitador de três | 429 após três respostas 200 |

Os oito casos passaram. O log possui somente timestamp real, UUID gerado no servidor, status, bytes lidos, duração e identidade do modelo. A busca do token completo no arquivo foi negativa; o verificador também confere o conjunto exato dos campos permitidos. O teste ASGI separado rejeitou peer não loopback mesmo com chave válida. Não foram testados credenciais de outros usuários do Windows, ataques locais com acesso ao processo, TLS, multitenancy, armazenamento seguro compartilhado ou exposição pública. O journal/log não possui rotação de longa duração; uma implantação contínua deve integrar retenção/capacidade antes de iniciar a janela. Esses limites restringem a conclusão ao serviço temporário local.

Em incidente local: interromper processo, invalidar chave pelo encerramento/reinício, preservar os registros sem segredos, conferir integridade/alias e revisar causa antes de reabrir. Um responsável e canal devem ser designados pelo titular para operação; Codex não assume plantão.

## Capacidade medida

O orçamento foi fixado em 240 requisições por cenário, concorrências 1 e 4, timeout de cinco segundos, duração máxima de 30 segundos por cenário, dois threads de CPU, p95 ≤ 500 ms, erros ≤ 1%, RSS ≤ 2.048 MB e interrupção em 3.072 MB. Não foram criados recursos pagos; o teto de gasto incremental cloud é R$ 0.

| Concorrência | Requisições | Duração | Throughput | p50 | p95 | p99 | Erros | CPU do processo | Pico RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 240 | 3,385 s | 70,89/s | 13,58 ms | 18,18 ms | 22,96 ms | 0 | 6,156 s | 430,76 MB |
| 4 | 240 | 3,875 s | 61,93/s | 59,14 ms | 79,37 ms | 240,77 ms | 0 | 6,672 s | 431,68 MB |

Os dois cenários passaram os SLOs locais. A concorrência maior **piorou throughput e latência** neste desenho: a inferência é síncrona no worker ASGI, com fila e contenção no mesmo processo. Isso orienta limitar concorrência e medir outra arquitetura antes de ampliar carga; não há evidência de escala positiva.

CPU e memória abrangem runner, cliente HTTP, servidor, bibliotecas MLflow e modelo no mesmo processo. CPU normalizada por um core pode exceder 100%; foram cerca de 182% e 172%. RSS é total, sem subtração de baseline. Nenhuma fatura foi obtida; energia/depreciação local não foram medidas. Zero recursos criados não significa custo total de produção observado. Os valores completos e resultados dos SLOs estão no [CSV](../../reports/fechamento_m00_m09/bloco3_engenharia/M06-08/capacidade_custo.csv). Foram poucos segundos de carga, sem ensaio de sete dias ou incidentes de infraestrutura real.

## Coleta, reconciliação e continuidade

O `ShadowLedger` registra origem, alvo de 24h, instante do evento de entrada, chegada, vintage, hash, modelo, trace e previsão. `received_at` é sempre o horário real de gravação. No replay, `emission_clock` e as chegadas são explicitamente simulados. O modo live sem contrato point-in-time M04 verificado falha antes de criar o arquivo; mesmo com o contrato declarado, emissões históricas fora dos cinco minutos tolerados são rejeitadas. O ledger rejeita chegada posterior à emissão, vintage posterior à chegada, entrada antiga/futura, horizonte errado e duplicação. A reconciliação exige emissão correspondente, alvo/chegada compatíveis e rótulo já disponível no relógio de observação. Reinício recupera emissões/alvos do journal; identidade de modelo/modo divergente ou sequência inválida bloqueia a leitura.

Foram gravadas **48 emissões e 48 reconciliações em replay**. Quatro contraprovas — chegada futura, vintage futuro, entrada antiga e origem duplicada — foram rejeitadas. O teste separado de persistência reiniciou o ledger, conciliou um alvo após sua chegada e rejeitou conciliação antecipada/duplicada. A simulação mantém o atraso de duas horas do alvo, portanto disponibilidade assumida em origem +26h. A execução levou minutos; **não foram esperadas 26 horas reais**. Não foi consultada uma fonte ao vivo nem criada uma emissão contemporânea de previsão com dados chegados realmente naquela origem.

Consequentemente, **zero horas de shadow live/continuidade foram demonstradas**. M06-04/C1–C2 e M06-05/C1–C4 continuam operacionais pendentes. Cobertura/largura de intervalos, Brier/confiabilidade, prevalência, custo/capacidade de alarmes prospectivos não foram inferidos deste journal. Permanecem preservados como C3/C4 de M06-05, com origem em M05-01/M05-02.

Preparação para a janela futura: confirmar M04/PIT e CI, designar responsável, autorizar coleta sem comandar equipamentos, congelar modelo/política e observar sete dias consecutivos, com mínimo de 144 emissões e conciliação posterior dos alvos reais. Essa janela é **plano não executado**, que deverá ser congelado novamente com datas/canais/fonte concretos antes da operação.

## Mudanças de distribuição, atraso e desempenho

O protocolo define as primeiras 24 linhas como referência e as 24 seguintes como corrente. A referência já foi examinada; não é referência prospectiva de produção. Os limiares são: mínimo 20 amostras, deslocamento da média maior que 1,5 desvios da referência, MAE maior que 1,5 vezes a referência e mais de 10 MW de aumento, missing acima de 5% ou atraso acima de seis horas. Trata-se de triagem determinística de efeito, sem p-value e sem garantia estatística de falso positivo.

No recorte histórico, o deslocamento foi 0,489 desvio; MAE de referência 41,60 MW e corrente 27,31 MW: nenhum alerta. Casos sintéticos separados provaram a reação: entrada deslocada em três desvios → investigar entrada; MAE elevado de 41,60 para 144,81 MW → investigar modelo; missing 20% ou atraso 12h → investigar qualidade primeiro. O caso sem alteração não alarmou. Nenhum caso retreinou ou promoveu modelo.

O orçamento de triagem é uma investigação por variável/janela diária, não um limite probabilístico de falso alarme. O protótipo devolve uma decisão por chamada; deduplicação entre janelas/plantões deve ser integrada ao sistema real de incidentes. A [resposta](../../reports/fechamento_m00_m09/bloco3_engenharia/M06-06/resposta_drift.md) orienta preservar evidência, investigar qualidade antes de atribuir queda ao modelo, avaliar baseline e submeter rollback/ajuste à revisão humana. Não foi observada resposta operacional ao vivo.

## Cloud e intervenção concreta ainda necessária

O [plano cloud](../../reports/fechamento_m00_m09/bloco3_engenharia/M06-09/deploy_cloud.json) prepara um primeiro ensaio privado: uma instância CPU, sem GPU, identidade mínima, storage privado, TTL, alarme de orçamento, smoke, rollback, inventário e encerramento. Conta/projeto/região/titular/teto financeiro e prazo não foram fornecidos/aprovados. O plano lista pontos de decisão e regras de interrupção; nenhum comando de cloud foi executado. `desligamento.json` informa expressamente que não houve provisionamento nem teardown, sem inventar um recibo de encerramento de recursos.

Docker não foi necessário e não foi aberto. A comprovação de CI remoto pertence à trilha do agente principal. A intervenção necessária antes de cloud é informar/autorizar a conta/projeto, região, orçamento numérico, prazo e credenciais do titular por mecanismo seguro; antes de shadow, também comprovar os contratos M04 e designar responsável/fonte/janela reais. Essas pendências não são exercícios do usuário nem condição para reconhecer a entrega local executada.

## Reprodução e conferência

Com PowerShell e o ambiente já instalado:

```powershell
& 'C:\Users\marhl\miniconda3\envs\renewable-forecast\python.exe' -m pytest tests/test_bloco3_ops.py -q
& 'C:\Users\marhl\miniconda3\envs\renewable-forecast\python.exe' scripts/bloco3_operacao_verificar.py
```

O primeiro comando executou **9 testes aprovados**; ocorreu apenas um warning de permissão para cache do pytest, sem falha de teste. O segundo verifica hashes das saídas congeladas, identidade do bundle, alias ativo, recarga/inferência do Registry, campos mínimos de telemetria, resultados de segurança/replay e contraprovas de drift; não treina nem mede nova carga.

Os comandos executados para a rodada original foram `scripts/bloco3_operacao_local.py prepare` e `scripts/bloco3_operacao_local.py run`, com o Python acima. O runner recusa sobrescrever protocolo ou banco já existentes. Para uma nova medição, preservar esta rodada e preparar protocolo/identificador de execução próprios antes de medir; não apagar evidências para repetir a mesma identidade. O reparo de compatibilidade está explicitamente encadeado ao protocolo original. As evidências não substituem CI remoto, autorização de implantação ou avaliação humana.
