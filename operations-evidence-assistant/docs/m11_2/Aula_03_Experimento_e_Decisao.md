# Aula 03 — Um exemplo no prompt resolve qual problema?

Comparamos `zero_shot` e `um_exemplo`. Instruções, modelo, FP32, dois threads, greedy, casos e teto de 120 novos tokens são os mesmos. A segunda versão acrescenta **um** par de registro e resultado, fora dos conjuntos de avaliação. Isso permite associar uma diferença neste ensaio à adição do exemplo, embora não permita concluir que qualquer exemplo ou modelo se comportará assim. Prompt maior também consome mais tokens de entrada. O limite local de 768 verifica prompt + saída antes da inferência; texto perdido por orçamento não é reparado.

## Como ler as métricas

Seis casos de desenvolvimento, os mesmos da M11.1, passam por ambos os prompts. Em cada braço, partindo do total:

- `json_ok`: passou pelo parser estrito — objeto e tipo ainda podem estar errados.
- `esquema_ok`: passou pelo contrato Pydantic — valor ou conclusão ainda podem divergir.
- `fiel`: passou pelas três etapas sobre a resposta bruta. `fiel_entre_esquema = fiel / esquema_ok`; se nenhum candidato passou no esquema, fica indefinida, não zero.
- `fallback`: caso resgatado pela rotina determinística. `publicado_conferido` inclui esse resgate; seu denominador é a carga do sistema, não um placar de qualidade do LLM.

Exemplo hipotético: de seis casos, 5 passaram no JSON, 3 no esquema e 1 na fidelidade. São 1/6 fiéis entre todas as respostas, 1/3 entre objetos tipados e 5/6 fallbacks. Uma tabela dizendo só “6/6 publicados” confundiria duas coisas que levam a decisões diferentes.

## Como escolher sem usar o futuro como régua

A ordem é predefinida: maior `fiel`, maior `esquema_ok`, menos tokens novos e, em empate, ordem do protocolo. O programa grava `decisao_prompt.json` **antes de ler** os seis cenários sintéticos reservados e roda apenas o escolhido neles. A conclusão sobre a superioridade relativa continua sendo deste desenvolvimento; não há comparação pareada dos dois prompts no reservado. A escolha também não equivale a um limite de aprovação: dois prompts podem ser ruins e ainda existir um escolhido para medir.

O reservado cobre falta, fronteira de corte, sem par e confirmações com k diferente. Os casos são sintéticos e estão no pacote para reprodução; não são teste externo nem conjunto de avaliação cego. Se você ler os resultados e trocar o exemplo, passe a tratar esses seis casos como desenvolvimento para a próxima iteração. Registre um novo conjunto antes de comparar adaptações de pesos.

## O que aconteceu na referência

| Partição | Prompt | JSON | Esquema | Fiel | Fallback | Tokens de entrada / novos |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Desenvolvimento | zero_shot | 5/6 | 0/6 | 0/6 | 6/6 | 1.881 / 375 |
| Desenvolvimento | um_exemplo | 0/6 | 0/6 | 0/6 | 6/6 | 2.451 / 720 |
| Reservado sintético | zero_shot, congelado | 6/6 | 0/6 | 0/6 | 6/6 | 1.807 / 265 |

No caso `renewcast_replay`, `zero_shot` copiou a entrada e terminou: o JSON trouxe `k` e `usable`, que o esquema de saída proíbe, e omitiu `code`, `reason` e `refs`. Essa não é uma falha da comparação por Decimal: a saída nunca chegou lá. Os dois braços empataram em fidelidade e esquema. O que decidiu foi a quantidade de tokens **novos** (375 contra 720), não a taxonomia de parse. O exemplo acrescentou 95 tokens de entrada por caso; as seis saídas bateram no teto nessa variante.

Nenhum candidato real passou pelo esquema nesta referência. A camada semântica foi exercitada pelas 16 contraprovas, incluindo entradas tipadas corretas e erradas. Não estime da execução uma taxa de checagem factual em prosa ou em objetos que não chegaram ao validador.

## A decisão de arquitetura

Use o [relatório de referência](../evidencias_m11_2/relatorio.html) para ver um candidato, seus erros e o resultado publicado. Compare a fidelidade antes do fallback e o tamanho da entrada ao avaliar o exemplo. Uma queda de erros de parse não basta para autorizar publicação direta. Se o relatório determinístico já cumpre o uso pretendido e os ganhos de texto não foram demonstrados, ele é a alternativa de menor complexidade para esse escopo.

A M11.3 usará a mesma ideia: comparar um modelo adaptado contra prompting e contra a regra, estratificar falhas e olhar entradas realmente separadas da adaptação. Formato válido por restrição de saída, quando usado, resolve uma camada; a fidelidade ainda requer evidência.
