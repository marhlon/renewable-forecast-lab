# Entrega M10.2 — reconstrução PCA e comparação dos detectores

A [função](notebooks/m10_2_pca_autoral.py) foi usada na execução Windows
`20261119T101049Z_253ff59f`. A rodada completa foi executada uma vez.
Passaram duas contas geométricas e a comparação dos resíduos com a biblioteca,
além de oito testes adicionais. A diferença máxima foi 3,73 × 10⁻¹⁴.

A entrega escrita está em [Resposta_M10_2.md](docs/m10_2/Resposta_M10_2.md):
função, caso real com percentis, sensibilidade ao ID dominante e conta de
transferência. O [guia passo a passo](docs/m10_2/Explicacao_Passo_a_Passo.md)
explica o percurso entre as aulas e as operações matriciais.

O [relatório HTML](reports/m10_2/20261119T101049Z_253ff59f/relatorio.html) e o
[resultado.json](reports/m10_2/20261119T101049Z_253ff59f/resultado.json)
preservam as saídas locais. A solicitação de abertura foi enviada ao Windows;
não houve inspeção visual automatizada do navegador.

## Conferir os arquivos sem ajustar novamente

Na raiz `C:\renewable-forecast-lab`, com o ambiente existente ativo:

```powershell
python -m unittest discover -s satellite-anomaly-monitor/tests -p test_m10_2_pca_autoral.py -v
python satellite-anomaly-monitor/docs/evidencias_m10_2_local/auditar_resultados.py
```

A auditoria lê a rodada fixa e recalcula coortes, resíduos, rankings, AP e
coberturas. Ela não ajusta detectores. Os escores persistidos da floresta
permitem recalcular sua avaliação; as árvores não foram exportadas como
checkpoint por este laboratório.

## Conteúdo

O ZIP contém a função, a resposta, o guia, os testes, as aulas e os códigos
originais usados no laboratório, o recorte identificado de dados e as saídas
completas desta execução. O manifesto `ENTREGA_M10_2_SHA256.json` identifica
cada arquivo incluído, exceto o próprio manifesto. Os arquivos da execução
não foram editados. O pacote complementa o projeto e usa NumPy, pandas e
scikit-learn do ambiente existente.

As anotações e a grade têm limitações descritas nas aulas e no protocolo da
fonte. AP é ranking por instante; nenhum limiar foi escolhido e o período
reservado não foi utilizado. A clínica de decisão do Renewcast é material
de revisão e não é insumo desta rodada.
