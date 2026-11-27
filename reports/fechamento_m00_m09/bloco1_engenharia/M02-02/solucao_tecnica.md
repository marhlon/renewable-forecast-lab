# Solução técnica assistida — M02-02

Responsável pela implementação e execução: Codex. Aplicação solicitada pelo usuário; não é resposta independente atribuída ao aluno.

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
