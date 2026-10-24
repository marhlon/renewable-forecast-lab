# M06.3 — revisão do parecer de monitoramento

5 de outubro de 2026 · projeto Renewcast · CJU_BA5EIGT · h24/d2

O monitor foi reproduzido pelo aluno nos quatro cenários. O parecer independente apresentado não auditou esse lote: depois de falhar na localização do banco, criou observações sintéticas e publicou um resultado sem confrontá-lo com as métricas oficiais. Brier 0,281875 e Skill −50,283% pertencem ao fallback. Não são evidência de piora do modelo.

A fórmula NumPy do Brier foi implementada corretamente. A revisão concentra-se na seleção da fonte, na unidade temporal de avaliação e no contrato de aceitação. O histórico de entregas anteriores permanece reconhecido.

## Instalação localizada

Baixe `renewcast_m06_parecer_20261005.zip` para `C:\renewable-forecast-lab`. No PowerShell já aberto nessa pasta, com `(renewable-forecast)` ativo:

```powershell
if (-not (Test-Path .\notebooks\parecer_monitoramento_antes_correcao_20261005.py)) {
    Copy-Item .\notebooks\parecer_monitoramento.py .\notebooks\parecer_monitoramento_antes_correcao_20261005.py
}
Expand-Archive -LiteralPath .\renewcast_m06_parecer_20261005.zip -DestinationPath . -Force
python notebooks/parecer_monitoramento.py
```

Somente o notebook de parecer e os documentos indicados no pacote são escritos. Não há banco, modelo, dataset, alteração de event_monitor ou comando de treino no ZIP. A cópia preserva o código anterior; os relatórios inválidos anteriores também permanecem disponíveis para rastrear o ocorrido.

Resultados desta correção:

```text
reports/monitoring/CJU_BA5EIGT/h24_event_batch_v1/parecer_validado/
  parecer.csv
  parecer.md
  auditoria.json
```

Abra o Markdown da nova pasta. Os antigos `notebooks/parecer.md` e `reports/.../parecer.md` gerados pelo fallback não passam a ser válidos por terem o mesmo nome.

## Contrato de entrada sem busca aproximada

| Entrada | Caminho relativo à raiz |
|---|---|
| Previsões e avaliações do lote | `reports/service/CJU_BA5EIGT/h24_event_batch_v1/ledger.sqlite` |
| Manifesto do modelo usado no lote | `models/CJU_BA5EIGT/h24_event_batch_v1/manifest.json` |
| Relatório normal | `reports/monitoring/CJU_BA5EIGT/h24_event_batch_v1/normal/monitor.json` |
| Outros relatórios | Mesma pasta-base: `missing_observation`, `changed_probability`, `missing_assessment` |
| Corte da avaliação | `2026-08-02T07:00:00Z` |

O programa aceita `--db`, `--manifest`, `--monitor-dir`, `--as-of` e `--output-dir` explícitos. As entradas devem pertencer ao mesmo lote e corte. Os caminhos padrão se resolvem pela localização do notebook, e não por uma procura em todo o disco.

`mlflow.db` é outro banco. A presença de uma tabela chamada assessments não o transforma no ledger. A procura por `*.db` também deixava de fora o arquivo `.sqlite` efetivamente gerado.

## O que mudou e por quê

| Falha encontrada | Consequência | Correção |
|---|---|---|
| Criar fallback sintético quando faltava a entrada | Produzia uma avaliação plausível de outro conjunto de dados | Arquivo ausente causa erro; SQLite aberto com `mode=ro` |
| Selecionar o manifesto `h24_event_api_v1` | Referência e identidade podiam vir de outro treino | Manifesto `h24_event_batch_v1`, conferido contra o hash registrado no ledger |
| Buscar nomes alternativos e usar frequência constante como fallback | Mascarava incompatibilidade de schema | Campos exatos `training_events` e `training_rows` obrigatórios |
| Consultar observed sem selecionar as_of | No lote normal, 5 + 24 = 29 linhas; cinco emissões seriam contadas duas vezes | `WHERE a.as_of = ? AND a.status = 'observed'` |
| Buscar Brier em campos inexistentes do JSON | Comparativo N/A não comprovava nada | Ler `performance.metrics.brier`, `baseline_brier` e `brier_skill` |
| Usar `or` para escolher valores numéricos | Zero podia ser confundido com ausência | Distinguir explicitamente zero, null e chave ausente |
| Imprimir divergência e continuar | Publicava sucesso sem aceite | Divergência acima de 1e-9, ou chave ausente, interrompe antes da gravação |
| Devolver tabela fixa para os cenários | O CSV não refletia os relatórios efetivamente recebidos | Ler os quatro JSONs e conferir corte/modelo/política/origem das cópias |

## Cálculo que deve ser defendido

Para cada emissão observada do corte escolhido, usamos y igual a 0 ou 1 e a probabilidade p que foi registrada quando a previsão foi emitida:

