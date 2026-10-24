# M06 — diagnosticar o serviço por requisição

5 de outubro de 2026 · Renewcast · CJU_BA5EIGT · h24/d2

## Ponto de partida e entrega desta unidade

O parecer anterior foi entregue: 24 observações, Brier0,1326030158, referência0,1875628068, Skill0,2930207323 e quatro cenários coerentes. Código e relatórios recebidos conferem entre si; a maior diferença numérica é1,11e-16. Essa correção está encerrada no escopo técnico demonstrado. Não falta uma nova síntese daquele exercício.

Agora você vai operar o classificador durante uma sequência de requisições, observar uma degradação controlada e diagnosticar se a ação deve recair sobre entrada, serviço ou modelo. A infraestrutura fornecida mede o processo. Sua autoria será uma análise independente das requisições que resulte numa decisão verificável.

**Entrega técnica:** API com log por requisição, IDs de correlação, latência, resultado HTTP e identidade do artefato; cliente/servidor conciliados sem mudar o modelo. **Entrega autoral:** `notebooks/diagnostico_servico.py`, métricas por fase e rastros dos incidentes. O objetivo não é aumentar a contagem de testes.

## Executar uma vez, de ponta a ponta

Baixe `renewcast_m06_telemetria_20261005.zip` para `C:\renewable-forecast-lab`. No PowerShell dessa pasta, com `(renewable-forecast)` ativo:

```powershell
Expand-Archive -LiteralPath .\renewcast_m06_telemetria_20261005.zip -DestinationPath . -Force
python -m renewable_forecast.service_exercise
```

O comando carrega o modelo já salvo em `models/CJU_BA5EIGT/h24_event_batch_v1`, inicia uma API em `127.0.0.1:8001`, realiza a carga e encerra essa API automaticamente. Não exige outro terminal, novo treino ou alteração do servidor que porventura esteja em8000. A entrada é o `example_request.json` desse mesmo artefato; a política é `reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json`.

Cada execução recebe um run_id e uma pasta própria:

```text
reports/service/CJU_BA5EIGT/h24_event_telemetry_v1/<run_id>/
  client_requests.csv
  server_requests.jsonl
  requests.csv
  summary.csv
  verification.json
```

O arquivo `reports/service/CJU_BA5EIGT/h24_event_telemetry_v1/latest_run.json` aponta para a última execução concluída e contém o hash de sua verificação. Não procure um CSV por nome em outras pastas. O console também informa o caminho completo.

Se8001 estiver ocupada, use o argumento existente:

```powershell
python -m renewable_forecast.service_exercise --port 8002
```

Isso muda apenas a porta local. Uma falha não cria métricas fictícias nem atualiza latest_run.json como se houvesse conclusão. Pode deixar logs parciais na nova pasta para diagnóstico; a aprovação depende de verification.json com verified=true.

## O experimento e a comparação que ele permite

Há uma requisição de aquecimento, separada da avaliação, e45 requisições medidas:

| Fase | Requisições | Composição planejada |
|---|---:|---|
| normal |20| Mesmo pedido válido;20 respostas200 |
| invalid_payload |5| Pedido com campo p_event proibido na inferência;5 respostas422 |
| incident |20|15 pedidos normais,3 com atraso adicional de750ms e2 respostas500 injetadas |

As falhas e os atrasos são intencionais e identificados nos logs. As durações são medidas em HTTP real no computador. Não são falhas espontâneas do modelo, tráfego de produção ou observações de vento inventadas. Nas38 respostas200 medidas, o pedido e o modelo são iguais; as probabilidades devem permanecer iguais. As duas falhas500 injetadas interrompem antes de executar o estimador.

O aquecimento reduz a mistura entre primeira chamada e chamadas subsequentes. Isso não transforma um exercício pequeno, sequencial e com o mesmo pedido em benchmark de capacidade. Não medimos concorrência, throughput máximo, saturação, disponibilidade mensal ou shadow ao vivo.

