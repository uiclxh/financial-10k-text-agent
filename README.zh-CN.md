# Financial 10-K Text Agent

一个面向金融实证研究的 SEC 10-K 文本因子流水线：从年报文本生成特征，做样本外预测、组合诊断、泄漏审计、多重检验和自动报告。

最新公开结果包：
[docs/results/10_company_public_fmp_alpha_2016_2025_v1](docs/results/10_company_public_fmp_alpha_2016_2025_v1/README.md)

当前 release：**v0.16.0 - 10-Company FMP/Alpha Applied Pilot**。

核心信息：

- 10 家美国 10-K 公司，FY2016-FY2025。
- 100 份 SEC 10-K，300 个 label，896 条样本外预测。
- eligible OOS prediction coverage = 100%。
- audit failure = 0，audit warning = 2。
- 使用 Loughran-McDonald tone 和 train-window-only TF-IDF/SVD。
- 472 个 tested specifications，并披露多重检验。
- 已准备 30 家和 50 家 S&P 500 行业分层种子样本配置，用于下一步扩展运行。

结论边界：

- 可以说：项目已经形成可审计、可复现的 applied-grade 金融 NLP 研究包。
- 可以说：存在 exploratory forecasting evidence。
- 不应说：已经证明正式交易 alpha 或 production trading strategy。

快速运行：

```bash
python -m pip install -e ".[dev]"
python -m text_factor_lab run --config configs/text_factor_lab/e2e_smoke.yaml --execute
python -m pytest -q
```

完整说明见根目录 [README.md](README.md)。
