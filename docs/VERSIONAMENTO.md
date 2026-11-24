# O que versionar e o que deixar no ambiente local

Revisão de 24/11/2026. Esta política cobre o Renewcast e o
`satellite-anomaly-monitor`, mantidos no mesmo repositório. As regras estão
no [`.gitignore`](../.gitignore).

O Git deve guardar o que explica, implementa e permite conferir o trabalho.
Dependências instaladas, caches, pesos e pacotes gerados ficam no ambiente
local ou em armazenamento de artefatos. Dados pequenos de referência e
evidências selecionadas permanecem disponíveis para reprodução.

## Mapa de decisão

| Caminho ou tipo | Decisão nesta revisão | Motivo |
|---|---|---|
| `src/`, `scripts/`, `tests/`, `tools/` | **Versionar** | Implementação, automação, testes e clientes são fontes do projeto. |
| `notebooks/*.py` e notebooks `.ipynb` | **Versionar** | São os laboratórios e funções implementadas. Apenas checkpoints do editor e cópias locais com `_antes_` são ignorados. |
| `README.md`, `docs/`, pareceres e respostas | **Versionar** | Documentam método, decisões, limitações e resultados. |
| `config/`, `deploy/`, `infra/`, `ci_examples/` e workflows | **Versionar** | Definem contratos, configuração e receitas de execução. |
| `pyproject.toml`, arquivos de requisitos e locks | **Versionar** | Registram dependências e configurações de ambiente. |
| `.env.example`, `.env.sample`, `.env.template` | **Versionar quando sanitizados** | Exemplificam nomes de variáveis sem valores privados. Não existem atualmente na raiz, mas as exceções já estão previstas. |
| `data/reference/` | **Versionar** | Cadastros, pesos de grade e metadados usados no P1. |
| `dist/databricks/CJU_BA5EIGT/m07_3/` | **Versionar** | Dois Parquet e um manifesto, cerca de 0,50 MiB, são entradas efetivas dos laboratórios M08/M09. |
| `satellite-anomaly-monitor/data/reference/` | **Versionar** | Recortes compactos ESA, anotações, proveniência e hashes usados em M10.1–M10.3; cerca de 7,58 MiB. |
| `data/raw/DicionarioDados_GeracaoPorUsina.json` | **Versionar** | É um dicionário de dados, não uma cópia das medições brutas. |
| `data/external/weather/` | **Manter a seleção atual visível** | Já possui 505 arquivos rastreados e participa da rastreabilidade meteorológica. Uma mudança para armazenamento externo deve preservar metadados e aquisição. |
| `reports/**/resultado.json`, protocolos, políticas, resumos CSV, HTML e pareceres | **Versionar a seleção conferida** | São evidências dos experimentos; não se ignora a pasta `reports/` inteira. |
| `reports/**/quantis_26_passos.npz` e escores `*.csv.gz` do P2 | **Versionar a seleção conferida** | Permitem recalcular quantis, rankings, alarmes e métricas sem repetir o treinamento. |
| Contratos de container em `dist/`: Dockerfile, `context.json`, `base_image.lock.json`, receitas e políticas JSON | **Manter visíveis** | O exemplo de CI exige um contexto revisado. `dist/` contém mais do que binários. |
| `.venv/`, `.venvs/`, `venv/`, `venvs/`, caches e bytecode | **Ignorar** | São dependências instaladas ou produtos locais do Python. |
| `.env`, `.env.*`, `secrets/`, credenciais locais | **Ignorar** | Configuração privada não faz parte da distribuição do projeto; exemplos sanitizados são exceções. |
| `build/`, wheelhouses, executáveis, DLLs e wheels em `dist/` | **Ignorar** | São produtos de build e dependências distribuídas, regeneráveis pelas receitas. |
| `dist/event_service/**/source/` | **Ignorar** | É uma exportação de código para empacotamento; as fontes canônicas ficam em `src/`. |
| `data/raw/` com medições, `data/interim/`, `data/processed/` | **Ignorar**, preservando exceções documentadas | São aquisição e transformações locais. O dicionário, README, `.gitkeep` e metadados `*.metadata.json` na raiz de `data/raw/` têm exceções. |
| `data/external/runtime/` | **Ignorar** | Contém dependências de runtime baixadas, como os JARs do Delta. |
| `models/`, checkpoints e pesos em `reports/` | **Ignorar** | Modelos binários devem ser identificados por versão/hash e distribuídos como artefatos. `models/README.md` e `.gitkeep` continuam permitidos. |
| MLflow local: `mlruns/`, `mlartifacts/`, bancos `mlflow*.db` previstos nas regras | **Ignorar** | São estado e artefatos locais do acompanhamento de experimentos. |
| Parquet e logs gerados dentro de `reports/`; `reports/setup/` | **Ignorar** | São saídas locais ou de instalação. Logs selecionados em `docs/` continuam visíveis. |
| ZIPs e 7z na raiz, ZIPs na raiz do P2 | **Ignorar** | São pacotes recebidos ou de entrega. Seus códigos, documentos e recibos úteis ficam extraídos e selecionados. |
| `backups/`, cópias `_antes_` em `notebooks/` e `tools/` | **Ignorar** | São cópias locais de trabalho; revisões e evidências selecionadas em `docs/` são preservadas. |

