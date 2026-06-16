# Public Result Artifacts

This directory contains compact, GitHub-friendly research outputs. It excludes
raw filings, API responses, full price panels, feature matrices, and private or
licensed intermediate data.

## Latest Result Package

[50_company_public_fmp_alpha_2016_2025_v1](50_company_public_fmp_alpha_2016_2025_v1/README.md)

Current public applied-grade pilot:

- 50 U.S. large-cap companies.
- FY2016-FY2025 SEC 10-K filings.
- 500 filings, 1,500 labels, 4,716 OOS predictions.
- 520k+ feature records and 568 tested specifications.
- Preregistered primary prediction: Ridge on `realized_volatility_1_20`,
  Rank IC `0.2606`, raw p-value `0.00017`.
- 0 audit failures and 2 audit warnings.
- Portfolio outputs are diagnostic only; no formal tradable-alpha claim.

## Historical Result Packages

- [10_company_public_fmp_alpha_2016_2025_v1](10_company_public_fmp_alpha_2016_2025_v1/README.md)
- `large_universe_90_company_final_summary.md`
- `large_universe_90_company_final_summary.json`
- `large_universe_feature_ablation_summary.md`
- `large_universe_feature_ablation_summary.json`

These are retained as historical diagnostics, not as the current primary public
package.

## Formal Licensed-Data Templates

- `crsp_wrds_formal_summary_template.md`
- `factor_card_crsp_wrds_template.md`

These define expected compact outputs for a future licensed CRSP/WRDS rerun.
Raw CRSP, WRDS, CCM, Compustat, vendor, or other licensed files must remain
under ignored private paths such as `data_private/`.
