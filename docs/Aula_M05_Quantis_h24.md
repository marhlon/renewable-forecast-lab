# M05.1 — Quanto podemos confiar na faixa de geração prevista?

Marlon Alves Bomfim · 02/10/2026 · Renewcast · E50–E52

**Entrega técnica confirmada:** artefato h24 salvo e previsão emitida a partir de 32 entradas sem alvo. Seis das dez macroentregas técnicas do P1 foram demonstradas: 60% por contagem. Isso não representa 60% de domínio da formação.

## 1. Revisão da sua entrega h24

`prediction.json`, `request.json`, `manifest.json` e `model.joblib` são coerentes: hashes do modelo e do pedido conferem; origem em 01/08/2026 05h UTC, alvo em 02/08 05h UTC, última geração nas entradas em 01/08 03h UTC, último rótulo de treino disponível às 04h UTC. O corte seleciona 717 linhas e exclui 27. As 32 features do pedido coincidem com a linha do dataset anteriormente recebido.

Sua previsão registrada é **143,6473739986 MWmed**, com persistência de **188,294 MWmed**. A referência da aula anterior, 152,7141273, foi calculada em outro ambiente. Essa diferença não invalida a entrega, nem foi atribuída a uma causa específica. Seu manifesto informa scikit-learn 1.9.0, e o ambiente do professor utiliza 1.8.0. O binário recebido teve seu hash conferido, sem recarga entre essas versões. O arquivo de previsão registra `model_retrained=false`; o código enviado separa ajuste e inferência.

O escopo continua sendo reprodução histórica com features pré-calculadas. Disponibilidade e fuso permanecem hipóteses documentadas; esta entrega não é uma nova avaliação independente da qualidade do candidato.

## 2. Correção localizada na função que você escreveu

Você colocou a validação no ponto correto, usou `np.hypot` e permitiu componentes negativas. O problema está na descoberta de nomes por trechos: `"u" in k` também encontra a letra **u de cubed** em `wind_speed_cubed_mean_m3s3`; a busca de velocidade também pode escolher essa coluna cúbica. A ordem do dicionário passa a decidir quais grandezas serão comparadas, inclusive com unidades diferentes.

Contraprova executada com seu código: velocidade média 12 m/s, u=30 m/s e v=0 é recusada na ordem original, mas aceita após inverter as chaves. O pedido real também passa a ser recusado nessa inversão.

Em **`C:\renewable-forecast-lab\src\renewable_forecast\weather_artifact.py`**, substitua somente a função `validate_wind_geometry` por:

```python
def validate_wind_geometry(features: dict) -> None:
    speed = features["wind_speed_mean_ms"]
    u = features["wind_u_mean_ms"]
    v = features["wind_v_mean_ms"]

    if speed < 0:
        raise ValueError("Velocidade média do vento não pode ser negativa.")

    if np.hypot(u, v) > speed + 1e-8:
        raise ValueError("Componentes incompatíveis com a velocidade média do vento.")
```

Mantenha a chamada que você já colocou em `validate_request`. A função chamadora já exige os nomes exatos e valores numéricos finitos. Não há motivo para tentar adivinhar outro nome nem aceitar silenciosamente a ausência de uma entrada obrigatória.

Para aplicar o contrato corrigido ao artefato existente, execute **predict**, que não ajusta o estimador:

```powershell
python -m renewable_forecast.weather_artifact predict --model-dir reports/inference/CJU_BA5EIGT/h24_replay_20260801T0500Z/model --request reports/inference/CJU_BA5EIGT/h24_replay_20260801T0500Z/request.json --output reports/inference/CJU_BA5EIGT/h24_replay_20260801T0500Z/prediction_geometry_checked.json
```

Não use `replay` para esta verificação: ele compara a assinatura do código de ajuste com o manifesto, e sua edição mudou o arquivo. O modelo existente continua próprio para `predict` no ambiente em que foi treinado. A previsão válida deve continuar 143,6473739986 dentro da tolerância numérica, pois a correção só valida as entradas.

**Princípio para guardar:** nomes de features pertencem ao contrato. Alterar a ordem das chaves de um JSON não pode alterar a validade física dos mesmos valores.

## 3. Novo problema: estimar uma distribuição, começando por três quantis

Uma previsão pontual não descreve a faixa de resultados plausíveis. Vamos ajustar três HGB independentes:

