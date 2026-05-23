"""Statistical inference and multiple-testing adjustment artifacts."""

from text_factor_lab.inference.multiple_testing import (
    InferenceBuildResult,
    build_inference_artifacts,
    write_multiple_testing_report_json,
    write_tested_specifications_jsonl,
)

__all__ = [
    "InferenceBuildResult",
    "build_inference_artifacts",
    "write_multiple_testing_report_json",
    "write_tested_specifications_jsonl",
]
