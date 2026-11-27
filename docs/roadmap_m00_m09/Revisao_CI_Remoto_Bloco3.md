# Revisão técnica do CI remoto — bloco 3

26/11/2026. Revisão: Codex, agente de operação local, em tarefa separada da publicação. Foram lidos os protocolos, recibos, workflow, guard, testes e logs preservados, recalculados hashes e consultados os endpoints públicos canônicos do GitHub por GET. Esta revisão não publicou arquivos, não executou novos testes/runs, não abriu PR e não alterou o cadastro, o código ou os pareceres anteriores.

**Parecer: aprovar M06-02/C1 e C2 para o escopo do workflow de contratos do bloco 3.** Existem execução remota, falha temporal relevante, correção mínima e execução positiva com 16 testes em ambiente GitHub Actions. O aceite é de CI; não autoriza produção e não comprova shadow, continuidade, implantação cloud ou treinamento integral do P1 no runner.

## Identidade e resultados conferidos

Repositório: `marhlon/renewable-forecast-lab`, público segundo a resposta de acesso preservada e os metadados remotos consultados. Branch: `codex/bloco3-ci-20261126`. Workflow: `.github/workflows/bloco3-contratos.yml`, nome `Bloco 3 - contratos locais`, evento `push`, job `contracts`, timeout de 15 minutos. A permissão declarada do workflow é `contents: read`; o checkout usa `persist-credentials: false`.

