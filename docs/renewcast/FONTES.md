
# Fontes dos três achados do README

Revisão editorial de 27/11/2026. As cópias em `evidencias/` são idênticas aos arquivos locais de origem, com hashes no [mapa editorial](evidencias/fontes_editoriais.json). Esse mapa descreve uma revisão documental; não é recibo de nova execução experimental.

| Achado | Arquivos de origem na raiz do repositório | Campos e interpretação |
| --- | --- | --- |
| 1 — Persistência e critério primário | `reports/fechamento_m00_m09/bloco3_engenharia/M03-04/summary.csv`, `bootstrap_pareado.csv`, `resultado.json` | `method`, `n`, `mae`, `rmse`; ganho Chronos em `ci95_low`/`ci95_high`; decisão congelada no resultado |
| 2 — MAE e RMSE nas três GRUs | Mesmo `M03-04/summary.csv` e `protocolo.json` | Linhas `gru_17`, `gru_29`, `gru_41` e `persistence`; todas com n=671; não selecionar a melhor semente após o teste |
| 3 — Cobertura e largura | `reports/fechamento_m00_m09/bloco3_engenharia/M03-04/metricas_intervalos.csv`, `resultado.json` e `protocolo.json` | Linhas `hgb_cqr` e `chronos_raw`; `coverage` é fração, `width` em MWmed; nominal 0,8 e limite de largura 100 no protocolo |

**Identificação:** diretório `reports/fechamento_m00_m09/bloco3_engenharia/M03-04`, partição final retrospectiva de setembro/2026, recibo concluído em `2026-11-26T16:16:56.269389+00:00`. O resultado não tem campo `run_id`. Nenhum UUID foi criado para fazer a execução parecer conforme a um contrato que ela não possui. A identidade usa diretório, timestamp e SHA-256 do recibo: `ab8cf503036652fe2b7832128bbe66ae6c7f9aba3e302a2e78dae1f2fc29f5a1`.

**Recorte:** 720 medições horárias da fonte principal produziram 671 origens comuns, com 24 medições históricas até origem−2h, alvo origem+24h e disponibilidade de rótulo assumida em origem+26h. Não foram agregados resultados de Linux, de outubro, das 168 origens de desenvolvimento ou do experimento global h+1.

**Estado de execução:** o [relatório do bloco 3](../roadmap_m00_m09/Relatorio_Engenharia_Bloco3.md) e os recibos locais `execucao_avaliacao_final.json` e `recuperacao_relatorio_final.json`, na pasta do bloco, registram a falha de impressão CP1252 e a recuperação somente da síntese em UTF-8. Os JSONs que incluem caminhos privados do ambiente não foram copiados para esta seleção pública. A revisão editorial não repetiu inferência, treinamento ou bootstrap.

**Figura:** nenhuma figura localizada representa as 671 origens. A [especificação](FIGURA_PROPOSTA.md) é uma pendência editorial explícita. A imagem histórica de julho não foi usada para sustentar números de setembro.

**Versionamento:** fontes e cópias existem no workspace. Novos arquivos de documentação e vários componentes do bloco 3 ainda não constam do índice Git inspecionado; criar este mapa não os publica nem garante sua presença num clone. Brutos, pesos, bancos e parte dos logs são ignorados. Consulte o [guia](REPRODUCAO.md).
