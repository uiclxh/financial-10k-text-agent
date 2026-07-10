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
        "skip": "跳到正文" if zh else "Skip to content",
        "nav": "主导航" if zh else "Primary navigation",
        "switch": "语言切换" if zh else "Language switch",
        "overview": "概览" if zh else "Overview",
        "results": "结果" if zh else "Results",
        "methods": "方法与审计" if zh else "Methods & Audit",
        "run": "本地运行" if zh else "Run Locally",
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
          <a href="{REPO}">GitHub ↗</a>
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
        <p>{"由 Xihang Lin 构建 · 金融数学 · 公开结果仅用于研究展示。" if zh else "Built by Xihang Lin · Financial Mathematics · Public result summaries are for research demonstration only."}</p>
        <nav class="footer-links" aria-label="{"页脚导航" if zh else "Footer navigation"}">
          <a href="{page_path("home", zh)}">{"主页" if zh else "Home"}</a>
          <a href="{page_path("results", zh)}">{"结果" if zh else "Results"}</a>
          <a href="{page_path("methods", zh)}">{"方法" if zh else "Methods"}</a>
          <a href="https://github.com/uiclxh">{"GitHub 主页" if zh else "GitHub profile"}</a>
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
              <span class="badge">应用型金融 NLP · v4 证据</span>
              <h1>Financial 10-K Text Agent</h1>
              <p class="hero-hook">10-K 文本能够排序未来波动率，但并不证明可交易 alpha。</p>
              <p class="hero-subtitle">一个可审计的 SEC 10-K 文本研究流水线，用于样本外波动率预测和实证研究审计。</p>
              <div class="hero-cta" aria-label="主要项目入口">
                <a class="btn btn-primary" href="results.zh-CN.html">查看结果</a>
                <a class="btn btn-secondary" href="methods.zh-CN.html">阅读方法</a>
                <a class="btn btn-secondary" href="{REPO}">打开 GitHub</a>
              </div>
            </div>
            <aside class="claim-boundary-card" aria-label="核心结论">
              <p class="eyebrow">30 秒摘要</p>
              <h2>有预测证据，但不是交易结论</h2>
              <p>v4 结果包检验 500 份 SEC 10-K 年报是否包含未来 20 日实现波动率排序信息。主预测结果为正；预注册组合检验不成立。</p>
              <strong>不是交易机器人，也不是 RAG 演示。</strong>
            </aside>
          </div>
          <div class="hero-kpi-grid" aria-label="v4 核心指标">
            <div class="proof-card"><strong>500</strong><span>SEC 10-K 年报</span></div>
            <div class="proof-card"><strong>8,133</strong><span>样本外预测</span></div>
            <div class="proof-card"><strong>0.2395</strong><span>预注册主结果 Rank IC</span></div>
            <div class="proof-card"><strong>0 / 2</strong><span>审计失败 / 警告</span></div>
          </div>
          <p class="metric-note">最佳探索性 Rank IC：<code>0.3668</code>，与预注册主结果分开报告。</p>
        </div>
      </section>

      <section class="section">
        <div class="container">
          <div class="section-header"><p class="eyebrow">当前版本</p><h2>50 家公司应用级结果包 v4</h2><p><code>{RUN_ID}</code></p></div>
          <div class="metric-grid compact">
{metric_cards([("1,500", "标签"), ("520k+", "特征记录"), ("594", "测试规格"), ("100%", "主预测覆盖率")])}
          </div>
        </div>
      </section>

      <section class="section muted">
        <div class="container">
          <div class="section-header"><p class="eyebrow">结果快照</p><h2>波动率排序证据</h2><p>最强观察结果属于探索性比较；预注册 Ridge 主结果仍为正。</p></div>
{rank_chart(True)}
        </div>
      </section>

      <section class="section" id="contribution">
        <div class="container">
          <div class="section-header"><p class="eyebrow">我的贡献</p><h2>我设计和实现了什么</h2><p>我从 SEC 年报抓取到样本外证据审计，搭建了完整研究流程。</p></div>
          <div class="capability-card-grid contribution-cards">
            <article class="capability-card"><strong>研究设计</strong><p>滚动训练 / 验证 / 测试切分、前瞻标签、预注册规格和 embargo 防泄漏控制。</p></article>
            <article class="capability-card"><strong>金融 NLP 流水线</strong><p>年报 section 解析、Loughran-McDonald 词典特征、训练期内 TF-IDF/SVD 和模型清单。</p></article>
            <article class="capability-card"><strong>评估与审计</strong><p>Rank IC、特征消融、行业中性诊断、cluster bootstrap、覆盖率检查和自动报告。</p></article>
          </div>
          <p class="tech-stack">Python · scikit-learn · XGBoost · SEC EDGAR · pytest · Ruff · GitHub Actions</p>
        </div>
      </section>

      <section class="section muted">
        <div class="container">
          <div class="section-header"><p class="eyebrow">为什么重要</p><h2>不只是情绪分数或文档检索</h2></div>
          <div class="capability-card-grid">
            <div class="capability-card"><strong>前瞻标签</strong><p>把年报文本连接到未来波动率和异常收益目标。</p></div>
            <div class="capability-card"><strong>滚动样本外设计</strong><p>按时间区分训练、验证和测试窗口。</p></div>
            <div class="capability-card"><strong>训练期特征</strong><p>每个 split 的 TF-IDF/SVD 词表只在训练窗口拟合。</p></div>
            <div class="capability-card"><strong>证据层级</strong><p>把预注册主结论和探索性模型比较分开报告。</p></div>
            <div class="capability-card"><strong>研究审计</strong><p>披露 parser 问题、bootstrap 不确定性、覆盖率和多重检验。</p></div>
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
              <span class="badge">Applied financial NLP · v4 evidence</span>
              <h1>Financial 10-K Text Agent</h1>
              <p class="hero-hook">10-K text ranks future volatility — but does not prove tradable alpha.</p>
              <p class="hero-subtitle">An auditable SEC 10-K text pipeline for out-of-sample volatility prediction and empirical research audit.</p>
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
            <article class="capability-card"><strong>Research design</strong><p>Rolling train/validation/test splits, forward labels, preregistered specifications, and embargo-based leakage controls.</p></article>
            <article class="capability-card"><strong>Financial NLP pipeline</strong><p>Section parsing, Loughran-McDonald tone features, train-window-only TF-IDF/SVD, and model manifests.</p></article>
            <article class="capability-card"><strong>Evaluation and audit</strong><p>Rank IC, feature ablation, industry-neutral diagnostics, clustered bootstrap, coverage checks, and automated reports.</p></article>
          </div>
          <p class="tech-stack">Python · scikit-learn · XGBoost · SEC EDGAR · pytest · Ruff · GitHub Actions</p>
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
        "explore": "探索性最佳" if zh else "Exploratory best",
        "diag": "增量诊断" if zh else "Incremental diagnostic",
        "base": "经济基准" if zh else "Economic baseline",
        "primary": "预注册主结果" if zh else "Preregistered primary",
        "pp": "主预测" if zh else "Primary prediction",
        "portfolio": "主组合" if zh else "Primary portfolio",
        "alpha": "尚未建立可交易 alpha。" if zh else "Tradable alpha is not established.",
    }
    return f"""          <div class="home-result-layout">
            <div class="model-chart-card" aria-label="Rank IC comparison chart">
              <div class="rank-chart-row is-exploratory"><div><strong>{"仅 TF-IDF/SVD" if zh else "TF-IDF/SVD only"}</strong><span>{labels["explore"]}</span></div><span class="rank-track"><span style="--bar-width: 100%"></span></span><code>0.3668</code></div>
              <div class="rank-chart-row"><div><strong>{"行业 + 文本" if zh else "Industry + text"}</strong><span>{labels["diag"]}</span></div><span class="rank-track"><span style="--bar-width: 90%"></span></span><code>0.3296</code></div>
              <div class="rank-chart-row"><div><strong>{"行业均值" if zh else "Industry mean"}</strong><span>{labels["base"]}</span></div><span class="rank-track"><span style="--bar-width: 80%"></span></span><code>0.2924</code></div>
              <div class="rank-chart-row is-primary"><div><strong>{"综合文本 Ridge" if zh else "Combined text Ridge"}</strong><span>{labels["primary"]}</span></div><span class="rank-track"><span style="--bar-width: 65%"></span></span><code>0.2395</code></div>
            </div>
            <div class="claim-pair">
              <article class="claim-card claim-positive"><span>{labels["pp"]}</span><strong>Rank IC 0.2395</strong><p>{"原始 p 值" if zh else "Raw p-value"} <code>0.00067</code>. {"支持探索性波动率排序证据。" if zh else "Positive exploratory volatility-ranking evidence."}</p></article>
              <article class="claim-card claim-negative"><span>{labels["portfolio"]}</span><strong>Sharpe -0.8539</strong><p>{"原始 p 值" if zh else "Raw p-value"} <code>0.1147</code>. {labels["alpha"]}</p></article>
            </div>
          </div>"""


