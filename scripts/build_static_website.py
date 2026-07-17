# ruff: noqa: E501
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
ASSETS = WEBSITE / "assets"
REPO = "https://github.com/uiclxh/financial-10k-text-agent"
SITE = "https://www.filingfactor.tech"
RUN_ID = "50_company_public_fmp_alpha_2016_2025_v4"
RESULT_DIR = f"{REPO}/tree/main/docs/results/{RUN_ID}"
RESULT_BLOB = f"{REPO}/blob/main/docs/results/{RUN_ID}"
PAPER_URL = "https://ssrn.com/abstract=6974978"
CONFIG_URL = f"{REPO}/blob/main/configs/text_factor_lab/50_company_public_fmp_alpha_v4.yaml"
SPEC_REGISTRY_URL = f"{RESULT_BLOB}/specification_registry.json"
SOURCE_URL = f"{REPO}/tree/main/src/text_factor_lab"
TESTS_URL = f"{REPO}/tree/main/tests"


def page_path(page: str, zh: bool) -> str:
    if page == "home":
        return "index.zh-CN.html" if zh else "index.html"
    return f"{page}.zh-CN.html" if zh else f"{page}.html"


def head(filename: str, title: str, description: str, zh: bool) -> str:
    if filename.startswith("index"):
        canonical = SITE if not zh else f"{SITE}/index.zh-CN.html"
        en_href = f"{SITE}/index.html"
        zh_href = f"{SITE}/index.zh-CN.html"
    elif filename.startswith("results"):
        canonical = f"{SITE}/{filename}"
        en_href = f"{SITE}/results.html"
        zh_href = f"{SITE}/results.zh-CN.html"
    else:
        canonical = f"{SITE}/{filename}"
        en_href = f"{SITE}/methods.html"
        zh_href = f"{SITE}/methods.zh-CN.html"
    return f"""  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta name="author" content="Xihang Lin">
    <link rel="canonical" href="{canonical}">
    <link rel="alternate" hreflang="en" href="{en_href}">
    <link rel="alternate" hreflang="zh-CN" href="{zh_href}">
    <link rel="alternate" hreflang="x-default" href="{SITE}/">
    <meta property="og:type" content="website">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{SITE}/assets/og-card.png">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{SITE}/assets/og-card.png">
    <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
    <link rel="stylesheet" href="assets/styles.css">
    <script defer src="assets/site.js"></script>
    <script type="application/ld+json">
      {{"@context":"https://schema.org","@type":"SoftwareSourceCode","name":"Financial 10-K Text Agent","author":{{"@type":"Person","name":"Xihang Lin"}},"codeRepository":"{REPO}","license":"{REPO}/blob/main/LICENSE","programmingLanguage":"Python"}}
    </script>
  </head>"""


def header(active: str, zh: bool) -> str:
    home = page_path("home", zh)
    results = page_path("results", zh)
    methods = page_path("methods", zh)
    run = f"{results}#reproducibility"
    labels = {
        "skip": "????" if zh else "Skip to content",
        "nav": "???" if zh else "Primary navigation",
        "switch": "????" if zh else "Language switch",
        "overview": "??" if zh else "Overview",
        "results": "??" if zh else "Results",
        "methods": "?????" if zh else "Methods & Audit",
        "run": "????" if zh else "Run Locally",
    }
    def current(name: str) -> str:
        return ' aria-current="page"' if active == name else ""
    en_link = page_path(active, False) if active != "overview" else "index.html"
    zh_link = page_path(active, True) if active != "overview" else "index.zh-CN.html"
    return f"""  <body>
    <a class="skip-link" href="#main">{labels["skip"]}</a>
    <header class="site-header">
      <div class="container header-inner">
        <a class="brand" href="{home}">Financial 10-K Text Agent</a>
        <nav class="primary-nav" aria-label="{labels["nav"]}">
          <a href="{home}"{current("overview")}>{labels["overview"]}</a>
          <a href="{results}"{current("results")}>{labels["results"]}</a>
          <a href="{methods}"{current("methods")}>{labels["methods"]}</a>
          <a href="{run}">{labels["run"]}</a>
          <a href="{REPO}">GitHub ?</a>
        </nav>
        <div class="language-switch" aria-label="{labels["switch"]}">
          <a class="switch-option{' is-active' if not zh else ''}" href="{en_link}" lang="en">English</a>
          <a class="switch-option{' is-active' if zh else ''}" href="{zh_link}" lang="zh-CN">Chinese</a>
        </div>
      </div>
    </header>"""


def footer(zh: bool) -> str:
    return f"""    <footer class="site-footer">
      <div class="container footer-inner">
        <p>{"? Xihang Lin ?? ? ???? ? ????????????" if zh else "Built by Xihang Lin ? Financial Mathematics ? Public result summaries are for research demonstration only."}</p>
        <nav class="footer-links" aria-label="{"????" if zh else "Footer navigation"}">
          <a href="{page_path("home", zh)}">{"??" if zh else "Home"}</a>
          <a href="{page_path("results", zh)}">{"??" if zh else "Results"}</a>
          <a href="{page_path("methods", zh)}">{"??" if zh else "Methods"}</a>
          <a href="https://github.com/uiclxh">{"GitHub ??" if zh else "GitHub profile"}</a>
          <a href="{REPO}/blob/main/LICENSE">MIT License</a>
        </nav>
      </div>
    </footer>
  </body>
</html>
"""


def shell(filename: str, active: str, title: str, description: str, body: str, zh: bool) -> str:
    return f"""<!doctype html>
<html lang="{"zh-CN" if zh else "en"}">
{head(filename, title, description, zh)}
{header(active, zh)}

    <main id="main">
{body}
    </main>

{footer(zh)}"""


def metric_cards(items: list[tuple[str, str]]) -> str:
    return "\n".join(
        f'            <div class="metric-card"><div class="metric-number">{value}</div><div class="metric-label">{label}</div></div>'
        for value, label in items
    )


