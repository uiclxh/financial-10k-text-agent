from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer

from text_factor_lab.schemas.document_manifest import DocumentManifestRecord
from text_factor_lab.schemas.features import FeatureManifestRecord, FeatureRecord
from text_factor_lab.schemas.parsed_sections import ParsedSectionRecord
from text_factor_lab.schemas.splits import SplitAssignmentRecord, SplitRole
from text_factor_lab.schemas.universe import UniverseRecord

DICTIONARY_FEATURE_VERSION = "dictionary-tone-v0"
TFIDF_FEATURE_VERSION = "tfidf-v0"
LM_DICTIONARY_SOURCE = "Notre Dame SRAF Loughran-McDonald Master Dictionary"
LM_DICTIONARY_VERSION = "LM_1993_2025"
LM_DICTIONARY_LICENSE_NOTE = (
    "Loughran-McDonald Master Dictionary 1993-2025 from Notre Dame SRAF; "
    "free for academic research use. Keep raw dictionary CSV under data_private/."
)
TOY_DICTIONARY_SOURCE = "builtin_mvp_toy_financial_dictionary"
TOY_DICTIONARY_VERSION = "mvp-toy-v0"
TOY_DICTIONARY_LICENSE_NOTE = (
    "Internal MVP toy dictionary for pipeline tests; not a substitute for "
    "Loughran-McDonald in formal research."
)
DEFAULT_LM_DICTIONARY_PATHS = (
    Path("data_private/dictionaries/Loughran-McDonald_MasterDictionary_1993-2025.csv"),
    Path("data_private/dictionaries/lm_dictionary.csv"),
)
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
LM_CATEGORY_COLUMNS = {
    "negative": "Negative",
    "positive": "Positive",
    "uncertainty": "Uncertainty",
    "litigious": "Litigious",
    "strong_modal": "Strong_Modal",
    "weak_modal": "Weak_Modal",
    "constraining": "Constraining",
}
_DICTIONARY_CACHE: tuple[dict[str, set[str]], dict[str, Any]] | None = None


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
    vocabulary_by_split: dict[str, dict[str, dict[str, int]]]
    feature_manifests: list[FeatureManifestRecord]


def load_default_financial_dictionaries() -> tuple[dict[str, set[str]], dict[str, Any]]:
    global _DICTIONARY_CACHE
    if _DICTIONARY_CACHE is not None:
        return _DICTIONARY_CACHE
    for path in DEFAULT_LM_DICTIONARY_PATHS:
        if path.exists() and path.stat().st_size > 1024:
            dictionaries = load_loughran_mcdonald_dictionary(path)
            if any(dictionaries.values()):
                metadata = {
                    "dictionary_source": LM_DICTIONARY_SOURCE,
                    "dictionary_version": LM_DICTIONARY_VERSION,
                    "dictionary_license_note": LM_DICTIONARY_LICENSE_NOTE,
                    "dictionary_term_count": len(set().union(*dictionaries.values())),
                    "dictionary_path": str(path),
                }
                _DICTIONARY_CACHE = dictionaries, metadata
                return _DICTIONARY_CACHE
    dictionaries = DEFAULT_FINANCIAL_DICTIONARIES
    metadata = {
        "dictionary_source": TOY_DICTIONARY_SOURCE,
        "dictionary_version": TOY_DICTIONARY_VERSION,
        "dictionary_license_note": TOY_DICTIONARY_LICENSE_NOTE,
        "dictionary_term_count": len(set().union(*dictionaries.values())),
        "dictionary_path": None,
    }
    _DICTIONARY_CACHE = dictionaries, metadata
    return _DICTIONARY_CACHE


def load_loughran_mcdonald_dictionary(path: str | Path) -> dict[str, set[str]]:
    import csv

    dictionaries: dict[str, set[str]] = {name: set() for name in LM_CATEGORY_COLUMNS}
    with Path(path).open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or "Word" not in reader.fieldnames:
            raise ValueError(f"Not a Loughran-McDonald master dictionary CSV: {path}")
        for row in reader:
            word = str(row.get("Word", "")).strip().lower()
            if not word:
                continue
            for category, column in LM_CATEGORY_COLUMNS.items():
                value = str(row.get(column, "0")).strip()
                if value and value != "0":
                    dictionaries[category].add(word)
    return dictionaries


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
    dictionary_terms = dictionaries or load_default_financial_dictionaries()[0]
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


