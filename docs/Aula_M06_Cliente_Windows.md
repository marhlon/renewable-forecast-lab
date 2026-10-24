# M06.5 — um cliente Windows que pode sair da pasta do projeto

**Entrega concreta:** `renewcast.exe`, numa pasta com suas dependências, capaz de enviar um pedido JSON à API aprovada e registrar a decisão. No destino, o cliente não exige ativar Conda nem instalar Python. A API continua sendo um serviço separado. O exemplo é histórico e mantém `development_inference`.

Esta unidade abre o item 9 do P1. A lógica autoral de concorrência foi aceita em E89; não se repete a medição nem se escolhe uma nova configuração de servidor.

## 1. A decisão de arquitetura

O serviço contém estimador, bibliotecas científicas e política. O cliente contém interface de linha de comando, HTTP, validação da resposta e gravação de recibo. Assim, substituir o modelo no servidor é uma operação diferente de distribuir a interface Windows.

| Camada | O que ela precisa | O que comprova a execução |
| --- | --- | --- |
| Construção do cliente | Python 3.12 x64 e PyInstaller em Windows | Executável e dependências produzidos |
| Cliente distribuído | Windows compatível; pasta completa | Pode executar sem Conda/Python externo |
| API | Imagem Docker e artefatos já aprovados | Executa o estimador e aplica a política |
| Entrada | Pedido JSON com 32 features e relógios | Define o caso a consultar; não fornece o alvo observado |

O executável não incorpora o estimador nem baixa novos ventos. “Portátil sem Conda” descreve o processo cliente; “funciona sem serviço” seria outra arquitetura, que este projeto ainda não entregou. Aqui existe uma dependência de rede local e da API ativa.

O PyInstaller inclui o interpretador e os módulos usados. A construção Windows precisa ocorrer no Windows. Usaremos `--onedir`: é preciso transportar a pasta inteira, inclusive `_internal`. `--onefile` extrairia componentes a uma pasta temporária no início de cada execução; essa simplificação de distribuição tem custo de inicialização. Escolheremos primeiro a forma mais fácil de inspecionar. O sucesso do build não demonstra funcionamento do executável.

## 2. Arquivos e fluxo

O pacote acrescenta arquivos novos:

| Arquivo | Responsabilidade |
| --- | --- |
| `tools/renewcast_client.py` | Cliente de biblioteca padrão; usa caminhos explícitos e nunca procura outro experimento |
| `scripts/criar_cliente_windows.py` | Confere E87, cria venv de build, captura wheels do empacotador e produz o programa |
| `scripts/verificar_cliente_windows.py` | Copia a pasta para fora do projeto e executa os quatro cenários descritos abaixo |
| `docs/Revisao_E89_Concorrencia.md` | Aceite e análise da sua autoria anterior |

São reutilizados `scripts/medir_concorrencia.py` e `scripts/verificar_container.py`, já entregues e executados. Esses controladores não entram no executável. Não se alteram modelo, política, benchmark ou seu `notebooks/analise_concorrencia.py`.

O build cria um ambiente exclusivo em `build/client_windows/<id>/venv`. Baixa PyInstaller 6.22.3 e suas dependências de construção, instala esses wheels localmente e registra versões, hashes e log. O ambiente de modelagem permanece com suas próprias dependências. Primeira execução requer acesso ao índice de pacotes; não há custo de cloud.

A saída é `dist/client_windows/<id>/renewcast/renewcast.exe`. O recibo guarda as identidades do serviço e os hashes dos arquivos produzidos. Isso documenta esta construção; não promete gerar bytes idênticos em qualquer reconstrução futura.

## 3. Execução no PowerShell, na raiz

