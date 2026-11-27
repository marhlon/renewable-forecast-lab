# Parecer da demonstração M02-03

Responsável: Codex, construção e execução assistidas. A família de quatro testes, o efeito mínimo de 1 e alpha Bonferroni de 0.0125 foram fixados antes da geração.

- B1: média 0.926374; p ingênuo 0.680591; p por blocos 0.536043; limite inferior ajustado -1.198458; rejeição = False.
- B2: média 0.185770; p ingênuo 1; p por blocos 0.870856; limite inferior ajustado -1.625885; rejeição = False.
- B3: média -0.071972; p ingênuo 1; p por blocos 0.969702; limite inferior ajustado -1.414253; rejeição = False.
- B4: média 0.334224; p ingênuo 1; p por blocos 0.846241; limite inferior ajustado -1.318383; rejeição = False.

O teste principal usa dez médias independentes pelo desenho sintético. Contar 240 horas como independentes encolhe artificialmente o erro-padrão quando as leituras compartilham um deslocamento por bloco. A coluna ingênua é diagnóstico e não decide aceite. A correção de Bonferroni controla a probabilidade de ao menos uma rejeição falsa na família, sob validade dos testes individuais; não repara dependência ignorada dentro de um teste.

As conclusões dizem respeito a diferenças sintéticas de perda. Nenhum resultado aqui sustenta superioridade de HGB, GRU ou Chronos. Não houve treino, consulta ao holdout histórico ou escolha da semente pelo resultado. Uma não rejeição limita a evidência contra H0 e não prova equivalência. A validade em uma população real precisaria de outro desenho e de dados apropriados.

Decisão: demonstração técnica executada; fechamento formativo aguarda interpretação do aluno em caso novo e revisão humana.
