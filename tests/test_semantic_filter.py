"""Tests for semantic filter — item format support."""

from src.filter.semantic import (
    build_item_filter_prompt,
    apply_item_scores,
    parse_filter_response,
    _source_guidance,
)


def _make_item(item_id="arxiv:2401.12345", source_type="arxiv"):
    return {
        "item_id": item_id,
        "source_type": source_type,
        "url": "http://arxiv.org/abs/2401.12345",
        "title": "Test Paper",
        "authors": [{"name": "Test Author", "affiliation": None}],
        "publish_date": "2024-01-15T00:00:00Z",
        "description": "Test abstract",
        "content_type": "preprint",
        "full_text_available": True,
        "relevance_score": 0,
        "inclusion_rationale": "",
        "included": False,
    }


def _make_policy():
    return {
        "scoring_rubric": {"inclusion_threshold": 3},
        "inclusion_criteria": ["Relevant to temporal video analysis"],
    }


def test_build_item_filter_prompt_contains_policy():
    policy = _make_policy()
    items = [_make_item()]
    prompt = build_item_filter_prompt(policy, items)
    assert "inclusion_threshold" in prompt
    assert "Editorial Policy" in prompt


def test_build_item_filter_prompt_contains_source_preamble():
    policy = _make_policy()
    items = [_make_item("arxiv:001", "arxiv"), _make_item("yt:abc", "youtube")]
    prompt = build_item_filter_prompt(policy, items)
    assert "arxiv" in prompt
    assert "youtube" in prompt
    assert "Source Types in This Batch" in prompt


def test_build_item_filter_prompt_uses_item_id():
    policy = _make_policy()
    items = [_make_item()]
    prompt = build_item_filter_prompt(policy, items)
    assert '"item_id"' in prompt
    assert '"video_id"' not in prompt


def test_source_guidance_known_types():
    assert "channel authority" in _source_guidance("youtube")
    assert "methodology" in _source_guidance("arxiv")
    assert "peer review" in _source_guidance("pubmed")
    assert "citation" in _source_guidance("semantic_scholar")


def test_source_guidance_unknown_type():
    result = _source_guidance("unknown")
    assert "general quality" in result


def test_apply_item_scores():
    items = [
        _make_item("arxiv:001"),
        _make_item("arxiv:002"),
    ]
    scores = [
        {"item_id": "arxiv:001", "relevance_score": 5, "inclusion_rationale": "Excellent", "included": True},
        {"item_id": "arxiv:002", "relevance_score": 2, "inclusion_rationale": "Marginal", "included": False},
    ]
    result = apply_item_scores(items, scores)
    assert len(result) == 2
    assert result[0]["relevance_score"] == 5
    assert result[0]["included"] is True
    assert result[1]["relevance_score"] == 2
    assert result[1]["included"] is False


def test_apply_item_scores_skips_unscored():
    items = [_make_item("arxiv:001"), _make_item("arxiv:002")]
    scores = [{"item_id": "arxiv:001", "relevance_score": 4, "inclusion_rationale": "Good", "included": True}]
    result = apply_item_scores(items, scores)
    assert len(result) == 1
    assert result[0]["item_id"] == "arxiv:001"


def test_parse_filter_response_works_for_items():
    """parse_filter_response is format-agnostic — works with item_id too."""
    response = '[{"item_id": "arxiv:001", "relevance_score": 4, "inclusion_rationale": "Good", "included": true}]'
    result = parse_filter_response(response)
    assert len(result) == 1
    assert result[0]["item_id"] == "arxiv:001"
