# M11.1 — Operations Evidence Assistant: tokens, geração e custo

**Decisão da rodada:** um LLM pequeno em CPU consegue produzir um diagnóstico fiel a uma evidência? Onde ficaria a regra exata e onde caberia geração?

O P3 é uma pasta própria. Ele usa seis registros pequenos já empacotados: quatro evidências anteriores do Renewcast/SatMon e duas contraprovas ilustrativas. Nenhum modelo do P1 ou P2 é refeito. O laboratório executa SmolLM2-135M-Instruct, baixa os pesos públicos na primeira rodada (cerca de **259 MiB com o tokenizer**), verifica os arquivos com SHA-256 e depois gera tudo neste computador. Não precisa de chave, GPU, servidor, conta na nuvem ou API de geração.

## 1. Extraia o pacote

Salve `rodada_m11_1_geracao_local.zip` em `C:\renewable-forecast-lab`. Na raiz:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\rodada_m11_1_geracao_local.zip -DestinationPath . -ErrorAction Stop
Invoke-Item .\operations-evidence-assistant\docs\COMECE_M11_1.md
```

## 2. Estude e faça uma implementação

| Aula | Operação que você pratica | Evidência na sua saída |
| --- | --- | --- |
| [01. Tokens e embeddings](m11_1/Aula_01_Tokens_e_Embeddings.md) | Separar texto, IDs, vetor inicial e vetor contextual. | `tokens.csv`, `embeddings.json` |
| [02. Decodificação e orçamento](m11_1/Aula_02_Decodificacao_e_Orcamento.md) | Implementar e conferir uma escolha top-k, comparar sementes e limitar contexto. | `trilha_tokens.json`, `geracoes.csv` |
| [03. Quantização e decisão](m11_1/Aula_03_Quantizacao_e_Decisao.md) | Comparar tempo, tamanho dos pesos e fidelidade contra uma regra calculável. | `benchmark.csv` (quando suportado), `relatorio.html`, `resultado.json` |

Edite **somente** `C:\renewable-forecast-lab\operations-evidence-assistant\notebooks\m11_1_amostragem_autoral.py`. O arquivo existe no ZIP. Implemente `selecionar_token_top_k(logits, *, temperatura, k, u)`: ordene por logit, selecione k, calcule pesos estáveis e encontre o intervalo de `u`. A segunda aula mostra uma conta inteira e o tratamento de empate. A função não gera a semente nem decide o alarme.

Se quiser verificar sua função **antes do download**:

```powershell
python .\operations-evidence-assistant\scripts\executar_m11_1.py --autoria .\operations-evidence-assistant\notebooks\m11_1_amostragem_autoral.py --verificar
```

## 3. Rode uma vez com a autoria

```powershell
python .\operations-evidence-assistant\scripts\executar_m11_1.py --autoria .\operations-evidence-assistant\notebooks\m11_1_amostragem_autoral.py
```

O lançador procura primeiro o Python de `.venvs/m09_3_chronos`, criado na M09.3, com as versões fixadas; não o modifica. Se informar que o ambiente está ausente ou incompatível, repita **apenas o comando acima** com `--preparar-ambiente` ao final. Isso instala em `.venvs/m11_1_smol`, fora do Conda. Caso tenha recebido os sete arquivos oficiais do modelo por outro meio, `--model-dir` aponta para a pasta e faz a mesma verificação em modo de leitura. O cache padrão evita repetir downloads. A comparação mede INT8 se há backend CPU compatível; se indisponível, mantenha o recibo FP32 e registre a limitação na terceira resposta.

Quando terminar, abra o `relatorio.html` do caminho que o terminal imprimir. A saída fica em `C:\renewable-forecast-lab\operations-evidence-assistant\reports\m11_1\<run_id>`. Um código de saída 0 confirma que a execução produziu as evidências; até um modelo que erre todas as respostas pode completar o experimento. O [relatório de referência Linux](evidencias_m11_1/relatorio.html) e a [revisão da M10.4](m11_1/Revisao_M10_4.md) já estão no pacote.

## 4. Entregue para fechar M11.1

Devolva o `.py` editado, o **novo** `resultado.json` (o autoral preenche `author_sha256`) e `geracoes.csv` da pasta impressa. Responda às três questões de [Resposta_M11_1.md](m11_1/Resposta_M11_1.md), no arquivo ou no chat. A conferência exige a função funcionando no modelo, a leitura de uma saída errada e uma decisão sobre o que fica em Python. Para defender INT8, cite tamanho e tempo pareados, ou diga que faltou backend. O próximo passo, M11.2, é testar um relatório com contrato JSON, validação e avaliação de fidelidade.
