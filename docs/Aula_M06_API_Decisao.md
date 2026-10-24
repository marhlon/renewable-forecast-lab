# M06.1 — política persistida e API local de decisão

Marlon Alves Bomfim · Renewcast · 03/10/2026 · E63/E64

## O que foi aceito

A função autoral `selecionar_politica` resolve corretamente a seleção no cenário proposto. Os quatro arquivos recebidos conferem: três hashes de saídas, hash das previsões de origem, 24 linhas de decisões, 120 de sensibilidade e quatro trocas HGB. A auditoria não executou novos estimadores.

| Regra viável sob 120 alarmes | Alarmes observados | Custo FP+4FN |
|---|---:|---:|
| Frequência / 0,5 | 0 | 452 |
| Logística / 0,5 | 81 | 268 |
| HGB / 0,5 | 109 | **191** |

HGB/0,2 tem custo158, mas emite156 alarmes e ultrapassa a capacidade didática. Selecionar HGB/0,5 é aceitar custo33 maior para respeitar a restrição observada. Em termos de Pesquisa Operacional: minimizar o custo entre um conjunto finito de alternativas viáveis. `loc` constrói o conjunto viável; `sort_values(...).iloc[0]` escolhe a alternativa.

**O limite foi verificado em julho. Ele não é imposto pelo limiar durante a operação.** Se todas as probabilidades de outro período forem superiores a0,5, essa regra poderá alarmar em todas as emissões. Garantir uma cota futura exigiria definir uma janela e uma regra de controle com estado. Esta aula não implementa esse controle.

O núcleo da função foi preservado. Foram acrescentados validação de capacidade inteira não negativa, desempate determinístico por método/limiar e conversão de razão indefinida para `None`. Esta última importa ao serializar: com capacidade zero, a frequência/0,5 é viável, mas sua precisão é indefinida; JSON estrito representa isso por `null`, não `NaN`.

## Entrega desta aula

A seleção deixa de existir apenas no `print`. Ela passa a ser um artefato `policy.json`, com regra, custos, capacidade observada, identificação e hash das previsões usadas. Um processo servidor carrega esse artefato; outro processo envia um pedido HTTP e recebe a decisão.

**Escopo preciso:** a API aplica a política a uma probabilidade já calculada pelo classificador. O cliente usa uma previsão real do relatório de julho. Isso é replay de decisão; o servidor ainda não carrega o estimador nem produz novas probabilidades a partir de features. Essa integração e o monitoramento pertencem às etapas seguintes de M06.

| Camada | Arquivo | Responsabilidade |
|---|---|---|
| Análise e exportação | `notebooks/inspecao_decisoes.py` | Selecionar a política do desenvolvimento e salvar `policy.json` |
| Contrato | `DecisionRequest` em `src/renewable_forecast/decision_api.py` | Exigir probabilidade válida, campos conhecidos e timestamps com fuso |
| Decisão | `decidir` no mesmo módulo | Conferir método/evento/horizonte e aplicar `p_event >= threshold` |
| HTTP | `create_app` no mesmo módulo | Expor a regra pelo FastAPI |
| Servidor | Uvicorn | Manter o processo ouvindo apenas em `127.0.0.1` |
| Cliente | `notebooks/consultar_api_decisao.py` | Enviar uma linha real e uma contraprova inválida; salvar pedidos/respostas |

O campo `event_drop` ou `target_generation` não pertence ao pedido. O resultado realizado é necessário para avaliar uma decisão depois; não para aplicar a política agora. `extra="forbid"` rejeita esses campos se forem enviados.

## Instalar e executar

Baixe `renewcast_m06_api_decisao_20261003.zip` para `C:\renewable-forecast-lab`. Execute os comandos abaixo um por vez; só avance após a conclusão sem erro. O ambiente `renewable-forecast` já existe.

No primeiro PowerShell, aberto na raiz do projeto:

```powershell
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m06_api_decisao_20261003.zip -DestinationPath . -Force
python -m pip install -r requirements_m06_api.txt
python notebooks/inspecao_decisoes.py
python -m renewable_forecast.decision_api --policy reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json --port 8000
```

A instalação acrescenta as dependências da API. O notebook usa o experimento existente, agora conferindo também seus `protocol.json` e `metadata.json`, e grava `policy.json` na pasta `decisions`. Não é preciso executar `weather_events` novamente. O pacote não altera `pyproject.toml`, não acessa Git e não inclui um novo modelo treinado.

Quando aparecer `Uvicorn running on http://127.0.0.1:8000`, deixe esse terminal aberto. O comando continuar em execução é o comportamento esperado de um servidor.

