# M06 — entregar uma instalação reproduzível do serviço

Marlon Alves Bomfim · Renewcast · E84 · 09/10/2026

## Resultado desta aula

Ao concluir, você terá uma distribuição do classificador h24: código instalável, bibliotecas, modelo, política, pedido de exemplo e evidência de inferência em um ambiente novo. A entrega funciona sem instalação editável e sem consultar um índice de pacotes durante a reprodução. A captura inicial precisa de internet para baixar os wheels e construir o pacote.

Esta aula trata de reprodução de software na mesma plataforma e versão exata de Python. Um venv isola os pacotes; continua apoiado em uma instalação de Python e no sistema operacional. Não é um executável Windows autossuficiente, uma imagem Docker nem uma aprovação do modelo para operação.

**Demanda profissional:** “Entregue o serviço a outro analista, de modo que ele consiga instalar e reproduzir sua resposta sem conhecer a configuração do seu ambiente de desenvolvimento. Documente o que foi transportado e o que continua sendo pré-requisito.”

## Onde estamos

O inventário técnico do Renewcast tem **7 de 10 entregas aceitas no escopo experimental: 70% por contagem de itens, sem pesos de esforço**. O item 8, serviço/monitoramento, está em andamento; o utilitário Windows e o benchmark neural/fundacional continuam pendentes. A formação contém 14 marcos mais M00; M01–M06 têm prática registrada, M07–M14 ainda não têm entrega correspondente. Isso não permite calcular um percentual de domínio da formação.

Seu registro/rollback foi aceito em E83: duas versões, três ativações, nove POST 200, duas falhas 500 injetadas e duas recusas 503 de processos desatualizados. A volta para v1/g3 preservou a probabilidade 0,2697810532292007. O número da geração avançou: restaurar um modelo antigo é uma nova ativação, não voltar o registro ao passado. Esses resultados mostram recuperação no exercício, sem medir estabilidade de produção.

A lacuna que vamos fechar agora é diferente: esse serviço ainda dependia da instalação de desenvolvimento. A escolha do interpretador gerou erros recorrentes no ambiente `base`; empacotar torna essas dependências explícitas e verificáveis.

## Aula: três identidades precisam viajar juntas

| Identidade | O que contém | Evidência nesta aula |
| --- | --- | --- |
| Modelo e política | Pesos aprendidos, ordem das 32 features, contratos de tempo e limiar | `artifacts/model.joblib`, `manifest.json`, `policy.json` e hashes |
| Código do serviço | Validação do pedido e chamada do estimador | wheel `renewcast_event_service-...whl` e hashes dos dois módulos |
| Ambiente | Interpretador e versões diretas/transitivas das bibliotecas | `requirements.lock`, identificação da plataforma e `environment.json` |

Um hash de modelo igual não resolve uma biblioteca incompatível. Uma resposta HTTP 200 não prova que o pacote veio da instalação correta. Por isso o protocolo confere as três identidades e o caminho efetivo do módulo importado.

**Wheel:** arquivo `.whl` instalável que contém o pacote e seus metadados. O nome da distribuição é `renewcast-event-service`; o namespace importado continua `renewable_forecast`. São conceitos distintos. A distribuição deste exercício contém somente `decision_api.py`, `event_artifact.py` e um `__init__.py` mínimo. Não substitui o pacote completo no seu Conda.

**Dependência direta e transitiva:** o serviço usa scikit-learn diretamente; scikit-learn depende de SciPy. Capturar somente as bibliotecas que você lembra de ter importado pode deixar a instalação incompleta. `capture_dependencies()` percorre `Requires-Dist`, avalia marcadores da plataforma atual e fixa as versões já instaladas. O runtime primeiro verifica a compatibilidade com as versões registradas no treino.

**Lock e wheelhouse:** o lock fixa nomes, versões e hashes; `wheelhouse/` contém os bytes que serão instalados. A reprodução usa `--no-index --require-hashes`. Não haverá escolha automática de uma versão mais recente. Um hash confere consistência com uma referência confiável; sozinho não autentica o autor se arquivo e referência forem adulterados juntos.

**Ambiente novo:** `venv` é criado sem `--system-site-packages`. O controlador chama seu Python pelo caminho completo e usa `-I`, que evita herdar `PYTHONPATH` e a importação pelo diretório de trabalho. Isso permite demonstrar que a API veio de `site-packages` do ambiente novo. Não é necessário ativar esse venv.

**Reprodução não é novo backtest:** igualdade da resposta de um pedido verifica compatibilidade daquele caso. Não reestima MAE, Brier ou calibração. Também não prova igualdade de todas as previsões possíveis, transporte para outro sistema operacional, capacidade de carga ou build binário idêntico entre compilações.

