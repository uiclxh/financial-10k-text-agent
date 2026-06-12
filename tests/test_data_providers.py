from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from text_factor_lab.data_providers import (
    CRSPWRDSProvider,
    FMPAlphaProvider,
    NasdaqSharadarProvider,
    build_market_data_provider,
)
from text_factor_lab.schemas import (
    CRSPDailyReturnRecord,
    CRSPDelistingReturnRecord,
    DataLicenseManifestRecord,
    ExperimentConfig,
)

CONFIG_PATH = Path("configs/text_factor_lab/mvp_v0.yaml")


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.write_text(
        ",".join(header)
        + "\n"
        + "\n".join(",".join(str(value) for value in row) for row in rows)
        + "\n",
        encoding="utf-8",
    )


def base_payload(tmp_path: Path) -> dict:
    payload = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    payload["run"]["run_id"] = "crsp_provider_test"
    payload["run"]["run_type"] = "formal_run"
    payload["run"]["output_dir"] = str(tmp_path / "runs" / "crsp_provider_test")
    payload["data_provider"] = {
        "market_data_provider": "crsp_wrds",
        "filing_provider": "sec_edgar",
        "price_source": "crsp_daily_stock",
        "return_source": "crsp_total_return",
        "delisting_return_source": "crsp_delisting",
        "link_source": "crsp_compustat_ccm",
        "allow_public_yahoo_fallback": False,
        "crsp_daily_returns_file": str(tmp_path / "crsp_daily.csv"),
        "crsp_delisting_returns_file": str(tmp_path / "crsp_delisting.csv"),
        "data_license_manifest_file": str(tmp_path / "license_manifest.json"),
    }
    payload["universe"]["name"] = "crsp_wrds_fixture"
    payload["universe"]["universe_data_level"] = "research_grade"
    payload["universe"]["tickers_file"] = str(tmp_path / "tickers.csv")
    payload["universe"]["security_master_file"] = str(tmp_path / "security_master.csv")
    payload["universe"]["membership_file"] = str(tmp_path / "membership.csv")
    payload["universe"]["entity_link_history_file"] = str(tmp_path / "links.csv")
    return payload


