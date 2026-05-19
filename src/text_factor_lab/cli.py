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
            "Run initialized. Pipeline stages after initialization will be implemented "
            f"in later steps. run_id={status.run_id} status={status.status} "
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

    raise NotImplementedError(f"Command '{args.command}' is scaffolded but not implemented yet.")
