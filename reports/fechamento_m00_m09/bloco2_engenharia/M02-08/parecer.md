# Parecer técnico assistido — M02-08

25/11/2026 · Responsável: Codex, agente de bootstrap e auditoria do bloco 2.

**Decisão: aprovado no escopo técnico de engenharia atribuído.** Foram localizadas execuções completas anteriores à retomada, com quatro recibos, comandos reais e exit codes 0. A auditoria posterior preservou esses arquivos e conferiu protocolo prévio, hashes, pareamento, relógios internos, estimativas e todos os resumos de 6/24/48h. Não houve novo treino nem repetição dos 59 testes congelados.

C1 atendido: previsões salvas reutilizadas, 5.000 réplicas, semente 42 e blocos pré-fixados, sem refazer ajuste. C2 atendido: blocos horários circulares dentro de folds fixos, agregação ponderada por n e intervalos condicionais explicitados; todos os blocos publicados.

O ganho principal é 9,3841 MWmed (24,5773% do MAE do HGB história).
Os três intervalos agregados ficam acima de zero. Isso sustenta uma redução
condicional do erro nesse desenvolvimento em relação ao HGB de história
congelado. No fold 1, porém, os intervalos de blocos 24h e 48h incluem zero,
enquanto o de 6h fica pouco acima de zero. Os folds 2 e 3 têm intervalos
positivos nas três escolhas. A média agregada não torna uniforme a evidência
de cada semana.

A persistência já tem MAE 29,3943 MWmed, menor que os 38,1821 do HGB história.
Contra ela, o ganho do candidato é apenas 0,5963 MWmed (2,0285%); os três
intervalos agregados incluem zero. O fold 1 apresenta ganho pontual
**negativo de −7,7185**, contraposto a +4,2482 e +5,2591 nos outros folds.
Logo, esta análise não estabelece melhoria estável sobre a persistência.
Escolher apenas o contraste contra história ou apenas o bloco de 6h ocultaria
essa conclusão prática. Não há limiar econômico de benefício registrado
neste protocolo; MAE e IC por si só não encerram uma decisão de operação.

A aprovação técnica é da execução/interpretação; não implica adoção do modelo. O desenvolvimento já foi examinado, os alvos dos horizontes diferem e o fuso físico não foi homologado por esta análise. Não há validação prospectiva, autorização de produção ou revisão humana independente atribuída. A revisão integrada e a atualização do cadastro serão realizadas pelo agente principal.

Evidências: `protocolo.json`, `resultado.json`, `bootstrap.csv`, `bootstrap_vs_persistencia.csv`, `linhagem_persistencia.json`, `analise_tecnica.md` e `auditoria_final.json`.
