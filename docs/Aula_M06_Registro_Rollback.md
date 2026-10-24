# M06 — registrar versões, ativar e comprovar um rollback

7 de outubro de 2026 · Renewcast · CJU_BA5EIGT · h24/d2

## De onde partimos e o que você entrega agora

O diagnóstico anterior está encerrado. Seus três arquivos de saída conferem com os hashes de conferencia.json; as cinco fontes coincidem com os anexos anteriores; as 33 métricas/ações e os dez incidentes foram reconciliados. Os NaN estão corretos. A reprodução da revisão é aceita em E80. Não há nova tarefa sobre aquele parecer.

Nesta unidade, a pergunta é operacional: **se eu apontar o serviço para outra versão, como identifico o que ele realmente carrega e como volto à anterior sem perder o histórico?**

Você vai executar uma troca real entre dois classificadores já produzidos, observar o processo desatualizado, provocar um incidente identificado e verificar a restauração. Depois escreverá uma auditoria SQL que confronta transações e requisições. A entrega reúne controle de versões, transações, concorrência, HTTP e interpretação; não exige novo tuning.

| Competência | Ferramenta | Evidência desta unidade |
|---|---|---|
| Identificar um artefato reproduzível no ambiente existente | SHA-256, manifesto, joblib | Versões v1/v2 com arquivos e hashes registrados |
| Alterar estado com rastreabilidade | SQLite, transação, chave estrangeira | Alias e histórico confirmados no mesmo commit |
| Recusar uma escrita baseada em leitura antiga | Geração do estado e compare-and-swap | Tentativa com geração zero rejeitada quando a atual é um |
| Distinguir configuração desejada de processo carregado | FastAPI/ASGI, HTTP 503, readiness | Processo antigo recusa novas inferências até reiniciar |
| Comprovar recuperação | Telemetria, request_id, identidade do modelo | HTTP 200 após rollback, com modelo e probabilidade da v1 |
| Auditar uma sequência temporal | SQL com LAG, CTE e JOIN | Consulta autoral sobre transições e chamadas reais |

Este é um registro local implementado em SQLite. Não é o MLflow Model Registry. A prática ensina o mecanismo de versões, aliases e ativação; operar o Registry do MLflow continua sendo uma competência distinta. A unidade não encerra M06 nem demonstra operação contínua.

## Os dois artefatos usados

| Nome no exercício | Pasta existente | Corte de treino |
|---|---|---|
| v1 | `models/CJU_BA5EIGT/h24_event_batch_v1` | 31/07/2026 06:00 UTC |
| v2 | `models/CJU_BA5EIGT/h24_event_api_v1` | 01/08/2026 05:00 UTC |

A política é a já usada: `reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json`.

O pedido comum vem de `h24_event_api_v1/example_request.json`, emitido em 01/08 às 05 UTC. É compatível com os dois cortes. Usar o pedido antigo da v1 para consultar o modelo ajustado no corte posterior violaria o contrato temporal: o runtime precisa rejeitar essa combinação.

O registro copia quatro arquivos por versão: model.joblib, manifest.json, example_request.json e policy.json. Os originais são preservados. O ambiente é conferido pelo runtime existente; o pacote não contém seus modelos nem instala bibliotecas. Se um dos artefatos estiver ausente/incompatível, o comando termina com erro explícito. Não procura outro modelo ou gera um substituto.

## Executar o fluxo completo

Baixe `renewcast_m06_registry_20261007.zip` para `C:\renewable-forecast-lab`. No PowerShell dessa pasta, com renewable-forecast ativo:

```powershell
Expand-Archive -LiteralPath .\renewcast_m06_registry_20261007.zip -DestinationPath . -Force
python -m renewable_forecast.registry_exercise --threads 2
python notebooks/inspecao_registry.py
```

O primeiro comando Python registra os artefatos, inicia e encerra as instâncias da API e faz as chamadas. Por padrão, escolhe uma porta local livre em cada início; não exige segundo terminal. O segundo abre o registro em modo somente leitura e mostra as transições, chamadas e colunas para sua auditoria.

Uma pasta por execução evita misturar repetições:

```text
reports/registry/CJU_BA5EIGT/h24_event_registry_v1/<run_id>/
  registry/registry.sqlite
  registry/versions/v1/  e  registry/versions/v2/
  versions.csv
  deployments.csv
  client_requests.csv
  server_requests.jsonl
  requests.csv
  deployment_probes.json
  rejected_changes.json
  common_request.json
  responses.json
  summary.csv
  verification.json
```

