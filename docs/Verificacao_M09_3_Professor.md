# M09.3 — verificação do professor

17/11/2026. Run final `20261117T160556Z_cc6dd09f`. Controlador executado em Linux/Python3.12.14,
criando ambiente privado novo com dependências fixadas, depois reutilizando-o offline.
PyTorch2.7.1+cpu, Chronos1.5.3, Transformers4.49.0, CPU2threads/float32.

O snapshot oficial Chronos-Bolt Tiny foi baixado e validado por tamanho/SHA256.
8.652.672 parâmetros congelados; nenhum fit ou passo de otimizador.
O pacote de entrada é a referência LinuxM07.3 preservada das etapas anteriores,
não declarado binariamente idêntico ao Windows. Baselines são os artefatos LinuxM08.3,
sem novos ajustes. A execução Windows usará os baselines locais do aluno.

Resultados: MAE31,340739, RMSE45,380137, viés observado−previsto+2,962412 MWmed.
HGB dessa referência: MAE31,846768 e RMSE44,051119. GanhoMAE1,59%, RMSE pior.
Cobertura brutaP10–P90=80,3571%; largura83,5952 MWmed; nenhum cruzamento entre
P10/P50/P90, sem clipping/recalibração. Não se afirma superioridade geral.

A auditoria independente verificou oito grupos: hashes, dez variantes pareadas,
30 métricas, alinhamento26 passos/contraprova24, pinball/cobertura, repetição,
reprodução em ambiente privado e snapshot. Maior diferença das métricas7,11e-15;
inferência repetida com diferença zero. Os recibos completos estão na pasta de evidências.

Tempo dos lotes na execução final: 0.1959s, separado de carga,
aquecimento, download e instalação. Pico do processo: 528.77MiB;
não é memória exclusiva dos pesos. Não comparar esse tempo com treinamento das redes.

A disponibilidade de wheelsWindows/Python3.12 foi conferida no PyPI para dependências
compiladas; isso não substitui uma execução Windows, que não foi feita nesta sessão.
A combinação fixada pode emitir aviso upstream de cache legado do Transformers;
a referência executou e suas saídas foram conferidas. Não se suprimem outros erros.

Fuso/disponibilidade permanecem assumidos conformeM07/M08. Sobreposição com o corpus
de pré-treino não verificada. A semana já foi examinada e não é novo holdout.
Nenhuma mudança no serviço operacional existente foi realizada.