| Saída | Estimativa desejada | Consequência de estar calibrada |
| --- | --- | --- |
| P10 | Quantil condicional de 10% | Aproximadamente 10% dos resultados abaixo dele em condições avaliadas adequadamente |
| P50 | Mediana condicional | Equilíbrio entre erros para cima e para baixo em probabilidade |
| P90 | Quantil condicional de 90% | Aproximadamente 10% dos resultados acima dele |

O intervalo **[P10, P90] tem cobertura nominal de 80%**. Essa é uma meta estatística; escrever `quantile=0.1` e `quantile=0.9` não garante que o intervalo a cumpra fora do treino. Cobertura agregada adequada também não prova cobertura adequada em cada horário, regime ou semana.

P50 não é obrigatoriamente a previsão de 143,647 da etapa anterior: aquele HGB foi ajustado com erro quadrático; agora o objetivo do ajuste muda. Mediana também não é sinônimo de moda.

Para erro `r = y - q`, a perda pinball de nível tau é:

\[
L_\tau(y,q)=\max(\tau r,(\tau-1)r).
\]

Exemplo para P90, com y=100 MWmed:

| Previsão q | Erro r | Perda para tau=0,9 |
| --- | --- | --- |
| 80 | +20 | 18 |
| 120 | −20 | 2 |

Subestimar custa mais nesse objetivo; o ajuste é incentivado a estimar a parte superior da distribuição. Para P50, a perda é metade do erro absoluto. O scikit-learn oferece `loss="quantile"` com `quantile=tau` e `mean_pinball_loss` para avaliação.

## 4. Experimento desta prática

O módulo `weather_quantiles.py` reutiliza o mesmo dataset h24 de julho, com três folds de 168 horas e treinos de 214, 382 e 550 linhas. Todos os rótulos usados no ajuste devem estar disponíveis antes da primeira emissão da respectiva validação. Os pesos dos modelos ficam fixos dentro de cada fold; as features mudam a cada emissão.

São nove ajustes HGB: três quantis por fold, com 32 entradas. Os demais hiperparâmetros são os já adotados, sem nova busca. A referência probabilística usa `lag_1h` acrescido dos quantis dos erros passados da persistência:

\[
\hat q_\tau(t)=y_{\mathrm{último\ disponível}}(t)+Q_\tau(y_i-\mathrm{lag1}_i),
\quad i\in\mathrm{treino\ elegível}.
\]

Esses resíduos são conhecidos antes do corte e seus quantis ficam congelados durante o fold. Eles não são resíduos calculados a partir dos alvos de validação. Essa referência permite avaliar se o modelo condicional entrega intervalos úteis frente a uma construção simples com o histórico dos erros.

Três modelos independentes podem produzir cruzamentos, como P10 > P50. O protocolo preserva as saídas brutas, conta os cruzamentos e aplica piso zero seguido de ordenação por linha, sem consultar o alvo. Ordenação garante limites coerentes, mas não calibração. Todas as métricas principais usam a saída ordenada.

## 5. Execute no mesmo ambiente do projeto

Salve `renewcast_m05_quantis_20261002.zip` em **C:\renewable-forecast-lab**. No PowerShell já com `(renewable-forecast)` ativo, execute uma linha por vez, interrompendo se houver erro:

```powershell
Set-Location "C:\renewable-forecast-lab"
```

```powershell
Expand-Archive -LiteralPath "C:\renewable-forecast-lab\renewcast_m05_quantis_20261002.zip" -DestinationPath "C:\renewable-forecast-lab" -Force
```

```powershell
python -m renewable_forecast.weather_quantiles --input-dir data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development --output-dir reports/probabilistic/CJU_BA5EIGT/h24_d2_july_quantiles_v1 --n-splits 3 --test-size-hours 168 --threads 2
```

O pacote acrescenta o módulo em `src/renewable_forecast` e esta aula em `docs`. Os resultados ficam na pasta indicada em `--output-dir`. Se ela já contiver uma execução, o módulo a preserva e pede outra pasta; uma repetição deliberada pode usar `h24_d2_july_quantiles_v2`.

| Arquivo de saída | Conteúdo |
| --- | --- |
| `predictions.csv` | 1.008 linhas: 504 emissões × dois métodos; quantis brutos, ordenados e alvo observado |
| `fold_metrics.csv` | Cobertura, perdas e largura por método/semana |
| `summary.csv` | Métricas agregadas por método |
| `folds.csv` | Cortes, contagens e última disponibilidade do rótulo de treino |
| `protocol.json` / `metadata.json` | Configuração, hipóteses, versões, fonte e hashes dos resultados |

