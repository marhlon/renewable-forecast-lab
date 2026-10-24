# Renewcast — do experimento ao artefato de inferência h24

Marlon Alves Bomfim · 01/10/2026 · M04, evidências E48/E49

**Entrega desta aula:** ajustar um candidato com os rótulos elegíveis, salvar o objeto treinado, abrir outro processo e prever usando um pedido que não contém `target_generation`. Seu papel autoral será acrescentar uma regra física ao contrato das entradas.

O código foi executado pelo professor com a tabela real enviada. A reprodução no Windows e a implementação autoral do aluno ainda estão pendentes. A execução é uma reprodução histórica, sem promoção do candidato a produção.

## 1. Instalar o incremento e executar

Salve `renewcast_h24_artifact_20261001.zip` na raiz `C:\renewable-forecast-lab`. O pacote contém um módulo novo em `src/renewable_forecast/weather_artifact.py` e esta aula em `docs/Aula_Artefato_h24.md`.

No PowerShell que já mostra `(renewable-forecast)`, execute cada comando em uma linha, na ordem. Se a extração falhar, interrompa antes do próximo comando.

```powershell
Expand-Archive -LiteralPath "C:\renewable-forecast-lab\renewcast_h24_artifact_20261001.zip" -DestinationPath "C:\renewable-forecast-lab" -Force
```

```powershell
python -m renewable_forecast.weather_artifact replay --input-dir data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development --forecast-origin 2026-08-01T05:00:00Z --output-dir reports/inference/CJU_BA5EIGT/h24_replay_20260801T0500Z
```

O comando executa um ajuste HGB, exporta o pedido e inicia um processo `predict`. Numa repetição com exatamente o mesmo código, dados, corte e ambiente compatível, reutiliza o artefato existente. Uma pasta com outro ajuste é recusada.

Resultado esperado no contrato:

```text
Treino elegível: 717/744; excluídas: 27
Último rótulo disponível: 2026-08-01 04:00:00+00:00
feature_count: 32
target_present_in_request: false
model_retrained: false
```

`model_retrained=false` descreve o processo de inferência. O ajuste foi realizado antes, pelo processo de treino.

## 2. Os relógios desta emissão

| Papel | Instante UTC | Significado |
| --- | --- | --- |
| Emissão | 01/08/2026 05h | Instante que estamos reproduzindo |
| Última geração nas entradas | 01/08/2026 03h | Disponível às 05h sob o atraso assumido de 2h |
| Último rótulo permitido no treino | Disponível em 01/08/2026 04h | Anterior ao início da emissão |
| Rodada meteorológica selecionada | 31/07/2026 18h | Disponível em 01/08 às 00h sob a latência assumida |
| Alvo | 02/08/2026 05h | Geração 24 horas após a emissão |

Os timestamps do CSV original incluem alvos conhecidos retrospectivamente. O corte impede que esses rótulos futuros entrem no ajuste; o pedido de inferência exportado exclui a coluna do alvo. Esse exercício verifica a operação histórica do artefato. A geração de pedidos a partir de uma alimentação contínua de dados é outra camada da operação.

Pelo protocolo já adotado, rótulos de treino precisam de `target_available_at < origin`; entradas podem estar disponíveis na própria emissão. A diferença é uma convenção de ordenação do processo, que precisa ser mantida explícita. Não se deve trocá-la para melhorar uma métrica.

## 3. Leia estas funções no módulo

**`select_training_rows`: o conjunto de treino é definido pelo conhecimento disponível.**

```python
eligible = (
    (frame["forecast_origin"] < origin)
    & (frame["target_available_at"] < origin)
)
```

Usar todas as 744 linhas incluiria rótulos ainda indisponíveis. Neste caso, 717 entram e 27 ficam fora. O horizonte e o atraso já aparecem em `target_available_at`; não se resolve isso com divisão aleatória.

**`make_request`: constrói uma fronteira explícita entre treino e inferência.**

```python
"features": {
    name: float(row[name])
    for name in source["model_feature_columns"]
}
```

É uma lista explícita de 32 atributos, acompanhada dos relógios e da identidade do conjunto. A tabela original tem 55 colunas, mas o serviço não deve receber esse dataframe inteiro. `target_time` é permitido: saber a hora que se quer prever é diferente de conhecer a geração dessa hora.

**`validate_request`: transforma um pedido válido em X na ordem do treino.**

```python
pd.DataFrame(
    [[float(features[name]) for name in columns]],
    columns=columns,
)
```

O nome de cada atributo identifica seu significado. A ordem de chegada das chaves no JSON pode mudar; a matriz entregue ao estimador preserva a ordem registrada no manifesto. A função recusa alvo no pedido, nomes ausentes/adicionais, valores não finitos, meteorologia futura e incompatibilidade dos relógios.

**`predict_artifact`: carrega e aplica o objeto ajustado.**

```python
model = joblib.load(model_dir / "model.joblib")
prediction = model.predict(X)
```

