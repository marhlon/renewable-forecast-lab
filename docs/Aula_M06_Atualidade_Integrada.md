# M06.5 — da regra autoral ao cliente distribuível

Marlon Alves Bomfim · 14/10/2026 · E91–E93 · cliente 1.1.0

## Resultado da revisão

Sua função `avaliar_atualidade` cumpre o contrato dos horários UTC apresentados:
valida fuso, modo, duração e relação origem/alvo; preserva a prioridade das regras;
aceita idade exatamente igual ao limite; bloqueia alvo igual a agora.
O relógio é um argumento, portanto o resultado é reproduzível.

A implementação foi promovida para `tools/politica_atualidade.py` sem mudar a ordem
das decisões. Foram adicionadas verificações explícitas de tipos e conversão para
UTC antes da aritmética. Isso trata um detalhe real do Python: dois datetimes com
o mesmo objeto `tzinfo` podem ser subtraídos pelo relógio de parede, ignorando uma
mudança de offset. A normalização permite medir tempo decorrido entre instantes.
Fonte: https://docs.python.org/3.12/library/datetime.html#datetime-objects

Seu notebook é preservado como autoria. O cliente usa o módulo em `tools/` para
distribuir a regra junto com o executável, sem depender de notebooks ou pandas.

## O que a integração faz

1. Lê pedido, contrato e modo de apresentação explícito.
2. Consulta a API e confere HTTP, identidade, campos e alarme.
3. Se essa etapa falhar, preserva a falha original: não tenta interpretar a data.
4. Se a resposta for válida, lê o relógio UTC real depois da resposta HTTP.
5. Aplica sua regra antes de disponibilizar a previsão para apresentação.
6. Grava um recibo novo, com versão, contexto, horário da avaliação e resultado.

O argumento `now` continua injetável na função. A CLI não oferece `--now`: uma
consulta operacional não deve ser liberada fingindo que hoje ainda é agosto.
Também não alteramos as datas do pedido histórico para fazê-lo parecer atual;
isso não produziria features atuais nem meteorologia disponível no instante novo.

## Três resultados diferentes

| Situação | HTTP | Saída do processo | Estado externo | `response` | `audit_response` |
| --- | --- | --- | --- | --- | --- |
| Pedido válido em reprodução histórica | 200 | 0 | `alarm` ou `no_alarm` | Resposta validada | null |
| Mesmo pedido antigo em contexto operacional | 200 | 7 | `presentation_blocked` | null | Resposta validada, somente para auditoria |
| API desligada | ausente | 3 | `unavailable` | null | null |

No segundo caso, `presentation.state` explica a causa, por exemplo `target_elapsed`.
O bloqueio pode coexistir com HTTP 200: o transporte funcionou, mas a regra temporal
não permite apresentar o resultado como atual. O console e o lançador não exibem
a probabilidade bloqueada; o arquivo conserva a resposta para investigação.

No primeiro caso, o lançador anuncia **REPRODUÇÃO HISTÓRICA — NÃO É PREVISÃO ATUAL**.
Ele exige `-Mode historical_replay` ou `-Mode operational`. O novo executável exige
o equivalente `--presentation-mode`. Uma chamada antiga sem modo recebe erro de
argumento; isso é uma mudança intencional da interface, documentada na versão 1.1.

O recibo passa a `renewcast-client-receipt-v2`. O contrato com a API permanece v1.
`response.mode` continua `development_inference`: mudar o modo de apresentação não
promove o estimador para produção. `operational_policy_approved` permanece false.
Este controle é do cliente; não é uma autorização de operação nem uma proteção
contra alguém que chame a API diretamente.

## Quatro relógios que não devem ser confundidos

| Grandeza | Cálculo neste projeto | Pergunta respondida |
| --- | --- | --- |
| Horizonte | alvo − origem | Quanto à frente foi previsto? |
| Idade de apresentação | agora − origem | Há quanto tempo esta previsão foi emitida? |
| Atraso assumido da geração | disponibilidade − instante observado | Quando o dado poderia ser usado? |
| Idade da rodada meteorológica | origem − instante da rodada | Quão antiga é a rodada selecionada? |

As duas horas de idade máxima são uma regra didática, não um SLA validado.
Coincidem numericamente com o atraso assumido de geração; são conceitos distintos.
Uma previsão dentro do limite temporal ainda pode ter meteorologia inadequada,
dados incorretos, modelo desatualizado ou probabilidade mal calibrada.

