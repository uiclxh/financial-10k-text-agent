# FMP / Alpha Public-Data Stack

This profile replaces the prior WRDS / Nasdaq Data Link dependency with an
applied-grade, non-WRDS data stack:

```text
SEC EDGAR official filings
  + FMP primary adjusted daily prices and market data
  + Yahoo Finance chart fallback for predeclared missing prices
  + Alpha Vantage backup listing-status checks
  + Loughran-McDonald dictionary
  + local NYSE/Nasdaq trading calendar
```

## Positioning

The committed public result is a **10-company applied-grade pilot panel**. The
configured expansion path now includes a **30-company S&P 500 sector seed** and
a more balanced **50-company S&P 500 sector seed**. None of these profiles is a
survivorship-free CRSP/WRDS replication.

The market data layer is explicitly **mixed-source applied-grade** when Yahoo
fallback is used. FMP remains the primary price provider; Yahoo is allowed only
for the predeclared fallback tickers `MCD` and `LLY` when FMP price access is
unavailable. The audit report must mark this boundary with
`mixed_market_data_source_boundary`.

Allowed claim:

```text
This experiment tests whether SEC 10-K text contains out-of-sample information
about future realized volatility in a fixed 10-company U.S. 10-K panel.
```

Blocked claim:

```text
This experiment proves a survivorship-free tradable equity factor or captures
CRSP-style delisting returns.
```

## Current 10-Company Universe

Sony is excluded because it is a foreign private issuer and normally files
`20-F`, not `10-K`. JPMorgan Chase is used instead.

| Role | Ticker | Company | CIK | Form |
| --- | --- | --- | ---: | --- |
| Target | MSFT | Microsoft | `0000789019` | 10-K |
| Target | NFLX | Netflix | `0001065280` | 10-K |
| Target | NKE | Nike | `0000320187` | 10-K |
| Target | MCD | McDonald's | `0000063908` | 10-K |
| Target | META | Meta Platforms | `0001326801` | 10-K |
| Target | SBUX | Starbucks | `0000829224` | 10-K |
| Target | JPM | JPMorgan Chase | `0000019617` | 10-K |
| Target | V | Visa | `0001403161` | 10-K |
| Target | XOM | ExxonMobil | `0000034088` | 10-K |
| Target | LLY | Eli Lilly | `0000059478` | 10-K |
| Benchmark | SPY | SPDR S&P 500 ETF | ETF | price benchmark |

## Expansion Panels

The first expansion keeps the current 10 companies and adds 20 S&P 500-style
large-cap U.S. `10-K` filers by sector. The second expansion keeps those 30 and
adds 20 more names to improve coverage in Energy, Industrials, Utilities,
Materials, Real Estate, and payment/financial infrastructure.

This is not random sampling and is not presented as official historical S&P 500
membership.

Config files:

- `configs/universe/30_company_sp500_sector_seed_2016_2025.csv`
- `configs/text_factor_lab/30_company_public_fmp_alpha.yaml`
- `configs/universe/50_company_sp500_sector_seed_2016_2025.csv`
- `configs/text_factor_lab/50_company_public_fmp_alpha.yaml`

30-company additions:

| Sector bucket | Added tickers |
| --- | --- |
| Information Technology | ORCL, ADBE, CRM, CSCO, IBM |
| Financials | BAC, GS, MS, WFC, AXP |
| Health Care | PFE, MRK, ABBV, JNJ, ABT |
| Consumer / media | COST, KO, PEP, HD, CMCSA |

50-company additions:

| Sector bucket | Added tickers |
| --- | --- |
| Energy | CVX, COP, EOG, OXY |
| Industrials | UNP, CAT, HON, GE, UPS |
| Utilities | NEE, DUK, SO, AEP |
| Materials | APD, SHW, FCX, NEM |
| Real Estate | PLD, AMT |
| Payment / financial infrastructure | MA |

The resulting 50-company panel should produce about 500 annual filings for
FY2016-FY2025 if SEC coverage is complete. Comcast replaces Disney after an API
coverage audit found Disney's current CIK seed missing 2016-2018 10-K coverage.

GE is retained under continuous CIK/ticker linkage, but flagged for manual
review due to major corporate restructuring during the sample period. The
research interpretation should not silently treat 2016 GE text and 2025 GE
Aerospace text as economically identical without this caveat.

Financials, utilities, and some large issuers can expose multiple SEC tickers
for preferred shares or affiliated securities. This does not affect price labels
because the extraction script uses only the configured canonical common equity
ticker for market data, labels, and portfolio returns.

## Required Inputs

