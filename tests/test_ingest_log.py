import json
import pytest
from src.ingest.log import write_ingestion_log, make_result_entry


def test_make_result_entry_success():
    entry = make_result_entry(
        video_id="abc123",
        url="https://youtube.com/watch?v=abc123",
        title="Test Video",
        status="success",
    )

    assert entry["video_id"] == "abc123"
    assert entry["url"] == "https://youtube.com/watch?v=abc123"
    assert entry["title"] == "Test Video"
    assert entry["status"] == "success"
    assert entry["error_message"] is None
    assert "timestamp" in entry


def test_make_result_entry_error():
    entry = make_result_entry(
        video_id="abc123",
        url="https://youtube.com/watch?v=abc123",
        title="Test Video",
        status="error",
        error_message="Source processing failed",
    )

    assert entry["status"] == "error"
    assert entry["error_message"] == "Source processing failed"


def test_write_ingestion_log(tmp_path):
    results = [
        make_result_entry("vid1", "https://youtube.com/watch?v=vid1", "Video 1", "success"),
        make_result_entry("vid2", "https://youtube.com/watch?v=vid2", "Video 2", "error", "Timeout"),
    ]
    path = tmp_path / "test_log.json"

    write_ingestion_log(
        path=str(path),
        notebook_id="nb_12345",
        notebook_name="AI Temporal Video",
        checkpoint_path="data/staged/test.json",
        results=results,
    )

    with open(path) as f:
        log = json.load(f)

    assert log["metadata"]["notebook_id"] == "nb_12345"
    assert log["metadata"]["notebook_name"] == "AI Temporal Video"
    assert log["metadata"]["checkpoint_path"] == "data/staged/test.json"
    assert log["metadata"]["total_attempted"] == 2
    assert log["metadata"]["total_succeeded"] == 1
    assert log["metadata"]["total_failed"] == 1
    assert len(log["results"]) == 2
    assert log["results"][0]["status"] == "success"
    assert log["results"][1]["status"] == "error"
