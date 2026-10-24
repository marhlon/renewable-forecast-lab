$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
python -m renewable_forecast.service_exercise
if ($LASTEXITCODE -ne 0) { throw "Telemetria interrompida. Leia o erro acima." }
