from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal

from text_factor_lab.schemas.document_manifest import DocumentManifestRecord
from text_factor_lab.schemas.parsed_sections import (
    ParsedSectionRecord,
    ParsingQualityReport,
    SectionKey,
)

SEC_10K_SECTION_PARSER_VERSION = "sec-10k-section-parser-v0"
AmendmentPolicy = Literal["exclude", "include"]

TARGET_ITEM_TO_SECTION: dict[str, tuple[SectionKey, str]] = {
    "1": ("item_1", "Business"),
    "1a": ("item_1a", "Risk Factors"),
    "3": ("item_3", "Legal Proceedings"),
    "7": ("item_7", "MD&A"),
}
SECTION_TO_TARGET_ITEM = {value[0]: key for key, value in TARGET_ITEM_TO_SECTION.items()}

ITEM_ORDER: dict[str, int] = {
    "1": 10,
    "1a": 11,
    "1b": 12,
    "1c": 13,
    "2": 20,
    "3": 30,
    "4": 40,
    "5": 50,
    "6": 60,
    "7": 70,
    "7a": 71,
    "8": 80,
    "9": 90,
    "9a": 91,
    "9b": 92,
    "9c": 93,
    "10": 100,
    "11": 110,
    "12": 120,
    "13": 130,
    "14": 140,
    "15": 150,
    "16": 160,
}

BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "caption",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
}
SKIP_TAGS = {"script", "style", "noscript"}
HEADING_PATTERN = re.compile(
    r"^\s*item\s+([0-9]{1,2}[a-z]?)\s*(?:[.\-:\u2013\u2014])?\s*(.*?)\s*$",
    re.IGNORECASE,
)
TOC_TRAILING_PAGE_PATTERN = re.compile(r"(?:\.{2,}|\s{2,})\s*\d+\s*$")


@dataclass(frozen=True)
class HeadingCandidate:
    item: str
    line: str
    char_start: int
    char_end: int
    is_toc_like: bool


@dataclass(frozen=True)
class SectionExtractionResult:
    records: list[ParsedSectionRecord]
    section_text_by_key: dict[SectionKey, str]
    normalized_text: str
    quality_report: ParsingQualityReport


class SecHtmlTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        tag_name = tag.lower()
        if tag_name in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth == 0 and tag_name in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        if tag_name in SKIP_TAGS and self.skip_depth > 0:
            self.skip_depth -= 1
            return
        if self.skip_depth == 0 and tag_name in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth == 0:
            self.parts.append(data)

    def get_text(self) -> str:
        return "".join(self.parts)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def should_parse_sec_filing(
    form_type: str,
    *,
    amendment_policy: AmendmentPolicy = "exclude",
) -> bool:
    normalized = form_type.strip().upper()
    if normalized.endswith("/A") and amendment_policy == "exclude":
        return False
    return normalized in {"10-K", "10-K/A"}


def normalize_sec_document_text(raw_document: str | bytes) -> str:
    if isinstance(raw_document, bytes):
        decoded = raw_document.decode("utf-8", errors="replace")
    else:
        decoded = raw_document

    decoded = decoded.replace("\r\n", "\n").replace("\r", "\n")
    if re.search(r"<\s*(html|body|document|div|p|table|ix:)", decoded, re.IGNORECASE):
        parser = SecHtmlTextExtractor()
        parser.feed(decoded)
        decoded = parser.get_text()

    decoded = unescape(decoded).replace("\xa0", " ")
    normalized_lines: list[str] = []
    previous_blank = False
    for raw_line in decoded.splitlines():
        line = re.sub(r"[ \t\f\v]+", " ", raw_line).strip()
        if not line:
            if not previous_blank and normalized_lines:
                normalized_lines.append("")
            previous_blank = True
            continue
        normalized_lines.append(line)
        previous_blank = False
    return "\n".join(normalized_lines).strip()


def _decode_raw_document(raw_document: str | bytes) -> str:
    if isinstance(raw_document, bytes):
        return raw_document.decode("utf-8", errors="replace")
    return raw_document


def raw_document_diagnostics(raw_document: str | bytes) -> tuple[bool, int]:
    decoded = _decode_raw_document(raw_document)
    inline_xbrl_detected = bool(re.search(r"<\s*ix:|xmlns:ix=", decoded, re.IGNORECASE))
    table_tag_count = len(re.findall(r"<\s*table\b", decoded, flags=re.IGNORECASE))
    return inline_xbrl_detected, table_tag_count


def _line_offsets(text: str) -> list[tuple[int, str]]:
    offsets: list[tuple[int, str]] = []
    position = 0
    for line in text.splitlines():
        offsets.append((position, line))
        position += len(line) + 1
    return offsets


def _normalize_item(raw_item: str) -> str:
    return raw_item.lower().rstrip(".")


