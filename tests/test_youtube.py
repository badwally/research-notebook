import pytest
from src.search.youtube import normalize_video


def test_normalize_video_from_api_response():
    """Verify normalize_video extracts and flattens the fields we need."""
    search_item = {
        "id": {"videoId": "dQw4w9WgXcQ"},
        "snippet": {
            "title": "TimeSformer: Is Space-Time Attention All You Need?",
            "channelTitle": "Meta AI",
            "channelId": "UC1234567890",
            "publishedAt": "2021-06-15T14:00:00Z",
            "description": "We present TimeSformer, a convolution-free approach to video classification built exclusively on self-attention over space and time. " * 5,
        },
    }
    details = {
        "contentDetails": {"duration": "PT25M30S"},
        "statistics": {"viewCount": "45000"},
    }
    captions_available = True

    result = normalize_video(search_item, details, captions_available)

    assert result["video_id"] == "dQw4w9WgXcQ"
    assert result["url"] == "https://youtube.com/watch?v=dQw4w9WgXcQ"
    assert result["title"] == "TimeSformer: Is Space-Time Attention All You Need?"
    assert result["channel_name"] == "Meta AI"
    assert result["channel_id"] == "UC1234567890"
    assert result["publish_date"] == "2021-06-15T14:00:00Z"
    assert result["duration"] == "PT25M30S"
    assert result["view_count"] == 45000
    assert len(result["description"]) <= 500
    assert result["has_captions"] is True


def test_normalize_video_truncates_long_description():
    search_item = {
        "id": {"videoId": "abc123"},
        "snippet": {
            "title": "Test",
            "channelTitle": "Test Channel",
            "channelId": "UC0000",
            "publishedAt": "2024-01-01T00:00:00Z",
            "description": "x" * 1000,
        },
    }
    details = {
        "contentDetails": {"duration": "PT10M"},
        "statistics": {"viewCount": "100"},
    }

    result = normalize_video(search_item, details, False)

    assert len(result["description"]) == 500
    assert result["has_captions"] is False


def test_normalize_video_handles_missing_view_count():
    search_item = {
        "id": {"videoId": "abc123"},
        "snippet": {
            "title": "Test",
            "channelTitle": "Test Channel",
            "channelId": "UC0000",
            "publishedAt": "2024-01-01T00:00:00Z",
            "description": "Short description",
        },
    }
    details = {
        "contentDetails": {"duration": "PT10M"},
        "statistics": {},
    }

    result = normalize_video(search_item, details, True)

    assert result["view_count"] == 0
