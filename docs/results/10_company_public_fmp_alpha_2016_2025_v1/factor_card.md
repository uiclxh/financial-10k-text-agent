# Factor Card - 10_company_public_fmp_alpha_2016_2025_v1

| Field | Value |
| --- | --- |
| Conclusion | `exploratory_report` |
| Formal result allowed | `False` |
| Audit status | `warn` |
| Coverage | `0.487` |
| Eligible OOS coverage | `1` |
| Primary spec coverage | `1` |
| Primary prediction coverage | `1` |
| Primary portfolio coverage | `1` |
| Signal direction policy | `pre_registered_score_convention_no_post_hoc_sign_flip` |
| Primary prediction sign | `negative` |
| Universe | `fixed_10_company_us_10k_fmp_alpha_pilot` |
| Sample | `2016-01-01..2025-12-31` |
| Targets | `realized_volatility_1_20`, `CAR_1_5`, `CAR_1_20` |
| Features | `dictionary_tone`, `tfidf` |
| Models | `historical_mean`, `industry_mean`, `ridge`, `xgboost` |
| Multiple-testing families | `20` |
| Git commit SHA | `48e48ef6a2c1f18cc8c3aab3678491eb97c9d9f2` |
| Package version | `0.15.0` |
| Dirty worktree flag | `True` |
| Portfolio return sources | `daily_price_panel`, `monthly_common_rebalance_price_panel` |
| Position accounting | `drifted_daily_positions`, `monthly_rebalance_drifted_daily_positions` |

## Best Prediction

- Model: `xgboost::CAR_1_5::ALL_SPLITS`.
- Target: `CAR_1_5`.
- Split: `ALL_SPLITS`.
- Rank IC: `0.321212`.
- Rank IC Newey-West t-stat: `4.1481`.
- Aggregation: `split_mean_ic_weighted_error_metrics`.
- RMSE: `0.0347187`.
- Directional accuracy: `0.475`.

## Best Backtest

- Model: `historical_mean::CAR_1_20::train_2016_2023__val_2024_2024__test_2025_2025`.
- Target: `CAR_1_20`.
- Net long-short return: `0.0928824`.
- Sharpe ratio: `12.1803`.
- Newey-West t-stat: `2.25068`.
- Signal direction: `long_high_score`.
- Turnover: `2`.

## Evidence Level

exploratory_prediction_evidence_not_formal_trading_alpha

## Primary Sign Convention

The preregistered volatility prediction specification contains ranking information, but the Rank IC sign is negative under the current score convention. This must not be post-hoc inverted or described as a positive volatility forecast.

## Diagnostics

- Vocabulary manifest rows: `20`.
- Section length flags: `{'manual_check_lt_100_words': 34, 'ok': 366}`.
- Section-level feature exclusions: `34`.
- Prediction ranking policy: Portfolio construction uses factor_score ordering to form ranks and quantiles; raw prediction magnitude is not used for equal-weight ranking except in explicitly risk-scaled variants.
- Portfolio interpretation: diagnostic only; current evidence does not establish formal trading alpha.

## Usage Boundary

Report as exploratory prediction evidence and disclose tested specifications, data-source boundaries, and portfolio limitations.
