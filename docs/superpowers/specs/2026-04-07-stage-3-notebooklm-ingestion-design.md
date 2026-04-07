# Stage 3: NotebookLM Ingestion — Design Spec

## Overview

Ingest YouTube videos from a Stage 2 checkpoint file into a NotebookLM notebook via the `notebooklm-mcp-cli` MCP server. Only included videos (score >= 3) are ingested. Per-video results are logged.

## Architecture

The MCP server (`notebooklm-mcp`) exposes NotebookLM operations as tools callable by Claude Code. The ingestion module reads a checkpoint file, creates (or reuses) a notebook, and adds each video URL as a source using the `--youtube` flag. An ingestion log captures per-video success/failure.

### Data Flow

```
checkpoint.json (Stage 2 output)
  → read included videos
  → create notebook via MCP (or CLI fallback)
  → for each video: add YouTube URL as source
  → write ingestion log to logs/
```

## Components

### MCP Server Setup

- Install: `uv tool install notebooklm-mcp-cli`
- Authenticate: `nlm login` (OAuth browser flow, one-time)
- Register MCP server: `nlm setup add claude-code` (adds to `.mcp.json`)
- Verify: `nlm doctor` to confirm auth and Pro tier

This is operational setup done once before first run, not automated in code.

### Ingestion Module (`src/ingest/notebooklm.py`)

Orchestrates the ingestion process using the CLI as the execution layer. MCP tools are available for interactive use during Claude Code sessions, but the ingestion script uses CLI commands for reliability and inspectability.

**Functions:**

- `create_notebook(project_name: str) -> str` — Creates a NotebookLM notebook, returns notebook ID. If a notebook with the same name already exists, returns its ID instead.
- `add_youtube_source(notebook_id: str, url: str, wait: bool = True) -> dict` — Adds a YouTube URL as a source. Returns status dict with video_id, url, status ("success" | "error"), and error_message.
- `ingest_checkpoint(checkpoint_path: str, notebook_name: str) -> dict` — Full ingestion flow: reads checkpoint, creates notebook, adds each included video, returns summary with notebook_id and per-video results.

### Ingestion Log (`logs/ingestion_{project}_{timestamp}.json`)

```json
{
  "metadata": {
    "notebook_id": "string",
    "notebook_name": "string",
    "checkpoint_path": "string",
    "timestamp": "ISO 8601",
    "total_attempted": 4,
    "total_succeeded": 3,
    "total_failed": 1
  },
  "results": [
    {
      "video_id": "string",
      "url": "string",
      "title": "string",
      "status": "success | error",
      "error_message": "string | null",
      "timestamp": "ISO 8601"
    }
  ]
}
```

## Error Handling

- **Per-video failure:** Log error, skip video, continue batch. No retry — failures surface in the ingestion log for manual review.
- **Auth failure:** `nlm login` session expired. Halt ingestion, print message telling user to run `nlm login`.
- **Rate limit:** The `--wait` flag on `nlm source add` handles processing time. If rate-limited by the API, wait and retry up to 3 times with exponential backoff.
- **Notebook creation failure:** Fatal — cannot proceed without a notebook. Raise exception.

## CLI vs MCP Decision

The spec originally chose MCP for the "tighter agentic feedback loop." After investigating the tooling:

- MCP is best for **interactive research sessions** (Stages 4-5) where Claude needs to query NotebookLM conversationally
- CLI (`nlm source add --youtube URL --wait`) is better for **batch ingestion** (Stage 3) because it's scriptable, inspectable, and doesn't require an active Claude Code session

**Decision:** Use CLI for Stage 3 ingestion. Keep MCP registered for Stages 4-5. This aligns with the spec's fallback clause: "If MCP proves fragile, fall back to CLI."

## Validation Script

`scripts/run_ingestion.py` — Reads a checkpoint file path as argument, runs the full ingestion, prints summary.

```
python scripts/run_ingestion.py data/staged/ai_temporal_video_20260407_170548.json
```

## Exit Criterion

NotebookLM notebook contains the included videos from the checkpoint as sources. Ingestion log on disk records per-video status. At least one video is queryable in NotebookLM.
