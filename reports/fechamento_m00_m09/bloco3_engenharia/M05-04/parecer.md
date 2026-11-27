# M05-04 — alternativas de boosting

Ajuste e seleção executados somente nas três semanas de junho; dois candidatos por família, orçamento fixado antes dos cálculos. Features/cortes/coortes iguais aos do bloco2. O ajuste final tem rótulos disponíveis antes de 01/07. Outubro já fora examinado: esta comparação é exploratória e não determina a seleção. Os números completos estão em candidatos.csv, folds.csv e metricas_outubro.csv.

  method   n       mae      rmse  bias_observed_minus_predicted  predict_seconds
lightgbm 695 18.058893 24.708468                      -0.147799         0.007608
catboost 695 18.421708 25.158648                      -0.799118         0.007319

Instalação privada de LightGBM4.6.0 e CatBoost1.2.8; Conda preservado. Somente previsão pontual, sem alegar quantis ou probabilidades desses dois ajustes. Sem promoção operacional ou certificação de autoria independente. A avaliação final de setembro pertence ao protocolo integrado e não altera estes ajustes.
