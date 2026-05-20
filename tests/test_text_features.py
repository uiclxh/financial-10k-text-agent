from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

from text_factor_lab.features import (
    build_dictionary_tone_features,
    build_tfidf_features,
    document_id_from_label_id,
    load_document_texts,
    read_document_manifest_jsonl,
    read_parsed_sections_jsonl,
    read_split_assignments_jsonl,
    tokenize,
    write_features_jsonl,
    write_vocabulary_json,
)
from text_factor_lab.schemas import (
    DocumentManifestRecord,
    ParsedSectionRecord,
    SplitAssignmentRecord,
)


def utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=UTC)


def manifest(document_id: str, ticker: str, year: int) -> DocumentManifestRecord:
    return DocumentManifestRecord(
        document_id=document_id,
        entity_id=f"CIK{ticker}",
        ticker=ticker,
        cik="0000000001",
        company_name=f"{ticker} Inc.",
        document_type="10-K",
        fiscal_year=year,
        fiscal_period="FY",
        source_id="SEC_EDGAR",
        source_url_or_path=f"https://www.sec.gov/{document_id}",
        retrieval_time_utc=utc(year, 3, 1),
        available_time_utc=utc(year, 3, 1),
        event_time_utc=utc(year, 3, 1),
        event_date=date(year, 3, 1),
        timezone="America/New_York",
        hash_sha256="a" * 64,
        license_note="Public SEC EDGAR filing; comply with SEC fair-access policy.",
        parser_version="sec-edgar-data-v0",
    )


def parsed_section(
    *,
    document: DocumentManifestRecord,
    section_key: str,
    artifact_path: Path,
) -> ParsedSectionRecord:
    return ParsedSectionRecord(
        section_id=f"{document.document_id}:{section_key}",
        document_id=document.document_id,
        entity_id=document.entity_id,
        ticker=document.ticker,
        cik=document.cik,
        document_type=document.document_type,
        fiscal_year=document.fiscal_year,
        section_key=section_key,
        section_name="Risk Factors",
        parser_status="parsed",
        char_start=0,
        char_end=100,
        text_length=len(artifact_path.read_text(encoding="utf-8")),
        text_hash_sha256="b" * 64,
        source_hash_sha256=document.hash_sha256,
        artifact_path=str(artifact_path),
        parser_version="sec-10k-section-parser-v0",
        failure_reason=None,
        created_at_utc=utc(document.fiscal_year, 3, 1),
    )


def split_assignment(document: DocumentManifestRecord, role: str) -> SplitAssignmentRecord:
    return SplitAssignmentRecord(
        split_id="train_2010_2014__val_2015_2015__test_2016_2016",
        label_id=f"{document.document_id}:CAR_1_20:labels-v0",
        entity_id=document.entity_id,
        ticker=document.ticker,
        target_name="CAR_1_20",
        role=role,
        event_date=document.event_date,
        label_start_date=date(document.fiscal_year, 3, 2),
        label_end_date=date(document.fiscal_year, 3, 31),
        train_start_date=date(2010, 1, 1),
        train_end_date=date(2014, 12, 31),
        validation_start_date=date(2015, 1, 1),
        validation_end_date=date(2015, 12, 31),
        test_start_date=date(2016, 1, 1),
        test_end_date=date(2016, 12, 31),
        embargo_days=20,
        split_version="rolling-year-split-v0",
    )


def build_text_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    train_doc = manifest("sec:train:doc", "AAPL", 2014)
    validation_doc = manifest("sec:validation:doc", "MSFT", 2015)
    test_doc = manifest("sec:test:doc", "NVDA", 2016)
    manifest_path = tmp_path / "document_manifest.jsonl"
    parsed_path = tmp_path / "parsed_sections.jsonl"
    split_path = tmp_path / "split_assignments.jsonl"

    section_dir = tmp_path / "sections"
    section_dir.mkdir()
    train_text = section_dir / "train_item_1a.txt"
    validation_text = section_dir / "validation_item_1a.txt"
    test_text = section_dir / "test_item_1a.txt"
    train_text.write_text(
        "Risk uncertainty liquidity pressure litigation legal claim supply chain.",
        encoding="utf-8",
    )
    validation_text.write_text("Risk liquidity demand outlook.", encoding="utf-8")
    test_text.write_text("Risk moonshot exclusive testonly growth.", encoding="utf-8")

    manifests = [train_doc, validation_doc, test_doc]
    parsed_sections = [
        parsed_section(document=train_doc, section_key="item_1a", artifact_path=train_text),
        parsed_section(
            document=validation_doc,
            section_key="item_1a",
            artifact_path=validation_text,
        ),
        parsed_section(document=test_doc, section_key="item_1a", artifact_path=test_text),
    ]
    assignments = [
        split_assignment(train_doc, "train"),
        split_assignment(validation_doc, "validation"),
        split_assignment(test_doc, "test"),
    ]
    manifest_path.write_text(
        "".join(record.model_dump_json() + "\n" for record in manifests),
        encoding="utf-8",
    )
    parsed_path.write_text(
        "".join(record.model_dump_json() + "\n" for record in parsed_sections),
        encoding="utf-8",
    )
    split_path.write_text(
        "".join(record.model_dump_json() + "\n" for record in assignments),
        encoding="utf-8",
    )
    return manifest_path, parsed_path, split_path


