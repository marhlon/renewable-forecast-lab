# M06 — do wheel Windows a um serviço em contêiner Linux

Marlon Alves Bomfim · 13/10/2026 · E85: aceite e revisão · E86: próxima unidade

## 1. O que sua entrega demonstrou

Foram conferidos os nove anexos e o código colado. O ponteiro corresponde ao recibo, e os cinco hashes de saída conferem com os arquivos recebidos. No Windows/Python 3.12.13, o ambiente novo importou a API do próprio `site-packages`. A resposta preservou modelo, política e probabilidade `0.20465385372296466`; a diferença para a referência foi zero. O pedido sem `lag_1h` recebeu HTTP 422.

Seu orçamento está correto: **26 wheels, 72.018.219 bytes, 68,6819 MiB; top 5 = 96,2425%**. Os percentuais do CSV conferem dentro do arredondamento a quatro casas. Usou biblioteca padrão, denominador correto, ordenação por tamanho e salvou todas as linhas.

| Item | Resultado da revisão |
| --- | --- |
| Reprodução Windows em venv novo | Aceita pelas evidências recebidas |
| Cálculo autoral do orçamento | Aceito |
| Parecer gerado automaticamente | Revisar aprovação presumida, vínculo entre ponteiros e compatibilidade de Python |
| Transporte para pasta independente | Não demonstrado nos anexos: os caminhos recebidos continuam na árvore do projeto |
| Docker e CI | Material entregue nesta unidade; execução ainda pendente |

O progresso reconhece cada entrega. A pendência de transporte permanece registrada; podemos avançar para a mudança real de ambiente no contêiner sem refazer a reprodução Windows já aceita.

## 2. Análise: onde compensa investigar o tamanho

SciPy ocupa 50,90%; NumPy, 17,45%. Juntos, **68,35%**. Os 21 wheels fora do top 5 somam apenas **2,58 MiB**. O wheel do serviço representa **0,014%** do total. Assim, reduzir seu código Python terá efeito pequeno sobre o volume distribuído. Não há evidência de que 68,68 MiB seja um problema operacional: medir transferência, disco e tempo de inicialização deve preceder uma otimização.

Os 173,86 segundos de instalação e 7,23 segundos de inicialização registrados são observações de uma execução; não são P95 nem benchmark de latência de previsão. Tamanho compactado dos wheels, tamanho instalado e tamanho da imagem Docker são medidas diferentes.

SciPy e NumPy são os dois maiores arquivos. NumPy é importado diretamente pelo runtime; SciPy é uma dependência do scikit-learn. Para provar a relação específica dos seus pacotes, a auditoria fornecida extrai `Requires-Dist` dos wheels reais. O relatório anterior mencionava o scikit-learn, mas não apresentava esses metadados nem explicava NumPy.

## 3. Corrigir a aprovação presumida

O trecho `else` do seu script assume diferença zero, cria um caminho descritivo e usa `release_sha256` como se fosse `model_sha256` quando falta o recibo. O texto final declara reprodutibilidade mesmo assim. Nesta execução o recibo existia, portanto não houve esse erro no resultado recebido. O problema é o comportamento em ausência de evidência.

Outra possibilidade é ler um `latest_release` novo e um `latest_run` antigo. O orçamento de A acabaria acompanhando o parecer de B. Nos anexos atuais, os IDs coincidem; a validação precisa preservar essa propriedade em execuções futuras.

O pacote adiciona `scripts/auditar_distribuicao.py`, que exige recibo, verifica os hashes, cruza IDs e referência, confere a lista e tamanho dos wheels e extrai dependências. Ele salva fatos em `autoria_revisada/`; preserva seu código e seu parecer original. Não cria uma conclusão humana automática.

**Correção autoral localizada:** no seu `notebooks/orcamento_distribuicao.py`, retire o fallback de aprovação. Se o recibo faltar, interrompa. Use campos obrigatórios, não valores padrão para sucesso. Impeça a associação entre releases diferentes. Você pode estudar `load_bundle()` no script fornecido para implementar essa verificação no seu código. Não precisa reescrever o cálculo do orçamento, que já está correto.

## 4. Aula de compatibilidade: interprete o nome do arquivo

`numpy-2.5.3-cp312-cp312-win_amd64.whl` identifica distribuição/versão, CPython 3.12, ABI CPython 3.12 e plataforma Windows x64. Esse arquivo não instala em um contêiner Linux.