def write_provider_fixtures(tmp_path: Path) -> None:
    write_csv(
        tmp_path / "security_master.csv",
        [
            "entity_id",
            "permno",
            "permco",
            "gvkey",
            "cik",
            "ticker",
            "historical_ticker",
            "company_name",
            "name_start_date",
            "name_end_date",
            "exchange",
            "share_class",
            "security_type",
            "exchcd",
            "shrcd",
            "siccd",
            "sic",
            "naics",
            "gics_sector",
            "gics_industry",
            "source",
            "source_version",
            "available_time_utc",
        ],
        [
            [
                "CIK0000320193",
                "14593",
                "7",
                "001690",
                "320193",
                "AAPL",
                "AAPL",
                "Apple Inc.",
                "1980-12-12",
                "",
                "NASDAQ",
                "common",
                "equity",
                "3",
                "11",
                "3571",
                "3571",
                "334220",
                "Information Technology",
                "Technology Hardware",
                "mock_crsp",
                "v1",
                "2015-12-31T00:00:00Z",
            ],
        ],
    )
    write_csv(
        tmp_path / "membership.csv",
        [
            "universe_id",
            "entity_id",
            "ticker",
            "selection_date",
            "entry_date",
            "exit_date",
            "delisting_date",
            "selection_rank",
            "market_cap_at_selection",
            "price_at_selection",
            "shares_outstanding_at_selection",
            "liquidity_filter_pass",
            "source",
            "source_version",
        ],
        [
            [
                "fixture",
                "CIK0000320193",
                "AAPL",
                "2016-01-01",
                "2016-01-01",
                "2025-12-31",
                "",
                "1",
                "100000000",
                "30",
                "3333333",
                "true",
                "mock_crsp",
                "v1",
            ],
        ],
    )
    write_csv(
        tmp_path / "links.csv",
        [
            "entity_id",
            "cik",
            "ticker",
            "permno",
            "gvkey",
            "link_start_date",
            "link_end_date",
            "link_type",
            "link_confidence",
            "source",
        ],
        [
            [
                "CIK0000320193",
                "320193",
                "AAPL",
                "14593",
                "001690",
                "1980-12-12",
                "",
                "primary",
                "1.0",
                "mock_ccm",
            ],
        ],
    )
    write_csv(
        tmp_path / "crsp_daily.csv",
        [
            "permno",
            "permco",
            "date",
            "ticker",
            "ret",
            "retx",
            "prc",
            "shrout",
            "volume",
            "exchcd",
            "shrcd",
            "siccd",
            "source_version",
        ],
        [
            [
                "14593",
                "7",
                "2020-01-02",
                "AAPL",
                "0.01",
                "0.009",
                "300",
                "1000",
                "10",
                "3",
                "11",
                "3571",
                "v1",
            ]
        ],
    )
    write_csv(
        tmp_path / "crsp_delisting.csv",
        ["permno", "dlstdt", "dlret", "dlstcd", "delisting_reason", "source_version"],
        [["14593", "2025-12-31", "-0.2", "500", "mock delisting", "v1"]],
    )
    (tmp_path / "license_manifest.json").write_text(
        json.dumps(
            DataLicenseManifestRecord(
                data_stack="mock_crsp_fixture",
                market_data_provider="crsp_wrds",
                filing_provider="sec_edgar",
                price_source="crsp_daily_stock",
                return_source="crsp_total_return",
                delisting_return_source="crsp_delisting",
                link_source="crsp_compustat_ccm",
                license_note="Mock fixture; no licensed raw CRSP data.",
                raw_data_committed=False,
                allow_public_yahoo_fallback=False,
                created_at_utc=datetime(2026, 5, 25, tzinfo=UTC),
            ).model_dump(mode="json"),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_crsp_records_validate_optional_fields() -> None:
    daily = CRSPDailyReturnRecord.model_validate(
        {
            "permno": "14593",
            "date": "2020-01-02",
            "ticker": "aapl",
            "ret": "0.01",
            "retx": "",
            "prc": "300",
            "shrout": "1000",
            "source_version": "v1",
        }
    )
    delisting = CRSPDelistingReturnRecord.model_validate(
        {
            "permno": "14593",
            "dlstdt": "2025-12-31",
            "dlret": "-0.2",
            "dlstcd": "500",
            "source_version": "v1",
        }
    )

    assert daily.ticker == "AAPL"
    assert daily.retx is None
    assert delisting.dlret == -0.2


def test_crsp_wrds_provider_loads_mock_fixture_without_wrds_account(tmp_path: Path) -> None:
    write_provider_fixtures(tmp_path)
    config = ExperimentConfig.model_validate(base_payload(tmp_path))
    provider = build_market_data_provider(config)
    bundle = provider.load_bundle()

    assert isinstance(provider, CRSPWRDSProvider)
    assert len(bundle.security_master) == 1
    assert len(bundle.universe_membership) == 1
    assert len(bundle.entity_links) == 1
    assert len(bundle.daily_returns) == 1
    assert len(bundle.delisting_returns) == 1
    assert bundle.license_manifest is not None
    assert bundle.license_manifest.raw_data_committed is False


def test_formal_run_rejects_public_yahoo_fallback(tmp_path: Path) -> None:
    payload = base_payload(tmp_path)
    payload["data_provider"]["market_data_provider"] = "public_yahoo"
    payload["data_provider"]["allow_public_yahoo_fallback"] = True

    with pytest.raises(ValidationError, match="market_data_provider"):
        ExperimentConfig.model_validate(payload)


def test_nasdaq_sharadar_provider_is_licensed_provider_profile(tmp_path: Path) -> None:
    payload = base_payload(tmp_path)
    payload["run"]["run_type"] = "formal_run"
    payload["data_provider"]["market_data_provider"] = "nasdaq_sharadar"
    payload["data_provider"]["price_source"] = "nasdaq_sharadar_sep_adjusted_close"
    payload["data_provider"]["return_source"] = "nasdaq_sharadar_sep_simple_return"
    payload["data_provider"]["delisting_return_source"] = (
        "sharadar_delisted_metadata_no_crsp_dlret"
    )
    payload["data_provider"]["link_source"] = "nasdaq_sharadar_tickers_cik_mapping"
    payload["data_provider"]["sharadar_prices_file"] = str(tmp_path / "sharadar_prices.csv")

    config = ExperimentConfig.model_validate(payload)
    provider = build_market_data_provider(config)

    assert isinstance(provider, NasdaqSharadarProvider)


def test_fmp_alpha_provider_is_applied_grade_provider_profile(tmp_path: Path) -> None:
    payload = base_payload(tmp_path)
    payload["run"]["run_type"] = "exploratory_run"
    payload["data_provider"]["market_data_provider"] = "fmp_alpha"
    payload["data_provider"]["price_source"] = "fmp_historical_eod_adjusted_close"
    payload["data_provider"]["return_source"] = "fmp_closeadj_log_return"
    payload["data_provider"]["delisting_return_source"] = (
        "fmp_alpha_listing_status_no_crsp_dlret"
    )
    payload["data_provider"]["link_source"] = "sec_cik_fmp_symbol_change_manual_fb_meta"
    payload["data_provider"]["allow_public_yahoo_fallback"] = False
    payload["data_provider"]["fmp_prices_file"] = str(tmp_path / "fmp_prices.csv")
    payload["data_provider"]["fmp_marketcap_file"] = str(tmp_path / "marketcap.csv")
    payload["data_provider"]["fmp_profile_file"] = str(tmp_path / "security_master.csv")
    payload["data_provider"]["alpha_listing_status_file"] = str(tmp_path / "listing.csv")

    config = ExperimentConfig.model_validate(payload)
    provider = build_market_data_provider(config)

    assert isinstance(provider, FMPAlphaProvider)
