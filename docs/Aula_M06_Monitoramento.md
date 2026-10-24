# M06.3 — Monitoramento que distingue causas e orienta decisões

Marlon Alves Bomfim · 05/10/2026 · P1/Renewcast

## O que já foi aceito

Você executou o lote de 24 previsões, demonstrou idempotência, escreveu a agregação SQL e distinguiu resultado ainda não disponível de observação atrasada. Sua falha simulada produziu 4/20 e 23/1 observadas/pendentes, com uma observação ausente após o prazo nos dois cortes. O custo final ficou 16 e o custo por avaliada 16/23=0,695652. Essa unidade está encerrada no escopo exercitado.

O Brier 0,137291 após retirar uma observação não comprova deterioração: você mudou a amostra avaliada. Comparações de desempenho precisam preservar o pareamento ou explicar a mudança de composição. Seu Brier original0,132603 e os valores do ambiente do professor continuam registrados separadamente.

Nesta entrega, a consulta exploratória vira um componente executável de monitoramento com contrato, regras versionadas, evidências e ações de triagem. Sua autoria será uma avaliação independente da referência e dos limites da decisão; não outra sequência de pequenas substituições de CASE.

## Objetivo e ferramentas

Ao concluir esta unidade, você deverá conseguir:

1. Separar indisponibilidade de dado, inconsistência do registro e problema de desempenho.
2. Definir indicadores com denominador correto e regras de triagem explícitas.
3. Comparar probabilidades com uma referência fixa e explicar o alcance dessa comparação.
4. Verificar a resposta do monitor a diferentes falhas, preservando os artefatos originais.
5. Produzir um parecer independente que não confunda alerta com diagnóstico causal ou autorização de retreino.

Ferramentas: sqlite3 em leitura, SQL relacional, JSON, hashlib, argparse, pathlib, relatórios HTML e testes de contratos. O monitor usa a biblioteca padrão; não exige outra instalação. Ele lê o manifesto e confere os bytes do modelo, mas não desserializa nem executa o estimador.

## Execute a entrega completa

Salve renewcast_m06_monitoramento_20261005.zip em C:\renewable-forecast-lab e execute:

```powershell
cd C:\renewable-forecast-lab
conda activate renewable-forecast
Expand-Archive -LiteralPath .\renewcast_m06_monitoramento_20261005.zip -DestinationPath . -Force
python -m renewable_forecast.event_monitor --exercise
Invoke-Item .\reports\monitoring\CJU_BA5EIGT\h24_event_batch_v1\normal\monitor.html
```

Não há novo treino, download, API aberta ou repetição do lote. O comando lê o banco já criado e gera quatro relatórios. Os incidentes são injetados em cópias temporárias; o original é aberto em modo somente leitura. Sua CTE anterior não alterou o banco, portanto não precisa ser desfeita para este comando funcionar.

Entradas padrão:

- reports/service/CJU_BA5EIGT/h24_event_batch_v1/ledger.sqlite
- models/CJU_BA5EIGT/h24_event_batch_v1/manifest.json e model.joblib
- config/monitoring_h24_v1.json
- Corte: 2026-08-02T07:00:00Z

Saída: reports/monitoring/CJU_BA5EIGT/h24_event_batch_v1. Dentro dela, normal, missing_observation, changed_probability e missing_assessment contêm monitor.html e monitor.json. exercise_summary.json reúne as quatro condutas.

Para inspecionar outro corte existente sem cenários:

```powershell
python -m renewable_forecast.event_monitor --as-of 2026-08-01T12:00:00Z --output-dir reports/monitoring/CJU_BA5EIGT/h24_event_batch_v1/partial
```

## Quatro diagnósticos e sua precedência

