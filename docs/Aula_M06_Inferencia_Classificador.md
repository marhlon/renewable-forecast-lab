# M06 — da tabela de features à decisão por HTTP

Marlon Alves Bomfim · Renewcast · 04/10/2026 · E68

## Entrega e aprendizagem

A nova rota **POST /predict-decision** recebe 32 features, executa o HGB classificador salvo, extrai a probabilidade da classe evento=1 e aplica a política selecionada. O cliente não envia p_event, target_generation ou event_drop. A rota /decisions permanece disponível para o replay anterior.

Ao terminar, você terá um classificador persistido, um contrato de entrada que independe da ordem das chaves, inferência fora do processo de treino, identificação do modelo/política e um experimento autoral de sensibilidade. O resultado técnico desta entrega foi verificado pelo professor; sua reprodução e a função autoral serão registradas separadamente.

| Camada | Arquivo no projeto | Responsabilidade |
|---|---|---|
| Construção do artefato | src/renewable_forecast/event_artifact.py → build_artifact | Selecionar treino elegível, ajustar uma vez e gravar modelo, manifesto e pedido |
| Contrato e inferência | Mesmo módulo → EventPredictRequest e EventRuntime | Validar entrada, conferir artefato, organizar X e chamar predict_proba |
| Interface | src/renewable_forecast/decision_api.py | Expor /predict-decision, /model, /health e preservar /decisions |
| Cliente | notebooks/consultar_api_inferencia.py | Enviar features e registrar a resposta calculada |
| Autoria | notebooks/inspecao_cenarios_evento.py → escalar_vento | Transformar coerentemente o vento e investigar a sensibilidade |

## 1. Instalar os arquivos e construir o artefato

Baixe **renewcast_m06_inferencia_20261004.zip** para **C:\renewable-forecast-lab**. Pare o servidor anterior com Ctrl+C. No PowerShell da raiz do projeto:

```powershell
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m06_inferencia_20261004.zip -DestinationPath . -Force
python -m renewable_forecast.event_artifact --input-dir data/interim/modeling/CJU_BA5EIGT/h24_d2_july_development --policy reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json --output-dir models/CJU_BA5EIGT/h24_event_api_v1 --forecast-origin 2026-08-01T05:00:00Z --threads 2
```

As dependências já pertencem ao ambiente utilizado nas etapas anteriores. O comando usa a tabela mensal h24 e a política existentes; não consulta meteorologia nem refaz a busca de parâmetros. Ele faz **um novo ajuste final de desenvolvimento do classificador** para criar o artefato que a API precisa carregar. Os estimadores dos folds anteriores não foram preservados pelo experimento.

Com a tabela recebida, o resultado é **717 linhas de treino, 170 eventos e 32 features**, de 744 linhas disponíveis. São elegíveis somente linhas em que forecast_origin < corte e target_available_at < corte. O último rótulo elegível ficou disponível em **01/08/2026 04 UTC**, antes do corte **05 UTC**. As 27 linhas restantes não entram no ajuste.

Arquivos produzidos em models/CJU_BA5EIGT/h24_event_api_v1:

- model.joblib: estimador ajustado;
- manifest.json: nomes e ordem das features, versões, hashes, corte e identidade do evento/política;
- example_request.json: features reais da emissão escolhida, sem o alvo nem probabilidade pronta.

Executar novamente com os mesmos arquivos e contrato reutiliza o artefato. Uma configuração diferente exige outra pasta; não há substituição silenciosa do modelo.

## 2. Iniciar o servidor com o modelo

Após a construção terminar sem erro, execute no mesmo terminal:

```powershell
python -m renewable_forecast.decision_api --policy reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json --model-dir models/CJU_BA5EIGT/h24_event_api_v1 --port 8000 --threads 2
```

