# Parecer técnico assistido — M02-07

25/11/2026 · Responsável: Codex, agente de bootstrap e auditoria do bloco 2.

**Decisão: aprovado no escopo técnico de engenharia atribuído.** Foram localizadas execuções completas anteriores à retomada, com quatro recibos, comandos reais e exit codes 0. A auditoria posterior preservou esses arquivos e conferiu protocolo prévio, hashes, pareamento, relógios internos, estimativas e todos os resumos de 6/24/48h. Não houve novo treino nem repetição dos 59 testes congelados.

A transferência aplicada usou h+6 como outro recorte, registrado antes da análise, com efeito e incerteza próprios. A resposta técnica explica a mudança de conclusão contra persistência e os limites da comparação entre horizontes. O critério antigo de resposta independente permanece histórico; esta entrega fornece a solução e não certifica autonomia.

O ganho principal é 6,2904 MWmed (19,2106% do MAE do HGB história).
Os três intervalos agregados ficam acima de zero; as frações ≤ 0 são 0,
0 e 0,0004. A última corresponde a 2 de 5.000 réplicas, sem interpretação
de p-valor. A heterogeneidade semanal permanece: o fold 2 inclui zero
com bloco de 6h, mas tem intervalos positivos com 24h/48h; no fold 3
acontece a inversão. O fold 1 tem ganho maior, 11,8074 MWmed, com os três
intervalos positivos. Dependência serial e truncamento do último bloco
podem tornar a largura não monotônica; não se exige que todo bloco maior
gere todo intervalo maior, nem se escolhe a conclusão mais conveniente.

Contra persistência, o ganho é 33,8080 MWmed (56,1017%), com intervalos
agregados positivos em 6/24/48h. Ainda assim, o fold 1 tem ganho apenas
3,6740 e intervalos cruzando zero nas três escolhas, enquanto os folds 2 e 3
mostram ganhos de 51,3050 e 46,4450. O efeito agregado forte está ligado
a essas duas semanas; não é evidência de benefício uniforme em todo regime.

A aprovação técnica é da execução/interpretação; não implica adoção do modelo. O desenvolvimento já foi examinado, os alvos dos horizontes diferem e o fuso físico não foi homologado por esta análise. Não há validação prospectiva, autorização de produção ou revisão humana independente atribuída. A revisão integrada e a atualização do cadastro serão realizadas pelo agente principal.

Evidências: `protocolo.json`, `resultado.json`, `bootstrap.csv`, `bootstrap_vs_persistencia.csv`, `linhagem_persistencia.json`, `analise_tecnica.md` e `auditoria_final.json`.
