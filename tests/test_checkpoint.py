import json
import pytest
from src.stage.schema import validate_checkpoint
from src.stage.checkpoint import write_checkpoint, read_checkpoint


def _make_video(video_id="abc123", score=4, included=True):
    return {
        "video_id": video_id,
        "url": f"https://youtube.com/watch?v={video_id}",
        "title": "Test Video",
        "channel_name": "Test Channel",
        "channel_id": "UC0000",
        "publish_date": "2024-01-01T00:00:00Z",
        "duration": "PT10M",
        "view_count": 1000,
        "description": "A test video description",
        "has_captions": True,
        "relevance_score": score,
        "inclusion_rationale": "Relevant to topic",
        "included": included,
    }


def test_validate_checkpoint_accepts_valid_data():
    checkpoint = {
        "metadata": {
            "research_project": "ai_temporal_video",
            "query_terms": ["temporal video understanding"],
            "research_criteria_version": "0.1.0",
            "timestamp": "2026-04-07T12:00:00Z",
            "total_candidates": 10,
            "total_included": 3,
        },
        "videos": [_make_video()],
    }

    errors = validate_checkpoint(checkpoint)
    assert errors == []


def test_validate_checkpoint_catches_missing_metadata_fields():
    checkpoint = {
        "metadata": {"research_project": "test"},
        "videos": [_make_video()],
    }

    errors = validate_checkpoint(checkpoint)
    assert len(errors) > 0
    assert any("query_terms" in e for e in errors)


def test_validate_checkpoint_catches_missing_video_fields():
    checkpoint = {
        "metadata": {
            "research_project": "test",
            "query_terms": ["test"],
            "research_criteria_version": "0.1.0",
            "timestamp": "2026-04-07T12:00:00Z",
            "total_candidates": 1,
            "total_included": 1,
        },
        "videos": [{"video_id": "abc123"}],
    }

    errors = validate_checkpoint(checkpoint)
    assert len(errors) > 0


def test_write_and_read_checkpoint_roundtrip(tmp_path):
    videos = [_make_video("vid1", 5, True), _make_video("vid2", 2, False)]
    path = tmp_path / "test_checkpoint.json"

    write_checkpoint(
        path=str(path),
        research_project="ai_temporal_video",
        query_terms=["temporal video", "video transformers"],
        research_criteria_version="0.1.0",
        videos=videos,
    )

    loaded = read_checkpoint(str(path))

    assert loaded["metadata"]["research_project"] == "ai_temporal_video"
    assert loaded["metadata"]["total_candidates"] == 2
    assert loaded["metadata"]["total_included"] == 1
    assert len(loaded["videos"]) == 2
    assert loaded["videos"][0]["video_id"] == "vid1"


def _make_item(item_id="arxiv:2401.12345", source_type="arxiv", score=4, included=True):
    return {
        "item_id": item_id,
        "source_type": source_type,
        "url": "https://arxiv.org/abs/2401.12345",
        "title": "Test Paper",
        "authors": [{"name": "Test Author", "affiliation": "Test University"}],
        "publish_date": "2024-01-15T00:00:00Z",
        "description": "A test paper abstract",
        "content_type": "preprint",
        "full_text_available": True,
        "relevance_score": score,
        "inclusion_rationale": "Relevant to topic",
        "included": included,
    }


def test_validate_checkpoint_accepts_item_format():
    checkpoint = {
        "metadata": {
            "research_project": "ai_temporal_video",
            "query_terms": ["temporal video understanding"],
            "research_criteria_version": "0.1.0",
            "timestamp": "2026-04-07T12:00:00Z",
            "total_candidates": 10,
            "total_included": 3,
        },
        "items": [_make_item()],
    }
    errors = validate_checkpoint(checkpoint)
    assert errors == []


def test_validate_checkpoint_catches_missing_item_fields():
    checkpoint = {
        "metadata": {
            "research_project": "test",
            "query_terms": ["test"],
            "research_criteria_version": "0.1.0",
            "timestamp": "2026-04-07T12:00:00Z",
            "total_candidates": 1,
            "total_included": 1,
        },
        "items": [{"item_id": "arxiv:2401.12345"}],
    }
    errors = validate_checkpoint(checkpoint)
    assert len(errors) > 0
    assert any("source_type" in e for e in errors)


def test_validate_checkpoint_rejects_missing_both_keys():
    checkpoint = {
        "metadata": {
            "research_project": "test",
            "query_terms": ["test"],
            "research_criteria_version": "0.1.0",
            "timestamp": "2026-04-07T12:00:00Z",
            "total_candidates": 0,
            "total_included": 0,
        },
    }
    errors = validate_checkpoint(checkpoint)
    assert any("videos" in e and "items" in e for e in errors)


def test_write_checkpoint_only_includes_scored_videos(tmp_path):
    """Checkpoint only includes videos that were scored (included=True)."""
    videos = [
        _make_video("vid1", 5, True),
        _make_video("vid2", 2, False),
        _make_video("vid3", 3, True),
    ]
    path = tmp_path / "test_checkpoint.json"

    write_checkpoint(
        path=str(path),
        research_project="test",
        query_terms=["test"],
        research_criteria_version="0.1.0",
        videos=videos,
        included_only=True,
    )

    loaded = read_checkpoint(str(path))
    assert len(loaded["videos"]) == 2
    assert all(v["included"] for v in loaded["videos"])


def test_write_item_checkpoint_roundtrip(tmp_path):
    from src.stage.checkpoint import write_item_checkpoint
    items = [_make_item("arxiv:001", "arxiv", 5, True), _make_item("arxiv:002", "arxiv", 2, False)]
    path = tmp_path / "test_item_checkpoint.json"

    write_item_checkpoint(
        path=str(path),
        research_project="ai_temporal_video",
        query_terms=["temporal video", "video transformers"],
        research_criteria_version="0.1.0",
        items=items,
        sources_used=["arxiv"],
    )

    loaded = read_checkpoint(str(path))
    assert "items" in loaded
    assert "videos" not in loaded
    assert loaded["metadata"]["research_project"] == "ai_temporal_video"
    assert loaded["metadata"]["total_candidates"] == 2
    assert loaded["metadata"]["total_included"] == 1
    assert loaded["metadata"]["sources_used"] == ["arxiv"]
    assert len(loaded["items"]) == 2


def test_write_item_checkpoint_included_only(tmp_path):
    from src.stage.checkpoint import write_item_checkpoint
    items = [
        _make_item("arxiv:001", "arxiv", 5, True),
        _make_item("arxiv:002", "arxiv", 2, False),
        _make_item("yt:abc", "youtube", 4, True),
    ]
    path = tmp_path / "test_item_checkpoint.json"

    write_item_checkpoint(
        path=str(path),
        research_project="test",
        query_terms=["test"],
        research_criteria_version="0.1.0",
        items=items,
        sources_used=["arxiv", "youtube"],
        included_only=True,
    )

    loaded = read_checkpoint(str(path))
    assert len(loaded["items"]) == 2
    assert all(item["included"] for item in loaded["items"])


def test_write_item_checkpoint_validation_error(tmp_path):
    from src.stage.checkpoint import write_item_checkpoint
    path = tmp_path / "bad_checkpoint.json"
    bad_items = [{"item_id": "arxiv:001"}]  # missing required fields

    with pytest.raises(ValueError, match="Checkpoint validation failed"):
        write_item_checkpoint(
            path=str(path),
            research_project="test",
            query_terms=["test"],
            research_criteria_version="0.1.0",
            items=bad_items,
            sources_used=["arxiv"],
        )
