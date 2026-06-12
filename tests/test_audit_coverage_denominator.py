from __future__ import annotations

from text_factor_lab.audit.coverage import CoverageDiagnostics
from text_factor_lab.audit.engine import _coverage_check


def diagnostics(
    *,
    raw: float,
    eligible: float,
    primary: float,
    missing_split: int = 0,
) -> CoverageDiagnostics:
    return CoverageDiagnostics(
        waterfall={
            "raw_label_coverage": raw,
            "eligible_oos_coverage": eligible,
            "model_expected_prediction_coverage": eligible,
            "portfolio_eligible_coverage": eligible,
            "primary_prediction_coverage": primary,
            "primary_portfolio_coverage": primary,
            "primary_spec_coverage": primary,
            "counts": {
                "eligible_oos_labels": 10,
                "primary_expected_label_pairs": 10,
                "primary_predicted_label_pairs": int(primary * 10),
                "primary_expected_specifications": 10,
                "primary_covered_specifications": int(primary * 10),
                "primary_prediction_expected_specifications": 5,
                "primary_prediction_covered_specifications": int(primary * 5),
                "primary_portfolio_expected_specifications": 5,
                "primary_portfolio_covered_specifications": int(primary * 5),
            },
            "failure_counts": {"missing_split_assignment": missing_split},
        },
        failures=[],
        by_target=[],
        by_split=[],
        by_ticker=[],
        by_model=[],
    )


def test_exploratory_coverage_gate_uses_eligible_oos_not_raw_labels() -> None:
    check = _coverage_check(
        "coverage_gate_test",
        diagnostics(raw=0.50, eligible=1.0, primary=1.0),
        0.80,
        formal=False,
    )

    assert check.status == "pass"
    assert "Raw=0.500" in check.message
    assert "eligible_oos=1.000" in check.message


def test_formal_coverage_gate_fails_missing_primary_spec_coverage() -> None:
    check = _coverage_check(
        "coverage_gate_test",
        diagnostics(raw=1.0, eligible=1.0, primary=0.90),
        0.80,
        formal=True,
    )

    assert check.status == "fail"
    assert "primary_spec=0.900" in check.message
