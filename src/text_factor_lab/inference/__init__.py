"""Statistical inference and multiple-testing adjustment artifacts."""

from text_factor_lab.inference.bootstrap import (
    build_primary_rank_ic_bootstrap_report,
    write_primary_rank_ic_bootstrap_report_json,
)
from text_factor_lab.inference.multiple_testing import (
    InferenceBuildResult,
    build_inference_artifacts,
    write_multiple_testing_report_json,
    write_specification_registry_json,
    write_tested_specifications_jsonl,
)

__all__ = [
    "InferenceBuildResult",
    "build_primary_rank_ic_bootstrap_report",
    "build_inference_artifacts",
    "write_multiple_testing_report_json",
    "write_primary_rank_ic_bootstrap_report_json",
    "write_specification_registry_json",
    "write_tested_specifications_jsonl",
]