def pipeline(zh: bool) -> str:
    nodes = [
        ("SEC 年报", "acceptance 时间戳") if zh else ("SEC Filings", "acceptance timestamps"),
        ("Parser 复核", "section 质量标记") if zh else ("Parser Review", "section quality flags"),
        ("标签", "未来目标") if zh else ("Labels", "future targets"),
        ("滚动切分", "embargo + OOS") if zh else ("Rolling Splits", "embargo + OOS"),
        ("文本特征", "仅训练窗口") if zh else ("Text Features", "train-window only"),
        ("诊断", "消融 + bootstrap") if zh else ("Diagnostics", "ablation + bootstrap"),
        ("审计", "结论与边界") if zh else ("Audit", "claims + boundaries"),
    ]
    parts = []
    for i, (a, b) in enumerate(nodes):
        parts.append(f'<div class="pipeline-node"><strong>{a}</strong><span>{b}</span></div>')
        if i != len(nodes) - 1:
            parts.append('<div class="pipeline-arrow" aria-hidden="true">→</div>')
    return f"""      <section class="section">
        <div class="container">
          <div class="section-header"><p class="eyebrow">{"流程" if zh else "Pipeline"}</p><h2>{"从 SEC 年报到可审计证据" if zh else "From SEC Filing to Audited Evidence"}</h2></div>
          <div class="pipeline-flow" aria-label="{"研究流程" if zh else "Research pipeline"}">
            {"".join(parts)}
          </div>
        </div>
      </section>"""