def build_metadata_features(
    *,
    manifest_by_document_id: dict[str, DocumentManifestRecord],
    universe_records: list[UniverseRecord],
    feature_version: str = "metadata-v0",
) -> list[FeatureRecord]:
    universe_by_entity = {record.entity_id: record for record in universe_records}
    features: list[FeatureRecord] = []
    for document in manifest_by_document_id.values():
        universe = universe_by_entity.get(document.entity_id)
        if universe is None:
            continue
        metadata_values: dict[str, str | float] = {
            "metadata__sector": universe.sector,
            "metadata__industry": universe.industry,
        }
        if universe.market_cap_at_selection is not None:
            metadata_values["metadata__market_cap"] = float(universe.market_cap_at_selection)
        for feature_name, feature_value in metadata_values.items():
            features.append(
                FeatureRecord(
                    feature_id=f"{document.document_id}:{feature_version}:{feature_name}",
                    entity_id=document.entity_id,
                    ticker=document.ticker,
                    event_time_utc=document.event_time_utc,
                    prediction_time_utc=document.event_time_utc,
                    feature_time_utc=document.event_time_utc,
                    feature_family="metadata",
                    feature_name=feature_name,
                    feature_value=feature_value,
                    feature_version=feature_version,
                    source_document_id=document.document_id,
                    source_chunk_id=f"{document.document_id}:metadata",
                )
            )
    return features


def build_dictionary_feature_manifests(
    document_texts: dict[str, DocumentText],
    split_assignments: list[SplitAssignmentRecord],
    *,
    dictionaries: dict[str, set[str]] | None = None,
    feature_version: str = DICTIONARY_FEATURE_VERSION,
    input_hashes: dict[str, str] | None = None,
) -> list[FeatureManifestRecord]:
    if dictionaries is None:
        dictionary_terms, dictionary_metadata = load_default_financial_dictionaries()
    else:
        dictionary_terms = dictionaries
        dictionary_metadata = {
            "dictionary_source": TOY_DICTIONARY_SOURCE,
            "dictionary_version": TOY_DICTIONARY_VERSION,
            "dictionary_license_note": TOY_DICTIONARY_LICENSE_NOTE,
            "dictionary_term_count": len(set().union(*dictionary_terms.values())),
        }
    dictionary_term_count = int(dictionary_metadata["dictionary_term_count"])
    manifests: list[FeatureManifestRecord] = []
    assignments_by_split = _assignments_by_split_and_role(split_assignments)
    created_at = datetime.now(UTC)

    for split_id, role_map in assignments_by_split.items():
        split_doc_ids = set().union(*role_map.values()) if role_map else set()
        text_scopes = _text_scopes_for_documents(document_texts, split_doc_ids)
        for text_scope in text_scopes:
            manifests.append(
                FeatureManifestRecord(
                    feature_version=feature_version,
                    feature_method="dictionary_tone",
                    dictionary_source=dictionary_metadata["dictionary_source"],
                    dictionary_version=dictionary_metadata["dictionary_version"],
                    dictionary_license_note=dictionary_metadata["dictionary_license_note"],
                    dictionary_term_count=dictionary_term_count,
                    tfidf_params=None,
                    fit_scope="no_fit_dictionary_counts",
                    split_id=split_id,
                    text_scope=text_scope,
                    train_doc_count=_count_docs_for_scope(
                        document_texts, role_map.get("train", set()), text_scope
                    ),
                    validation_doc_count=_count_docs_for_scope(
                        document_texts, role_map.get("validation", set()), text_scope
                    ),
                    test_doc_count=_count_docs_for_scope(
                        document_texts, role_map.get("test", set()), text_scope
                    ),
                    vocabulary_size=dictionary_term_count,
                    created_at_utc=created_at,
                    input_hashes=input_hashes or {},
                )
            )
    return manifests