Salve `renewcast_m06_cliente_windows_20261014.zip` em `C:\renewable-forecast-lab` e use:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m06_cliente_windows_20261014.zip -DestinationPath . -Force
python scripts/criar_cliente_windows.py --container-run reports/containers/CJU_BA5EIGT/h24_event_v1/20261013T185650Z_ffc01dd8
```

Depois de “Cliente criado”, execute:

```powershell
python scripts/verificar_cliente_windows.py
```

O primeiro comando compila em Windows. O segundo usa a imagem local aprovada, publica uma porta aleatória em `127.0.0.1`, faz as consultas e encerra somente o contêiner que criou. Não é preciso abrir a API manualmente para essa verificação. Docker Desktop deve estar aberto no mecanismo Linux.

O processo filho do `.exe` recebe PATH limitado às pastas do Windows, sem variáveis Conda/PYTHONPATH. A pasta do aplicativo é copiada para um diretório externo criado em TEMP. Recibos identificam `frozen=true`, caminho do próprio `.exe`, diretório de trabalho e estado do ambiente. Testar assim demonstra independência do ambiente ativo no mesmo computador; não substitui testar outro computador/versão de Windows.

## 4. O que uma falha significa para quem recebe a previsão

| Caso | HTTP | Exit code do cliente | Resultado utilizável |
| --- | --- | ---: | --- |
| Pedido válido, identidade e regra conferidas | 200 | 0 | `alarm` ou `no_alarm`, com resposta e rastreabilidade |
| Feature ausente | 422 | 2 | `rejected`; corrigir pedido |
| Modelo esperado diferente do servido | 200 | 4 | `invalid_response`; bloquear a interpretação |
| API encerrada | Sem resposta | 3 | `unavailable`; não existe decisão nova |
| JSON/contrato local inválido | Sem consulta válida | 5 | `invalid_input`; corrigir entrada local |

**Ponto central:** HTTP 200 é um resultado de transporte/aplicação, não prova suficiente de uma decisão válida. O cliente também compara identidades, relógios, regra `alarm == (p_event >= threshold)` e referência da queda. Uma resposta de outro modelo pode ser tecnicamente bem formada e ainda violar o contrato desta entrega.

O código 0 significa que houve uma decisão coerente com o contrato; ele não significa que a previsão acertará. Já o código 3 não equivale a `alarm=false`. O campo `response` fica nulo nos casos de falha. Cada consulta usa um arquivo novo; o cliente recusa sobrescrever um resultado anterior.

O verificador altera uma cópia do contrato para testar a divergência de identidade. Preserva o contrato original, o modelo, a política e os arquivos da distribuição. A probabilidade do pedido válido deve coincidir com a referência aprovada; divergência acima da tolerância ou de outro campo interrompe o aceite.

## 5. Sua demanda de programação: a entrada de uso por outra pessoa

Após a reprodução, escreva **`tools/Consultar_Renewcast.ps1`**. Sua função é permitir a consulta sem conhecer o ambiente de desenvolvimento. Depois copie esse arquivo para a pasta externa, ao lado de `renewcast.exe`. Não há implementação pronta desse lançador no pacote.

Contrato a implementar:

1. Receber `-Request` como caminho de um JSON e `-Url` com padrão `http://127.0.0.1:8000`.
2. Encontrar `renewcast.exe` e `contract.json` a partir de `$PSScriptRoot`, independentemente da pasta atual do terminal.
3. Criar um nome novo para o recibo em uma subpasta `consultas` junto ao lançador. Passar caminhos como argumentos, preservando espaços.
4. Executar o `.exe` com `&` e guardar imediatamente `$LASTEXITCODE`.
5. Somente com código 0, ler o recibo e apresentar origem, alvo, probabilidade, limiar e alarme. Para código diferente de 0, informar estado/falha e o caminho do recibo, se existir; não mostrar uma previsão antiga como nova.
6. Devolver o mesmo código ao processo chamador usando `exit`. O lançador não ativa Conda, instala bibliotecas, muda a política ou calcula uma probabilidade substituta.

Ferramentas novas aplicadas: parâmetros de script, `$PSScriptRoot`, `Join-Path`, operador `&`, `$LASTEXITCODE`, `Get-Content -Raw`, `ConvertFrom-Json` e propagação de código de saída. Sua prova é uma consulta válida e uma consulta após parar a API, executadas de uma pasta diferente da pasta do lançador.

Para inspecionar o destino que o verificador criou:

```powershell
$ponteiro = Get-Content -Raw .\reports\windows_client\CJU_BA5EIGT\h24_event_v1\latest_run.json | ConvertFrom-Json
$prova = Get-Content -Raw (Join-Path $ponteiro.directory 'verification.json') | ConvertFrom-Json
$cliente = Join-Path $prova.external_directory 'renewcast'
Invoke-Item $cliente
```

