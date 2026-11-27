# Aula 02 — Conferir números e a conclusão, antes de publicar

Cada tentativa tem uma `fonte` com `id, usable, k, cutoff, s1, s2`. A lógica Python já conhecida da M11.1 calcula a classe; esta unidade mapeia a classe e os valores para uma razão e os campos que a sustentam. `s1` é o pico, `s2` o melhor mínimo de um par e `k` o número de leituras da regra.

| Caso com a primeira condição aplicável | Classe | Razão | Campos exigidos em `refs` |
| --- | --- | --- | --- |
| Evidência não utilizável | `INSUFFICIENT` | `unavailable` | usable |
| Pico abaixo do corte | `BELOW` | `below` | s1, cutoff |
| Pico alcança corte, k=2, sem par utilizável | `ISOLATED` | `no_pair` | k, s1, s2, cutoff |
| Pico alcança corte, k=2, par abaixo | `ISOLATED` | `pair_below` | k, s1, s2, cutoff |
| k=1, pico alcança corte | `ELIGIBLE` | `single_met` | k, s1, cutoff |
| k=2, par alcança corte | `ELIGIBLE` | `pair_met` | k, s2, cutoff |

As referências são nomes de campos da mesma evidência, não links nem garantia de causalidade. A lista exige um conjunto por razão, sem repetição. A fonte não registra ocorrência física, pelo que `physical_cause` e `incident_detected` são exemplos de afirmações que cabem no tipo de razão, mas não passam pela fidelidade. Permitir esses códigos no esquema, nesta aula, deixa a falha visível no nível certo. A lista de razões é outro limite explícito: este laboratório não pontua alucinação em prosa livre.

## Sua implementação

Abra `notebooks/m11_2_fidelidade_autoral.py` na pasta do P3. `esperado` já é o resultado escrito por Python a partir da fonte; você implementa o comparador, sem recalcular o diagnóstico em outro lugar.

1. Compare `id` e `code`; acumule os erros, sem devolver no primeiro.
2. Para `cutoff`, `s1` e `s2`, compare os nulos primeiro e só converta strings com `Decimal`. Exemplo: `"0.70"` e `"0.700"` valem o mesmo. Já `"0.6999999999999999999"` é menor que `"0.70"`; em ponto flutuante esses dois números podem colapsar no mesmo valor. A regra original conta igualdade, o que muda a classe.
3. Confronte a razão com o que a fonte sustenta. Compare os conjuntos de referências e o comprimento da lista original para não perder duplicações. Use os nomes dos erros de [COMECE_M11_2.md](../COMECE_M11_2.md).

Se as referências esperadas são `["k","s1","s2","cutoff"]` e o candidato trouxe `["k","s1","cutoff","usable","s1"]`, o contrato tem **três** ocorrências: ausente `s2`, extra `usable`, repetida `s1`. Aceitar por “maioria de campos coincidentes” não é uma boa regra para esse uso.

## O que efetivamente sai

Em `tentativas.jsonl`, cada linha guarda a proposta textual, o objeto tipado quando houve, a etapa, os motivos e o campo `publicado`. Se houver desvio, a rota `fallback` produz um objeto novo a partir da fonte. Se o candidato passar, a rota `conferido` ainda copia o texto decimal original e usa uma frase controlada para a razão. O caso é auditável sem usar prosa livre do modelo nem autorizar qualquer ação. Uma fonte inválida é erro de entrada e interrompe a avaliação; o fallback não fabrica uma decisão para dados inconsistentes.

**Pergunta prática:** em dois casos, ambos o candidato e o fallback podem dizer `ISOLATED`. Mostre como distinguir “modelo acertou” de “Python recuperou uma proposta incorreta”, usando os campos da trilha.
