# M11.2 — Relatórios que precisam bater com a evidência

**Pergunta:** colocar um exemplo de JSON no prompt ajuda o modelo a obedecer ao formato e a preservar os dados? O seu ensaio anterior mostrou `ELIGIBLE` no formato certo para um caso `ISOLATED`. Aqui cada uma dessas verificações ganha sua própria métrica.

Este complemento acrescenta arquivos ao mesmo `operations-evidence-assistant` da M11.1. Reaproveita o SmolLM2 FP32 e o cache dos pesos. O lançador confere o ambiente usado naquela rodada e, se faltar a versão do Pydantic, instala apenas o validador em um cache privado. Não precisa alterar o Conda. O laboratório compara 2 prompts × 6 casos de desenvolvimento e congela um para rodar em outros 6 casos sintéticos. As inferências em CPU levam alguns minutos, conforme seu computador.

## 1. Extraia e abra o roteiro

Salve `rodada_m11_2_relatorios.zip` em `C:\renewable-forecast-lab`, onde a M11.1 já foi extraída.

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\rodada_m11_2_relatorios.zip -DestinationPath . -ErrorAction Stop
Invoke-Item .\operations-evidence-assistant\docs\COMECE_M11_2.md
```

| Aula | O que você aprende a verificar | O que inspecionar |
| --- | --- | --- |
| [01. JSON e esquema](m11_2/Aula_01_JSON_e_Esquema.md) | Separar sintaxe, campos faltantes, tipos e valores conformes. | `esquema.json`, `contraprovas.json` |
| [02. Conferência com a fonte](m11_2/Aula_02_Fidelidade_e_Fallback.md) | Comparar decimais sem arredondamento e exigir citações que sustentem a razão. | Sua função, `tentativas.jsonl` |
| [03. Experimento e decisão](m11_2/Aula_03_Experimento_e_Decisao.md) | Comparar prompts na mesma coorte, reservar casos e contar o fallback à parte. | `metricas.csv`, `decisao_prompt.json`, `relatorio.html` |

A [revisão da M11.1](m11_2/Revisao_M11_1_Windows.md) usa sua execução Windows. O relatório de referência desta rodada, com o reservado somente em agregado, está em [evidencias_m11_2](evidencias_m11_2/relatorio.html).

## 2. Implemente uma função

Abra `C:\renewable-forecast-lab\operations-evidence-assistant\notebooks\m11_2_fidelidade_autoral.py`. Implemente `conferir_fidelidade(candidato, esperado)`. Os dois dicts já passaram pelo contrato. O primeiro veio do LLM; o segundo foi calculado em Python pela fonte. Sua função devolve **todos** os erros em uma lista de strings sem duplicatas (ordem livre). Não altere as entradas nem gere um novo relatório. Use `Decimal` e conjuntos ou contagens.

| Divergência | Código a devolver |
| --- | --- |
| ID diferente | `id_divergente` |
| Classe diferente | `classe_divergente` |
| Um número mudou (incluindo trocar um nulo por zero) | `numero_divergente:<campo>`, para `cutoff`, `s1` e/ou `s2` |
| Razão diferente da sustentada pela fonte | `razao_sem_suporte` |
| Uma referência repetida | `citacao_repetida` |
| Referência exigida ausente | `citacao_ausente:<campo>` |
| Referência que não sustenta a razão neste contrato | `citacao_extra:<campo>` |

Ordem de `refs` não conta. `"0.700"` e `"0.70"` são equivalentes em valor; a publicação conserva o texto original da fonte. `null` só coincide com `null`. Se tudo confere, devolva `[]`. A Aula 02 trabalha um caso inteiro.

## 3. Execute

Para checar suas contraprovas sem carregar o LLM:

```powershell
python .\operations-evidence-assistant\scripts\executar_m11_2.py --autoria .\operations-evidence-assistant\notebooks\m11_2_fidelidade_autoral.py --verificar
```

Depois rode o mesmo comando sem `--verificar`:

```powershell
python .\operations-evidence-assistant\scripts\executar_m11_2.py --autoria .\operations-evidence-assistant\notebooks\m11_2_fidelidade_autoral.py
```

O programa mostra o andamento por caso e imprime a saída em `C:\renewable-forecast-lab\operations-evidence-assistant\reports\m11_2\<run_id>`. Abra o `relatorio.html` dessa execução. O modo completo seleciona e avalia automaticamente: deixe o reservado fechado enquanto estiver ajustando o desenvolvimento. Se a mensagem indicar ambiente M11.1 ausente, o lançador aceita `--preparar-ambiente` para repor o Python privado sem mexer no Conda.

## 4. Entregue para avançar

Devolva a função, o **novo** `resultado.json` (`autor_sha256` preenchido), `metricas.csv` e as três respostas de [Resposta_M11_2.md](m11_2/Resposta_M11_2.md). Acertar o laboratório exige explicar pelo menos um erro de conteúdo e usar a contagem de candidatos brutos, antes do fallback. Não é preciso montar um ZIP. Na M11.3, aproveitaremos o contrato para comparar prompting com adaptação dos pesos.