| Cenário | O que aconteceu | Estado/conduta esperados |
|---|---|---|
| normal |24 previsões e24 avaliações coerentes|integridade pass; dados ok; desempenho insufficient_evidence; collect_evidence|
| missing_observation |Uma observação devida está ausente; métricas dessa linha são NULL|integridade pass; dados investigate; investigate_data|
| changed_probability |A probabilidade tabular foi alterada, mas a resposta registrada não|integridade fail; métricas bloqueadas; repair_record|
| missing_assessment |Uma linha de avaliação sumiu por inteiro|cobertura de avaliação inconsistente; repair_record|

O último cenário é diferente de missing_observation. No primeiro existe uma avaliação dizendo que o dado faltou. No segundo nem a avaliação existe. Uma consulta iniciada em assessments pode simplesmente ocultar essa ausência. Por isso o monitor compara o conjunto esperado de emissões com os registros e as avaliações.

Ordem da triagem: integridade → disponibilidade → desempenho. Avaliar qualidade sobre uma probabilidade adulterada ou um processo incompleto produziria uma conclusão sem base. O monitor recomenda condutas, mas não interrompe serviços, publica alertas externos ou retreina.

## Indicadores e objetivos: SLI não é SLO

Um SLI é uma medida observada; um SLO é um objetivo para essa medida, com período, tolerância e contexto definidos.

| SLI aplicado | Fórmula/contrato | Regra didática deste lote |
|---|---|---|
| Completude das emissões |origens registradas = origens horárias esperadas|nenhuma emissão ausente|
| Completude da conciliação |uma avaliação por emissão em cada corte|nenhuma avaliação ausente|
| Completude dos rótulos devidos |observados ÷ (observados + missing_observation)|investigar qualquer ausência após prazo|
| Qualidade probabilística |Brier do modelo e da referência nas mesmas observações|comparar após 168 observados; revisão se Brier >1,10×referência|

No corte parcial, 19 awaiting_label ficam fora do denominador dos rótulos devidos. Não são 19 violações. Os objetivos acima ainda não são um SLA contratual: atraso real, tolerância da fonte e impacto de negócio precisam ser confirmados.

## Referência fixa de probabilidade

O novo artefato teve 168 eventos em 694 exemplos de treino. A referência do monitor é sempre:

\[
p_0=168/694\approx0,242075.
\]

Ela usa apenas os rótulos de treino do artefato, não a frequência do lote avaliado. Nas mesmas n emissões observadas, calculamos:

\[
BS_{modelo}=\frac1n\sum_i(p_i-y_i)^2,
\qquad BS_{ref}=\frac1n\sum_i(p_0-y_i)^2.
\]

\[
Skill=1-\frac{BS_{modelo}}{BS_{ref}}.
\]

Skill positivo significa erro probabilístico médio menor que o dessa referência na amostra; não prova calibração nem estabilidade futura. Se a referência tiver erro zero, o skill relativo fica indefinido. O relatório preserva null nesse caso.

Nos 24 resultados há 6 eventos. Seu Brier 0,132603 pode ser comparado com a referência calculada nessas mesmas 24 linhas. Isso não deve ser misturado à frequência baseline antiga de outro fold/artefato. Também não reutilizamos estes dados explorados como novo holdout independente.

## Regras explícitas, sem falsa garantia

Abra config/monitoring_h24_v1.json:

- min_observed=168: mínimo didático de uma semana de emissões horárias observadas. Não garante independência, representatividade ou significância. Uma janela com lacunas pode demorar mais de uma semana para alcançar 168 resultados.
- max_missing_observations=0: qualquer ausência devida gera investigação neste exercício.
- brier_relative_tolerance=0.1: após o mínimo, Brier maior que 110% da referência gera review_model.

Com 24 resultados, o estado é insufficient_evidence. Você ainda vê métricas, mas a regra não emite aprovação. Reduzir 168 para 24 apenas para obter um estado favorável mudaria o protocolo após observar o resultado. Qualquer regra real precisa ser definida e validada antes do período de avaliação.

Mesmo com 168 observações e disparo da regra, o monitor não prova concept drift. Erros podem vir de mudanças de vento, indisponibilidade de ativos, revisão da geração, NWP, pré-processamento ou composição da amostra. O alerta inicia investigação. Decidir retreino exige evidência e comparação temporal de um candidato.

