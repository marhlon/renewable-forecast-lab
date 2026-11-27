# Parecer aplicado — M08-03

Entrega de engenharia de 25/11/2026. Solução, execução e revisão técnica fornecidas pelo Codex. Não houve resposta independente do usuário nem certificação de autonomia. O protocolo antecipou os shapes e 273 parâmetros antes da execução. Não foram alterados módulos ou treinos históricos.

**Resultado técnico favorável ao aceite aplicado.** A GRU nova recebeu `[11,12,1]`, gerou recorrência `[11,12,8]`, estado `[1,11,8]` e previsão `[11,1]`, conforme previsto. Nos três lotes os tamanhos foram 4, 4 e 3. Há 264 parâmetros recorrentes mais nove da cabeça, total de 273.

O MSE por exemplo foi **5,603784129359859**, exatamente a soma dos 11 erros quadráticos dividida por 11. A média incorreta das três perdas médias por lote seria **6,324715874928384**. A diferença demonstra a importância do denominador por exemplo quando o último lote é menor; o CSV preserva os 11 termos utilizados.

O avaliador preservou `state_dict`, pesos, gradientes preexistentes e ausentes, flags mistas de treino/avaliação e estado do gerador aleatório. Isso foi conferido no sucesso e em quatro falhas: alvo com dimensão incorreta após um lote válido, NaN após um lote válido, loader vazio e janela de 11 posições indevidamente fornecida. Os modos são restaurados individualmente em `finally`, evitando que `train()` recursivo apague a configuração mista original. Não houve passo de otimizador nem alteração de gradientes.

Repetição da chamada e permutação do batch confirmaram estado reiniciado por janela, sem ligação entre exemplos. A implementação NumPy preservada das portas r/z/n foi aplicada aos mesmos pesos em 12 passos; a maior diferença para a GRU PyTorch foi **2,220446049250313e−16**, abaixo de `1e−12`. No PyTorch, r multiplica o termo recorrente já transformado e com seu viés; z pesa o estado anterior em `h=(1−z)n+zh_anterior`.

A separação temporal usa origem sintética t14, disponibilidade `evento+4` e janela t−1..t10, com alvo t15 separado. A alteração de todos os valores indisponíveis t11 em diante deixou a previsão com diferença zero. O controle que os incluiu indevidamente na janela mudou a saída em **0,2879685512583976**, mostrando que o modelo responde aos valores vazados. Não é um teste de disponibilidade publicada real.

O runner terminou com retorno 0 e 12 conferências do item aprovadas. O teste específico também passou. Os pesos são aleatórios e as entradas são sintéticas: demonstram adaptação de shape, batching, avaliação e estado, sem evidência de acurácia ou generalização. O material atende à engenharia aplicada e não demonstra autoria independente ou operação contínua.

Evidências: `protocolo.json`, `resultado.json`, `avaliacao_11_exemplos.csv`, `notebooks/bloco3_transferencia_neural.py`, `tests/test_bloco3_transferencia_neural.py` e `docs/roadmap_m00_m09/Bloco_3_Transferencia_Neural.md`.
