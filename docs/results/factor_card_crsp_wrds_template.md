# CRSP/WRDS Formal Factor Card Template

## Factor

- Factor name: TBD
- Text source: SEC 10-K
- Feature block: dictionary tone + TF-IDF/SVD + metadata controls
- Primary target: `realized_volatility_1_20`
- Primary model: `ridge`
- Portfolio policy: validation-selected signal direction with target-aware risk scaling

## Data Quality

| Item | Status |
| --- | --- |
| Licensed CRSP/WRDS manifest | TBD |
| Survivorship-free membership intervals | TBD |
| Historical CIK/PERMNO/GVKEY links | TBD |
| Delisting returns applied | TBD |
| Public fallback disabled | TBD |

## Prediction Evidence

| Metric | Value |
| --- | ---: |
| ALL_SPLITS Rank IC | TBD |
| Rank IC Newey-West t-stat | TBD |
| RMSE | TBD |
| Directional accuracy | TBD |

## Portfolio Evidence

| Metric | Value |
| --- | ---: |
| Net annual return | TBD |
| Annualized volatility | TBD |
| Sharpe | TBD |
| Newey-West t-stat | TBD |
| Max drawdown | TBD |
| Turnover | TBD |

## Robustness

| Check | Result |
| --- | --- |
| Equal-weight | TBD |
| Value-weight | TBD |
| Sector-neutral equal-weight | TBD |
| Sector-neutral value-weight | TBD |
| Multiple-testing adjustment | TBD |

## Interpretation

TBD. State whether the factor supports formal prediction evidence, formal
portfolio evidence, both, or diagnostic-only evidence.
