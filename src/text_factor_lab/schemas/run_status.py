from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from text_factor_lab.schemas.base import StrictBaseModel, is_timezone_aware

RunType = Literal["exploratory_run", "formal_run"]
RunStatus = Literal[
    "created",
    "data_ready",
    "parsed",
    "features_ready",
    "labels_ready",
    "trained",
    "evaluated",
    "audited",
    "reported",
    "failed",
    "rejected",
]
AuditStatus = Literal["pass", "warn", "fail", "not_run"]


class RunStatusRecord(StrictBaseModel):
    run_id: str = Field(min_length=1)
    run_type: RunType
    status: RunStatus
    created_at_utc: datetime
    updated_at_utc: datetime
    config_path: str = Field(min_length=1)
    failure_reason: str | None = None
    audit_status: AuditStatus
    coverage: float = Field(ge=0, le=1)
    git_commit_sha: str | None = None
    package_version: str | None = None
    dirty_worktree_flag: bool | None = None

    @field_validator("created_at_utc", "updated_at_utc")
    @classmethod
    def validate_aware_datetime(cls, value: datetime) -> datetime:
        if not is_timezone_aware(value):
            raise ValueError("datetime fields must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_update_order(self) -> RunStatusRecord:
        if self.updated_at_utc < self.created_at_utc:
            raise ValueError("updated_at_utc must be after or equal to created_at_utc")
        return self
