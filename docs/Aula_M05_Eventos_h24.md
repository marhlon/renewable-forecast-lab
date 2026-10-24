# M05.3 — Da previsão de geração à probabilidade de queda

Marlon Alves Bomfim · 03/10/2026 · evidências E59/E60

**Entrega:** uma comparação reproduzível entre frequência histórica, regressão logística e HGB classificador, com previsões probabilísticas por emissão, avaliação temporal e análise da decisão de emitir um alarme.

Sua inspeção anterior está concluída no plano exportado: n=48 e k=40 nos três folds, correções 19,693951/0,619147/23,473284 MWmed e ambas as fronteiras verdadeiras. Os totais de escores zero foram 16/38/31. Essa etapa não precisa ser refeita para iniciar a classificação.

## 1. Fixar o significado do evento antes de olhar o desempenho

Para a primeira prática, o evento positivo é:

> A geração no horário alvo t+24 fica pelo menos 22,77 MWmed abaixo do último valor disponível na emissão t.

Com o atraso assumido de duas horas, esse último valor é y(t−2). Portanto:

```python
generation_drop_mwmed = lag_1h - target_generation
event_drop = (generation_drop_mwmed >= 22.77).astype(int)
```

`lag_1h` é o nome herdado do construtor; nesta tabela h24/d2, o remapeamento temporal faz com que represente a geração em `history_end = forecast_origin − 2h`. A coluna `last_available_generation` torna essa interpretação explícita nos novos relatórios.

O limiar 22,77 corresponde a 10% dos 227,7 MW do cadastro usado como referência. É uma hipótese fixa de desenvolvimento, definida antes desta comparação. Não demonstra que a capacidade histórica de julho era essa nem que esse limiar tenha valor econômico comprovado. O evento é definido em MWmed absolutos nesta execução.

Exemplo: na emissão de 11/07 às 10 UTC, temos geração das 08 UTC igual a 150 MWmed. O alvo é 12/07 às 10 UTC. Se a geração nesse alvo for 120 MWmed, a queda de 30 MWmed torna `event_drop=1`; se for 140, a queda de 10 produz `event_drop=0`.

**São 26 horas entre as duas observações.** A previsão continua tendo horizonte h24. O evento descreve os valores nos dois extremos; não representa uma rampa horária, nem “qualquer queda que aconteça durante as próximas24 horas”. Uma queda seguida de recuperação antes do alvo pode resultar em classe0.

O evento só se torna conhecido quando o alvo chega: `target_available_at`, equivalente a t+26 no protocolo. A coluna `event_drop` é y, nunca uma feature de X.

## 2. As ferramentas novas e o papel de cada uma

| Ferramenta | Aplicação nesta prática |
|---|---|
| `Pipeline` | Mantém padronização e classificador no mesmo ajuste por fold |
| `StandardScaler` | Estima médias/desvios exclusivamente no treino da regressão logística |
| `LogisticRegression` | Estima a chance do evento por uma função logística das features padronizadas |
| `HistGradientBoostingClassifier` | Estima probabilidades com relações não lineares e interações |
| `predict_proba` | Produz p(evento=1) para cada emissão |
| Brier e log loss | Avaliam as probabilidades antes de escolher um alarme |
| Average Precision | Resume a ordenação de eventos ao percorrer limiares de decisão |
| Matriz de confusão | Quantifica acertos, alarmes falsos e eventos perdidos num limiar específico |

Na regressão logística, p=1/(1+exp(−z)), onde z é uma combinação linear das 32 features padronizadas. O HGB classificador usa árvores; a mudança em relação ao regressor anterior não é apenas o nome da saída: agora o alvo é0/1 e a perda de ajuste é `log_loss`.

A referência `historical_frequency` usa a proporção de eventos no treino elegível. No Fold 1, por exemplo, 52 das 214 linhas são positivas; sua previsão é52/214≈24,30% para todas as emissões daquela semana. É uma referência probabilística útil mesmo sem distinguir horas dentro do fold.

Os hiperparâmetros estão fixos. A regressão logística usa C=1; o HGB reutiliza a configuração estrutural anterior com perda de classificação. O experimento não utiliza reamostragem nem pesos de classe. As probabilidades desta primeira comparação não recebem recalibração adicional.

## 3. Protocolo temporal

| Fold | Treino elegível | Eventos no treino | Avaliação | Eventos na avaliação |
|---|---:|---:|---:|---:|
| 1 | 214 | 52 | 168 | 38 |
| 2 | 382 | 94 | 168 | 43 |
| 3 | 550 | 139 | 168 | 32 |

Os três métodos recebem as mesmas 504 emissões de avaliação. Cada ajuste usa somente rótulos com `target_available_at < primeira forecast_origin da avaliação`. Modelos, scaler e frequência histórica permanecem fixos durante a semana; as features são as disponíveis em cada emissão.