def _looks_like_toc_line(line: str) -> bool:
    compact = re.sub(r"\s+", " ", line).strip()
    return bool(TOC_TRAILING_PAGE_PATTERN.search(compact))


def find_item_heading_candidates(normalized_text: str) -> list[HeadingCandidate]:
    candidates: list[HeadingCandidate] = []
    for char_start, line in _line_offsets(normalized_text):
        match = HEADING_PATTERN.match(line)
        if match is None:
            continue
        item = _normalize_item(match.group(1))
        if item not in ITEM_ORDER:
            continue
        candidates.append(
            HeadingCandidate(
                item=item,
                line=line,
                char_start=char_start,
                char_end=char_start + len(line),
                is_toc_like=_looks_like_toc_line(line),
            )
        )
    return candidates


def _next_later_heading_start(
    candidate: HeadingCandidate,
    all_candidates: list[HeadingCandidate],
    text_length: int,
) -> int:
    current_order = ITEM_ORDER[candidate.item]
    for next_candidate in all_candidates:
        if next_candidate.char_start <= candidate.char_start:
            continue
        if ITEM_ORDER[next_candidate.item] > current_order:
            return next_candidate.char_start
    return text_length


def _choose_heading_for_item(
    target_item: str,
    candidates: list[HeadingCandidate],
    text_length: int,
) -> tuple[HeadingCandidate, int] | None:
    item_candidates = [
        candidate
        for candidate in candidates
        if candidate.item == target_item and not candidate.is_toc_like
    ]
    if not item_candidates:
        return None

    scored: list[tuple[int, HeadingCandidate, int]] = []
    for candidate in item_candidates:
        end = _next_later_heading_start(candidate, candidates, text_length)
        scored.append((end - candidate.char_end, candidate, end))
    _, best_candidate, section_end = max(scored, key=lambda item: (item[0], item[1].char_start))
    return best_candidate, section_end


def _record_for_section(
    *,
    manifest_record: DocumentManifestRecord,
    section_key: SectionKey,
    section_name: str,
    parser_status: Literal["parsed", "missing", "failed"],
    char_start: int | None,
    char_end: int | None,
    section_text: str,
    failure_reason: str | None,
    artifact_path: str | None = None,
    parser_version: str = SEC_10K_SECTION_PARSER_VERSION,
) -> ParsedSectionRecord:
    return ParsedSectionRecord(
        section_id=f"{manifest_record.document_id}:{section_key}",
        document_id=manifest_record.document_id,
        entity_id=manifest_record.entity_id,
        ticker=manifest_record.ticker,
        cik=manifest_record.cik,
        document_type=manifest_record.document_type,
        fiscal_year=manifest_record.fiscal_year,
        section_key=section_key,
        section_name=section_name,
        parser_status=parser_status,
        char_start=char_start,
        char_end=char_end,
        text_length=len(section_text),
        text_hash_sha256=sha256_text(section_text) if parser_status == "parsed" else None,
        source_hash_sha256=manifest_record.hash_sha256,
        artifact_path=artifact_path,
        parser_version=parser_version,
        failure_reason=failure_reason,
        created_at_utc=datetime.now(UTC),
    )


def parse_sec_10k_sections(
    raw_document: str | bytes,
    manifest_record: DocumentManifestRecord,
    *,
    target_sections: list[SectionKey] | None = None,
    parser_version: str = SEC_10K_SECTION_PARSER_VERSION,
) -> SectionExtractionResult:
    if not should_parse_sec_filing(manifest_record.document_type):
        raise ValueError(f"Unsupported SEC filing type: {manifest_record.document_type}")

    inline_xbrl_detected, table_tag_count = raw_document_diagnostics(raw_document)
    normalized_text = normalize_sec_document_text(raw_document)
    candidates = find_item_heading_candidates(normalized_text)
    selected_sections = target_sections or ["item_1", "item_1a", "item_3", "item_7"]
    records: list[ParsedSectionRecord] = []
    section_text_by_key: dict[SectionKey, str] = {}

    for section_key in selected_sections:
        target_item = SECTION_TO_TARGET_ITEM[section_key]
        _, section_name = TARGET_ITEM_TO_SECTION[target_item]
        selected = _choose_heading_for_item(target_item, candidates, len(normalized_text))
        if selected is None:
            records.append(
                _record_for_section(
                    manifest_record=manifest_record,
                    section_key=section_key,
                    section_name=section_name,
                    parser_status="missing",
                    char_start=None,
                    char_end=None,
                    section_text="",
                    failure_reason=f"Could not locate Item {target_item.upper()} heading.",
                    parser_version=parser_version,
                )
            )
            continue

        heading, section_end = selected
        section_text = normalized_text[heading.char_end:section_end].strip()
        if not section_text:
            records.append(
                _record_for_section(
                    manifest_record=manifest_record,
                    section_key=section_key,
                    section_name=section_name,
                    parser_status="failed",
                    char_start=None,
                    char_end=None,
                    section_text="",
                    failure_reason=f"Item {target_item.upper()} heading found but body was empty.",
                    parser_version=parser_version,
                )
            )
            continue

        text_start = normalized_text.find(section_text, heading.char_end, section_end)
        text_end = text_start + len(section_text)
        section_text_by_key[section_key] = section_text
        records.append(
            _record_for_section(
                manifest_record=manifest_record,
                section_key=section_key,
                section_name=section_name,
                parser_status="parsed",
                char_start=text_start,
                char_end=text_end,
                section_text=section_text,
                failure_reason=None,
                parser_version=parser_version,
            )
        )

    quality_report = build_parsing_quality_report(
        manifest_record=manifest_record,
        records=records,
        candidates=candidates,
        target_sections=selected_sections,
        inline_xbrl_detected=inline_xbrl_detected,
        table_tag_count=table_tag_count,
        parser_version=parser_version,
    )

    return SectionExtractionResult(
        records=records,
        section_text_by_key=section_text_by_key,
        normalized_text=normalized_text,
        quality_report=quality_report,
    )


