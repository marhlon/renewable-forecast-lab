$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
python scripts/auditar_distribuicao.py
if ($LASTEXITCODE -ne 0) { throw "A auditoria falhou; nenhum contexto sera preparado." }
python scripts/preparar_container.py
if ($LASTEXITCODE -ne 0) { throw "A preparacao falhou; nenhum container sera executado." }
python scripts/verificar_container.py
if ($LASTEXITCODE -ne 0) { throw "Container nao aprovado. O contexto e os logs foram preservados; leia o erro." }
