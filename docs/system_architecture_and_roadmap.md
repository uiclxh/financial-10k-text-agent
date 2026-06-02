# System Architecture And Roadmap

This document describes the implemented research pipeline and the planned
prompt-governed extension. The current evidence supports out-of-sample
volatility forecasting from SEC 10-K text. It does not establish formal
tradable alpha.

## System Architecture

```mermaid
flowchart TD
    A["Research Config<br/>run type, universe, labels, splits, models, audit gates"]
    B["Data Providers<br/>SEC EDGAR, public prices, Nasdaq Sharadar, CRSP/WRDS profile"]
    C["Universe Layer<br/>security master, membership intervals, historical entity links"]
    D["Market Calendar<br/>open, close, holiday, early close, event-date policy"]
    E["SEC 10-K Manifest<br/>CIK, accession, available_time_utc, license note, hash"]
    F["10-K Parser<br/>Item 1, Item 1A, Item 3, Item 7, full text"]
    G["Label Builder<br/>CAR, realized volatility, simple/log return, delisting-aware policy"]
    H["Rolling OOS Splitter<br/>train, validation, embargo, test"]
    I["Feature Layer<br/>dictionary tone, TF-IDF/SVD, metadata, section/full-text variants"]
    J["Model Layer<br/>historical mean, industry mean, Ridge, XGBoost"]
    K["OOS Evaluation<br/>RMSE, MAE, R-squared, IC, Rank IC, NW t-stat"]
    L["Portfolio Layer<br/>direction rule, target-aware policy, sector neutral, value weight"]
    M["Portfolio Time Series<br/>daily returns, monthly ALL_SPLITS aggregate, costs, turnover"]
    N["Inference Layer<br/>tested specifications, multiple testing, preregistered rules"]
    O["Audit Gate<br/>coverage, leakage, metadata, portfolio, licensed-data boundaries"]
    P["Report Layer<br/>empirical report, factor card, audit report, compact summary"]

    A --> B
    A --> C
    B --> E
    C --> E
    D --> E
    E --> F
    B --> G
    D --> G
    F --> H
    G --> H
    H --> I
    I --> J
    J --> K
    K --> L
    L --> M
    K --> N
    M --> N
    N --> O
    O -->|"pass"| P
    O -->|"fail"| Q["Diagnostic-only report<br/>formal conclusion blocked"]
```

### Plain-Text View

```text
experiment config
  -> provider and universe validation
  -> SEC metadata + market-calendar event alignment
  -> 10-K section parsing
  -> delisting-aware labels
  -> rolling train / validation / embargo / test splits
  -> train-window-only dictionary tone + TF-IDF/SVD + metadata features
  -> historical_mean / industry_mean / Ridge / XGBoost
  -> OOS prediction metrics
  -> target-aware portfolio time series
  -> costs + sector neutrality + ALL_SPLITS monthly aggregation
  -> preregistered specification registry + multiple-testing control
  -> audit gate
  -> empirical report or diagnostic-only report
```

## Algorithm Logic

### 1. Event-Time Alignment

```text
SEC acceptance_time_utc
  -> exchange trading calendar
  -> pre-open filing      -> same trading day
  -> intraday filing      -> same trading day
  -> after-close filing   -> next trading day
  -> weekend / holiday    -> next trading day
  -> resolved event_date
```

The calendar must use the actual market close, including early-close days. The
resolved date determines the start of the forward label window.

### 2. Leakage-Safe Feature Construction

```text
train documents only
  -> fit TF-IDF vocabulary
  -> fit optional SVD projection
  -> freeze feature transform
  -> transform validation documents
  -> transform test documents
```

Dictionary features and metadata features use the same timestamp rule:

```text
feature_available_time_utc <= prediction_time_utc
```

Any violation is an audit failure.

### 3. Model Comparison

```text
Level 0: historical_mean
  -> unconditional baseline

Level 1: industry_mean
  -> industry baseline with global fallback

Level 2: Ridge
  -> stable linear text-factor baseline
  -> alpha selected on validation only

Level 3: XGBoost
  -> nonlinear interaction model
  -> hyperparameters selected on validation only
```

The test window is used once for out-of-sample evaluation. Test metrics cannot
select features, prompts, hyperparameters, signal direction, or portfolio
variants.

### 4. Target-Aware Portfolio Construction

```text
predictions
  -> preregistered signal direction
       -> long_high_score
       -> long_low_score
       -> validation_selected
  -> target-aware policy
       -> return target: score-ranked long/short
       -> volatility target: long_low_vol or risk_scaled
  -> sector-neutral / value-weight variants
  -> daily holdings and turnover
  -> gross return - transaction cost
  -> monthly ALL_SPLITS OOS return series
```

The primary portfolio p-value is based on the `ALL_SPLITS` out-of-sample return
series, not on a single favorable split.

### 5. Statistical Inference

```text
all tested specifications
  -> specification registry
  -> raw p-values
  -> multiple-testing adjustment
  -> Newey-West inference for overlapping return horizons
  -> preregistered primary rule evaluation
  -> supported / exploratory / blocked conclusion
```

## Prompt-Governed Extension

The production research path is deterministic by default. LLM prompts should
enter only as auditable feature-extraction or report-assistance modules. They
must never receive forward labels, test returns, or undisclosed test metrics.