def build_parsing_quality_report(
    *,
    manifest_record: DocumentManifestRecord,
    records: list[ParsedSectionRecord],
    candidates: list[HeadingCandidate],
    target_sections: list[SectionKey],
    inline_xbrl_detected: bool,
    table_tag_count: int,
    parser_version: str,
) -> ParsingQualityReport:
    target_items = {SECTION_TO_TARGET_ITEM[section] for section in target_sections}
    body_target_candidates = [
        candidate
        for candidate in candidates
        if candidate.item in target_items and not candidate.is_toc_like
    ]
    duplicate_items = sorted(
        item
        for item in target_items
        if sum(1 for candidate in body_target_candidates if candidate.item == item) > 1
    )
    parsed_count = sum(1 for record in records if record.parser_status == "parsed")
    missing_count = sum(1 for record in records if record.parser_status == "missing")
    failed_count = sum(1 for record in records if record.parser_status == "failed")
    coverage = 0.0 if not target_sections else parsed_count / len(target_sections)
    warnings: list[str] = []
    if duplicate_items:
        warnings.append(
            "Duplicate target Item headings detected; parser chose the longest body span."
        )
    if inline_xbrl_detected:
        warnings.append("Inline XBRL markup detected; section extraction should be spot-checked.")
    if table_tag_count:
        warnings.append("HTML table tags detected; table text order may require manual review.")
    if missing_count or failed_count:
        warnings.append("One or more target sections were missing or failed extraction.")

    return ParsingQualityReport(
        document_id=manifest_record.document_id,
        parser_version=parser_version,
        target_sections_total=len(target_sections),
        parsed_sections=parsed_count,
        missing_sections=missing_count,
        failed_sections=failed_count,
        parsed_coverage=coverage,
        heading_candidates_total=len(candidates),
        duplicate_target_heading_items=duplicate_items,
        inline_xbrl_detected=inline_xbrl_detected,
        table_tag_count=table_tag_count,
        warnings=warnings,
        sample_review_required=bool(warnings),
    )


def _safe_document_dir_name(document_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", document_id)


def write_section_artifacts(
    result: SectionExtractionResult,
    output_dir: str | Path,
) -> list[ParsedSectionRecord]:
    root = Path(output_dir)
    sections_dir = root / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)

    records_with_paths: list[ParsedSectionRecord] = []
    for record in result.records:
        if record.parser_status != "parsed":
            records_with_paths.append(record)
            continue

        document_dir = sections_dir / _safe_document_dir_name(record.document_id)
        document_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = document_dir / f"{record.section_key}.txt"
        artifact_path.write_text(result.section_text_by_key[record.section_key], encoding="utf-8")
        records_with_paths.append(record.model_copy(update={"artifact_path": str(artifact_path)}))

    manifest_path = root / "parsed_sections.jsonl"
    with manifest_path.open("w", encoding="utf-8") as file:
        for record in records_with_paths:
            file.write(record.model_dump_json())
            file.write("\n")

    normalized_path = root / "normalized_document_text.txt"
    normalized_path.write_text(result.normalized_text, encoding="utf-8")
    quality_path = root / "parsing_quality_report.json"
    with quality_path.open("w", encoding="utf-8") as file:
        json.dump(result.quality_report.model_dump(mode="json"), file, indent=2)
        file.write("\n")
    return records_with_paths


def read_parsed_sections_jsonl(path: str | Path) -> list[ParsedSectionRecord]:
    records: list[ParsedSectionRecord] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(ParsedSectionRecord.model_validate(json.loads(line)))
    return records
