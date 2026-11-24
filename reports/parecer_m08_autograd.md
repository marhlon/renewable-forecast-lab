# Parecer M08.1 — gradiente, estabilidade e generalização

Execução local: 04/11/2026, Windows, Python 3.12.13, PyTorch 2.7.1+cpu, CPU,
float64 e dois threads. Implementação e redação assistidas por Codex a pedido de
Marlon A. Bomfim; a concordância numérica não certifica autoria independente.

## Dimensões e sinal do gradiente

O modelo afim calcula `X @ w + b`, com `X [n,2]`, `w [2,1]` e `b` escalar.
A previsão e o alvo devem ter shape `[n,1]`: sua subtração produz `[n,1]`, um
resíduo por exemplo. Se o alvo tiver shape `[n]`, a subtração `[n,1] - [n]`
produz `[n,n]`: cada previsão é comparada com todos os alvos. Isso muda a perda
otimizada. A demonstração com duas linhas produziu `[2,2]`, e o laboratório
rejeitou esse alvo na função MSE. A implementação NumPy também valida os shapes.

Defini `r = X @ w + b - y` e implementei `dw = (2/n) * X.T @ r` e
`db = (2/n) * sum(r)`. O fator 2 vem da derivada do quadrado e `1/n` vem da
média. No caso manual, os resíduos são −1 e −2, `dw=[[-1],[-2]]` e `db=-3`.
Com taxa 0,1, `b_novo = 0 - 0,1*(-3) = 0,3`: subtrair um gradiente negativo
aumenta o intercepto. Os pesos passam a 0,1 e 0,2, as previsões passam a 0,4 e
0,5 e a perda cai de 2,5 para 1,305. `backward()` calcula e acumula as derivadas;
`step()` atualiza os parâmetros. `zero_grad()` limpa as derivadas anteriores,
sem zerar os parâmetros. No modo `--autoria`, a função NumPy é conferida;
o treinamento continua usando autograd e SGD do PyTorch.

## Estabilidade observada nas duas curvas

| Execução | Atualizações | MSE inicial padronizado | MSE final padronizado |
| --- | ---: | ---: | ---: |
| Taxa 0,05 | 400 | 1,000000 | 0,6346101118839145 |
| Taxa 0,8 | 30 | 1,000000 | 1,7769091784326462 × 10¹⁶ |

Com taxa 0,05 a perda diminuiu e ficou apenas `2,626978645725586e-8` acima do
MSE de mínimos quadrados (`0,634610085614128`) no mesmo ajuste. Isso indica
proximidade do mínimo desta função quadrática; não significa erro preditivo
nulo nem proximidade do melhor modelo possível. Com taxa 0,8 a perda cresceu
até aproximadamente 1,78 × 10¹⁶. É uma falha de otimização, mantendo os dados,
o modelo e a divisão. O limite estrito calculado no ajuste é aproximadamente
`0 < taxa < 0,550816954646894`. Essa condição vale para esta quadrática e
gradiente descendente de lote completo; não é uma regra universal para redes.
As duas execuções terminaram com `training_state=completed` e código 0:
no laboratório isso indica passos concluídos com perda finita, não aprovação
do ajuste. A taxa 0,8 permanece inadequada apesar de o processo ter terminado.

## Generalização e decisão

| Medida na mesma semana de desenvolvimento | Modelo afim | Persistência d2 |
| --- | ---: | ---: |
| MAE (MWmed) | 37,035713 | 37,991646 |
| RMSE (MWmed) | 52,017796 | 55,434342 |
| Viés: observado − previsto (MWmed) | +22,459944 | −3,016872 |

O viés positivo do modelo indica **subestimação média** de aproximadamente
22,46 MWmed. A redução de MAE é de cerca de 0,956 MWmed, mas essa melhora
agregada não elimina o viés nem demonstra utilidade operacional. O ensaio
abrange apenas uma semana de desenvolvimento já examinada. Não é um teste
final intocado, não identifica a causa do viés e não permite comparar
diretamente com HGB+vento de outros folds. A decisão é manter o modelo no
escopo didático; estes resultados não autorizam promovê-lo à operação.

As 7.485 linhas foram separadas em 7.291 de ajuste, 26 excluídas por
indisponibilidade do alvo e 168 de validação. O último alvo usado no ajuste
ficou disponível em 03/07/2026 03h, antes do início da validação em
03/07/2026 04h. Médias e desvios das features e do alvo foram calculados
somente nas 7.291 linhas para evitar usar informação da validação no ajuste.
Essas escalas fixas foram aplicadas à validação; as previsões voltaram a
MWmed antes das métricas. Não houve escolha de época pela validação nem
busca de taxa: foram executados os dois regimes prescritos pela aula.

## Evidências desta entrega

- [Função NumPy](../notebooks/m08_gradiente_autoral.py).
- [Explicação passo a passo](../docs/Explicacao_M08_1_Passo_a_Passo.md).
- Padrão 0,05: [resultado](neural/CJU_BA5EIGT/m08_1_autograd/20261104T131859Z_8f277a44/resultado.json)
  e [curva](neural/CJU_BA5EIGT/m08_1_autograd/20261104T131859Z_8f277a44/curva_treino.csv).
- Contraprova 0,8: [resultado](neural/CJU_BA5EIGT/m08_1_autograd/20261104T132027Z_d5a8612c/resultado.json)
  e [curva](neural/CJU_BA5EIGT/m08_1_autograd/20261104T132027Z_d5a8612c/curva_treino.csv).
- Modo autoral 0,05: [resultado](neural/CJU_BA5EIGT/m08_1_autograd/20261104T132133Z_97eada41/resultado.json)
  e [curva](neural/CJU_BA5EIGT/m08_1_autograd/20261104T132133Z_97eada41/curva_treino.csv).

As três execuções passaram nas conferências de derivada, broadcasting,
acumulação e recarregamento dos pesos. Uma checagem adicional confirmou o caso
manual, preservação de entradas somente para leitura e rejeição de shapes
inválidos e lote vazio. A implementação usa NumPy, não chama a referência
do professor e não modifica as entradas.

O treino local passou na verificação de tamanho e SHA-256 contra seu próprio
manifesto. Seu hash é
`6ab1e8fc1e6c11673d3620a937e98ff43e2cee5965c19beab4566a6b87b7762e`.
Esse hash difere do registrado na verificação Linux do professor. As métricas
acima são medidas nesta execução Windows; a coincidência numérica não prova
identidade binária dos arquivos com aquela execução. O código do laboratório
foi preservado, com hash
`3b8ffdc46ecbb64406de1220c29e43b7dd37943d33a8ab4b3095334148ee935b`.

Para repetir no ambiente `renewable-forecast`, a partir da raiz do projeto:

```powershell
python notebooks/laboratorio_autograd.py
python notebooks/laboratorio_autograd.py --learning-rate 0.8 --steps 30
python notebooks/laboratorio_autograd.py --autoria notebooks/m08_gradiente_autoral.py
```

Referências de API: [autograd](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)
e [broadcasting no PyTorch 2.7](https://docs.pytorch.org/docs/2.7/notes/broadcasting.html).
As métricas e a interpretação de estabilidade acima se baseiam nas execuções
locais identificadas, não apenas na documentação.
