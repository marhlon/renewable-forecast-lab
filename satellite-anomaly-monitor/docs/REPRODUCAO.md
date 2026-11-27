# Reprodução e evidências do Satellite Anomaly Monitor

Este guia acompanha o [README específico](../README.md). Os comandos foram conferidos por leitura da implementação; esta edição documental não instalou dependências, baixou dados, executou contraprovas ou ajustou detectores.

## Ambiente e diretório de trabalho

Execute da raiz do repositório, que contém `pyproject.toml` e a pasta `satellite-anomaly-monitor`. O manifesto da raiz exige Python >=3.12,<3.13 e inclui NumPy, pandas e scikit-learn; o runner usa também threadpoolctl, dependência do scikit-learn. O pacote `satmon` é localizado pelo próprio script por meio de `satellite-anomaly-monitor/src`; ele não é instalado pelo entry point `renewcast`.

A execução Windows M10.4 citada registrou Python 3.12.13, NumPy 2.5.3, pandas 3.0.5 e scikit-learn 1.9.0. O ambiente Conda `renewable-forecast` já preparado foi usado naquela máquina; esse nome não cria um ambiente em outro computador. Não há um lock dedicado ao P2 identificado nesta revisão. Uma instalação nova precisa resolver as dependências do manifesto; não se promete identidade numérica entre versões diferentes apenas por ler os intervalos permitidos no manifesto.

## Entradas obrigatórias

O caminho mínimo não precisa refazer M10.1–M10.3. Ele precisa dos arquivos preservados abaixo, com os nomes e hashes conferidos pelos recibos:

| Conjunto | Caminhos dentro de `satellite-anomaly-monitor` |
| --- | --- |
| Ajuste/desenvolvimento | `data/reference/esa_mission1_m10_2/protocolo.json`, `canais_grade.csv.gz`, `eventos.csv` |
| Teste histórico | `data/reference/esa_mission1_m10_3/proveniencia.json`, `grade_teste.csv.gz`, `eventos_teste.csv` |
| M10.2 Windows | `reports/m10_2/20261119T101049Z_253ff59f/resultado.json` e `escores_desenvolvimento.csv.gz` |
| M10.3 Windows | `reports/m10_3/20261123T195301Z_332fb306/resultado.json`, `politica_congelada.json` e `escores_teste.csv.gz` |
| Contratos e código | `docs/m10_3/protocolo_politica.json`, `docs/m10_4/protocolo_diagnostico.json`, `scripts/executar_m10_2.py`, `scripts/executar_m10_3.py`, `scripts/executar_m10_4.py` e módulos de `src/satmon` |

A inspeção do índice Git encontrou esses recortes, runs M10.2/M10.3, protocolos e scripts rastreados. Eles também existem nesta árvore de trabalho. Não foram baixados novamente nem foi aberto um clone separado nesta revisão. Se uma distribuição omitir os arquivos grandes, reponha os recortes preservados e confira seus hashes pelos respectivos protocolos/proveniência; o README não fornece um URL inventado para um pacote ausente.

O run Windows M10.4 `reports/m10_4/20261124T152509Z_3878d5e2` e `notebooks/m10_4_limite_autoral.py` existem localmente, mas não estavam rastreados no índice Git inspecionado. O README aponta para cópias intactas leves de seu recibo e de sua tabela de ablação em `docs/evidencias_readme`. Seus hashes de origem/cópia estão no [manifesto](evidencias_readme/manifesto.json). Essas cópias, o novo README, o guia e a figura são arquivos novos; sua inclusão no próximo commit/distribuição precisa ser conferida, pois esta tarefa não faz commit ou push.

## Caminho mínimo

Com o ambiente existente e as entradas acima:

```powershell
conda activate renewable-forecast
python satellite-anomaly-monitor/scripts/executar_m10_4.py --verificar
python satellite-anomaly-monitor/scripts/executar_m10_4.py
```

`--verificar` executa sete contraprovas pequenas da função de referência e retorna antes de ler os dados ou ajustar florestas. O modo completo valida a cadeia de recibos, ajusta 11 florestas apenas no período 2004–2007, reutiliza literalmente os escores da referência de três canais/semente 17 e escreve um novo diretório em `satellite-anomaly-monitor/reports/m10_4/<run_id>`. O programa imprime o caminho de `relatorio.html`; não se deve localizar esse run por um `latest_run.json` que o runner M10.4 não escreve.

