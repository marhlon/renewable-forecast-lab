$ErrorActionPreference = "Stop"
$project = Split-Path -Parent $PSScriptRoot
Set-Location $project

python -c "import sys; from pathlib import Path; assert sys.version_info[:2] == (3, 12), 'Use Python 3.12'; assert Path(sys.prefix).name == 'renewable-forecast', 'Ative conda activate renewable-forecast'; import renewable_forecast.decision_api; print(sys.executable)"
if ($LASTEXITCODE -ne 0) { throw "Ambiente incorreto. O empacotamento nao iniciou." }

python scripts/empacotar_servico.py
if ($LASTEXITCODE -ne 0) { throw "Captura falhou. A reproducao nao sera executada. Leia o erro e build.log." }

python scripts/reproduzir_servico.py
if ($LASTEXITCODE -ne 0) { throw "Reproducao falhou. Leia installation.log/server.log na pasta indicada." }

Write-Host "Entrega tecnica gerada. Proxima demanda: docs/Aula_M06_Empacotamento.md"
