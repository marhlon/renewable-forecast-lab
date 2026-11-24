# Aula 01 — Do pico à confirmação

Seu 0/8 da M10.3 tem uma explicação lógica imediata: o ponto mais alto de 2011–2013 foi **0,716436**; o corte era **0,719944**. Nenhum ponto passou. Isso responde à pergunta “por onde começar?”: trocar duas leituras por uma não criaria sinal nessa política. Ainda falta entender por que o escore perdeu capacidade de separar os períodos.

Agora suponha que o máximo tivesse passado. Dois picos separados por uma lacuna confirmam o quê? Nada. Para distinguir um pico de uma sequência, considere uma janela com k posições consecutivas da **grade**, todas utilizáveis. Com corte L, ela confirma se todos os escores são pelo menos L. Isso equivale a dizer que o menor escore da janela é pelo menos L. A janela que melhor consegue sustentar um limiar é a que tem **o maior desses mínimos**:

```text
S_k = máximo, entre janelas utilizáveis de comprimento k, do mínimo de cada janela.
```

Numa partição inteira, se não há janela válida ou se `S_k < L`, não existe nenhum início de alarme para esse corte e k. Se `S_k >= L`, pelo menos uma sequência global confirma; o primeiro início é a primeira confirmação naquela sequência. Para um ID isolado a interpretação muda: o início pode ter ocorrido antes de seu intervalo, ou o crédito pode ir a outro ID.

### Conta guiada

Use o mesmo exemplo da sua resposta M10.3. Escores: `[.70, .80, .90, .95, .88, .89, .65, .71, .71]`. A posição 3 é inválida mesmo com escore .95:

| Par consecutivo | Pode entrar? | Mínimo |
| --- | --- | ---: |
| 0–1 | Sim | 0,70 |
| 1–2 | Sim | 0,80 |
| 2–3 e 3–4 | Não: lacuna | — |
| 4–5 | Sim | **0,88** |
| 5–6 e 6–7 | Sim | 0,65 |
| 7–8 | Sim | 0,71 |

Resultado para `k=2`: `{"limiar_maximo": 0.88, "indice_confirmacao": 5}`. Para `k=1`, `S1 = .90`, na posição 2. Retirar o índice 3 da série criaria um par artificial entre os índices originais 2 e 4. Neste caso o mínimo dele seria .88, mas o horário do melhor par passaria incorretamente de 5 para 4. Manter a grade importa mesmo quando o número final coincide.

No programa, percorra os possíveis **índices finais** de `k-1` até o fim. Na fatia de k posições conte somente se todas estão utilizáveis, tire o mínimo e troque a janela campeã apenas se o valor for **estritamente maior**. Em empate mantém-se o primeiro fim. Não inicialize o melhor mínimo em zero: o contrato admite escores negativos. Não zere ou preencha lacunas. No caso `k > len(escores)` não existe janela candidata; retorne os dois campos como `None`. O laço simples custa O(nk) e resolve a tarefa com k=1 ou 2. Uma deque monotônica reduz o custo para O(n) quando for necessário escalar k.

### Leitura real

| Mesma floresta e mesmo corte | S1: máximo utilizável | S2: melhor mínimo de dois |
| --- | ---: | ---: |
| 2008–2010 | 0,759400 | 0,759400 |
| 2011–2013 | 0,716436 | 0,638230 |

A margem do melhor par posterior para o corte é de aproximadamente **−0,081715**. A diferença do pico para o corte é só **−0,003508**; olhar apenas o pico subestimaria a distância da regra de dois pontos. A coluna `s2_no_id` usa somente janelas contidas nos slots avaliáveis anotados para aquele ID. Ela é um diagnóstico de alcance, não uma promessa de detecção. Exemplo: para `[.8,.9,.95,.97]`, corte .8 e k=2, o alarme inicia no índice 1. Um ID que começa no índice 2 tem S2=.95 dentro dele e ainda assim não recebe novo início.

Use `--verificar` para receber a primeira contraprova que divergir. O laboratório também compara sua saída com o cálculo de referência em cada grade, ano e ID.