```text
data_private/
  sec/
    raw_filings/
    document_manifest.jsonl
    parsed_sections.jsonl
    filing_coverage_report.json
  market/
    prices_with_returns.csv
    spy_benchmark.csv
    daily_marketcap.csv
    corporate_actions.csv
    price_quality_report.json
  metadata/
    tickers.csv
    security_master.csv
    universe_membership.csv
    entity_link_history.csv
    listing_status.csv
    license_manifest.json
    license_manifest.yaml
    data_provenance.json
  dictionaries/
    lm_dictionary.csv
    lm_dictionary_license_note.txt
```

## Extraction

```powershell
$env:FMP_API_KEY="your-fmp-key"
$env:ALPHAVANTAGE_API_KEY="your-alpha-vantage-key"
$env:SEC_USER_AGENT="financial-10k-text-agent contact: your-email@example.com"

python scripts\extract_fmp_alpha_10_company_panel.py `
  --start-date 2015-12-01 `
  --end-date 2026-04-30 `
  --filing-start-year 2016 `
  --filing-end-year 2025 `
  --yahoo-fallback-tickers MCD LLY `
  --lm-dictionary-file "E:\path\to\Loughran-McDonald_MasterDictionary_1993-2025.csv"
```

30-company expansion:

```powershell
python scripts\extract_fmp_alpha_10_company_panel.py `
  --panel 30_company_sp500_sector_seed `
  --start-date 2015-12-01 `
  --end-date 2026-04-30 `
  --filing-start-year 2016 `
  --filing-end-year 2025 `
  --yahoo-fallback-tickers MCD LLY `
  --lm-dictionary-file "E:\path\to\Loughran-McDonald_MasterDictionary_1993-2025.csv"
```

50-company expansion:

```powershell
python scripts\extract_fmp_alpha_10_company_panel.py `
  --panel 50_company_sp500_sector_seed `
  --start-date 2015-12-01 `
  --end-date 2026-04-30 `
  --filing-start-year 2016 `
  --filing-end-year 2025 `
  --yahoo-fallback-tickers MCD LLY `
  --lm-dictionary-file "E:\path\to\Loughran-McDonald_MasterDictionary_1993-2025.csv"
```

Dry run:

```powershell
python scripts\extract_fmp_alpha_10_company_panel.py --dry-run
python scripts\extract_fmp_alpha_10_company_panel.py --panel 30_company_sp500_sector_seed --dry-run
python scripts\extract_fmp_alpha_10_company_panel.py --panel 50_company_sp500_sector_seed --dry-run
```

Pipeline run:

```powershell
python -m text_factor_lab run `
  --config configs/text_factor_lab/10_company_public_fmp_alpha.yaml `
  --execute

python -m text_factor_lab run `
  --config configs/text_factor_lab/30_company_public_fmp_alpha.yaml `
  --execute

python -m text_factor_lab run `
  --config configs/text_factor_lab/50_company_public_fmp_alpha.yaml `
  --execute
```

## Hard Coverage Rules

```text
Filing coverage:
  each target company should have FY2016-FY2025 annual form_type = 10-K

Price coverage:
  date range = 2015-12-01 to 2026-04-30
  expected calendar = SPY trading dates
  all target tickers should have closeadj and returns on observed SPY dates

Text coverage:
  each filing should parse at least two core sections
  Risk Factors or MD&A should have word_count > 0

Label coverage:
  each filing should generate realized_volatility_1_20, CAR_1_5, and CAR_1_20
  label_start_time must be after prediction_time

Audit interpretation:
  coverage >= 0.90    -> main applied result
  0.70 <= coverage < 0.90 -> applied result with limitations
  coverage < 0.70     -> exploratory only
```

## Primary Target

The main analysis should emphasize:

```text
realized_volatility_1_20
```

CAR and portfolio results should be reported as secondary/exploratory unless
they pass transaction-cost, sector-neutral, ALL_SPLITS, and multiple-testing
checks.

## Source Boundaries

- SEC EDGAR provides official filings and filing timestamps.
- FMP provides primary adjusted daily prices, historical market cap, profiles,
  symbol changes, and delisted-company checks.
- Yahoo Finance chart data is a narrow fallback for predeclared prices only;
  runs using it must be described as mixed-source applied-grade runs.
- Price labels use the configured common equity ticker only. SEC submissions
  metadata can include preferred-share tickers such as bank preferreds; those
  SEC tickers must not be used for stock-return labels.
- Alpha Vantage is a backup source for listing status and optional price
  cross-checks.
- Loughran-McDonald is the primary finance dictionary source.
- This stack does not provide CRSP `DLRET` and does not make the fixed
  10-company panel survivorship-free.
