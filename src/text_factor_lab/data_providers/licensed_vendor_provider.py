from __future__ import annotations

from text_factor_lab.data_providers.crsp_provider import CRSPWRDSProvider


class LicensedVendorProvider(CRSPWRDSProvider):
    provider_name = "licensed_vendor"
