"""SEC filing parsing utilities."""

from text_factor_lab.parsing.sec_10k_sections import (
    SEC_10K_SECTION_PARSER_VERSION,
    SectionExtractionResult,
    find_item_heading_candidates,
    normalize_sec_document_text,
    parse_sec_10k_sections,
    raw_document_diagnostics,
    read_parsed_sections_jsonl,
    should_parse_sec_filing,
    write_section_artifacts,
)

__all__ = [
    "SEC_10K_SECTION_PARSER_VERSION",
    "SectionExtractionResult",
    "find_item_heading_candidates",
    "normalize_sec_document_text",
    "parse_sec_10k_sections",
    "read_parsed_sections_jsonl",
    "raw_document_diagnostics",
    "should_parse_sec_filing",
    "write_section_artifacts",
]
