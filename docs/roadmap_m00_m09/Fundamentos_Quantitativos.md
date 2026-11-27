# Fundamentos quantitativos — M02-01 a M02-04

25/11/2026 · Renewcast/P1 · retomada das etapas 1–3

Este material cobre quatro lacunas do cadastro: probabilidade, estimação, testes de hipóteses e fundamentos da regressão. As contas resolvidas e as execuções são **assistidas**. A [avaliação com casos novos](Avaliacao_Fundamentos.md) fica sem respostas para o aluno resolver e para revisão humana. Receber código e resultados não comprova compreensão independente.

Todos os dados desta rodada são **sintéticos**. Não foram usados para escolher novamente HGB, GRU ou Chronos. Não há consulta a um novo holdout ONS, treinamento desses benchmarks, download, Docker ou implantação. NumPy e SciPy já estão disponíveis no ambiente verificado.

## 1. Como executar e onde conferir

Da raiz do repositório, com o ambiente `renewable-forecast` ativo:

```powershell
# Primeiro: registrar hipóteses e parâmetros, sem gerar dados.
python notebooks/laboratorio_probabilidade.py --preparar
python notebooks/laboratorio_regressao_fundamentos.py --preparar

# Depois: executar as demonstrações e conferir as contas.
python notebooks/laboratorio_probabilidade.py
python notebooks/laboratorio_regressao_fundamentos.py

# Testes pequenos, sem os benchmarks históricos.
python -m unittest discover -s tests -p test_fundamentos_quantitativos.py -v
```

O primeiro laboratório produz M02-01, M02-02 e M02-03. O segundo produz M02-04. Cada pasta em `reports/fechamento_m00_m09/<ID>/` recebe `protocolo.json`, `resultado.json` e `parecer.md`; as saídas específicas são `exercicios.md`, `estimativas.csv`, `plano_hipoteses.md`/`comparacao.csv` e `diagnosticos.csv`.

`--preparar` registra fontes, seeds, hipóteses, tamanhos, distribuição e critérios **antes** da simulação. A execução verifica que o protocolo não mudou, salva versões e hashes e declara `learning_validated=false`. Protocolos com outro código e resultados já existentes não são sobrescritos. Para reproduzir em outra pasta, passe o mesmo `--output-root` aos comandos de preparo e execução, por exemplo `--output-root reports/reproducao_fundamentos_01`.

O identificador da rotina de números aleatórios é PCG64 e as sementes são fixas. Isso permite reprodução no ambiente registrado; uma semente não comprova validade de uma hipótese. Não trocamos seed até obter uma conclusão conveniente.

## 2. M02-01 — probabilidade, população e distribuições

Uma população é o conjunto sobre o qual se quer afirmar algo. Uma amostra contém as unidades efetivamente observadas. Antes de contar, defina a unidade: uma hora, um evento ou um canal. Três canais do mesmo evento não constituem automaticamente três eventos independentes. Uma tabela sintética de 10.000 oportunidades é uma construção; não é evidência da taxa-base do ONS ou da ESA.

Se A é “há um evento” e B é “o detector sinaliza”, então:

```text
P(A | B) = P(A e B) / P(B), quando P(B) > 0
P(B) = P(B | A) P(A) + P(B | não A) P(não A)
```

No exemplo resolvido, prevalência = 1%, sensibilidade = 90% e taxa de falso positivo = 5%:

| Situação em 10.000 oportunidades | Evento | Sem evento | Total |
| --- | ---: | ---: | ---: |
| Sinal positivo | 90 | 495 | 585 |
| Sinal negativo | 10 | 9.405 | 9.415 |
| Total | 100 | 9.900 | 10.000 |

Assim, `P(evento | positivo) = 90/585 = 15,384615…%`. A sensibilidade de 90% mede `P(positivo | evento)`. Inverter a condição ignora a taxa-base. Um percentil de escore alto também não fornece, por si, a probabilidade de evento necessária para decidir por custo.

