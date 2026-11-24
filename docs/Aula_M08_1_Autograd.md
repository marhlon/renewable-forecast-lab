# M08.1 — como os parâmetros de um modelo aprendem

Marlon A. Bomfim · Renewcast · 29/10/2026 · CPU, dados reais e validação temporal

## 1. Entrega e propósito

No M07 você tornou explícitos os dados usados por uma previsão: horários, disponibilidade, transformações e snapshots. Agora vamos tornar explícito **como uma função muda seus parâmetros para reduzir uma perda**.

O laboratório usa as duas features temporais do treino já aceito: geração no último instante disponível e média das seis horas disponíveis. Ajusta um modelo afim com três parâmetros, verifica seu gradiente de três maneiras, registra a curva de otimização, avalia uma semana de desenvolvimento e salva/recarrega seus pesos. É a base matemática que será reutilizada no MLP e na GRU; este modelo afim ainda não é uma rede profunda.

**Ao terminar, você deve conseguir:** rastrear dimensões de um cálculo, derivar o MSE, explicar o que `backward()` faz, distinguir gradiente de atualização, detectar broadcasting indevido e separar erro de otimização de erro preditivo.

O programa de referência está completo. A autoria é uma função pequena, independente, que confere o autograd. Não existe função vazia bloqueando a primeira execução.

## 2. Arquivos, ambiente e execução

O pacote acrescenta:

```text
notebooks/laboratorio_autograd.py
docs/Aula_M08_1_Autograd.md
docs/Verificacao_M08_1_Professor.json
```

Entrada existente, criada na etapa anterior:

```text
C:/renewable-forecast-lab/dist/databricks/CJU_BA5EIGT/m07_3/
    manifesto_entrada.json
    treino_referencia.parquet
```

O script usa esses arquivos locais, verifica o hash do treino e lê os parâmetros. Não precisa baixar a tabela do Databricks, refazer Spark ou reconstruir Docker. Não altera os arquivos de entrada, o modelo da API ou relatórios anteriores. As saídas de cada execução ficam numa pasta identificada dentro de `reports/neural/CJU_BA5EIGT/m08_1_autograd`.

No PowerShell:

```powershell
Set-Location C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m08_autograd.zip -DestinationPath .

# Uma vez para esta unidade. CPU; sem torchvision, torchaudio ou CUDA.
python -m pip install "torch==2.7.1" --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -eq 0) {
    python notebooks/laboratorio_autograd.py
}
```

A versão 2.7.1 é a versão fixada e executada nesta aula, não uma afirmação de que seja a mais recente. O índice oficial fornece essa versão para CPU em Linux e Windows. NumPy, pandas e PyArrow já pertencem ao seu projeto. O professor verificou em Linux/Python3.12; a execução Windows ainda é sua evidência a produzir.

Se o script informar arquivo de entrada ausente, confira essa pasta local; não aponte para `predictions.csv` de outro experimento. A entrada aqui é exatamente o treino do M07.3.

## 3. Primeiro: qual informação pode entrar no ajuste?

As 7.485 origens são divididas antes de calcular médias, desvios ou pesos:

| Papel | Quantidade | Regra |
| --- | --- | --- |
| Ajuste de parâmetros e escalas | 7.291 | `target_available_at < início_da_validação` |
| Excluídas da divisão | 26 | Origem anterior à validação, mas rótulo ainda indisponível no seu início |
| Validação de desenvolvimento | 168 | Últimas 168 origens da tabela |

A validação vai de **03/07/2026 04h a 10/07/2026 03h**, no eixo de timestamps sem fuso preservado pelo M07. O último alvo do ajuste fica disponível em **03/07/2026 03h**. São h24 + d2: a fronteira estrita explica as 26 exclusões. Não embaralhamos origens entre ajuste e validação.

Esta semana já foi examinada no projeto. É uma validação de desenvolvimento; não recebe o rótulo de teste final intocado. As 400 atualizações são fixadas antes de olhar o resultado, sem escolher uma época pelo erro de validação.

