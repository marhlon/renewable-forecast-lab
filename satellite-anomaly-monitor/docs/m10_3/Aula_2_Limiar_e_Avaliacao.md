# Aula 2 — qual limiar merece passar do desenvolvimento?

**Problema.** Descer o limiar pode aumentar o número de detecções e consumir a capacidade de investigação. Subir demais pode produzir uma regra silenciosa. Vamos comparar políticas contra um orçamento explícito e usar a mesma exposição para todos os candidatos. O teto é didático, não veio de um acordo de operação com a ESA.

## 1. Fixe a unidade a ser avaliada

**Evento** é um ID `Anomaly`, representado pela união de seus intervalos anotados nos três canais. Preservamos descontinuidades: se um ID tem dois intervalos separados, o tempo entre eles não vira positivo. **Alarme** é um início produzido pela sua função. Um início só pode dar crédito a um ID. Se mais de um ID ainda não detectado estiver ativo, vence o intervalo ativo que termina primeiro; empate por ID. Um novo alarme num evento já detectado é repetição, sem crédito adicional. Um alarme que começou antes do intervalo não ganha crédito retroativo, mesmo se sua sequência continuar no evento.

Um ID é **observável** quando pelo menos um instante de sua união de intervalos é utilizável, sem sobreposição com `Rare Event` ou `Communication Gap`. Isso não garante que a regra de confirmação consiga capturá-lo. Anote separadamente eventos sem oportunidade de observação. Inícios em `Rare Event` ou `Communication Gap` ficam na classe “ignorados” para esta avaliação. Fora de todas as categorias, registramos **alarme sem anotação**: proxy de falso alarme. A falta de rótulo não prova ausência de falha.

## 2. Calcule os denominadores antes de interpretar

| Métrica | Numerador e denominador | Cuidado |
| --- | --- | --- |
| Recall entre observáveis | IDs com primeiro alarme / IDs observáveis | Relate também detectados / todos os IDs. |
| Precisão dos inícios avaliáveis | Inícios com primeiro crédito / todos os inícios menos os ignorados | Repetições gastam capacidade; não entram no numerador. Sem início avaliável, precisão indefinida. |
| Taxa de alarmes sem anotação | Inícios sem anotação / (instantes utilizáveis sem anotação / 96) | Um “dia equivalente” são 96 intervalos de 15 min de exposição; dias de calendário não servem de denominador quando a cobertura muda. |
| Atraso | Primeiro início creditado menos primeiro início anotado do ID, em minutos | Mediana e P90 consideram só IDs detectados. Sem detecção, ficam indefinidos. |

**Conta manual.** Um ID começa às 08h07. O primeiro alerta dentro da anotação é às 08h30, e outro às 08h45 está dentro do mesmo evento. Há também um alerta às 09h30 sem anotação e dois em categoria ignorada. São cinco inícios no total, três avaliáveis e um com primeiro crédito: precisão de 1/3. O atraso do ID é 23 min, e a repetição não cria outro evento. Suponha 192 instantes utilizáveis sem anotação: isso soma 2 dias equivalentes, logo a taxa sem anotação é 0,5/dia. Se houver outros dois IDs, um observável mas perdido e outro sem instante elegível, o recall observável é 1/2 e o recall sobre todos os IDs é 1/3.

`cobertura_canais_teste.csv` responde uma pergunta retrospectiva: para IDs observáveis em determinado canal, quantos receberam o primeiro alarme dentro de uma anotação **daquele canal**? O escore combina os três; isso não diagnostica qual sensor causou o alarme nem mede três detectores separados. A mesma notificação pode aparecer na visão de vários canais do mesmo ID; não some os numeradores para estimar recall global.

## 3. Seleção feita somente em 2008–2010

1. Dos escores utilizáveis de cada método, extraia 11 quantis com `method="higher"`. O corte é um número na escala do método. Quantil de 0,99 não é probabilidade do evento. Empates de escore podem produzir limiares iguais entre quantis diferentes e incluir mais pontos que a cauda nominal.
2. Aplique a mesma regra de **duas leituras** a cada um dos 33 pares método–quantil, na grade inteira. Só depois associe os inícios aos IDs e calcule a exposição.
3. Considere viáveis candidatos com pelo menos um ID detectado e **até 0,50 alarme sem anotação por dia equivalente**. Entre eles, maximize IDs detectados. Nos empates, minimize taxa sem anotação e depois atraso mediano; persistindo, use a ordem fixa robusto → PCA → floresta, e por fim o quantil maior.
4. Grave método, limiar, confirmações, versão e recibo em `politica_congelada.json`. Se nenhum candidato for viável, pare: o teste não é usado para buscar outro.

Note a escolha de desenho: o orçamento conta alarmes sem anotação, mas não controla sozinho a carga total de investigação. Também reportamos repetidos e ignorados. Se o custo de perder um evento for dominante, a preferência por menos alarmes como desempate pode ser conservadora demais. Uma regra alternativa seria um experimento novo, definido no desenvolvimento e avaliado em outro período. Não mude esse critério depois de ver o resultado reservado.

**Código para ler.** Em `scripts/executar_m10_3.py`, `escolher` gera os candidatos a partir dos escores já existentes. Em `src/satmon/alarmes_m10_3.py`, `Avaliador` recebe a grade completa, atribui início a ID e mede a exposição. Sua função de alarme entra **antes** dessa associação. O protocolo desta aula é didático; consulte o [artigo ESA-ADB](https://arxiv.org/abs/2406.17826) para o benchmark publicado, que possui outras regras de avaliação.