Independência significa `P(A e B) = P(A)P(B)`. Não é sinônimo de “eventos diferentes” nem de exclusão mútua. Se duas horas compartilham a mesma ocorrência, tratar ambas como ensaios Bernoulli independentes pode subestimar a incerteza.

Para uma variável discreta X com valores 0, 1, 2 e probabilidades 0,5, 0,3, 0,2:

```text
E[X] = soma(x p(x)) = 0,7
E[X²] = 0²×0,5 + 1²×0,3 + 2²×0,2 = 1,1
Var(X) = E[X²] − E[X]² = 1,1 − 0,49 = 0,61
```

A esperança é uma média ponderada da distribuição, não necessariamente um valor que uma observação possa assumir. A variância tem unidades ao quadrado; o desvio-padrão volta às unidades da variável. `E[X+Y]=E[X]+E[Y]` não exige independência; `Var(X+Y)=Var(X)+Var(Y)+2Cov(X,Y)` mostra por que omitir dependência altera a dispersão.

| Distribuição | Objeto e parâmetros | Média / variância | Pressuposto a defender |
| --- | --- | --- | --- |
| Bernoulli(p) | Um indicador 0/1 | p / p(1−p) | A definição do evento e a população de p |
| Binomial(n,p) | Número de sucessos em n tentativas | np / np(1−p) | Independência e p constante |
| Poisson(λ) | Número de ocorrências numa exposição | λ / λ | Taxa estável e incrementos independentes no modelo |
| Normal(μ,σ²) | Quantidade contínua, como um erro sintético | μ / σ² | Forma, suporte e condições do processo |
| t de Student(ν) | Estatística padronizada com variância estimada | 0 para ν>1 / ν/(ν−2) para ν>2 | A estatística e seus pressupostos; não é “a distribuição de qualquer dado pequeno” |

Para Binomial(24,0,01), a média é 0,24 e a variância 0,2376. Poisson(0,24) pode aproximar certas contagens raras, mas não torna legítima uma hipótese de independência falsa. A normal admite negativos: aplicar a distribuição à geração não negativa exige outra análise de suporte. A t não tem média definida para ν≤1, e não tem variância finita para ν≤2; fórmulas também têm domínio. Para uma variável contínua, a densidade não é a probabilidade de um ponto; probabilidades são áreas em intervalos. A CDF acumula probabilidade até um valor; um quantil inverte essa relação, sujeito à definição em distribuições discretas.

## 3. M02-02 — estimando, estimador, viés e intervalos

O **estimando** é a quantidade-alvo: por exemplo, a média μ do erro de uma população definida. O **estimador** é a regra calculada com a amostra, como `x̄`. A estimativa é o valor obtido numa realização. Viés é `E[estimador]−parâmetro`, definido sobre repetições do procedimento; não é o resíduo de uma única observação.

Sob amostragem IID com variância finita, `E[x̄]=μ` e `Var(x̄)=σ²/n`. Para variância desconhecida, `s² = soma((x−x̄)²)/(n−1)` é não viesado nesse desenho. Usar divisor n dá o estimador de máxima verossimilhança sob normalidade, cuja esperança é `(n−1)σ²/n`. O laboratório compara essas duas regras em 2.000 amostras normais de tamanho 16, com σ²=4: os alvos esperados são 3,75 e 4. A simulação oscila em torno das identidades teóricas.

Na conta manual `[8,10,12]`, `n=3`, `x̄=10`, soma dos quadrados dos desvios = 8, `s²=8/2=4` e `SE(x̄)=2/√3`. Se as observações forem normais IID, com variância desconhecida:

```text
IC de 95% para μ = x̄ ± t(2;0,975) s/√n
                 = 10 ± 4,302653 × 2/√3

PI de 95% para UMA nova observação independente da mesma população
                 = x̄ ± t(2;0,975) s√(1+1/n)
```

