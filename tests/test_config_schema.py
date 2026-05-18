from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from text_factor_lab.schemas import ExperimentConfig, load_experiment_config


CONFIG_PATH = Path("configs/text_factor_lab/mvp_v0.yaml")


def load_config_payload() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def test_mvp_v0_config_loads() -> None:
    config = load_experiment_config(CONFIG_PATH)

    assert config.run.run_id == "tflab_10k_mvp_v0_001"
    assert config.run.run_type == "formal_run"
    assert config.features.tfidf is not None
    assert config.features.tfidf.fit_scope == "train_window_only"


def test_formal_run_requires_available_time_gate() -> None:
    payload = load_config_payload()
    payload["text_source"]["require_available_time"] = False

    with pytest.raises(ValidationError, match="require_available_time"):
        ExperimentConfig.model_validate(payload)


def test_formal_run_requires_license_gate() -> None:
    payload = load_config_payload()
    payload["audit"]["require_license_note"] = False

    with pytest.raises(ValidationError, match="require_license_note"):
        ExperimentConfig.model_validate(payload)


def test_newey_west_lag_must_cover_holding_window() -> None:
    payload = load_config_payload()
    payload["backtest"]["newey_west_lag"] = 5

    with pytest.raises(ValidationError, match="newey_west_lag"):
        ExperimentConfig.model_validate(payload)


def test_unknown_config_fields_are_rejected() -> None:
    payload = load_config_payload()
    payload["run"]["surprise"] = "not allowed"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ExperimentConfig.model_validate(payload)


def test_config_payload_can_be_copied_without_mutating_fixture() -> None:
    payload = load_config_payload()
    clone = deepcopy(payload)
    clone["run"]["run_id"] = "other"

    assert payload["run"]["run_id"] == "tflab_10k_mvp_v0_001"