def home(zh: bool) -> str:
    if zh:
        return f"""      <section class="hero retention-hero">
        <div class="container">
          <div class="hero-grid">
            <div class="hero-copy">
              <span class="badge">????? NLP ? v4 ??</span>
              <h1>Financial 10-K Text Agent</h1>
              <p class="hero-hook">10-K ???????????????????? alpha?</p>
              <p class="hero-subtitle">???????? NLP ???????? SEC 10-K ????????? 20 ?????????????</p>
              <div class="hero-cta" aria-label="??????">
                <a class="btn btn-primary" href="results.zh-CN.html">????</a>
                <a class="btn btn-secondary" href="methods.zh-CN.html">????</a>
                <a class="btn btn-secondary" href="{REPO}">?? GitHub</a>
              </div>
            </div>
            <aside class="claim-boundary-card" aria-label="????">
              <p class="eyebrow">30 ???</p>
              <h2>?????????????</h2>
              <p>v4 ????? 500 ? SEC 10-K ???????? 20 ??????????????????????????????</p>
              <strong>??????????? RAG ???</strong>
            </aside>
          </div>
          <div class="hero-kpi-grid" aria-label="v4 ????">
            <div class="proof-card"><strong>500</strong><span>SEC 10-K ??</span></div>
            <div class="proof-card"><strong>8,133</strong><span>?????</span></div>
            <div class="proof-card"><strong>0.2395</strong><span>?????? Rank IC</span></div>
            <div class="proof-card"><strong>0 / 2</strong><span>???? / ??</span></div>
          </div>
          <p class="metric-note">????? Rank IC?<code>0.3668</code>?????????????</p>
        </div>
      </section>

      <section class="section">
        <div class="container">
          <div class="section-header"><p class="eyebrow">????</p><h2>50 ????????? v4</h2><p><code>{RUN_ID}</code></p></div>
          <div class="metric-grid compact">
{metric_cards([("1,500", "??"), ("520k+", "????"), ("594", "????"), ("100%", "??????")])}
          </div>
        </div>
      </section>

      <section class="section muted">
        <div class="container">
          <div class="section-header"><p class="eyebrow">????</p><h2>???????</h2><p>????????????????? Ridge ???????</p></div>
{rank_chart(True)}
        </div>
      </section>

      <section class="section" id="contribution">
        <div class="container">
          <div class="section-header"><p class="eyebrow">????</p><h2>?????????</h2><p>?? SEC ???????????????????????</p></div>
          <div class="capability-card-grid contribution-cards">
            <article class="capability-card"><strong>????</strong><p>???? / ?? / ???????????????? embargo ??????</p><div class="evidence-links"><a class="evidence-link" href="{CONFIG_URL}">???? ?</a><a class="evidence-link" href="{SPEC_REGISTRY_URL}">????? ?</a></div></article>
            <article class="capability-card"><strong>?? NLP ???</strong><p>?? section ???Loughran-McDonald ????????? TF-IDF/SVD ??????</p><div class="evidence-links"><a class="evidence-link" href="{SOURCE_URL}">???? ?</a></div></article>
            <article class="capability-card"><strong>?????</strong><p>Rank IC?????????????cluster bootstrap????????????</p><div class="evidence-links"><a class="evidence-link" href="{RESULT_DIR}">v4 ??? ?</a><a class="evidence-link" href="{TESTS_URL}">?? ?</a></div></article>
          </div>
          <p class="tech-stack">Python ? scikit-learn ? XGBoost ? SEC EDGAR ? pytest ? Ruff ? GitHub Actions</p>
        </div>
      </section>

      <section class="section muted">
        <div class="container">
          <div class="section-header"><p class="eyebrow">?????</p><h2>????????????</h2></div>
          <div class="capability-card-grid">
            <div class="capability-card"><strong>????</strong><p>?????????????????????</p></div>
            <div class="capability-card"><strong>???????</strong><p>????????????????</p></div>
            <div class="capability-card"><strong>?????</strong><p>?? split ? TF-IDF/SVD ???????????</p></div>
            <div class="capability-card"><strong>????</strong><p>????????????????????</p></div>
            <div class="capability-card"><strong>????</strong><p>?? parser ???bootstrap ??????????????</p></div>
          </div>
        </div>
      </section>
{pipeline(True)}
{evidence_links(True)}
{boundary(True)}"""
    return f"""      <section class="hero retention-hero">
        <div class="container">
          <div class="hero-grid">
            <div class="hero-copy">
              <span class="badge">Applied financial NLP ? v4 evidence</span>
              <h1>Financial 10-K Text Agent</h1>
              <p class="hero-hook">10-K text ranks future volatility ? but does not prove tradable alpha.</p>
              <p class="hero-subtitle">An auditable financial NLP pipeline for testing whether SEC 10-K disclosures contain out-of-sample information about future 20-day realized volatility.</p>
              <div class="hero-cta" aria-label="Primary project actions">
                <a class="btn btn-primary" href="results.html">View Results</a>
                <a class="btn btn-secondary" href="methods.html">Read Methods</a>
                <a class="btn btn-secondary" href="{REPO}">Open GitHub</a>
              </div>
            </div>
            <aside class="claim-boundary-card" aria-label="Main takeaway">
              <p class="eyebrow">30-second summary</p>
              <h2>Prediction evidence, not a trading claim</h2>
              <p>The v4 package tests whether 500 SEC 10-K filings contain ranking information about future 20-day realized volatility. The primary prediction is positive; the preregistered portfolio test is not.</p>
              <strong>Not a trading bot. Not a RAG demo.</strong>
            </aside>
          </div>
          <div class="hero-kpi-grid" aria-label="v4 core metrics">
            <div class="proof-card"><strong>500</strong><span>SEC 10-K filings</span></div>
            <div class="proof-card"><strong>8,133</strong><span>OOS predictions</span></div>
            <div class="proof-card"><strong>0.2395</strong><span>Preregistered primary Rank IC</span></div>
            <div class="proof-card"><strong>0 / 2</strong><span>Audit failures / warnings</span></div>
          </div>
          <p class="metric-note">Best exploratory Rank IC: <code>0.3668</code>, reported separately from the preregistered primary result.</p>
        </div>
      </section>

      <section class="section">
        <div class="container">
          <div class="section-header"><p class="eyebrow">Current release</p><h2>50-Company Applied-Grade Package v4</h2><p><code>{RUN_ID}</code></p></div>
          <div class="metric-grid compact">
{metric_cards([("1,500", "Labels"), ("520k+", "Feature records"), ("594", "Tested specifications"), ("100%", "Primary prediction coverage")])}
          </div>
        </div>
      </section>

      <section class="section muted">
        <div class="container">
          <div class="section-header"><p class="eyebrow">Result snapshot</p><h2>Volatility Ranking Evidence</h2><p>The strongest observed result is exploratory; the preregistered Ridge result remains positive.</p></div>
{rank_chart(False)}
        </div>
      </section>

      <section class="section" id="contribution">
        <div class="container">
          <div class="section-header"><p class="eyebrow">My contribution</p><h2>What I Designed and Built</h2><p>I developed the workflow from SEC filing ingestion to audited out-of-sample evidence.</p></div>
          <div class="capability-card-grid contribution-cards">
            <article class="capability-card"><strong>Research design</strong><p>Rolling train/validation/test splits, forward labels, preregistered specifications, and embargo-based leakage controls.</p><div class="evidence-links"><a class="evidence-link" href="{CONFIG_URL}">Inspect config ?</a><a class="evidence-link" href="{SPEC_REGISTRY_URL}">Specification registry ?</a></div></article>
            <article class="capability-card"><strong>Financial NLP pipeline</strong><p>Section parsing, Loughran-McDonald tone features, train-window-only TF-IDF/SVD, and model manifests.</p><div class="evidence-links"><a class="evidence-link" href="{SOURCE_URL}">Inspect implementation ?</a></div></article>
            <article class="capability-card"><strong>Evaluation and audit</strong><p>Rank IC, feature ablation, industry-neutral diagnostics, clustered bootstrap, coverage checks, and automated reports.</p><div class="evidence-links"><a class="evidence-link" href="{RESULT_DIR}">v4 result package ?</a><a class="evidence-link" href="{TESTS_URL}">Test suite ?</a></div></article>
          </div>
          <p class="tech-stack">Python ? scikit-learn ? XGBoost ? SEC EDGAR ? pytest ? Ruff ? GitHub Actions</p>
        </div>
      </section>

      <section class="section muted">
        <div class="container">
          <div class="section-header"><p class="eyebrow">Why it matters</p><h2>Beyond Sentiment Scores and Document Search</h2></div>
          <div class="capability-card-grid">
            <div class="capability-card"><strong>Forward labels</strong><p>Links filing text to future volatility and abnormal-return targets.</p></div>
            <div class="capability-card"><strong>Rolling OOS design</strong><p>Separates training, validation, and test windows through time.</p></div>
            <div class="capability-card"><strong>Train-only features</strong><p>Fits TF-IDF/SVD vocabularies only inside each training window.</p></div>
            <div class="capability-card"><strong>Evidence hierarchy</strong><p>Separates preregistered claims from exploratory model comparisons.</p></div>
            <div class="capability-card"><strong>Research audit</strong><p>Discloses parser issues, bootstrap uncertainty, coverage, and multiple testing.</p></div>
          </div>
        </div>
      </section>
{pipeline(False)}
{evidence_links(False)}
{boundary(False)}"""