O IC quantifica a incerteza sobre a média fixa. O PI inclui a dispersão de uma nova observação e é mais largo. Para n=3, a meia largura do PI é duas vezes a do IC. Não é correto interpretar um IC frequentista observado como probabilidade posterior de 95% de μ estar dentro dele; o procedimento cobre o parâmetro em 95% das repetições sob seus pressupostos.

Em séries dependentes, para uma média estacionária com autocovariâncias γ(h):

```text
Var(x̄) = [n γ(0) + 2 soma((n−h) γ(h), h=1..n−1)] / n²
```

No AR(1) estacionário sintético com correlação ρ^h, o laboratório calcula `n_eff = n²/[n+2 soma((n−h)ρ^h)]`. A aproximação para séries longas é `n(1−ρ)/(1+ρ)`, dentro desse modelo. Não existe um n_eff universal para todas as métricas, dependências ou tamanhos. Para 48 leituras com ρ=0,8, ignorar covariâncias estreita indevidamente o IC. A simulação usa σ e ρ **conhecidos do gerador**; em dados reais eles precisariam de estimação e validação, ou de outro procedimento adequado. Esse exemplo não substitui o bootstrap em blocos M02-08.

## 4. M02-03 — hipótese, efeito relevante e multiplicidade

O exemplo gera diferenças de perda diretamente: `d = perda_A−perda_B`. Uma diferença positiva favorece B. O alvo é a média populacional μ_d. O efeito mínimo relevante é 1 unidade de perda sintética:

```text
H0: μ_d ≤ 1
H1: μ_d > 1
```

Isso evita chamar qualquer melhoria positiva de suficiente. Efeito prático e evidência estatística respondem a perguntas distintas. O p-valor mede uma probabilidade de estatística tão extrema quanto a observada sob o modelo nulo; não é a probabilidade de H0 ser verdadeira. Não rejeitar não prova equivalência. Um teste de equivalência precisaria de margens e desenho próprios.

O gerador cria dez blocos independentes com 24 leituras cada. Dentro de cada bloco existe um deslocamento normal compartilhado e um ruído normal individual. Logo, as horas são correlacionadas; as dez médias de blocos são independentes e normais **pelo desenho construído**. O teste principal usa essas médias. A estatística t é `(média_blocos−1)/(s_blocos/√10)`, com nove graus de liberdade, comparada à cauda superior. O cálculo que finge 240 observações independentes aparece como contraprova e não decide a rodada. Em dados reais, escolher um bloco de 24 horas por conveniência não garante independência.

Existem quatro hipóteses na família, registradas previamente. Com alpha familiar de 5%, Bonferroni usa `0,05/4 = 0,0125` por teste. Rejeitamos H0 apenas quando `p_blocos < 0,0125`; o limite inferior unilateral correspondente tem confiança de 98,75% por teste. Reportamos os quatro candidatos, incluindo os desfavoráveis. Bonferroni não exige independência entre os quatro testes, mas exige validade dos p-valores individuais. Ele não corrige pseudorreplicação dentro de um teste.

A seleção dos casos, as sementes, o efeito mínimo e os critérios antecedem a geração. Alterar o critério depois e testar de novo nos mesmos resultados converteria esse material em desenvolvimento. Testes pequenos e muitos blocos correlacionados podem ter pouca potência; tamanho de efeito, incerteza e desenho devem acompanhar a conclusão. Nenhum resultado dessa família sintética é uma comparação confirmatória entre os modelos históricos do P1.

## 5. M02-04 — regressão como problema matemático

Com intercepto explícito, a matriz X tem shape `(n,p)`, o vetor y `(n,)`, os coeficientes β `(p,)` e a previsão `X@β` `(n,)`. Uma coluna y `(n,1)` subtraída de um vetor `(n,)` pode produzir broadcasting `(n,n)`: o laboratório rejeita essa entrada.

No exemplo, x = `[−1,0,1]`, y = `[1,2,4]` e:

