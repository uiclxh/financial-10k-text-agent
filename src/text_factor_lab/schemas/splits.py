from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import Field, model_validator

from text_factor_lab.schemas.base import StrictBaseModel

SplitRole = Literal["train", "validation", "test"]
LeakageSeverity = Literal["purged", "warn", "fail"]


class SplitAssignmentRecord(StrictBaseModel):
    split_id: str = Field(min_length=1)
    label_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    target_name: str = Field(min_length=1)
    role: SplitRole
    event_date: date
    label_start_date: date
    label_end_date: date
    train_start_date: date
    train_end_date: date
    validation_start_date: date
    validation_end_date: date
    test_start_date: date
    test_end_date: date
    embargo_days: int = Field(ge=0)
    split_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_date_order(self) -> SplitAssignmentRecord:
        if self.train_start_date > self.train_end_date:
            raise ValueError("train_start_date must be before or equal to train_end_date")
        if self.validation_start_date > self.validation_end_date:
            raise ValueError(
                "validation_start_date must be before or equal to validation_end_date"
            )
        if self.test_start_date > self.test_end_date:
            raise ValueError("test_start_date must be before or equal to test_end_date")
        if not (
            self.train_end_date < self.validation_start_date
            and self.validation_end_date < self.test_start_date
        ):
            raise ValueError("split windows must be ordered train < validation < test")
        if self.label_start_date > self.label_end_date:
            raise ValueError("label_start_date must be before or equal to label_end_date")
        return self


class SplitLeakageRecord(StrictBaseModel):
    split_id: str = Field(min_length=1)
    label_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    target_name: str = Field(min_length=1)
    role: SplitRole
    severity: LeakageSeverity
    leakage_type: str = Field(min_length=1)
    message: str = Field(min_length=1)
    event_date: date
    label_end_date: date
