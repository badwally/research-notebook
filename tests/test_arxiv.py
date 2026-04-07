"""Tests for arXiv search adapter."""

import pytest
from unittest.mock import patch, MagicMock
from src.search.arxiv import build_query, normalize_paper, search_and_normalize


def _make_entry(
    arxiv_id="2401.12345v1",
    title="Test Paper Title",
    summary="This is a test abstract.",
    authors=None,
    categories=None,
    published="2024-01-15T00:00:00Z",
    journal_ref=None,
    comment=None,
):
    """Create a mock feedparser entry dict."""
    if authors is None:
        authors = [{"name": "Alice Smith"}, {"name": "Bob Jones"}]
    if categories is None:
        categories = ["cs.CV", "cs.AI"]
    return {
        "id": f"http://arxiv.org/abs/{arxiv_id}",
        "title": title,
        "summary": summary,
        "authors": authors,
        "tags": [{"term": cat, "scheme": "http://arxiv.org/schemas/atom"} for cat in categories],
        "arxiv_primary_category": {"term": categories[0]},
        "published": published,
        "arxiv_journal_ref": journal_ref,
        "arxiv_comment": comment,
    }


def test_build_query_simple():
    assert build_query("temporal video") == "all:temporal video"


def test_build_query_with_categories():
    result = build_query("temporal video", categories=["cs.CV", "cs.AI"])
    assert "all:temporal video" in result
    assert "cat:cs.CV" in result
    assert "cat:cs.AI" in result
    assert "AND" in result


def test_normalize_paper_basic():
    entry = _make_entry()
    item = normalize_paper(entry)
    assert item["item_id"] == "arxiv:2401.12345"
    assert item["source_type"] == "arxiv"
    assert item["url"] == "http://arxiv.org/abs/2401.12345v1"
    assert item["title"] == "Test Paper Title"
    assert len(item["authors"]) == 2
    assert item["authors"][0]["name"] == "Alice Smith"
    assert item["content_type"] == "preprint"
    assert item["full_text_available"] is True
    assert item["relevance_score"] == 0
    assert item["included"] is False


def test_normalize_paper_strips_version():
    entry = _make_entry(arxiv_id="2401.12345v3")
    item = normalize_paper(entry)
    assert item["item_id"] == "arxiv:2401.12345"
    assert item["source_metadata"]["arxiv_id"] == "2401.12345"


def test_normalize_paper_journal_article():
    entry = _make_entry(journal_ref="Nature 2024")
    item = normalize_paper(entry)
    assert item["content_type"] == "journal_article"
    assert item["source_metadata"]["journal_ref"] == "Nature 2024"


def test_normalize_paper_cleans_title():
    entry = _make_entry(title="Multi-line\n  Title  Here")
    item = normalize_paper(entry)
    assert item["title"] == "Multi-line Title Here"


def test_normalize_paper_truncates_long_description():
    long_abstract = "a" * 1500
    entry = _make_entry(summary=long_abstract)
    item = normalize_paper(entry)
    assert len(item["description"]) == 1000
    assert item["description"].endswith("...")


def test_normalize_paper_source_metadata():
    entry = _make_entry(comment="8 pages, CVPR 2024")
    item = normalize_paper(entry)
    meta = item["source_metadata"]
    assert meta["arxiv_id"] == "2401.12345"
    assert meta["categories"] == ["cs.CV", "cs.AI"]
    assert meta["primary_category"] == "cs.CV"
    assert meta["pdf_url"] == "http://arxiv.org/pdf/2401.12345v1.pdf"
    assert meta["comment"] == "8 pages, CVPR 2024"


@patch("src.search.arxiv.search_arxiv")
@patch("src.search.arxiv.time.sleep")
def test_search_and_normalize(mock_sleep, mock_search):
    mock_search.return_value = [_make_entry(), _make_entry(arxiv_id="2402.67890v1", title="Second Paper")]
    results = search_and_normalize("temporal video", categories=["cs.CV"])
    assert len(results) == 2
    assert results[0]["item_id"] == "arxiv:2401.12345"
    assert results[1]["item_id"] == "arxiv:2402.67890"
    mock_sleep.assert_called_once_with(3)
