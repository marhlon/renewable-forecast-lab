# M05.1 — Da pinball à calibração temporal dos intervalos

Marlon Alves Bomfim · 02/10/2026 · prática ligada às evidências E55/E56

**Entrega desta prática:** comparar os limites originais e corrigidos das mesmas previsões, explicar o custo em largura e identificar quando a correção aprendida no passado falha na semana seguinte. O objetivo nominal é cobertura de 80%. A mediana não muda nesta intervenção.

## O que sua inspeção já demonstrou

Seu cálculo manual coincide com as quatro métricas de cada método. A média pinball do HGB é 8,0771513557, contra 10,4513977745 da referência. Sua explicação distingue corretamente frequência de erros e magnitude dos desvios.

Três ajustes na interpretação:

1. **10% é uma probabilidade nominal, não uma contagem exata obrigatória em cada amostra.** Em 504 previsões, 10% seriam 50,4 observações. Mesmo um quantil correto pode apresentar variação amostral; empates também afetam as proporções. Isso não torna irrelevante o resultado observado: 152/504 acima do P90 e a variação por semana precisam de investigação.
2. **Os três HGB são ajustados separadamente.** O código minimiza a pinball de cada nível; não contém uma função conjunta que mande comprimir a largura P90−P10. Sob distribuição contínua, para uma previsão constante q, a derivada da perda esperada é F(q)−τ. Seu ponto de mínimo satisfaz F(q)=τ. Portanto, a perda foi construída para estimar quantis; ela não prefere intrinsecamente quantis descalibrados. Limitações do modelo, regularização, amostra finita e mudança de distribuição podem impedir que a estimativa tenha boa cobertura fora do treino. Estes resultados não isolam qual mecanismo causou a falha.
3. **Recalibração é uma intervenção a avaliar.** Não é obrigatória para todo modelo quantílico, nem promete exatamente 80% em cada semana. A garantia clássica da CQR é marginal e depende de hipóteses, incluindo intercambialidade. Ordenar temporalmente as partições evita certos vazamentos, mas não estabelece essa hipótese numa série dependente.

A decomposição abaixo usa suas 504 previsões por método, sem novo ajuste:

| P90: quantidade observada | HGB com vento | Persistência + resíduos |
|---|---:|---:|
| Alvos acima do P90 | 152 | 30 |
| Excesso médio apenas nesses casos, MWmed | 14,9575 | 26,8818 |
| Folga média apenas nos demais casos, MWmed | 35,5239 | 84,6134 |
| Contribuição dos estouros à pinball média | 4,0599 | 1,4401 |
| Contribuição das folgas à pinball média | 2,4810 | 7,9577 |
| Pinball P90: soma das duas contribuições | **6,5409** | **9,3978** |

As contribuições dividem pela amostra inteira: `0.9 * sum(max(y-p90, 0)) / 504` e `0.1 * sum(max(p90-y, 0)) / 504`. Aqui, a redução do custo das folgas superou o aumento do custo dos estouros. Essa é a explicação sustentada pelos números; não permite atribuir uma intenção ao otimizador.

## Como vamos calibrar

Vamos executar nove ajustes HGB, três níveis por fold, preservando as 32 entradas e os parâmetros anteriores. A janela de calibração de 48 horas foi fixada antes de observar os resultados desta intervenção: é uma escolha de piloto que conserva algum treino no primeiro fold. É curta e não foi demonstrada como ótima ou suficiente para operação.

| Fold | Linhas para ajustar HGB | Linhas para calibrar | Linhas para avaliar |
|---|---:|---:|---:|
| 1 | 140 | 48 | 168 |
| 2 | 308 | 48 | 168 |
| 3 | 476 | 48 | 168 |

Os relógios obedecem a duas regras estritas:

```text
max(target_available_at do treino) < primeira origem da calibração
max(target_available_at da calibração) < primeira origem da avaliação
```

Para h24 com atraso de duas horas, ficam 26 linhas de intervalo entre os conjuntos em cada fronteira. Por exemplo, no Fold 1, o último rótulo de treino chega em 08/07 às 03 UTC, antes da primeira emissão de calibração às 04 UTC. O último rótulo de calibração chega em 11/07 às 05 UTC, antes da avaliação às 06 UTC.

Na calibração, medimos quanto cada alvo ficou fora dos limites:

```python
score = max(base_p10 - y, y - base_p90, 0)
```

