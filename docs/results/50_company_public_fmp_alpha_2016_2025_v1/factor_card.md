# Factor Card - 50_company_public_fmp_alpha_2016_2025_v1

| Field | Value |
| --- | --- |
| Conclusion | `exploratory_report` |
| Formal result allowed | `False` |
| Formal result blockers | `run_type is exploratory_run, so the run is intentionally not eligible for a formal empirical result.`, `market data uses a mixed FMP/Yahoo public-source stack, not a single CRSP/WRDS-equivalent research-grade source.`, `market_cap_at_selection is based on applied-grade estimates rather than licensed CRSP/Compustat/WRDS market-cap history.`, `the universe is an applied fixed-company panel, not a survivorship-free CRSP/WRDS research-grade universe.`, `audit_status is warn; warnings are boundary disclosures, not pipeline failures.` |
| Audit status | `warn` |
| Coverage | `0.496` |
| Eligible OOS coverage | `1` |
| Primary spec coverage | `1` |
| Primary prediction coverage | `1` |
| Primary portfolio coverage | `1` |
| Signal direction policy | `pre_registered_score_convention_no_post_hoc_sign_flip` |
| Primary prediction sign | `positive` |
| Universe | `fixed_50_company_sp500_sector_seed_fmp_alpha_pilot` |
| Sample | `2016-01-01..2025-12-31` |
| Targets | `realized_volatility_1_20`, `CAR_1_5`, `CAR_1_20` |
| Features | `dictionary_tone`, `tfidf` |
| Models | `historical_mean`, `industry_mean`, `ridge`, `xgboost` |
| Multiple-testing families | `20` |
| Git commit SHA | `753240be4524ea3eff153f60c22fd5338e8639eb` |
| Package version | `0.16.0` |
| Dirty worktree flag | `False` |
| Portfolio return sources | `daily_price_panel`, `monthly_common_rebalance_price_panel` |
| Position accounting | `drifted_daily_positions`, `monthly_rebalance_drifted_daily_positions` |

## Best Prediction

- Model: `xgboost::realized_volatility_1_20::ALL_SPLITS`.
- Target: `realized_volatility_1_20`.
- Split: `ALL_SPLITS`.
- Rank IC: `0.313338`.
- Rank IC Newey-West t-stat: `6.84785`.
- Aggregation: `split_mean_ic_weighted_error_metrics`.
- RMSE: `0.00833559`.
- Directional accuracy: `1`.

## Best Backtest

- Model: `ridge::CAR_1_20::train_2016_2023__val_2024_2024__test_2025_2025`.
- Target: `CAR_1_20`.
- Net long-short return: `0.049517`.
- Sharpe ratio: `5.04654`.
- Newey-West t-stat: `1.00483`.
- Signal direction: `long_high_score`.
- Turnover: `2`.

## Evidence Level

exploratory_prediction_evidence_not_formal_trading_alpha

## Primary Sign Convention

The preregistered prediction specification has a positive Rank IC under the current score convention.

## Diagnostics

- Vocabulary manifest rows: `20`.
- Section length flags: `{'manual_check_lt_100_words': 144, 'ok': 1840, 'warn_lt_500_words': 16}`.
- Section-level feature exclusions: `144`.
- Prediction ranking policy: Portfolio construction uses factor_score ordering to form ranks and quantiles; raw prediction magnitude is not used for equal-weight ranking except in explicitly risk-scaled variants.
- Portfolio interpretation: diagnostic only; current evidence does not establish formal trading alpha.

## Usage Boundary

Formal result is not allowed for data-boundary reasons, not because the pipeline failed:
- run_type is exploratory_run, so the run is intentionally not eligible for a formal empirical result.
- market data uses a mixed FMP/Yahoo public-source stack, not a single CRSP/WRDS-equivalent research-grade source.
- market_cap_at_selection is based on applied-grade estimates rather than licensed CRSP/Compustat/WRDS market-cap history.
- the universe is an applied fixed-company panel, not a survivorship-free CRSP/WRDS research-grade universe.
- audit_status is warn; warnings are boundary disclosures, not pipeline failures.

Report as exploratory prediction evidence and disclose tested specifications, data-source boundaries, and portfolio limitations.