def evidence_links(zh: bool) -> str:
    links = [
        ("v4 结果包", "所有公开文件", RESULT_DIR) if zh else ("v4 Result Package", "all public artifacts", RESULT_DIR),
        ("因子卡片", "最快结果摘要", f"{RESULT_BLOB}/factor_card.md") if zh else ("Factor Card", "fastest result summary", f"{RESULT_BLOB}/factor_card.md"),
        ("特征消融", "文本与行业对比", f"{RESULT_BLOB}/feature_ablation_summary.json") if zh else ("Feature Ablation", "text versus industry", f"{RESULT_BLOB}/feature_ablation_summary.json"),
        ("Bootstrap 报告", "聚类置信区间", f"{RESULT_BLOB}/primary_rank_ic_bootstrap_report.json") if zh else ("Bootstrap Report", "clustered confidence intervals", f"{RESULT_BLOB}/primary_rank_ic_bootstrap_report.json"),
        ("Parser 复核", "人工质量附录", f"{RESULT_BLOB}/parser_manual_review_appendix.md") if zh else ("Parser Review", "manual quality appendix", f"{RESULT_BLOB}/parser_manual_review_appendix.md"),
    ]
    cards = "".join(f'<a class="artifact-card" aria-label="{a} - {b}" href="{href}"><span>{a}</span><span>{b}</span></a>' for a, b, href in links)
    return f"""      <section class="section muted">
        <div class="container split-section">
          <div><p class="eyebrow">{"查看证据" if zh else "Inspect the evidence"}</p><h2>{"沿着公开审计链检查" if zh else "Follow the Public Audit Trail"}</h2><p>{"精简、合规的公开文件把每个核心数字连接到可复核证据。" if zh else "Compact, license-safe artifacts connect every headline number to a reproducible evidence file."}</p></div>
          <div class="artifact-list">{cards}</div>
        </div>
      </section>"""


def boundary(zh: bool) -> str:
    text = "这是应用级探索性运行，不是 CRSP/WRDS 等价的正式资产定价证据，不是无幸存者偏差复现，不是生产交易系统，也不是投资建议。" if zh else "This is an applied-grade exploratory run, not CRSP/WRDS-equivalent formal asset-pricing evidence, a survivorship-free replication, a production trading system, proven tradable alpha, or investment advice."
    return f"""      <section class="section"><div class="container"><div class="boundary-box"><h2>{"使用边界" if zh else "Usage Boundary"}</h2><p>{text}</p></div></div></section>"""