Um alvo dentro do intervalo recebe escore zero. Um alvo fora recebe a distância até a borda mais próxima. O zero é uma escolha explícita: esta variante apenas expande, enquanto a formulação original da CQR também pode produzir correção negativa e estreitar um intervalo.

Ordenamos os 48 escores e selecionamos o de posição:

```python
k = ceil((48 + 1) * (1 - 0.20))  # 40
correcao = escores_ordenados[k - 1]
```

É o **40º menor escore**, sem interpolação. O padrão de `np.quantile(scores, 0.8)` não implementa automaticamente essa regra de posição.

Aplicação à semana seguinte:

```python
lower_80 = max(0, base_p10 - correcao)
upper_80 = base_p90 + correcao
p50 = base_p50
```

Os modelos permanecem os mesmos entre calibração e avaliação: **não há refit após calcular a correção**. A correção fica fixa durante a semana; as features de cada emissão seguem sua disponibilidade temporal. Os alvos dessa semana servem somente para avaliar aquela previsão. Em folds posteriores, observações anteriores podem entrar no treino quando já estiverem disponíveis.

Os novos nomes são `lower_80` e `upper_80`: a intervenção busca a cobertura do intervalo central. Não impõe 10% de erros em cada cauda nem comprova que os limites sejam quantis condicionais P10/P90 bem calibrados.

## Onde colocar e como executar

Baixe `renewcast_m05_calibracao_temporal_20261002.zip` e coloque-o em `C:\renewable-forecast-lab`. No PowerShell, dentro dessa pasta e com o ambiente `renewable-forecast` ativo, execute:

```powershell
Expand-Archive -LiteralPath .\renewcast_m05_calibracao_temporal_20261002.zip -DestinationPath . -Force
```

O ZIP contém o módulo novo em `src/renewable_forecast/weather_interval_calibration.py`, esta aula em `docs` e a referência do professor em `docs/evidencias_m05_calibracao_professor`. A entrada continua sendo o dataset h24 já montado. Não há instalação, coleta ou reconstrução de dados nesta prática.

```powershell
python -m renewable_forecast.weather_interval_calibration --input-dir data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development --output-dir reports/probabilistic/CJU_BA5EIGT/h24_d2_july_calibration_v1 --calibration-size-hours 48 --n-splits 3 --test-size-hours 168 --threads 2
```

O módulo recusa sobrescrever uma pasta de resultados não vazia. Se uma execução anterior concluiu, inspecione os arquivos existentes. Se precisar repetir, conserve a primeira execução e escolha explicitamente outro sufixo de saída.

| Arquivo na pasta de saída | O que permite auditar |
|---|---|
| `folds.csv` | Tamanhos, duas fronteiras de disponibilidade, posição k e correção |
| `calibration_scores.csv` | 144 casos usados para calcular as três correções |
| `predictions.csv` | 504 emissões por método; limites originais/corrigidos, mediana e alvos |
| `fold_metrics.csv` | Cobertura, duas caudas, largura, interval score e MAE por semana |
| `summary.csv` | As mesmas métricas no conjunto das 504 emissões |
| `protocol.json` | Parâmetros, regra de seleção, hipóteses, versões e identidade da entrada |
| `metadata.json` | Contagens e hashes dos arquivos gerados |

## Referência já executada pelo professor

Execução sobre seu `model_frame.csv` de 744 linhas, hash `d142dbaf75a0e18fb203b77dfea8d8377c6d3b1d2c9fc1fc5908b1a50a9a6635`. Ambiente: Python 3.12.14, scikit-learn 1.8.0, NumPy 2.3.5 e pandas 2.2.3. As versões do seu ambiente são diferentes; seus valores numéricos podem diferir. Os tamanhos e as regras temporais devem coincidir.

| Métrica agregada | HGB sem correção | Mesmo HGB com expansão |
|---|---:|---:|
| Cobertura | 57,14% | 79,37% |
| Abaixo do limite inferior | 13,29% | 3,57% |
| Acima do limite superior | 29,56% | 17,06% |
| Largura média, MWmed | 60,7609 | 88,8669 |
| Interval score 80%, menor é melhor | 125,5090 | 117,5757 |
| MAE da mediana, MWmed | 27,0997 | 27,0997 |

| Fold | Correção, MWmed | Cobertura antes | Cobertura depois |
|---|---:|---:|---:|
| 1 | 19,6940 | 48,81% | 88,10% |
| 2 | 0,0000 | 67,26% | 67,26% |
| 3 | 22,4651 | 55,36% | 82,74% |