## O que o código faz

Abra `src/renewable_forecast/http_telemetry.py` e percorra três componentes:

1. `HttpTelemetry`: gera request_id; mede com perf_counter_ns; intercepta o início e o fim do envio da resposta ASGI; registra status, duração, rota, erro e identidade do modelo. Faz isso também quando há422 ou500.
2. `LabFaults`: somente com ativação explícita aceita os comandos didáticos de atraso/erro. Fora desse modo, rejeita a tentativa de simulação. A política de decisão e as32 features continuam sob o contrato anterior.
3. `JsonlWriter`: registra um objeto JSON por linha. O laboratório usa um processo; a escrita tem proteção entre threads. Uma falha de escrita é sinalizada e a conciliação detecta ausência de registros.

Depois abra `src/renewable_forecast/service_exercise.py`:

- `call`: mede do lado do cliente até receber o corpo completo; conserva status e X-Request-ID mesmo numa resposta de erro.
- `reconcile`: exige correspondência1:1 entre os IDs do cliente e do servidor, mesma fase/status/modelo e respostas concluídas.
- `summarize`: aplica o denominador declarado e calcula percentis apenas entre respostas bem-sucedidas.
- `run_exercise`: controla ciclo de vida do servidor, carga, artefatos e encerramento. Nunca chama fit.

O tempo ASGI termina ao concluir o envio do corpo da resposta pela aplicação. O tempo do cliente inclui também conexão, comunicação e recebimento. Nenhum deles, isoladamente, mede somente predict_proba. Os logs não registram corpo das features, query string nem credenciais.

## Métricas e regras declaradas antes da carga

Neste exercício:

```text
elegíveis_serviço = quantidade_2xx + quantidade_5xx
taxa_falha_servidor = quantidade_5xx / elegíveis_serviço
taxa_rejeição_entrada = quantidade_4xx / quantidade_total
latência_P95 = quantil empírico0,95 das durações das respostas2xx
```

Separar4xx é uma escolha explícita para avaliar o atendimento dos pedidos elegíveis deste experimento. Não é uma lei universal para todo serviço. Rejeições também precisam de observação e de um indicador próprio; uma mudança de contrato pode tornar inválido o que antes era aceito.

**Regra didática:** investigar o serviço se taxa5xx>1% ou P95 das respostas bem-sucedidas>250ms. Se não houver requisição elegível, a taxa de falha e o percentil ficam indefinidos. Nenhuma fase é certificada como operação segura por passar nessa regra.

Na fase incident, a taxa de falha planejada é2/20=10%. A mediana pode continuar pequena enquanto P95 cresce:15 das18 respostas200 não receberam atraso, mas3 receberam. Uma média ou mediana isolada pode esconder a experiência da cauda. Os tempos normais e os percentis exatos dependerão do computador.

Para pandas, o contrato é `Series.quantile(0.95, interpolation="linear")`. Em NumPy, use `np.quantile(valores, 0.95, method="linear")`. P95 é um quantil empírico; não promete que95% das próximas requisições cumprirão aquele valor.

## Sua implementação autoral

Crie **`notebooks/diagnostico_servico.py`**. O programa deve partir dos dados por requisição de uma execução, sem importar summarize nem copiar os números do summary.csv. Implemente estas saídas em `<run_id>/autoria/`:

**1. `diagnostico.csv`, uma linha por fase.** Calcule: requests, success_2xx, rejected_4xx, failed_5xx, eligible_requests, server_error_rate, rejection_rate, median_success_ms, p95_success_ms, slow_successes e action. As colunas comuns devem coincidir com summary.csv dentro da tolerância1e-9. Valores indefinidos precisam permanecer ausentes, sem zero substituto.

**2. `incidentes.csv`, uma linha por requisição problemática.** Inclua toda resposta4xx/5xx e toda resposta200 com duration_ms>250. Guarde request_id, phase, status_code, duration_ms, requested_fault, fault_injection e uma classificação autoral: entrada, serviço ou latência. Esse arquivo permite sair da métrica agregada e chegar ao registro responsável.

