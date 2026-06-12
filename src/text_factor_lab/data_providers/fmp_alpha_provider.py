from __future__ import annotations

import json
from pathlib import Path

from text_factor_lab.data import (
    load_entity_link_history,
    load_security_master,
    load_universe_membership,
)
from text_factor_lab.data_providers.base import MarketDataProvider, load_csv_records
from text_factor_lab.schemas import (
    CRSPDailyReturnRecord,
    CRSPDelistingReturnRecord,
    DataLicenseManifestRecord,
    EntityLinkHistoryRecord,
    SecurityMasterRecord,
    UniverseMembershipRecord,
)


class FMPAlphaProvider(MarketDataProvider):
    """Applied-grade FMP primary / Alpha Vantage backup market-data profile.

    This profile is intended for fixed-company pilot studies. It is not a
    CRSP replacement: it does not provide survivorship-free universe membership
    or CRSP delisting returns, so formal reports must keep those boundaries
    explicit.
    """

    provider_name = "fmp_alpha"

    def load_security_master(self) -> list[SecurityMasterRecord]:
        return (
            load_security_master(self.config.universe.security_master_file)
            if self.config.universe.security_master_file is not None
            else []
        )

    def load_universe_membership(self) -> list[UniverseMembershipRecord]:
        return (
            load_universe_membership(self.config.universe.membership_file)
            if self.config.universe.membership_file is not None
            else []
        )

    def load_entity_links(self) -> list[EntityLinkHistoryRecord]:
        return (
            load_entity_link_history(self.config.universe.entity_link_history_file)
            if self.config.universe.entity_link_history_file is not None
            else []
        )

    def load_daily_returns(self) -> list[CRSPDailyReturnRecord]:
        return load_csv_records(
            self.config.data_provider.fmp_prices_file,
            CRSPDailyReturnRecord,
        )

    def load_delisting_returns(self) -> list[CRSPDelistingReturnRecord]:
        return []

    def load_market_benchmark(self) -> list[CRSPDailyReturnRecord]:
        return self.load_daily_returns()

    def load_license_manifest(self) -> DataLicenseManifestRecord | None:
        path = self.config.data_provider.data_license_manifest_file
        if path is None or not Path(path).exists():
            return None
        return DataLicenseManifestRecord.model_validate(
            json.loads(Path(path).read_text(encoding="utf-8"))
        )
