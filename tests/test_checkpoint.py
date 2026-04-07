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