def rank_chart(zh: bool) -> str:
    labels = {
        "explore": "?????" if zh else "Exploratory best",
        "diag": "????" if zh else "Incremental diagnostic",
        "base": "????" if zh else "Economic baseline",
        "primary": "??????" if zh else "Preregistered primary",
        "pp": "???" if zh else "Primary prediction",
        "portfolio": "???" if zh else "Primary portfolio",
        "alpha": "??????? alpha?" if zh else "Tradable alpha is not established.",
    }
    return f"""          <div class="home-result-layout">
            <div class="model-chart-card" aria-label="Rank IC comparison chart">
              <div class="rank-chart-row is-exploratory"><div><strong>{"? TF-IDF/SVD" if zh else "TF-IDF/SVD only"}</strong><span>{labels["explore"]}</span></div><span class="rank-track"><span style="--bar-width: 100%"></span></span><code>0.3668</code></div>
              <div class="rank-chart-row"><div><strong>{"?? + ??" if zh else "Industry + text"}</strong><span>{labels["diag"]}</span></div><span class="rank-track"><span style="--bar-width: 90%"></span></span><code>0.3296</code></div>
              <div class="rank-chart-row"><div><strong>{"????" if zh else "Industry mean"}</strong><span>{labels["base"]}</span></div><span class="rank-track"><span style="--bar-width: 80%"></span></span><code>0.2924</code></div>
              <div class="rank-chart-row is-primary"><div><strong>{"???? Ridge" if zh else "Combined text Ridge"}</strong><span>{labels["primary"]}</span></div><span class="rank-track"><span style="--bar-width: 65%"></span></span><code>0.2395</code></div>
            </div>
            <div class="claim-pair">
              <article class="claim-card claim-positive"><span>{labels["pp"]}</span><strong>Rank IC 0.2395</strong><p>{"?? p ?" if zh else "Raw p-value"} <code>0.00067</code>. {"?????????????" if zh else "Positive exploratory volatility-ranking evidence."}</p></article>
              <article class="claim-card claim-negative"><span>{labels["portfolio"]}</span><strong>Sharpe -0.8539</strong><p>{"?? p ?" if zh else "Raw p-value"} <code>0.1147</code>. {labels["alpha"]}</p></article>
            </div>
          </div>"""


