# From SEC 10-K Filings to Volatility Signals

[Main README](README.md) | [中文](README.zh-CN.md)

## Positioning

This repository is an auditable, leakage-safe agentic pipeline for financial
text factor research. Its primary research question is:

> **Can 10-K textual information forecast future realized volatility?**

The current evidence supports out-of-sample volatility forecasting, not a
formal claim of tradable stock-return alpha.

## Headline Evidence

| Target | Best model | ALL_SPLITS Rank IC | Rank IC NW t-stat |
| --- | --- | ---: | ---: |
| `CAR_1_20` | industry mean | 0.1698 | 3.539 |
| `CAR_1_5` | industry mean | 0.1834 | 4.524 |
| `realized_volatility_1_20` | **XGBoost** | **0.3899** | **21.32** |

The preregistered primary prediction rule also passes:
`realized_volatility_1_20 / Ridge`, Rank IC `0.3335`, p about `6.85e-11`.

The preregistered primary portfolio rule does not pass after costs, sector
neutrality, ALL_SPLITS aggregation, and multiple-testing control:
Sharpe `-0.3602`, p `0.4598`.

## Pipeline

```text
SEC 10-K filings
  -> event-time manifest and parser
  -> leakage-controlled labels and rolling splits
  -> dictionary tone, TF-IDF/SVD, metadata features
  -> historical mean, industry mean, Ridge, XGBoost
  -> OOS IC metrics and portfolio diagnostics
  -> multiple-testing report, audit report, empirical report
```

## Distinctive Features

- Auditable `available_time_utc` and market-calendar event alignment.
- Train-window-only TF-IDF fitting.
- Cost-aware, sector-neutral, and value-weight portfolio variants.
- Preregistered primary specifications and multiple-testing adjustment.
- Explicit boundaries for public, licensed, and delisting-return data.

## Validation

```bash
python -m pip install -e ".[dev]"
python -m text_factor_lab run --config configs/text_factor_lab/e2e_smoke.yaml --execute
python -m pytest -q
python -m ruff check src scripts tests
```

## Research Boundaries

The public 90-company experiment is exploratory/applied-grade. Formal
replication still requires a licensed survivorship-free universe, historical
entity links, delisting returns, and stricter market-data controls.

See [working paper positioning](docs/working_paper_positioning.md) and
[compact result summaries](docs/results/README.md). The
[system architecture and roadmap](docs/system_architecture_and_roadmap.md)
documents the algorithm flow, agent responsibilities, and prompt-governed LLM
extension strategy.

## License

Released under the [MIT License](LICENSE). This repository is for research and
education only. It is not investment, trading, legal, accounting, or tax
advice.
