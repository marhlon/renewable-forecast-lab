"""Entrada do contêiner; a API original mantém seu contrato."""
from pathlib import Path
import uvicorn
from renewable_forecast.decision_api import create_app

if __name__ == '__main__':
    app = create_app(Path('/app/artifacts/policy.json'), Path('/app/artifacts'), threads=2)
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