def pipeline(zh: bool) -> str:
    nodes = [
        ("SEC ??", "acceptance ???") if zh else ("SEC Filings", "acceptance timestamps"),
        ("Parser ??", "section ????") if zh else ("Parser Review", "section quality flags"),
        ("??", "????") if zh else ("Labels", "future targets"),
        ("????", "embargo + OOS") if zh else ("Rolling Splits", "embargo + OOS"),
        ("????", "?????") if zh else ("Text Features", "train-window only"),
        ("??", "?? + bootstrap") if zh else ("Diagnostics", "ablation + bootstrap"),
        ("??", "?????") if zh else ("Audit", "claims + boundaries"),
    ]
    parts = []
    for i, (a, b) in enumerate(nodes):
        parts.append(f'<div class="pipeline-node"><strong>{a}</strong><span>{b}</span></div>')
        if i != len(nodes) - 1:
            parts.append('<div class="pipeline-arrow" aria-hidden="true">?</div>')
    return f"""      <section class="section">
        <div class="container">
          <div class="section-header"><p class="eyebrow">{"??" if zh else "Pipeline"}</p><h2>{"? SEC ????????" if zh else "From SEC Filing to Audited Evidence"}</h2></div>
          <div class="pipeline-flow" aria-label="{"????" if zh else "Research pipeline"}">
            {"".join(parts)}
          </div>
        </div>
      </section>"""


def evidence_links(zh: bool) -> str:
    links = [
        ("?? Working Paper", "SSRN ??????", PAPER_URL) if zh else ("Read Working Paper", "stable SSRN publication page", PAPER_URL),
        ("v4 ???", "??????", RESULT_DIR) if zh else ("v4 Result Package", "all public artifacts", RESULT_DIR),
        ("????", "??????", f"{RESULT_BLOB}/factor_card.md") if zh else ("Factor Card", "fastest result summary", f"{RESULT_BLOB}/factor_card.md"),
        ("????", "???????", f"{RESULT_BLOB}/feature_ablation_summary.json") if zh else ("Feature Ablation", "text versus industry", f"{RESULT_BLOB}/feature_ablation_summary.json"),
        ("Bootstrap ??", "??????", f"{RESULT_BLOB}/primary_rank_ic_bootstrap_report.json") if zh else ("Bootstrap Report", "clustered confidence intervals", f"{RESULT_BLOB}/primary_rank_ic_bootstrap_report.json"),
        ("Parser ??", "??????", f"{RESULT_BLOB}/parser_manual_review_appendix.md") if zh else ("Parser Review", "manual quality appendix", f"{RESULT_BLOB}/parser_manual_review_appendix.md"),
    ]
    cards = "".join(f'<a class="artifact-card" aria-label="{a} - {b}" href="{href}"><span>{a}</span><span>{b}</span></a>' for a, b, href in links)
    return f"""      <section class="section muted">
        <div class="container split-section">
          <div><p class="eyebrow">{"????" if zh else "Inspect the evidence"}</p><h2>{"?????????" if zh else "Follow the Public Audit Trail"}</h2><p>{"??????????????????????????" if zh else "Compact, license-safe artifacts connect every headline number to a reproducible evidence file."}</p></div>
          <div class="artifact-list">{cards}</div>
        </div>
      </section>"""


def boundary(zh: bool) -> str:
    text = "????????????? CRSP/WRDS ????????????????????????????????????????" if zh else "This is an applied-grade exploratory run, not CRSP/WRDS-equivalent formal asset-pricing evidence, a survivorship-free replication, a production trading system, proven tradable alpha, or investment advice."
    return f"""      <section class="section"><div class="container"><div class="boundary-box"><h2>{"????" if zh else "Usage Boundary"}</h2><p>{text}</p></div></div></section>"""


def results(zh: bool) -> str:
    toc = [("primary-result", "???" if zh else "Primary result"), ("ablation", "????" if zh else "Feature ablation"), ("bootstrap", "Bootstrap"), ("coverage", "???" if zh else "Coverage"), ("reproducibility", "??" if zh else "Reproduce")]
    toc_html = "".join(f'<a href="#{anchor}">{label}</a>' for anchor, label in toc)
    metric_items = [("500", "SEC 10-K ??" if zh else "SEC 10-K filings"), ("1,500", "??" if zh else "Labels"), ("8,133", "?????" if zh else "OOS predictions"), ("520,465", "????" if zh else "Feature records"), ("594", "????" if zh else "Tested specifications"), ("26", "???" if zh else "Testing families"), ("100%", "????????" if zh else "Eligible OOS coverage"), ("0 / 2", "???? / ??" if zh else "Audit failures / warnings")]
    return f"""      <section class="page-hero">
        <div class="container narrow">
          <span class="badge">{"50 ??? v4 ?????" if zh else "50-company v4 public package"}</span>
          <h1>{"?????" if zh else "Results and Artifacts"}</h1>
          <p class="hero-hook">{"?????????????????? alpha?" if zh else "The strongest evidence is volatility ranking, not stock-return alpha."}</p>
          <p class="hero-subtitle">{"???????" if zh else "Compact public summary of"} <code>{RUN_ID}</code>.</p>
          <nav class="page-toc" aria-label="{"????" if zh else "On this page"}">{toc_html}</nav>
        </div>
      </section>

      <section class="section muted" id="primary-result">
        <div class="container">
          <div class="result-summary-card"><div><p class="eyebrow">{"??????" if zh else "Preregistered primary prediction"}</p><h2>Ridge Rank IC = 0.2395</h2><p>{"??? 20 ??????????????????? p ?" if zh else "Positive out-of-sample ranking information for future 20-day realized volatility; raw p-value"} <code>0.00067</code>.</p></div><div class="result-claim-box"><span>{"????" if zh else "Claim boundary"}</span><strong>{"???????????????? alpha?" if zh else "Exploratory volatility-prediction evidence, not tradable alpha."}</strong></div></div>
          <div class="claim-pair result-claim-pair"><article class="claim-card claim-positive"><span>{"???" if zh else "Primary prediction"}</span><strong>Rank IC 0.2395</strong><p>{"???????????????????" if zh else "Positive and fully covered across the preregistered prediction specification."}</p></article><article class="claim-card claim-negative"><span>{"???" if zh else "Primary portfolio"}</span><strong>Sharpe -0.8539</strong><p>{"?? p ?" if zh else "Raw p-value"} <code>0.1147</code>; {"????????? alpha?" if zh else "formal tradable alpha is not established."}</p></article></div>
        </div>
      </section>

      <section class="section"><div class="container"><div class="section-header"><p class="eyebrow">{"????" if zh else "Run summary"}</p><h2>{"???????" if zh else "Applied-Grade Public Evidence"}</h2></div><div class="metric-grid">{metric_cards(metric_items)}</div></div></section>

      <section class="section muted"><div class="container split-section equal-cards"><article class="finding-card"><p class="eyebrow">{"??????" if zh else "Preregistered primary"}</p><h2>{"???? Ridge" if zh else "Combined-Text Ridge"}</h2><p><code>realized_volatility_1_20</code>, {"? ALL_SPLITS Rank IC ???" if zh else "evaluated by ALL_SPLITS Rank IC."}</p><div class="result-grid"><div><span class="result-label">Rank IC</span><strong class="result-number">0.2395</strong></div><div><span class="result-label">{"?? p ?" if zh else "Raw p-value"}</span><strong class="result-number">0.00067</strong></div></div><p>{"???????????????" if zh else "Supports positive exploratory volatility-ranking evidence."}</p></article><article class="exploratory-card"><p class="eyebrow">{"?????????" if zh else "Best observed exploratory result"}</p><h2>{"? TF-IDF/SVD ? Ridge" if zh else "TF-IDF/SVD-Only Ridge"}</h2><p>{"?????????????????????" if zh else "The strongest observed model-comparison result, not the preregistered primary claim."}</p><div class="result-grid"><div><span class="result-label">Rank IC</span><strong class="result-number">0.3668</strong></div><div><span class="result-label">NW t-stat</span><strong class="result-number">5.4055</strong></div></div><p>RMSE <code>0.00992</code>.</p></article></div></section>
{ablation(zh)}
{bootstrap(zh)}
{coverage_and_artifacts(zh)}
{reproducibility(zh)}"""


