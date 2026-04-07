"""Map NotebookLM source IDs to video metadata for citation resolution."""

import json
import subprocess


NLM_CMD = ["uvx", "--from", "notebooklm-mcp-cli", "nlm"]


def fetch_nlm_sources(notebook_id: str) -> list:
    """Fetch the source list from NotebookLM."""
    result = subprocess.run(
        NLM_CMD + ["source", "list", notebook_id, "--json"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch NLM sources: {result.stderr}")
    return json.loads(result.stdout)


def load_all_videos(checkpoint_paths: list) -> list:
    """Load all included videos from checkpoint files."""
    seen = set()
    videos = []
    for path in checkpoint_paths:
        with open(path) as f:
            checkpoint = json.load(f)
        for v in checkpoint["videos"]:
            if v.get("included") and v["video_id"] not in seen:
                seen.add(v["video_id"])
                videos.append(v)
    return videos


def build_source_map(nlm_sources: list, videos: list) -> dict:
    """Build a mapping from NLM source ID to video metadata. Matches by title."""
    title_to_video = {}
    for v in videos:
        title_to_video[v["title"]] = v

    source_map = {}
    for src in nlm_sources:
        title = src.get("title", "")
        if title in title_to_video:
            source_map[src["id"]] = title_to_video[title]

    return source_map


def resolve_citation(citations: dict, source_map: dict) -> dict:
    """Resolve citation numbers to video metadata."""
    resolved = {}
    for num, nlm_id in citations.items():
        resolved[num] = source_map.get(nlm_id)
    return resolved
