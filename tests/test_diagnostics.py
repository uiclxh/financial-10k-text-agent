from text_factor_lab.diagnostics import build_parser_manual_review_appendix


def test_parser_manual_review_appendix_lists_excluded_and_included_short_rows() -> None:
    report = {
        "section_count": 2,
        "rows": [
            {
                "document_id": "doc-a",
                "ticker": "AAA",
                "section": "item_1a",
                "char_count": 80,
                "word_count": 12,
                "quality_flag": "manual_check_lt_100_words",
                "excluded_from_section_level_features": True,
            },
            {
                "document_id": "doc-b",
                "ticker": "BBB",
                "section": "item_3",
                "char_count": 120,
                "word_count": 20,
                "quality_flag": "ok",
                "excluded_from_section_level_features": False,
            },
        ],
    }

    appendix = build_parser_manual_review_appendix(report)

    assert "# Parser Manual Review Appendix" in appendix
    assert "AAA | item_1a | 12" in appendix
    assert "BBB | item_3 | 20" in appendix
    assert "Combined/full scope" in appendix