```text
p0 = training_events / training_rows
Brier_modelo = média((p - y)²)
Brier_referência = média((p0 - y)²)
Skill = 1 - Brier_modelo / Brier_referência
```

A referência tem probabilidade fixa calculada no treino e é avaliada nos mesmos resultados do modelo. Não substituímos p0 pela frequência de eventos observada depois no lote. Se o Brier da referência for zero, o quociente é indefinido: o JSON recebe null, e não um Skill inventado igual a zero.

Os logs anteriores do aluno registram 24 observações, 6 eventos, Brier do modelo 0,13260301577839723 e treino 168/694. Esses números implicam Brier de referência 0,187562806766936 e Skill aproximadamente 0,293021. São valores esperados se os arquivos continuam correspondendo àquela execução; não estão inseridos como respostas no programa. A autoridade da conferência é o recálculo sobre os arquivos reais e a concordância entre eles.

O número 168 tem dois usos distintos neste exercício: número de eventos positivos no treino e mínimo didático de observações para a regra do monitor. A igualdade numérica é coincidência; nenhum dos dois é o denominador da avaliação atual, que tem 24 observações.

## Parecer técnico sustentado pelas evidências

| Cenário relatado pelo aluno | Ação exportada | Interpretação |
|---|---|---|
| normal | collect_evidence | Registro coerente, mas apenas 24 resultados; métricas descritivas |
| missing_observation | investigate_data | Existe avaliação que registra falta do resultado após target_available_at |
| changed_probability | repair_record | Probabilidade tabulada diverge da resposta registrada; métricas bloqueadas |
| missing_assessment | repair_record | Falta uma linha de avaliação que deveria existir; métricas bloqueadas |

As duas falhas de integridade têm prioridade crítica na regra atual. Não há base para dar uma prioridade menor à avaliação desaparecida somente porque parece uma falha administrativa. Deve-se restaurar o registro confiável antes de julgar o desempenho.

Não é possível atribuir divergências de métricas apenas à flutuação amostral. Aqui a discrepância do parecer decorre, desde logo, de uma fonte sintética diferente. Tampouco se pode afirmar que a observação ausente será recuperada ou que o incidente é definitivamente permanente sem investigar a fonte.

O mínimo de 168 observações é um disparador didático. Não garante representatividade, independência, estabilidade, concept drift ou validade estatística. Brier favorável em 24 resultados não aprova promoção/retreino. O monitor orienta investigação; não executa essas ações.

## Verificação da correção pelo professor

O programa foi executado na réplica local do lote real já construída no projeto: 24 observações finais, quatro cenários lidos e métricas coincidentes com os relatórios dessa réplica. Ela tem probabilidades distintas das relatadas pelo aluno: Brier 0,11456217343445767. Esse valor não substitui o Brier do aluno nem precisa ser reproduzido no Windows.

Dez verificações dirigidas passaram: corte correto sem dupla contagem; banco ausente sem criação; banco alheio rejeitado; manifesto alheio rejeitado; métrica obrigatória ausente rejeitada; divergência de 1e-6 rejeitada; cenário de outro modelo rejeitado; falha da CLI sem publicação de parecer; zero e Skill indefinido tratados; ledger original preservado. `docs/evidencias_m06_parecer_professor/verification.json` contém o registro.

Limites: não houve execução deste script no Windows do aluno; o banco e os quatro monitor.json atuais dele não foram anexados nesta rodada. Hash identifica coerência dos bytes, não a veracidade física da medição. O script recalcula métricas e lê relatórios; não reexecuta os incidentes, estimadores ou avaliações meteorológicas.

## Fixação lexical no próprio código

| Termo | Onde demonstrar o significado |
|---|---|
| Linhagem | `auditar`: liga ledger, manifesto e relatórios pelo mesmo modelo/política |
| Grão da tabela | `consultar_resultados_observados`: avaliação identificada por as_of e forecast_origin |
| Snapshot | O filtro as_of escolhe uma fotografia de avaliação, sem acumular fotografias |
| Contrato | Nomes obrigatórios e tipos aceitos; ausência reprova |
| Referência fixa | `obter_frequencia_treino`: usa o manifesto do modelo do lote |
| Recalcular | `recalcular_metricas`: parte de p e y; não reaproveita a.brier |
| Evidência insuficiente | Pode-se calcular uma métrica sem liberar uma decisão operacional |

A revisão fornecida pelo professor não é registrada como autoria independente do aluno. A execução corrigida encerra o bloqueio técnico localizado; a retomada de autonomia será feita na próxima aplicação, sem apagar os aceites anteriores ou exigir nova rodada de treino e dezenas de testes.

Próximo bloco já previsto: telemetria do serviço — registrar duração e resultado das requisições e diagnosticar um incidente pelos próprios registros. M06 continua em andamento; esta correção não inaugura outro marco nem altera o percentual da formação.
