from text_factor_lab import __version__
from text_factor_lab.cli import build_parser


def test_package_version_is_defined() -> None:
    assert __version__


def test_cli_parser_has_expected_commands() -> None:
    parser = build_parser()
    help_text = parser.format_help()

    assert "run" in help_text
    assert "audit" in help_text
    assert "report" in help_text
    assert "parse-10k" in help_text
    assert "build-labels" in help_text
    assert "build-splits" in help_text


def test_run_command_validates_config(capsys) -> None:
    from text_factor_lab.cli import main

    exit_code = main(["run", "--config", "configs/text_factor_lab/mvp_v0.yaml"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Run initialized" in captured.out
