# M08.2 — aceite da entrega e alcance da evidência

Registro E112, 15/11/2026. Entrega recebida em texto: função `avaliar_lotes` e parecer referente à execução Windows de 05/11/2026, `20261105T152149Z_941d0398`. Implementação e redação assistidas por Codex, conforme declaração de Marlon A. Bomfim. Aceite nesse escopo; não certifica autoria independente.

A função cumpre o contrato: acumula a soma dos erros quadráticos e divide pelo número de exemplos; usa `eval()` e `no_grad()`; preserva modos mistos por submódulo em `finally`; rejeita lote de formato incorreto, loader vazio e erro não finito. A diferença é calculada no dtype da previsão/alvo, e só depois convertida para float64; o quadrado e a soma são em float64. O parecer descreve corretamente essa precisão. Não é necessário reescrever o avaliador nem repetir o M08.2.

Nesta revisão a função recebida foi transcrita e executada em PyTorch 2.7.1+cpu. Conferências: lote 4+1 com MSE=20; modos mistos restaurados no sucesso e nas exceções; pesos e gradientes preservados; rejeição de shape incompatível, loader vazio, NaN e soma quadrática infinita. O relatório técnico M08.3 registra essa verificação. Isso confere a função apresentada, não autentica os arquivos Windows que não foram anexados.

| Critério do parecer | Avaliação |
| --- | --- |
| Janela e disponibilidade | Origem 03/07 04h, histórico 02/07 03h–03/07 02h, alvo 04/07 04h; disponibilidade 06h assumida. Mantido o eixo sem fuso físico validado. |
| Separação temporal | 7.079 ajuste, 168 seleção, 168 avaliação, 52 exclusões por disponibilidade e 18 janelas incompletas. `shuffle` só no ajuste, sem reorganizar o interior da janela. |
| Época e checkpoint | Seleção decide a época; avaliação não escolhe semente. Curvas em `eval()` distinguem-se da perda online com Dropout e pesos em atualização. |
| Comparação | MLP não ganha em MAE nas três sementes; a semente 29 perde por 0,022147 MWmed. As três melhoram RMSE frente ao linear, coerentemente com uma perda quadrática, sem provar superioridade geral. |
| Complexidade | MLP tem 833 parâmetros; linear, 25. Ganho mediano de MAE sobre o linear é 0,518876 MWmed, aproximadamente 1,54%. A faixa de sementes não é intervalo de confiança. |
| Decisão | Manter o linear como referência simples e a MLP como candidata de estudo é compatível com os resultados e o escopo de uma semana já examinada. |

Valores de MAE relatados: persistência 37,991646; linear 33,678664; MLP sementes 17/29/41: 32,724828 / 33,700811 / 33,159788 MWmed. Viés observado−previsto continua positivo nos modelos aprendidos. O relato de diferença zero no recarregamento e identidade byte a byte entre execuções Windows permanece evidência declarada pelo aluno, não uma auditoria dos arquivos ausentes.

**Estado:** M08.2 encerrado no escopo da entrega assistida. Próxima unidade M08.3: recorrência, GRU e comparação pareada com HGB, mantendo a base temporal. M07 e M08.1 não são reabertos. M08 completo e comparação fundacional continuam pendentes; nenhum percentual global de formação foi calculado.
