# Solução técnica assistida — M02-04

Responsável pela implementação e execução: Codex. Aplicação solicitada pelo usuário; não é resposta independente atribuída ao aluno.

## M02-04 — OLS, Ridge, gradiente e posto

### Matriz e solução OLS

```text
X = [[1,−2], [1,0], [1,2]]    shape (3,2)
y = [0,1,5]                    shape (3,)
beta                            shape (2,)
X@beta                          shape (3,)
XᵀX = [[3,0], [0,8]]
Xᵀy = [6,10]
beta_OLS = [6/3,10/8] = [2,5/4]
```

A implementação por SVD retornou `[2.000000000000, 1.250000000000]`. As previsões são `[−0,5;2;4,5]`; os resíduos `y−previsão` são `[0,5;−1;0,5]`. RSS=1,5 e MSE=0.500000000000. O vetor y precisa ser `(3,)`: `(3,1)` pode induzir broadcasting e uma matriz errada de resíduos `(3,3)`; o validador rejeita esse shape.

### Sinal do gradiente e taxa

```text
J_OLS = ||y−X beta||²/n
gradiente = 2Xᵀ(X beta−y)/n
em beta=[0,0]: gradiente = −2[6,10]/3 = [−4,−20/3]
beta_novo = beta−eta*gradiente = [4 eta,(20/3) eta]
```

Portanto, uma taxa positiva pequena inicialmente aumenta intercepto e inclinação. Isso segue do sinal negativo das derivadas; não significa que uma taxa arbitrária seja estável. A Hessiana OLS é `diag(2,16/3)`. Para descida de gradiente nessa quadrática com taxa constante, a faixa estrita de convergência é `0<eta<2/L = 0.375000000000`, onde L é o maior autovalor. O passo demonstrativo eta=0,1 reduziu a MSE de 8.666666666667 para 3.967407407407; eta=1 aumentou-a para 82.740740740741. Foram dois passos isolados predefinidos, não um treino ou busca de taxa.

### Ridge com a normalização correta

```text
J_Ridge = ||y−X beta||²/n + lambda*beta_1²
P = diag(0,1); lambda=1/3; n lambda=1
(XᵀX+n lambda P) beta = Xᵀy
[[3,0],[0,9]] beta = [6,10]
beta_Ridge = [2,10/9] = [2.000000000000, 1.111111111111]
```

O intercepto não é penalizado. A inclinação encolhe de 1,25 para 10/9; omitir n mudaria a solução. A MSE de ajuste Ridge foi 0.551440329218, maior que a OLS, mas seu objetivo **com a penalização comum lambda=1/3** foi 0.962962962963, menor que 1.020833333333 ao avaliar OLS com a mesma penalização. Isso confere que os dois algoritmos resolvem objetivos distintos. Na quadrática Ridge, a Hessiana é `diag(2,6)` e a faixa correspondente é `0<eta<1/3`. Nenhuma dessas contas garante menor erro futuro ou identificação causal.

### Colinearidade e direção nula

Ao acrescentar a coluna 2x, X tem três colunas e posto 2. A direção `[0,2,−1]` é nula: `2x−(2x)=0`. Somá-la a qualquer solução deixa as previsões iguais; a maior diferença numérica observada foi 0. A SVD devolveu uma solução de norma mínima `[2.000000000000, 0.250000000000, 0.500000000000]`, que é uma convenção entre várias decomposições equivalentes. Regularização pode tornar a solução numérica única, mas não cria efeitos físicos separados.

### Resíduos de ajuste e futuro

Com intercepto em OLS, `Xᵀr=0` implica soma residual de ajuste aproximadamente zero. Essa propriedade algébrica não valida previsões futuras nem seus intervalos. Se resíduos futuros exibirem autocorrelação, a fórmula IID usual de erro-padrão dos coeficientes não fica justificada. Sob exogeneidade, OLS pode continuar sem viés, mas a inferência precisa da estrutura de covariância; dependência e mudança de regime também importam para previsão. O exercício não fornece uma série futura, então não foi fabricada nem medida autocorrelação futura. A conta resolve a interpretação da hipótese apresentada, sem alegar um experimento que não ocorreu.
