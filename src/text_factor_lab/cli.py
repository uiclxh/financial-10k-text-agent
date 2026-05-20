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

    audit_parser = subparsers.add_parser("audit", help="Audit a completed run.")
    audit_parser.add_argument("--run-id", required=True, help="Run identifier.")

    report_parser = subparsers.add_parser("report", help="Generate reports for a run.")
    report_parser.add_argument("--run-id", required=True, help="Run identifier.")

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

    model_parser = subparsers.add_parser(
        "build-models",
        help="Train baseline and Ridge models from labels, features, and split assignments.",
    )
    model_parser.add_argument("--run-id", required=True)
    model_parser.add_argument("--labels", required=True)
    model_parser.add_argument("--features", required=True)
    model_parser.add_argument("--split-assignments", required=True)
    model_parser.add_argument("--predictions-output", required=True)
    model_parser.add_argument("--model-manifest-output", required=True)
    model_parser.add_argument("--tuning-log-output", required=True)
    model_parser.add_argument(
        "--model",
        action="append",
        choices=["historical_mean", "ridge"],
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
        print(
            "Run initialized as a run manager workspace with independent CLI stages. "
            "Full Data -> Parsing -> Label -> Split -> Feature -> Model -> Backtest -> "
            "Audit -> Report orchestration is not enabled yet. "
            f"run_id={status.run_id} status={manager.read_status().status} "
            f"run_dir={manager.run_dir}"
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
        from text_factor_lab.features import (
            build_dictionary_feature_manifests,
            build_dictionary_tone_features,
            build_feature_input_hashes,
            build_tfidf_features,
            load_document_texts,
            read_document_manifest_jsonl,
            read_parsed_sections_jsonl,
            read_split_assignments_jsonl,
            write_feature_manifest_json,
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
        if "tfidf" in args.method:
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
            read_features_jsonl,
            read_labels_jsonl,
            read_split_assignments_jsonl,
            write_model_manifest_json,
            write_predictions_jsonl,
            write_tuning_log_json,
        )

        result = build_model_artifacts(
            run_id=args.run_id,
            labels=read_labels_jsonl(args.labels),
            features=read_features_jsonl(args.features),
            split_assignments=read_split_assignments_jsonl(args.split_assignments),
            models=args.model or ["historical_mean", "ridge"],
            random_seed=args.random_seed,
            ridge_alpha_grid=args.ridge_alpha,
        )
        write_predictions_jsonl(result.predictions, args.predictions_output)
        write_model_manifest_json(result.model_manifests, args.model_manifest_output)
        write_tuning_log_json(result.tuning_logs, args.tuning_log_output)
        print(
            "Built model artifacts. "
            f"predictions={len(result.predictions)} "
            f"models={len(result.model_manifests)} "
            f"tuning_logs={len(result.tuning_logs)}"
        )
        return 0

    raise NotImplementedError(f"Command '{args.command}' is scaffolded but not implemented yet.")
