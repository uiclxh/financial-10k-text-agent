from __future__ import annotations

from pydantic import Field

from text_factor_lab.schemas.base import StrictBaseModel


class ModelManifestRecord(StrictBaseModel):
    model_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    model_family: str = Field(min_length=1)
    model_level: int = Field(ge=0)
    model_version: str = Field(min_length=1)
    hyperparameters: dict
    random_seed: int
    training_window: str = Field(min_length=1)
    validation_window: str = Field(min_length=1)
    test_window: str = Field(min_length=1)
    feature_version: str = Field(min_length=1)
    label_version: str = Field(min_length=1)
    code_commit: str | None = None
