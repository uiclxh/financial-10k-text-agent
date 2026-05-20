from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

from text_factor_lab.schemas.document_manifest import DocumentManifestRecord
from text_factor_lab.schemas.features import FeatureRecord
from text_factor_lab.schemas.parsed_sections import ParsedSectionRecord
from text_factor_lab.schemas.splits import SplitAssignmentRecord, SplitRole

DICTIONARY_FEATURE_VERSION = "dictionary-tone-v0"
TFIDF_FEATURE_VERSION = "tfidf-v0"
TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z\-']*")
DEFAULT_FINANCIAL_DICTIONARIES: dict[str, set[str]] = {
    "negative": {
        "adverse",
        "decline",
        "declined",
        "decrease",
        "decreased",
        "loss",
        "losses",
        "negative",
        "pressure",
        "weak",
        "weakness",
    },
    "uncertainty": {
        "approximately",
        "contingent",
        "depend",
        "depends",
        "fluctuate",
        "may",
        "might",
        "risk",
        "risks",
        "uncertain",
        "uncertainty",
    },
    "litigation": {
        "claim",
        "claims",
        "court",
        "legal",
        "litigation",
        "proceeding",
        "proceedings",
        "regulatory",
    },
    "liquidity_pressure": {
        "cash",
        "capital",
        "credit",
        "debt",
        "financing",
        "liquidity",
        "obligation",
        "obligations",
    },
}


@dataclass(frozen=True)
class DocumentText:
    document_id: str
    entity_id: str
    ticker: str
    event_time_utc: datetime
    prediction_time_utc: datetime
    section_texts: dict[str, str]

    @property
    def full_text(self) -> str:
        return "\n\n".join(text for _, text in sorted(self.section_texts.items()))


@dataclass(frozen=True)
class FeatureBuildResult:
    features: list[FeatureRecord]
    vocabulary_by_split: dict[str, dict[str, int]]


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]


def read_document_manifest_jsonl(path: str | Path) -> dict[str, DocumentManifestRecord]:
    records: dict[str, DocumentManifestRecord] = {}
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                record = DocumentManifestRecord.model_validate(json.loads(line))
                records[record.document_id] = record
    return records


def read_parsed_sections_jsonl(path: str | Path) -> list[ParsedSectionRecord]:
    records: list[ParsedSectionRecord] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(ParsedSectionRecord.model_validate(json.loads(line)))
    return records


def read_split_assignments_jsonl(path: str | Path) -> list[SplitAssignmentRecord]:
    records: list[SplitAssignmentRecord] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(SplitAssignmentRecord.model_validate(json.loads(line)))
    return records


def load_document_texts(
    *,
    manifest_by_document_id: dict[str, DocumentManifestRecord],
    parsed_sections: list[ParsedSectionRecord],
) -> dict[str, DocumentText]:
    section_texts_by_document: dict[str, dict[str, str]] = defaultdict(dict)
    for section in parsed_sections:
        if section.parser_status != "parsed" or section.artifact_path is None:
            continue
        section_texts_by_document[section.document_id][section.section_key] = Path(
            section.artifact_path
        ).read_text(encoding="utf-8")

    document_texts: dict[str, DocumentText] = {}
    for document_id, section_texts in section_texts_by_document.items():
        manifest = manifest_by_document_id[document_id]
        document_texts[document_id] = DocumentText(
            document_id=document_id,
            entity_id=manifest.entity_id,
            ticker=manifest.ticker,
            event_time_utc=manifest.event_time_utc,
            prediction_time_utc=manifest.event_time_utc,
            section_texts=section_texts,
        )
    return document_texts


def build_dictionary_tone_features(
    document_texts: dict[str, DocumentText],
    *,
    dictionaries: dict[str, set[str]] | None = None,
    feature_version: str = DICTIONARY_FEATURE_VERSION,
) -> list[FeatureRecord]:
    dictionary_terms = dictionaries or DEFAULT_FINANCIAL_DICTIONARIES
    features: list[FeatureRecord] = []
    for document in document_texts.values():
        text_blocks = {"full": document.full_text} | document.section_texts
        for block_name, text in text_blocks.items():
            tokens = tokenize(text)
            token_count = len(tokens)
            counts = Counter(tokens)
            features.append(
                _feature_record(
                    document=document,
                    feature_family="dictionary_tone",
                    feature_name=f"dictionary_{block_name}__word_count",
                    feature_value=float(token_count),
                    feature_version=feature_version,
                    source_chunk_id=f"{document.document_id}:{block_name}",
                )
            )
            for dictionary_name, terms in dictionary_terms.items():
                hit_count = sum(counts[term] for term in terms)
                denominator = token_count if token_count > 0 else 1
                features.append(
                    _feature_record(
                        document=document,
                        feature_family="dictionary_tone",
                        feature_name=f"dictionary_{block_name}__{dictionary_name}_count",
                        feature_value=float(hit_count),
                        feature_version=feature_version,
                        source_chunk_id=f"{document.document_id}:{block_name}",
                    )
                )
                features.append(
                    _feature_record(
                        document=document,
                        feature_family="dictionary_tone",
                        feature_name=f"dictionary_{block_name}__{dictionary_name}_share",
                        feature_value=float(hit_count / denominator),
                        feature_version=feature_version,
                        source_chunk_id=f"{document.document_id}:{block_name}",
                    )
                )
    return features