## O que o monitor verifica no código

Leia src/renewable_forecast/event_monitor.py por estas entradas:

1. read_only: conexão URI mode=ro.
2. evaluate: fotografia consistente de leitura; conferência de manifesto/modelo/política; conjuntos de origens; pedido/resposta; relógios; rótulos; recálculo de Brier e custo.
3. select_action: precedência de integridade/dados/desempenho.
4. exercise: backup para cópias temporárias, falhas localizadas e conferência de preservação do arquivo original.
5. save_report: a mesma estrutura gera JSON para programas e HTML para leitura.

O hash confirma identidade/coerência de bytes, não a veracidade da medição física. SQLite e esses hashes não tornam os arquivos invioláveis. O monitor verifica os contratos implementados, não qualquer adulteração coordenada possível.

## Sua entrega autoral completa

Crie **notebooks/parecer_monitoramento.py**. Esta vez não há função para completar nem laço pronto: você já dispõe do banco, dos relatórios e do contrato abaixo. Implemente um programa independente que:

1. Abra ledger.sqlite em modo somente leitura e selecione somente avaliações observed do corte final, unindo-as às previsões.
2. Leia training_events/training_rows do manifesto e calcule p0. Recalcule BS_modelo, BS_ref e Skill com NumPy ou SQL, sem importar event_monitor.
3. Confira esses três valores contra normal/monitor.json com tolerância 1e-9; trate denominador zero explicitamente.
4. Leia os quatro monitor.json e grave reports/monitoring/CJU_BA5EIGT/h24_event_batch_v1/parecer.csv com scenario,integrity_status,data_status,performance_status,action,observed,missing_observation.
5. Grave parecer.md com três decisões justificadas: qual incidente priorizar, por que o caso normal ainda não libera retreino/promoção e por que missing_assessment não é sinônimo de observação atrasada.

Execute:

```powershell
python notebooks/parecer_monitoramento.py
```

Critérios de aceite: métricas independentes iguais às do monitor; quatro linhas sem misturar cenários; nenhuma alteração do banco; parecer que separa evidência, hipótese e ação. Entregue o código e os dois arquivos. Não é necessário enviar dezenas de testes ou repetir o histórico anterior.

Essa tarefa combina SQL, Python, probabilidades, contratos, diagnóstico e comunicação técnica em uma entrega de ponta a ponta. Se ela bloquear, envie o trecho e o erro; a intervenção será localizada, preservando sua autoria.

## Fixação lexical aplicada

| Termo | Frase que você deve conseguir defender com o artefato aberto |
|---|---|
| SLI |Eu medi completude somente entre rótulos cujo prazo já venceu.|
| SLO |A tolerância que dispara investigação está declarada nas regras.|
| Integridade |A tabela, o pedido e a resposta devem descrever a mesma previsão.|
| Referência fixa |Minha comparação usa a frequência do treino, sem estimá-la nos resultados do lote.|
| Triagem |Primeiro restauro confiança no registro, depois interpreto desempenho.|
| Evidência insuficiente |Posso descrever 24 erros sem declarar estabilidade operacional.|

## Limite e próximo bloco

O componente monitora um lote histórico quando executado. Não mede latência/uptime HTTP, não agenda coleta, não impõe cota de alarmes, não detecta drift estatisticamente e não constitui shadow ao vivo. Esses estados ficam explícitos no JSON/HTML.

Após esta entrega autoral, a sequência de M06 é: telemetria real do serviço e tratamento de incidentes; versão candidata/rollback; automação/empacotamento. M07–M14 permanecem no roteiro. Nada desta unidade é contado como formação concluída por percentual arbitrário.

Referências primárias: https://sre.google/sre-book/service-level-objectives/ ; https://docs.python.org/3.12/library/sqlite3.html ; https://scikit-learn.org/stable/modules/model_evaluation.html#brier-score-loss .