def build_tfidf_features(
    document_texts: dict[str, DocumentText],
    split_assignments: list[SplitAssignmentRecord],
    *,
    max_features: int = 50_000,
    ngram_range: tuple[int, int] = (1, 2),
    min_df: int | float = 1,
    max_df: int | float = 1.0,
    feature_version: str = TFIDF_FEATURE_VERSION,
    input_hashes: dict[str, str] | None = None,
) -> FeatureBuildResult:
    features: list[FeatureRecord] = []
    manifests: list[FeatureManifestRecord] = []
    vocabulary_by_split: dict[str, dict[str, dict[str, int]]] = {}
    assignments_by_split = _assignments_by_split_and_role(split_assignments)
    created_at = datetime.now(UTC)

    for split_id, role_map in assignments_by_split.items():
        train_doc_ids = sorted(role_map.get("train", set()))
        if not train_doc_ids:
            continue
        text_scopes = _text_scopes_for_documents(document_texts, set(train_doc_ids))
        vocabulary_by_split[split_id] = {}

        for text_scope in text_scopes:
            train_texts = [
                _text_for_scope(document_texts[document_id], text_scope)
                for document_id in train_doc_ids
                if document_id in document_texts
            ]
            if not any(text.strip() for text in train_texts):
                continue
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
            vocabulary_by_split[split_id][text_scope] = {
                term: int(index) for term, index in sorted(vectorizer.vocabulary_.items())
            }

            manifests.append(
                FeatureManifestRecord(
                    feature_version=f"{feature_version}:{split_id}:{text_scope}",
                    feature_method="tfidf",
                    dictionary_source=None,
                    dictionary_version=None,
                    dictionary_license_note=None,
                    dictionary_term_count=None,
                    tfidf_params={
                        "max_features": max_features,
                        "ngram_range": list(ngram_range),
                        "min_df": min_df,
                        "max_df": max_df,
                        "sublinear_tf": True,
                        "token_pattern": r"(?u)\b[a-zA-Z][a-zA-Z\-']+\b",
                    },
                    fit_scope="train_window_only",
                    split_id=split_id,
                    text_scope=text_scope,
                    train_doc_count=_count_docs_for_scope(
                        document_texts, train_doc_ids, text_scope
                    ),
                    validation_doc_count=_count_docs_for_scope(
                        document_texts, role_map.get("validation", set()), text_scope
                    ),
                    test_doc_count=_count_docs_for_scope(
                        document_texts, role_map.get("test", set()), text_scope
                    ),
                    vocabulary_size=len(vectorizer.vocabulary_),
                    created_at_utc=created_at,
                    input_hashes=input_hashes or {},
                )
            )

            for role in ("train", "validation", "test"):
                doc_ids = [
                    document_id
                    for document_id in sorted(role_map.get(role, set()))
                    if document_id in document_texts
                ]
                if not doc_ids:
                    continue
                matrix = vectorizer.transform(
                    [
                        _text_for_scope(document_texts[document_id], text_scope)
                        for document_id in doc_ids
                    ]
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
                                feature_name=f"tfidf_{text_scope}__{term}",
                                feature_value=float(value),
                                feature_version=(
                                    f"{feature_version}:{split_id}:{text_scope}:{role}"
                                ),
                                source_chunk_id=f"{document.document_id}:{text_scope}",
                            )
                        )
    return FeatureBuildResult(
        features=features,
        vocabulary_by_split=vocabulary_by_split,
        feature_manifests=manifests,
    )


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


def _text_scopes_for_documents(
    document_texts: dict[str, DocumentText],
    document_ids: set[str],
) -> list[str]:
    section_scopes: set[str] = set()
    for document_id in document_ids:
        document = document_texts.get(document_id)
        if document is not None:
            section_scopes.update(document.section_texts)
    return ["full", *sorted(section_scopes)]


def _text_for_scope(document: DocumentText, text_scope: str) -> str:
    if text_scope == "full":
        return document.full_text
    return document.section_texts.get(text_scope, "")


def _count_docs_for_scope(
    document_texts: dict[str, DocumentText],
    document_ids: set[str] | list[str],
    text_scope: str,
) -> int:
    return sum(
        1
        for document_id in document_ids
        if document_id in document_texts
        and (
            text_scope == "full"
            or bool(document_texts[document_id].section_texts.get(text_scope))
        )
    )


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


def write_vocabulary_json(
    vocabulary_by_split: dict[str, dict[str, dict[str, int]]],
    path: str | Path,
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object]
    if vocabulary_by_split:
        payload = vocabulary_by_split
    else:
        payload = {
            "note": (
                "Full train-window vocabulary is stored in feature matrix "
                "feature_names.json files and summarized in vocabulary_manifest.json. "
                "This run does not write a full long-form vocabulary payload here."
            ),
            "full_vocabulary_committed": False,
            "manifest_path": "vocabulary_manifest.json",
        }
    with output.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, sort_keys=True)
        file.write("\n")


def write_feature_manifest_json(
    manifests: list[FeatureManifestRecord],
    path: str | Path,
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(
            [manifest.model_dump(mode="json") for manifest in manifests],
            file,
            indent=2,
            sort_keys=True,
        )
        file.write("\n")


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_feature_input_hashes(
    *,
    document_manifest_path: str | Path,
    parsed_sections_path: str | Path,
    split_assignments_path: str | Path,
) -> dict[str, str]:
    return {
        "document_manifest": sha256_file(document_manifest_path),
        "parsed_sections": sha256_file(parsed_sections_path),
        "split_assignments": sha256_file(split_assignments_path),
    }
