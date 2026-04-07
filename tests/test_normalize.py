from src.search.normalize import make_item_id, truncate_description, deduplicate_items, empty_scores
import pytest


def test_make_item_id_youtube():
    assert make_item_id("youtube", "dQw4w9WgXcQ") == "yt:dQw4w9WgXcQ"


def test_make_item_id_arxiv():
    assert make_item_id("arxiv", "2401.12345") == "arxiv:2401.12345"


def test_make_item_id_pubmed():
    assert make_item_id("pubmed", "39876543") == "pmid:39876543"


def test_make_item_id_semantic_scholar():
    assert make_item_id("semantic_scholar", "abc123") == "s2:abc123"


def test_make_item_id_unknown_raises():
    with pytest.raises(ValueError):
        make_item_id("unknown_source", "123")


def test_truncate_description_short():
    assert truncate_description("short text", 500) == "short text"


def test_truncate_description_long():
    text = "a" * 600
    result = truncate_description(text, 500)
    assert len(result) == 500
    assert result.endswith("...")


def test_truncate_description_none():
    assert truncate_description(None) == ""


def test_deduplicate_items_removes_dupes():
    items = [
        {"item_id": "yt:abc", "title": "First"},
        {"item_id": "arxiv:123", "title": "Second"},
        {"item_id": "yt:abc", "title": "Duplicate"},
    ]
    result = deduplicate_items(items)
    assert len(result) == 2
    assert result[0]["title"] == "First"
    assert result[1]["title"] == "Second"


def test_deduplicate_items_preserves_order():
    items = [
        {"item_id": "c", "title": "C"},
        {"item_id": "a", "title": "A"},
        {"item_id": "b", "title": "B"},
    ]
    result = deduplicate_items(items)
    assert [i["title"] for i in result] == ["C", "A", "B"]


def test_empty_scores():
    scores = empty_scores()
    assert scores == {"relevance_score": 0, "inclusion_rationale": "", "included": False}
