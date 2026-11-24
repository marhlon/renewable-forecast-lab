# Parecer M08.3 — recorrência e comparação nas mesmas origens

Execução de 15/11/2026 em Windows, Python 3.12.13, PyTorch 2.7.1+cpu,
NumPy 2.5.3, pandas 3.0.5 e scikit-learn 1.9.0. Foram usados dois threads
e redes float32. Os resultados abaixo pertencem à execução local
`20261115T170309Z_90a6625f`.

## Arquitetura e contrato temporal

A entrada `[B,24,1]` contém B origens, 24 medições ordenadas e uma variável.
A GRU processa cada janela com estado inicial zero e produz `hidden [1,B,16]`.
`hidden[-1]` seleciona a única camada final, preservando o lote `[B,16]`;
Dropout e cabeça linear geram `[B,1]`. Os 912 parâmetros recorrentes e os
17 da cabeça somam 929, contra 833 da MLP e 25 do linear.

A porta `r` controla a contribuição recorrente ao candidato, depois da
transformação afim, incluindo seu viés. A porta `z` combina candidato e
estado anterior: `h_novo=(1-z)*n+z*h`. Carregar esse estado entre lotes
embaralhados ligaria histórias de origens diferentes, tornando a previsão
dependente da ordem de processamento. O estado permanece dentro de cada janela.

A janela vai de `o−25h` a `o−2h`, com alvo em `o+24h` e disponibilidade
assumida em `o+26h`. Mantiveram-se 7.079 exemplos de ajuste, 168 de seleção,
168 de avaliação e exclusões de 52 por disponibilidade e 18 por contexto.
Normalização e parâmetros foram estimados somente no ajuste. O eixo temporal
continua sem fuso físico validado.

## Seleção e curvas

Cada rede usou AdamW, até 60 épocas e paciência oito. A tabela mostra a
época escolhida pelo menor MSE de seleção e a parada:

| Modelo | Semente | Melhor época | Parada | MSE de seleção: melhor → parada |
|---|---:|---:|---:|---:|
| MLP | 17 | 8 | 16 | 0,435417 → 0,461290 |
| MLP | 29 | 20 | 28 | 0,445700 → 0,460707 |
| MLP | 41 | 15 | 23 | 0,434813 → 0,440834 |
| GRU | 17 | 23 | 31 | 0,480804 → 0,490080 |
| GRU | 29 | 38 | 46 | 0,441596 → 0,451408 |
| GRU | 41 | 24 | 32 | 0,459523 → 0,488427 |

As curvas de ajuste e seleção são calculadas com pesos fixos e Dropout
desativado. Na GRU 41, o ajuste cai de 0,524985 para 0,518826 entre esses
pontos, enquanto a seleção piora. Na GRU 29, ambos pioram: o ajuste passa
de 0,514911 a 0,517896. A perda online mistura atualizações e Dropout ativo.
Restauraram-se os melhores checkpoints, sem refit; empates conservaram a
primeira época. Minimizar MSE numa semana anterior não garante menor MAE
na seguinte: são critérios e períodos diferentes.

## Resultados pareados e decisão

Todos os métodos usam as mesmas 168 origens; métricas em MWmed:

| Método | Semente | MAE | RMSE | Viés observado − previsto |
|---|---:|---:|---:|---:|
| Persistência d2 | — | 37,991646 | 55,434342 | −3,016872 |
| Linear 24h | — | 33,678664 | 44,938111 | +15,148681 |
| HGB 24h | 17 | 32,323956 | 44,221683 | +13,119039 |
| MLP | 17 | 32,724828 | 44,019866 | +10,655947 |
| MLP | 29 | 33,700811 | 44,892316 | +12,652757 |
| MLP | 41 | 33,159788 | 44,069511 | +13,724280 |
| GRU | 17 | 35,675970 | 45,200733 | +18,525120 |
| GRU | 29 | 34,911227 | 43,816199 | +17,993098 |
| GRU | 41 | 34,573202 | 43,066020 | +14,777710 |

O MAE mediano da MLP é 33,159788, com faixa 32,724828–33,700811;
na GRU, 34,911227, com faixa 34,573202–35,675970. São faixas entre sementes,
sem interpretação de intervalo de confiança ou ensemble. Todas foram
reportadas, sem escolher uma pela semana de avaliação.

O HGB recebe os mesmos 24 lags históricos, sem vento; não é o antigo
HGB+vento. Ele apresenta o menor MAE desta execução. As GRUs 29 e 41 têm
RMSE menor que o HGB, embora MAE maior. O quadrado aumenta o peso dos
erros grandes; a tabela agregada não identifica quais eventos explicam isso.
Todos os estimadores ajustados mantêm viés positivo, indicando subestimação média.

Adoto provisoriamente o HGB como referência pela métrica MAE. Seu ajuste
registrou 0,69 s, contra 0,005 s do linear, 29,00 s somados das três MLPs
e 210,12 s das três GRUs. Os tempos neurais incluem avaliações por época;
esta sequência não é benchmark controlado. O pico de 396,04 MiB pertence
ao processo inteiro. A complexidade recorrente e seu custo não trouxeram
ganho em MAE neste orçamento. O HGB continua com viés relevante.

Na referência Linux, o HGB tem MAE 31,846768 e scikit-learn 1.8.0.
Os hashes das entradas também diferem: os prefixos Windows/Linux são
`bf3a58b3`/`b286eb4f` para geração e `6ab1e8fc`/`0aabb682` para treino.
Os arquivos locais passaram contra seu próprio manifesto. Há diferenças
simultâneas de ambiente e artefatos; a causa da diferença preditiva não foi isolada.

Esta semana já foi examinada no desenvolvimento. A referência escolhida
precisa ser avaliada em novos períodos, com regras e métrica fixadas antes
de observá-los. A execução não autoriza promoção operacional.

## Evidências

A [função NumPy](../notebooks/m08_gru_autoral.py) passou na
[conferência separada](neural/CJU_BA5EIGT/m08_3_gru/20261115T170409Z_592111fa/conferencia_sem_treino.json):
11 grupos, diferença máxima `2,220446049250313e-16`, abaixo de `1e-12`.
Os cinco testes adicionais passaram; os seis recarregamentos tiveram diferença zero.
O treinamento permaneceu em GRU/autograd.

Os [resultados](neural/CJU_BA5EIGT/m08_3_gru/20261115T170309Z_90a6625f/resultado.json),
[resumo](neural/CJU_BA5EIGT/m08_3_gru/20261115T170309Z_90a6625f/summary.csv),
[curvas](neural/CJU_BA5EIGT/m08_3_gru/20261115T170309Z_90a6625f/curvas.png)
e [relatório HTML](neural/CJU_BA5EIGT/m08_3_gru/20261115T170309Z_90a6625f/relatorio.html)
sustentam esta leitura. O [guia](../docs/Explicacao_M08_3_Passo_a_Passo.md)
detalha os cálculos; a [verificação Linux](../docs/Verificacao_M08_3_Professor.md)
documenta a referência comparada.
