from __future__ import annotations

import argparse

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

    raise NotImplementedError(f"Command '{args.command}' is scaffolded but not implemented yet.")
