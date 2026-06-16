# Financial 10-K Text Agent

一个可审计的金融 NLP 研究流水线，用来检验 SEC 10-K 文本特征是否包含对未来波动率和异常收益目标的样本外预测信息。

这个项目不是 RAG demo、通用 FinBERT 情绪分类器，也不是 AI 炒股机器人。它的定位是：金融 NLP、实证资产定价、rolling 样本外验证和研究审计的交叉项目。

## 当前版本

最新公开结果包：

[`docs/results/50_company_public_fmp_alpha_2016_2025_v1`](docs/results/50_company_public_fmp_alpha_2016_2025_v1/README.md)

| 字段 | 数值 |
| --- | --- |
| Run ID | `50_company_public_fmp_alpha_2016_2025_v1` |
| Universe | 50 家美国大盘公司 |
| 样本 | FY2016-FY2025 |
| SEC 10-K filings | 500 |
| Labels | 1,500 |
| 样本外预测 | 4,716 |
| 特征记录 | 520k+ |
| 测试规格 | 568 |
| Eligible OOS coverage | 100% |
| Audit failures | 0 |
| Audit warnings | 2 |
| 结果状态 | exploratory applied-grade run |

## 本地复现

仓库包含一个不需要私有 API key 或授权数据集的公开 smoke-test pipeline。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev,ml]"
python -m pytest -q
python -m ruff check .
python -m text_factor_lab run --config configs/text_factor_lab/e2e_smoke.yaml --execute
```

smoke run 会把 artifacts 写入：

```text
runs/text_factor_lab/tflab_e2e_smoke_001/
```

如果要重跑 50-company applied-data experiment，需要先提供市场数据 API key 和必要的私有数据缓存：

```powershell
$env:FMP_API_KEY="..."
$env:ALPHAVANTAGE_API_KEY="..."
$env:SEC_USER_AGENT="financial-10k-text-agent contact:your_email@example.com"
python -m text_factor_lab run --config configs/text_factor_lab/50_company_public_fmp_alpha.yaml --execute
```

仓库中提交的 50-company 结果包是 compact artifact summary；raw SEC filings、API responses、完整价格面板和私有中间数据不会提交到仓库。

## 主要发现

预注册的 primary prediction specification 使用 Ridge 预测 `realized_volatility_1_20`，并用 ALL_SPLITS Rank IC 评估。

| Model | Target | Metric | Value | Raw p-value |
| --- | --- | ---: | ---: | ---: |
| Ridge | `realized_volatility_1_20` | Rank IC | 0.2606 | 0.00017 |

这提供了探索性的样本外证据：10-K 文本特征对未来 20 日 realized volatility 含有排序预测信息。这个结论被刻意表述为 prediction evidence，而不是 tradable-alpha claim。

## 最佳探索性预测结果

最强的模型横向比较结果是：

| Model | Target | Rank IC | Newey-West t-stat | RMSE |
| --- | --- | ---: | ---: | ---: |
| XGBoost | `realized_volatility_1_20` | 0.3133 | 6.8479 | 0.00834 |

这个结果被报告为 exploratory model-comparison evidence，而不是预注册 primary claim。

## Pipeline

```text
SEC 10-K filings
-> section parsing
-> event-time label construction
-> rolling train / validation / test splits
-> dictionary tone + train-window-only TF-IDF/SVD features
-> historical mean / industry mean / Ridge / XGBoost
-> OOS Rank IC, Newey-West diagnostics, portfolio diagnostics
-> audit and multiple-testing reports
```

核心 artifacts 包括 document manifests、parsed section indexes、labels、split assignments、feature manifests、model manifests、predictions、evaluation metrics、portfolio diagnostics、multiple-testing reports、audit reports 和 empirical result summaries。

## 使用边界

这个 release 是 applied-grade exploratory research run。它不声称：

- Formal CRSP/WRDS-equivalent asset-pricing evidence
- Survivorship-free research-grade universe
- Production trading system
- Proven tradable alpha
- Investment advice

Portfolio 输出仅作为诊断结果。预注册的 primary portfolio specification 没有证明正式可交易 alpha。

formal result 不成立的主要原因是数据边界，不是 pipeline 失败：

- 市场数据使用 mixed FMP/Yahoo public-source stack
- market-cap-at-selection 是 applied-grade estimates
- universe 是固定 active-company panel，不是 CRSP/WRDS survivorship-free universe
- audit warnings 是边界披露，不是 pipeline failed checks

## License

代码基于 [MIT License](LICENSE) 发布。

公开结果摘要仅用于研究展示。Raw SEC filings、licensed market data、API keys 和 private intermediate datasets 不提交到仓库。
