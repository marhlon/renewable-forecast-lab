# Comece aqui — rodada M10.3

Do ferro ao pró — Data Science · Satellite Anomaly Monitor (P2) · 23/11/2026

**Nesta rodada você transforma escores em inícios de alarme, congela uma política e avalia sua transferência temporal.** O M10.2 já está conferido. Mantenha os arquivos e a execução que você gerou; você não precisa reproduzir aquela rodada. O recorte reservado de 2011–2013 vem no ZIP.

## 1. Extraia na raiz do projeto

Baixe `rodada_m10_3_alarmes.zip` para `C:\renewable-forecast-lab`. Da raiz:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\rodada_m10_3_alarmes.zip -DestinationPath . -ErrorAction Stop
```

O ZIP já contém a pasta `satellite-anomaly-monitor`. Ele acrescenta caminhos novos. O comando usa **o seu M10.2** em `satellite-anomaly-monitor\reports\m10_2\20261119T101049Z_253ff59f`: mantenha ali `resultado.json` e `escores_desenvolvimento.csv.gz`. Também usa as entradas e os scripts originais já extraídos do M10.2. Não use `latest_run.json` do laboratório anterior para localizar esta execução.

## 2. Leia e implemente

| Aula | O que você vai fazer |
| --- | --- |
| [1 — Da leitura ao alarme](m10_3/Aula_1_Da_Leitura_ao_Alarme.md) | Fazer a conta de confirmação e escrever `iniciar_alarmes`. |
| [2 — Limiar e avaliação por episódio](m10_3/Aula_2_Limiar_e_Avaliacao.md) | Ver como 33 candidatos competem dentro de um orçamento de alarmes. |
| [3 — Teste temporal e decisão](m10_3/Aula_3_Teste_Temporal_e_Decisao.md) | Explicar o silêncio do detector e defender o próximo experimento. Se quiser formular a hipótese antes de ver os resultados, leia a seção 2 após executar. |

Crie **`C:\renewable-forecast-lab\satellite-anomaly-monitor\notebooks\m10_3_alarme_autoral.py`**. Sua única implementação é esta função:

```python
def iniciar_alarmes(escores, utilizavel, *, limiar, consecutivos):
    """Devolve um booleano por instante: True só quando uma sequência é confirmada."""
```

A Aula 1 especifica argumentos, fronteiras e casos. O script e a avaliação por ID já estão implementados.

## 3. Execute uma vez com sua função

```powershell
python .\satellite-anomaly-monitor\scripts\executar_m10_3.py --autoria .\satellite-anomaly-monitor\notebooks\m10_3_alarme_autoral.py
if ($LASTEXITCODE -ne 0) { throw 'Corrija o erro acima antes de abrir o relatório.' }
$r = Get-Content -Raw .\satellite-anomaly-monitor\reports\m10_3\latest_run.json | ConvertFrom-Json
Invoke-Item -LiteralPath (Join-Path $r.directory 'relatorio.html')
```

O script lê os escores de desenvolvimento e grava a política antes de abrir o recorte reservado. O M10.2 não salvou as árvores: se a floresta for selecionada, o script reconstitui **só a floresta**, com a configuração e o ajuste originais, e exige que os escores e os disparos do desenvolvimento coincidam antes de liberar o teste. Nenhum código é ajustado com dados de 2011–2013. Não há download, instalação ou Docker. Sem `--autoria`, usa-se o código de referência; para a entrega basta a sua execução autoral.

Se a sua execução M10.2 estiver em outra pasta válida, passe `--run-dir` apontando para a pasta que contém o recibo e os escores, sem renomear o run. Exemplo: `--run-dir "D:\P2\reports\m10_2\20261119T101049Z_253ff59f"`.

## 4. Devolva a função e as três respostas

Cole `iniciar_alarmes` e responda ao [modelo de devolutiva](m10_3/Resposta_M10_3.md). Pode responder direto no chat. O trabalho se fecha com **regra causal correta + interpretação da exposição, dos IDs e do atraso + decisão defensável diante do teste**. Se sua tabela divergir, inclua só o `resultado.json` do M10.3 e a saída do terminal; não repita o M10.2.

No relatório, a primeira seção compara desenvolvimento e teste. `politica_congelada.json` registra a decisão escolhida no desenvolvimento. `candidatos_dev.csv` registra as tentativas anteriores ao teste. `eventos_teste.csv` distingue perdidos de não observáveis; `escores_teste.csv.gz` permite confirmar se o limiar realmente foi atingido. Todos ficam em `C:\renewable-forecast-lab\satellite-anomaly-monitor\reports\m10_3\<run_id>`.

**A continuação é M10.4:** diagnóstico de estabilidade, análise por canal e ablação. Se a política falhar no teste, M10.3 ainda cumpre seu objetivo: a avaliação delimitou o que a regra pode sustentar. Use esse achado para propor um experimento; não altere o limiar para ganhar pontos no mesmo teste.
