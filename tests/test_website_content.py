from __future__ import annotations

from pathlib import Path

WEBSITE_DIR = Path("website")
WORKING_PAPER = Path("docs/working_paper/auditing_predictive_information_in_sec_10k_text.pdf")
WORKING_PAPER_SSRN_URL = "https://ssrn.com/abstract=6974978"

OBSOLETE_VALUES = {
    "4,716",
    "0.2606",
    "0.3133",
    "568",
    "50_company_public_fmp_alpha_2016_2025_v1",
}

REQUIRED_VALUES = {
    "50_company_public_fmp_alpha_2016_2025_v4",
    "8,133",
    "0.2395",
    "0.3668",
    "594",
}


def test_website_contains_no_obsolete_release_values() -> None:
    for page in WEBSITE_DIR.glob("*.html"):
        text = page.read_text(encoding="utf-8")
        for value in OBSOLETE_VALUES:
            assert value not in text, f"{page}: obsolete value {value}"


def test_website_contains_current_v4_values() -> None:
    combined = "\n".join(page.read_text(encoding="utf-8") for page in WEBSITE_DIR.glob("*.html"))
    for value in REQUIRED_VALUES:
        assert value in combined, f"missing current v4 value {value}"


def test_chinese_pages_are_utf8_and_translated() -> None:
    for page in WEBSITE_DIR.glob("*.zh-CN.html"):
        text = page.read_text(encoding="utf-8")
        assert "Financial 10-K Text Agent" in text
        assert any(term in text for term in ("???", "???", "?????"))
        assert "?" not in text
        assert "?" not in text


def test_homepages_link_public_working_paper_and_contribution_evidence() -> None:
    assert WORKING_PAPER.is_file()
    assert WORKING_PAPER.stat().st_size > 100_000
    for page in (WEBSITE_DIR / "index.html", WEBSITE_DIR / "index.zh-CN.html"):
        text = page.read_text(encoding="utf-8")
        assert WORKING_PAPER_SSRN_URL in text
        assert "Read Working Paper" in text or "?? Working Paper" in text
        assert "50_company_public_fmp_alpha_v4.yaml" in text
        assert "specification_registry.json" in text
        assert "/tree/main/src/text_factor_lab" in text
        assert "/tree/main/tests" in text
