from __future__ import annotations

from text_factor_lab.data import (
    load_entity_link_history,
    load_security_master,
    load_universe_membership,
)
from text_factor_lab.data_providers.base import MarketDataProvider
from text_factor_lab.schemas import (
    CRSPDailyReturnRecord,
    CRSPDelistingReturnRecord,
    DataLicenseManifestRecord,
    EntityLinkHistoryRecord,
    SecurityMasterRecord,
    UniverseMembershipRecord,
)


class PublicYahooProvider(MarketDataProvider):
    provider_name = "public_yahoo"

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
        return []

    def load_delisting_returns(self) -> list[CRSPDelistingReturnRecord]:
        return []

    def load_market_benchmark(self) -> list[CRSPDailyReturnRecord]:
        return []

    def load_license_manifest(self) -> DataLicenseManifestRecord | None:
        return None