O ganho em cobertura teve custo em largura. O interval score penaliza tanto a largura quanto as distâncias fora da faixa; sua melhora indica que, neste recorte, a troca foi favorável segundo essa métrica. A mediana não muda porque a intervenção não a altera.

O Fold 2 expõe o limite do procedimento: 40 dos 48 escores de calibração eram zero. O 40º escore, portanto, produz expansão zero. A cobertura posterior de 67,26% mostra que o desempenho dessas 48 horas não se transferiu integralmente para a semana seguinte. Isso não identifica sozinho a causa da mudança.

**Não compare a cobertura original desta execução diretamente com os 55,36% anteriores como se a única mudança fosse a calibração.** Antes, o HGB usava 214/382/550 linhas de treino; agora usa 140/308/476. A comparação que isola a correção está entre as duas linhas do resumo desta execução.

Conferências do professor: as duas fronteiras temporais; recomposição dos escores e do 40º valor; métricas por cálculo independente; igualdade das medianas; expansão dos limites; hashes. Alterar os alvos da avaliação do primeiro fold para 100.000 manteve suas previsões e sua correção, confirmando que esses alvos não são usados para produzi-las. A helper de splits foi reconstruída a partir do código já fornecido pelo aluno; o projeto Windows completo não foi acessado.

## Sua implementação autoral

Crie `C:\renewable-forecast-lab\notebooks\inspecao_calibracao.py`, usando como entrada a pasta `reports/probabilistic/CJU_BA5EIGT/h24_d2_july_calibration_v1`.

Implemente **`correcao_manual(scores, alpha=0.2)`**, sem importar a função do módulo e sem `np.quantile`. Valide vetor finito, não vazio e não negativo; calcule k com `ceil`, ordene, selecione a posição correspondente e devolva `(correcao, k)`. Se k exceder o tamanho, recuse o cálculo finito.

No script:

1. Leia `calibration_scores.csv` e `folds.csv`.
2. Agrupe por `fold` e recalcule a correção. Confira k e correção contra `folds.csv` com `np.testing.assert_allclose`.
3. Exiba `fold`, `n_calibration`, `zero_scores`, `rank_k`, `manual_expansion`, `reported_expansion`.
4. Converta as quatro colunas de fronteira em timestamps UTC e confirme as duas desigualdades de disponibilidade.
5. Leia `fold_metrics.csv` e explique o fold com menor cobertura após a intervenção: o que a calibração viu e o que ocorreu depois? Se sua execução diferir da referência, use os seus números.

Execute:

```powershell
python notebooks/inspecao_calibracao.py
```

Entregue a função, sua tabela de conferência e os relatórios da execução. A decisão a defender é: **a melhora agregada basta para publicar o intervalo como risco operacional calibrado?** Sustente sua resposta com cobertura semanal, caudas e largura; não apenas com proximidade agregada a 80%.

## Fixação léxica aplicada

| Termo | Operação que você acabou de usar | Frase para recuperar sem consultar |
|---|---|---|
| Quantil | Ajuste de uma função para um nível τ | “P90 define um nível probabilístico; sua estimativa precisa de avaliação.” |
| Pinball | Média de distâncias com pesos assimétricos | “A perda depende de quanto errei e de qual lado.” |
| Cobertura | Contagem de alvos dentro dos limites | “Cobertura não mede o tamanho do estouro.” |
| Escore de não conformidade | Distância do alvo para fora da faixa | “Escore zero significa alvo contido nesta variante.” |
| Estatística de ordem | Seleção do 40º menor entre 48 escores | “Posição inteira não é interpolação.” |
| Calibração | Correção calculada num período separado | “Não posso usar o resultado futuro para corrigir sua própria previsão.” |
| Interval score | Largura mais penalização de alvos fora | “Alargar pode melhorar cobertura e ainda piorar a utilidade.” |

Na próxima sessão, recupere de memória o significado de **escore**, **posição** e **duas fronteiras temporais**, apontando a coluna que comprova cada um. Após esta prática, o próximo avanço é a previsão probabilística de eventos de rampa; mudanças adaptativas da calibração exigirão protocolo próprio, sem varrer janelas até embelezar julho.

Referência primária: Romano, Patterson e Candès, [Conformalized Quantile Regression](https://arxiv.org/pdf/1905.03222). Esta aula adapta a correção para expansão não negativa e avaliação cronológica empírica; não transfere automaticamente a garantia teórica para a série do projeto.