def results(zh: bool) -> str:
    toc = [("primary-result", "主结果" if zh else "Primary result"), ("ablation", "特征消融" if zh else "Feature ablation"), ("bootstrap", "Bootstrap"), ("coverage", "覆盖率" if zh else "Coverage"), ("reproducibility", "复现" if zh else "Reproduce")]
    toc_html = "".join(f'<a href="#{anchor}">{label}</a>' for anchor, label in toc)
    metric_items = [("500", "SEC 10-K 年报" if zh else "SEC 10-K filings"), ("1,500", "标签" if zh else "Labels"), ("8,133", "样本外预测" if zh else "OOS predictions"), ("520,465", "特征记录" if zh else "Feature records"), ("594", "测试规格" if zh else "Tested specifications"), ("26", "检验族" if zh else "Testing families"), ("100%", "合格样本外覆盖率" if zh else "Eligible OOS coverage"), ("0 / 2", "审计失败 / 警告" if zh else "Audit failures / warnings")]
    return f"""      <section class="page-hero">
        <div class="container narrow">
          <span class="badge">{"50 家公司 v4 公开结果包" if zh else "50-company v4 public package"}</span>
          <h1>{"结果与文件" if zh else "Results and Artifacts"}</h1>
          <p class="hero-hook">{"最强证据是波动率排序，而不是股票收益 alpha。" if zh else "The strongest evidence is volatility ranking, not stock-return alpha."}</p>
          <p class="hero-subtitle">{"公开精简摘要：" if zh else "Compact public summary of"} <code>{RUN_ID}</code>.</p>
          <nav class="page-toc" aria-label="{"本页导航" if zh else "On this page"}">{toc_html}</nav>
        </div>
      </section>

      <section class="section muted" id="primary-result">
        <div class="container">
          <div class="result-summary-card"><div><p class="eyebrow">{"预注册主预测" if zh else "Preregistered primary prediction"}</p><h2>Ridge Rank IC = 0.2395</h2><p>{"对未来 20 日实现波动率有正向样本外排序信息；原始 p 值" if zh else "Positive out-of-sample ranking information for future 20-day realized volatility; raw p-value"} <code>0.00067</code>.</p></div><div class="result-claim-box"><span>{"结论边界" if zh else "Claim boundary"}</span><strong>{"探索性波动率预测证据，不是可交易 alpha。" if zh else "Exploratory volatility-prediction evidence, not tradable alpha."}</strong></div></div>
          <div class="claim-pair result-claim-pair"><article class="claim-card claim-positive"><span>{"主预测" if zh else "Primary prediction"}</span><strong>Rank IC 0.2395</strong><p>{"预注册主预测规格完全覆盖，且方向为正。" if zh else "Positive and fully covered across the preregistered prediction specification."}</p></article><article class="claim-card claim-negative"><span>{"主组合" if zh else "Primary portfolio"}</span><strong>Sharpe -0.8539</strong><p>{"原始 p 值" if zh else "Raw p-value"} <code>0.1147</code>; {"尚未建立正式可交易 alpha。" if zh else "formal tradable alpha is not established."}</p></article></div>
        </div>
      </section>

      <section class="section"><div class="container"><div class="section-header"><p class="eyebrow">{"运行摘要" if zh else "Run summary"}</p><h2>{"应用级公开证据" if zh else "Applied-Grade Public Evidence"}</h2></div><div class="metric-grid">{metric_cards(metric_items)}</div></div></section>

      <section class="section muted"><div class="container split-section equal-cards"><article class="finding-card"><p class="eyebrow">{"预注册主结果" if zh else "Preregistered primary"}</p><h2>{"综合文本 Ridge" if zh else "Combined-Text Ridge"}</h2><p><code>realized_volatility_1_20</code>, {"用 ALL_SPLITS Rank IC 评价。" if zh else "evaluated by ALL_SPLITS Rank IC."}</p><div class="result-grid"><div><span class="result-label">Rank IC</span><strong class="result-number">0.2395</strong></div><div><span class="result-label">{"原始 p 值" if zh else "Raw p-value"}</span><strong class="result-number">0.00067</strong></div></div><p>{"支持正向探索性波动率排序证据。" if zh else "Supports positive exploratory volatility-ranking evidence."}</p></article><article class="exploratory-card"><p class="eyebrow">{"最佳探索性观察结果" if zh else "Best observed exploratory result"}</p><h2>{"仅 TF-IDF/SVD 的 Ridge" if zh else "TF-IDF/SVD-Only Ridge"}</h2><p>{"最强的模型比较观察结果，不是预注册主结论。" if zh else "The strongest observed model-comparison result, not the preregistered primary claim."}</p><div class="result-grid"><div><span class="result-label">Rank IC</span><strong class="result-number">0.3668</strong></div><div><span class="result-label">NW t-stat</span><strong class="result-number">5.4055</strong></div></div><p>RMSE <code>0.00992</code>.</p></article></div></section>
{ablation(zh)}
{bootstrap(zh)}
{coverage_and_artifacts(zh)}
{reproducibility(zh)}"""


def ablation(zh: bool) -> str:
    rows = [
        ("仅 TF-IDF/SVD" if zh else "TF-IDF/SVD only", "Ridge", "0.3668", "0.3416", "0.00992", "100%", "93%"),
        ("行业 + 文本" if zh else "Industry + text", "Ridge", "0.3296", "0.3251", "0.01076", "90%", "89%"),
        ("仅行业" if zh else "Industry only", "Industry mean", "0.2924", "0.0000", "0.00913", "80%", "0%"),
        ("仅词典" if zh else "Dictionary only", "Ridge", "0.2244", "0.2465", "0.00984", "61%", "67%"),
        ("综合文本" if zh else "Combined text", "Ridge", "0.2395", "0.2023", "0.01932", "65%", "55%"),
    ]
    chart = "".join(f'<div class="ablation-row"><strong>{name}</strong><div class="paired-bars"><span class="bar-raw" style="--bar-width: {raw_w}"></span><span class="bar-neutral" style="--bar-width: {neu_w}"></span></div><code>{raw} / {neu}</code></div>' for name, _, raw, neu, _, raw_w, neu_w in rows)
    table = "".join(f'<tr><td>{name}</td><td>{est}</td><td class="numeric">{raw}</td><td class="numeric">{neu}</td><td class="numeric">{rmse}</td></tr>' for name, est, raw, neu, rmse, *_ in rows)
    return f"""      <section class="section" id="ablation"><div class="container"><div class="section-header"><p class="eyebrow">{"特征消融" if zh else "Feature ablation"}</p><h2>{"原始与行业中性 Rank IC" if zh else "Raw vs Industry-Neutral Rank IC"}</h2><p>{"在 split 内行业去均值后，文本表示仍保留正向排序诊断。" if zh else "Text representations retain positive ranking diagnostics after within-split industry demeaning."}</p></div><div class="ablation-chart" aria-label="Feature ablation Rank IC chart"><div class="chart-legend"><span class="legend-raw">{"原始 Rank IC" if zh else "Raw Rank IC"}</span><span class="legend-neutral">{"行业中性 Rank IC" if zh else "Industry-neutral Rank IC"}</span></div>{chart}</div><div class="table-wrap chart-fallback"><table><thead><tr><th>{"特征集" if zh else "Feature set"}</th><th>{"估计器" if zh else "Estimator"}</th><th>Rank IC</th><th>{"行业中性 Rank IC" if zh else "Industry-neutral Rank IC"}</th><th>RMSE</th></tr></thead><tbody>{table}</tbody></table></div></div></section>"""


