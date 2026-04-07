# Stage 3: NotebookLM Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ingest included YouTube videos from a Stage 2 checkpoint file into a NotebookLM notebook via the `nlm` CLI, with per-video status logging.

**Architecture:** Python module calls the `nlm` CLI via subprocess for notebook creation and YouTube source ingestion. Reads checkpoint files produced by Stage 2. Writes JSON ingestion logs with per-video results. The `notebooklm-mcp-cli` package provides the `nlm` command.

**Tech Stack:** Python 3.9+, notebooklm-mcp-cli (via uv tool), subprocess, existing Stage 2 checkpoint module

---

## Prerequisites

Before starting, the implementer must:

1. Install the CLI: `uv tool install notebooklm-mcp-cli`
2. Authenticate: `uvx --from notebooklm-mcp-cli nlm login` (opens browser for Google OAuth)
3. Verify: `uvx --from notebooklm-mcp-cli nlm doctor`
4. Register MCP for later stages: `uvx --from notebooklm-mcp-cli nlm setup add claude-code`

---

## File Structure

| File | Purpose |
|------|---------|
| `src/ingest/notebooklm.py` | NotebookLM ingestion: create notebook, add sources, orchestrate batch |
| `src/ingest/log.py` | Ingestion log writing and schema |
| `tests/test_ingest_log.py` | Tests for ingestion log writing |
| `scripts/run_ingestion.py` | CLI script to run ingestion from a checkpoint file |

---

### Task 1: Ingestion Log Module (TDD)

**Files:**
- Create: `src/ingest/log.py`
- Create: `tests/test_ingest_log.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_ingest_log.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
source .venv/bin/activate
python -m pytest tests/test_ingest_log.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement the ingestion log module**

```python
# src/ingest/log.py
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
    results: list[dict],
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
source .venv/bin/activate
python -m pytest tests/test_ingest_log.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/ingest/log.py tests/test_ingest_log.py
git commit -m "Add ingestion log module with per-video result tracking

make_result_entry creates individual result dicts.
write_ingestion_log writes the full log with metadata summary."
```

---

### Task 2: NotebookLM Ingestion Module

**Files:**
- Create: `src/ingest/notebooklm.py`

- [ ] **Step 1: Implement the ingestion module**

```python
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


def _run_nlm(args: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
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

    # Create new notebook
    result = _run_nlm(["notebook", "create", project_name, "--json"])
    try:
        notebook = json.loads(result.stdout)
        notebook_id = notebook["id"]
        print(f"Created notebook: {project_name} ({notebook_id})")
        return notebook_id
    except (json.JSONDecodeError, KeyError) as e:
        raise RuntimeError(f"Failed to parse notebook creation response: {e}\n{result.stdout}")


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
```

- [ ] **Step 2: Verify all existing tests still pass**

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

Expected: All 13 tests PASS (10 existing + 3 new from Task 1).

- [ ] **Step 3: Commit**

```bash
git add src/ingest/notebooklm.py
git commit -m "Add NotebookLM ingestion module

create_notebook creates or reuses notebooks by name.
add_youtube_source adds URLs with retry and backoff.
ingest_checkpoint orchestrates full batch ingestion from
a Stage 2 checkpoint file."
```

---

### Task 3: Ingestion Validation Script

**Files:**
- Create: `scripts/run_ingestion.py`

- [ ] **Step 1: Create the script**

```python
#!/usr/bin/env python3
"""Run NotebookLM ingestion from a Stage 2 checkpoint file.

Usage:
    python scripts/run_ingestion.py <checkpoint_path> [--notebook-name NAME]

Examples:
    python scripts/run_ingestion.py data/staged/ai_temporal_video_20260407_170548.json
    python scripts/run_ingestion.py data/staged/ai_temporal_video_20260407_170548.json --notebook-name "AI Video Research"
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingest.notebooklm import ingest_checkpoint
from src.stage.checkpoint import read_checkpoint


def main():
    parser = argparse.ArgumentParser(description="Ingest checkpoint into NotebookLM")
    parser.add_argument("checkpoint", help="Path to Stage 2 checkpoint JSON file")
    parser.add_argument(
        "--notebook-name",
        default=None,
        help="Notebook display name (default: research_project from checkpoint metadata)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.checkpoint):
        print(f"Error: checkpoint file not found: {args.checkpoint}")
        sys.exit(1)

    # Derive notebook name from checkpoint if not provided
    checkpoint = read_checkpoint(args.checkpoint)
    notebook_name = args.notebook_name or checkpoint["metadata"]["research_project"]

    print(f"Checkpoint: {args.checkpoint}")
    print(f"Notebook: {notebook_name}")
    included = [v for v in checkpoint["videos"] if v.get("included")]
    print(f"Videos to ingest: {len(included)}")
    print()

    result = ingest_checkpoint(args.checkpoint, notebook_name)

    if result["notebook_id"]:
        print(f"\nNotebook ID: {result['notebook_id']}")
        print(f"Ingestion log: {result['log_path']}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make executable and verify it parses**

```bash
chmod +x scripts/run_ingestion.py
source .venv/bin/activate
python scripts/run_ingestion.py --help
```

Expected: Help text with usage info.

- [ ] **Step 3: Commit**

```bash
git add scripts/run_ingestion.py
git commit -m "Add NotebookLM ingestion validation script

Reads checkpoint path as argument, derives notebook name from
metadata, runs full ingestion, prints summary."
```

---

### Task 4: MCP Server Registration and End-to-End Test

This task is operational — no code to write, just setup and validation.

- [ ] **Step 1: Install and authenticate**

```bash
uv tool install notebooklm-mcp-cli
uvx --from notebooklm-mcp-cli nlm login
uvx --from notebooklm-mcp-cli nlm doctor
```

Verify doctor output confirms authentication and Pro tier.

- [ ] **Step 2: Register MCP server for Stages 4-5**

```bash
uvx --from notebooklm-mcp-cli nlm setup add claude-code
```

Verify `.mcp.json` is updated with the notebooklm server entry.

- [ ] **Step 3: Run end-to-end ingestion**

Find the checkpoint file from the Stage 1-2 test run:

```bash
ls data/staged/ai_temporal_video_*.json
```

Run ingestion:

```bash
source .venv/bin/activate
python scripts/run_ingestion.py data/staged/ai_temporal_video_20260407_170548.json --notebook-name "AI Temporal Video Analysis"
```

Expected output:
- Notebook created (or existing one found)
- 4 videos attempted
- Ingestion log written to logs/

- [ ] **Step 4: Verify in NotebookLM**

```bash
uvx --from notebooklm-mcp-cli nlm source list <notebook_id>
```

Verify sources appear. Try a test query:

```bash
uvx --from notebooklm-mcp-cli nlm notebook query <notebook_id> "What temporal video analysis methods are discussed?"
```

- [ ] **Step 5: Update CLAUDE.md**

Update the Status section:

```
- Stage 3: NotebookLM ingestion — COMPLETE
```

```bash
git add CLAUDE.md
git commit -m "Mark Stage 3 (NotebookLM ingestion) complete"
```
