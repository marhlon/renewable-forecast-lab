# Parecer M03-03 — seleção e avaliação congeladas

Codex, 25/11/2026. Aprovada a entrega de engenharia: oito candidatos e grupos fixados antes do ajuste, coorte comum, três folds temporais com purga, baseline e custos computacionais registrados. Vencedor: HGB_lags24_calendar; estudo aprendido: HGB_lags24_calendar.

A avaliação nova de outubro aplicou o artefato congelado sem ajuste: MAE selecionado 19.520624 MW, persistência 19.218456 MW e aprendido 19.520624 MW, 695 origens. O ganho não era condição de aceite; qualquer piora é conservada. Acesso ao teste ocorreu depois dos congelamentos segundo o protocolo geral. Sem certificação de autonomia pessoal ou aprovação operacional; revisão integradora do agente principal separada.

O HGB **perdeu na métrica primária**, com MAE 0,302168 MW maior, aproximadamente 1,57% de piora. Sua RMSE foi menor, 24,989582 MW frente a 31,732297 MW da persistência, mas esse diagnóstico não substitui a MAE previamente escolhida. O viés, definido como previsão menos observado, foi +1,054634 MW no HGB e +0,732986 MW na persistência. Não há evidência de superioridade por MAE para recomendar promoção do HGB neste recorte. O vencedor do desenvolvimento e seus parâmetros foram preservados; não se trocou o modelo após observar o teste.

A inferência única terminou em 25/11/2026 às 19:55:10 UTC, usando o snapshot de outubro obtido somente após o selo integrado. Outubro é posterior ao treino e à calibração na série, mas anterior ao protocolo real de novembro: trata-se de **avaliação retrospectiva em snapshot novo e reservado**, não de coleta prospectiva, publicação historicamente point-in-time ou shadow ao vivo. O mês passa a ser examinado a partir desta execução. Qualquer nova escolha após esse resultado precisará de protocolo e avaliação segregada novos; não reapresentar outubro como intocado.

Aprovação da entrega de engenharia significa que o procedimento foi implementado, executado, revisado e limitado corretamente, inclusive quando a hipótese de ganho não se confirmou. Não significa aprovação operacional, ganho estatisticamente demonstrado ou certificação de autonomia pessoal. Os registros históricos aceitos permanecem preservados.
