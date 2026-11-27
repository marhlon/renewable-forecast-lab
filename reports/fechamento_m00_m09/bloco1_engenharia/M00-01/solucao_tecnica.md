# M00-01 — diagnóstico e adaptação temporal aplicados

Solução técnica fornecida com assistência Codex. O objetivo é entregar a análise e sua execução verificável, sem exigir exame, professor ou resposta independente.

## Contrato do caso

A emissão é 02/07/2026 às 04h no relógio de referência, com atraso de três horas, horizonte de doze horas e janela de quatro horas. O último rótulo de medição elegível é 01h. A janela inclusiva contém **01/07 22h, 23h; 02/07 00h e 01h**. O alvo é 02/07 16h; sua disponibilidade seria 19h sob a mesma hipótese de atraso.

Uma medição rotulada 02h, disponibilizada às 05h pela regra simulada, é rejeitada na emissão 04h. O filtro precisa conferir `available_at <= origem`, além da faixa temporal; conhecer depois o valor não permite usá-lo retrospectivamente nessa emissão.

No executor novo, os valores simulados desses quatro instantes são 4, 6, 8 e 10, com média 7. A seleção SQL é confrontada com a seleção pandas e com as quatro horas fixadas antes da execução. Ao retirar uma medição, a janela deixa de estar completa: uma média completa não é publicada; permanece desconhecida. Isso é um controle de contrato, não uma previsão de um modelo.

## Rastreio da aplicação existente

1. `pyproject.toml` registra `renewcast = renewable_forecast.cli:main`.
2. `cli.main` interpreta o subcomando e encaminha `predict` a `run_predict_command`.
3. Esse handler chama `modeling.predict_next(model_dir, input_path)`.
4. `predict_next` exige metadados e diretório do modelo; carrega o artefato MLflow, lê e ordena o Parquet.
5. O alvo desse fluxo inicial é o maior timestamp da série mais uma hora. Acrescenta uma linha futura com geração desconhecida, chama `build_feature_frame(require_target=False)` e seleciona uma única linha de `FEATURE_COLUMNS`.
6. A previsão usa essa linha; a persistência usa a última geração observada. A geração futura desconhecida não é substituída por zero para construir a entrada.

Essa leitura do código não executou o modelo. O fluxo inicial é h+1 relativo ao fim da série fornecida; não recebe uma origem de parede e atraso de três horas. Mudar apenas o número do horizonte na saída não o tornaria um modelo h+12. Uma implementação preditiva desse novo contrato exigiria preparação e artefato compatíveis, fora da execução sem treino desta entrega.

## Ordem de diagnóstico adotada

Primeiro identifico interpretador, ambiente, comando, arquivo e hashes. Depois verifico esquema, tipos, chave, ordenação, calendário, ausências e disponibilidade; só então considero a construção de features e a compatibilidade do artefato. O mesmo sintoma aparente pode vir de um caminho errado, duplicata, lacuna, janela incompleta ou hipótese temporal diferente.

A adaptação entregue está em `../M01-02/executar.py`, função `clock_case`: parâmetro de origem, atraso, janela, horizonte e filtro de disponibilidade são explícitos. `janela.csv`, `janela_temporal.json` e `resultado.json` registram o resultado observado. Não houve treino, inferência, substituição de artefato ou alteração do comando h+1 existente.

O relógio físico e a publicação da fonte continuam sujeitos aos limites externos M04; aqui a aritmética usa rótulos de referência declarados.
