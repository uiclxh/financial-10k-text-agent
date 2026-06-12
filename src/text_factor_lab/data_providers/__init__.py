"""Provider abstractions for public and licensed market data stacks."""

from text_factor_lab.data_providers.base import MarketDataBundle, MarketDataProvider
from text_factor_lab.data_providers.crsp_provider import CRSPWRDSProvider
from text_factor_lab.data_providers.fmp_alpha_provider import FMPAlphaProvider
from text_factor_lab.data_providers.licensed_vendor_provider import LicensedVendorProvider
from text_factor_lab.data_providers.nasdaq_sharadar_provider import NasdaqSharadarProvider
from text_factor_lab.data_providers.public_yahoo_provider import PublicYahooProvider
from text_factor_lab.data_providers.sec_edgar_provider import SECEdgarProvider
from text_factor_lab.data_providers.wrds_provider import WRDSProvider
from text_factor_lab.schemas.config import ExperimentConfig


def build_market_data_provider(config: ExperimentConfig) -> MarketDataProvider:
    provider_name = config.data_provider.market_data_provider
    if provider_name == "crsp_wrds":
        return CRSPWRDSProvider(config)
    if provider_name == "licensed_vendor":
        return LicensedVendorProvider(config)
    if provider_name == "nasdaq_sharadar":
        return NasdaqSharadarProvider(config)
    if provider_name == "fmp_alpha":
        return FMPAlphaProvider(config)
    return PublicYahooProvider(config)


__all__ = [
    "CRSPWRDSProvider",
    "FMPAlphaProvider",
    "LicensedVendorProvider",
    "MarketDataBundle",
    "MarketDataProvider",
    "NasdaqSharadarProvider",
    "PublicYahooProvider",
    "SECEdgarProvider",
    "WRDSProvider",
    "build_market_data_provider",
]
