# Devolutiva M11.1

Execução Windows **`20261124T182345Z_2a298bc9`**, com SmolLM2-135M-Instruct,
revisão `12fd25f77366fa6b3b4b768ec3050bf629380bac`, em CPU com dois threads.
As respostas abaixo usam os arquivos desta rodada, não os tempos Linux da referência.

1. **Tokens e vetores.** Os probes 0 e 2 têm 29 caracteres, 31 bytes UTF-8 e **18 tokens**, com embeddings de shape `[1,18,576]`; na posição **10**, contando de zero, a vírgula de `0,719944` usa o **ID 28**, enquanto o ponto de `0.719944` usa o **ID 30**. Portanto a quantidade de tokens igual não significa sequência de IDs igual. Nas duas frases que terminam com `Status:`, o token final é `:`, **ID 42**: a diferença máxima entre os embeddings de entrada é **0**, mas entre os vetores após as camadas é **1,9337141513824463**. O lookup do mesmo ID fornece o mesmo vetor inicial, e as camadas acrescentam informação do prefixo; isso não comprova que a representação preserve uma comparação decimal exata. Por esse motivo, `s1`, `s2` e `cutoff` continuam como valores identificados no registro e são comparados em Python com `Decimal`, mantendo a precisão e a igualdade inclusiva do contrato; o LLM recebe a evidência para explicação, sem substituir essa regra.

2. **Decodificação e orçamento.** No caso `satmon_sem52`, o greedy FP32 de seis tokens produziu exatamente **`ELIGIBLE means the`** e parou por **`limite_novos_tokens`**, não por EOS; a geração longa manteve esse prefixo e também consumiu seu orçamento de 36 tokens. Mantendo caso, precisão FP32, `k=8` e semente **17**, a amostragem com **T=0,35** começou com a primeira linha `ELIGIBLE`, seguida de um registro incompleto: o código tem formato válido, mas está errado, pois `s1=0.7541511974686277` supera o corte `0.7201268845204545` e `s2=0.6915642216840697` fica abaixo dele, exigindo **`ISOLATED`**. Com **T=1,2**, a mesma semente começou com `The records that follow can be classified as follows:` e trouxe `1. "IsOLATED,"` depois; a primeira linha não cumpre o contrato. Ambas as amostras chegaram a 36 tokens, sem EOS. Há outro erro concreto no greedy INT8 de `satmon_tres_canais`: o texto inicia o campo `cutoff` com `0.7164359`, prefixo do pico `s1`, em vez do corte `0.7199442558330269`. Semente e temperatura controlam a escolha da continuação, não validam a regra ou a fidelidade dos campos; aumentar o orçamento também não garante diagnóstico correto.

3. **Custo e escolha de arquitetura.** O `state_dict` serializado caiu de **538.149.619 bytes (513,219470 MiB)** em FP32 para **219.806.563 bytes (209,623874 MiB)** com lineares INT8, redução de **59,1551%**; foram convertidas 210 lineares internas, mantendo embedding e cabeça de vocabulário em FP32. Nas três rodadas aquecidas do mesmo prompt de **239 tokens** e trajetória forçada de **17 tokens**, a mediana do tempo total foi **1.985,2231 ms** em FP32 e **1.604,8635 ms** em INT8, redução de **19,1595%**. Isso mede esse trabalho na CPU local, excluindo download, carga e conversão; tamanho serializado não mede RAM, e INT8 foi mais lento na primeira rodada. No CSV, cada precisão teve **0/6 códigos greedy válidos e 0/6 corretos** nos seis casos completos; as seis continuações pareadas mudaram, portanto igualdade de acertos no piso não demonstra preservação de qualidade. Na arquitetura, disponibilidade, validação numérica, comparação por `Decimal`, classe, orçamento e qualquer autorização permanecem em Python; o LLM pode redigir uma explicação revisável da decisão já calculada. Na M11.2, identificadores e números devem ser copiados da evidência, o JSON deve ser validado estruturalmente e seus campos e afirmações devem ser confrontados com o registro e a regra; JSON válido sozinho não detectaria a troca de `s1` por `cutoff`. Uma divergência deve impedir o uso da explicação e acionar uma resposta determinística, sem comandar equipamentos ou alterar alarmes.

## Arquivos da execução

- [Função top-k](../../notebooks/m11_1_amostragem_autoral.py)
- [resultado.json](../../reports/m11_1/20261124T182345Z_2a298bc9/resultado.json)
- [geracoes.csv](../../reports/m11_1/20261124T182345Z_2a298bc9/geracoes.csv)
- [benchmark.csv](../../reports/m11_1/20261124T182345Z_2a298bc9/benchmark.csv)
- [tokens.csv](../../reports/m11_1/20261124T182345Z_2a298bc9/tokens.csv) e [embeddings.json](../../reports/m11_1/20261124T182345Z_2a298bc9/embeddings.json)
- [Relatório HTML](../../reports/m11_1/20261124T182345Z_2a298bc9/relatorio.html)

Passaram **seis contraprovas**, **13 testes adicionais** e **216 escolhas
autorais comparadas com a referência sobre logits reais**. A escolha top-k
correta é uma evidência de implementação, não de correção das respostas do modelo.
Os seis casos são exploratórios; a parte textual não recebeu avaliação
automática completa e não houve treinamento ou aprovação operacional.

A [auditoria dos arquivos](../evidencias_m11_1_local/auditoria_resultados.json)
conferiu hashes, códigos, tokens, textos e medidas persistidas sem repetir
o modelo ou o benchmark. As 216 comparações completas de top-k são evidência
do runner: a trilha salva contém apenas os quatro maiores logits dos dois
primeiros passos e não permite reconstruir exatamente toda distribuição
top-8 ou todas as escolhas posteriores. Esse limite está registrado, sem
substituir a saída observada por uma avaliação mais ampla.