def test_tokenize_lowercases_financial_text() -> None:
    assert tokenize("Liquidity, litigation-risk MAY fluctuate.") == [
        "liquidity",
        "litigation-risk",
        "may",
        "fluctuate",
    ]


def test_dictionary_tone_features_include_section_and_full_text(tmp_path: Path) -> None:
    manifest_path, parsed_path, _ = build_text_fixture(tmp_path)
    document_texts = load_document_texts(
        manifest_by_document_id=read_document_manifest_jsonl(manifest_path),
        parsed_sections=read_parsed_sections_jsonl(parsed_path),
    )

    features = build_dictionary_tone_features(document_texts)
    train_features = {
        feature.feature_name: feature.feature_value
        for feature in features
        if feature.source_document_id == "sec:train:doc"
    }

    assert train_features["dictionary_full__word_count"] == 9.0
    assert train_features["dictionary_full__uncertainty_count"] == 2.0
    assert train_features["dictionary_item_1a__litigation_count"] == 3.0


def test_tfidf_vocabulary_is_fit_on_train_documents_only(tmp_path: Path) -> None:
    manifest_path, parsed_path, split_path = build_text_fixture(tmp_path)
    document_texts = load_document_texts(
        manifest_by_document_id=read_document_manifest_jsonl(manifest_path),
        parsed_sections=read_parsed_sections_jsonl(parsed_path),
    )
    split_assignments = read_split_assignments_jsonl(split_path)

    result = build_tfidf_features(
        document_texts,
        split_assignments,
        max_features=100,
        ngram_range=(1, 1),
        min_df=1,
        max_df=1.0,
    )
    vocabulary = result.vocabulary_by_split["train_2010_2014__val_2015_2015__test_2016_2016"]
    feature_names = {feature.feature_name for feature in result.features}

    assert "risk" in vocabulary
    assert "moonshot" not in vocabulary
    assert "tfidf_full__moonshot" not in feature_names
    assert any(":test" in feature.feature_version for feature in result.features)


def test_document_id_from_label_id_strips_target_and_version() -> None:
    assert document_id_from_label_id("sec:0000320193:abc.htm:CAR_1_20:labels-v0") == (
        "sec:0000320193:abc.htm"
    )


def test_write_feature_and_vocabulary_artifacts(tmp_path: Path) -> None:
    manifest_path, parsed_path, split_path = build_text_fixture(tmp_path)
    document_texts = load_document_texts(
        manifest_by_document_id=read_document_manifest_jsonl(manifest_path),
        parsed_sections=read_parsed_sections_jsonl(parsed_path),
    )
    result = build_tfidf_features(
        document_texts,
        read_split_assignments_jsonl(split_path),
        ngram_range=(1, 1),
    )
    features_path = tmp_path / "features.jsonl"
    vocabulary_path = tmp_path / "vocabulary.json"

    write_features_jsonl(result.features, features_path)
    write_vocabulary_json(result.vocabulary_by_split, vocabulary_path)

    assert features_path.read_text(encoding="utf-8").count("\n") > 0
    vocabulary_payload = json.loads(vocabulary_path.read_text(encoding="utf-8"))
    assert "train_2010_2014__val_2015_2015__test_2016_2016" in vocabulary_payload


def test_build_features_cli_writes_dictionary_and_tfidf_outputs(tmp_path: Path, capsys) -> None:
    from text_factor_lab.cli import main

    manifest_path, parsed_path, split_path = build_text_fixture(tmp_path)
    features_path = tmp_path / "features.jsonl"
    vocabulary_path = tmp_path / "vocabulary.json"

    exit_code = main(
        [
            "build-features",
            "--document-manifest",
            str(manifest_path),
            "--parsed-sections",
            str(parsed_path),
            "--split-assignments",
            str(split_path),
            "--features-output",
            str(features_path),
            "--vocabulary-output",
            str(vocabulary_path),
            "--method",
            "dictionary_tone",
            "--method",
            "tfidf",
            "--tfidf-ngram-min",
            "1",
            "--tfidf-ngram-max",
            "1",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "documents=3" in captured.out
    assert features_path.exists()
    assert vocabulary_path.exists()