## 6. O que já apareceu na execução do professor

Referência calculada com sua tabela real, em scikit-learn 1.8.0. Seu ambiente pode produzir valores diferentes; os cortes e as contagens devem coincidir.

| Método | Cobertura observada | Largura média (MWmed) | Pinball média dos três quantis | Interval score 80% |
| --- | ---: | ---: | ---: | ---: |
| Persistência + quantis dos resíduos | 88,49% | 139,56 | 10,4514 | 166,5230 |
| HGB com vento quantílico | 52,58% | 57,16 | 8,2821 | 120,5798 |

O HGB cobriu 265 de 504 resultados e teve 53 cruzamentos brutos. Suas coberturas semanais foram 60,71%, 53,57% e 43,45%. Portanto, o rótulo “80%” ainda não descreve o desempenho empírico desse intervalo. O HGB teve menor pinball e menor interval score, mas ficou muito aquém da cobertura nominal. A referência cobriu mais, com faixas largas. Nenhum método foi promovido.

Para interpretar as métricas:

- **Cobertura:** proporção dos alvos dentro dos limites. Analise também os erros em cada cauda.
- **Largura:** P90 − P10; uma faixa estreita só é útil se representar adequadamente o risco.
- **Pinball:** avalia o erro assimétrico de cada quantil; menor é melhor para o mesmo nível e amostra.
- **Interval score:** soma a largura a uma penalização dos resultados fora dos limites. Para 80%, a penalização é dez vezes a distância fora da faixa. Menor é melhor nesse critério, mas não substitui a inspeção de cobertura.

Este é desenvolvimento exploratório sobre julho já utilizado. Calibração posterior deve ser aprendida em dados anteriores elegíveis, com avaliação cronologicamente posterior; os alvos da mesma janela avaliada não podem ser usados para alargar retroativamente seus próprios intervalos. O antigo holdout de agosto continua consumido.

## 7. Sua prática autoral e entrega

Em **`C:\renewable-forecast-lab\notebooks\inspecao_quantis.py`**, implemente `pinball_manual(y, prediction, tau)` usando NumPy e a fórmula acima, sem chamar `mean_pinball_loss`. A função deve retornar a média das perdas.

Leia o `predictions.csv` desta execução, filtre `method == "hgb_weather_quantiles"` e recalcule a perda de P10, P50 e P90 usando `target_generation` como y. Compare com as três colunas `pinball_p10`, `pinball_p50` e `pinball_p90` do seu `summary.csv`. Use os valores da sua execução como referência; não exija igualdade com os números do professor.

Além do código, escreva uma decisão curta: **você permitiria apresentar [P10, P90] ao usuário como uma faixa de 80% confiável neste estágio?** Sustente com cobertura, largura e resultado por fold. Explique por que a pinball menor pode coexistir com cobertura insuficiente.

Envie `summary.csv`, `fold_metrics.csv`, `predictions.csv`, `protocol.json`, `metadata.json` e seu `inspecao_quantis.py`. A correção de vento pode ser mostrada junto da função revisada. A próxima unidade é calibrar intervalos respeitando a cronologia, após analisar sua execução; previsão de eventos continua pendente na macroentrega 7.

## 8. Léxico de fixação

| Termo | Operação concreta | Confusão a evitar |
| --- | --- | --- |
| Contrato / schema | Acessar nomes exatos no pedido | Descobrir unidade e significado por substring |
| Quantil / quantile | Ajustar `quantile=0.1/0.5/0.9` | Tratar P50 como a média ou a moda |
| Pinball loss | Ponderar subestimação e superestimação conforme tau | Usar MAE como avaliação suficiente de P90 |
| Cobertura / coverage | Contar `p10 <= y <= p90` | Supor 80% porque os níveis foram chamados P10/P90 |
| Intervalo preditivo | Estimar faixa para um resultado futuro | Confundir com IC bootstrap do ganho médio entre modelos |

Ao concluir, explique cada termo usando uma linha do seu próprio resultado. Na próxima retomada, reconstruiremos a perda para P10 sem abrir esta tabela.

Referências primárias: [HGB e perda quantílica](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html), [mean_pinball_loss](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_pinball_loss.html) e [exemplo de intervalos e cobertura](https://scikit-learn.org/stable/auto_examples/ensemble/plot_gradient_boosting_quantile.html).
