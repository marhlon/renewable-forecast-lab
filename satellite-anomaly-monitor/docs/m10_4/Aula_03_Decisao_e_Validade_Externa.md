# Aula 03 — Decisão e validade externa

Imagine que alguém proponha baixar o corte hoje porque o 0/8 ficou ruim. Isso pode até mudar as métricas antigas, mas gasta aqueles oito casos para decidir o parâmetro. A nova regra já “viu” esses casos; relatar o resultado como confirmação independente responde à pergunta errada.

A decisão com os dados disponíveis é **manter a referência para estudo e não promover nenhuma variante**. O 0/8 atingiu todas as 12 combinações desta rodada. O orçamento nominal foi respeitado no exemplo justamente quando a detecção falhou. Um serviço que não emite alertas pode ter taxa zero com oito perdas. O custo importante inclui as perdas, o tempo até o primeiro alarme e o trabalho causado por alarmes sem anotação ou repetidos. As anotações retrospectivas limitam o que sabemos sobre “falso”.

| Pergunta de revisão | Evidência disponível | O que ainda falta |
| --- | --- | --- |
| Por que não houve alertas? | Original: S1 abaixo do corte. Em algumas ablações, S1 passa e S2 não. | Entender por que o escore, a cadência e a incidência anotada mudaram. |
| Retirar canais resolve? | Coorte fixa, três sementes, AP e IDs pareados; nenhuma variante detectou os oito IDs posteriores. | Comparação em outra missão ou período ainda não usado para uma regra candidata. |
| O canal que mudou causou a anomalia? | Quantis, correlações e efeito de remover uma entrada no detector. | Regime de operação, unidades, origem das medições e investigação do evento. |

### Como desenhar a prova seguinte

1. Escreva a pergunta antes do experimento. Por exemplo: “um detector mais sensível a mudanças entre canais ganha detecção por ID sem exceder o orçamento e sem aumentar o atraso?” Especifique hipótese e regra do candidato. Uma hipótese plausível é uma feature de diferença normalizada entre canais, calculada em instantes válidos, com escala do ajuste. Ela não precisa de rede neural para ser confrontada com o baseline neste volume.
2. Fixe ajuste, calibração de regra usando período de desenvolvimento, e um período confirmatório futuro, outra missão ou grupo nunca usado para selecionar. Defina o contrato de horário e de atraso de observação. Estabeleça o que fazer com ausência de canal, intervalos ignorados e IDs sem observação. Não confunda quantil com probabilidade ou com orçamento real.
3. Fixe métrica principal de episódios e a decisão antes de abrir o período: mesmos IDs observáveis, limite de inícios sem anotação por dia equivalente, distribuição dos atrasos e a contagem de repetidos. Compare com o baseline no mesmo relógio. Se a amostra for pequena, reporte o numerador e o denominador, liste os IDs que mudaram e trate a conclusão como limitada. Milhares de slots sobrepostos não são milhares de episódios independentes.

Até aqui, a competência demonstrada é como **refutar a explicação errada com um teste controlado**. Em um serviço Renewcast, uma checagem análoga distinguiria “nenhuma probabilidade atingiu 0,5 nas emissões utilizáveis” de “houve probabilidade acima de 0,5, mas o cliente bloqueou por atualidade ou o serviço não respondeu”. O evento de telemetria e a previsão de geração são produtos distintos; transfere-se o diagnóstico, não as métricas ou o modelo.

A M10.4 encerra o laboratório do P2 quando a cadeia acima puder ser defendida com seus próprios resultados. O M11 começa o P3, com aplicação generativa e critérios próprios; a pendência de produção do Renewcast continua no seu inventário.