Deixe o processo aberto quando aparecer Uvicorn running on http://127.0.0.1:8000. O modelo é carregado uma vez na inicialização. A API não chama fit, não lê model_frame.csv e não refaz features a partir de dados brutos: recebe a tabela de atributos já preparada por seu fluxo anterior.

O serviço confere o hash do modelo e o contrato lógico da política, além das versões das bibliotecas registradas. A identidade lógica da política ignora ordem das chaves e quebras LF/CRLF; a resposta também conserva o SHA-256 dos bytes do arquivo efetivamente carregado.

Esse artefato é gerado e servido no seu próprio ambiente. Não inclui um joblib treinado no ambiente do professor: carregar estimadores entre versões diferentes de scikit-learn não é suportado. Use arquivos de modelo que você gerou e controla; um hash confere correspondência de bytes, não certifica a origem de um arquivo desconhecido.

## 3. Fazer a primeira inferência

Abra um segundo PowerShell:

```powershell
cd C:\renewable-forecast-lab
conda activate renewable-forecast
python notebooks/consultar_api_inferencia.py
```

O cliente envia example_request.json para **POST /predict-decision**. Também confere três riscos concretos: ordem invertida das features não altera a resposta; feature ausente é rejeitada; tentativa de fornecer p_event é rejeitada. Isso não exige reexecutar a suíte completa do projeto.

No ambiente do professor, o resultado foi:

```text
Inferência: HTTP 200
forecast_origin: 2026-08-01T05:00:00Z
target_time: 2026-08-02T05:00:00Z
last_available_generation: 188.294 MWmed
event_generation_at_or_below_mwmed: 165.524 MWmed
p_event: 0.20179188830321645
threshold: 0.5
alarm: false
feature_count: 32
estimator_executed: true
model_retrained: false
```

A geração de referência é 188,294. O evento definido no projeto é o valor no alvo ser menor ou igual a **188,294 − 22,77 = 165,524 MWmed**. O modelo retornou cerca de 20,18% para esse evento. Isso não significa 20,18% de acurácia nem probabilidade de qualquer queda durante as próximas 24 horas.

O valor acima é uma referência calculada com scikit-learn 1.8.0; o artefato produzido no Windows pode dar outro valor se as versões/implementações forem diferentes. O aceite exige contrato e resultado coerentes, e não igualdade de um número entre ambientes distintos. As versões utilizadas ficam no manifesto.

Saídas locais em **reports/service/CJU_BA5EIGT/h24_event_inference_v1**: request.json, prediction.json, verification.json e respostas das contraprovas. Para inspecionar no navegador, abra http://127.0.0.1:8000/docs e escolha **POST /predict-decision**, exemplo **features_reais**. Ele já contém as 32 entradas. GET /model mostra corte e esquema do estimador carregado.

## 4. Parte autoral: sensibilidade física do vento

Abra **notebooks/inspecao_cenarios_evento.py** e implemente somente **escalar_vento(features, fator)**, substituindo o NotImplementedError. O programa de chamadas/relatório já está pronto; o fluxo principal da API funciona sem essa atividade.

Hipótese do cenário: todas as velocidades locais do vento são multiplicadas pelo mesmo fator s, preservando direção, pesos espaciais e todo o histórico da geração. Construa três cenários: **0,8; 1,0; 1,2**. Eles são perturbações hipotéticas das features, não novas rodadas NWP observadas.

Derive as transformações antes de codificar:

| Feature | Transformação quando v_i passa a s·v_i, com s >= 0 |
|---|---|
| wind_speed_mean_ms | A média ponderada fica s vezes maior |
| wind_speed_spatial_std_ms | O desvio espacial fica s vezes maior |
| wind_u_mean_ms e wind_v_mean_ms | As componentes ficam s vezes maiores; preserve seus sinais |
| wind_speed_cubed_mean_m3s3 | A média dos cubos fica s³ vezes maior |
| Outras 27 features | Permanecem idênticas |

