# CRSP/WRDS Formal Replication Summary Template

This template is for a licensed local rerun of the 10-K text factor pipeline.
Do not commit raw CRSP, WRDS, CCM, Compustat, or vendor files. Commit only compact
aggregate summaries that are allowed by the applicable data license.

## Run Identity

- Run ID: `real_10k_large_universe_crsp_wrds_formal_template`
- Config: `configs/text_factor_lab/real_10k_large_universe_crsp_wrds.yaml`
- Run type: `formal_run`
- Data stack: SEC EDGAR + CRSP/WRDS + CRSP delisting returns + CCM links
- Raw licensed data committed: `false`

## Required Formal Gates

| Gate | Required Status | Observed Status |
| --- | --- | --- |
| Licensed data manifest | pass | TBD |
| Universe quality report | pass | TBD |
| Coverage diagnosis | pass or disclosed warn | TBD |
| Feature no-lookahead audit | pass | TBD |
| Split leakage audit | pass | TBD |
| Delisting application report | pass | TBD |
| Multiple-testing disclosure | pass | TBD |

## Sample

| Field | Value |
| --- | --- |
| Documents | TBD |
| Firms | TBD |
| Sample window | 2016-01-01 to 2025-12-31 |
| Universe | Survivorship-free large-cap CRSP/WRDS universe |
| Delisted firms retained | TBD |
| Primary target | `realized_volatility_1_20` |

## Prediction Results

| Target | Best Model | Rank IC | NW t-stat | RMSE | N |
| --- | --- | ---: | ---: | ---: | ---: |
| `realized_volatility_1_20` | TBD | TBD | TBD | TBD | TBD |
| `CAR_1_5` | TBD | TBD | TBD | TBD | TBD |
| `CAR_1_20` | TBD | TBD | TBD | TBD | TBD |

## Portfolio Results

| Target | Model | Variant | Sharpe | NW t-stat | Adjusted p-value | Net annual return |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `realized_volatility_1_20` | TBD | monthly sector-neutral | TBD | TBD | TBD | TBD |

## Delisting Handling

- Positions affected by delisting: TBD
- Delisting returns applied: TBD
- Missing delisting returns: TBD
- Audit conclusion: TBD

## Multiple Testing

- Tested specifications: TBD
- Primary discoveries after adjustment: TBD
- Robustness discoveries after adjustment: TBD
- Conclusion after adjustment: TBD

## Conclusion Policy

- If audit fails: diagnostic only.
- If audit passes but adjusted portfolio evidence fails: prediction evidence only.
- If audit, prediction, portfolio, robustness, and multiple-testing gates pass:
  formal research-grade text factor evidence.
