from __future__ import annotations

from dataclasses import dataclass

from text_factor_lab.schemas.config import ExperimentConfig


@dataclass(frozen=True)
class SECEdgarProvider:
    config: ExperimentConfig
    provider_name: str = "sec_edgar"

    @property
    def user_agent(self) -> str | None:
        return self.config.text_source.sec_user_agent
