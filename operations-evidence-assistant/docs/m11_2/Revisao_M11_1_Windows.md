# Revisão M11.1 — execução Windows e autoria aceitas

**24/11/2026.** Execução Windows `20261124T182345Z_2a298bc9`, CPU, dois threads. A função colada tem o mesmo SHA-256 que o arquivo executado. Sete hashes de saída, cinco textos de tokenização, 19 decodificações e os seis tempos da trajetória forçada foram reconciliados sem carregar os pesos. A função reproduziu as seis contraprovas e 256 escolhas calculadas por uma implementação independente com Decimal. O recibo do runner registra as 216 comparações sobre logits reais; a trilha parcial não permite recalculá-las na íntegra. Os 13 testes adicionais citados não foram anexados.

| Pergunta | Parecer |
| --- | --- |
| Tokens e embeddings | Aceita. Os probes 0 e 2 têm 18 tokens; muda apenas a posição 10, de 28 para 30. O ID 42 tem o mesmo embedding de entrada; a diferença contextual reportada é 1,933714. Isso não valida comparações numéricas em texto. |
| Decodificação e orçamento | Aceita. O texto curto é o prefixo longo e para pelo limite, não por EOS. Em T=0,35 e semente 17, `ELIGIBLE` passou na forma, mas a evidência pede `ISOLATED`. |
| Custo e arquitetura | Aceita. Estado serializado de 513,219 para 209,624 MiB; na mesma trajetória, mediana de 1.985,22 para 1.604,86 ms (−19,1595%). A primeira rodada INT8 foi mais lenta. Não mede RAM, produção nem conservação de fidelidade. |
| Qualidade | 0/6 códigos válidos e corretos em cada precisão greedy; os seis pares têm sequências diferentes. A regra e qualquer autorização ficam em código. |

A escolha por ordenação completa custa O(V log V) para V logits. Um heap top-k pode reduzir o trabalho quando k é pequeno, mas isso não explica o ganho medido na trajetória forçada: o benchmark mantinha os tokens fixos e não chamava o sampler. Sem necessidade de repetir a M11.1. A M11.2 conserva a evidência e verifica a recomendação de separar esquema, fidelidade e fallback.
