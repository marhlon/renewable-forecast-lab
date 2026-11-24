# M08.1: o que foi feito, passo a passo

Esta prática ajustou um modelo afim aos dados locais do Renewcast, conferiu suas derivadas e comparou duas taxas de aprendizagem. A função NumPy e esta explicação foram produzidas com assistência do Codex, a pedido de Marlon A. Bomfim. A concordância numérica comprova o funcionamento nos casos verificados; não certifica autoria independente.

## 1. O que o modelo recebe e tenta prever

Cada linha representa uma origem de previsão. O modelo recebe duas informações históricas: `geracao_em_history_end`, a geração no último instante disponível, e `media_historico_mwmed`, a média das seis horas disponíveis. Com atraso assumido de duas horas, a origem das 03h usa a última medição da 01h e a janela das 20h do dia anterior à 01h do dia corrente.

O alvo é a geração 24 horas depois da origem. A regra do modelo é:

```text
previsão = primeira_feature × w1 + segunda_feature × w2 + b
```

Os dois pesos dizem quanto cada feature contribui. O intercepto `b` desloca todas as previsões. São três parâmetros aprendidos. Esta é uma função afim, sem camadas ocultas ou arquitetura profunda.

## 2. Como os dados foram separados

O laboratório verifica o hash do arquivo de treino contra o manifesto e confere o contrato temporal antes de ajustar parâmetros. As 7.485 linhas são ordenadas por origem e divididas assim:

| Destino | Linhas | Motivo |
|---|---:|---|
| Ajuste | 7.291 | O alvo já estaria disponível antes do início da validação |
| Exclusão da divisão | 26 | A origem é anterior, mas o alvo ainda não estaria disponível |
| Validação de desenvolvimento | 168 | As últimas 168 origens: uma semana |

A validação começa em 03/07/2026 às 04h. O último alvo do ajuste fica disponível às 03h. A regra é estrita: `target_available_at < início_da_validação`. Um alvo disponível exatamente às 04h fica fora do ajuste. Os horários preservam o eixo sem fuso da entrada; não foram convertidos implicitamente.

Depois da divisão, calculam-se média e desvio de cada feature **somente nas 7.291 linhas de ajuste**:

```text
valor_padronizado = (valor_original − média_do_ajuste) / desvio_do_ajuste
```

O alvo também é padronizado. Na validação aplicam-se as mesmas médias e desvios, sem recalculá-los. Usar a validação para estimar essas escalas deixaria informação do período de avaliação entrar no preparo do treino. Ao prever, a transformação inversa devolve o resultado a MWmed.

## 3. O que significam as dimensões

`Shape` é o formato do arranjo: quantas linhas, colunas ou eixos ele possui.

| Objeto | Shape no ajuste | Significado |
|---|---|---|
| `X` | `[7291, 2]` | Duas features em cada origem |
| `w` | `[2, 1]` | Um peso para cada feature |
| `b` | `[]` | Um número escalar |
| `X @ w + b` | `[7291, 1]` | Uma previsão por origem |
| `y` | `[7291, 1]` | Um alvo por origem |
| Perda | `[]` | Um número resumindo os erros |
| `dw` e `db` | `[2, 1]` e `[]` | Uma derivada por parâmetro |

O operador `@` faz a multiplicação matricial: `[n,2] @ [2,1] → [n,1]`. Somar o escalar `b` a cada linha é intencional.

## 4. Como a função NumPy calcula o gradiente

Em `notebooks/m08_gradiente_autoral.py`, `gradiente_mse` converte as entradas para NumPy `float64`, verifica seus formatos e rejeita um conjunto sem linhas. Não atualiza os dados nem os parâmetros recebidos. Seu cálculo central é:

```python
residuo = X @ w + b - y
fator = 2.0 / n
dw = fator * (X.T @ residuo)
db = float(fator * np.sum(residuo))
return dw, db
```

Definimos `resíduo = previsto − observado`. A perda MSE é a média dos resíduos ao quadrado: `L = soma(resíduo²)/n`. O quadrado penaliza erros positivos e negativos. Ao derivá-lo aparece o fator `2`; ao derivar a média permanece `1/n`. Daí vem `2/n`.

Para os pesos, cada resíduo é multiplicado pela feature correspondente e somado. `X.T` realiza essa soma para as duas features: `[2,n] @ [n,1] → [2,1]`. Para `b`, a contribuição de cada linha é simplesmente o resíduo, pois a derivada de `b` em relação a ele mesmo é 1.

## 5. Uma atualização feita à mão

Use duas linhas, `X=[[1,0],[0,1]]`, alvos `y=[[1],[2]]`, pesos zerados e `b=0`. As previsões iniciais são zero; os resíduos são −1 e −2. Assim:

```text
MSE = (1² + 2²)/2 = 2,5
dw = [[−1], [−2]]
db = −3
```

Com taxa `0,1`, subtraímos o gradiente:

```text
w_novo = [[0],[0]] - 0.1 * [[-1],[-2]] = [[0.1],[0.2]]
b_novo = 0 - 0.1 * (-3) = 0.3
```

O intercepto aumenta porque subtrair um número negativo produz um acréscimo. As previsões passam a 0,4 e 0,5. O novo MSE é `(0,6² + 1,5²)/2 = 1,305`. O gradiente indica como a perda varia; o passo usa essa informação para mudar os parâmetros.

## 6. O trabalho de cada comando do PyTorch

No treino, `requires_grad=True` permite registrar os cálculos que envolvem os parâmetros. Cada iteração calcula previsões e perda. `zero_grad(set_to_none=True)` limpa as derivadas anteriores; `backward()` calcula e acumula novas derivadas em `.grad`; `optimizer.step()` atualiza os parâmetros usando essas derivadas e a taxa. Sem a limpeza, duas passagens com os mesmos parâmetros somam os gradientes.

Na demonstração manual e na inferência, `torch.no_grad()` evita registrar operações para diferenciação. Isso não equivale a `model.eval()`, que trata comportamentos próprios de certos módulos. O modelo afim desta aula não contém Dropout ou BatchNorm. Esses mecanismos estão descritos na [documentação de autograd do PyTorch 2.7](https://docs.pytorch.org/docs/2.7/notes/autograd.html).

## 7. Como conferimos a matemática e evitamos um erro silencioso

A função NumPy aplica a fórmula derivada. O autograd percorre as operações registradas usando a regra da cadeia. As diferenças finitas aproximam cada derivada por `(L(θ+ε)−L(θ−ε))/(2ε)`, com `ε=10⁻⁶`. São caminhos distintos para conferir o mesmo resultado no caso manual e em oito linhas reais.

O comando `--autoria notebooks/m08_gradiente_autoral.py` carrega a função, compara os resultados e registra seu hash. **O treinamento segue com autograd e SGD do PyTorch**; a função NumPy participa da conferência.

Um cuidado decisivo é manter previsão e alvo com shape `[n,1]`. Com previsões `[[0.4],[0.5]]` e alvos `[1,2]`, a subtração mistura uma coluna `[2,1]` com um vetor `[2]` e produz:

```text
[[-0.6, -1.6],
 [-0.5, -1.5]]     # shape [2,2]
```

Cada previsão foi comparada com ambos os alvos. A comparação correta produz apenas `[[-0.6],[-1.5]]`, shape `[2,1]`. O laboratório rejeita esse erro antes de calcular o MSE. A expansão automática segue as [regras de broadcasting do PyTorch 2.7](https://docs.pytorch.org/docs/2.7/notes/broadcasting.html).

## 8. Por que comparamos as taxas 0,05 e 0,8

A taxa define o tamanho do passo. Para esta perda quadrática e este treino de lote completo, o limite estrito calculado é `0,5508169546468945`. A taxa `0,05` fica abaixo dele e é usada por 400 atualizações; `0,8` ultrapassa-o e é usada na contraprova de 30 atualizações.

Compare a coluna `fit_mse_standardized` dos dois `curva_treino.csv`: redução e aproximação do mínimo caracterizam o padrão; crescimento acentuado na contraprova indica instabilidade de otimização. No Windows, a taxa `0,8` terminou com perda de aproximadamente `1,7769 × 10¹⁶`, embora tenha retornado código 0 e `training_state="completed"`. Aqui, esse estado significa passos concluídos com perda finita. Esse limite vale para esta quadrática, não como regra universal para redes profundas.

O laboratório também resolve mínimos quadrados no mesmo ajuste. O pequeno gap do padrão para essa solução mostra que o otimizador praticamente resolveu o problema matemático proposto. Não garante que esse problema represente bem o futuro.

## 9. O que os resultados permitem concluir

Na execução padrão Windows desta sessão, o MAE foi **37,03571274923828 MWmed** no modelo e **37,99164583333333 MWmed** na persistência, nas mesmas origens. O viés foi **+22,45994407623489 MWmed**, na convenção **observado − previsto**: houve subestimação média.

Um MAE menor pode coexistir com esse deslocamento sistemático. A otimização correta não autoriza promover o modelo. Uma semana já explorada é validação de desenvolvimento, sem demonstrar desempenho em outros períodos ou utilidade operacional. Modelo, features e diferenças entre períodos precisam ser investigados; esses números não isolam a causa do viés. O parecer e os arquivos de cada execução guardam as evidências desta conclusão.