Para cada feature, calculamos no ajuste:

\[
z_j=(x_j-\mu_j)/s_j.
\]

Padronizamos o alvo com sua média e desvio no mesmo ajuste. Na validação aplicamos **essas escalas fixas**. A previsão retorna a MWmed por `predição_padronizada * scale_y + mean_y`. A perda otimizada é adimensional; MAE e RMSE do relatório estão em MWmed.

Por que padronizar? Features em escalas distintas mudam a geometria da perda: uma mesma taxa pode dar passos pequenos numa direção e exagerados noutra. Padronizar melhora esse aspecto, mas não elimina correlação entre features nem garante uma boa previsão.

## 4. Tensor e shape: a multiplicação que você precisa enxergar

Um tensor é um arranjo de números com dimensões, tipo e dispositivo. Neste laboratório:

| Símbolo | Conteúdo | Shape |
| --- | --- | --- |
| `X` | Duas features de cada uma das 7.291 origens de ajuste | `[7291, 2]` |
| `w` | Um peso por feature | `[2, 1]` |
| `b` | Intercepto compartilhado | `[]`, escalar |
| `X @ w + b` | Uma previsão por origem | `[7291, 1]` |
| `y` | Um alvo por origem | `[7291, 1]` |
| `loss` | Média dos erros quadráticos | `[]`, escalar |

O operador `@` contrai a dimensão das duas features: `[n,2] @ [2,1] → [n,1]`. O escalar `b` é somado a cada previsão. Esse broadcasting é intencional.

Já `[n,1] - [n]` pode produzir **`[n,n]`**: cada previsão é comparada com todos os alvos. O código continua executando, mas otimiza outro problema. A função `mse` exige shapes iguais e rejeita esse caso. A contraprova utiliza duas linhas para exibir a matriz errada `[2,2]` sem criar uma matriz grande.

Usamos CPU, dois threads e `float64` para tornar a conferência de derivadas precisa. Em redes maiores, custo, memória e precisão de `float32` serão discutidos; não dependemos da GPU MX110 nesta aula.

## 5. Derivação: do erro ao gradiente

Defina a previsão e o resíduo com este sinal:

\[
\hat y=Xw+b,\qquad r=\hat y-y,\qquad L=\frac1n\sum_{i=1}^{n}r_i^2.
\]

Para um peso \(w_j\), a regra da cadeia dá

\[
\frac{\partial L}{\partial w_j}
=\frac1n\sum_i 2r_i\frac{\partial r_i}{\partial w_j}
=\frac2n\sum_i r_ix_{ij}.
\]

Como a derivada do resíduo em relação ao intercepto é 1:

\[
\nabla_w L=\frac2nX^Tr,\qquad
\frac{\partial L}{\partial b}=\frac2n\sum_i r_i.
\]

Observe as dimensões: `[2,n] @ [n,1] → [2,1]`, exatamente o shape de `w`. O gradiente de `b` é um escalar.

**Caso manual de referência:** `X=[[1,0],[0,1]]`, `y=[[1],[2]]`, `w=[[0],[0]]`, `b=0`. As previsões são zero; resíduos -1 e -2; MSE=2,5; `dw=[[-1],[-2]]`; `db=-3`.

Um passo com taxa 0,1:

\[
w\leftarrow w-0{,}1\,dw=\begin{bmatrix}0{,}1\\0{,}2\end{bmatrix},
\qquad b\leftarrow 0-0{,}1(-3)=0{,}3.
\]

As novas previsões são 0,4 e 0,5; MSE=(0,6²+1,5²)/2=**1,305**. A subtração do gradiente explica por que pesos com gradientes negativos aumentam.

## 6. Onde isso aparece no código PyTorch?

Leia `gradiente_autograd`, `demonstrar_armadilhas` e o laço de `main`, nessa ordem. A infraestrutura de hashes e arquivos pode ser deixada para depois.