def bootstrap(zh: bool) -> str:
    rows = [
        ("原始 Rank IC" if zh else "Raw Rank IC", "Split bootstrap", "0.2395", "[-0.0050, 0.4841]", "0.111"),
        ("原始 Rank IC" if zh else "Raw Rank IC", "Event-date bootstrap" if not zh else "事件日 bootstrap", "0.2395", "[0.0719, 0.3743]", "0.005"),
        ("原始 Rank IC" if zh else "Raw Rank IC", "Ticker-cluster bootstrap" if not zh else "Ticker 聚类 bootstrap", "0.2395", "[0.1091, 0.3522]", "0.001"),
        ("行业中性 Rank IC" if zh else "Industry-neutral Rank IC", "Split bootstrap", "0.2023", "[-0.1157, 0.5202]", "0.117"),
        ("行业中性 Rank IC" if zh else "Industry-neutral Rank IC", "Event-date bootstrap" if not zh else "事件日 bootstrap", "0.2023", "[-0.1546, 0.4273]", "0.366"),
        ("行业中性 Rank IC" if zh else "Industry-neutral Rank IC", "Ticker-cluster bootstrap" if not zh else "Ticker 聚类 bootstrap", "0.2023", "[-0.1787, 0.4181]", "0.357"),
    ]
    trs = "".join(f'<tr><td>{a}</td><td>{b}</td><td class="numeric">{c}</td><td>{d}</td><td class="numeric">{e}</td></tr>' for a, b, c, d, e in rows)
    return f"""      <section class="section muted" id="bootstrap"><div class="container"><div class="section-header"><p class="eyebrow">Bootstrap inference</p><h2>{"主 Rank IC 置信区间" if zh else "Primary Rank IC Confidence Intervals"}</h2><p>{"使用 2,000 次确定性重抽样；由于只有四个样本外 split 簇，split bootstrap 结论不充分。" if zh else "Two thousand deterministic resamples. Split bootstrap is inconclusive because there are only four OOS split clusters."}</p></div><div class="table-wrap"><table><thead><tr><th>{"估计量" if zh else "Estimand"}</th><th>{"方法" if zh else "Method"}</th><th>{"点估计" if zh else "Point"}</th><th>95% CI</th><th>p-value</th></tr></thead><tbody>{trs}</tbody></table></div></div></section>"""


def coverage_and_artifacts(zh: bool) -> str:
    cards = [
        ("因子卡片", "最快结果摘要", f"{RESULT_BLOB}/factor_card.md") if zh else ("Factor Card", "fastest result summary", f"{RESULT_BLOB}/factor_card.md"),
        ("实证报告", "完整文字报告", f"{RESULT_BLOB}/empirical_report.md") if zh else ("Empirical Report", "full narrative report", f"{RESULT_BLOB}/empirical_report.md"),
        ("特征消融", "文本与行业对比", f"{RESULT_BLOB}/feature_ablation_summary.json") if zh else ("Feature Ablation", "text versus industry", f"{RESULT_BLOB}/feature_ablation_summary.json"),
        ("审计报告", "覆盖率与警告", f"{RESULT_BLOB}/audit_report.json") if zh else ("Audit Report", "coverage and warnings", f"{RESULT_BLOB}/audit_report.json"),
        ("多重检验", "规格族", f"{RESULT_BLOB}/multiple_testing_report.json") if zh else ("Multiple Testing", "specification families", f"{RESULT_BLOB}/multiple_testing_report.json"),
        ("Parser 复核", "section 质量附录", f"{RESULT_BLOB}/parser_manual_review_appendix.md") if zh else ("Parser Review", "section quality appendix", f"{RESULT_BLOB}/parser_manual_review_appendix.md"),
    ]
    links = "".join(f'<a class="artifact-card" aria-label="{a} - {b}" href="{href}"><span>{a}</span><span>{b}</span></a>' for a, b, href in cards)
    coverage_text = "原始标签覆盖率为 49.6%，合格样本外覆盖率为 100%，模型预期预测覆盖率为 98.546%，主预测 / 主组合覆盖率为 100%。" if zh else "Raw label coverage is 49.6%, eligible OOS coverage is 100%, model-expected prediction coverage is 98.546%, and primary prediction / portfolio coverage is 100%."
    boundary_text = "本公开数据实验使用 FMP/Yahoo 混合市场数据和应用级市值估计，不是 CRSP/WRDS 等价的无幸存者偏差复现。" if zh else "This public-source experiment uses mixed FMP/Yahoo market data and applied-grade market-cap estimates. It is not a CRSP/WRDS-equivalent survivorship-free replication."
    return f"""      <section class="section" id="coverage"><div class="container split-section equal-cards"><div class="boundary-box"><h2>{"覆盖率与控制" if zh else "Coverage and Controls"}</h2><p>{coverage_text}</p></div><div class="boundary-box"><h2>{"数据边界" if zh else "Data Boundary"}</h2><p>{boundary_text}</p></div></div></section><section class="section muted"><div class="container"><div class="section-header"><p class="eyebrow">{"代表性证据文件" if zh else "Representative evidence files"}</p><h2>{"查看公开文件" if zh else "Inspect the Public Artifacts"}</h2></div><div class="artifact-grid">{links}</div></div></section>"""


