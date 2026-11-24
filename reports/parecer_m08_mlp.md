# Parecer M08.2 — avaliação em lotes e comparação temporal

Execução autoral em 05/11/2026, Windows, Python 3.12.13 e PyTorch 2.7.1+cpu,
com dois threads e rede float32. Implementação e redação assistidas por Codex
a pedido de Marlon A. Bomfim; a conferência não certifica autoria independente.

## Janela, divisão e avaliação

Na origem de 03/07/2026 às 04h, a janela contém 24 medições: começa em
02/07 às 03h, com 91,721 MWmed, e termina em 03/07 às 02h, com 77,34 MWmed.
O alvo é 182,0555 MWmed em 04/07 às 04h, disponível às 06h sob o atraso
assumido de duas horas. Preservou-se o eixo sem fuso físico validado.

Das 7.485 origens, 18 não possuem histórico completo; 7.079 ajustam pesos e
escalas, 168 selecionam a época, 168 avaliam e 52 são excluídas por
disponibilidade dos rótulos. `shuffle=True` atua somente depois dessa divisão,
nas origens de ajuste. Não embaralha os horários internos das janelas nem
transfere exemplos entre conjuntos. A sobreposição temporal continua existindo.

O avaliador soma erros quadráticos em float64 e divide pelo total de exemplos,
preservando o peso do último lote: no caso 4+1, o MSE correto é 20, não 50.
Usa `eval()` e `no_grad()`, restaura os modos e preserva pesos e gradientes.
As médias e desvios vêm apenas do ajuste.

## Épocas e comportamento das curvas

Os valores abaixo são MSEs padronizados, calculados com pesos fixos e sem
Dropout; as setas ligam a melhor época à época de parada.

| Semente | Melhor / parada | Ajuste: melhor → parada | Seleção: melhor → parada |
|---|---:|---:|---:|
| 17 | 8 / 16 | 0,518609 → 0,508039 | 0,435417 → 0,461290 |
| 29 | 20 / 28 | 0,504057 → 0,499582 | 0,445700 → 0,460707 |
| 41 | 15 / 23 | 0,512898 → 0,506986 | 0,434813 → 0,440834 |

Em todas as sementes, o ajuste melhora entre esses pontos, enquanto a seleção
piora. Prolongar o treino não melhorou essa seleção. Após oito épocas sem
melhora estrita, restaurou-se o checkpoint escolhido, sem refit. Isso não
identifica isoladamente a causa da deterioração. `online_train_mse` mistura
pesos atualizados e Dropout ativo; não substitui essas duas curvas.

## Comparação e decisão

Todos os métodos foram avaliados nas mesmas 168 origens, em MWmed:

| Método | MAE | RMSE | Viés observado − previsto |
|---|---:|---:|---:|
| Persistência d2 | 37,991646 | 55,434342 | −3,016872 |
| Linear 24h | 33,678664 | 44,938111 | +15,148681 |
| MLP 17 | 32,724828 | 44,019866 | +10,655947 |
| MLP 29 | 33,700811 | 44,892316 | +12,652757 |
| MLP 41 | 33,159788 | 44,069511 | +13,724280 |

A MLP não vence o linear em MAE nas três sementes: a 29 é ligeiramente pior.
A mediana é 33,159788 e a faixa 32,724828–33,700811; essa faixa não é intervalo
de confiança nem resultado de ensemble. Escolher apenas a semente 17 pelo
MAE desta semana usaria a avaliação como seleção adicional.

As redes reduzem o viés do linear, mas continuam subestimando em média.
A persistência tem menor viés absoluto, embora maior MAE/RMSE. Os tempos
autorais registrados foram 35,06, 82,39 e 59,04 segundos, somando 176,50
segundos de treino. São medidas desta execução, não benchmark de plataforma
ou tempo total do programa. A MLP tem 833 parâmetros, contra 25 do linear.

Prefiro o linear por enquanto como referência simples, mantendo a MLP como
candidata de estudo. O ganho varia entre sementes e exige maior complexidade
e treinamento; o benefício observado merece avaliação em outros períodos.
Esta semana já foi explorada, não é teste final intocado. Nenhum resultado
autoriza promoção operacional ou comparação direta com o afim do M08.1,
cujas entradas e divisão eram diferentes.

## Evidências

- [Função](../notebooks/m08_avaliacao_autoral.py) e [guia completo](../docs/Explicacao_M08_2_Passo_a_Passo.md).
- Execução autoral: [resultado](neural/CJU_BA5EIGT/m08_2_mlp/20261105T152149Z_941d0398/resultado.json),
  [resumo](neural/CJU_BA5EIGT/m08_2_mlp/20261105T152149Z_941d0398/summary.csv) e
  [curvas](neural/CJU_BA5EIGT/m08_2_mlp/20261105T152149Z_941d0398/curvas.csv).
- [Figura das curvas autorais](neural/CJU_BA5EIGT/m08_2_mlp/curvas_autoria_20261105.png).

As três redes recarregadas reproduziram suas previsões com diferença zero.
Curvas, resumo e previsões autorais coincidiram byte a byte com a execução
de referência Windows; essa concordância verifica esta reprodução, sem
ampliar o alcance da evidência preditiva.