```python
w = torch.zeros((2, 1), dtype=torch.float64, requires_grad=True)
b = torch.zeros((), dtype=torch.float64, requires_grad=True)
prediction = x_t @ w + b
loss = mse(prediction, y_t)
optimizer.zero_grad(set_to_none=True)
loss.backward()
optimizer.step()
```

| Linha | Efeito |
| --- | --- |
| `requires_grad=True` | Solicita o cálculo de derivadas em relação aos parâmetros. |
| `x_t @ w + b` | Calcula as previsões e registra operações necessárias à diferenciação. |
| `mse(...)` | Reduz os erros a uma perda escalar. |
| `zero_grad(...)` | Limpa gradientes do passo anterior. Não zera pesos nem intercepto. |
| `backward()` | Aplica a regra da cadeia e acumula derivadas em `.grad`. Não atualiza pesos. |
| `step()` | O SGD usa as derivadas e a taxa para atualizar parâmetros. |

O laboratório constrói um novo forward e faz `backward()` duas vezes sem limpar `.grad`: o segundo gradiente acumulado dobra. Depois limpa e confirma o valor original. Acumular pode ser uma técnica deliberada de treinamento; aqui demonstramos o erro de fazê-lo sem intenção.

Durante uma atualização manual e a inferência, `torch.no_grad()` evita registrar novas operações para derivação. Isso é diferente de `model.eval()`: este último muda o comportamento de módulos como Dropout e BatchNorm e será usado no MLP. Não há tais módulos neste modelo afim.

A conferência adicional por diferenças finitas calcula, para cada parâmetro:

\[
\frac{L(\theta+\varepsilon)-L(\theta-\varepsilon)}{2\varepsilon},\quad \varepsilon=10^{-6}.
\]

Ela aproxima numericamente a derivada. Autograd calcula derivadas pela regra da cadeia das operações registradas; não é um algoritmo de diferenças finitas. Verificamos o caso manual e oito linhas reais padronizadas.

## 7. Por que a taxa de aprendizagem pode fazer o treino divergir?

Ao acrescentar uma coluna de uns a `X`, o intercepto pode ser incluído em um único vetor de parâmetros: `A=[X,1]`. Para este MSE quadrático:

\[
H=\frac2nA^TA,\qquad 0<\eta<\frac2{\lambda_{max}(H)}.
\]

Essa condição controla a estabilidade do gradiente descendente de lote completo nesta quadrática. Não é uma regra geral para escolher taxa de redes profundas. O programa calcula o limite com dados de ajuste; não usa a validação.

O modo padrão usa `eta=0.05` e 400 passos. Nesta verificação, o limite foi aproximadamente **0,550817**. Depois de executar o padrão, faça uma única contraprova:

```powershell
python notebooks/laboratorio_autograd.py --learning-rate 0.8 --steps 30
```

Os dados, a divisão e o modelo são os mesmos; muda a otimização. Abra os dois `curva_treino.csv`: a taxa acima do limite permite observar a instabilidade. Valores ainda finitos e processo concluído não equivalem a um modelo aceitável. Se a perda ficar não finita, o programa registra o estado e retorna código 2.

O ajuste usa todas as linhas a cada passo. Há um único lote completo; ainda não temos mini-batches nem DataLoader. Em M08.2 eles permitirão organizar treino de uma rede compacta, sem alterar a separação temporal.

## 8. Otimizador correto não significa previsão adequada

O programa também resolve mínimos quadrados com `numpy.linalg.lstsq`, apenas no mesmo ajuste. A diferença entre seu MSE e o MSE do gradiente descendente mede a distância ao melhor valor desse problema quadrático. Não é diferença para a melhor previsão possível.

Na execução do professor, o modo padrão produziu:

| Diagnóstico | Resultado aproximado |
| --- | --- |
| Diferença para o mínimo quadrático de ajuste | 2,63e-8 de MSE padronizado |
| MAE do modelo afim na semana de desenvolvimento | 37,036 MWmed |
| MAE da persistência com atraso 2h, nas mesmas origens | 37,992 MWmed |
| Viés do modelo, observado menos previsto | +22,460 MWmed |
| Viés da persistência, mesma convenção | -3,017 MWmed |

