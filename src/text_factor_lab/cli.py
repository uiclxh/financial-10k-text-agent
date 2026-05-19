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

    raise NotImplementedError(f"Command '{args.command}' is scaffolded but not implemented yet.")
