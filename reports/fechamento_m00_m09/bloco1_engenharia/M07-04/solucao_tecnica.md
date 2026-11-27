# M07-04 — janela, plano e medição

Solução técnica fornecida com assistência Codex. A explicação abaixo resolve as questões de engenharia pendentes; não há nova execução Spark, Databricks ou modelo.

## Janela que atravessa a meia-noite

Para emissão 02/07/2026 05h, atraso de três horas e quatro observações horárias, o fim do histórico é 02h. As medições são **01/07 23h; 02/07 00h, 01h e 02h**. A fórmula é `fim = origem - atraso`, `início = fim - (janela - 1) horas`.

A janela deve separar a identidade da série e ordenar o timestamp único. Particionar logicamente por dia perderia a medição de 23h, deixando três das quatro horas. No exemplo simulado executado, os valores 6, 8, 10 e 12 dão média 9; restringir ao dia corrente mudaria a média para 10 e a pergunta respondida.

Em grade completa, a contagem de linhas corresponde às horas esperadas. Na fonte esparsa, um deslocamento de uma linha pode pular várias horas. Duplicatas também quebram essa equivalência; precisam de política explícita antes da janela. Os casos SQL M01 verificam os dois problemas.

## O que o plano permite concluir

O `Exchange 10` do trecho histórico prepara o lado usado para broadcast no JOIN. Ele não identifica sozinho a distribuição de todas as janelas. Um plano inicial com `isFinalPlan=false` tampouco demonstra coalescência pelo AQE.

Para investigar a execução efetiva, são necessárias a árvore final após a ação e as métricas do estágio/query profile: distribuição final, tamanhos, tarefas, bytes e tempos de shuffle, broadcast e leitura. A presença de um operador não mede sua contribuição causal para o tempo total.

Photon usa execução nativa C++; o resultado não deve ser atribuído a “Java/Photon compilado por JIT”. Aquecimento, cache e agendamento continuam hipóteses para a diferença observada, sem isolamento causal no ensaio recebido.

## Como investigar os tempos sem repetir agora

O ensaio histórico mediu uma passagem de cada configuração em ordem fixa: 3,691632100 s com duas partições solicitadas e 2,993797549 s com quatro. Ambas reproduziram 7.485 linhas, sem divergências, a partir de 8.760 registros. Isso demonstra equivalência no recorte, não superioridade causal de quatro partições nem escala industrial.

Um protocolo futuro deveria fixar os bytes, versões, consulta, recursos e verificação de equivalência; separar condições frias e aquecidas; alternar ou randomizar a ordem AB/BA; repetir ambas nas mesmas condições; e registrar cada observação, mediana e dispersão. Uma intervenção específica sobre cache deve ser documentada como fator controlado. Esse desenho está proposto, não executado.

Os relógios também precisam de fronteiras explícitas. Inicialização da sessão é separada. Transformação mais comparação deve terminar após a ação materializada e o cálculo das divergências. A captura de `explain()` e do plano final fica separada. Inferência de modelo é outra fase e não foi medida por esse ensaio. Em Spark, medir apenas a criação de uma transformação preguiçosa não mede seu processamento.

## Identidades e revisões

Uma revisão Delta simulada demonstra o comportamento da transação e seu efeito nos dados, não uma retificação publicada pelo ONS nem a disponibilidade real no passado. `Table ID + Version` identifica um snapshot daquela tabela; é necessário preservar os arquivos e também vincular código, parâmetros, ambiente e hashes de entrada/saída para reproduzir a comparação.

O parecer reconciliado em `reports/scale_comparison.md` continua como evidência histórica, preservado. Nesta entrega, `janela_temporal.json` e os testes SQL/pandas fornecem a nova conferência aritmética dos limites; nenhum tempo de cluster foi reestimado.
