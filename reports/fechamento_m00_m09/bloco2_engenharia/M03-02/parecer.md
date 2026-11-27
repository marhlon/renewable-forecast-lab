# Parecer M03-02 — explicação local por Shapley de grupos

Codex, 25/11/2026. Aprovada a entrega de engenharia: método compatível com `HGB_lags24_calendar`, seis origens de julho e fundos de treino predefinidos, enumeração exata de 8 coalizões por exemplo/fundo e teste analítico linear. O modelo explicado é o melhor aprendido; isto não o promove sobre a persistência.

O jogo usa v(S)=média das previsões em linhas do fundo de treino nas quais os grupos presentes são substituídos pelos do exemplo. O fundo principal tem 16 linhas uniformemente espaçadas no treino elegível, com rótulos disponíveis antes de 01/07; a sensibilidade repete com oito linhas. Não houve amostragem de coalizões nem dependência de instalação SHAP. Os grupos particionam somente as features efetivamente usadas. Assim, a exatidão refere-se a esse jogo interventional finito, sem alegar os valores de outra definição SHAP.

O maior resíduo de aditividade |base+Σphi−previsão| foi 7.11e-15 MW. Os grupos de maior contribuição absoluta foram:

- 2026-07-01 12:00: grupo calendar, contribuição -12.919336 MW.
- 2026-07-03 12:00: grupo calendar, contribuição -13.801045 MW.
- 2026-07-05 12:00: grupo calendar, contribuição -14.188418 MW.
- 2026-07-07 12:00: grupo calendar, contribuição -14.824520 MW.
- 2026-07-10 12:00: grupo calendar, contribuição -15.066986 MW.
- 2026-07-13 12:00: grupo calendar, contribuição -13.639335 MW.

A troca de fundo alterou a contribuição em até 19.782388 MW e mudou 0 sinais entre 18 atribuições. Essa sensibilidade é registrada, sem escolher apenas exemplos estáveis. A diferença entre exemplos descreve a resposta do estimador às histórias disponíveis; não mede um efeito físico do grupo. Grupos ausentes do modelo não recebem importância zero como conclusão científica: simplesmente não fazem parte do jogo.

Lags e estatísticas são fortemente dependentes. Substituir grupos independentemente produz combinações híbridas que podem sair da distribuição real; médias e desvios podem ficar incoerentes com lags. O fundo influencia base e contribuições, e um grupo correlacionado pode dividir/absorver informação de outro. A soma exata não elimina esses limites. Não há intervenção na geração, meteorologia ou causalidade física; as atribuições são do modelo e do jogo escolhido. Sem autorização de produção e sem certificação de autonomia pessoal; revisão integradora do agente principal separada.
