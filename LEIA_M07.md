# M07.1 — revisão de 19/10/2026

Leia `docs/Revisao_M07_1_20261019.md` para aplicar a correção com backup.
Este pacote substitui a inicialização que falhou no ZIP de17/10 e corrige as contagens da tentativa recebida.

A próxima execução é `python scripts/executar_m07_spark.py --autoria`.
Após sucesso, compare com `--autoria --shuffle-partitions 4` e conclua `reports/scale_comparison.md`.
Não extraia o ZIP antigo por cima desta revisão. A aula original continua válida nos conceitos; os comandos de retomada estão na revisão.

Os arquivos em docs/Verificacao_E97_Professor.json e docs/Comparacao_SQL_E97.csv registram somente a verificação do professor em Linux nativo. Não substituem o recibo Docker/Windows do aluno.
