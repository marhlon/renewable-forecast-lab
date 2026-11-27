# M01-01 — defesa independente pendente

O exemplo A/B de janeiro no guia é uma demonstração resolvida e assistida.
As perguntas abaixo usam um caso novo, ainda não calculado pelo laboratório.

Para a série C, entre 10/02/2027 22h e 12/02/2027 00h, inclusive, existem:

| Instante | Valor |
|---|---:|
| 10/02 22h | 5 |
| 10/02 23h | 0 |
| 11/02 01h | NULL |
| 11/02 02h | 7 |
| 11/02 02h | 9 |
| 12/02 00h | 4 |

1. Declare a chave, a granularidade e a política para as duas linhas repetidas. Não apague uma delas silenciosamente.
2. Preveja manualmente a saída diária, dizendo se o denominador é um dia completo ou apenas as horas do recorte.
3. Compare LEFT e INNER JOIN nesse recorte parcial: o que deve constar no calendário esperado?
4. Qual instante aparece em LAG de uma linha na fonte e na grade completa? Como a passagem de meia-noite muda a janela?
5. Explique por que um valor zero pode entrar na média e uma ausência não deve ser preenchida como geração zero.

Conta prévia: **a preencher**.
SQL/adaptação: **a preencher**.
Resultado e reconciliação: **a preencher**.
Assistência e revisão: **pendentes**.