def ablation(zh: bool) -> str:
    rows = [
        ("? TF-IDF/SVD" if zh else "TF-IDF/SVD only", "Ridge", "0.3668", "0.3416", "0.00992", "100%", "93%"),
        ("?? + ??" if zh else "Industry + text", "Ridge", "0.3296", "0.3251", "0.01076", "90%", "89%"),
        ("???" if zh else "Industry only", "Industry mean", "0.2924", "0.0000", "0.00913", "80%", "0%"),
        ("???" if zh else "Dictionary only", "Ridge", "0.2244", "0.2465", "0.00984", "61%", "67%"),
        ("????" if zh else "Combined text", "Ridge", "0.2395", "0.2023", "0.01932", "65%", "55%"),
    ]
    chart = "".join(f'<div class="ablation-row"><strong>{name}</strong><div class="paired-bars"><span class="bar-raw" style="--bar-width: {raw_w}"></span><span class="bar-neutral" style="--bar-width: {neu_w}"></span></div><code>{raw} / {neu}</code></div>' for name, _, raw, neu, _, raw_w, neu_w in rows)
    table = "".join(f'<tr><td>{name}</td><td>{est}</td><td class="numeric">{raw}</td><td class="numeric">{neu}</td><td class="numeric">{rmse}</td></tr>' for name, est, raw, neu, rmse, *_ in rows)
    return f"""      <section class="section" id="ablation"><div class="container"><div class="section-header"><p class="eyebrow">{"????" if zh else "Feature ablation"}</p><h2>{"??????? Rank IC" if zh else "Raw vs Industry-Neutral Rank IC"}</h2><p>{"? split ??????????????????????" if zh else "Text representations retain positive ranking diagnostics after within-split industry demeaning."}</p></div><div class="ablation-chart" aria-label="Feature ablation Rank IC chart"><div class="chart-legend"><span class="legend-raw">{"?? Rank IC" if zh else "Raw Rank IC"}</span><span class="legend-neutral">{"???? Rank IC" if zh else "Industry-neutral Rank IC"}</span></div>{chart}</div><div class="table-wrap chart-fallback"><table><thead><tr><th>{"???" if zh else "Feature set"}</th><th>{"???" if zh else "Estimator"}</th><th>Rank IC</th><th>{"???? Rank IC" if zh else "Industry-neutral Rank IC"}</th><th>RMSE</th></tr></thead><tbody>{table}</tbody></table></div></div></section>"""


def bootstrap(zh: bool) -> str:
    rows = [
        ("?? Rank IC" if zh else "Raw Rank IC", "Split bootstrap", "0.2395", "[-0.0050, 0.4841]", "0.111"),
        ("?? Rank IC" if zh else "Raw Rank IC", "Event-date bootstrap" if not zh else "??? bootstrap", "0.2395", "[0.0719, 0.3743]", "0.005"),
        ("?? Rank IC" if zh else "Raw Rank IC", "Ticker-cluster bootstrap" if not zh else "Ticker ?? bootstrap", "0.2395", "[0.1091, 0.3522]", "0.001"),
        ("???? Rank IC" if zh else "Industry-neutral Rank IC", "Split bootstrap", "0.2023", "[-0.1157, 0.5202]", "0.117"),
        ("???? Rank IC" if zh else "Industry-neutral Rank IC", "Event-date bootstrap" if not zh else "??? bootstrap", "0.2023", "[-0.1546, 0.4273]", "0.366"),
        ("???? Rank IC" if zh else "Industry-neutral Rank IC", "Ticker-cluster bootstrap" if not zh else "Ticker ?? bootstrap", "0.2023", "[-0.1787, 0.4181]", "0.357"),
    ]
    trs = "".join(f'<tr><td>{a}</td><td>{b}</td><td class="numeric">{c}</td><td>{d}</td><td class="numeric">{e}</td></tr>' for a, b, c, d, e in rows)
    return f"""      <section class="section muted" id="bootstrap"><div class="container"><div class="section-header"><p class="eyebrow">Bootstrap inference</p><h2>{"? Rank IC ????" if zh else "Primary Rank IC Confidence Intervals"}</h2><p>{"?? 2,000 ????????????????? split ??split bootstrap ??????" if zh else "Two thousand deterministic resamples. Split bootstrap is inconclusive because there are only four OOS split clusters."}</p></div><div class="table-wrap"><table><thead><tr><th>{"???" if zh else "Estimand"}</th><th>{"??" if zh else "Method"}</th><th>{"???" if zh else "Point"}</th><th>95% CI</th><th>p-value</th></tr></thead><tbody>{trs}</tbody></table></div></div></section>"""


