"""Tests for multi-source pipeline orchestrator."""

import os
import pytest
from unittest.mock import patch
from src.pipeline import run_multi_source_search, stage_items


def _make_arxiv_item(item_id="arxiv:2401.12345", included=True):
    return {
        "item_id": item_id,
        "source_type": "arxiv",
        "url": f"http://arxiv.org/abs/{item_id.split(':')[1]}",
        "title": "Test Paper",
        "authors": [{"name": "Test Author", "affiliation": None}],
        "publish_date": "2024-01-15T00:00:00Z",
        "description": "Test abstract",
        "content_type": "preprint",
        "full_text_available": True,
        "relevance_score": 4,
        "inclusion_rationale": "Relevant",
        "included": included,
    }


@patch("src.pipeline.arxiv_search")
def test_run_multi_source_search_arxiv(mock_arxiv):
    mock_arxiv.return_value = [_make_arxiv_item()]

    import tempfile, yaml
    domain = {
        "domain": {"topic": "temporal video analysis", "field": "computer vision"},
        "academic_sources": {"arxiv": {"categories": ["cs.CV"]}}
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(domain, f)
        domain_path = f.name

    try:
        results = run_multi_source_search(["arxiv"], domain_path)
        assert len(results) == 1
        assert results[0]["item_id"] == "arxiv:2401.12345"
        mock_arxiv.assert_called_once_with(
            "temporal video analysis", max_results=50, categories=["cs.CV"]
        )
    finally:
        os.unlink(domain_path)


def test_run_multi_source_search_unsupported():
    with pytest.raises(ValueError, match="Unsupported source types"):
        run_multi_source_search(["unknown_source"], "/dev/null")


@patch("src.pipeline.arxiv_search")
def test_run_multi_source_search_deduplicates(mock_arxiv):
    mock_arxiv.return_value = [
        _make_arxiv_item("arxiv:001"),
        _make_arxiv_item("arxiv:001"),  # duplicate
        _make_arxiv_item("arxiv:002"),
    ]

    import tempfile, yaml
    domain = {"domain": {"topic": "test", "field": "test"}}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(domain, f)
        domain_path = f.name

    try:
        results = run_multi_source_search(["arxiv"], domain_path)
        assert len(results) == 2
    finally:
        os.unlink(domain_path)


def test_stage_items_writes_checkpoint(tmp_path):
    items = [_make_arxiv_item("arxiv:001", True), _make_arxiv_item("arxiv:002", False)]

    path = stage_items(
        items=items,
        research_project="test_project",
        query_terms=["test query"],
        research_criteria_version="0.1.0",
        sources_used=["arxiv"],
        output_dir=str(tmp_path),
        included_only=False,
    )

    assert os.path.exists(path)
    from src.stage.checkpoint import read_checkpoint
    loaded = read_checkpoint(path)
    assert "items" in loaded
    assert len(loaded["items"]) == 2
    assert loaded["metadata"]["sources_used"] == ["arxiv"]


def test_stage_items_included_only(tmp_path):
    items = [_make_arxiv_item("arxiv:001", True), _make_arxiv_item("arxiv:002", False)]

    path = stage_items(
        items=items,
        research_project="test_project",
        query_terms=["test"],
        research_criteria_version="0.1.0",
        sources_used=["arxiv"],
        output_dir=str(tmp_path),
        included_only=True,
    )

    from src.stage.checkpoint import read_checkpoint
    loaded = read_checkpoint(path)
    assert len(loaded["items"]) == 1
    assert loaded["items"][0]["included"] is True
