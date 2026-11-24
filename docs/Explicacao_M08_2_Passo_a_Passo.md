# M08.2: dos horários aos lotes, e dos lotes à avaliação

Esta unidade transforma medições horárias em exemplos temporais, treina uma MLP pequena e compara seus checkpoints com referências simples. A função de avaliação e este guia foram implementados com assistência do Codex, a pedido de Marlon A. Bomfim. A conferência comprova comportamento nos casos verificados, sem certificar autoria independente. Os resultados Windows e a decisão experimental ficam no [parecer](../reports/parecer_m08_mlp.md); os números de referência Linux da aula não são apresentados aqui como execução Windows.

## 1. Qual informação entra em uma previsão

Uma origem `o` é o horário em que se emite a previsão. O atraso assumido de duas horas permite usar, no máximo, a medição de `o−2h`. Uma janela de 24 medições consecutivas vai de **`o−25h` até `o−2h`**, inclusive. O alvo é a geração em `o+24h`; sob a hipótese de disponibilidade, seu rótulo chega em `o+26h`.

Na primeira origem de avaliação da aula:

| Elemento | Horário no eixo sem fuso preservado da entrada |
|---|---|
| Origem | 03/07/2026 04h |
| Primeira medição da janela | 02/07/2026 03h |
| Última medição da janela | 03/07/2026 02h |
| Alvo | 04/07/2026 04h |
| Disponibilidade do alvo | 04/07/2026 06h |

`montar_janelas` procura cada horário explicitamente com `reindex`. Não pega simplesmente as últimas 24 linhas existentes: uma hora ausente precisa continuar ausente. Janelas sem valores finitos são excluídas, sem imputação. O laboratório também verifica arquivos, hashes, grade horária e fronteiras temporais antes do treino.

## 2. Por que há três conjuntos temporais

O ajuste aprende pesos e escalas; a seleção escolhe a época; a avaliação mede os checkpoints depois dessa escolha. Escolher a época pela própria semana de avaliação deixaria essa semana influenciar o modelo.

| Papel | Quantidade | Uso |
|---|---:|---|
| Ajuste | 7.079 | Pesos e padronização |
| Seleção | 168 | Melhor época de cada semente |
| Avaliação | 168 | Comparação dos checkpoints e referências |
| Exclusão por disponibilidade | 52 | Dois intervalos de 26 origens entre os papéis |
| Histórico inicial insuficiente | 18 | Sem janela completa de 24 horas |

A soma é 7.485. A divisão exige que o rótulo esteja disponível **antes** da fronteira seguinte: igualdade fica excluída. O último rótulo de ajuste chega em 25/06 às 01h, antes da seleção às 02h; o último de seleção chega em 03/07 às 03h, antes da avaliação às 04h.

Médias e desvios são calculados somente nas janelas de ajuste, separadamente para cada uma das 24 posições. O alvo também usa apenas o ajuste. Seleção e avaliação reutilizam essas escalas. Assim, informação dos períodos seguintes não participa da estimativa da padronização. A previsão retorna a MWmed antes das métricas.

## 3. O trabalho do Dataset e do DataLoader

`JanelasDataset.__len__()` informa a quantidade de exemplos. `__getitem__(i)` devolve a janela e o alvo de uma origem. Uma janela tem shape `[24,1]`: 24 instantes e uma variável, a geração. O alvo tem shape `[1]`.

O `DataLoader` reúne exemplos:

| Objeto | Shape de um lote completo |
|---|---|
| Entradas | `[128,24,1]` |
| Alvos | `[128,1]` |
| Previsões | `[128,1]` |