Isso não significa que toda mudança de Python invalide todo wheel compilado. Mudanças de patch dentro de 3.12 normalmente preservam a tag `cp312`; wheels `abi3` têm outra abrangência; `py3-none-any` não carrega uma ABI nativa. Também contam `Requires-Python`, arquitetura e requisitos das bibliotecas. A restrição à versão exata no exercício anterior foi uma regra conservadora do protocolo.

Uma migração do modelo persistido exige manter uma referência conhecida e verificar carregamento, features e previsões. Baixar novos wheels não basta para aprová-la. Neste exercício, manteremos a versão exata do Python e das bibliotecas, o código, o pedido, o modelo e a política; a mudança planejada é Windows → Linux no contêiner. Se a instalação ou a comparação falhar, o pipeline encerra sem aprovar e conserva os logs.

## 5. O que você vai construir

| Etapa | Entrada | Saída |
| --- | --- | --- |
| Auditoria | Release + recibo Windows + wheels | Orçamento conferido e metadados das dependências |
| Preparação | Distribuição auditada | Contexto Docker com wheel puro do serviço, modelo, política e versões |
| Construção | Imagem Python fixada por digest + contexto | Imagem Linux, wheels Linux e novo lock com seus hashes |
| Verificação | Imagem executada localmente | HTTP 200/422, comparação de resposta e recibo |
| Integração contínua, depois da execução local | Mesmo contexto revisado, scripts e lock da imagem base | Mesmo gate executado por um runner; logs preservados |

**Imagem** é o conjunto de camadas usado para criar o ambiente. **Contêiner** é uma instância executando essa imagem. **Contexto de build** é o conjunto de arquivos enviado ao construtor. **Tag** nomeia uma imagem e pode mudar de destino; **digest** identifica seu conteúdo. O controlador resolve a imagem base, grava `base_image.lock.json` e reutiliza o digest em reconstruções daquele contexto.

O Dockerfile tem dois estágios. O primeiro obtém wheels para Linux nas versões capturadas e gera os hashes correspondentes. O segundo instala esses arquivos com `--no-index --require-hashes`, confere dependências e carrega o serviço. Os wheels Windows não são copiados. A primeira obtenção de dependências Linux usa rede; o build completo não é offline.

Se uma versão não tiver wheel Linux compatível, ou houver uma dependência específica da plataforma ausente, o build falha. Esse resultado exige revisar a migração, não remover a checagem ou atualizar bibliotecas automaticamente. O lock Linux é capturado nesta etapa; não representa uma promessa de builds binários idênticos indefinidamente.

Há duas configurações de rede diferentes: Uvicorn escuta em `0.0.0.0:8000` dentro do contêiner, permitindo receber tráfego pela interface dele; Docker publica uma porta aleatória somente em `127.0.0.1` do seu computador. `EXPOSE` documenta a porta, mas não publica o serviço sozinho.

## 6. Executar no seu Windows