def reproducibility(zh: bool) -> str:
    return f"""      <section class="section muted" id="reproducibility"><div class="container narrow"><div class="section-header"><p class="eyebrow">{"可复现性" if zh else "Reproducibility"}</p><h2>{"在本地运行公开代码" if zh else "Run the Public Code Locally"}</h2></div><div class="code-card"><div class="code-toolbar"><span>Shell</span><button class="copy-button" type="button" data-copy-target="run-code">{"复制" if zh else "Copy"}</button></div><pre id="run-code"><code>git clone https://github.com/uiclxh/financial-10k-text-agent.git
cd financial-10k-text-agent
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest</code></pre><p class="small-note">{"公开仓库不包含原始授权输入数据。" if zh else "Raw licensed inputs are not included in the public repository."}</p></div></div></section>"""


def methods(zh: bool) -> str:
    flow = [
        ("Filing 时间戳", "SEC acceptance time 定义信息可得时间。") if zh else ("Filing timestamp", "SEC acceptance time defines information availability."),
        ("Section 解析", "抽取 Business、Risk Factors、Legal Proceedings 和 MD&A。") if zh else ("Section parsing", "Business, Risk Factors, Legal Proceedings, and MD&A are extracted."),
        ("前瞻标签", "波动率和 CAR 目标只在 filing 可得后开始计算。") if zh else ("Forward labels", "Volatility and CAR targets begin only after filing availability."),
        ("滚动切分", "训练、验证和测试窗口随时间滚动，并执行 embargo purge。") if zh else ("Rolling splits", "Train, validation, and test windows move through time with embargo purges."),
        ("训练窗口特征", "TF-IDF/SVD 词表只在训练窗口内拟合。") if zh else ("Train-window features", "TF-IDF/SVD vocabularies are fit inside training windows only."),
        ("仅验证集调参", "超参数只用 validation Rank IC 选择。") if zh else ("Validation-only tuning", "Hyperparameters are selected using validation Rank IC only."),
        ("考虑并列值的测试 Rank IC", "测试排序使用平均秩；常数预测返回零 Rank IC。") if zh else ("Tie-aware test Rank IC", "Test ranking uses average ranks; constant predictions return zero Rank IC."),
        ("证据层级", "主规格、稳健性规格和探索性规格保持分离。") if zh else ("Evidence hierarchy", "Primary, robustness, and exploratory specifications remain separate."),
        ("审计边界", "披露覆盖率、parser 质量、数据限制和结论强度。") if zh else ("Audit boundary", "Coverage, parser quality, data limitations, and claim strength are disclosed."),
    ]
    steps = []
    for i, (title, desc) in enumerate(flow, 1):
        steps.append(f'<div class="leakage-step"><span>{i}</span><strong>{title}</strong><small>{desc}</small></div>')
        if i != len(flow):
            steps.append('<div class="leakage-arrow" aria-hidden="true">↓</div>')
    controls = [
        ("事件时间对齐", "Filing 时间戳定义信息可得性。") if zh else ("Event-time alignment", "Filing timestamps define information availability."),
        ("滚动样本外设计", "训练 / 验证 / 测试窗口随时间滚动。") if zh else ("Rolling OOS design", "Train / validation / test windows roll through time."),
        ("防泄漏控制", "Embargo purge 和 split-leakage logs。") if zh else ("Leakage control", "Embargo purge and split-leakage logs."),
        ("模型选择", "仅使用 validation Rank IC。") if zh else ("Model selection", "Validation-only Rank IC."),
        ("TF-IDF 控制", "训练窗口内词表拟合。") if zh else ("TF-IDF control", "Train-window-only vocabulary fitting."),
        ("文本增量诊断", "行业中性 Rank IC 和特征消融。") if zh else ("Incremental text diagnostic", "Industry-neutral Rank IC and feature ablation."),
        ("统计不确定性", "Newey-West 和聚类 bootstrap 置信区间。") if zh else ("Statistical uncertainty", "Newey-West and clustered bootstrap confidence intervals."),
        ("数据挖掘风险", "规格注册表和多重检验报告。") if zh else ("Data snooping", "Specification registry and multiple-testing report."),
        ("Parser 质量", "对较短或异常 section 建立人工复核附录。") if zh else ("Parser quality", "Manual review appendix for short or malformed sections."),
    ]
    control_rows = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in controls)
    return f"""      <section class="page-hero"><div class="container narrow"><span class="badge">{"方法 / 审计 · v4" if zh else "Methods / Audit · v4"}</span><h1>{"方法与审计" if zh else "Methods and Audit"}</h1><p class="hero-hook">{"每个结论都必须连接到带时间戳、可检验的证据文件。" if zh else "Every claim must be linked to a timestamped, testable artifact."}</p><p class="hero-subtitle">{"年报、标签、切分、特征、模型、预测、推断、组合诊断和审计检查共同构成证据链。" if zh else "Filings, labels, splits, features, models, predictions, inference, portfolio diagnostics, and audit checks form one evidence chain."}</p><p><code>{RUN_ID}</code></p><nav class="page-toc" aria-label="{"本页导航" if zh else "On this page"}"><a href="#research-flow">{"研究流程" if zh else "Research flow"}</a><a href="#controls">{"控制项" if zh else "Controls"}</a><a href="#features">{"特征" if zh else "Features"}</a><a href="#parser-review">Parser {"复核" if zh else "review"}</a><a href="#claim-boundary">{"证据边界" if zh else "Claim boundary"}</a><a href="#boundary">{"数据边界" if zh else "Data boundary"}</a></nav></div></section>
      <section class="section" id="research-flow"><div class="container"><div class="section-header"><p class="eyebrow">{"防泄漏研究设计" if zh else "Leakage-safe research design"}</p><h2>{"只有过去可得信息进入预测" if zh else "Only Past Information Enters the Forecast"}</h2><p>{"每个文本特征和模型决策都必须在预测时间点之前可得。" if zh else "Every text feature and model decision must be available before the prediction timestamp."}</p></div><div class="leakage-flow-card" aria-label="Leakage-safe research flow">{"".join(steps)}</div></div></section>
      <section class="section muted" id="controls"><div class="container"><div class="section-header"><p class="eyebrow">{"关键控制项" if zh else "Key controls"}</p><h2>{"研究控制概览" if zh else "Research Controls at a Glance"}</h2></div><div class="table-wrap"><table><thead><tr><th>{"控制项" if zh else "Control"}</th><th>{"实现方式" if zh else "Implementation"}</th></tr></thead><tbody>{control_rows}</tbody></table></div></div></section>
      <section class="section" id="features"><div class="container split-section"><div><p class="eyebrow">{"特征构造" if zh else "Feature construction"}</p><h2>{"金融文本表示" if zh else "Financial Text Representations"}</h2><p>{"Loughran-McDonald 词典语调和 TF-IDF/SVD 覆盖全文、Business、Risk Factors、Legal Proceedings 和 MD&A 范围。" if zh else "Loughran-McDonald dictionary tone and TF-IDF/SVD are built over full filing, Business, Risk Factors, Legal Proceedings, and MD&A scopes."}</p></div><div class="table-wrap"><table><thead><tr><th>{"特征集" if zh else "Feature set"}</th><th>{"含义" if zh else "Meaning"}</th></tr></thead><tbody><tr><td><code>industry_only</code></td><td>{"训练窗口行业均值基准。" if zh else "Training-window industry-mean baseline."}</td></tr><tr><td><code>dictionary_only</code></td><td>{"词典语调文本特征。" if zh else "Dictionary-tone text features."}</td></tr><tr><td><code>tfidf_svd_only</code></td><td>{"TF-IDF/SVD 文本表示。" if zh else "TF-IDF/SVD text representations."}</td></tr><tr><td><code>combined_text</code></td><td>{"词典与文本表示的组合。" if zh else "Combined dictionary and text representation."}</td></tr><tr><td><code>industry_plus_text</code></td><td>{"行业特征加文本特征。" if zh else "Industry features plus text features."}</td></tr></tbody></table></div></div></section>
      <section class="section muted"><div class="container"><div class="method-callout"><span>{"行业中性诊断" if zh else "Industry-neutral diagnostic"}</span><strong>{"移除 split-行业均值后，文本是否仍保留信息？" if zh else "Does text retain information after removing split-industry means?"}</strong><p>{"行业中性 Rank IC 是描述性诊断，不是因果分解。" if zh else "Industry-neutral Rank IC is a descriptive diagnostic, not a causal decomposition."}</p></div></div></section>
      <section class="section"><div class="container"><div class="section-header"><p class="eyebrow">Bootstrap inference</p><h2>{"如何报告不确定性" if zh else "How Uncertainty Is Reported"}</h2></div><div class="policy-grid"><div><strong>Split bootstrap</strong><p>{"v4 只有四个 OOS split 簇，因此结论不充分。" if zh else "Inconclusive for v4 because there are only four OOS split clusters."}</p></div><div><strong>{"事件日 bootstrap" if zh else "Event-date bootstrap"}</strong><p>{"支持正向原始主 Rank IC 区间。" if zh else "Supports a positive raw primary Rank IC interval."}</p></div><div><strong>{"Ticker 聚类 bootstrap" if zh else "Ticker-cluster bootstrap"}</strong><p>{"支持正向原始主 Rank IC 区间。" if zh else "Supports a positive raw primary Rank IC interval."}</p></div><div><strong>{"行业中性 bootstrap" if zh else "Industry-neutral bootstrap"}</strong><p>{"点估计为正，但 bootstrap 稳健性不足。" if zh else "Positive point estimate, but not bootstrap-robust."}</p></div></div></div></section>
      <section class="section muted" id="parser-review"><div class="container"><div class="section-header"><p class="eyebrow">{"Parser 质量复核" if zh else "Parser quality review"}</p><h2>{"Section 抽取经过审计，而不是默认可信" if zh else "Section Extraction Is Audited, Not Assumed"}</h2></div><div class="metric-grid compact">{metric_cards([("2,000", "解析 section 记录" if zh else "Parsed section records"), ("144", "人工复核记录" if zh else "Manual-review records"), ("144", "被排除 section 记录" if zh else "Excluded section-level records"), ("494", "较短但保留记录" if zh else "Short but included records")])}</div><p class="section-note">{"Item 1A 和 Item 7 少于 100 词时从 section 级特征中排除；100 到 499 词的核心 section 保留但带 warning。" if zh else "Item 1A and Item 7 below 100 words are excluded from section-level features. Core sections from 100 to 499 words remain included but carry a warning."}</p></div></section>
      <section class="section" id="claim-boundary"><div class="container"><div class="section-header"><p class="eyebrow">{"证据边界" if zh else "Evidence boundary"}</p><h2>{"预测证据与交易证据分别判断" if zh else "Prediction and Trading Evidence Are Judged Separately"}</h2></div><div class="result-pair"><article class="result-card primary"><p class="eyebrow">{"预注册主预测" if zh else "Preregistered primary prediction"}</p><h3>Ridge · <code>realized_volatility_1_20</code></h3><div class="result-stat"><span>Rank IC</span><strong>0.2395</strong></div><p>{"原始 p 值为 0.00067，支持探索性波动率排序证据。" if zh else "Raw p-value 0.00067; supports exploratory volatility-ranking evidence."}</p></article><article class="result-card diagnostic"><p class="eyebrow">{"预注册主组合" if zh else "Preregistered primary portfolio"}</p><h3>{"月度行业中性等权组合" if zh else "Monthly sector-neutral equal-weight"}</h3><div class="result-stat"><span>Sharpe</span><strong>-0.8539</strong></div><p>{"原始 p 值为 0.1147；未建立可交易 alpha。" if zh else "Raw p-value 0.1147; does not establish tradable alpha."}</p></article></div></div></section>
      <section class="section" id="boundary"><div class="container"><div class="boundary-box"><h2>{"正式结论边界" if zh else "Formal Result Boundary"}</h2><p>{"正式实证金融结论受数据边界限制，而不是 pipeline 失败：FMP/Yahoo 混合数据、应用级市值估计、固定 50 公司样本、parser 质量限制，以及少量诊断模型-标签对缺失。" if zh else "Formal empirical-finance claims are blocked by data-boundary issues, not pipeline failures: mixed FMP/Yahoo data, applied-grade market-cap estimates, fixed 50-company panel, parser-quality limitations, and a small number of missing diagnostic model-label pairs."}</p><p>{"该项目应理解为用于探索性波动率排序的应用级、可审计金融 NLP 工作流。" if zh else "The project should be interpreted as an applied-grade, auditable financial NLP workflow for exploratory volatility ranking."}</p></div></div></section>"""


