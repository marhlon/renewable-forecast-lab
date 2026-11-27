# Aula 02 — Escolher o próximo token, sem esconder a decisão

Em cada passo o modelo devolve um logit por ID. O logit é a pontuação ainda não normalizada para o próximo token **condicionado ao texto que já existe**. Greedy escolhe o de maior pontuação por passo. Isso não garante a sequência inteira mais provável; o token escolhido muda as alternativas do passo seguinte. O laboratório confere seis novos tokens do laço greedy manual com `generate` do Transformers, usando os mesmos IDs e máscara.

No primeiro passo, o modelo lê o prompt inteiro (*prefill*). Nos seguintes envia um token de cada vez e reutiliza as chaves e valores de atenção anteriores (*cache KV*). Ele para ao ver o token de fim (EOS) ou ao consumir o orçamento de saída. A execução usa teto local de 512 tokens, mesmo que a configuração do modelo permita mais. O teste de excesso mostra a soma **tokens do prompt + máximo de tokens novos** e recusa antes do primeiro forward. O modelo nunca recebe um pedaço truncado em silêncio.

## Temperatura e seleção top-k

Para logits `[-100, 1000, 999]` e `k=2`, os candidatos são os IDs 1 e 2, nessa ordem. Subtraia o maior logit antes de exponenciar. Com temperatura T, os pesos são:

```text
w1 = exp((1000 - 1000) / T)
w2 = exp(( 999 - 1000) / T)
p1 = w1 / (w1 + w2)
p2 = w2 / (w1 + w2)
```

| T | Prob. ID 1 | Prob. ID 2 | ID quando u=0,8 |
| ---: | ---: | ---: | ---: |
| 1,0 | 0,7311 | 0,2689 | 2 |
| 0,5 | 0,8808 | 0,1192 | 1 |

A uniforme `u` é um sorteio externo. Acumule as probabilidades e escolha o primeiro candidato cuja soma **excede** `u`. Na fronteira exata, a massa seguinte ganha: em `[0,0,0]`, `k=2`, `u=0,5`, entram IDs 0 e 1, com 0,5 cada; resultado ID 1. Candidatos fora do top-k têm probabilidade zero. Temperatura positiva muda concentração, não a ordem do top-k. `T=0` é fora do contrato; neste laboratório a rota greedy é separada.

## Sua função

Abra `C:\renewable-forecast-lab\operations-evidence-assistant\notebooks\m11_1_amostragem_autoral.py`. Substitua o corpo do esqueleto. Use `math.exp` (e opcionalmente `math.fsum`), `enumerate`, `sorted` e um laço. Não chame uma biblioteca de sampling e não gere a uniforme dentro da função.

- Assinatura: `selecionar_token_top_k(logits, *, temperatura, k, u)`. As entradas avaliadas são uma sequência 1D finita, `1 <= k <= len(logits)`, T finita positiva e `0 <= u < 1`. Retorne um `int` Python.
- Ordene por maior logit e, em empate, pelo menor ID. Selecione só os primeiros k. Os pesos são exponenciais depois de deslocar o máximo. Não altere as entradas.
- Acumular pesos brutos e comparar com `u * sum(pesos)` é equivalente a acumular probabilidades. Um peso que ficou zero por underflow não deve ganhar. Se o arredondamento deixar a massa exatamente na fronteira final, o último candidato com peso positivo é o fallback.
- O modo `--verificar` executa seis contas sem pesos. Na execução real, o laboratório passa seus logits e o mesmo `u` à sua função e à referência a cada passo amostrado. Os IDs, uniformes iniciais e alternativas dos dois primeiros passos são gravados.

## Leia duas mudanças diferentes

No caso `satmon_sem52`, compare o greedy de 6 e 36 tokens. Eles têm o mesmo prefixo quando a versão longa ainda não parou; o orçamento curto pode cortar a razão. Com amostragem, compare as sementes 17, 29 e 41 em T=0,35 e T=1,2. Para isolar o efeito do sorteio mantenha o mesmo caso, mesma precisão e top-k. Para isolar o efeito de T compare a mesma semente entre temperaturas.

O código escrito na primeira linha é avaliado contra uma regra exata. Uma razão fluente pode estar errada mesmo quando o código passa. Confira ambos; relatório fluente não torna um 0/8 em 8/8, e `ELIGIBLE` só significa que a sequência pode confirmar, sem crédito por ID.
