"""Ingestion log writing for the NotebookLM ingestion pipeline."""

import json
import os
from datetime import datetime, timezone


def make_result_entry(
    video_id: str,
    url: str,
    title: str,
    status: str,
    error_message: str = None,
) -> dict:
    """Create a per-video result entry for the ingestion log.

    Args:
        video_id: YouTube video ID.
        url: Full YouTube URL.
        title: Video title.
        status: "success" or "error".
        error_message: Error details if status is "error".

    Returns:
        Result entry dict.
    """
    return {
        "video_id": video_id,
        "url": url,
        "title": title,
        "status": status,
        "error_message": error_message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def write_ingestion_log(
    path: str,
    notebook_id: str,
    notebook_name: str,
    checkpoint_path: str,
    results: list,
) -> str:
    """Write an ingestion log to disk.

    Args:
        path: Output file path.
        notebook_id: NotebookLM notebook ID.
        notebook_name: Notebook display name.
        checkpoint_path: Path to the checkpoint file that was ingested.
        results: List of per-video result entries from make_result_entry().

    Returns:
        Path to the written log file.
    """
    succeeded = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "error")

    log = {
        "metadata": {
            "notebook_id": notebook_id,
            "notebook_name": notebook_name,
            "checkpoint_path": checkpoint_path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_attempted": len(results),
            "total_succeeded": succeeded,
            "total_failed": failed,
        },
        "results": results,
    }

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(log, f, indent=2)

    return path