O verificador encerra sua API ao final. Para a sua demonstração manual, abra um terminal separado na raiz do projeto e execute:

```powershell
$recibo = Get-Content -Raw .\reports\containers\CJU_BA5EIGT\h24_event_v1\20261013T185650Z_ffc01dd8\verification.json | ConvertFrom-Json
docker run --rm --pull never --cpus 2 --memory 1g --read-only --tmpfs /tmp:rw,size=64m --cap-drop ALL --security-opt no-new-privileges -p 127.0.0.1:8000:8000 $recibo.image_id
```

Esse terminal permanece ocupado pela API. Se a porta já estiver ocupada, use outra porta explicitamente e passe-a em `-Url`; não encerre um serviço desconhecido. No terminal cliente, copie o lançador e execute-o de fora da pasta do aplicativo:

```powershell
Copy-Item .\tools\Consultar_Renewcast.ps1 (Join-Path $cliente 'Consultar_Renewcast.ps1')
Set-Location $env:TEMP
& (Join-Path $cliente 'Consultar_Renewcast.ps1') -Request (Join-Path $cliente 'example_request.json')
```

Pare a API com Ctrl+C no terminal dela e repita a consulta. Compare o código e o estado, sem reutilizar o recibo anterior. A função de negócio continua no servidor; o lançador lida com caminho, execução e comunicação de resultado.

## 6. Fixação lexical por recuperação e transferência

| Termo | Localize a evidência | Explique de memória |
| --- | --- | --- |
| Build | `build.log` e `release.json` | Por que compilar não comprova que o programa funciona? |
| Runtime | `frozen` e `executable` no recibo | Onde está o Python que o executável utiliza? |
| Diretório atual | `working_directory` | Por que ele não identifica a pasta do programa? |
| Cliente/serviço | `.exe` e imagem Docker | Qual processo calcula a probabilidade? |
| Contrato | `contract.json` | Por que um HTTP 200 pode ser recusado? |
| Exit code | `exit_code` e `$LASTEXITCODE` | Como diferenciar ausência de alarme e ausência de resposta? |

Depois de executar, feche a aula e explique os seis termos usando seus próprios arquivos. Na transferência, aplique a diferença entre “sem evento” e “sem resposta” a uma API de detecção de fraude: uma falha de consulta pode ser registrada como probabilidade zero? Justifique a consequência na decisão.

## 7. Evidência, aceite e andamento

Envie o log final de `verificar_cliente_windows.py`, `verification.json`, `valid.json`, `unavailable.json` e o código do seu lançador com as duas saídas. Os arquivos ficam em `reports/windows_client/CJU_BA5EIGT/h24_event_v1/<run_id>/`. Não é necessário enviar `_internal` ou o venv de build.

O aceite exige: execução do `.exe` copiado fora do projeto; ambiente filho sem Conda/PYTHONPATH; identidade e resposta preservadas; falhas diferenciadas; lançador funcionando de outra pasta. E90 entrega material, não declara esses resultados já obtidos pelo aluno. CI remoto, shadow ao vivo, MLflow Registry e a implantação cloud mantêm seus estados próprios. O roteiro continua com M00 e M01–M14; esta entrega não gera um percentual global de senioridade.

**Verificação do professor:** cliente Python executado contra a réplica HGB existente, com fit proibido. Conferidos resposta válida, 422, divergência de identidade, alarme inconsistente, indisponibilidade e preservação de saída anterior. A réplica tem outra identidade/probabilidade, explicitadas em `Verificacao_E90_Professor.json`. Docker, PowerShell e executável Windows não foram executados neste ambiente. O build Windows e o controlador de reprodução permanecem para a execução acima.

## Referências primárias

- [PyInstaller — funcionamento, plataforma e onedir/onefile](https://pyinstaller.org/en/stable/operating-mode.html)
- [PyInstaller — opções de construção](https://pyinstaller.org/en/stable/usage.html)
- [PyInstaller — frozen e sys.executable](https://pyinstaller.org/en/stable/runtime-information.html)
- [PowerShell — variáveis automáticas](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_automatic_variables)
- [PowerShell — operadores, incluindo &](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_operators)
