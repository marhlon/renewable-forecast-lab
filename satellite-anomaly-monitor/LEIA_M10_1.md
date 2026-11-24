# P2 — satellite-anomaly-monitor: M10.1

Na raiz `C:\renewable-forecast-lab`, execute:

```powershell
conda activate renewable-forecast
python satellite-anomaly-monitor/scripts/executar_m10_1.py
```

Leia `docs/Aula_M10_1_Contrato_Telemetria.md` dentro desta pasta. Os dados reais ESA já acompanham o pacote. Esta unidade lê CSVs, produz perfil, sincroniza três canais com idade máxima e preserva as anotações em tabela separada. Não instala dependências nem treina modelos.

O módulo reutilizável está em `src/satmon/temporal.py`. A demanda de implementação e os dois comandos autorais estão na seção 7 da aula. A execução normal está completa e não depende da autoria. A pasta `notebooks` foi reservada para seu arquivo; não há função pendente dentro do pipeline.

Saídas em `reports/m10_1/<run_id>`. `latest_run.json` aponta a execução completa mais recente. A referência Linux e a auditoria independente ficam em `docs/evidencias_professor/`, separadas das suas saídas.

Limites: recorte exploratório de um ano, três canais anonimizados; disponibilidade e interpretação UTC assumidas; três IDs de anomalia; nenhuma conclusão operacional ou métrica de detector.
