# Avaliação de fundamentos — casos novos, sem resolução

25/11/2026 · M02-01 a M02-04 · **aguarda resposta do aluno e revisão humana**

As demonstrações no [guia](Fundamentos_Quantitativos.md) foram construídas e executadas com assistência. Os números abaixo são novos e não são calculados pelos laboratórios. Não há gabarito preenchido neste arquivo. Registre a assistência que usar e mantenha sua tentativa inicial; a revisão deve avaliar a sua explicação, não atribuir autonomia a uma resposta fornecida por outra pessoa ou ferramenta.

Nome de quem respondeu: **pendente**. Data da tentativa: **pendente**. Assistência utilizada: **pendente**. Responsável/data da revisão: **pendente**.

## 1. M02-01 — taxa-base e distribuição

Um detector será observado em uma população didática de 20.000 oportunidades. A prevalência do evento é 2%, a sensibilidade 85% e a taxa de falso positivo 3%.

1. Monte a tabela evento/sem evento × sinal positivo/negativo. Calcule `P(evento|positivo)` e explique por que ela não é a sensibilidade.
2. Agora as oportunidades são horas consecutivas de um mesmo sensor, e um evento dura oito horas. Podemos usar Binomial(24,p) para o número de horas positivas sem outra hipótese? Qual unidade e dependência precisam ser revistas?
3. Escolha uma distribuição possível para: um indicador de alarme; uma contagem por exposição fixa; um erro contínuo. Dê pelo menos um motivo para rejeitar sua escolha em dados reais.
4. Distinga a população definida, a amostra efetivamente coletada e o que mudaria se a prevalência viesse de outro ano.

**Sua resposta e conta:** pendentes.

## 2. M02-02 — parâmetro ou observação futura?

Considere a amostra `[18,20,22,24]`. Admita inicialmente Normal IID e variância desconhecida. Para ajudar a conta manual, use `t(3;0,975)=3,182446`.

1. Defina o estimando. Calcule média, variância com divisor n−1, erro-padrão e IC de 95% da média.
2. Calcule o PI de 95% para uma nova observação da mesma população. Explique o termo adicional e o que os dois intervalos cobrem.
3. Se as leituras vierem de AR(1) com ρ=0,6, qual hipótese do cálculo anterior muda? Para n=72, calcule a aproximação `n(1−ρ)/(1+ρ)` e diga por que ela não é um n_eff universal ou exato para qualquer amostra.
4. Uma pessoa diz “o parâmetro tem 95% de probabilidade de estar no IC que observei”. Qual correção você faria no contexto frequentista usado na aula?

**Sua resposta e conta:** pendentes.

## 3. M02-03 — diferença relevante e família de testes

Seis blocos independentes de um novo ensaio têm diferenças médias `perda_A−perda_B` iguais a `[0.2,1.4,0.9,1.8,1.2,1.0]`. O efeito mínimo relevante foi fixado em 0,5 antes do ensaio. Admita normalidade das médias dos blocos. Para uma conta unilateral a 5%, use `t(5;0,95)=2,015048`.

1. Escreva H0/H1, calcule a média, o erro-padrão entre blocos e o limite inferior unilateral. Qual conclusão esse desenho permite, e qual não permite?
2. Uma analista usa as 144 horas originais como observações independentes. O que precisa ser verdadeiro para essa substituição ser válida? Por que 144 linhas não bastam como argumento?
3. Em outra família de três hipóteses já predefinidas, os p-valores individuais válidos foram `[0.009,0.03,0.4]`. Com alpha familiar de 5% e Bonferroni, quais passam? Informe o limiar e o denominador da família.
4. Um teste não rejeitou H0. Isso estabelece equivalência entre os modelos? O que precisaria ser definido para uma pergunta de equivalência?

**Sua resposta e conta:** pendentes.

## 4. M02-04 — regressão, shapes e interpretação

Agora use x=`[−2,0,2]` e y=`[0,1,5]`, com intercepto explícito. A perda é MSE com divisor n. No Ridge, λ=1/3 e o intercepto não é penalizado.

1. Escreva X e os shapes de X, y, β e previsão. Calcule `XᵀX`, `Xᵀy` e os coeficientes OLS.
2. Calcule o gradiente em β=`[0,0]`. Qual é o primeiro sentido de atualização para uma taxa positiva pequena? Explique usando o sinal, sem afirmar que a taxa pode ser arbitrariamente grande.
3. Calcule os coeficientes Ridge para a definição de perda desta questão. Mostre onde aparece nλ.
4. Acrescente a coluna 2x. O que acontece com o posto e a identificação dos coeficientes? Dê uma direção de coeficientes que deixe a previsão inalterada.
5. OLS tem média residual de ajuste próxima de zero, mas os resíduos futuros exibem autocorrelação. Isso valida a previsão futura ou o IC usual dos coeficientes? Separe as duas conclusões e suas hipóteses.

**Sua resposta e conta:** pendentes.

## Registro da revisão

Não preencher automaticamente. Para cada item, o revisor deverá registrar conta conferida, interpretação correta, correção solicitada e se a transferência foi demonstrada com a assistência declarada. Até essa revisão, os quatro itens continuam com **aprendizagem não validada**.
