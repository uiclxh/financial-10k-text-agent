from __future__ import annotations

from pathlib import Path

WEBSITE_DIR = Path("website")

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
        assert any(term in text for term in ("预注册", "样本外", "方法与审计"))
        assert "鐢" not in text
        assert "涓" not in text