O `latest_run.json` da pasta superior identifica a última execução concluída. Uma execução interrompida conserva rastros parciais e não recebe aprovação. A inspeção confere o hash do manifesto e dos arquivos usados; a consulta autoral roda em cópias temporárias em memória. Não modifica o registro encerrado.

## O que deve acontecer

| Etapa | Alias desejado | Processo carregado | Resposta/resultado |
|---|---|---|---|
| Início | v1, geração 1 | v1, geração 1 | Três inferências 200 |
| Tentativa com leitura antiga | Continua v1/g1 | v1/g1 | Escrita esperava geração 0: rejeitada |
| Ativação da v2 | v2, geração 2 | Ainda v1/g1 | Readiness e tentativa de inferência retornam 503 |
| Reinício | v2/g2 | v2/g2 | Três inferências 200 |
| Incidente controlado | v2/g2 | v2/g2 | Duas respostas 500 com marca `error` |
| Rollback confirmado no banco | v1, geração 3 | Ainda v2/g2 | Readiness e tentativa de inferência retornam 503 |
| Reinício após rollback | v1/g3 | v1/g3 | Três inferências 200; probabilidade da v1 restaurada |

São 13 tentativas de inferência: nove sucessos, duas falhas injetadas e duas recusas de processo desatualizado. Há ainda cinco consultas GET de readiness, registradas separadamente. Os dois 503 fazem parte da comprovação do contrato; não devem ser confundidos com as duas falhas injetadas que motivam o rollback didático.

O último resultado deve conter `rollback restaurou v1 com geração 3`. Os números de probabilidade dependerão dos seus artefatos; o critério é a igualdade antes/depois para o mesmo modelo e pedido, com tolerância 1e-12. Na réplica do professor, v1 produziu 0,411681 e v2 0,201792. Esses números não são metas para o seu computador nem comparam a qualidade preditiva dos candidatos.

## Entender o mecanismo antes de escrever a auditoria

**Versão e alias.** A versão identifica um conjunto de bytes registrado. O alias é um nome estável que aponta para uma versão. Repetir o registro com mesmo identificador e mesmos bytes é idempotente; tentar substituir os bytes sob o mesmo identificador é recusado. A imutabilidade é um contrato da aplicação: um administrador ainda consegue editar o disco, e as conferências detectam divergências.

**Geração e concorrência.** A versão pode voltar a v1; a geração avança de 1 para 2 e depois para 3. Uma operação escrita por quem leu geração 1 não pode ser aplicada quando o registro já está na 3, mesmo que o nome ativo tenha voltado a v1. É o problema conhecido como ABA: o nome voltou ao início, mas o histórico mudou.

**Transação e atomicidade.** Em `event_registry.py`, leia `switch_version`. O código prepara a versão, inicia `BEGIN IMMEDIATE`, confere a geração, insere a transição e atualiza o alias. Se a segunda escrita falhar, o rollback da transação remove também a primeira. Não pode existir uma troca confirmada no histórico sem a mudança correspondente do alias. Esse rollback de uma transação SQL é diferente de restaurar uma versão de modelo.

**Carregado e desejado.** Em `registry_service.py`, leia `same_activation` e `Guard`. O processo guarda a identidade com que iniciou. Na entrada de novas inferências, compara-a com o estado desejado. Se divergir, responde 503. `/health` informa que o processo está vivo; `/deployment` informa se está pronto para atender a ativação atual.

**Recuperação observada.** Atualizar o alias para v1 não basta. O fluxo reinicia o serviço e faz novas inferências. A resposta e o log devem identificar v1, geração 3, novo activation_id e os mesmos hashes da primeira v1. As probabilidades também precisam coincidir para o pedido comum.

A checagem ocorre na entrada: uma chamada já admitida pode terminar durante uma mudança de alias. A prática usa chamadas sequenciais e reinício controlado; não implementa implantação sem interrupção, cancelamento de requisições em andamento ou coordenação distribuída. O reinício é deliberado e observável.

## Sua autoria: auditar transações contra o que foi servido

Abra **`notebooks/inspecao_registry.py`**. A leitura, a conferência dos arquivos e a conexão temporária estão prontas. Implemente **uma consulta SQL em `SQL_AUTORAL`**, devolvendo estas sete colunas, uma linha por geração:

| Coluna | Regra |
|---|---|
| generation | Geração confirmada na tabela deployments |
| from_version | Versão de origem da transição |
| to_version | Versão de destino da transição |
| previous_to_version | Destino da transição anterior, calculado com LAG |
| chain_ok | 1 quando a transição inicial parte de NULL ou a origem corresponde ao destino anterior, com geração consecutiva; 0 caso contrário |
| successes_2xx | Quantidade de respostas 2xx ligadas ao activation_id daquela transição |
| model_sha256 | Hash do modelo da versão de destino, obtido em versions |

