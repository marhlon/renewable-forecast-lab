# Fundamentos aplicados — soluções e resultados M02-01–04

Aplicação técnica assistida solicitada pelo usuário. Os casos antes apresentados como questões foram agora resolvidos por código e por derivação. **Não se exige uma resposta do usuário para concluir esta aplicação técnica.** Isso não declara autoria independente nem mede aprendizagem; `learning_validated=false` permanece como limite de escopo, sem constituir uma pendência que bloqueie esta entrega de engenharia.

Os protocolos foram gravados antes dos cálculos, e as saídas estão separadas em `reports/fechamento_m00_m09/bloco1_engenharia/M02-01` a `M02-04`. As demonstrações e avaliações anteriores foram preservadas. Os dados desta aplicação são os números fixos dos enunciados: não há treino de benchmark, novo holdout, download ou equipamento comandado.

Para conferir a execução em outra pasta, use na raiz:

```powershell
python notebooks/aplicar_fundamentos_quantitativos.py --preparar --output-root reports/reproducao_fundamentos_aplicados_01
python notebooks/aplicar_fundamentos_quantitativos.py --output-root reports/reproducao_fundamentos_aplicados_01
```

No destino alternativo, o documento compartilhado fica na própria pasta de reprodução. Arquivos já existentes não são sobrescritos. Os CSVs mantêm os números usados nas contas; cada recibo guarda versões, fontes, hashes e conferências observadas.

## M02-01 — taxa-base, unidade e distribuição

### Conta executada

Das 20,000 oportunidades didáticas, 2% correspondem a 400 eventos e 19.600 a situações sem evento. A sensibilidade de 85% produz 340 positivos entre os eventos e 60 negativos. A taxa de falso positivo de 3% produz 588 positivos entre os 19.600 sem evento; restam 19.012 negativos.

| Sinal | Evento | Sem evento | Total |
| --- | ---: | ---: | ---: |
| Positivo | 340 | 588 | 928 |
| Negativo | 60 | 19.012 | 19.072 |
| Total | 400 | 19.600 | 20.000 |

```text
P(evento | positivo) = 340 / 928 = 85 / 232
                    = 0.366379310345 = 36.637931%
P(positivo | evento) = 340 / 400 = 85%
```

A primeira condição pergunta quantos positivos são eventos; a segunda pergunta quantos eventos geram um positivo. A taxa-base de 2% afeta a primeira. Sensibilidade alta não impede que a maioria dos positivos seja falsa quando o evento é raro e o falso positivo incide sobre uma população maior.

### As oito horas não são oito eventos independentes

Se uma mesma ocorrência dura oito horas, seus indicadores horários compartilham informação e duração. Não se justifica uma Binomial(24,p) apenas porque há 24 linhas: seriam necessários ensaios independentes e p constante. A unidade pode ser uma hora positiva ou o início de um episódio; são alvos diferentes. Para avaliar episódios, é preciso identificar início, fim, exposição observável e regra de agrupamento, preservando a informação temporal. Não foi estimada aqui uma probabilidade operacional de um detector real.

### Distribuições e condições de rejeição

Um indicador isolado 0/1 pode ser descrito marginalmente por Bernoulli(p); isso não torna a sequência IID nem mantém p estável entre regimes. Uma contagem por exposição fixa pode motivar Poisson(λ), se a taxa e os incrementos independentes forem defensáveis; agrupamento de episódios ou sobredispersão pode invalidar essa forma simples. Um erro contínuo pode motivar Normal(μ,σ²), mas assimetria forte, caudas pesadas ou variância que muda com o estado exigiriam outra avaliação. Se o objeto for geração não negativa, o suporte negativo da normal é outro ponto a examinar.

### População, amostra e outro ano

Os 20.000 casos e seus totais são uma tabela construída a partir das porcentagens fornecidas, não 20.000 medições coletadas pelo programa. Numa amostra real, as contagens flutuariam e a inclusão/ausência de dados precisaria ser descrita. A população-alvo deve definir período, equipamentos e unidade. Uma prevalência de outro ano pode não se transferir; sensibilidade e taxa de falso positivo também podem mudar. Inserir uma taxa-base antiga na fórmula não comprova disponibilidade, calibração ou validade operacional atuais.


## M02-02 — média, variância, IC e previsão

### Derivação com os quatro valores

O estimando é a média populacional μ da variável e população definidas. O estimador é a média amostral; sua realização é 21. Para `[18,20,22,24]`, os desvios são `[−3,−1,1,3]`, cuja soma dos quadrados é 20.

```text
n = 4; soma(x) = 84; média = 84/4 = 21
s² = 20/(4−1) = 20/3 = 6.666666666667
SE(média) = sqrt(s²/n) = sqrt(5/3) = 1.290994448736
```

Sob Normal IID com variância desconhecida, há três graus de liberdade. Usando o t arredondado fornecido, 3.182446:

