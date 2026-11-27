# Aula 03 — Reduzir o tamanho sem perder de vista a tarefa

## O que foi convertido?

FP32 usa 32 bits por valor de peso. Para uma camada linear, uma representação inteira aproximada usa uma escala s, um zero z e valores q numa faixa finita. Uma forma de descrever a aproximação é `q ≈ arredondar(w/s + z)`; ao voltar para unidades do peso, `w_aprox = s * (q - z)`. Passo de arredondamento, escala e faixa introduzem erro. Uma operação com pesos próximos não precisa gerar exatamente os mesmos logits; basta mudar a ordem de duas alternativas próximas para alterar a continuação.

Neste projeto, [quantização dinâmica do PyTorch 2.7](https://docs.pytorch.org/docs/2.7/generated/torch.ao.quantization.quantize_dynamic.html) substitui as camadas `Linear` internas por versões CPU com peso `qint8`. O programa confirma o tipo de suas matrizes. Os kernels ajustam a representação das ativações durante a operação; o resto do modelo continua com componentes em ponto flutuante. Embedding e cabeça de vocabulário ficam FP32. Portanto não divida o tamanho total por quatro como previsão de economia. Isso não é treino, LoRA ou QLoRA.

## Como fizemos a comparação

Há dois experimentos, com conclusões separadas:

1. **Trabalho fixo e tempo.** Mesmo modelo de origem, prompt do caso `satmon_sem52`, ids da continuação fixados, CPU, dois threads e o mesmo número de forwards. Uma rodada de aquecimento por variante; três medidas, com ordem FP32/INT8 invertida na segunda. Medimos *prefill*, tempo total e tokens/s na parte de decodificação. A trajetória é forçada, por isso a duração da resposta gerada livremente não favorece uma variante. Compare as medianas, não o melhor número. O tamanho é o `state_dict` serializado temporariamente; não mede RAM de pico nem o download original do modelo.
2. **Comportamento.** A geração greedy roda nas duas precisões sobre os mesmos seis casos. O programa conta uma linha de código válida e depois se ela confere com o esperado. A parte textual fica às claras no CSV; não é validada automaticamente pela contagem de códigos. A referência para a classe é a regra do projeto, que usa `Decimal` para comparar escores. A igualdade no limiar é incluída. Em SatMon, `ELIGIBLE` significa que o critério admite confirmação em algum ponto; não dá crédito de detecção a nenhum ID.

O estado serializado medido no Linux de referência caiu de cerca de **513 MiB para 210 MiB** (redução de **59,2%**). Abra `resultado.json → quantizacao.medianas` e use os **seus** tempos de CPU. Por exemplo, um ganho de 35% na mediana de tempo seria `1 − t_int8/t_fp32`, enquanto ganho de vazão seria `v_int8/v_fp32 − 1`; as duas medidas não têm a mesma escala percentual. É um laboratório com três rodadas e uma trajetória para custo. Não use como teste de carga ou inferência de latência de produção.

## Decisão sobre o uso do LLM

Na referência, as duas precisões tiveram **0/6 códigos greedy válidos**. Dizer que quantizar preservou qualidade porque “0/6 = 0/6” seria errado: a referência já falhou, e as seis continuações mudaram. Em `satmon_tres_canais`, a saída INT8 começou a escrever `0.716435…` como corte, embora esse prefixo pertença ao pico e o corte seja `0.719944…`. É um erro concreto de campo, ainda que o texto pareça cuidadoso. Há também uma saída amostrada que fornece `ELIGIBLE` como primeira linha, exatamente no formato, para a evidência `satmon_sem52`, cujo código correto é `ISOLATED`.

A comparação de números, estados sem resposta e autorização de alarmes ficam em código verificável. A geração pode ajudar a explicar uma decisão, mas só depois de receber dados identificados e ter as afirmações avaliadas. A M11.2 vai separar três erros: JSON malformado, campo numericamente infiel e afirmação que não tem fonte. A quantização reduz custo de uma implementação específica; não conserta nenhum desses erros por si só.

**Transferência:** se um LLM não puder calcular o código, seria suficiente obrigá-lo a emitir JSON? Use uma saída da rodada para defender sua resposta e diga qual parte do próximo relatório deve ser copiada e verificada em vez de inferida.
