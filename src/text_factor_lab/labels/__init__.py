"""Return, volatility, and event-study label construction."""

from text_factor_lab.labels.builder import (
    LABEL_BUILDER_VERSION,
    LabelBuildResult,
    LabelFailureRecord,
    build_labels_for_document,
    build_labels_for_documents,
    parse_target_name,
    read_document_manifest_jsonl,
    write_label_artifacts,
)

__all__ = [
    "LABEL_BUILDER_VERSION",
    "LabelBuildResult",
    "LabelFailureRecord",
    "build_labels_for_document",
    "build_labels_for_documents",
    "parse_target_name",
    "read_document_manifest_jsonl",
    "write_label_artifacts",
]
