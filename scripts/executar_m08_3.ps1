<# Executar na raiz, no ambiente renewable-forecast ja existente. #>
[CmdletBinding()]
param([switch]$Verificar)
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
Push-Location $project
try {
    python -c "import sys; from pathlib import Path; assert Path(sys.prefix).name == 'renewable-forecast', 'Ative: conda activate renewable-forecast'; import torch, pandas, pyarrow, sklearn; import renewable_forecast.neural_gru; print('Python:', sys.executable); print('PyTorch:', torch.__version__)"
    if ($LASTEXITCODE -ne 0) { throw 'Ambiente ou modulo ausente. Nao houve treino.' }
    if ($Verificar) {
        python notebooks/laboratorio_gru.py --verificar
    } else {
        python notebooks/laboratorio_gru.py
    }
    if ($LASTEXITCODE -ne 0) { throw 'M08.3 interrompida. Preserve a mensagem e failure.json.' }
} finally {
    Pop-Location
}
