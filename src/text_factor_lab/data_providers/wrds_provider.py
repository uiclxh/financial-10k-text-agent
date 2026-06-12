from __future__ import annotations

from text_factor_lab.data_providers.crsp_provider import CRSPWRDSProvider


class WRDSProvider(CRSPWRDSProvider):
    """Licensed WRDS profile backed by locally exported CRSP/CCM files.

    The class intentionally does not open a WRDS connection. CI and public GitHub
    runs use mock/exported CSV fixtures, while licensed local runs can point the
    config at private CRSP/WRDS exports that are never committed.
    """

    provider_name = "wrds"