def build_tfidf_features(
    document_texts: dict[str, DocumentText],
    split_assignments: list[SplitAssignmentRecord],
    *,
    max_features: int = 50_000,
    ngram_range: tuple[int, int] = (1, 2),
    min_df: int | float = 1,
    max_df: int | float = 1.0,
    feature_version: str = TFIDF_FEATURE_VERSION,
) -> FeatureBuildResult:
    features: list[FeatureRecord] = []
    vocabulary_by_split: dict[str, dict[str, int]] = {}
    assignments_by_split = _assignments_by_split_and_role(split_assignments)

    for split_id, role_map in assignments_by_split.items():
        train_doc_ids = sorted(role_map.get("train", set()))
        if not train_doc_ids:
            continue
        train_texts = [document_texts[document_id].full_text for document_id in train_doc_ids]
        vectorizer = TfidfVectorizer(
            lowercase=True,
            max_features=max_features,
            ngram_range=ngram_range,
            min_df=min_df,
            max_df=max_df,
            sublinear_tf=True,
            token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-']+\b",
        )
        vectorizer.fit(train_texts)
        vocabulary_by_split[split_id] = {
            term: int(index) for term, index in sorted(vectorizer.vocabulary_.items())
        }

        for role in ("train", "validation", "test"):
            doc_ids = sorted(role_map.get(role, set()))
            if not doc_ids:
                continue
            matrix = vectorizer.transform(
                [document_texts[document_id].full_text for document_id in doc_ids]
            )
            terms = vectorizer.get_feature_names_out()
            for row_index, document_id in enumerate(doc_ids):
                document = document_texts[document_id]
                row = matrix.getrow(row_index)
                for term_index, value in zip(row.indices, row.data, strict=True):
                    term = terms[term_index]
                    features.append(
                        _feature_record(
                            document=document,
                            feature_family="tfidf",
                            feature_name=f"tfidf_full__{term}",
                            feature_value=float(value),
                            feature_version=f"{feature_version}:{split_id}:{role}",
                            source_chunk_id=f"{document.document_id}:full",
                        )
                    )
    return FeatureBuildResult(features=features, vocabulary_by_split=vocabulary_by_split)


def _assignments_by_split_and_role(
    split_assignments: list[SplitAssignmentRecord],
) -> dict[str, dict[SplitRole, set[str]]]:
    grouped: dict[str, dict[SplitRole, set[str]]] = defaultdict(lambda: defaultdict(set))
    for assignment in split_assignments:
        document_id = document_id_from_label_id(assignment.label_id)
        grouped[assignment.split_id][assignment.role].add(document_id)
    return grouped


def document_id_from_label_id(label_id: str) -> str:
    parts = label_id.rsplit(":", 2)
    if len(parts) != 3:
        raise ValueError(f"Cannot infer document_id from label_id={label_id}")
    return parts[0]


def _feature_record(
    *,
    document: DocumentText,
    feature_family: str,
    feature_name: str,
    feature_value: float | str,
    feature_version: str,
    source_chunk_id: str,
) -> FeatureRecord:
    return FeatureRecord(
        feature_id=f"{document.document_id}:{feature_version}:{feature_name}",
        entity_id=document.entity_id,
        ticker=document.ticker,
        event_time_utc=document.event_time_utc,
        prediction_time_utc=document.prediction_time_utc,
        feature_time_utc=document.event_time_utc,
        feature_family=feature_family,
        feature_name=feature_name,
        feature_value=feature_value,
        feature_version=feature_version,
        source_document_id=document.document_id,
        source_chunk_id=source_chunk_id,
    )


def write_features_jsonl(features: list[FeatureRecord], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        for feature in features:
            file.write(feature.model_dump_json())
            file.write("\n")


def write_vocabulary_json(vocabulary_by_split: dict[str, dict[str, int]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(vocabulary_by_split, file, indent=2, sort_keys=True)
        file.write("\n")