```text
X = [[1,−1], [1,0], [1,1]]
XᵀX = [[3,0], [0,2]]
Xᵀy = [7,3]
β_OLS = [7/3,3/2]
ŷ = [5/6,7/3,23/6]
r = y−ŷ = [1/6,−1/3,1/6]
RSS = 1/6; MSE = RSS/3 = 1/18
```

Para `J(β)=||y−Xβ||²/n`, o gradiente é `2Xᵀ(Xβ−y)/n`, com shape `(p,)`. Um componente positivo indica que aumentar aquele coeficiente aumenta localmente a perda; o passo de descida usa o sinal oposto. No mínimo OLS, `Xᵀr=0`. A fórmula `β=(XᵀX)⁻¹Xᵀy` requer posto completo e é uma descrição algébrica; a implementação usa `lstsq`/SVD para evitar inversão explícita e lidar melhor com condicionamento.

Ridge, nesta implementação, minimiza:

```text
J(β) = ||y−Xβ||²/n + λ soma(β_j², j>=1)
P = diag(0,1,...,1)   # intercepto não penalizado
gradiente = 2Xᵀ(Xβ−y)/n + 2λPβ
(XᵀX+nλP)β = Xᵀy
```

O fator n acompanha esta convenção de normalização da perda. Para λ=1/3 na conta manual, o coeficiente de x vira `3/(2+3×1/3)=1`, e o intercepto continua 7/3. Penalizar o intercepto ou omitir n seria outro problema. Ridge altera o compromisso entre ajuste e magnitude dos coeficientes; não garante menor erro futuro. A escala das features muda o significado da penalização; em um fluxo real, qualquer padronizador precisa ser ajustado só no treino.

Se acrescentarmos a coluna 2x, o design tem três colunas e posto dois. Somar `[0,2,−1]` a β não muda `X@β`. Os coeficientes separados não estão identificados; a solução de norma mínima da SVD é uma convenção. Regularização pode tornar a solução numérica única sem identificar causas físicas. Diferenças finitas centrais, num ponto fora do mínimo, conferem o gradiente analítico sem depender do teste trivial de gradiente zero no ótimo.

## 6. Resíduos: prever e inferir não têm os mesmos requisitos

O segundo laboratório gera `y_t=2+3x_t+erro_t`, com x independente dos erros e erros AR(1) estacionários de ρ=0,8. OLS e Ridge com λ=0,1 predefinido usam as primeiras 160 linhas; as 80 seguintes recebem avaliação descritiva, sem busca de lambda nem escolha posterior de modelo. `diagnosticos.csv` mostra posto, shapes implícitos nas contagens, coeficientes, RMSE, média residual, correlação lag1 e Durbin–Watson descritivo.

- Linearidade refere-se à forma da média condicional especificada, não à aparência isolada de um gráfico.
- Exogeneidade `E[erro|X]=0` é central para interpretar ausência de viés OLS. Não é comprovada apenas com resíduos pequenos e não implica identificação causal.
- Homocedasticidade e ausência de correlação importam para a fórmula usual de variância OLS e para os resultados de eficiência. Normalidade é uma hipótese adicional para certos testes exatos em amostras finitas.
- Autocorrelação não destrói automaticamente a capacidade de previsão, mas invalida inferência que ignore a matriz de covariâncias. Aqui não publicamos p-valores ou ICs IID dos coeficientes.
- Com intercepto, a média dos resíduos OLS de ajuste é aproximadamente zero por álgebra. Isso não comprova viés zero no próximo período.
- Durbin–Watson é reportado como estatística descritiva. Não foi convertido em teste formal, nem usado sozinho para diagnosticar a causa de uma falha.

O próximo passo formativo é responder aos casos novos, justificando cada pressuposto. Depois, a revisão poderá apontar correções específicas. O cadastro não deve marcar M02-01–04 como `validado` apenas porque estes programas rodaram.
