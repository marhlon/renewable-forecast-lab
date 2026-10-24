# Execute na raiz: .\scripts\run_m06_lote.ps1
# Nao instala dependencias, nao baixa dados e nao usa o servidor HTTP.
$ErrorActionPreference = 'Stop'
$ProjectPath = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectPath

function Invoke-CheckedPython {
    param([string[]]$CommandArgs)
    & python @CommandArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Execucao interrompida (codigo $LASTEXITCODE). Nao execute as etapas seguintes."
    }
}

Invoke-CheckedPython -CommandArgs @('-c', 'import sys; import renewable_forecast.event_batch; print(sys.executable)')
$InputDir = 'data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development'
$PolicyPath = 'reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json'
$ModelDir = 'models/CJU_BA5EIGT/h24_event_batch_v1'
$DatabasePath = 'reports/service/CJU_BA5EIGT/h24_event_batch_v1/ledger.sqlite'

Invoke-CheckedPython -CommandArgs @('-m', 'renewable_forecast.event_artifact', '--input-dir', $InputDir, '--policy', $PolicyPath, '--output-dir', $ModelDir, '--forecast-origin', '2026-07-31T06:00:00Z', '--threads', '2')
$EmitArgs = @('-m', 'renewable_forecast.event_batch', 'emit', '--input-dir', $InputDir, '--model-dir', $ModelDir, '--policy', $PolicyPath, '--db', $DatabasePath, '--origin-start', '2026-07-31T06:00:00Z', '--origin-end', '2026-08-01T05:00:00Z', '--threads', '2')
Invoke-CheckedPython -CommandArgs $EmitArgs
# Repetir e intencional: deve reutilizar as 24 previsoes, sem duplicar nem recalcular.
Invoke-CheckedPython -CommandArgs $EmitArgs
Invoke-CheckedPython -CommandArgs @('-m', 'renewable_forecast.event_batch', 'reconcile', '--input-dir', $InputDir, '--db', $DatabasePath, '--as-of', '2026-08-01T12:00:00Z')
Invoke-CheckedPython -CommandArgs @('-m', 'renewable_forecast.event_batch', 'reconcile', '--input-dir', $InputDir, '--db', $DatabasePath, '--as-of', '2026-08-02T07:00:00Z')
Write-Host 'Lote concluido. Leia docs/Aula_M06_Lote_Conciliacao.md para a inspecao SQL.'