## Aplicação no seu projeto

Baixe `renewcast_m06_atualidade_20261014.zip` para `C:\renewable-forecast-lab`.
Abra Docker Desktop com o mecanismo Linux. No PowerShell:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast

$backup = '.\tools\Consultar_Renewcast_antes_atualidade_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.ps1'
Copy-Item -LiteralPath .\tools\Consultar_Renewcast.ps1 -Destination $backup -ErrorAction Stop
Expand-Archive -LiteralPath .\renewcast_m06_atualidade_20261014.zip -DestinationPath . -Force

python scripts/criar_cliente_windows.py --container-run reports/containers/CJU_BA5EIGT/h24_event_v1/20261013T185650Z_ffc01dd8
if ($LASTEXITCODE -eq 0) {
    python scripts/verificar_cliente_windows.py
} else {
    Write-Error 'A construção falhou; não executar a verificação. Leia o build.log indicado.'
}
```

O build agora inclui a regra temporal e o lançador UTF-8 com BOM. É necessário
reempacotar porque editar um `.py` não altera o código já embutido em um `.exe`.
São criados novos diretórios de release/verificação; a release 1.0 e seus recibos
continuam preservados. O notebook autoral não está dentro do ZIP.

O controlador inicia sua própria instância temporária da imagem Docker já aceita,
usa uma porta local livre e encerra essa instância ao terminar. Não precisa abrir
manualmente a API em outro terminal. Modelo, política de decisão e imagem não são
retreinados ou reconstruídos. O cliente roda copiado para fora do projeto.

Saída esperada (o diretório recebe um identificador novo):

```text
Cliente 1.1: replay 200/exit0; mesmo pedido operacional 200/exit7 (target_elapsed).
Regressao: 422/exit2; identidade divergente/exit4; API encerrada/exit3.
Diferenca de probabilidade: 0
```

Tolerância da conferência numérica preservada: absoluta de 1e-12.
Arquivos: `reports/windows_client/CJU_BA5EIGT/h24_event_v1/<nova_execucao>/`.
`valid.json` mostra a reprodução; `blocked.json` mostra o bloqueio; `verification.json`
liga os resultados à release e à imagem. Não acrescente esses arquivos a uma pasta
de execução antiga.

## Uso manual posterior

Com uma API local ativa e estando na pasta completa do novo cliente:

```powershell
.\Consultar_Renewcast.ps1 -Request .\example_request.json -Mode historical_replay
.\Consultar_Renewcast.ps1 -Request .\example_request.json -Mode operational
```

O segundo comando deve bloquear o pedido antigo. A pasta contém `renewcast.exe`,
`_internal`, `contract.json`, `example_request.json` e o lançador; copie-a inteira.

## Evidência e fechamento

E91 aceita a reprodução Windows e o lançador 1.0 com base nos logs e recibos
colados pelo aluno. Isso não equivale a revalidar todos os arquivos locais por hash.
E92 aceita a autoria da regra no contrato proposto. E93 entrega sua integração.

Aqui o cliente Python 1.1 foi executado contra a réplica HGB nativa existente,
com treino proibido, e passou nos cinco cenários HTTP. Também foram conferidas
fronteiras de tempo, offsets e precedência de falhas. O professor não executou
PyInstaller Windows, PowerShell ou Docker nesta etapa. O JSON de verificação
anexo explicita esses limites e a identidade diferente do modelo da réplica.

**Sua entrega agora:** a saída do controlador e o novo `verification.json`.
Com isso conferido, encerramos esta evolução do cliente e avançamos a M07.1:
uma transformação real do Renewcast em PySpark/DataFrame e Spark SQL, comparada
com DuckDB. Estudaremos plano de execução, avaliação lazy e shuffle. As pendências
de operação ao vivo/CI ficam registradas; não viram novas condições para permanecer
indefinidamente em M06.

**Fixação léxica aplicada:** transporte → HTTP 200; contrato → identidade e campos;
domínio → `target_elapsed`; auditoria → resposta preservada; apresentação → nenhuma
probabilidade utilizável quando bloqueada. `no_alarm` é decisão; `unavailable` e
`presentation_blocked` são ausência de decisão apresentável por motivos diferentes.
