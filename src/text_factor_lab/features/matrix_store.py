from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

from text_factor_lab.features.text import (
    DocumentText,
    _assignments_by_split_and_role,
    _count_docs_for_scope,
    _feature_record,
    _text_for_scope,
    _text_scopes_for_documents,
    make_streaming_tfidf_analyzer,
)
from text_factor_lab.schemas.features import FeatureManifestRecord, FeatureRecord
from text_factor_lab.schemas.splits import SplitAssignmentRecord

MATRIX_STORE_VERSION = "tfidf-matrix-store-v0"
SVD_FEATURE_VERSION = "tfidf-svd-v0"


@dataclass(frozen=True)
class FeatureMatrixIndexRecord:
    split_id: str
    text_scope: str
    role: str
    matrix_path: str
    document_ids: list[str]
    feature_names_path: str
    vocabulary_size: int
    row_count: int
    nonzero_count: int


@dataclass(frozen=True)
class FeatureMatrixStoreResult:
    index_records: list[FeatureMatrixIndexRecord]
    svd_features: list[FeatureRecord]
    svd_manifests: list[FeatureManifestRecord]


def build_tfidf_matrix_store(
    document_texts: dict[str, DocumentText],
    split_assignments: list[SplitAssignmentRecord],
    *,
    output_dir: str | Path,
    max_features: int = 50_000,
    ngram_range: tuple[int, int] = (1, 2),
    min_df: int | float = 1,
    max_df: int | float = 1.0,
    svd_components: int = 0,
    input_hashes: dict[str, str] | None = None,
) -> FeatureMatrixStoreResult:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    index_records: list[FeatureMatrixIndexRecord] = []
    svd_features: list[FeatureRecord] = []
    svd_manifests: list[FeatureManifestRecord] = []
    assignments_by_split = _assignments_by_split_and_role(split_assignments)
    created_at = datetime.now(UTC)

    for split_id, role_map in assignments_by_split.items():
        train_doc_ids = sorted(role_map.get("train", set()))
        if not train_doc_ids:
            continue
        text_scopes = _text_scopes_for_documents(document_texts, set(train_doc_ids))
        for text_scope in text_scopes:
            train_texts = [
                _text_for_scope(document_texts[document_id], text_scope)
                for document_id in train_doc_ids
                if document_id in document_texts
            ]
            if not any(text.strip() for text in train_texts):
                continue
            vectorizer = TfidfVectorizer(
                analyzer=make_streaming_tfidf_analyzer(ngram_range),
                lowercase=False,
                max_features=max_features,
                min_df=min_df,
                max_df=max_df,
                sublinear_tf=True,
            )
            vectorizer.fit(train_texts)
            terms = list(vectorizer.get_feature_names_out())
            split_scope_dir = output / _safe_name(split_id) / _safe_name(text_scope)
            split_scope_dir.mkdir(parents=True, exist_ok=True)
            feature_names_path = split_scope_dir / "feature_names.json"
            feature_names_path.write_text(
                json.dumps(terms, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            matrices_by_role: dict[str, Any] = {}
            doc_ids_by_role: dict[str, list[str]] = {}
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
                matrix_path = split_scope_dir / f"{role}.npz"
                sparse.save_npz(matrix_path, matrix)
                doc_ids_path = split_scope_dir / f"{role}_document_ids.json"
                doc_ids_path.write_text(
                    json.dumps(doc_ids, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                matrices_by_role[role] = matrix
                doc_ids_by_role[role] = doc_ids
                index_records.append(
                    FeatureMatrixIndexRecord(
                        split_id=split_id,
                        text_scope=text_scope,
                        role=role,
                        matrix_path=str(matrix_path),
                        document_ids=doc_ids,
                        feature_names_path=str(feature_names_path),
                        vocabulary_size=len(terms),
                        row_count=int(matrix.shape[0]),
                        nonzero_count=int(matrix.nnz),
                    )
                )

            if svd_components > 0 and "train" in matrices_by_role:
                train_matrix = matrices_by_role["train"]
                component_count = _effective_svd_components(
                    requested=svd_components,
                    row_count=train_matrix.shape[0],
                    column_count=train_matrix.shape[1],
                )
                if component_count <= 0:
                    continue
                svd = TruncatedSVD(n_components=component_count, random_state=0)
                svd.fit(train_matrix)
                params = {
                    "source_feature_method": "tfidf",
                    "matrix_store_version": MATRIX_STORE_VERSION,
                    "svd_components_requested": svd_components,
                    "svd_components_effective": component_count,
                    "max_features": max_features,
                    "ngram_range": list(ngram_range),
                    "min_df": min_df,
                    "max_df": max_df,
                    "sublinear_tf": True,
                    "token_pattern": r"(?u)\b[a-zA-Z][a-zA-Z\-']+\b",
                    "explained_variance_ratio_sum": float(svd.explained_variance_ratio_.sum()),
                }
                svd_manifests.append(
                    FeatureManifestRecord(
                        feature_version=f"{SVD_FEATURE_VERSION}:{split_id}:{text_scope}",
                        feature_method="tfidf_svd",
                        dictionary_source=None,
                        dictionary_version=None,
                        dictionary_license_note=None,
                        dictionary_term_count=None,
                        tfidf_params=params,
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
                        vocabulary_size=component_count,
                        created_at_utc=created_at,
                        input_hashes=input_hashes or {},
                    )
                )
                for role, matrix in matrices_by_role.items():
                    transformed = svd.transform(matrix)
                    for row_index, document_id in enumerate(doc_ids_by_role[role]):
                        document = document_texts[document_id]
                        for component_index, value in enumerate(transformed[row_index]):
                            svd_features.append(
                                _feature_record(
                                    document=document,
                                    feature_family="tfidf_svd",
                                    feature_name=(
                                        f"tfidf_svd_{text_scope}__component_"
                                        f"{component_index:03d}"
                                    ),
                                    feature_value=float(value),
                                    feature_version=(
                                        f"{SVD_FEATURE_VERSION}:{split_id}:{text_scope}:{role}"
                                    ),
                                    source_chunk_id=f"{document.document_id}:{text_scope}",
                                )
                            )

    return FeatureMatrixStoreResult(
        index_records=index_records,
        svd_features=svd_features,
        svd_manifests=svd_manifests,
    )


def _effective_svd_components(*, requested: int, row_count: int, column_count: int) -> int:
    upper_bound = min(row_count - 1, column_count - 1)
    return max(0, min(requested, upper_bound))


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "artifact"


def write_feature_matrix_index_json(
    records: list[FeatureMatrixIndexRecord],
    path: str | Path,
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "split_id": record.split_id,
            "text_scope": record.text_scope,
            "role": record.role,
            "matrix_path": record.matrix_path,
            "document_ids": record.document_ids,
            "feature_names_path": record.feature_names_path,
            "vocabulary_size": record.vocabulary_size,
            "row_count": record.row_count,
            "nonzero_count": record.nonzero_count,
        }
        for record in records
    ]
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