O problema de otimização está praticamente resolvido, mas o viés de validação é elevado. Reduzir a perda de treino não é prova de boa calibração nem de utilidade operacional. Modelo, features, função de perda e mudanças entre períodos são dimensões distintas a investigar. Estes números não isolam a causa do viés.

O comparador usa somente duas features históricas e uma semana; não compare seu MAE diretamente com HGB+vento de outros folds ou com o holdout anterior. Não houve busca de hiperparâmetros, aprovação operacional ou inclusão de novos dados.

## 9. Sua autoria: uma função e uma decisão

Crie **`C:/renewable-forecast-lab/notebooks/m08_gradiente_autoral.py`**. Implemente:

```python
def gradiente_mse(X, y, w, b):
    # Devolver dw com shape [2,1] e db escalar, usando NumPy.
    # X: [n,2]; y: [n,1]; w: [2,1]; b: escalar.
```

Essa assinatura é o contrato, não um arquivo pronto para executar. Use a derivação da seção 5, sem `torch`, sem `autograd` e sem chamar a função de referência do professor. Preserve as entradas. Acrescente no arquivo um comentário explicando o fator `2/n` e o sinal do resíduo. Não precisa reescrever o restante do laboratório.

Conferência integrada:

```powershell
python notebooks/laboratorio_autograd.py --autoria notebooks/m08_gradiente_autoral.py
```

O modo normal já usa uma implementação completa do professor; esse modo opcional compara **a sua** derivada com autograd e diferenças finitas e registra o hash do arquivo. A conferência numérica não certifica autoria independente: sua explicação e o código também serão lidos.

Em **`reports/parecer_m08_autograd.md`**, escreva um parecer curto respondendo de forma conectada:

1. Como `[n,1] - [n]` muda o problema otimizado? Mostre as duas shapes.
2. No caso manual, por que `db=-3` faz o intercepto aumentar? Diferencie `backward` de `step`.
3. Usando as curvas de 0,05 e 0,8, o que indica problema de otimização? O que o pequeno gap para mínimos quadrados mostra no padrão?
4. O viés de +22,46 MWmed autoriza promover o modelo? Explique por que mesmo uma queda de MAE não basta e por que a escala foi ajustada só nas 7.291 linhas.

**Entrega desta unidade:** função autoral, parecer e `resultado.json`/`curva_treino.csv` das duas taxas; inclua o `resultado.json` do modo autoral quando executado. O script escreve no console a pasta exata de cada execução. Não envie todas as pastas antigas do projeto.

## 10. Critério de conclusão e sequência

M08.1 termina quando a execução real passa nas conferências de gradiente/shape/recarregamento, a função autoral coincide e o parecer distingue derivação, estabilidade e generalização. Não é necessário melhorar o MAE para concluir a aprendizagem; é necessário interpretar corretamente o resultado.

M08.2 usará `Dataset`/`DataLoader`, `nn.Module`, mini-batches e uma rede compacta; M08.3 tratará a arquitetura temporal e a comparação controlada com HGB. Eles continuam pendentes. Não acrescentaremos um novo ciclo de instalação Spark ou testes de Databricks.

## Referências primárias

- [PyTorch: autograd](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html) — grafo de operações, derivadas e acumulação de gradientes.
- [PyTorch: otimização](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html) — forward, perda, limpeza de gradientes e atualização.
- [PyTorch: broadcasting](https://docs.pytorch.org/docs/2.15/notes/broadcasting.html) — alinhamento de dimensões; a regra usada também existe na versão executada nesta aula.
- [PyTorch: instalação de versões anteriores](https://pytorch.org/get-started/previous-versions/) — comando CPU da versão fixada 2.7.1.

As derivações e exemplos desta aula foram construídos para o Renewcast. As referências documentam as APIs; resultados medidos constam da verificação do professor, que não substitui sua execução Windows.
