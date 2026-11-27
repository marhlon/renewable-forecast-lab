# Parecer de engenharia — global multissérie

Solução fornecida, executada e analisada por Codex. Seleção prévia por metadata: CEECVA, CEEMAU, CEUCZ, CEUFM; 744 registros por série na origem. O mesmo outubro já estava no disco e uma outra série já fora examinada no bloco 2. Este é estudo retrospectivo exploratório novo nas quatro séries, não teste final intocado.

Foram comparados um HGB global, quatro HGB locais e persistência disponível t−2, nas mesmas origens e alvo t+1h. Treino só com label_available_at estritamente anterior a 16/10; maior disponibilidade admitida 2026-10-15 23:00:00. Não houve normalizador ou cadastro externo, ajuste em validação/teste ou promoção do P1. Coortes totais: {'train': 1332, 'validation': 576, 'test': 956}.

Erro em MW e viés são comparados por série e microagregado. Escalas diferentes tornam MAE agregado sensível ao porte das usinas. A comparação não mede generalização para séries nunca vistas, outras estações, fuso validado ou disponibilidade histórica. Ganho positivo não condiciona aceite de engenharia C1/C2. Métricas completas no CSV e resultado.json; operação continua separada.

## Interpretação dos resultados executados

As quatro séries são eólicas do Ceará. O código escolheu seus ids pela ordem lexicográfica e cobertura de timestamps, sem usar geração ou erro para ordenar candidatos. A cobertura 744 foi verificada no mês completo: é uma seleção retrospectiva de um universo com dados disponíveis, não prova de que esse cadastro/cobertura fossem conhecidos em 16/10. As quatro categorias efetivamente aparecem no treino. Nenhuma estatística de normalização, capacidade externa ou valor do alvo de teste entra nos atributos.

| Série ou agregado | N teste | MAE global MW | MAE local MW | MAE persistência MW |
| --- | ---: | ---: | ---: | ---: |
| CEECVA | 239 | 0,972872 | 0,987465 | 0,583297 |
| CEEMAU | 239 | 2,809614 | 2,713715 | 4,661912 |
| CEUCZ | 239 | 7,933634 | 8,631439 | 6,615253 |
| CEUFM | 239 | 12,206883 | 12,372471 | 20,393228 |
| Microagregado | 956 | 5,980751 | 6,176272 | 8,063423 |

O global reduz o MAE agregado em aproximadamente 25,8% frente à persistência e 3,2% frente aos locais. Esse resultado não é uniforme: a persistência vence em CEECVA e CEUCZ; o global vence em CEEMAU e CEUFM. Contra o local, o global vence em três séries, mas perde CEEMAU. Na validação, o agregado local (6,077012 MW) foi melhor que o global (6,198759 MW), outra razão para não escolher um vencedor universal a partir de poucos dias. Os hiperparâmetros foram mantidos em ambos os recortes.

O RMSE de teste é 9,902025 MW no global, 10,451806 no local e 15,262370 na persistência. O viés global agregado de −0,101754 MW esconde compensação entre CEUCZ (+2,030379 MW) e CEUFM (−2,508647 MW). Logo, viés agregado perto de zero não comprova ausência de erro sistemático por usina.

A persistência usa a última medição disponível t−2 para prever t+1; com a latência hipotética, são três horas entre a observação usada e o alvo. O treino removeu, em cada série, as origens 15/10 21h, 22h e 23h porque seus rótulos chegariam à meia-noite ou depois. Além das 24 primeiras origens necessárias à lag24, o último horário do mês foi excluído porque o alvo seria novembro. Restaram 333 origens de treino, 144 de validação e 239 de teste por série. O ajuste único consumiu 0,3919 s de parede no global e 0,6683 s somando os quatro locais; são medições curtas de fit, sem medir inferência ou custo sustentado.

O ganho observado justifica manter o global como alternativa para outro protocolo prévio em mais séries/meses. Não justifica substituir o modelo P1, misturar este alvo h+1 com o benchmark h+24 ou aprovar produção. Não foi estimada incerteza de generalização neste pequeno estudo.