Como `7079 = 55×128 + 39`, o ajuste tem 56 lotes por época e o último contém 39 exemplos. Seleção e avaliação têm lotes de 128 e 40. `drop_last=False` mantém esses lotes menores. O funcionamento de índices, lotes e opções está na [documentação de dados do PyTorch 2.7](https://docs.pytorch.org/docs/2.7/data.html).

Somente o ajuste usa `shuffle=True`, depois da divisão temporal. Isso muda a ordem das origens de ajuste, preservando os 24 horários dentro de cada janela e os papéis de cada conjunto. A MLP não transporta estado entre janelas. Embaralhar também não elimina a dependência temporal: janelas vizinhas compartilham medições.

`num_workers=0` mantém a leitura no processo principal. Os dois threads configurados para operações do PyTorch são outro recurso; não significam dois processos de leitura.

## 4. Como a rede transforma uma janela em um número

A rede recebe o lote, achata cada janela e aplica:

| Etapa | Transformação | Parâmetros aprendidos |
|---|---|---:|
| `Flatten(start_dim=1)` | `[B,24,1] → [B,24]` | 0 |
| `Linear(24,32)` | `[B,24] → [B,32]` | 800 |
| `ReLU` | `[B,32] → [B,32]` | 0 |
| `Dropout(0.1)` | `[B,32] → [B,32]` | 0 |
| `Linear(32,1)` | `[B,32] → [B,1]` | 33 |

São **833 parâmetros**. `start_dim=1` conserva a dimensão do lote. A ReLU substitui valores negativos por zero, permitindo respostas não lineares; sem ela, a composição das duas camadas afins continuaria afim.

Durante o treino, Dropout zera ativações aleatoriamente com probabilidade 0,1 e reescala as restantes. Na avaliação ele funciona como identidade, conforme a [documentação do Dropout 2.7](https://docs.pytorch.org/docs/2.7/generated/torch.nn.Dropout.html). A rede usa `float32`. A referência linear recebe as mesmas 24 entradas e possui 25 parâmetros com intercepto; é ajustada por mínimos quadrados nas mesmas linhas de ajuste.

## 5. O que acontece em cada época

Cada lote executa o percurso já conhecido:

```python
optimizer.zero_grad(set_to_none=True)
previsao = modelo(x)
perda = (previsao - y).square().mean()
perda.backward()
optimizer.step()
```

Uma época percorre todos os exemplos de ajuste. `zero_grad` limpa derivadas anteriores, `backward` calcula novas derivadas e `step` atualiza os parâmetros. Aqui o otimizador é AdamW, com taxa `0.001` e decaimento de pesos `0.0001`. Ele usa estatísticas dos gradientes e decaimento separado dessa atualização, como registra a [documentação do AdamW 2.7](https://docs.pytorch.org/docs/2.7/generated/torch.optim.AdamW.html).

O limite de taxa calculado em M08.1 descrevia SGD de lote completo numa quadrática. Não pode ser transferido para esta rede não linear com AdamW e minilotes. Dropout e decaimento podem ajudar a controlar o ajuste, mas esta unidade não isola seu benefício em experimentos separados.

## 6. Como a melhor época é preservada

O protocolo fixa as sementes **17, 29 e 41**, até 60 épocas por semente e paciência de oito épocas. Ao fim de cada época, o programa avalia ajuste e seleção com pesos fixos e Dropout desativado.

Se o MSE de seleção melhora estritamente, guarda uma cópia do `state_dict` e zera a contagem de espera. Caso contrário, aumenta essa contagem. O treino para após oito épocas consecutivas sem melhora ou ao atingir 60; empates conservam a primeira época. Depois restaura o melhor checkpoint, sem novo ajuste.

Cada semente tem seu checkpoint. A semana de avaliação é consultada depois que os três estão escolhidos. Não se escolhe somente a melhor semente pelo resultado dessa semana. Sementes fixas ajudam a repetir o procedimento, sem garantir identidade bit a bit entre plataformas.

## 7. A função que foi implementada

[m08_avaliacao_autoral.py](../notebooks/m08_avaliacao_autoral.py) implementa `avaliar_lotes(modelo, loader)`. A ideia é guardar somente duas quantidades: soma dos erros quadráticos, ou SSE, e total de exemplos.

```python
residuo = (previsao - y).to(dtype=torch.float64)
soma_quadrados += residuo.square().sum().item()
total_exemplos += y.shape[0]
# Ao terminar:
return {"rows": total_exemplos, "mse": soma_quadrados / total_exemplos}
```

O algoritmo percorre um lote de cada vez, sem acumular todos os tensores numa lista. A conversão para `float64` ocorre antes do quadrado e da soma, favorecendo a precisão da acumulação. Ela não recalcula a rede ou a subtração anterior em `float64`.

Considere quatro exemplos com erro zero e um último com erro 10. Os lotes têm MSE 0 e 100. Fazer `(0+100)/2` produz **50**, dando ao exemplo isolado o mesmo peso dos outros quatro juntos. O cálculo correto é:

```text
SSE = 0 + 100 = 100
n = 4 + 1 = 5
MSE = 100 / 5 = 20
```

Esse detalhe pode mudar qual época parece melhor. O denominador precisa contar exemplos, não lotes.

## 8. Avaliar sem deixar efeitos no treino

`modelo.eval()` desativa comportamentos de treino, como Dropout. Não desativa a diferenciação. `torch.no_grad()` evita registrar o grafo dessas operações; sozinho, não desativa Dropout. Por isso o avaliador usa ambos. A distinção faz parte da [API de módulos do PyTorch 2.7](https://docs.pytorch.org/docs/2.7/generated/torch.nn.Module.html#torch.nn.Module.eval).

Antes de avaliar, a função guarda a flag `training` de **cada módulo**, incluindo o principal. Dentro de `try`, chama `eval()` e percorre os lotes em `no_grad`. No `finally`, repõe individualmente as flags originais:

```python
for modulo, modo_anterior in modos_anteriores:
    modulo.training = modo_anterior
```

Isso preserva até configurações mistas: por exemplo, modelo em treino com um submódulo previamente em avaliação. Restaurar somente `modelo.train(modo_antigo)` mudaria os filhos recursivamente e perderia essa configuração.

O `finally` executa também quando há erro no loader, na previsão ou na validação. O contexto `no_grad` igualmente termina ao sair. A função não chama `backward`, `step` ou `zero_grad`, nem escreve nos pesos ou nos gradientes existentes.

## 9. Quais entradas são recusadas

O alvo deve ter shape `[B,1]`, e a previsão precisa ter exatamente o mesmo formato. Um alvo `[B]` poderia provocar broadcasting e uma matriz `[B,B]`, comparando cada previsão com vários alvos. O avaliador interrompe esse caso.

Também gera `ValueError` para resíduo não finito, SSE não finita ou loader sem exemplos. A verificação da SSE cobre inclusive um estouro no quadrado ou na soma. Todos esses caminhos passam pela restauração das flags.

A conferência integrada usa os cinco exemplos em lotes 4+1, exige MSE 20 e testa os modos iniciais treino/avaliação, gradiente previamente existente, pesos preservados e loader vazio. Com `--autoria`, a função é conferida **e usada nas avaliações de ajuste e seleção durante o treino**.

## 10. Como ler os arquivos e decidir

Em `curvas.csv`, `online_train_mse` combina erros durante atualizações, com pesos mudando e Dropout ativo. `fit_eval_mse` mede o ajuste ao fim da época, com pesos fixos e sem Dropout. `selection_mse` mede a seleção nessas mesmas condições. As duas últimas curvas permitem discutir a evolução fora do ajuste; seus conjuntos diferentes podem ter dificuldades diferentes.

`protocol.json` registra as regras; `particoes.csv` documenta os papéis temporais; `janelas_avaliacao.csv` permite reconstruir entradas. `summary.csv` e `predictions.csv` comparam os métodos nas mesmas origens. Checkpoints, hashes e `resultado.json` ajudam a conferir preservação e repetição.

A comparação controlada é **MLP 24h versus linear 24h nesta execução**. Comparar diretamente com o afim de M08.1 confundiria mudanças de arquitetura, entrada e ajuste. A faixa entre três sementes descreve sensibilidade ao treino; não é intervalo de confiança nem previsão de ensemble.

Mesmo um MAE menor precisa ser lido junto de RMSE, viés, variação entre sementes e custo. Viés observado menos previsto positivo indica subestimação média. A última semana já foi explorada: separar a seleção nesta execução não a transforma em teste final intocado. Esses resultados orientam a próxima investigação e não constituem aprovação operacional.

## 11. Como repetir e onde conferir esta entrega

No PowerShell, com o ambiente já instalado:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
python notebooks/laboratorio_mlp.py --autoria notebooks/m08_avaliacao_autoral.py
python -m unittest discover -s tests -p test_m08_avaliacao_autoral.py -v
```

Os oito testes adicionais passaram nesta entrega. Cobrem o lote menor, modos
mistos, restauração após falha, shapes inválidos, resíduos não finitos, estouro
da soma dos quadrados, loader vazio e preservação do contexto de gradientes.

O [gráfico das curvas autorais](../reports/neural/CJU_BA5EIGT/m08_2_mlp/curvas_autoria_20261105.png)
mostra ajuste e seleção com pesos fixos. A linha tracejada indica a época
restaurada em cada semente. As melhores épocas foram 8, 20 e 15; as paradas
ocorreram em 16, 28 e 23. O [parecer](../reports/parecer_m08_mlp.md) contém as
métricas Windows, os tempos medidos, a decisão e os links dos resultados.