Use estas relações:

```text
deployments.to_version = versions.version_id
deployments.activation_id = requests.activation_id
```

O ponto de partida para a janela é:

```sql
LAG(to_version) OVER (
    PARTITION BY alias ORDER BY generation
) AS previous_to_version
```

Calcule também a geração anterior para verificar consecutividade. Uma CTE pode calcular as janelas; outra agrega as chamadas por activation_id; o SELECT final faz os JOINs. Agregar antes do JOIN impede que as 13 requisições multipliquem as três transições. `COALESCE(contagem, 0)` é válido para ausência de chamadas contadas; não autoriza transformar uma taxa 0/0 em zero.

Para esta execução, a consulta deve produzir três linhas, gerações 1/2/3, cadeia válida e três sucessos em cada geração. A geração 3 deve apontar para o mesmo modelo da 1. Não preencha esses valores manualmente: derive-os das tabelas. O notebook confere o formato, mas não declara a lógica autoral correta só porque a consulta executou.

Depois de implementar:

```powershell
python notebooks/inspecao_registry.py --autoria
```

A saída fica em `<run_id>/autoria/auditoria_transicoes.csv`. Escreva também **`<run_id>/autoria/parecer_rollback.md`**, com uma decisão curta sustentada por:

- activation_id e hash que mostram qual versão foi restaurada;
- um request_id de sucesso após a restauração, distinto dos dois IDs que motivaram a ação;
- a distinção entre voltar o alias e comprovar que o processo atende a nova geração;
- o motivo pelo qual o incidente injetado não demonstra piora estatística da v2.

Entregue `verification.json`, `deployments.csv`, `versions.csv`, `requests.csv`, seu `inspecao_registry.py` e os dois arquivos de autoria. Todos são pequenos; os binários dos modelos e o banco não precisam ser reenviados. O conjunto permite verificar sua consulta e decisão sem pedir outra sequência de alterações mínimas.

## Verificação do material entregue e alcance

O professor executou o fluxo com os dois artefatos reais da réplica, usando HTTP local. O método fit foi substituído por uma função que falha se for chamado: o fluxo completo passou. Quatro verificações dirigidas passaram: atomicidade alias/histórico, duas escritas concorrentes, adulteração de arquivo e retorno ABA que exige atualizar o processo. Nenhum teste foi pulado. A execução foi Python/Linux; Windows/PowerShell não foi executado aqui.

O pacote acrescenta event_registry.py, registry_service.py e registry_exercise.py em src/renewable_forecast; o notebook de inspeção, o teste dirigido e esta aula. A API, o runtime e a telemetria anteriores são reutilizados. As saídas de referência e o registro de verificação do professor ficam em `docs/evidencias_m06_registry_professor/` e são identificados como referência.

O teste dirigido está em `tests/test_event_registry.py`, para quando você modificar o mecanismo. Ele usa os modelos já existentes; se faltarem, informa skip. O comando principal de execução da aula já verifica o fluxo e é suficiente para iniciar a prática; não é necessário repetir toda a suíte do projeto.

## Fixação lexical por artefato

| Termo | Onde você o demonstra |
|---|---|
| Bundle | Quatro arquivos vinculados a uma identidade de conteúdo |
| Alias | Linha active em aliases, apontando para uma versão |
| Geração | Revisão do estado; cresce mesmo ao retornar à versão antiga |
| Compare-and-swap | Atualização aceita somente se expected_generation ainda corresponder à atual |
| Commit | Alias e histórico confirmados juntos |
| Liveness | Processo responde em /health |
| Readiness | Processo carregou a ativação desejada e pode servir inferência |
| Rollback do modelo | Nova ativação da versão anterior, com motivo e evidências |
| LAG | Relação entre uma transição e sua antecessora na consulta autoral |

Fontes primárias: [SQLite — transações](https://www.sqlite.org/lang_transaction.html) e [MLflow — versões e aliases](https://mlflow.org/docs/latest/ml/model-registry/workflow/). A transação e o registro desta aula são locais; a referência MLflow permite comparar os conceitos, não implica uso dessa API no exercício.

E80 encerra a reprodução do diagnóstico. E81 registra esta prática de versionamento/rollback como entregue e verificada pelo professor. Execução e auditoria autoral do aluno ainda estão pendentes. O próximo trabalho de M06 será empacotamento e reprodução do serviço em ambiente isolado; operação contínua, validação operacional e os demais marcos permanecem separados.