def coverage_and_artifacts(zh: bool) -> str:
    cards = [
        ("????", "??????", f"{RESULT_BLOB}/factor_card.md") if zh else ("Factor Card", "fastest result summary", f"{RESULT_BLOB}/factor_card.md"),
        ("????", "??????", f"{RESULT_BLOB}/empirical_report.md") if zh else ("Empirical Report", "full narrative report", f"{RESULT_BLOB}/empirical_report.md"),
        ("????", "???????", f"{RESULT_BLOB}/feature_ablation_summary.json") if zh else ("Feature Ablation", "text versus industry", f"{RESULT_BLOB}/feature_ablation_summary.json"),
        ("????", "??????", f"{RESULT_BLOB}/audit_report.json") if zh else ("Audit Report", "coverage and warnings", f"{RESULT_BLOB}/audit_report.json"),
        ("????", "???", f"{RESULT_BLOB}/multiple_testing_report.json") if zh else ("Multiple Testing", "specification families", f"{RESULT_BLOB}/multiple_testing_report.json"),
        ("Parser ??", "section ????", f"{RESULT_BLOB}/parser_manual_review_appendix.md") if zh else ("Parser Review", "section quality appendix", f"{RESULT_BLOB}/parser_manual_review_appendix.md"),
    ]
    links = "".join(f'<a class="artifact-card" aria-label="{a} - {b}" href="{href}"><span>{a}</span><span>{b}</span></a>' for a, b, href in cards)
    coverage_text = "???????? 49.6%?????????? 100%??????????? 98.546%???? / ??????? 100%?" if zh else "Raw label coverage is 49.6%, eligible OOS coverage is 100%, model-expected prediction coverage is 98.546%, and primary prediction / portfolio coverage is 100%."
    boundary_text = "????????? FMP/Yahoo ????????????????? CRSP/WRDS ????????????" if zh else "This public-source experiment uses mixed FMP/Yahoo market data and applied-grade market-cap estimates. It is not a CRSP/WRDS-equivalent survivorship-free replication."
    return f"""      <section class="section" id="coverage"><div class="container split-section equal-cards"><div class="boundary-box"><h2>{"??????" if zh else "Coverage and Controls"}</h2><p>{coverage_text}</p></div><div class="boundary-box"><h2>{"????" if zh else "Data Boundary"}</h2><p>{boundary_text}</p></div></div></section><section class="section muted"><div class="container"><div class="section-header"><p class="eyebrow">{"???????" if zh else "Representative evidence files"}</p><h2>{"??????" if zh else "Inspect the Public Artifacts"}</h2></div><div class="artifact-grid">{links}</div></div></section>"""


def reproducibility(zh: bool) -> str:
    return f"""      <section class="section muted" id="reproducibility"><div class="container narrow"><div class="section-header"><p class="eyebrow">{"????" if zh else "Reproducibility"}</p><h2>{"?????????" if zh else "Run the Public Code Locally"}</h2></div><div class="code-card"><div class="code-toolbar"><span>Shell</span><button class="copy-button" type="button" data-copy-target="run-code">{"??" if zh else "Copy"}</button></div><pre id="run-code"><code>git clone https://github.com/uiclxh/financial-10k-text-agent.git
cd financial-10k-text-agent
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest</code></pre><p class="small-note">{"????????????????" if zh else "Raw licensed inputs are not included in the public repository."}</p></div></div></section>"""


