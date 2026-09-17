# Model governance report

- Champion: `persistence_1h`
- Challenger: `hist_gradient_boosting_calibrated_mean`
- Decision: **approved_for_shadow**
- Evidence: `development_backtest`
- Shadow ready: `True`
- Statistically superior: `False`
- Production ready: `False`

## Gates

| Gate | Passed |
|---|---:|
| mae_within_tolerance | yes |
| absolute_bias_within_limit | yes |
| rmse_improvement_sufficient | yes |
| ramp_mae_improvement_sufficient | yes |
| fold_win_rate_sufficient | yes |
| mae_gain_ci_above_zero | no |

## Metrics

| Metric | Value |
|---|---:|
| candidate_mae | 10.403154 |
| baseline_mae | 10.709036 |
| candidate_bias | 0.258303 |
| rmse_improvement_pct | 16.816862 |
| ramp_mae_improvement_pct | 40.179535 |
| fold_win_rate_pct | 60.000000 |
| mean_fold_mae_gain | 0.305882 |
| mae_gain_ci_low | -0.416077 |
| mae_gain_ci_high | 0.980022 |

> Production promotion is not authorized. A locked chronological holdout is required before production promotion.
