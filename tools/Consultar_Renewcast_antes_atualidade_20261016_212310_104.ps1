<#
Lançador Renewcast 1.1. Use ao lado de renewcast.exe e contract.json.
A regra temporal é executada no cliente Python empacotado.
0: decisão disponível no modo escolhido; 2/3/4/5: erros do cliente;
6: falha do lançador; 7: apresentação bloqueada pela regra temporal.
#>
[CmdletBinding()]
param (
    [Parameter(Mandatory = $true)]
    [string]$Request,

    [Parameter(Mandatory = $true)]
    [ValidateSet("historical_replay", "operational")]
    [string]$Mode,

    [string]$Url = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"
# No PowerShell 7, um código nativo não zero deve chegar ao tratamento abaixo.
# No 5.1 esta variável local não muda o comportamento dos comandos nativos.
$PSNativeCommandUseErrorActionPreference = $false
$clientExit = $null
$outputPath = $null

try {
    $exePath = Join-Path -Path $PSScriptRoot -ChildPath "renewcast.exe"
    $contractPath = Join-Path -Path $PSScriptRoot -ChildPath "contract.json"
    foreach ($path in @($exePath, $contractPath, $Request)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Arquivo não encontrado: $path"
        }
    }
    $requestPath = (Resolve-Path -LiteralPath $Request).Path
    $consultasDir = Join-Path -Path $PSScriptRoot -ChildPath "consultas"
    [System.IO.Directory]::CreateDirectory($consultasDir) | Out-Null
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
    $uniqueId = [guid]::NewGuid().ToString("N")
    $outputPath = Join-Path -Path $consultasDir -ChildPath "recibo_${timestamp}_${uniqueId}.json"

    & $exePath --url $Url --request $requestPath --contract $contractPath --output $outputPath --presentation-mode $Mode | Out-Null
    $clientExit = $LASTEXITCODE

    if (-not (Test-Path -LiteralPath $outputPath -PathType Leaf)) {
        throw "Cliente terminou com código $clientExit sem produzir recibo."
    }
    $recibo = Get-Content -Raw -LiteralPath $outputPath -Encoding UTF8 | ConvertFrom-Json
    if ($recibo.schema -ne "renewcast-client-receipt-v2" -or
        $recibo.exit_code -ne $clientExit -or
        $recibo.requested_presentation_mode -ne $Mode) {
        throw "Recibo incompatível com esta execução."
    }

    if ($clientExit -eq 0) {
        if ($recibo.state -notin @("alarm", "no_alarm") -or
            $null -eq $recibo.response -or
            $recibo.presentation.allowed -ne $true -or
            $recibo.presentation.mode -ne $Mode) {
            throw "Recibo incompatível com apresentação permitida."
        }
        if ($Mode -eq "historical_replay") {
            Write-Host "REPRODUÇÃO HISTÓRICA - NÃO É PREVISÃO ATUAL" -ForegroundColor Yellow
        } else {
            Write-Host "ATUALIDADE APROVADA - MODELO EM DESENVOLVIMENTO" -ForegroundColor Yellow
        }
        $resp = $recibo.response
        Write-Host "Origem:        $($resp.forecast_origin)"
        Write-Host "Alvo:          $($resp.target_time)"
        Write-Host "Probabilidade: $($resp.p_event)"
        Write-Host "Limiar:        $($resp.threshold)"
        Write-Host "Alarme:        $($resp.alarm)"
    } else {
        if ($null -ne $recibo.response) {
            throw "Cliente devolveu uma resposta apresentável junto com código de falha."
        }
        Write-Host "CONSULTA SEM DECISÃO APRESENTÁVEL (código $clientExit)" -ForegroundColor Yellow
        Write-Host "Estado:  $($recibo.state)"
        Write-Host "Detalhe: $($recibo.detail)"
        if ($null -ne $recibo.presentation) {
            Write-Host "Regra temporal: $($recibo.presentation.state)"
        }
    }
    Write-Host "Recibo: $outputPath"
} catch {
    Write-Host "Falha do lançador: $($_.Exception.Message)" -ForegroundColor Red
    if ($null -ne $outputPath) {
        Write-Host "Caminho previsto do recibo: $outputPath"
    }
    exit 6
}
exit $clientExit