def methods(zh: bool) -> str:
    flow = [
        ("Filing ???", "SEC acceptance time ?????????") if zh else ("Filing timestamp", "SEC acceptance time defines information availability."),
        ("Section ??", "?? Business?Risk Factors?Legal Proceedings ? MD&A?") if zh else ("Section parsing", "Business, Risk Factors, Legal Proceedings, and MD&A are extracted."),
        ("????", "???? CAR ???? filing ????????") if zh else ("Forward labels", "Volatility and CAR targets begin only after filing availability."),
        ("????", "??????????????????? embargo purge?") if zh else ("Rolling splits", "Train, validation, and test windows move through time with embargo purges."),
        ("??????", "TF-IDF/SVD ????????????") if zh else ("Train-window features", "TF-IDF/SVD vocabularies are fit inside training windows only."),
        ("??????", "????? validation Rank IC ???") if zh else ("Validation-only tuning", "Hyperparameters are selected using validation Rank IC only."),
        ("???????? Rank IC", "????????????????? Rank IC?") if zh else ("Tie-aware test Rank IC", "Test ranking uses average ranks; constant predictions return zero Rank IC."),
        ("????", "????????????????????") if zh else ("Evidence hierarchy", "Primary, robustness, and exploratory specifications remain separate."),
        ("????", "??????parser ?????????????") if zh else ("Audit boundary", "Coverage, parser quality, data limitations, and claim strength are disclosed."),
    ]
    steps = []
    for i, (title, desc) in enumerate(flow, 1):
        steps.append(f'<div class="leakage-step"><span>{i}</span><strong>{title}</strong><small>{desc}</small></div>')
        if i != len(flow):
            steps.append('<div class="leakage-arrow" aria-hidden="true">?</div>')
    controls = [
        ("??????", "Filing ???????????") if zh else ("Event-time alignment", "Filing timestamps define information availability."),
        ("???????", "?? / ?? / ??????????") if zh else ("Rolling OOS design", "Train / validation / test windows roll through time."),
        ("?????", "Embargo purge ? split-leakage logs?") if zh else ("Leakage control", "Embargo purge and split-leakage logs."),
        ("????", "??? validation Rank IC?") if zh else ("Model selection", "Validation-only Rank IC."),
        ("TF-IDF ??", "??????????") if zh else ("TF-IDF control", "Train-window-only vocabulary fitting."),
        ("??????", "???? Rank IC ??????") if zh else ("Incremental text diagnostic", "Industry-neutral Rank IC and feature ablation."),
        ("??????", "Newey-West ??? bootstrap ?????") if zh else ("Statistical uncertainty", "Newey-West and clustered bootstrap confidence intervals."),
        ("??????", "?????????????") if zh else ("Data snooping", "Specification registry and multiple-testing report."),
        ("Parser ??", "?????? section ?????????") if zh else ("Parser quality", "Manual review appendix for short or malformed sections."),
    ]
    control_rows = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in controls)
    return f"""      <section class="page-hero"><div class="container narrow"><span class="badge">{"?? / ?? ? v4" if zh else "Methods / Audit ? v4"}</span><h1>{"?????" if zh else "Methods and Audit"}</h1><p class="hero-hook">{"????????????????????????" if zh else "Every claim must be linked to a timestamped, testable artifact."}</p><p class="hero-subtitle">{"??????????????????????????????????????" if zh else "Filings, labels, splits, features, models, predictions, inference, portfolio diagnostics, and audit checks form one evidence chain."}</p><p><code>{RUN_ID}</code></p><nav class="page-toc" aria-label="{"????" if zh else "On this page"}"><a href="#research-flow">{"????" if zh else "Research flow"}</a><a href="#controls">{"???" if zh else "Controls"}</a><a href="#features">{"??" if zh else "Features"}</a><a href="#parser-review">Parser {"??" if zh else "review"}</a><a href="#claim-boundary">{"????" if zh else "Claim boundary"}</a><a href="#boundary">{"????" if zh else "Data boundary"}</a></nav></div></section>
      <section class="section" id="research-flow"><div class="container"><div class="section-header"><p class="eyebrow">{"???????" if zh else "Leakage-safe research design"}</p><h2>{"????????????" if zh else "Only Past Information Enters the Forecast"}</h2><p>{"?????????????????????????" if zh else "Every text feature and model decision must be available before the prediction timestamp."}</p></div><div class="leakage-flow-card" aria-label="Leakage-safe research flow">{"".join(steps)}</div></div></section>
      <section class="section muted" id="controls"><div class="container"><div class="section-header"><p class="eyebrow">{"?????" if zh else "Key controls"}</p><h2>{"??????" if zh else "Research Controls at a Glance"}</h2></div><div class="table-wrap"><table><thead><tr><th>{"???" if zh else "Control"}</th><th>{"????" if zh else "Implementation"}</th></tr></thead><tbody>{control_rows}</tbody></table></div></div></section>
      <section class="section" id="features"><div class="container split-section"><div><p class="eyebrow">{"????" if zh else "Feature construction"}</p><h2>{"??????" if zh else "Financial Text Representations"}</h2><p>{"Loughran-McDonald ????? TF-IDF/SVD ?????Business?Risk Factors?Legal Proceedings ? MD&A ???" if zh else "Loughran-McDonald dictionary tone and TF-IDF/SVD are built over full filing, Business, Risk Factors, Legal Proceedings, and MD&A scopes."}</p></div><div class="table-wrap"><table><thead><tr><th>{"???" if zh else "Feature set"}</th><th>{"??" if zh else "Meaning"}</th></tr></thead><tbody><tr><td><code>industry_only</code></td><td>{"???????????" if zh else "Training-window industry-mean baseline."}</td></tr><tr><td><code>dictionary_only</code></td><td>{"?????????" if zh else "Dictionary-tone text features."}</td></tr><tr><td><code>tfidf_svd_only</code></td><td>{"TF-IDF/SVD ?????" if zh else "TF-IDF/SVD text representations."}</td></tr><tr><td><code>combined_text</code></td><td>{"???????????" if zh else "Combined dictionary and text representation."}</td></tr><tr><td><code>industry_plus_text</code></td><td>{"??????????" if zh else "Industry features plus text features."}</td></tr></tbody></table></div></div></section>
      <section class="section muted"><div class="container"><div class="method-callout"><span>{"??????" if zh else "Industry-neutral diagnostic"}</span><strong>{"?? split-????????????????" if zh else "Does text retain information after removing split-industry means?"}</strong><p>{"???? Rank IC ??????????????" if zh else "Industry-neutral Rank IC is a descriptive diagnostic, not a causal decomposition."}</p></div></div></section>
      <section class="section"><div class="container"><div class="section-header"><p class="eyebrow">Bootstrap inference</p><h2>{"????????" if zh else "How Uncertainty Is Reported"}</h2></div><div class="policy-grid"><div><strong>Split bootstrap</strong><p>{"v4 ???? OOS split ??????????" if zh else "Inconclusive for v4 because there are only four OOS split clusters."}</p></div><div><strong>{"??? bootstrap" if zh else "Event-date bootstrap"}</strong><p>{"??????? Rank IC ???" if zh else "Supports a positive raw primary Rank IC interval."}</p></div><div><strong>{"Ticker ?? bootstrap" if zh else "Ticker-cluster bootstrap"}</strong><p>{"??????? Rank IC ???" if zh else "Supports a positive raw primary Rank IC interval."}</p></div><div><strong>{"???? bootstrap" if zh else "Industry-neutral bootstrap"}</strong><p>{"??????? bootstrap ??????" if zh else "Positive point estimate, but not bootstrap-robust."}</p></div></div></div></section>
      <section class="section muted" id="parser-review"><div class="container"><div class="section-header"><p class="eyebrow">{"Parser ????" if zh else "Parser quality review"}</p><h2>{"Section ??????????????" if zh else "Section Extraction Is Audited, Not Assumed"}</h2></div><div class="metric-grid compact">{metric_cards([("2,000", "?? section ??" if zh else "Parsed section records"), ("144", "??????" if zh else "Manual-review records"), ("144", "??? section ??" if zh else "Excluded section-level records"), ("494", "???????" if zh else "Short but included records")])}</div><p class="section-note">{"Item 1A ? Item 7 ?? 100 ??? section ???????100 ? 499 ???? section ???? warning?" if zh else "Item 1A and Item 7 below 100 words are excluded from section-level features. Core sections from 100 to 499 words remain included but carry a warning."}</p></div></section>
      <section class="section" id="claim-boundary"><div class="container"><div class="section-header"><p class="eyebrow">{"????" if zh else "Evidence boundary"}</p><h2>{"?????????????" if zh else "Prediction and Trading Evidence Are Judged Separately"}</h2></div><div class="result-pair"><article class="result-card primary"><p class="eyebrow">{"??????" if zh else "Preregistered primary prediction"}</p><h3>Ridge ? <code>realized_volatility_1_20</code></h3><div class="result-stat"><span>Rank IC</span><strong>0.2395</strong></div><p>{"?? p ?? 0.00067??????????????" if zh else "Raw p-value 0.00067; supports exploratory volatility-ranking evidence."}</p></article><article class="result-card diagnostic"><p class="eyebrow">{"??????" if zh else "Preregistered primary portfolio"}</p><h3>{"??????????" if zh else "Monthly sector-neutral equal-weight"}</h3><div class="result-stat"><span>Sharpe</span><strong>-0.8539</strong></div><p>{"?? p ?? 0.1147??????? alpha?" if zh else "Raw p-value 0.1147; does not establish tradable alpha."}</p></article></div></div></section>
      <section class="section" id="boundary"><div class="container"><div class="boundary-box"><h2>{"??????" if zh else "Formal Result Boundary"}</h2><p>{"??????????????????? pipeline ???FMP/Yahoo ??????????????? 50 ?????parser ?????????????-??????" if zh else "Formal empirical-finance claims are blocked by data-boundary issues, not pipeline failures: mixed FMP/Yahoo data, applied-grade market-cap estimates, fixed 50-company panel, parser-quality limitations, and a small number of missing diagnostic model-label pairs."}</p><p>{"??????????????????????????? NLP ????" if zh else "The project should be interpreted as an applied-grade, auditable financial NLP workflow for exploratory volatility ranking."}</p></div></div></section>"""