| Evidência | Controle negativo | Execução corrigida |
| --- | --- | --- |
| Commit | `047d8662158793f3e0e393957f1a6b382f8f3296` | `a487f7c9f37951102cc2be9ff38830ea04ad5f52` |
| Run | [45889419488](https://github.com/marhlon/renewable-forecast-lab/actions/runs/45889419488) | [45889590759](https://github.com/marhlon/renewable-forecast-lab/actions/runs/45889590759) |
| Job | [140148107307](https://github.com/marhlon/renewable-forecast-lab/actions/runs/45889419488/job/140148107307) | [140148659800](https://github.com/marhlon/renewable-forecast-lab/actions/runs/45889590759/job/140148659800) |
| Conclusão remota | `completed / failure` | `completed / success` |
| Início/fim do job, UTC | 20:13:15–20:13:54 | 20:14:36–20:15:27 |
| Verificação temporal | Falhou com lag2 observado 29, esperado 28 | Passou com lag2 observado 28, esperado 28 |
| Testes pytest | Não executados após a falha do guard | **16 passed in 2.50s** |

As respostas remotas de [run negativo](https://api.github.com/repos/marhlon/renewable-forecast-lab/actions/runs/45889419488) e [run positivo](https://api.github.com/repos/marhlon/renewable-forecast-lab/actions/runs/45889590759) confirmaram independentemente branch, evento, SHA e conclusão dos recibos locais.

O [commit de correção](https://github.com/marhlon/renewable-forecast-lab/commit/a487f7c9f37951102cc2be9ff38830ea04ad5f52) é filho direto do negativo. A consulta do diff mostrou somente `config/ci_bloco3.json`: `inject_lag_failure` mudou de `true` para `false`, restaurando a configuração aceita. Workflow, guard e testes não foram removidos ou flexibilizados para produzir o sucesso. O commit negativo adicionou dez arquivos à base remota; outras fontes selecionadas do pacote já existiam no parent. A contagem de arquivos do pacote não deve ser apresentada como contagem de arquivos alterados no commit.

## Falha relevante e contraprova

No controle negativo, checkout, instalação de dependências e instalação de PyTorch CPU passaram. O passo **Verificar contrato temporal** executou `python scripts/verificar_ci_bloco3.py` e informou `passed=false`, `invariant=lag2_exact_timestamp`, `expected_lag2=28`, `observed_lag2=29.0`. O processo encerrou com código 1. Os passos posteriores de contraprova e pytest foram pulados. Portanto, a falha demonstrada ocorreu no contrato temporal esperado, não por falta de dependência, credencial ou erro de infraestrutura.

No commit corrigido, o guard informou `passed=true` e lag2 28. O passo seguinte executou novamente o guard com `--contraprova` por subprocesso e exigiu código 1, o nome exato da invariante e `passed=false`. Esse passo passou. Assim, a execução verde conserva um teste negativo e não depende apenas de um caminho que sempre retorna sucesso.

O último passo executou os três arquivos selecionados: cinco testes de dados, nove de operação local e dois de contratos neurais. Os logs registram 16 aprovações. Os dados são fixtures construídas em memória; persistência usa diretórios temporários dos testes; as redes dos contratos são instanciadas no próprio teste. Não foi carregado um bundle treinado ou snapshot de dados ignorado da máquina Windows.

## Ambiente e reprodução por checkout remoto

Os logs mostram checkout via `actions/checkout@v7`, fetch do SHA integral de cada run, profundidade 1, em `/home/runner/work/renewable-forecast-lab/renewable-forecast-lab`. Os runners foram GitHub-hosted distintos, identificados como `GitHub Actions 1000000442` e `1000000443`, ambos Ubuntu 26.04. As imagens eram revisões diferentes de `ubuntu-latest`; não se usa esta rodada para comparar desempenho de hardware.

O Python executado foi `/opt/hostedtoolcache/Python/3.12.16/x64`, configurado por `actions/setup-python@v7`. O workflow fixa `PYTHONPATH=src`, `PYTHONNOUSERSITE=1` e `OMP_NUM_THREADS=2`. PyTorch **2.7.1+cpu** foi instalado do índice oficial CPU. O log inicial de cada setup informa que o cache pip não foi encontrado. O run positivo salvou depois o cache de pacotes pip; não há etapa de restauração de modelos/datasets locais.

Foram comparadas as **13 fontes do protocolo** com a árvore Git remota do commit positivo: todos os SHA-256 locais coincidiram com o protocolo e todos os hashes Git de blob calculados localmente coincidiram com a árvore retornada pelo GitHub. Incluem workflow, requisitos/configuração, guard, módulos importados, notebook de contratos e três arquivos de teste. A configuração positiva coincide com a fonte aceita antes da publicação.

O repositório remoto também contém arquivos históricos versionados, inclusive ambientes/artefatos antigos. Por isso, não se descreve o checkout como uma árvore contendo somente essas 13 fontes. A conclusão demonstrada é mais precisa: **o workflow dos contratos reproduziu-se a partir do checkout remoto em runner novo, usando o Python instalado pelo setup e fixtures próprias, sem depender de arquivos ignorados ou caches de modelos da estação local**. Não foi executada a suíte integral de todos os módulos, Docker, treino de modelos, avaliação sobre os dados históricos completos ou implantação.

## Integridade dos logs e histórico de tentativas

Os hashes abaixo foram recalculados dos arquivos locais e coincidem com `execucao_ci_remoto.json`:

| Arquivo em `reports/fechamento_m00_m09/bloco3_engenharia/M06-02` | SHA-256 |
| --- | --- |
| `actions_falha_job_140148107307.log` | `9b197e3de365669aa8f510c015e9a9c093cad1060c8b7da6d63fd6b3ff9c7f18` |
| `actions_sucesso_job_140148659800.log` | `3fd44cf4011dede979caac05856d03b120222b91c5af8f1b1b6920c13a992480` |

Os arquivos `actions_falha_jobs.json` e `actions_sucesso_jobs.json` conservam conclusões de cada passo, identidades, SHAs e horários. `publicacao_falha.json` e `publicacao_correcao.json` vinculam as publicações à branch e aos commits. `execucao_ci_remoto.json` registra o ciclo encerrado às **20:15:39.725773 UTC**, código 0, ambos os controles confirmados e ausência de merge/deploy.

A primeira tentativa do orquestrador, às 19:27:40–19:27:41 UTC, retornou HTTP 404 antes de qualquer evento de publicação registrado. Seu recibo foi preservado em `execucao_ci_remoto_tentativa1.json`. O adendo `adendo_endpoint_github.json`, das **20:12:27.838303 UTC**, registra a correção da barra final na URL REST raiz, a contraprova de endpoint público e o hash do recibo anterior. Esse adendo antecede a nova execução, iniciada às **20:12:43.896284 UTC**. A resposta de acesso canônico das **20:12:46.473295 UTC** identifica o repositório correto e `private=false`.

O reparo de URL não foi tratado como alteração de modelo ou melhora de teste. Os recibos da cópia isolada e o parecer local anterior também foram preservados; eles descreviam o estado antes da execução remota e não são sobrescritos por esta revisão.

Os recibos de acesso/publicação não contêm valores de credenciais; a revisão não solicitou ou leu o conteúdo da credencial em cache. O log de checkout contém o tratamento mascarado padrão do Actions, e não foi observado valor de segredo nos trechos de autenticação inspecionados. A comprovação de CI não é uma auditoria geral de segredos de todo o histórico do repositório.

## Decisão por critério e efeito no fechamento

**C1 atendido:** workflow realmente ativado no repositório remoto, com URLs, commits, ambiente e logs das execuções.

**C2 atendido no escopo dos contratos selecionados:** falha temporal deliberada e pertinente, correção mínima, contraprova preservada na execução verde e 16 testes aprovados em checkout/runner remoto, sem dependência de arquivos ignorados da estação. O escopo deve constar expressamente no cadastro e no relatório; não se conclui que o pipeline completo de produção foi validado.

Recomenda-se acrescentar esta revisão e os novos recibos ao cadastro M06-02, conservando o snapshot e as constatações anteriores como histórico. Considerando a contagem integrada informada pelo agente principal, esse aceite permite passar de **11 para 12 IDs integralmente validados** no bloco 3 e de **sete para seis IDs abertos**, sem encerrar M06-04/05/06/07/08/09 ou migrar suas exigências operacionais para obter aprovação artificial.

Não houve merge ou deploy nesta entrega. Não foi aberto PR nesta revisão; o workflow possui gatilho `pull_request`, portanto essa ação poderia disparar uma terceira rodada além das duas autorizadas. O [link de comparação](https://github.com/marhlon/renewable-forecast-lab/compare/main...codex/bloco3-ci-20261126) permite revisar as diferenças. A aprovação aqui é de evidência técnica de CI remoto e não concede autorização de implantação.