“Versionar” não significa adicionar toda execução produzida indefinidamente.
Selecione os resultados que sustentam as tabelas e decisões do README e
mantenha seus manifestos, parâmetros e origem. Resultados adicionais podem
ser armazenados como artefatos de uma release, com seus hashes.

## Regras que não devem ser usadas de forma global aqui

Evite `data/`, `dist/`, `reports/`, `*.csv`, `*.json`, `*.gz`, `*.parquet`,
`*.npz` e `*.lock` como exclusões gerais. Elas esconderiam entradas,
configurações, estados de políticas e evidências necessários. As exclusões
de Parquet e pesos do `.gitignore` são limitadas às pastas de saídas;
os Parquet de referência em `dist/databricks` continuam visíveis.

Exceções com `!` precisam respeitar os diretórios ancestrais: um arquivo
dentro de uma pasta excluída não pode ser recuperado apenas por uma regra
para o arquivo. Essa precedência é definida na
[documentação do Git](https://git-scm.com/docs/gitignore).

## O que foi encontrado no índice

Antes da revisão, havia **14.607 caminhos rastreados**. O inventário por
prefixo mostrou:

| Prefixo | Caminhos rastreados | MiB lógicos no índice |
|---|---:|---:|
| `venvs/` | 6.815 | 134,98 |
| `build/` | 6.602 | 69,35 |
| `dist/` | 216 | 131,21 |
| `data/` | 516 | 35,25 |
| `reports/` | 239 | 4,19 |
| `docs/` | 98 | 1,56 |

Ambientes e build representam **91,85% dos caminhos**. Os 378,39 MiB
lógicos de todos os caminhos incluem blobs repetidos; os blobs únicos
presentes no índice somam cerca de 290,17 MiB. Esses números não medem
o tamanho de toda a história do Git.

Após a atualização, **13.638 caminhos já rastreados correspondem a regras
de ignore**: 6.815 em `venvs`, 6.602 em `build`, 180 em `dist`, 28 em
`reports` e 13 entre backups, cópias e ZIPs. Eles **continuam rastreados**.
O `.gitignore` só atua sobre arquivos não rastreados; não limpa o índice
nem a história. Essa distinção consta da
[documentação oficial](https://git-scm.com/docs/gitignore).

Esta revisão alterou regras e documentação. Não removeu arquivos locais,
não executou `git rm --cached`, não criou commit e não reescreveu histórico.

## Conferir antes de preparar um commit

```powershell
# Explica qual regra atinge um caminho, inclusive se ele já for rastreado
git check-ignore --no-index -v -- venvs/exemplo/Scripts/python.exe
git check-ignore --no-index -v -- dist/databricks/CJU_BA5EIGT/m07_3/geracao.parquet

# Lista arquivos já rastreados que correspondem às regras novas
git ls-files -ci --exclude-standard

# Mostra alterações e novos arquivos sem listar os milhares de arquivos internos
git status --short --untracked-files=normal
git diff -- .gitignore README.md
```

Para caminhos sem regra correspondente, `git check-ignore` não imprime
saída e retorna 1. O `--no-index` permite conferir a regra mesmo para
arquivos já rastreados; veja a
[referência do comando](https://git-scm.com/docs/git-check-ignore).

A retirada de arquivos do índice é uma etapa separada. Depois de revisar
a lista e decidir os diretórios, `git rm -r --cached -- venvs build`
prepararia sua remoção do próximo commit, mantendo as cópias locais.
Esse comando **não foi executado** nesta revisão e não elimina cópias
dos commits antigos. Não é necessário remover e adicionar o repositório
inteiro para aplicar a política.

## Validação desta revisão

Foram conferidos **100 caminhos** com `git check-ignore --no-index`,
incluindo todos os arquivos de referência atuais do P1/P2 e do recorte
Databricks, exemplos de configuração, código, recibos e artefatos locais.
Nenhuma divergência foi encontrada. O registro está em
[`Verificacao_Gitignore_20261124.json`](Verificacao_Gitignore_20261124.json).

Antes de adicionar novos recortes, formatos ou diretórios, confira se são
fonte, entrada curada ou saída gerada e teste a regra correspondente.
Novos metadados em `data/raw/` que não correspondam às exceções atuais
precisam de uma exceção específica ou de uma localização em referências.
