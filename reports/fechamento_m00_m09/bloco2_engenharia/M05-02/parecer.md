# M05-02 — calibrar probabilidades não garante a melhor política

25/11/2026 · avaliação retrospectiva executada · entrega de engenharia

O HGB, o calibrador Platt e a política foram congelados antes da obtenção do arquivo de avaliação. A aplicação única terminou com código 0, sobre as mesmas 695 origens dos outros estudos M05. Houve 117 eventos positivos, ou 16,8345%. O evento compara geração disponível e geração alvo separadas por 26 horas; não é uma rampa horária.

## Probabilidade: melhora agregada com instabilidade por semana

| Probabilidade | Brier | Log loss | AP |
| --- | ---: | ---: | ---: |
| HGB bruto | 0,085677 | 0,250749 | 0,687644 |
| HGB com Platt congelado | 0,083296 | 0,243630 | 0,687644 |
| Frequência fixa do treino | 0,140752 | 0,455717 | 0,168345 |

Brier é a média de `(probabilidade − classe real)²`. Log loss penaliza especialmente probabilidades confiantes erradas; menor é melhor nas duas métricas. AP resume o ranking; maior é melhor. O calibrador melhorou Brier e log loss no agregado, mas preservou a ordenação neste ensaio e, consequentemente, a mesma AP. A frequência constante do treino foi 19,5679%, acima dos 16,8345% de eventos observados no recorte.

A melhora não foi uniforme. Na semana 4, o Brier piorou de 0,093479 para 0,105639; na parte final de 23 horas, de 0,060842 para 0,069523. As outras três semanas completas melhoraram. O agregado não autoriza chamar as probabilidades de operacionalmente calibradas para qualquer período.

A tabela de confiabilidade contém dez faixas fixas e também as contagens. Por exemplo, entre as 93 previsões brutas na faixa de 0,5 a 0,6, a probabilidade média foi 54,2825%, mas os eventos ocorreram em 36,5591%. No calibrado, a faixa de 0,2 a 0,3 contém 45 previsões, média de 25,7710% e frequência observada de 35,5556%. Ainda existem desvios. As faixas reagrupam amostras depois da transformação e não devem ser comparadas como pares de observações idênticas. Faixas vazias ou com poucos exemplos não sustentam conclusões fortes.

## Alarmes: o corte escolhido em julho perdeu de uma comparação fixada

Todas as quatro regras abaixo estavam definidas antes da avaliação. Cada uma aplica o mesmo orçamento causal: no máximo os seis primeiros casos elegíveis de cada dia, sem ordenar o dia usando escores futuros. Os custos relativos são FP=1 e FN=4.

| Regra | TP | FP | FN | Alarmes | Custo |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bruto, corte 0,5 | 45 | 70 | 72 | 115 | 358 |
| Calibrado, corte 0,5 | 43 | 12 | 74 | 55 | 308 |
| Frequência, corte 0,5 | 0 | 0 | 117 | 0 | 468 |
| Política congelada: calibrado, corte 0,3 | 48 | 78 | 69 | 126 | 354 |

O corte 0,3 escolhido no desenvolvimento não foi o de menor custo entre essas comparações de outubro. O custo da política congelada foi `78 + 4×69 = 354`, ou 0,509353 por origem. A comparação calibrada em 0,5 custou `12 + 4×74 = 308`, com menos cinco acertos positivos e menos 66 falsos positivos. Não substituímos a política pela regra que ficou melhor depois de observar a avaliação.

Baixar o corte não implica apenas acrescentar os alarmes do corte maior: com orçamento causal, casos elegíveis mais cedo podem consumir a capacidade diária antes de casos posteriores. O cálculo respeitou essa regra, sem selecionar retrospectivamente os maiores escores de cada dia. O arquivo diário confirma que nenhuma regra excedeu seis alarmes no dia. Essa verificação demonstra a aplicação do limite no replay de arquivos, não a operação de um serviço contínuo.

O custo por origem da política congelada variou entre 0,279762 e 0,625 nas quatro semanas completas. Na primeira semana, ela custou 105, contra 104 da referência que nunca alarma. A variação temporal e a perda para a comparação em 0,5 impedem defender o corte escolhido como uma decisão estável já aprovada para produção.

## Decisão e limites

O item foi executado e documentado: há probabilidades brutas, calibradas e constantes; confiabilidade; seleção separada; política congelada; e um orçamento aplicado sem antecipação. O resultado da política continua limitado. Não houve novo treino, recalibração ou troca de corte depois da avaliação.

Uma política futura exige custos e capacidade de negócio definidos, além de outro período ainda não usado para escolher parâmetros. O snapshot de outubro foi obtido agora e não comprova a versão historicamente publicada em cada origem. Os horários e o atraso de duas horas continuam hipóteses. Não houve shadow ao vivo, implantação ou monitoramento contínuo.

O [método](metodo_ajuste.md) descreve as amostras e a escolha do corte. [calibracao_classe.csv](calibracao_classe.csv), [confiabilidade.csv](confiabilidade.csv), [alarmes.csv](alarmes.csv), [orcamento_diario.csv](orcamento_diario.csv) e [resultado.json](resultado.json) preservam a evidência. Implementação, execução e revisão com assistência de Codex; não há certificação de autonomia pessoal do usuário.
