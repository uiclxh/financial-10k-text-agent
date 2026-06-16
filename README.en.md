# Financial 10-K Text Agent

Auditable SEC 10-K text-factor research pipeline for out-of-sample forecasting,
portfolio diagnostics, leakage checks, and empirical-finance reporting.

Latest public package:
[docs/results/10_company_public_fmp_alpha_2016_2025_v1](docs/results/10_company_public_fmp_alpha_2016_2025_v1/README.md)

Current release: **v0.16.0 - 10-Company FMP/Alpha Applied Pilot**.

Key facts:

- 10-company U.S. 10-K pilot, FY2016-FY2025.
- 100 SEC filings, 300 labels, 896 OOS predictions.
- 100% eligible OOS prediction coverage.
- 0 audit failures, 2 audit warnings.
- Loughran-McDonald tone plus train-window-only TF-IDF/SVD.
- 472 tested specifications with multiple-testing disclosure.
- 30-company and 50-company S&P 500 sector-seed expansion configs are prepared.

Interpretation: this is an applied-grade, leakage-aware research package. It
shows exploratory forecasting evidence and a complete audit/report workflow,
but it does not establish formal tradable alpha.

Run the smoke workflow:

```bash
python -m pip install -e ".[dev]"
python -m text_factor_lab run --config configs/text_factor_lab/e2e_smoke.yaml --execute
python -m pytest -q
```

See the root [README.md](README.md) for the full overview.