Voltamos aos treinos 214/382/550 porque esta comparação ainda não reserva uma janela para recalibrar as probabilidades. Os treinos 140/308/476 pertenciam à intervenção anterior sobre intervalos, que exigia uma terceira partição. São protocolos distintos, documentados.

Julho já foi examinado e os parâmetros anteriores foram escolhidos durante o desenvolvimento. Estes resultados são exploratórios. O holdout antigo não volta a ser intocado e não haverá promoção automática de um alarme por vencer esta comparação.

## 4. Onde colocar e executar

Baixe `renewcast_m05_eventos_20261003.zip` e coloque-o em `C:\renewable-forecast-lab`. No PowerShell dessa pasta, com `(renewable-forecast)` ativo:

```powershell
Expand-Archive -LiteralPath .\renewcast_m05_eventos_20261003.zip -DestinationPath . -Force
```

O pacote coloca o módulo em `src/renewable_forecast/weather_events.py`, esta aula em `docs` e os resultados de referência em `docs/evidencias_m05_eventos_professor`. Reaproveita o dataset h24 existente.

```powershell
python -m renewable_forecast.weather_events --input-dir data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development --output-dir reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1 --drop-mw 22.77 --alarm-threshold 0.5 --n-splits 3 --test-size-hours 168 --threads 2
```

São seis ajustes: duas famílias de classificadores em três folds. Não há consulta meteorológica nesta execução. Uma pasta de saída não vazia é recusada para preservar o experimento anterior.

| Arquivo | Conteúdo |
|---|---|
| `event_labels.csv` |744 emissões e sua definição auditável de evento |
| `predictions.csv` |1512 linhas:504 emissões ×3 métodos, com p_event e alarm |
| `folds.csv` |Cortes temporais, contagens de treino e prevalências |
| `fold_metrics.csv` |Métricas semanais, incluindo TP/FP/FN/TN |
| `summary.csv` |Métricas agregadas e AP média dos folds |
| `probability_bins.csv` |Probabilidade média e frequência observada em faixas fixas, por fold e no conjunto |
| `protocol.json` |Limiar físico, limiar probabilístico, modelos, versões e hipóteses |
| `metadata.json` |Contagens e hashes dos resultados |

## 5. Como interpretar o resultado

Para evento y ∈{0,1} e probabilidade p, Brier=mean((p−y)²). Uma previsão p=0,8 perde 0,04 se o evento acontecer e 0,64 se não acontecer. A função avalia a probabilidade, antes de convertê-la em sim/não.

Menor Brier não demonstra isoladamente melhor calibração: também responde à capacidade de separar casos com riscos diferentes. A tabela de faixas permite examinar se, por exemplo, previsões próximas de 60% encontram uma frequência de eventos compatível, respeitando contagens e instabilidade semanal. Cinco bins fixos são um diagnóstico grosseiro, não um certificado de calibração.

AP é calculada por `average_precision_score`: soma das precisões ponderadas pelos incrementos de recall. Não é a área trapezoidal interpolada da curva PR. O resumo separa `pooled_average_precision` de `mean_fold_average_precision`. Juntar os folds pode mudar a ordenação entre probabilidades de modelos ajustados em datas diferentes; por isso mostramos as duas medidas.

Na frequência histórica, AP de cada fold coincide com a prevalência daquela semana, pois todas as horas recebem a mesma probabilidade. A AP agregada pode diferir porque a probabilidade constante muda entre folds.

O alarme inicial é `p_event >= 0.5`. Há dois limiares com funções diferentes:

- **22,77 MWmed** define o que aconteceu no mundo: o alvo positivo.
- **0,5** define a ação sobre uma probabilidade estimada: emitir o alarme.

Precision=TP/(TP+FP): entre os alarmes, quantos correspondiam a eventos? Recall=TP/(TP+FN): entre os eventos, quantos foram avisados? Se não houver alarmes, precision é indefinida e aparece como `NaN`/campo vazio; isso não é falha de coleta.

## 6. Execução de referência já verificada

Executada pelo professor no seu dataset real de 744 linhas,32 features e hash `d142dbaf75a0e18fb203b77dfea8d8377c6d3b1d2c9fc1fc5908b1a50a9a6635`. Ambiente: Python3.12.14, sklearn1.8.0, NumPy2.3.5 e pandas2.2.3. Valores dos classificadores podem diferir no seu ambiente; definição dos eventos, cortes e contagens devem coincidir se a entrada for a mesma.