```text
IC95% da média = 21 ± t × sqrt(5/3)
               = [16.891479880599, 25.108520119401]
PI95% de UMA nova observação independente da mesma população
               = 21 ± t × sqrt((20/3) × (1+1/4))
               = [11.813069726093, 30.186930273907]
```

SciPy retornou t=3.182446305284. O resultado preserva os dois cálculos: a diferença dos limites fica abaixo de 10⁻⁶ e decorre apenas do arredondamento fornecido. O PI é √5 vezes mais largo: ele inclui tanto a incerteza da média quanto a dispersão da observação futura. O IC não é um intervalo que deva conter 95% dos valores individuais.

### Dependência e tamanho efetivo

Se as leituras forem AR(1), deixa de valer a hipótese de independência usada pelo IC t simples. Para o cenário separado n=72 e ρ=0,6, a aproximação de série longa dá:

```text
n_eff aproximado = 72 × (1−0,6)/(1+0,6) = 18.000000000000
n_eff finito exato para a variância da média de AR(1) estacionário
                = n² / [n + 2 soma((n−h)ρ^h)]
                = 18.481283422460
```

A soma finita foi conferida também com aritmética racional. Os dois números diferem porque a aproximação ignora o efeito de borda. São específicos da média e de uma covariância AR(1) conhecida: não são n_eff universais nem licença para trocar n por 18 e inventar automaticamente novos graus de liberdade t. Não há 72 observações novas fornecidas neste exercício; o programa calculou a expressão da covariância, sem fabricar uma série ou afirmar cobertura empírica.

### Interpretação frequentista

μ é fixo nesse enquadramento, e o intervalo varia entre amostras. A afirmação correta é que o procedimento cobre μ em 95% das repetições sob o desenho e os pressupostos declarados. A frase “há 95% de probabilidade de o parâmetro estar neste intervalo observado” exigiria outro enquadramento probabilístico, como uma análise bayesiana com seus próprios pressupostos. A precisão aritmética desta conta não valida normalidade, independência ou representatividade em dados reais.


## M02-03 — efeito relevante, blocos e multiplicidade

### Teste sobre as seis médias fornecidas

O ganho é `perda_A−perda_B`: positivo favorece B. O alvo é μ_d, sua média populacional. O efeito mínimo relevante foi fixado em 0,5; portanto H0: μ_d≤0,5 e H1: μ_d>0,5. Os números `[0.2,1.4,0.9,1.8,1.2,1.0]` já são **médias de seis blocos independentes**, não seis horas selecionadas de uma série.

```text
soma(d) = 6,5
média = 13/12 = 1.083333333333
s² entre blocos = 869/3000 = 0.289666666667
SE = sqrt(s²/6) = 0.219722046636
t = (média−0,5)/SE = 2.654869378222; graus de liberdade = 5
p unilateral = 0.022580683718
limite inferior95%, usando t dado=2,015048
             = 0.640582862704
```

O t exato da biblioteca foi 2.015048373333; o limite correspondente é 0.640582780675. A diferença está dentro do arredondamento previsto. O limite inferior é maior que 0,5 e o p é menor que 0,05; **rejeitamos H0 no teste nominal especificado**, sob normalidade e independência dessas médias. Há evidência, nesse desenho, de ganho médio superior ao mínimo relevante. Não se demonstrou superioridade de um modelo Renewcast real, causalidade ou transferência para outro período.

### Por que não usar automaticamente as 144 horas

Para o teste t IID aplicado a 144 valores, seria necessário justificar independência e a distribuição/condições apropriadas desses valores. Horas do mesmo bloco podem compartilhar estado, regime ou erro; a contagem de linhas não é uma justificativa. A alternativa é tratar a estrutura de covariância ou manter uma unidade de inferência adequada, como as médias de blocos independentes assumidas na questão. Como as 144 observações originais não foram fornecidas, não foram replicadas artificialmente as médias para produzir uma falsa série horária nem calculado um teste “horário” sem dados.

### Outra família de três hipóteses

Esta é uma pergunta separada: os p-valores fornecidos são 0,009; 0,03; 0,4. Com alpha familiar de 5% e três testes, Bonferroni fixa `0,05/3 = 0.016666666667` por teste. **Somente H1, com p=0,009, passa**. H2 e H3 não passam. A família e o denominador são três; não se escolhe apenas o menor p e depois se declara que só houve um teste. Não é necessário assumir independência entre os três para o limite Bonferroni, mas os p-valores individuais precisam ser válidos.

O teste das seis médias e essa família de p-valores foram mantidos distintos porque o enunciado diz “em outra família”. Nenhum p-valor adicional foi inventado para completar uma comparação.

### Não rejeição e equivalência

Não rejeitar H0 não demonstra equivalência: pode refletir pouca precisão ou baixa potência. Uma pergunta de equivalência exige margem inferior/superior relevante, hipóteses próprias e um procedimento como dois testes unilaterais ou intervalo compatível, escolhidos antes do resultado. Também exige unidade, exposição e dependência apropriadas. O p-valor não é P(H0|dados), e significância não corrige um desenho inválido.


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
