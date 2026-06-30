from __future__ import annotations

import argparse
import json
from pathlib import Path

from text_factor_lab import __version__
from text_factor_lab.orchestration import RunManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="text_factor_lab",
        description="Financial Text Factor Lab Agent command line interface.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run an experiment from a YAML config.")
    run_parser.add_argument("--config", required=True, help="Path to experiment config YAML.")
    run_parser.add_argument(
        "--execute",
        action="store_true",
        help="Run the artifact-aware pipeline controller after initialization.",
    )
    run_parser.add_argument(
        "--allow-failed-audit-report",
        action="store_true",
        help="Allow diagnostic report generation when audit fails during --execute.",
    )

    audit_parser = subparsers.add_parser("audit", help="Audit a completed run.")
    audit_parser.add_argument("--run-id", required=True, help="Run identifier.")
    audit_parser.add_argument(
        "--run-dir",
        help="Run artifact directory. Defaults to runs/text_factor_lab/<run-id>.",
    )
    audit_parser.add_argument(
        "--config",
        help="Config path. Defaults to run_dir/config_snapshot.yaml.",
    )
    audit_parser.add_argument("--coverage-threshold", type=float)

    report_parser = subparsers.add_parser("report", help="Generate reports for a run.")
    report_parser.add_argument("--run-id", required=True, help="Run identifier.")
    report_parser.add_argument(
        "--run-dir",
        help="Run artifact directory. Defaults to runs/text_factor_lab/<run-id>.",
    )
    report_parser.add_argument(
        "--config",
        help="Config path. Defaults to run_dir/config_snapshot.yaml.",
    )
    report_parser.add_argument(
        "--output-dir",
        help="Output directory. Defaults to the run artifact directory.",
    )
    report_parser.add_argument(
        "--allow-failed-audit",
        action="store_true",
        help="Generate a diagnostic report even when audit_status=fail.",
    )

    parse_parser = subparsers.add_parser(
        "parse-10k",
        help="Parse one SEC 10-K document into audited section artifacts.",
    )
    parse_parser.add_argument(
        "--manifest-record",
        required=True,
        help="Path to one document_manifest JSON record.",
    )
    parse_parser.add_argument("--document", required=True, help="Path to raw SEC filing HTML/text.")
    parse_parser.add_argument("--output-dir", required=True, help="Directory for parsed artifacts.")

    labels_parser = subparsers.add_parser(
        "build-labels",
        help="Build event-study labels from a document manifest and price CSV.",
    )
    labels_parser.add_argument("--document-manifest", required=True, help="Path to JSONL manifest.")
    labels_parser.add_argument("--prices", required=True, help="Path to price CSV.")
    labels_parser.add_argument("--labels-output", required=True, help="Output JSONL labels path.")
    labels_parser.add_argument(
        "--failures-output",
        required=True,
        help="Output JSONL label failures path.",
    )
    labels_parser.add_argument(
        "--target",
        action="append",
        required=True,
        help="Target name, repeatable. Example: CAR_1_20",
    )
    labels_parser.add_argument("--benchmark", default="SPY", help="Market benchmark ticker.")
    labels_parser.add_argument("--return-type", choices=["log", "simple"], default="log")
    labels_parser.add_argument("--price-field", default="adj_close")
    labels_parser.add_argument("--annualization-days", type=int, default=252)

    split_parser = subparsers.add_parser(
        "build-splits",
        help="Build rolling year train/validation/test split assignments from labels.",
    )
    split_parser.add_argument("--labels", required=True, help="Path to labels JSONL.")
    split_parser.add_argument(
        "--assignments-output",
        required=True,
        help="Output JSONL split assignments path.",
    )
    split_parser.add_argument(
        "--leakage-output",
        required=True,
        help="Output JSONL split leakage report path.",
    )
    split_parser.add_argument("--sample-start", required=True, help="YYYY-MM-DD sample start.")
    split_parser.add_argument("--sample-end", required=True, help="YYYY-MM-DD sample end.")
    split_parser.add_argument("--train-years-min", type=int, required=True)
    split_parser.add_argument("--validation-years", type=int, default=1)
    split_parser.add_argument("--test-years", type=int, default=1)
    split_parser.add_argument("--embargo-days", type=int, default=20)

    feature_parser = subparsers.add_parser(
        "build-features",
        help="Build dictionary tone and TF-IDF text features.",
    )
    feature_parser.add_argument("--document-manifest", required=True)
    feature_parser.add_argument("--parsed-sections", required=True)
    feature_parser.add_argument("--split-assignments", required=True)
    feature_parser.add_argument(
        "--universe-manifest",
        help="Optional universe CSV used to attach sector, industry, and market-cap metadata.",
    )
    feature_parser.add_argument("--features-output", required=True)
    feature_parser.add_argument("--vocabulary-output", required=True)
    feature_parser.add_argument(
        "--feature-manifest-output",
        help=(
            "Output feature manifest JSON path. Defaults to feature_manifest.json "
            "beside features."
        ),
    )
    feature_parser.add_argument(
        "--method",
        action="append",
        choices=["dictionary_tone", "tfidf"],
        required=True,
    )
    feature_parser.add_argument("--tfidf-max-features", type=int, default=50000)
    feature_parser.add_argument("--tfidf-ngram-min", type=int, default=1)
    feature_parser.add_argument("--tfidf-ngram-max", type=int, default=2)
    feature_parser.add_argument("--tfidf-min-df", type=int, default=1)
    feature_parser.add_argument("--tfidf-max-df", type=float, default=1.0)
    feature_parser.add_argument(
        "--no-tfidf-long-features",
        action="store_true",
        help="Do not expand non-zero TF-IDF terms into features.jsonl.",
    )
    feature_parser.add_argument(
        "--feature-matrix-dir",
        help="Optional directory for split/scope/role sparse TF-IDF .npz matrices.",
    )
    feature_parser.add_argument(
        "--feature-matrix-index-output",
        help="Output JSON index for sparse TF-IDF matrices.",
    )
    feature_parser.add_argument(
        "--tfidf-svd-components",
        type=int,
        default=0,
        help="Optional train-fit TruncatedSVD component count to emit as compact features.",
    )

    model_parser = subparsers.add_parser(
        "build-models",
        help="Train baseline and Ridge models from labels, features, and split assignments.",
    )
    model_parser.add_argument("--run-id", required=True)
    model_parser.add_argument("--labels", required=True)
    model_parser.add_argument("--features", required=True)
    model_parser.add_argument("--split-assignments", required=True)
    model_parser.add_argument("--predictions-output", required=True)
    model_parser.add_argument(
        "--prediction-failures-output",
        help=(
            "Output JSONL model prediction failures path. Defaults to "
            "model_prediction_failures.jsonl beside predictions."
        ),
    )
    model_parser.add_argument("--model-manifest-output", required=True)
    model_parser.add_argument("--tuning-log-output", required=True)
    model_parser.add_argument(
        "--model",
        action="append",
        choices=["historical_mean", "industry_mean", "ridge", "xgboost"],
        default=None,
        help="Model to train, repeatable. Defaults to historical_mean and ridge.",
    )
    model_parser.add_argument("--random-seed", type=int, default=42)
    model_parser.add_argument(
        "--ridge-alpha",
        action="append",
        type=float,
        default=None,
        help="Ridge alpha grid value, repeatable.",
    )

    eval_parser = subparsers.add_parser(
        "evaluate-models",
        help="Evaluate predictions and build event-based long-short backtest artifacts.",
    )
    eval_parser.add_argument("--run-id", required=True)
    eval_parser.add_argument("--predictions", required=True)
    eval_parser.add_argument("--labels", required=True)
    eval_parser.add_argument(
        "--prices",
        help="Optional price CSV for daily price-driven portfolio return simulation.",
    )
    eval_parser.add_argument("--metrics-output", required=True)
    eval_parser.add_argument("--backtest-output", required=True)
    eval_parser.add_argument("--portfolio-weights-output")
    eval_parser.add_argument("--portfolio-returns-output")
    eval_parser.add_argument("--portfolio-metrics-output")
    eval_parser.add_argument("--factor-panel-output")
    eval_parser.add_argument("--monthly-portfolio-weights-output")
    eval_parser.add_argument("--monthly-portfolio-returns-output")
    eval_parser.add_argument("--monthly-portfolio-metrics-output")
    eval_parser.add_argument("--delisting-application-report-output")
    eval_parser.add_argument("--tested-specifications-output")
    eval_parser.add_argument("--multiple-testing-output")
    eval_parser.add_argument("--specification-registry-output")
    eval_parser.add_argument("--portfolio-return-type", choices=["simple", "log"], default="simple")
    eval_parser.add_argument("--transaction-cost-bps-one-way", type=float, default=10.0)
    eval_parser.add_argument("--newey-west-lag", type=int, default=19)
    eval_parser.add_argument(
        "--portfolio-signal-direction",
        choices=["long_high_score", "long_low_score", "validation_selected"],
        default="long_high_score",
        help=(
            "Portfolio side policy. validation_selected chooses long_high_score or "
            "long_low_score from the validation window and freezes it for test."
        ),
    )
    eval_parser.add_argument(
        "--target-aware-portfolio-policy",
        choices=["none", "long_low_vol", "risk_scaled"],
        default="none",
        help=(
            "Target-aware portfolio policy. Volatility targets can force low-score "
            "long portfolios or inverse predicted-volatility risk scaling."
        ),
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "run":
        manager = RunManager.from_config_path(args.config)
        status = manager.initialize_run()
        if args.execute:
            report = manager.run_pipeline(
                allow_failed_audit_report=args.allow_failed_audit_report
            )
            print(
                "Run pipeline executed. "
                f"run_id={status.run_id} status={manager.read_status().status} "
                f"stages={report['stage_count']} blocked_reason={report['blocked_reason']} "
                f"orchestrator_report={manager.orchestrator_report_path}"
            )
            return 0
        print(
            "Run initialized as a run manager workspace with independent CLI stages. "
            "Use --execute to run the artifact-aware Label -> Split -> Feature -> "
            "Model -> Evaluation -> Audit -> Report controller. "
            f"run_id={status.run_id} status={manager.read_status().status} "
            f"run_dir={manager.run_dir}"
        )
        return 0

    if args.command == "audit":
        from text_factor_lab.audit import audit_run

        report = audit_run(
            run_id=args.run_id,
            run_dir=args.run_dir,
            config_path=args.config,
            coverage_threshold=args.coverage_threshold,
        )
        print(
            "Audit completed. "
            f"run_id={report.run_id} status={report.audit_status} "
            f"coverage={report.coverage:.3f} failures={report.fail_count} "
            f"warnings={report.warn_count} formal_allowed={report.formal_result_allowed}"
        )
        return 0

    if args.command == "report":
        from text_factor_lab.reports import generate_run_report

        result = generate_run_report(
            run_id=args.run_id,
            run_dir=args.run_dir,
            config_path=args.config,
            output_dir=args.output_dir,
            allow_failed_audit=args.allow_failed_audit,
        )
        print(
            "Report generated. "
            f"run_id={result.run_id} conclusion={result.conclusion_level} "
            f"formal_allowed={result.formal_result_allowed} "
            f"markdown={result.report_markdown_path} "
            f"empirical={result.empirical_report_path} "
            f"factor_card={result.factor_card_path} "
            f"appendix={result.appendix_tables_path} "
            f"summary={result.report_summary_path}"
        )
        return 0

    if args.command == "parse-10k":
        from text_factor_lab.parsing import parse_sec_10k_sections, write_section_artifacts
        from text_factor_lab.schemas import DocumentManifestRecord

        manifest_payload = json.loads(Path(args.manifest_record).read_text(encoding="utf-8"))
        manifest_record = DocumentManifestRecord.model_validate(manifest_payload)
        raw_document = Path(args.document).read_bytes()
        result = parse_sec_10k_sections(raw_document, manifest_record)
        records = write_section_artifacts(result, args.output_dir)
        parsed_count = sum(record.parser_status == "parsed" for record in records)
        failed_count = len(records) - parsed_count
        print(
            "Parsed SEC 10-K sections. "
            f"document_id={manifest_record.document_id} parsed={parsed_count} "
            f"failed_or_missing={failed_count} output_dir={args.output_dir}"
        )
        return 0

    if args.command == "build-labels":
        from text_factor_lab.data import load_price_panel_csv
        from text_factor_lab.labels import (
            build_labels_for_documents,
            read_document_manifest_jsonl,
            write_label_artifacts,
        )

        documents = read_document_manifest_jsonl(args.document_manifest)
        price_panel = load_price_panel_csv(args.prices, price_field=args.price_field)
        result = build_labels_for_documents(
            documents=documents,
            price_panel=price_panel,
            target_names=args.target,
            benchmark_ticker=args.benchmark,
            return_type=args.return_type,
            adjustment_method=args.price_field,
            annualization_days=args.annualization_days,
        )
        write_label_artifacts(
            result,
            labels_path=args.labels_output,
            failures_path=args.failures_output,
        )
        print(
            "Built labels. "
            f"documents={len(documents)} labels={len(result.labels)} "
            f"failures={len(result.failures)} labels_output={args.labels_output}"
        )
        return 0

    if args.command == "build-splits":
        from datetime import date

        from text_factor_lab.splits import (
            build_rolling_year_splits,
            read_labels_jsonl,
            write_split_artifacts,
        )

        labels = read_labels_jsonl(args.labels)
        result = build_rolling_year_splits(
            labels=labels,
            sample_start=date.fromisoformat(args.sample_start),
            sample_end=date.fromisoformat(args.sample_end),
            train_years_min=args.train_years_min,
            validation_years=args.validation_years,
            test_years=args.test_years,
            embargo_days=args.embargo_days,
        )
        write_split_artifacts(
            result,
            assignments_path=args.assignments_output,
            leakage_path=args.leakage_output,
        )
        print(
            "Built rolling splits. "
            f"labels={len(labels)} windows={len(result.windows)} "
            f"assignments={len(result.assignments)} "
            f"leakage_records={len(result.leakage_records)}"
        )
        return 0

    if args.command == "build-features":
        from text_factor_lab.data import load_universe_manifest
        from text_factor_lab.features import (
            build_dictionary_feature_manifests,
            build_dictionary_tone_features,
            build_feature_input_hashes,
            build_metadata_features,
            build_tfidf_features,
            build_tfidf_matrix_store,
            load_document_texts,
            read_document_manifest_jsonl,
            read_parsed_sections_jsonl,
            read_split_assignments_jsonl,
            write_feature_manifest_json,
            write_feature_matrix_index_json,
            write_features_jsonl,
            write_vocabulary_json,
        )

        manifest_by_document_id = read_document_manifest_jsonl(args.document_manifest)
        parsed_sections = read_parsed_sections_jsonl(args.parsed_sections)
        split_assignments = read_split_assignments_jsonl(args.split_assignments)
        document_texts = load_document_texts(
            manifest_by_document_id=manifest_by_document_id,
            parsed_sections=parsed_sections,
        )
        input_hashes = build_feature_input_hashes(
            document_manifest_path=args.document_manifest,
            parsed_sections_path=args.parsed_sections,
            split_assignments_path=args.split_assignments,
        )
        features = []
        feature_manifests = []
        vocabulary_by_split = {}
        if "dictionary_tone" in args.method:
            features.extend(build_dictionary_tone_features(document_texts))
            feature_manifests.extend(
                build_dictionary_feature_manifests(
                    document_texts,
                    split_assignments,
                    input_hashes=input_hashes,
                )
            )
        if args.universe_manifest:
            universe_records = load_universe_manifest(args.universe_manifest)
            features.extend(
                build_metadata_features(
                    manifest_by_document_id=manifest_by_document_id,
                    universe_records=universe_records,
                )
            )
        if "tfidf" in args.method and not args.no_tfidf_long_features:
            tfidf_result = build_tfidf_features(
                document_texts,
                split_assignments,
                max_features=args.tfidf_max_features,
                ngram_range=(args.tfidf_ngram_min, args.tfidf_ngram_max),
                min_df=args.tfidf_min_df,
                max_df=args.tfidf_max_df,
                input_hashes=input_hashes,
            )
            features.extend(tfidf_result.features)
            feature_manifests.extend(tfidf_result.feature_manifests)
            vocabulary_by_split = tfidf_result.vocabulary_by_split
        if (
            "tfidf" in args.method
            and (
                args.feature_matrix_dir
                or args.tfidf_svd_components > 0
                or args.no_tfidf_long_features
            )
        ):
            matrix_dir = Path(args.feature_matrix_dir) if args.feature_matrix_dir else (
                Path(args.features_output).with_name("feature_matrices")
            )
            matrix_result = build_tfidf_matrix_store(
                document_texts,
                split_assignments,
                output_dir=matrix_dir,
                max_features=args.tfidf_max_features,
                ngram_range=(args.tfidf_ngram_min, args.tfidf_ngram_max),
                min_df=args.tfidf_min_df,
                max_df=args.tfidf_max_df,
                svd_components=args.tfidf_svd_components,
                input_hashes=input_hashes,
            )
            features.extend(matrix_result.svd_features)
            feature_manifests.extend(matrix_result.svd_manifests)
            matrix_index_output = (
                Path(args.feature_matrix_index_output)
                if args.feature_matrix_index_output
                else Path(args.features_output).with_name("feature_matrix_index.json")
            )
            write_feature_matrix_index_json(matrix_result.index_records, matrix_index_output)
        manifest_output = (
            Path(args.feature_manifest_output)
            if args.feature_manifest_output
            else Path(args.features_output).with_name("feature_manifest.json")
        )
        write_features_jsonl(features, args.features_output)
        write_vocabulary_json(vocabulary_by_split, args.vocabulary_output)
        write_feature_manifest_json(feature_manifests, manifest_output)
        print(
            "Built text features. "
            f"documents={len(document_texts)} features={len(features)} "
            f"vocabularies={len(vocabulary_by_split)} "
            f"feature_manifest={manifest_output}"
        )
        return 0

    if args.command == "build-models":
        from text_factor_lab.models import (
            build_model_artifacts,
            iter_features_jsonl,
            read_labels_jsonl,
            read_split_assignments_jsonl,
            write_model_manifest_json,
            write_model_prediction_failures_jsonl,
            write_predictions_jsonl,
            write_tuning_log_json,
        )

        result = build_model_artifacts(
            run_id=args.run_id,
            labels=read_labels_jsonl(args.labels),
            features=iter_features_jsonl(args.features),
            split_assignments=read_split_assignments_jsonl(args.split_assignments),
            models=args.model or ["historical_mean", "ridge"],
            random_seed=args.random_seed,
            ridge_alpha_grid=args.ridge_alpha,
        )
        write_predictions_jsonl(result.predictions, args.predictions_output)
        prediction_failures_output = (
            Path(args.prediction_failures_output)
            if args.prediction_failures_output
            else Path(args.predictions_output).with_name("model_prediction_failures.jsonl")
        )
        write_model_prediction_failures_jsonl(
            result.prediction_failures,
            prediction_failures_output,
        )
        write_model_manifest_json(result.model_manifests, args.model_manifest_output)
        write_tuning_log_json(result.tuning_logs, args.tuning_log_output)
        print(
            "Built model artifacts. "
            f"predictions={len(result.predictions)} "
            f"prediction_failures={len(result.prediction_failures)} "
            f"models={len(result.model_manifests)} "
            f"tuning_logs={len(result.tuning_logs)}"
        )
        return 0

    if args.command == "evaluate-models":
        from text_factor_lab.backtest import (
            build_evaluation_artifacts,
            read_labels_jsonl,
            read_predictions_jsonl,
            write_backtest_results_json,
            write_delisting_application_report_json,
            write_evaluation_metrics_json,
            write_factor_panel_jsonl,
            write_portfolio_metrics_json,
            write_portfolio_returns_jsonl,
            write_portfolio_weights_jsonl,
        )
        from text_factor_lab.data import load_price_panel_csv

        price_panel = (
            load_price_panel_csv(args.prices)
            if args.prices is not None
            else None
        )

        result = build_evaluation_artifacts(
            run_id=args.run_id,
            predictions=read_predictions_jsonl(args.predictions),
            labels=read_labels_jsonl(args.labels),
            price_panel=price_panel,
            portfolio_return_type=args.portfolio_return_type,
            transaction_cost_bps_one_way=args.transaction_cost_bps_one_way,
            newey_west_lag=args.newey_west_lag,
            portfolio_signal_direction=args.portfolio_signal_direction,
            target_aware_portfolio_policy=args.target_aware_portfolio_policy,
        )
        write_evaluation_metrics_json(result.metrics, args.metrics_output)
        write_backtest_results_json(result.backtests, args.backtest_output)
        if args.portfolio_weights_output:
            write_portfolio_weights_jsonl(result.portfolio_weights, args.portfolio_weights_output)
        if args.portfolio_returns_output:
            write_portfolio_returns_jsonl(result.portfolio_returns, args.portfolio_returns_output)
        if args.portfolio_metrics_output:
            write_portfolio_metrics_json(result.portfolio_metrics, args.portfolio_metrics_output)
        if args.factor_panel_output:
            write_factor_panel_jsonl(result.factor_panel, args.factor_panel_output)
        if args.monthly_portfolio_weights_output:
            write_portfolio_weights_jsonl(
                result.monthly_portfolio_weights,
                args.monthly_portfolio_weights_output,
            )
        if args.monthly_portfolio_returns_output:
            write_portfolio_returns_jsonl(
                result.monthly_portfolio_returns,
                args.monthly_portfolio_returns_output,
            )
        if args.monthly_portfolio_metrics_output:
            write_portfolio_metrics_json(
                result.monthly_portfolio_metrics,
                args.monthly_portfolio_metrics_output,
            )
        if args.delisting_application_report_output:
            write_delisting_application_report_json(
                result.delisting_application_report,
                args.delisting_application_report_output,
            )
        if (
            args.tested_specifications_output
            or args.multiple_testing_output
            or args.specification_registry_output
        ):
            from text_factor_lab.inference import (
                build_inference_artifacts,
                write_multiple_testing_report_json,
                write_specification_registry_json,
                write_tested_specifications_jsonl,
            )

            inference_result = build_inference_artifacts(
                run_id=args.run_id,
                metrics=result.metrics,
                backtests=result.backtests,
                portfolio_metrics=result.portfolio_metrics + result.monthly_portfolio_metrics,
            )
            if args.tested_specifications_output:
                write_tested_specifications_jsonl(
                    inference_result.tested_specifications,
                    args.tested_specifications_output,
                )
            if args.multiple_testing_output:
                write_multiple_testing_report_json(
                    inference_result.multiple_testing_report,
                    args.multiple_testing_output,
                )
            if args.specification_registry_output:
                write_specification_registry_json(
                    inference_result.specification_registry,
                    args.specification_registry_output,
                )
        print(
            "Built evaluation artifacts. "
            f"metrics={len(result.metrics)} backtests={len(result.backtests)} "
            f"portfolio_returns={len(result.portfolio_returns)} "
            f"monthly_portfolio_returns={len(result.monthly_portfolio_returns)}"
        )
        return 0

    raise NotImplementedError(f"Command '{args.command}' is scaffolded but not implemented yet.")
