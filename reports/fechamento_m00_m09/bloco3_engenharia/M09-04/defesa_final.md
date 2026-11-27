# Avaliação final segregada — setembro2026

671 origens comuns; contexto24, histórico até origem−2h, alvo+24h, índiceChronos25. Snapshot obtido somente após congelar código, modelos, escaladores, calibradores e política. Estudo retrospectivo, sem comprovação da versão publicada na origem.

          method   n       mae      rmse  bias_observed_minus_predicted
     persistence 671 35.616479 50.351806                      -0.118539
     chronos_p50 671 35.689509 47.649804                       3.594809
          mlp_17 671 35.798434 46.331283                      13.530202
          mlp_29 671 36.071127 46.324847                      16.434027
          mlp_41 671 36.078965 46.057445                      16.998245
          gru_41 671 36.550595 45.015515                      20.323878
   linear_legacy 671 36.773465 46.863352                      19.237325
          gru_17 671 37.262908 46.370827                      23.423832
          gru_29 671 38.939038 47.425211                      25.320816
        lightgbm 671 39.935226 48.006647                      23.808183
      hgb_bloco2 671 40.160344 48.084892                      27.001884
        catboost 671 40.853216 48.483520                      26.829121
hgb_quantile_p50 671 42.338754 51.419292                      29.446851
      hgb_legacy 671 42.971842 52.854430                      25.951265

Critérios predefinidos do candidato HGBbloco2:
{
  "fixed_champion": "hgb_bloco2",
  "mean_gain_at_least2": false,
  "gain_ci_above_zero": false,
  "cqr_coverage_within70_90": true,
  "cqr_width_at_most100": false,
  "policy_cost_better_than_never": true,
  "daily_alarm_limits_respected": true,
  "maximum_daily_alarms": 6,
  "operational_data_contract_proven": false,
  "promotion_authorized": false,
  "no_reselection_on_final": true
}

Todas as sementes neurais foram mantidas; os ajustes antigos não foram repetidos. O treino neural original e o ajuste B2 usam cortes diferentes, declarados nos protocolos. As probabilidades de classe são somente do classificador B2, não inferidas de quantis/points. Métricas/custos são pareados, sob as mesmas origens; custos são relativos hipotéticos. A seleção não foi refeita com setembro. Índices de latência e memória de processos distintos não representam benchmark estritamente equivalente. Sem CI/shadow/produção aprovados nem certificação de autonomia pessoal.