def write_pages() -> None:
    pages = {
        "index.html": shell("index.html", "overview", "Financial 10-K Text Agent", "An auditable SEC 10-K text pipeline for out-of-sample volatility-ranking research.", home(False), False),
        "index.zh-CN.html": shell("index.zh-CN.html", "overview", "Financial 10-K Text Agent", "一个可审计的 SEC 10-K 金融文本研究流水线，用于检验未来波动率排序信号。", home(True), True),
        "results.html": shell("results.html", "results", "Results | Financial 10-K Text Agent", "V4 results, feature ablation, bootstrap inference, and audit artifacts for the Financial 10-K Text Agent.", results(False), False),
        "results.zh-CN.html": shell("results.zh-CN.html", "results", "结果 | Financial 10-K Text Agent", "Financial 10-K Text Agent 的 v4 结果、特征消融、bootstrap 推断与审计文件。", results(True), True),
        "methods.html": shell("methods.html", "methods", "Methods and Audit | Financial 10-K Text Agent", "Leakage controls, rolling OOS design, parser review, bootstrap inference, and audit boundaries for the v4 package.", methods(False), False),
        "methods.zh-CN.html": shell("methods.zh-CN.html", "methods", "方法与审计 | Financial 10-K Text Agent", "v4 结果包的方法、审计、防泄漏、parser 复核、bootstrap 和数据边界说明。", methods(True), True),
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
  const isChinese = originalLabel.includes("复制");
  const text = target.textContent.trim();

  try {
    await navigator.clipboard.writeText(text);
    button.textContent = isChinese ? "已复制" : "Copied";
    button.classList.add("is-copied");
  } catch {
    button.textContent = isChinese ? "复制失败" : "Copy failed";
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
