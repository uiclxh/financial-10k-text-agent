# Result Artifacts

This directory contains compact, GitHub-friendly summaries from the public
90-company SEC 10-K large-universe experiment. It intentionally excludes raw
filings, price panels, feature matrices, prediction JSONL, portfolio return
series, and other large generated artifacts.

## Included

- `large_universe_90_company_final_summary.md`
- `large_universe_90_company_final_summary.json`
- `large_universe_feature_ablation_summary.md`
- `large_universe_feature_ablation_summary.json`
- `crsp_wrds_formal_summary_template.md`
- `factor_card_crsp_wrds_template.md`

## Headline

The strongest out-of-sample evidence is for predicting future realized
volatility from 10-K text:

| Target | Best model | ALL_SPLITS Rank IC | Rank IC NW t-stat |
| --- | --- | ---: | ---: |
| `CAR_1_20` | industry mean | 0.1698 | 3.539 |
| `CAR_1_5` | industry mean | 0.1834 | 4.524 |
| `realized_volatility_1_20` | **XGBoost** | **0.3899** | **21.32** |

The preregistered primary prediction rule passes, while the preregistered
primary portfolio rule does not pass after transaction costs, sector
neutrality, ALL_SPLITS aggregation, and multiple-testing control.

These summaries are research diagnostics, not investment advice.

## Formal CRSP/WRDS Profile

`crsp_wrds_formal_summary_template.md` and
`factor_card_crsp_wrds_template.md` define the compact public outputs expected
from a licensed local CRSP/WRDS rerun. Raw CRSP, WRDS, CCM, Compustat, vendor,
or other licensed files must remain under ignored private paths such as
`data_private/`.
