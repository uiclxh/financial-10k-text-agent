from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, field_validator, model_validator

from text_factor_lab.schemas.base import StrictBaseModel

RunType = Literal["exploratory_run", "formal_run"]
SplitMethod = Literal["rolling_year"]
DocumentType = Literal["10-K", "10-Q", "earnings_call"]
ReturnType = Literal["log", "simple"]
WeightingMethod = Literal["equal_weight", "value_weight"]
PortfolioMethod = Literal["top_bottom_quintile"]
FitScope = Literal["train_window_only"]
UniverseDataLevel = Literal["exploratory", "applied", "research_grade"]


class RunConfig(StrictBaseModel):
    run_id: str = Field(min_length=1)
    run_type: RunType
    random_seed: int
    output_dir: Path


class InputsConfig(StrictBaseModel):
    document_manifest_path: Path | None = None
    prices_path: Path | None = None
    parsed_sections_path: Path | None = None
    raw_filings_dir: Path | None = None
    copy_inputs_to_run_dir: bool = True


class UniverseConfig(StrictBaseModel):
    name: str = Field(min_length=1)
    selection_date: date
    tickers_file: Path
    security_master_file: Path | None = None
    membership_file: Path | None = None
    entity_link_history_file: Path | None = None
    universe_data_level: UniverseDataLevel = "exploratory"
    survivorship_bias_control: bool
    allow_delisted_firms: bool
    historical_ticker_mapping: bool


class SampleConfig(StrictBaseModel):
    start_date: date
    end_date: date
    timezone: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_date_order(self) -> SampleConfig:
        if self.start_date > self.end_date:
            raise ValueError("sample.start_date must be before or equal to sample.end_date")
        return self


class TextSourceConfig(StrictBaseModel):
    document_type: DocumentType
    source: str = Field(min_length=1)
    sections: list[str] = Field(min_length=1)
    require_available_time: bool
    require_license_note: bool
    sec_user_agent: str | None = None


class LabelsConfig(StrictBaseModel):
    targets: list[str] = Field(min_length=1)
    return_type: ReturnType
    portfolio_return_type: ReturnType
    price_field: str = Field(min_length=1)
    market_benchmark: str = Field(min_length=1)
    annualization_days: int = Field(gt=0)


class SplitConfig(StrictBaseModel):
    method: SplitMethod
    train_years_min: int = Field(gt=0)
    validation_years: int = Field(gt=0)
    test_years: int = Field(gt=0)
    embargo_days: int = Field(ge=0)


class DictionaryToneConfig(StrictBaseModel):
    dictionaries: list[str] = Field(min_length=1)


class TfidfConfig(StrictBaseModel):
    max_features: int = Field(gt=0)
    ngram_range: tuple[int, int]
    min_df: int = Field(gt=0)
    max_df: float = Field(gt=0, le=1)
    fit_scope: FitScope

    @field_validator("ngram_range")
    @classmethod
    def validate_ngram_range(cls, value: tuple[int, int]) -> tuple[int, int]:
        if len(value) != 2:
            raise ValueError("tfidf.ngram_range must contain exactly two integers")
        start, end = value
        if start < 1 or end < start:
            raise ValueError("tfidf.ngram_range must satisfy 1 <= start <= end")
        return value


class FeaturesConfig(StrictBaseModel):
    methods: list[str] = Field(min_length=1)
    dictionary_tone: DictionaryToneConfig | None = None
    tfidf: TfidfConfig | None = None

    @model_validator(mode="after")
    def validate_method_configs(self) -> FeaturesConfig:
        if "dictionary_tone" in self.methods and self.dictionary_tone is None:
            raise ValueError("features.dictionary_tone is required when method is enabled")
        if "tfidf" in self.methods and self.tfidf is None:
            raise ValueError("features.tfidf is required when method is enabled")
        return self


class ModelsTuningConfig(StrictBaseModel):
    selection_metric: str = Field(min_length=1)
    save_tuning_log: bool


class ModelsConfig(StrictBaseModel):
    enabled: list[str] = Field(min_length=1)
    tuning: ModelsTuningConfig


class BacktestConfig(StrictBaseModel):
    rebalance_frequency: str = Field(min_length=1)
    portfolio_method: PortfolioMethod
    weighting: WeightingMethod
    holding_window_days: int = Field(gt=0)
    transaction_cost_bps_one_way: float = Field(ge=0)
    sector_neutral: bool
    newey_west_lag: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_newey_west_lag(self) -> BacktestConfig:
        minimum_lag = self.holding_window_days - 1
        if self.newey_west_lag < minimum_lag:
            raise ValueError(
                "backtest.newey_west_lag must be at least holding_window_days - 1"
            )
        return self


class AuditConfig(StrictBaseModel):
    coverage_threshold: float = Field(ge=0, le=1)
    require_license_note: bool
    require_available_time: bool
    reject_on_lookahead: bool
    reject_on_train_test_leakage: bool


class ExperimentConfig(StrictBaseModel):
    run: RunConfig
    inputs: InputsConfig = Field(default_factory=InputsConfig)
    universe: UniverseConfig
    sample: SampleConfig
    text_source: TextSourceConfig
    labels: LabelsConfig
    split: SplitConfig
    features: FeaturesConfig
    models: ModelsConfig
    backtest: BacktestConfig
    audit: AuditConfig

    @model_validator(mode="after")
    def validate_formal_run_gates(self) -> ExperimentConfig:
        if self.universe.selection_date > self.sample.start_date:
            raise ValueError(
                "universe.selection_date must be before or equal to sample.start_date"
            )

        if self.run.run_type == "formal_run":
            if not self.text_source.require_available_time:
                raise ValueError("formal_run requires text_source.require_available_time=true")
            if not self.text_source.require_license_note:
                raise ValueError("formal_run requires text_source.require_license_note=true")
            if not self.audit.require_available_time:
                raise ValueError("formal_run requires audit.require_available_time=true")
            if not self.audit.require_license_note:
                raise ValueError("formal_run requires audit.require_license_note=true")
            if self.text_source.source == "SEC_EDGAR" and not self.text_source.sec_user_agent:
                raise ValueError("formal_run with SEC_EDGAR requires text_source.sec_user_agent")
        return self


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file)
    return ExperimentConfig.model_validate(payload)

