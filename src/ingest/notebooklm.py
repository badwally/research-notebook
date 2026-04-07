# src/ingest/notebooklm.py
"""NotebookLM ingestion via the nlm CLI."""

import json
import os
import subprocess
import time
from datetime import datetime, timezone

from src.stage.checkpoint import read_checkpoint
from src.ingest.log import make_result_entry, write_ingestion_log


NLM_CMD = ["uvx", "--from", "notebooklm-mcp-cli", "nlm"]


def _run_nlm(args: list, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run an nlm CLI command and return the result.

    Args:
        args: Arguments to pass after 'nlm'.
        timeout: Command timeout in seconds.

    Returns:
        CompletedProcess with stdout/stderr.

    Raises:
        RuntimeError: If the command fails.
    """
    cmd = NLM_CMD + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"nlm command failed (exit {result.returncode}): {' '.join(cmd)}\n"
            f"stderr: {result.stderr.strip()}"
        )
    return result


def create_notebook(project_name: str) -> str:
    """Create a NotebookLM notebook or return existing one's ID.

    Args:
        project_name: Display name for the notebook.

    Returns:
        Notebook ID string.

    Raises:
        RuntimeError: If notebook creation fails.
    """
    # Check for existing notebook with this name
    result = _run_nlm(["notebook", "list", "--json"])
    try:
        notebooks = json.loads(result.stdout)
        for nb in notebooks:
            if nb.get("title") == project_name:
                print(f"Found existing notebook: {project_name} ({nb['id']})")
                return nb["id"]
    except (json.JSONDecodeError, KeyError):
        pass  # No existing notebooks or unexpected format, create new

    # Create new notebook (no --json flag available, parse text output)
    result = _run_nlm(["notebook", "create", project_name])
    # Output format: "✓ Created notebook: Name\n  ID: <uuid>"
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("ID:"):
            notebook_id = line.split(":", 1)[1].strip()
            print(f"Created notebook: {project_name} ({notebook_id})")
            return notebook_id
    raise RuntimeError(f"Failed to parse notebook ID from output:\n{result.stdout}")


def add_youtube_source(
    notebook_id: str,
    url: str,
    wait: bool = True,
    max_retries: int = 3,
) -> dict:
    """Add a YouTube URL as a source to a notebook.

    Args:
        notebook_id: NotebookLM notebook ID.
        url: YouTube video URL.
        wait: Wait for source processing to complete.
        max_retries: Max retries on failure (exponential backoff).

    Returns:
        Dict with keys: url, status ("success" | "error"), error_message.
    """
    args = ["source", "add", notebook_id, "--youtube", url]
    if wait:
        args.extend(["--wait", "--wait-timeout", "300"])

    for attempt in range(max_retries):
        try:
            _run_nlm(args, timeout=360)
            return {"url": url, "status": "success", "error_message": None}
        except RuntimeError as e:
            error_msg = str(e)
            if attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)
                print(f"  Retry {attempt + 1}/{max_retries} in {wait_time}s: {error_msg[:100]}")
                time.sleep(wait_time)
            else:
                return {"url": url, "status": "error", "error_message": error_msg}

    return {"url": url, "status": "error", "error_message": "Max retries exceeded"}


def ingest_checkpoint(checkpoint_path: str, notebook_name: str) -> dict:
    """Ingest all included videos from a checkpoint file into NotebookLM.

    Args:
        checkpoint_path: Path to Stage 2 checkpoint JSON file.
        notebook_name: Display name for the NotebookLM notebook.

    Returns:
        Summary dict with notebook_id, results list, and log_path.
    """
    checkpoint = read_checkpoint(checkpoint_path)
    included_videos = [v for v in checkpoint["videos"] if v.get("included")]

    if not included_videos:
        print("No included videos in checkpoint. Nothing to ingest.")
        return {"notebook_id": None, "results": [], "log_path": None}

    print(f"Ingesting {len(included_videos)} videos into NotebookLM...")

    # Create or reuse notebook
    notebook_id = create_notebook(notebook_name)

    # Add each video
    results = []
    for i, video in enumerate(included_videos):
        print(f"  [{i+1}/{len(included_videos)}] {video['title'][:60]}...")
        source_result = add_youtube_source(notebook_id, video["url"])

        results.append(make_result_entry(
            video_id=video["video_id"],
            url=video["url"],
            title=video["title"],
            status=source_result["status"],
            error_message=source_result["error_message"],
        ))

        if source_result["status"] == "success":
            print(f"    OK")
        else:
            print(f"    FAILED: {source_result['error_message'][:80]}")

    # Write ingestion log
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = f"logs/ingestion_{notebook_name.replace(' ', '_').lower()}_{timestamp}.json"

    write_ingestion_log(
        path=log_path,
        notebook_id=notebook_id,
        notebook_name=notebook_name,
        checkpoint_path=checkpoint_path,
        results=results,
    )

    succeeded = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "error")
    print(f"\nIngestion complete: {succeeded} succeeded, {failed} failed")
    print(f"Log: {log_path}")

    return {"notebook_id": notebook_id, "results": results, "log_path": log_path}