Salve `renewcast_m06_docker_20261013.zip` em `C:\renewable-forecast-lab`. O pacote acrescenta scripts, templates e documentação; não substitui seus modelos nem seu parecer.

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m06_docker_20261013.zip -DestinationPath . -Force
python scripts/auditar_distribuicao.py
```

O resultado esperado da auditoria é **26 wheels e 68,68 MiB** para a execução enviada. Os arquivos ficam em:

`reports/packaging/CJU_BA5EIGT/h24_event_v1/20261010T231840Z_388ee417/autoria_revisada/`

Prepare o contexto:

```powershell
python scripts/preparar_container.py
```

Esse comando não precisa de Docker. A saída é `dist/container_service/<context_id>/`, identificada por `dist/container_service/latest_context.json`. O contexto contém o modelo e um pedido com features; mantenha o mesmo cuidado de acesso dos artefatos locais.

Para construir e executar, abra **Docker Desktop no modo de contêineres Linux**, com o mecanismo iniciado. Confira:

```powershell
docker version
docker info --format '{{.OSType}}'
```

O segundo comando precisa retornar `linux`. Se Docker não estiver instalado, use a instalação oficial para Windows indicada nas referências; o pacote não altera WSL, virtualização ou configurações do sistema. Se aparecer erro de mecanismo indisponível, abra Docker Desktop e aguarde o início antes de continuar.

```powershell
python scripts/verificar_container.py
```

Ele solicita a imagem `python:3.12.13-slim-bookworm` para sua captura, fixa o digest obtido, constrói e executa a imagem, compara o pedido e encerra o contêiner. A disponibilidade da tag e a execução do Docker serão verificadas na sua máquina. Se o pull falhar, preserve a mensagem; não substitua a tag silenciosamente.

Com Docker já funcionando, a sequência inteira pode ser executada por `scripts/run_m06_container.ps1`, que interrompe na primeira falha. Ele prepara um contexto novo; para repetir somente a construção do mesmo contexto e reutilizar seu digest, use `python scripts/verificar_container.py`.

Os resultados ficam em `reports/containers/CJU_BA5EIGT/h24_event_v1/<run_id>/`: `verification.json`, `response.json`, `environment.json`, `image.json`, `requirements.linux.lock`, `server.log` e `pipeline.log`. `latest_run.json` só é atualizado após aprovação. A imagem permanece local; o contêiner criado pelo exercício é removido ao final, inclusive em falha.

## 7. Integração contínua: o mesmo critério fora do seu terminal

O controlador retorna código de saída diferente de zero quando falha. Esse contrato permite que um runner interrompa a entrega. CI automatiza execução e verificação; não acrescenta evidência de generalização do modelo por si só.

`ci_examples/renewcast-container.yml` contém um workflow manual para GitHub Actions. Foi deixado fora de `.github/workflows`, portanto extrair o pacote não o ativa. Não houve acesso ao seu Git, push, publicação ou execução remota nesta entrega.

Para uma adoção futura, o checkout precisa conter os scripts e um contexto aprovado, com artefatos e `base_image.lock.json`; o campo `context_path` recebe o caminho relativo desse contexto. Só então o arquivo é instalado como workflow. Ele constrói/verifica e guarda logs, sem publicar imagem ou promover o modelo. A preparação do repositório e a execução remota ainda não estão concluídas.

## 8. Sua demanda: defender a migração

Primeiro corrija as três conclusões do parecer anterior: ausência de recibo impede aprovação; os dois maiores wheels são SciPy e NumPy; compatibilidade depende das tags/ABI/requisitos, e baixar arquivos não aprova uma migração.

Após executar o contêiner, escreva `parecer_container.md` na pasta do novo run, com até 20 linhas. Use os valores reais dos arquivos para responder:

1. Qual mudança foi isolada? Cite o Python e as versões de NumPy/scikit-learn em Windows e Linux, e os hashes de modelo/política.
2. O que mudou entre o lock Windows e o Linux? Distinga versão do pacote, nome/tag do wheel e hash. Não exija hash igual de dois binários de sistemas diferentes.
3. A probabilidade e a decisão foram preservadas? Cite referência, resultado e diferença. Se não foram, investigue sem aumentar a tolerância só para aprovar.
4. O que significa o tamanho da imagem? Explique por que não equivale aos 68,68 MiB de wheels compactados.
5. Qual decisão você toma: compatibilidade aceita, bloqueada ou evidência insuficiente? Delimite-a ao experimento, sem afirmar qualidade de produção.

**Fixação lexical:** contexto → arquivos de entrada; imagem → `image_id`; contêiner → processo temporário; tag → nome; digest → identidade de conteúdo; ABI → compatibilidade binária; gate → condições que determinam o código de saída. Feche a aula e explique esses sete termos usando seus próprios arquivos. O parecer será avaliado pelas relações e evidências que você estabeleceu.

**Critério de conclusão:** Docker executado com recibo coerente, locks e resposta conferidos, parecer autoral correto. A execução remota de CI será aceita somente quando houver run real. A entrega de um YAML não é CI concluída.

## 9. O que foi verificado pelo professor

Anexos Windows auditados, orçamento recalculado e erros lógicos identificados. Componentes Python executados na réplica: auditoria de release real, extração de METADATA, preparação do contexto, reconstrução do lock a partir de wheels Linux existentes, recusa de recibo ausente e ponteiros incompatíveis, comparação de respostas incluindo divergência de modelo/probabilidade. Sintaxe Python conferida.

**Não há mecanismo Docker ou PowerShell neste ambiente do professor.** Build da imagem, inicialização dentro do contêiner, disponibilidade de tags/versões Linux da captura Windows e workflow remoto não foram executados aqui. Esses estados permanecem pendentes; não foram substituídos por dados sintéticos ou recibos de aprovação.

## Referências primárias

- [PyPA — tags de compatibilidade](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/)
- [Docker — builds em múltiplos estágios](https://docs.docker.com/build/building/multi-stage/)
- [Docker Desktop para Windows](https://docs.docker.com/desktop/setup/install/windows-install/)
- [Docker — publicação de portas](https://docs.docker.com/engine/network/port-publishing/)
- [scikit-learn — persistência](https://scikit-learn.org/stable/model_persistence.html)
- [GitHub — disparo de workflows](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