**3. `decisao.md`, uma decisão apoiada em evidências.** Registre a fase prioritária, dois request_id que sustentem a escolha e a ação. Explique por que este experimento não sustenta retreinar o classificador. Use a igualdade das previsões/modelo e os registros das falhas, não apenas frases gerais.

Resolva a entrada por `--run-dir` explícito ou pelo ponteiro latest_run.json da pasta definida. Rejeite ausência/incompatibilidade; não procure outro experimento nem crie fallback. Para reforçar linhagem, confira o hash de requests.csv com output_sha256 desse nome no verification.json. O arquivo requests.csv já está conciliado; warmup está excluído.

| Coluna de requests.csv | Significado |
|---|---|
| request_id | Chave única gerada pelo servidor e recebida pelo cliente |
| phase | normal, invalid_payload ou incident |
| status_code | Código HTTP, conciliado entre cliente e servidor |
| duration_ms | Tempo medido dentro da aplicação ASGI |
| client_duration_ms | Tempo medido pelo cliente até ler o corpo |
| requested_fault / fault_injection | Simulação pedida / aplicada: slow, error ou ausente |
| p_event | Probabilidade retornada em200; ausente em rejeição/falha |
| response_complete | Confirma o fim do envio da resposta |
| model_sha256 / policy_sha256 | Identidade do modelo e da política usados |

O programa precisa aceitar este comando depois que você o implementar:

```powershell
python notebooks/diagnostico_servico.py
```

**O que enviar ao concluir:** seu `diagnostico_servico.py`, `diagnostico.csv`, `incidentes.csv`, `decisao.md` e o `verification.json` da execução. Não é necessário reenviar o parecer anterior. Se houver bloqueio de execução, envie o erro antes de mudar caminhos ou criar dados substitutos.

## Critério de conclusão e continuidade

A entrega estará demonstrada quando:45 requisições tiverem correspondência1:1; o modelo permanecer preservado; a análise separar corretamente4xx/5xx/latência; os cálculos autorais coincidirem; e a decisão apontar para os registros concretos. Não exigirei nova bateria de tarefas de uma linha depois disso. A revisão será do conjunto entregue.

Na verificação do professor, seis testes dos contratos passaram e o fluxo HTTP real foi executado com fit proibido por instrumentação de teste. O arquivo de evidência acompanha o pacote. Os tempos do professor não são metas de reprodução. PowerShell/Windows não foram executados aqui; o comando Python correspondente foi verificado.

Essa unidade amplia o serviço com telemetria local. Continuam pendentes operação contínua, carga concorrente, coleta ao vivo, orçamento real de alarmes e rollback/registry. A próxima unidade de M06 é versionamento e retorno à versão anterior com um incidente rastreável; não se declara M06 completo por este exercício.

## Fixação lexical pela ação

| Termo | Fixação no artefato |
|---|---|
| Middleware | Localize o código que observa a requisição e a resposta sem recalcular o modelo |
| Correlação | Mostre o mesmo request_id nos registros do cliente e do servidor |
| Latência de cauda | Compare mediana e P95 na fase incident |
| SLI | Defenda o numerador, denominador e escopo de sua taxa5xx |
| SLO | Diferencie o indicador medido do limite didático1%/250ms |
| Injeção de falha | Mostre a marca que identifica uma falha deliberada |
| Triagem | Use request_id para decidir entre corrigir entrada, recuperar serviço ou investigar demora |

Fontes primárias: [FastAPI — middleware](https://fastapi.tiangolo.com/tutorial/middleware/), [Starlette — middleware ASGI](https://starlette.dev/middleware/), [Google SRE — monitoring distributed systems](https://sre.google/sre-book/monitoring-distributed-systems/). São referências técnicas; os limiares e a carga desta aula são escolhas didáticas explícitas.
