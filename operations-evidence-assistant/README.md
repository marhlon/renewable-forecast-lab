# Operations Evidence Assistant

Terceiro produto da trilha Do ferro ao pró — Data Science. Comece por [docs/COMECE_M11_1.md](docs/COMECE_M11_1.md). Esta rodada gera localmente explicações de evidências conhecidas e mede comportamentos contra uma decisão em Python. O modelo não decide nem altera políticas dos outros produtos.

- `data/casos_m11_1.json`: casos e origem de cada recorte.
- `model/model_lock.json`: hashes dos arquivos públicos do modelo, sem incluir pesos no ZIP.
- `src/opevid`: contrato, amostragem de referência e preparação do modelo.
- `scripts/executar_m11_1.py`: entrada para execução e conferência.
- `notebooks/m11_1_amostragem_autoral.py`: única função a editar na atividade.

Casos de ensino/de desenvolvimento. Sem adaptação de pesos e sem aprovação para uso operacional.
