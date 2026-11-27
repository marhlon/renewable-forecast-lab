# M10.4 — aceite técnico da função e revisão da evidência

**24/11/2026.** A função em NumPy foi transcrita do código enviado, executada em Linux com as versões numéricas do laboratório (NumPy 2.5.3, pandas 3.0.5, scikit-learn 1.9.0) e conferida contra a referência nas grades reais, anos e IDs. Passou nas sete contraprovas e reproduziu por SHA-256 as oito saídas esperadas. A execução de revisão é `20261124T161841Z_1ffa116d`.

O recibo anexado é da **referência Linux distribuída no ZIP** (`20261123T235056Z_d98b7536`), com `authorship_sha256: null`. Todos os seus oito arquivos coincidem com os hashes declarados. Isso não é um recibo do modo autoral Windows. O aceite técnico decorre da execução do código colado nesta revisão. As respostas 2 e 3 foram mencionadas, mas seu texto completo não veio anexado; não houve nota para o que não chegou.

| Trabalho verificável | Resultado |
| --- | --- |
| Janela e lacunas | Zera o contador em instante inválido; exige k posições consecutivas; índice final e primeiro empate corretos. |
| Dois mecanismos de silêncio | Três canais: S1=0,716436 já abaixo de 0,719944. Sem 52/semente 17: quatro pontos no corte, mas S2=0,691564 < 0,720127. |
| Contraprova | Sem 52 e com k=1, os quatro pontos isolados abririam quatro sequências. O número de IDs depende da interseção e das regras de atribuição, não só da contagem. |
| Ablação | Sem 50, id_145 é perdido nas sementes 17, 29 e 41 em 2008–2010. A grade, os IDs e as regras de disponibilidade foram conservados. Isso mede sensibilidade do detector; não localiza uma causa física. |
| Decisão | 0/8 nas 12 combinações retrospectivas em 2011–2013. Não promover. Uma proposta nova exige dados ainda não usados na seleção e critério de detecção, atrasos e carga definido antes. |

O laço requer espaço auxiliar constante além dos vetores convertidos e leva O(nk) pelo mínimo de cada fatia. Com k=1 ou 2 atende bem; para uma janela grande, recalcule o mínimo com deque monotônica se medição justificar.

Não há necessidade de repetir a M10.4 para avançar. O P2 continua exploratório. M11 inicia o P3: resumir evidências preservando o que a regra e os registros dizem.