def write_pages() -> None:
    pages = {
        "index.html": shell("index.html", "overview", "Financial 10-K Text Agent", "An auditable SEC 10-K text pipeline for out-of-sample volatility-ranking research.", home(False), False),
        "index.zh-CN.html": shell("index.zh-CN.html", "overview", "Financial 10-K Text Agent", "?????? SEC 10-K ????????????????????????", home(True), True),
        "results.html": shell("results.html", "results", "Results | Financial 10-K Text Agent", "V4 results, feature ablation, bootstrap inference, and audit artifacts for the Financial 10-K Text Agent.", results(False), False),
        "results.zh-CN.html": shell("results.zh-CN.html", "results", "?? | Financial 10-K Text Agent", "Financial 10-K Text Agent ? v4 ????????bootstrap ????????", results(True), True),
        "methods.html": shell("methods.html", "methods", "Methods and Audit | Financial 10-K Text Agent", "Leakage controls, rolling OOS design, parser review, bootstrap inference, and audit boundaries for the v4 package.", methods(False), False),
        "methods.zh-CN.html": shell("methods.zh-CN.html", "methods", "????? | Financial 10-K Text Agent", "v4 ??????????????parser ???bootstrap ????????", methods(True), True),
    }
    WEBSITE.mkdir(parents=True, exist_ok=True)
    for filename, content in pages.items():
        (WEBSITE / filename).write_text(content, encoding="utf-8", newline="\n")


def write_assets() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "site.js").write_text(
        """document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-copy-target]");
  if (!button) return;

  const targetId = button.getAttribute("data-copy-target");
  const target = document.getElementById(targetId);
  if (!target) return;

  const originalLabel = button.textContent;
  const isChinese = originalLabel.includes("??");
  const text = target.textContent.trim();

  try {
    await navigator.clipboard.writeText(text);
    button.textContent = isChinese ? "???" : "Copied";
    button.classList.add("is-copied");
  } catch {
    button.textContent = isChinese ? "????" : "Copy failed";
  }

  window.setTimeout(() => {
    button.textContent = originalLabel;
    button.classList.remove("is-copied");
  }, 1800);
});
""",
        encoding="utf-8",
        newline="\n",
    )
    (ASSETS / "favicon.svg").write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#0f2a43"/><path d="M16 16h32v7H25v9h19v7H25v9h23v7H16z" fill="#e0f2fe"/><path d="M42 18l6 6-6 6" fill="none" stroke="#0e7490" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>
""",
        encoding="utf-8",
    )
    img = Image.new("RGB", (1200, 630), "#f8fafc")
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("arial.ttf", 58)
        big_font = ImageFont.truetype("arialbd.ttf", 46)
        body_font = ImageFont.truetype("arial.ttf", 30)
        small_font = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        title_font = big_font = body_font = small_font = None
    draw.rounded_rectangle((50, 50, 1150, 580), radius=34, fill="#ffffff", outline="#cbd5e1", width=2)
    draw.text((90, 95), "Financial 10-K Text Agent", fill="#0f172a", font=title_font)
    draw.text((90, 170), "Auditable SEC 10-K text pipeline for volatility-ranking research", fill="#475569", font=body_font)
    x = 90
    for value, label in [("500", "SEC filings"), ("8,133", "OOS predictions"), ("0.2395", "Primary Rank IC")]:
        draw.rounded_rectangle((x, 265, x + 300, 420), radius=22, fill="#f1f5f9", outline="#e2e8f0")
        draw.text((x + 28, 300), value, fill="#0f2a43", font=big_font)
        draw.text((x + 28, 360), label, fill="#475569", font=small_font)
        x += 335
    draw.rounded_rectangle((90, 470, 1110, 525), radius=18, fill="#fffbeb", outline="#fcd34d")
    draw.text((115, 484), "Prediction evidence, not a trading claim", fill="#92400e", font=body_font)
    img.save(ASSETS / "og-card.png")


if __name__ == "__main__":
    write_pages()
    write_assets()