Para usar o arquivo autoral local, acrescente `--autoria satellite-anomaly-monitor/notebooks/m10_4_limite_autoral.py` ao comando. Esse arquivo precisa estar presente e terá seu hash registrado no novo recibo. `--m10-2-run` e `--m10-3-run` permitem apontar para as pastas preservadas quando movidas, conservando os IDs; `--output-dir` muda somente a raiz de saída. Os caminhos padrão estão fixados nos IDs acima.

Essa execução é reprodução de um diagnóstico retrospectivo: 2011–2013 já foi aberto em M10.3. Ela não é uma nova seleção de política nem uma avaliação temporal ainda não examinada.

## Mapa das três evidências do README

| Achado | Run, partição e arquivos que sustentam os números |
| --- | --- |
| 1 — Ranking | Windows `20261119T101049Z_253ff59f`, desenvolvimento 2008–2010: `reports/m10_2/20261119T101049Z_253ff59f/resultado.json`, campos `average_precision` e `dev_rows_evaluated`; tabela `metricas.csv` |
| 2 — Transferência | Windows `20261123T195301Z_332fb306`, desenvolvimento 2008–2010 e teste 2011–2013 apresentados separadamente: `reports/m10_3/20261123T195301Z_332fb306/resultado.json`, lista `metricas`; corte e confirmação em `politica_congelada.json`; tabela `metricas_episodios.csv` |
| 3 — Diagnóstico | Windows `20261124T152509Z_3878d5e2`, partição `diagnostico`, 2011–2013: `reports/m10_4/20261124T152509Z_3878d5e2/metricas_ablacao.csv`, sementes 17/29/41 e variantes `tres_canais/sem_50/sem_51/sem_52`; cadeia e retrospectividade em `resultado.json` |

O recibo M10.4 registra `verified_against_reference_real_data=true`, sete contraprovas e a preservação da política M10.3. As [cópias do recibo](evidencias_readme/m10_4_windows_resultado.json) e das [métricas](evidencias_readme/m10_4_windows_metricas_ablacao.csv) mantêm os mesmos bytes das fontes acima. A auditoria local já existente em `docs/evidencias_m10_4_local/auditoria_resultados.json` recalculou os limites da referência a partir dos escores persistidos. As novas variantes não salvaram seus vetores completos de escores/checkpoints: a auditoria delas se limita às identidades, coortes, tabelas, álgebra e agregados declarados. Não se anuncia reprodução independente de todas as florestas por apenas conferir essas tabelas.

## Figura e origem dos dados

A figura estável `docs/images/alcance_confirmacao_2011_2013.png` é uma cópia sem alteração de `docs/evidencias_m10_4/alcance_do_corte.png`. Essa figura veio da execução de referência `20261123T235056Z_d98b7536`, não foi gerada pelo run Windows citado. Nesta edição, foram conferidos nas duas tabelas `metricas_ablacao.csv` os cortes, S1 e S2 das quatro variantes da semente 17 na partição `diagnostico`: a diferença máxima foi zero. A figura foi inspecionada visualmente e pode ilustrar os números coincidentes; não transforma a referência em execução pessoal. SHA-256 da origem e da cópia: `61145bb5b7216967ee7dda6e03e7a1945b6ae2e2842e432c06018284b2eadced`.

S1 é o maior escore utilizável. S2 é o maior dos mínimos das janelas de duas posições adjacentes utilizáveis. O gráfico mostra S1−corte e S2−corte, unidade adimensional, para 2011–2013. Remover canal preserva a exigência de disponibilidade dos três canais para manter a mesma população avaliada.

Fonte: [ESA Anomaly Dataset Mission1 v2](https://doi.org/10.5281/zenodo.15237121), canais 50–52. A origem, os hashes dos membros e a atribuição/licença dos dados constam de `data/reference/esa_mission1_m10_2/protocolo.json` e `data/reference/esa_mission1_m10_3/proveniencia.json`. A semântica física dos canais é desconhecida; estas séries não são imagens de satélite. UTC e disponibilidade na medição são hipóteses. Uma nova avaliação exige congelar outra janela e critérios antes de observar seus resultados.