A última linha de vento representa Σ w_i v_i³. Para s=1,2, o multiplicador é **1,728**, não 1,2. Não substitua essa grandeza pelo cubo da velocidade média: em geral Σ w_i v_i³ difere de (Σ w_i v_i)³. Essa distinção liga unidades físicas à engenharia de atributos.

Requisitos da sua função: devolver uma cópia; preservar as chaves; rejeitar fator negativo, booleano, textual, NaN ou infinito; aceitar zero. Use os nomes explícitos de WIND_LINEAR e WIND_CUBIC. Componentes u/v podem ser negativas; não aplique restrição de velocidade escalar a elas.

Depois execute, com o servidor aberto:

```powershell
python notebooks/inspecao_cenarios_evento.py
```

O programa confere sua transformação e salva **scenarios/scenarios.csv** e **scenarios/requests_responses.json** dentro da pasta de inferência. Registra probabilidade, mudança em pontos percentuais, alarme e os mesmos hashes de modelo/política. A ordem esperada das probabilidades é uma hipótese a investigar, não uma condição imposta ao teste: esse HGB não tem restrição monotônica.

**Sua análise deve responder:** a probabilidade cresceu ou caiu com o vento? O alarme mudou? Houve resposta não monotônica? O que o resultado diz sobre a função aprendida — e o que ele não permite afirmar sobre geração real? Essa análise é de sensibilidade do modelo, não estimação de efeito causal ou validação de calibração.

## 5. Critérios de aceite e limites

Para fechar esta unidade técnica, envie **prediction.json** e **verification.json** da nova pasta. Para registrar autonomia, envie sua função escalar_vento, o CSV de cenários e uma interpretação curta. Não é necessário enviar o binário joblib.

O professor verificou: treino real; CLI e cliente HTTP em processos separados; inicialização e inferência com o diretório da tabela de treino indisponível; resposta com fit proibido; ordem das features invariável; rejeição de feature ausente/adicional, tipo inválido, alvo/probabilidade injetados, relógios incompatíveis, meteorologia futura, modelo adulterado e política trocada. /decisions continua atendendo ao contrato anterior. Registros estão em docs/evidencias_m06_inferencia/.

Esta execução prova integração de engenharia. Usa features históricas e uma política escolhida retrospectivamente no desenvolvimento, não uma política que comprovadamente existia naquela emissão de agosto. Os parâmetros também vieram de desenvolvimento que incluiu julho. Não é um novo backtest causal, holdout ou aprovação operacional. A inferência respeita o corte de rótulos do ajuste, mas isso sozinho não elimina a seleção retrospectiva da política/parâmetros.

Disponibilidade, fuso/semântica temporal e cadastro mantêm as hipóteses já registradas. O serviço ainda não coleta fontes, monitora resultados ou controla cota acumulada de alarmes. M06 permanece em andamento; esta entrega avança a integração do estimador.

## Fixação lexical

| Termo | Operação concreta | Confusão a evitar |
|---|---|---|
| fit / ajuste | Aprender o classificador com 717 linhas elegíveis | Fazer fit a cada chamada de previsão |
| persistência do modelo | Salvar/carregar model.joblib | Confundir com o baseline de persistência da geração |
| manifest / manifesto | Relacionar esquema, versões, corte e identidade | Tratar qualquer arquivo .joblib como compatível |
| feature schema | Montar X na ordem registrada em feature_columns | Usar a ordem de chegada do dicionário |
| predict_proba | Selecionar a coluna correspondente a classes_=1 | Usar predict e chamar 0/1 de probabilidade |
| inference / inferência | Executar o estimador salvo sobre as features | Reenviar uma probabilidade pronta e dizer que o modelo executou |
| sensitivity / sensibilidade | Alterar entradas hipotéticas mantendo modelo fixo | Afirmar causalidade física a partir da resposta do modelo |

Referências oficiais: [persistência de modelos scikit-learn](https://scikit-learn.org/stable/model_persistence.html) e [HistGradientBoostingClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html).