```mermaid
flowchart LR
    A["10-K section chunks<br/>available at prediction time only"]
    B["Versioned extraction prompt<br/>task, glossary, examples, JSON schema"]
    C["LLM structured output<br/>risk topics, uncertainty, liquidity, legal pressure"]
    D["Schema validator<br/>type checks, evidence spans, confidence bounds"]
    E["Prompt QA gate<br/>coverage, consistency, hallucination checks"]
    F["Frozen prompt-derived features<br/>prompt_version + model_version + input_hash"]
    G["Same rolling OOS model pipeline"]
    H["Audit report<br/>prompt manifest + failures + fallbacks"]

    A --> B --> C --> D --> E
    E -->|"pass"| F --> G --> H
    E -->|"fail"| I["Retry once with repair prompt<br/>then deterministic fallback"]
    I --> D
```

### Prompt Roles

| Prompt role | Input | Output | Hard rule |
| --- | --- | --- | --- |
| Section extraction | One 10-K section chunk | Structured risk-topic JSON | Preserve evidence span and source hash |
| Tone classification | Evidence-bounded sentence set | Tone, uncertainty, intensity | No external company knowledge |
| QA critic | Source chunk plus proposed JSON | Validated or rejected JSON | Reject unsupported claims |
| Report assistant | Audited artifacts only | Draft interpretation | Must separate supported, exploratory, and blocked claims |

### Prompt Optimization Strategy

```text
prompt template v1
  -> define narrow financial task
  -> require JSON schema
  -> require source evidence spans
  -> add representative train-only examples
  -> run parser reliability checks
  -> compare validation-only feature utility
  -> inspect failure taxonomy
  -> revise prompt
  -> freeze prompt_version before test evaluation
  -> register prompt hash and model version
```

Optimization rules:

1. Use train and validation documents only while revising prompts.
2. Keep temperature at `0` for extraction runs unless the experiment explicitly
   preregisters a different setting.
3. Store `prompt_version`, `prompt_sha256`, `model_version`, `chunk_policy`,
   `created_at_utc`, and input hashes in a prompt manifest.
4. Require structured JSON outputs and validate them before feature generation.
5. Record retries, rejected outputs, missing evidence spans, and deterministic
   fallback usage.
6. Freeze prompt and model versions before the test window is scored.
7. Treat every prompt variant as a tested specification for multiple-testing
   disclosure.
8. Allow the Report Agent to summarize audited artifacts only; it cannot
   upgrade an exploratory result into a formal conclusion.

## Agent Responsibilities

```text
Controller Agent
  -> reads config
  -> checks prerequisites
  -> executes stages
  -> persists run status
  -> blocks formal reporting after failed audit

Data Agent
  -> builds manifests
  -> records provider, license, timestamp, and hashes

Parsing Agent
  -> extracts SEC sections
  -> stores section spans and parser failures

Feature Agent
  -> fits train-only transforms
  -> emits feature and prompt manifests

Label Agent
  -> aligns prices, benchmarks, calendars, and delisting policy

Model Agent
  -> tunes on validation only
  -> emits OOS predictions and tuning logs

Portfolio And Inference Agent
  -> constructs OOS portfolios
  -> applies costs, neutrality, aggregation, and multiple testing

Audit Agent
  -> verifies coverage, leakage, metadata, and research-grade boundaries

Report Agent
  -> produces evidence-bounded summaries from audited artifacts
```

## Roadmap

```mermaid
flowchart LR
    A["v0.1-v0.4<br/>foundation<br/>schemas, CLI, orchestration, parsing, labels"]
    B["v0.5-v0.8<br/>research controls<br/>calendar, portfolio series, inference, universe"]
    C["v0.9-v0.15<br/>robustness<br/>coverage, daily accounting, target-aware portfolios"]
    D["Current evidence<br/>90-company public run<br/>volatility forecasting signal"]
    E["Next: licensed replication<br/>CRSP/WRDS or qualified vendor panel"]
    F["Next: prompt-governed text extension<br/>versioned JSON extraction + QA"]
    G["Next: broader robustness<br/>subperiods, industries, costs, capacity"]
    H["Research-grade package<br/>audited evidence, bounded claims, reproducible reports"]

    A --> B --> C --> D
    D --> E
    D --> F
    E --> G
    F --> G
    G --> H
```

| Stage | Status | Deliverable | Gate |
| --- | --- | --- | --- |
| Pipeline foundation | Complete | Config-driven SEC-to-report workflow | Smoke tests and schema checks |
| Leakage and inference controls | Complete | Calendar alignment, train-only fitting, registry, multiple testing | Audit pass |
| Public 90-company experiment | Complete | Compact volatility evidence summary | Exploratory/applied-grade only |
| Licensed replication | Next | Survivorship-free universe, entity links, delisting-aware prices | Licensed-data manifest pass |
| Prompt-governed extraction | Next | Versioned prompt manifest, structured LLM factors, QA fallback | Prompt audit and validation-only freeze |
| Broader empirical robustness | Next | Subperiod, industry, cost, capacity, and ablation tables | Preregistered robustness report |

## Claim Boundary

```text
current supported claim
  -> 10-K textual information contains out-of-sample information about future
     realized volatility

current unsupported claim
  -> the project has established formal cost-adjusted tradable alpha

next evidence threshold
  -> licensed survivorship-free replication
  -> portfolio robustness after costs and neutrality
  -> multiple-testing-adjusted significance
  -> frozen prompt/model versions for any LLM-derived feature
```
