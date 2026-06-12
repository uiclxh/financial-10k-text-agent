from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from text_factor_lab.schemas import (
    CRSPDailyReturnRecord,
    CRSPDelistingReturnRecord,
    DataLicenseManifestRecord,
    EntityLinkHistoryRecord,
    SecurityMasterRecord,
    UniverseMembershipRecord,
)
from text_factor_lab.schemas.base import StrictBaseModel
from text_factor_lab.schemas.config import ExperimentConfig

T = TypeVar("T", bound=StrictBaseModel)


@dataclass(frozen=True)
class MarketDataBundle:
    security_master: list[SecurityMasterRecord]
    universe_membership: list[UniverseMembershipRecord]
    entity_links: list[EntityLinkHistoryRecord]
    daily_returns: list[CRSPDailyReturnRecord]
    delisting_returns: list[CRSPDelistingReturnRecord]
    license_manifest: DataLicenseManifestRecord | None


class MarketDataProvider(ABC):
    provider_name: str

    def __init__(self, config: ExperimentConfig) -> None:
        self.config = config

    @abstractmethod
    def load_security_master(self) -> list[SecurityMasterRecord]:
        raise NotImplementedError

    @abstractmethod
    def load_universe_membership(self) -> list[UniverseMembershipRecord]:
        raise NotImplementedError

    @abstractmethod
    def load_entity_links(self) -> list[EntityLinkHistoryRecord]:
        raise NotImplementedError

    @abstractmethod
    def load_daily_returns(self) -> list[CRSPDailyReturnRecord]:
        raise NotImplementedError

    @abstractmethod
    def load_delisting_returns(self) -> list[CRSPDelistingReturnRecord]:
        raise NotImplementedError

    @abstractmethod
    def load_market_benchmark(self) -> list[CRSPDailyReturnRecord]:
        raise NotImplementedError

    @abstractmethod
    def load_license_manifest(self) -> DataLicenseManifestRecord | None:
        raise NotImplementedError

    def load_bundle(self) -> MarketDataBundle:
        return MarketDataBundle(
            security_master=self.load_security_master(),
            universe_membership=self.load_universe_membership(),
            entity_links=self.load_entity_links(),
            daily_returns=self.load_daily_returns(),
            delisting_returns=self.load_delisting_returns(),
            license_manifest=self.load_license_manifest(),
        )


def load_csv_records(path: str | Path | None, model: type[T]) -> list[T]:
    if path is None:
        return []
    input_path = Path(path)
    if not input_path.exists():
        return []
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        return [model.model_validate(row) for row in csv.DictReader(file)]