## 1. Executar a entrega técnica

Salve `renewcast_m06_empacotamento_20261009.zip` em `C:\renewable-forecast-lab`. Extraia na raiz; o pacote adiciona três arquivos em `scripts/` e a documentação. Não substitui o código atual da API, modelos ou `pyproject.toml` do projeto.

No PowerShell:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m06_empacotamento_20261009.zip -DestinationPath . -Force
.\scripts\run_m06_empacotamento.ps1
```

O script interrompe a sequência se o ambiente, a captura ou a reprodução falhar. O download pode levar alguns minutos. A API de verificação usa uma porta livre, é iniciada pelo controlador e encerrada ao final; não é necessário manter a API anterior aberta.

Internamente há duas ações, que também podem ser executadas separadamente:

```powershell
python scripts/empacotar_servico.py
python scripts/reproduzir_servico.py
```

Somente execute a segunda se a primeira terminou corretamente. A primeira lê o artefato existente em `models/CJU_BA5EIGT/h24_event_api_v1`; não chama `fit`. O `pyproject.toml` de distribuição é gerado em uma pasta temporária e uma cópia fica no release. Não há alteração do ambiente Conda atual.

| Saída | Local exato relativo à raiz |
| --- | --- |
| Ponteiro para a captura concluída | `dist/event_service/latest_release.json` |
| Distribuição, lock e wheels | `dist/event_service/<release_id>/` |
| Ambientes descartáveis de reprodução | `venvs/m06_package/<id>/` |
| Ponteiro para a reprodução aprovada | `reports/packaging/CJU_BA5EIGT/h24_event_v1/latest_run.json` |
| Recibo, importações, resposta e logs | `reports/packaging/CJU_BA5EIGT/h24_event_v1/<run_id>/` |

O sucesso exige: módulo importado do novo ambiente, versões capturadas iguais às instaladas, código/modelo/política preservados, HTTP 200 para o pedido válido, diferença de probabilidade até `1e-12` e HTTP 422 para feature ausente. O programa só grava `verification.json` aprovado depois dessas verificações. Não compare sua probabilidade com a da réplica do professor: a referência correta é o seu próprio artefato.

Para abrir a pasta da execução concluída:

```powershell
$r = Get-Content .\reports\packaging\CJU_BA5EIGT\h24_event_v1\latest_run.json -Raw | ConvertFrom-Json
Invoke-Item $r.directory
```

## 2. Transferência: executar fora da árvore original

Esta é a aplicação central da aula. Transporte o **release**, não a pasta `venv`. Um venv pode conter referências absolutas e deve ser recriado no destino. Abaixo, o destino será uma pasta nova em `%TEMP%`; a origem não é modificada.

Execute na raiz, com `renewable-forecast` ativo:

```powershell
$ErrorActionPreference = "Stop"
$python = (Get-Command python).Source
$p = Get-Content .\dist\event_service\latest_release.json -Raw | ConvertFrom-Json
$source = Join-Path (Resolve-Path .\dist\event_service).Path $p.directory
$delivery = Join-Path $env:TEMP ("renewcast_entrega_" + [guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Path $delivery | Out-Null
Copy-Item -LiteralPath $source -Destination (Join-Path $delivery "release") -Recurse
Copy-Item -LiteralPath .\scripts\reproduzir_servico.py -Destination $delivery
Push-Location $delivery
try {
    & $python .\reproduzir_servico.py --release .\release --output-root .\evidencias --venv-root .\venvs
    if ($LASTEXITCODE -ne 0) { throw "Reproducao no destino falhou; leia o erro." }
} finally {
    Pop-Location
}
Write-Host "Entrega transportada: $delivery"
```

O controlador precisa do interpretador existente para criar o novo ambiente; as bibliotecas do Conda não são usadas pela API reproduzida. O caminho `module_path` deverá estar na pasta de destino. O lock é específico para o sistema, arquitetura e versão exata de Python capturados. Não copie wheels Windows para Linux esperando compatibilidade.

## 3. Sua autoria: orçamento da distribuição e decisão de entrega

Crie **`notebooks/orcamento_distribuicao.py`**, usando apenas a biblioteca padrão. Esta parte fica com você. O programa deve:

1. Ler `dist/event_service/latest_release.json` e localizar o release indicado, sem procurar outro experimento.
2. Percorrer `wheelhouse/*.whl` e produzir uma linha por arquivo com `arquivo`, `bytes` e `participacao_pct` no tamanho total dos wheels.
3. Ordenar por tamanho decrescente, mostrar os cinco maiores e salvar `orcamento_distribuicao.csv` **na pasta da reprodução**, cujo caminho está em `reports/packaging/CJU_BA5EIGT/h24_event_v1/latest_run.json`.
4. Informar o total em MiB (`bytes / 1024**2`) e o percentual acumulado dos cinco maiores. Grave o CSV completo, não apenas os cinco mostrados.

Ferramentas disponíveis: `json.loads`, `Path`, `Path.glob`, `Path.stat().st_size`, `sorted` e `csv.DictWriter`. Pense no denominador: a participação é no total dos wheels, não no tamanho do modelo ou de toda a pasta. Não é necessário instalar pandas no pacote só para esse relatório.

Depois escreva **`parecer_distribuicao.md` na mesma pasta da reprodução**, com no máximo 20 linhas:

- Declare se a entrega é reproduzível **no escopo que você efetivamente executou** e cite `module_path`, hash do modelo e diferença de probabilidade.
- Identifique os dois maiores wheels e explique se podem ser removidos. Use `METADATA/Requires-Dist` dentro do wheel ou `release.json` para sustentar a relação de dependências. Tamanho grande, sozinho, não é justificativa para remoção.
- Decida o que fazer se o destino tiver outro Python, mesmo que o hash do modelo seja igual. Não altere o manifesto apenas para passar na validação.
- Separe a conclusão “instala e reproduz” da conclusão “pode operar com o risco aceito”. Cite uma evidência que ainda falta para a segunda.

Aqui a competência avaliada é controlar o custo de distribuição sem quebrar o contrato, e limitar uma aprovação ao que foi demonstrado. Você entrega código próprio, cálculo verificável e decisão técnica. A entrega não se encerra em copiar o comando.

## Fixação lexical: termo → arquivo → explicação sua

| Termo | Âncora concreta | O que explicar de memória depois da prática |
| --- | --- | --- |
| Wheel | arquivo `.whl` | Como difere do código editável em `src/` |
| Dependência transitiva | relação scikit-learn → SciPy | Por que retirar um pacote não importado diretamente pode quebrar o serviço |
| Lock | `requirements.lock` | O que versão e hash fixam, e o que não fixam |
| Wheelhouse | pasta de wheels | Por que permite instalação sem consulta ao índice |
| Isolamento | `environment.json` e `module_path` | Que evidência mostra de onde o código foi importado |
| Reprodutibilidade | referência versus `response.json` | Qual experimento foi reproduzido e qual conclusão continua fora do escopo |

Ao terminar, feche esta tabela e use os seis termos no seu parecer, ligados aos arquivos reais. Na próxima retomada, explique novamente sem consultar; a revisão avaliará seu raciocínio e as evidências, não a repetição literal das definições.

## Critério de conclusão e sequência

Esta unidade termina quando recebermos: recibo e ambiente da reprodução; reprodução no destino; seu script de orçamento, CSV e parecer. A execução do professor demonstra que o material funciona na réplica; a sua entrega demonstra a execução Windows; a autoria demonstra entendimento aplicado. Esses estados serão registrados separadamente em E84 e na evidência seguinte.

A unidade seguinte é **imagem Docker e uma rotina de integração contínua que reconstrói/verifica a distribuição**, reaproveitando o contrato desta aula. Executável Windows, operação contínua e comparação neural continuam entregas distintas. Não será necessário repetir registry/rollback ou rodar todo o backtest para fechar este empacotamento.

## Verificação do material pelo professor

O pacote foi executado com Python 3.12.14 em Linux, usando a réplica existente do serviço e seu próprio modelo. Foram capturadas 24 dependências, além do wheel do serviço; houve instalação offline, importação por `site-packages`, inferência HTTP e rejeição de pedido incompleto. A resposta reproduziu exatamente a probabilidade da referência da réplica. Detalhes e limites em `docs/Verificacao_E84_Professor.json`.

Windows/PowerShell e transporte para outro computador não foram executados pelo professor. A distribuição criada em sua máquina captura suas versões; não contém o modelo da réplica. Os comandos do PowerShell são fornecidos para sua execução e registrados como pendentes, não como já aprovados.

## Referências primárias

- [Python 3.12 — venv](https://docs.python.org/3.12/library/venv.html): isolamento, caminho do interpretador e necessidade de recriar ambientes no destino.
- [Python Packaging — pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/): dependências, metadados e backend de construção.
- [pip — download](https://pip.pypa.io/en/stable/cli/pip_download/): coleta de distribuições para instalação posterior.
- [pip — instalações com hashes](https://pip.pypa.io/en/stable/topics/secure-installs/): versões fixadas e verificação dos arquivos.
- [scikit-learn — persistência](https://scikit-learn.org/stable/model_persistence.html): restrições de compatibilidade do ambiente ao carregar modelos persistidos.
