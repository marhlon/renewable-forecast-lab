# Parecer aplicado — M08-02

Entrega de engenharia de 25/11/2026, solução e interpretação fornecidas pelo Codex. Não foi recebida uma defesa independente do usuário nem é certificado domínio pessoal. O protocolo foi registrado antes dos cálculos desta rodada; o código e as entradas foram conferidos contra os hashes antes da execução. O run preservado não foi treinado novamente.

**Resultado técnico favorável ao aceite aplicado.** As 168 origens são as mesmas em HGB e nas três GRUs, com igualdade de alvos e erros recalculados. O SHA-256 de `predictions.csv` coincide com o recibo histórico. O runner terminou com retorno 0; as oito conferências do item passaram. Os números são em MWmed, exceto a perda quadrática em MWmed².

| Método | Semente | MAE | RMSE | Viés previsão−alvo | RMSE centrado |
| --- | ---: | ---: | ---: | ---: | ---: |
| HGB | 17 | 32,323956 | 44,221683 | −13,119039 | 42,230890 |
| GRU | 17 | 35,675970 | 45,200733 | −18,525120 | 41,230161 |
| GRU | 29 | 34,911227 | 43,816199 | −17,993098 | 39,951317 |
| GRU | 41 | 34,573202 | 43,066020 | −14,777710 | 40,451222 |

As três GRUs perdem no MAE: diferenças GRU−HGB de +3,352014, +2,587271 e +2,249246. As sementes 29 e 41 ganham no RMSE em 0,405484 e 1,155663; a 17 perde 0,979050. Não se selecionou a melhor semente após olhar a avaliação. O MAE GRU mediano é 34,911227, com mínimo 34,573202, máximo 35,675970 e desvio amostral entre sementes de 0,564976. A dispersão de RMSE entre sementes é 1,082951. Essas estatísticas não quantificam incerteza de generalização.

Os vieses negativos indicam subestimação média. O sinal é o inverso do parecer histórico, que definiu viés como observado−previsto; não é uma mudança dos resultados. Nas três GRUs o deslocamento médio é maior em magnitude que no HGB, mas o RMSE centrado é menor. Isso explica por que subestimação média maior pode coexistir com RMSE menor: a menor dispersão pode compensar o deslocamento na identidade RMSE² = viés² + erro centrado².

O diagnóstico por origem identifica a razão da discordância das perdas. A GRU ganha em erro absoluto em apenas 64/168, 76/168 e 72/168 origens, respectivamente. Nas sementes 29 e 41, a soma das diferenças quadráticas nas cinco origens mais favoráveis é −23.111,034088 e −23.453,535824; nas outras 163 origens é +17.113,771442 e +6.506,507213. Portanto o ganho agregado de MSE depende de redução forte em poucos erros grandes, enquanto o conjunto restante prejudica a GRU. Essa decomposição é descritiva e não exclui observações do resultado.

Por exemplo, em 10/07/2026 02h, o erro absoluto do HGB é 95,479344, contra 55,456199 da GRU29; a diferença de perda quadrática é −6.040,915176. Na origem seguinte, HGB erra 87,631901 e GRU29 51,601218, diferença −5.016,664327. Em 03/07/2026 04h, HGB erra 133,058943 e GRU41 108,747766, diferença −5.878,605767. Esses timestamps nomeiam as origens preservadas; o alvo de cada uma está 24 horas adiante. As 504 linhas pareadas estão em `perdas_por_origem.csv`.

Sob a restrição registrada de custo linear do erro, prioridade MAE e orçamento CPU, mantenho HGB como referência de desenvolvimento. Seu menor MAE é consistente contra as três sementes; o custo histórico de ajuste também foi menor, embora os tempos não sejam benchmark controlado de inferência. Uma aplicação que penalize fortemente erros extremos pode preferir investigar a hipótese favorecida pelo RMSE, mas ainda deve fixar política de sementes, custo, tolerância de viés e comparação futura antes de decidir. Nem HGB nem GRU estão promovidos à operação por este parecer.

Mudariam a decisão novos períodos com protocolo congelado, seleção fora do teste, comparação pareada, ganho no custo de uso declarado e medição controlada de inferência, além de disponibilidade histórica comprovada. A semana reanalisada já era desenvolvimento examinado. Mantêm-se as hipóteses de atraso de geração de duas horas e o limite de fuso/versões físicas não comprovados. Não houve novos dados ou evidência operacional.

Evidências: `protocolo.json`, `resultado.json`, `metricas.csv`, `perdas_por_origem.csv`; a explicação integrada está em `docs/roadmap_m00_m09/Bloco_3_Transferencia_Neural.md`. Valida-se a solução aplicada, sem atribuir ao usuário uma resposta não recebida.
