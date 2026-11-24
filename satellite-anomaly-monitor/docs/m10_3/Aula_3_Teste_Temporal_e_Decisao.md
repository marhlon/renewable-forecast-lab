# Aula 3 — quando a política vence no desenvolvimento e fica muda no teste

## 1. O que foi congelado e o que foi transportado

Os escores do M10.2 selecionam a política em 2008–2010. Os parâmetros do pontuador vêm de 2004–2007; nenhum parâmetro é aprendido novamente do desenvolvimento ou do teste. Com robusto ou PCA, o script usa mediana, escala e, quando pertinente, a base do PCA gravados no recibo. Com Isolation Forest, as árvores não foram serializadas no M10.2: o script reconstitui apenas esse estimador no ajuste original, com a mesma semente e configuração. Antes de abrir o teste, confere a reconstrução dos escores e dos disparos de 2008–2010 contra o resultado Windows recebido.

Só depois de gravar a política a avaliação lê 2011–2013. É o mesmo satélite/missão e os mesmos três canais, com grade de 15 min, amostra anterior de até 180 s e nenhuma amostra atravessando a fronteira do período. Não há IDs em comum entre as partições. Essa separação testa **transferência temporal na missão**, sem pretensão de transferir entre missões. Como em M10.2, o instante de medição serve como disponibilidade por hipótese; não conhecemos latência real de ingestão ou severidade física.

## 2. Referência executada sobre seus escores Windows

O critério escolheu **Isolation Forest, escore ≥ 0,7199442558330269, duas leituras**. O valor aparece para mais de um quantil candidato por empate dos escores; o desempate escolheu 0,9995. Houve 2.822 leituras atingindo o corte no desenvolvimento; 0,9995 não equivale a deixar exatamente 0,05% em alerta.

| Resultado | Desenvolvimento 2008–2010 | Teste 2011–2013 |
| --- | ---: | ---: |
| Instantes utilizáveis | 105.165 | 105.212 |
| IDs detectados / observáveis | 3/8 | **0/8** |
| Inícios de alarme totais | 15 | 0 |
| Com primeiro crédito / repetidos / sem anotação / ignorados | 3 / 6 / 4 / 2 | 0 / 0 / 0 / 0 |
| Precisão dos inícios avaliáveis | 3/13 = 23,08% | Indefinida |
| Dias equivalentes sem anotação | 1.053,47 | 1.065,21 |
| Alarmes sem anotação por dia equivalente | 0,003797 | 0 |
| Atraso mediano dos detectados | 26,83 min | Indefinido |
| Pontos que atingiram o limiar | 2.822 | **0** |
| Maior escore utilizável | 0,75939973 | **0,71643597** |

O diagnóstico imediato está nas últimas duas linhas: **nenhum escore utilizável alcançou o corte**. Permitir apenas uma leitura não teria mudado as detecções mantendo o mesmo limiar. A ausência de disparo, aqui, não se explica só por falta de dados ou por confirmação em duas leituras. O resultado é compatível com uma escala/distribuição de escores diferente entre períodos; a tabela, sozinha, não identifica mudança física de regime, problema de manutenção ou causa instrumental.

Também havia apenas oito IDs observáveis. Informe o número de IDs junto do percentual. Zero alarmes sem anotação acompanha oito eventos observáveis perdidos; não é razão para recomendar a política. Sem início avaliável, o cálculo de precisão seria 0/0 e não deve virar 100% nem 0%. O relatório retém esse valor ausente. Finalmente, nem a AP de 0,7581 do M10.2 nem o sucesso de reprodução da floresta são garantias de serviço de alerta.

**Decisão de referência:** não promover esta política. Preservar a avaliação atual, diagnosticar por período/canal e comparar ablações no M10.4. Qualquer nova regra de limiar precisa ser formulada em desenvolvimento; depois de usar 2011–2013 para investigação, esse mesmo recorte deixa de servir como teste independente para a regra nova.

## 3. Devolutiva e critério de revisão

Cole `iniciar_alarmes` e responda ao [modelo](Resposta_M10_3.md). Em cada item, apresente uma conta ou uma evidência reproduzível e uma conclusão. Vou separar:

| Critério | O que precisa ficar demonstrado |
| --- | --- |
| Implementação | Respeita linha ausente, limiar inclusivo, primeiro disparo e invariância ao futuro. Concorda com a referência em desenvolvimento e no teste. |
| Avaliação | Calcula a taxa usando exposição e distingue o ID, o início do alarme e um instante acima do corte. Trata precisão sem alarmes como indefinida. |
| Transferência | Distingue um corte nunca cruzado de cruzamentos esparsos sem confirmação. Defende uma hipótese para M10.4 que pode ser testada sem otimizar no teste já visto. |

M10.4 usa a decomposição da falha para perguntar se um canal, uma combinação de canais ou um regime alterou a distribuição do escore. O propósito é comparar ablações e estabilidade, mantendo o resultado original.

Fonte dos dados: [ESA Anomaly Dataset v2](https://zenodo.org/records/15237121), DOI 10.5281/zenodo.15237121, European Space Agency, [CC BY 3.0 IGO](https://creativecommons.org/licenses/by/3.0/igo/). Grade e protocolo foram adaptados para a formação. A referência foi reconstituída e executada em Linux sobre as saídas Windows recebidas; esta não é uma medição de operação ou uma validação da sua execução M10.3 ainda não recebida.
