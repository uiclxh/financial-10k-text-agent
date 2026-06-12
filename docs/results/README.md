# Public Result Artifacts

This directory contains compact, GitHub-friendly research outputs. It excludes
raw filings, API responses, full price panels, large feature matrices, and
private or licensed intermediate data.

## Latest Result Package

[10_company_public_fmp_alpha_2016_2025_v1](10_company_public_fmp_alpha_2016_2025_v1/README.md)

This is the current public applied-grade pilot:

- 10 U.S. companies.
- FY2016-FY2025 SEC 10-K filings.
- 100 filings, 300 labels, 896 model predictions.
- Loughran-McDonald dictionary plus train-window-only TF-IDF/SVD features.
- 472 tested specifications with multiple-testing disclosure.
- 0 audit failures and 2 audit warnings.

Main conclusion: the pipeline is validated and audit-clean enough for an
applied research demo, but the public pilot remains exploratory and does not
establish formal trading alpha.

## Historical / Extension Summaries

- `large_universe_90_company_final_summary.md`
- `large_universe_90_company_final_summary.json`
- `large_universe_feature_ablation_summary.md`
- `large_universe_feature_ablation_summary.json`

These are compact summaries from an earlier large-universe experiment. They are
kept as historical diagnostics, not as the current primary public package.

## Formal Licensed-Data Templates

- `crsp_wrds_formal_summary_template.md`
- `factor_card_crsp_wrds_template.md`

These define the expected compact outputs for a future licensed CRSP/WRDS rerun.
Raw CRSP, WRDS, CCM, Compustat, vendor, or other licensed files must remain
under ignored private paths such as `data_private/`.
