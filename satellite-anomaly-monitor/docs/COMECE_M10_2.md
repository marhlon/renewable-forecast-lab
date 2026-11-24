# Comece aqui — rodada M10.2

Do ferro ao pró — Data Science · Satellite Anomaly Monitor (P2) · 18/11/2026

**Nesta rodada você explica por que três detectores discordam, implementa o erro de reconstrução do PCA e interpreta uma comparação com telemetria real.** M10.1 já está aceito: seus arquivos e seu trabalho de sincronização não precisam ser refeitos. O recorte ampliado vem junto.

## O que fazer, em ordem

1. Baixe `rodada_m10_2_detectores.zip` para **`C:\renewable-forecast-lab`**. Extraia ali. O ZIP já contém a pasta `satellite-anomaly-monitor`; não extraia dentro dela.

   ```powershell
   Set-Location C:\renewable-forecast-lab
   conda activate renewable-forecast
   Expand-Archive -LiteralPath .\rodada_m10_2_detectores.zip -DestinationPath . -ErrorAction Stop
   ```

2. Abra este guia em `C:\renewable-forecast-lab\satellite-anomaly-monitor\docs\COMECE_M10_2.md`. Leia as aulas na ordem. Faça a conta da Aula 2 antes de olhar a implementação de referência.

   | Aula | O que você vai saber explicar | Onde praticar |
   | --- | --- | --- |
   | [1 — Escore robusto](m10_2/Aula_1_Escore_Robusto.md) | Por que ajustar mediana/MAD no passado e por que o máximo por canal ignora a relação entre canais | Conta curta com valor extremo e análise do contrato temporal |
   | [2 — PCA por reconstrução](m10_2/Aula_2_PCA_Reconstrucao.md) | Como projetar, voltar ao espaço original e medir o resíduo por amostra | Sua função `erro_pca_por_amostra` |
   | [3 — Isolation Forest e avaliação](m10_2/Aula_3_Isolation_Forest_e_Avaliacao.md) | Como comparar rankings e identificar quando um evento longo conduz a conclusão | Análise do relatório e exercício de transferência |

3. Crie **`C:\renewable-forecast-lab\satellite-anomaly-monitor\notebooks\m10_2_pca_autoral.py`**. Escreva apenas a função `erro_pca_por_amostra(x, centro, componentes)` da Aula 2. O código do laboratório já está completo; você não precisa editar o runner.

4. Execute **uma vez**, da raiz `C:\renewable-forecast-lab`, com sua função:

   ```powershell
   python .\satellite-anomaly-monitor\scripts\executar_m10_2.py --autoria .\satellite-anomaly-monitor\notebooks\m10_2_pca_autoral.py
   if ($LASTEXITCODE -ne 0) { throw 'Corrija o erro acima antes de abrir o relatório.' }
   $r = Get-Content -Raw .\satellite-anomaly-monitor\reports\m10_2\latest_run.json | ConvertFrom-Json
   Invoke-Item -LiteralPath (Join-Path $r.directory 'relatorio.html')
   ```

   A execução confere duas contas manuais, ajusta os métodos no período histórico e verifica todos os resíduos autorais contra a referência de biblioteca. NumPy, pandas e scikit-learn do seu ambiente bastam; não há download, instalação ou Docker nesse comando. Se quiser explorar o relatório antes de escrever, o mesmo script sem `--autoria` usa a referência. Para a entrega, basta sua execução autoral.

5. **Envie numa mensagem** a sua função e a resposta abaixo. Pode escrever direto no chat ou preencher [Resposta_M10_2.md](m10_2/Resposta_M10_2.md). Se um valor divergir da referência, inclua o `resultado.json` **da sua rodada**, em `C:\renewable-forecast-lab\satellite-anomaly-monitor\reports\m10_2\<run_id>\resultado.json`.

   - **Caso real:** escolha uma linha de desacordo em `casos_reais.csv`. Cite timestamp e dois percentis. Use a geometria do escore para explicar como o desacordo pode acontecer. Diga o que a anotação permite afirmar e o que continua desconhecido.
   - **Decisão:** compare a melhor AP com todos os eventos e sem `id_134`. Quanto do conjunto positivo esse ID representa? O que você congelaria para decidir o limiar no M10.3?
   - **Transferência:** resolva o novo caso de três canais na seção 5 da Aula 3. Calcule os escores de A e B com dois componentes e diga o que muda ao incluir o terceiro. Faça a previsão antes de consultar sua função.

**Como a rodada fecha:** as contas e a comparação em todos os dados aceitam o código; a correção da explicação e da transferência fecha a parte formativa. Vou revisar a sua justificativa por critério da Aula 3 e apontar a correção específica se houver erro. M10.3 usa a tabela de escores para passar de ranking a limiar, falso alarme e atraso por evento. Esse passo não depende de repetir M10.1 nem de abrir um terceiro projeto.

## O que é o arquivo da rodada anterior

| Arquivo | Destino no Windows se quiser manter no projeto | Uso nesta rodada |
| --- | --- | --- |
| `Aula_M02_M03_M05_Decisao_e_Risco.md` | `C:\renewable-forecast-lab\docs\Aula_M02_M03_M05_Decisao_e_Risco.md` | Revisão do **Renewcast**. As seções 4 e 7 ligam perda a quantil e probabilidade de evento a decisão. |
| `clinica_decisao_forecast.py` | `C:\renewable-forecast-lab\notebooks\clinica_decisao_forecast.py` | Reproduz a tabela de custo que já foi calculada. Não é insumo do M10.2. |

Para reproduzir a revisão anterior, se quiser, use a rodada completa que originou a análise:

```powershell
python .\notebooks\clinica_decisao_forecast.py --run-dir .\reports\transformer\CJU_BA5EIGT\m09_3_pre_treinado\20261117T212230Z_965de3d1
```

O elo entre as duas aulas é a decisão: no Renewcast, custo e probabilidade guiam a ação; no P2, um escore fornece uma ordem de investigação. Um percentil alto no ranking não fornece a probabilidade necessária para usar a regra de custo do Renewcast.

## Onde estão as saídas

| Arquivo em `C:\renewable-forecast-lab\satellite-anomaly-monitor\reports\m10_2\<run_id>` | Para que serve |
| --- | --- |
| `relatorio.html` | Comece aqui: métricas, casos, cobertura, sensibilidade e contexto. |
| `casos_reais.csv` e `sensibilidade_evento.csv` | Insumos para sua justificativa. |
| `cobertura_eventos.csv` | Confere quantos pontos um mesmo ID acrescentou ao ranking, sem contar cada canal como um evento independente. |
| `escores_desenvolvimento.csv.gz` | Mantém a linha do tempo e os escores para avaliar uma política de alarmes no M10.3. |
| `resultado.json` | Identifica o run e a execução de sua função. |

Referência: 136.202 instantes de ajuste, 105.042 comparáveis no desenvolvimento e oito IDs de anomalia. Isolation Forest lidera em AP no recorte completo; escore robusto lidera quando se retira o evento dominante, com os escores fixos. A análise está na Aula 3. Pequenas diferenças numéricas entre versões não são o objetivo da comparação.