Essa função não chama `fit`. A recarga dispensa repetir o ajuste para cada emissão. Os detalhes de versões e origem do artefato fazem parte da reprodutibilidade; a documentação do scikit-learn orienta manter o ambiente de dependências compatível e usar arquivos de origem confiável: [Model persistence](https://scikit-learn.org/stable/model_persistence.html).

## 4. Arquivos que você produzirá

Todos ficam em `reports/inference/CJU_BA5EIGT/h24_replay_20260801T0500Z`.

| Arquivo | O que guarda | O que permite conferir |
| --- | --- | --- |
| `model/model.joblib` | Estimador ajustado | Reutilizar os pesos sem novo ajuste |
| `model/manifest.json` | Features, parâmetros, versões, corte, contagens e hashes | Qual modelo está sendo usado e com quais restrições |
| `request.json` | 32 entradas e relógios, sem alvo | Informação entregue ao previsor |
| `prediction.json` | Previsão, persistência de referência e vínculo com artefato/pedido | Rastrear a emissão |

A função do manifesto é tornar o modelo identificável. Um arquivo de pesos sozinho não esclarece horizonte, conjunto, ordem de atributos ou corte de treino.

## 5. Evidência executada pelo professor

- Tabela real: 744 linhas e 55 colunas, com 32 entradas. Hash do CSV e dos metadados coincidem com o protocolo h24 recebido.
- Reconciliados os timestamps, calendário, deltas e janelas móveis usando os valores de geração repetidos nos lags e alvos do próprio arquivo. Isso não substitui uma leitura independente do Parquet original ou uma verificação das versões históricas do ONS.
- Treino em 717 linhas; último rótulo disponível em 01/08 às 04h UTC.
- Previsão após salvar/recarregar: **152,7141273 MWmed**. Persistência: **188,294 MWmed**.
- Inferência repetida em processo novo com a pasta de treino fora do caminho e com `fit` explicitamente proibido; mesma previsão.
- Alterar os 27 alvos indisponíveis para um valor extremo não muda as linhas/valores entregues ao treino.
- Alvo no pedido, feature ausente e meteorologia futura foram recusados. Inverter a ordem das chaves preservou X.

Ambiente do professor: Python 3.12.14, scikit-learn 1.8.0, NumPy 2.3.5, pandas 2.2.3 e joblib 1.5.3. Seu último protocolo registra scikit-learn 1.9.0. Gere seu artefato no seu ambiente; a previsão de referência não é uma exigência de igualdade numérica entre versões. As contagens e os relógios acima devem coincidir.

## 6. Sua implementação: coerência física do vento

Acrescente ao mesmo módulo uma função `validate_wind_geometry(features)` e chame-a em `validate_request`, depois das verificações numéricas e antes de montar X.

A regra é:

\[
\sqrt{\overline{u}^{\,2}+\overline{v}^{\,2}} \leq \overline{V}
\]

Aqui, `u` e `v` são as componentes médias ponderadas e `V` é a velocidade escalar média ponderada, todas em m/s. Com os pesos positivos normalizados usados no projeto, a desigualdade triangular garante que a intensidade do vetor médio não excede a média das intensidades. Direções diferentes podem se compensar.

Contrato da função que você implementará:

1. Recusar `wind_speed_mean_ms < 0`.
2. Calcular o lado esquerdo com `np.hypot(wind_u_mean_ms, wind_v_mean_ms)`.
3. Recusar quando ele superar `wind_speed_mean_ms + 1e-8`, lançando `ValueError` com mensagem específica.
4. Aceitar componentes `u` e `v` negativas: elas representam direção.

O pedido real desta aula deve continuar válido. Como contraponto, considere média escalar de 12 m/s, `u=30` m/s e `v=0`: esse pedido deve ser recusado antes da previsão. Sua implementação deve justificar a recusa pela coerência das entradas, sem depender do valor previsto pelo HGB.

Essa alteração avalia transferência: usar o significado físico de features construídas em uma aula anterior para proteger uma interface de inferência. Não é necessário aumentar a suíte geral de pytest nesta rodada.

## 7. Entrega e continuidade

Envie `prediction.json`, `request.json` e `model/manifest.json` produzidos no seu ambiente, além da função `validate_wind_geometry` que escreveu. Não é necessário enviar o arquivo binário do modelo.

Execução e autoria são evidências distintas. Confirmar o ciclo salvo/recarregado/previsto fecha a sexta macroentrega técnica; a função autoral e sua justificativa avaliam aprendizagem. A próxima unidade do produto é M05: previsão probabilística e eventos. A superioridade operacional do candidato continua sujeita às limitações registradas em E46/E47.

Léxico para esta prática: **artefato** = objeto ajustado que pode ser recarregado; **contrato de inferência** = entradas aceitas e regras que dão significado à previsão; **cutoff** = corte de conhecimento do ajuste; **replay** = reprodução de uma decisão histórica; **invariante** = relação que deve continuar válida entre entradas admissíveis.
