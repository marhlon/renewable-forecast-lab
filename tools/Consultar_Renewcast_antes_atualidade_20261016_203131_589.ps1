<#
.SYNOPSIS
    Lançador do cliente Windows Renewcast (tools/Consultar_Renewcast.ps1).
.DESCRIPTION
    Executa o cliente standalone `renewcast.exe` a partir do diretório onde o script está localizado,
    gerando um recibo novo na subpasta `consultas` e comunicando previsões ou falhas com fidelidade.
#>
[CmdletBinding()]
param (
    [Parameter(Mandatory = $true, HelpMessage = "Caminho para o arquivo de pedido JSON.")]
    [string]$Request,

    [Parameter(Mandatory = $false, HelpMessage = "URL base da API Renewcast.")]
    [string]$Url = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

# 1. Localizar executável e contrato a partir da pasta do próprio lançador ($PSScriptRoot)
$exePath = Join-Path -Path $PSScriptRoot -ChildPath "renewcast.exe"
$contractPath = Join-Path -Path $PSScriptRoot -ChildPath "contract.json"

if (-not (Test-Path -Path $exePath)) {
    Write-Error "Executável 'renewcast.exe' não foi encontrado em: $exePath"
    exit 5
}

if (-not (Test-Path -Path $contractPath)) {
    Write-Error "Arquivo de contrato 'contract.json' não foi encontrado em: $contractPath"
    exit 5
}

if (-not (Test-Path -Path $Request)) {
    Write-Error "Arquivo de pedido JSON não foi encontrado em: $Request"
    exit 5
}

# Resolve o caminho absoluto do pedido para evitar dependência do diretório atual
$requestPath = (Resolve-Path -LiteralPath $Request -ErrorAction Stop).Path

# 2. Criar subpasta 'consultas' junto ao lançador
$consultasDir = Join-Path -Path $PSScriptRoot -ChildPath "consultas"
if (-not (Test-Path -Path $consultasDir)) {
    New-Item -ItemType Directory -Path $consultasDir -Force | Out-Null
}

# 3. Gerar um nome único e novo para o recibo
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
$uniqueId = [guid]::NewGuid().ToString("N")
$outputPath = Join-Path -Path $consultasDir -ChildPath "recibo_${timestamp}_${uniqueId}.json"

# 4. Executar o .exe com o operador '&' e capturar imediatamente $LASTEXITCODE
& $exePath --url $Url --request $requestPath --contract $contractPath --output $outputPath
$exitCode = $LASTEXITCODE

# 5. Processar e exibir o resultado
if ($exitCode -eq 0) {
    if (Test-Path -Path $outputPath) {
        $recibo = Get-Content -Raw -LiteralPath $outputPath -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
        $resp = $recibo.response
        if (
            $recibo.exit_code -ne 0 -or
            $recibo.state -notin @("alarm", "no_alarm") -or
            $null -eq $resp
        ) {
            Write-Host "Falha do lançador: recibo incompatível com uma consulta bem-sucedida." -ForegroundColor Red
            exit 6
        }
        
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "CONSULTA REALIZADA COM SUCESSO" -ForegroundColor Green
        Write-Host "========================================"
        Write-Host "Origem:        $($resp.forecast_origin)"
        Write-Host "Alvo:          $($resp.target_time)"
        Write-Host "Probabilidade: $($resp.p_event)"
        Write-Host "Limiar:        $($resp.threshold)"
        Write-Host "Alarme:        $($resp.alarm)"
        Write-Host "----------------------------------------"
        Write-Host "Estado:        $($recibo.state)"
        Write-Host "Recibo novo:   $outputPath"
    } else {
        Write-Host "Falha do lançador: o cliente retornou 0, mas não gerou recibo." -ForegroundColor Red
        exit 6
    }
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "FALHA NA CONSULTA (Código de Saída: $exitCode)" -ForegroundColor Red
    Write-Host "========================================"
    
    if (Test-Path -Path $outputPath) {
        $recibo = Get-Content -Raw -LiteralPath $outputPath -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
        Write-Host "Estado da Falha: $($recibo.state)"
        Write-Host "Detalhe:          $($recibo.detail)"
        if ($null -ne $recibo.http_status) {
            Write-Host "HTTP Status:      $($recibo.http_status)"
        }
        Write-Host "Recibo de erro:   $outputPath"
    } else {
        Write-Host "Nenhum recibo foi gerado para esta execução."
    }
}

# 6. Devolver o mesmo código ao processo chamador
exit $exitCode
