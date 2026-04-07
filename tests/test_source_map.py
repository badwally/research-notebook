import pytest
from src.output.source_map import build_source_map, resolve_citation


def test_build_source_map_matches_by_title():
    nlm_sources = [
        {"id": "nlm-aaa", "title": "Video About ST-GCN", "type": "youtube"},
        {"id": "nlm-bbb", "title": "TriDet Paper", "type": "youtube"},
    ]
    videos = [
        {"video_id": "vid1", "title": "Video About ST-GCN", "url": "https://youtube.com/watch?v=vid1", "channel_name": "CVF"},
        {"video_id": "vid2", "title": "TriDet Paper", "url": "https://youtube.com/watch?v=vid2", "channel_name": "CVPR"},
        {"video_id": "vid3", "title": "Unmatched Video", "url": "https://youtube.com/watch?v=vid3", "channel_name": "Other"},
    ]

    source_map = build_source_map(nlm_sources, videos)

    assert source_map["nlm-aaa"]["video_id"] == "vid1"
    assert source_map["nlm-bbb"]["video_id"] == "vid2"
    assert "nlm-ccc" not in source_map


def test_resolve_citation_returns_video_id():
    source_map = {
        "nlm-aaa": {"video_id": "vid1", "title": "Video About ST-GCN"},
    }
    citations = {"1": "nlm-aaa", "2": "nlm-aaa", "3": "nlm-unknown"}

    resolved = resolve_citation(citations, source_map)

    assert resolved["1"]["video_id"] == "vid1"
    assert resolved["3"] is None


def test_build_source_map_handles_html_entities():
    nlm_sources = [
        {"id": "nlm-aaa", "title": "ECCV&#39;24 Training-free Video", "type": "youtube"},
    ]
    videos = [
        {"video_id": "vid1", "title": "ECCV&#39;24 Training-free Video", "url": "https://youtube.com/watch?v=vid1", "channel_name": "Test"},
    ]

    source_map = build_source_map(nlm_sources, videos)
    assert "nlm-aaa" in source_map
