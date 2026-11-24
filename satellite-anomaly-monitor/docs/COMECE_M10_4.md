# M10.4 — Diagnosticar um detector que ficou em silêncio

**Produto:** Satellite Anomaly Monitor (P2). **Decisão:** descobrir em qual etapa surgiu o 0/8 da M10.3 e se retirar um canal resolve algo quando se medem as mesmas ocorrências.

O ZIP acrescenta esta rodada à sua pasta em Windows. Reutiliza as duas execuções já aceitas; não há download, instalação, Docker, nuvem ou execução de M10.2/M10.3. O diagnóstico ajusta 11 florestas pequenas para a comparação controlada; a referência de três canais e semente 17 lê os escores salvos.

## 1. Leia, nesta ordem

| Aula | O que você aprende | Evidência para abrir |
| --- | --- | --- |
| [01 — Do pico à confirmação](m10_4/Aula_01_Limite_de_Confirmacao.md) | Provar se uma regra com k leituras poderia sequer emitir um início. | `perfil_escores_ano.csv` e `limites_por_id.csv` |
| [02 — Ablação que responde uma pergunta](m10_4/Aula_02_Ablacao_e_Estabilidade.md) | Comparar canais sem mudar a coorte, o ajuste ou o orçamento por acidente. | `metricas_ablacao.csv`, `estabilidade_sementes.csv` e `mudancas_por_id.csv` |
| [03 — Decisão e teste novo](m10_4/Aula_03_Decisao_e_Validade_Externa.md) | Defender por que manter o detector como diagnóstico, e desenhar uma prova de transferência. | `relatorio.html` e `resultado.json` |

Use a [revisão M10.3](m10_4/Revisao_M10_3_Windows.md) para ver o que já está encerrado. A referência executada está em [evidencias_m10_4](evidencias_m10_4/), se quiser consultar os números antes de editar.

## 2. Edite só sua função

Salve em:

`C:\renewable-forecast-lab\satellite-anomaly-monitor\notebooks\m10_4_limite_autoral.py`

O [modelo](m10_4/Modelo_limite_confirmacao.py.txt) é texto para copiar ou usar como ponto de partida. Implemente `limite_confirmacao(escores, utilizavel, *, consecutivos)`. Para cada janela com exatamente `consecutivos` posições adjacentes e utilizáveis, calcule o menor escore. Retorne o maior desses mínimos como `limiar_maximo`, e como `indice_confirmacao` o índice, começando em zero, do **último** elemento da primeira janela empatada nesse máximo. Sem janela válida, ambos os valores são `None`. Preserve lacunas e entradas. A Aula 01 traz uma conta completa, o algoritmo em palavras e critérios de verificação.

## 3. Execute uma vez com sua função

Baixe `rodada_m10_4_diagnostico.zip` para `C:\renewable-forecast-lab`. Os passos 1 e 2 são leitura e edição; o teste só roda depois de salvar seu arquivo.

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\rodada_m10_4_diagnostico.zip -DestinationPath . -ErrorAction Stop
Invoke-Item .\satellite-anomaly-monitor\docs\COMECE_M10_4.md
```

Após salvar sua função:

```powershell
python .\satellite-anomaly-monitor\scripts\executar_m10_4.py --autoria .\satellite-anomaly-monitor\notebooks\m10_4_limite_autoral.py
```

Para verificar **só a função** em segundos, sem dados e sem ajuste, acrescente `--verificar` ao comando. Ele já roda as mesmas sete contraprovas antes do diagnóstico completo. Se o runner mostrar caminho ausente, confira os diretórios dos seus resultados locais. Os padrões são `satellite-anomaly-monitor/reports/m10_2/20261119T101049Z_253ff59f` e `satellite-anomaly-monitor/reports/m10_3/20261123T195301Z_332fb306`. Só use `--m10-2-run` ou `--m10-3-run` se tiver movido esses resultados para outro lugar; conserve a pasta com o ID. Não misture execuções de referência com recibos Windows.

O programa imprime a pasta em `satellite-anomaly-monitor/reports/m10_4/<run_id>`. Abra seu `relatorio.html`. Os CSVs mostram o que foi contado; o `resultado.json` identifica as entradas e guarda os hashes. Os arquivos das unidades anteriores ficam preservados.

## 4. Entregue para avançarmos

Preencha [Resposta_M10_4.md](m10_4/Resposta_M10_4.md). Devolva **sua função, o `resultado.json` novo, `metricas_ablacao.csv` e as três respostas**. Não é preciso zipar ou reenviar o projeto. O aceite exige a equivalência da função nas janelas reais, uma comparação de canal com a mesma coorte e uma decisão que indique qual evidência faltaria. Depois disso, o roteiro segue para M11.