| Método | Brier | AP média dos folds | Precision em 0,5 | Recall em 0,5 | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| Frequência histórica |0,174640|0,224206|indefinida|0,00%|0|113|
| Logística |0,132262|0,674682|65,43%|46,90%|28|60|
| HGB classificador |0,112417|0,751761|68,52%|65,49%|34|39|

O HGB teve redução agregada de 35,63% do Brier contra a frequência. Detectou 74 dos 113 eventos e emitiu 34 alarmes falsos. A logística teve menor Brier no Fold 2:0,1275 contra0,1431 do HGB. Portanto, o vencedor agregado não dominou todas as semanas.

A log loss da logística foi 0,5362, ligeiramente pior que 0,5341 da frequência, apesar de seu Brier menor. As perdas ponderam os erros de formas diferentes; examine as probabilidades associadas a erros confiantes antes de afirmar superioridade universal.

Uma regra que nunca alerta acertaria391/504≈77,58% das classes, mas perderia todos os113 eventos. Esse exemplo mostra por que acurácia isolada não é nosso critério de decisão.

Verificações executadas: mesma amostra nos três métodos; sentido/limite da classe; disponibilidade; frequência calculada no treino; Brier e matriz de confusão reconciliados; scaler ajustado somente nas214 linhas do primeiro treino. Alterar os alvos futuros do primeiro fold manteve suas probabilidades. Não houve acesso ao repositório Windows completo; o helper de splits usa o código anteriormente fornecido pelo aluno.

## 7. Sua implementação autoral: converter probabilidade em decisão

Crie `C:\renewable-forecast-lab\notebooks\inspecao_decisoes.py`. A entrada é `reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/predictions.csv`.

Implemente esta interface, usando operações NumPy em vez das funções prontas de matriz de confusão:

```python
def avaliar_limiar(y, p, threshold, cost_fp=1.0, cost_fn=4.0) -> dict:
    ...
```

Valide vetores 1D de mesmo tamanho e não vazios, y em {0,1}, probabilidades finitas em [0,1], limiar entre 0 e 1 e custos finitos/não negativos. Retorne `tp`, `fp`, `fn`, `tn`, `precision`, `recall`, `cost_total` e `cost_per_emission`. Use `np.nan` para razões com denominador zero.

Para cada método, calcule os limiares0,2 e0,5, tanto no conjunto quanto por fold. As colunas reais são `method`, `fold`, `event_drop` e `p_event`; não use o campo `alarm` para reconstruir decisões de outro limiar.

O custo é **hipotético**, em unidades didáticas: cada FP custa 1 e cada FN custa 4. Assim:

```python
cost_total = fp + 4 * fn
```

Se p fosse uma probabilidade condicional adequada e esses fossem os custos relevantes, o custo esperado de alertar seria(1−p)×1; o de não alertar seria p×4. Comparando-os, a regra de menor custo seria alertar a partir de p=1/(1+4)=0,2. Isso explica de onde vem o segundo limiar. Não o valida para operação, nem permite assumir que as probabilidades brutas estejam calibradas.

Antes de aplicar aos arquivos, confira um caso pequeno à mão:

```python
y = [1, 0, 1, 0]
p = [0.8, 0.6, 0.3, 0.1]
```

Em 0,5: TP1/FP1/FN1/TN1, precision 0,5, recall 0,5, custo 5. Em 0,2: TP2/FP1/FN0/TN1, precision 2/3, recall 1, custo 1.

Execute:

```powershell
python notebooks/inspecao_decisoes.py
```

Entregue sua função e a tabela de resultados. Defenda a escolha entre 0,2 e 0,5 sob esses custos, explicitando mudanças em FP e FN, estabilidade semanal e a hipótese de calibração. As previsões não mudam quando alteramos o limiar: Brier e AP permanecem iguais. Essa é uma análise exploratória de decisão; não é seleção de um limiar operacional em dados independentes.

## 8. Fixação léxica

| Termo | Frase que você deve conseguir ligar ao arquivo |
|---|---|
| Evento |“O que conta como classe 1 está definido antes de ajustar o modelo.”|
| Prevalência |“É a fração de positivos no conjunto indicado.”|
| Probabilidade |“p_event expressa a estimativa de chance, ainda sujeita a avaliação.”|
| Discriminação |“O modelo ordena casos de maior risco acima dos de menor risco?”|
| Calibração |“A frequência observada corresponde às probabilidades informadas?”|
| Limiar |“Transforma a probabilidade em uma decisão.”|
| Precision |“Quantos dos meus alarmes eram eventos?”|
| Recall |“Quantos dos eventos receberam alarme?”|
| Custo |“Qual consequência atribuo a cada tipo de erro?”|

Referências primárias: [Probability calibration](https://scikit-learn.org/stable/modules/calibration.html), [Average precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html) e [HistGradientBoostingClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html).