Abra um **segundo PowerShell**:

```powershell
cd C:\renewable-forecast-lab
conda activate renewable-forecast
python notebooks/consultar_api_decisao.py
```

O cliente lê a política pela API e verifica o hash do relatório. Envia a primeira emissão cronológica do método escolhido, sem alvo observado, e depois um pedido alterado com `p_event=1.2` para verificar a rejeição.

Resultados esperados com os arquivos recebidos:

```text
Pedido real: HTTP 200
p_event: 0.16175954827073333
threshold: 0.5
alarm: false
Contraprova p_event=1.2: HTTP 422 (rejeição esperada).
```

`200` indica processamento bem-sucedido. `422` indica que o pedido não satisfaz o contrato; nessa contraprova, é a resposta correta. `alarm=false` no primeiro pedido também é correto:0,16176 é menor que0,5.

O cliente salva `request.json`, `decision.json`, `invalid_request.json`, `invalid_response.json` e `verification.json` em:

`C:\renewable-forecast-lab\reports\service\CJU_BA5EIGT\h24_event_policy_v1`

O serviço também expõe:

- `GET /health`: identifica a versão e informa que está disponível.
- `GET /policy`: mostra a política carregada.
- `POST /decisions`: recebe o pedido e devolve a decisão.
- [Documentação interativa local](http://127.0.0.1:8000/docs): permite enviar pedidos pelo navegador enquanto o servidor estiver aberto.

Para encerrar o servidor, use Ctrl+C no primeiro terminal. Se alterar o artefato, reinicie o servidor: a política é carregada uma vez na inicialização. O hash identifica exatamente seus bytes.

## Prática aplicada no contrato

Abra `http://127.0.0.1:8000/docs`, expanda `POST /decisions`, clique em **Try it out** e copie o conteúdo do `request.json` produzido. Troque somente `p_event` por `0.5` e execute. Como a regra é inclusiva (`>=`), o alarme deve ser verdadeiro. Depois envie um timestamp sem o sufixo de fuso: o contrato deve rejeitá-lo.

No código `decision_api.py`, localize `Probability`, `AwareDatetime`, `extra="forbid"` e `decidir`. Identifique qual parte responde por domínio numérico, relógio, campos inesperados e regra de negócio. Essa leitura liga cada biblioteca ao comportamento que você acabou de observar.

Envie o `decision.json`, o `verification.json` e explique em três ou quatro linhas por que o campo `capacity_enforced_at_runtime` é falso mesmo quando a política foi selecionada sob limite120. A implementação autoral da seleção já foi aceita; essa explicação verifica a transferência do conceito para um serviço.

## Fixação lexical

| Termo | O que observar |
|---|---|
| Artefato de política | JSON que permite reproduzir qual regra foi aplicada |
| Contrato de entrada | Tipos, campos e relações que um pedido precisa respeitar |
| Endpoint | Operação identificada por método HTTP e caminho, como `POST /decisions` |
| Serialização | Transformação entre objetos Python e JSON; `None` vira `null` |
| Stateless | Cada decisão usa apenas o pedido e a política; não há contador acumulado de alarmes |
| Replay | Aplicação do serviço a uma previsão histórica, sem chamar isso de observação ao vivo |

## Evidências e próximo marco

Execução verificada pelo professor em Python3.12: seleção com capacidades120/156/0, ausência de alternativa viável, desempate invariável à ordem, JSON estrito, limites da probabilidade, timestamps equivalentes e rejeição de método/evento/horizonte incompatíveis. Servidor e cliente foram executados em processos separados; pedido real retornou200 e contraprova retornou422. Não foram reajustados estimadores.

O pacote inclui `docs/evidencias_m06_api/` com a auditoria, a política de referência, a resposta do serviço e os registros de verificação. Os arquivos de referência não são entrada automática da API: o comando carrega o `policy.json` gerado no seu experimento.

**Progresso:70%, com a oitava macroentrega em andamento.** M05 tem implementação autoral aceita; a API de decisão foi verificada pelo professor e aguarda reprodução pelo aluno. Carregar o classificador para gerar novas probabilidades, operar em shadow, registrar resultados posteriormente e monitorar falhas/desempenho ainda não foram concluídos.

Referências primárias: [FastAPI: corpo do pedido](https://fastapi.tiangolo.com/tutorial/body/), [Pydantic: tipos e AwareDatetime](https://docs.pydantic.dev/latest/api/types/#pydantic.types.AwareDatetime), [FastAPI: verificação de endpoints](https://fastapi.tiangolo.com/tutorial/testing/).
