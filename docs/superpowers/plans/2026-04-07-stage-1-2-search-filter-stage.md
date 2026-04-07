# Stages 1-2: YouTube Search, Semantic Filter & JSON Staging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first three pipeline stages — YouTube API search, Claude semantic filtering, and JSON checkpoint staging — so that a search query produces a validated, scored, staged corpus file on disk.

**Architecture:** Python scripts orchestrated by Claude Code. Stage 1a calls YouTube Data API v3 to retrieve video metadata. Stage 1b merges the editorial policy template with the domain config and uses Claude (via Claude Code's own reasoning) to score each video. Stage 2 writes the filtered results to a versioned JSON checkpoint file with schema validation. Each stage is a standalone module with a clear input/output contract.

**Tech Stack:** Python 3.11+, google-api-python-client, PyYAML, pytest

---

## Prerequisites

Before starting, the implementer must:

1. Set up a Python venv: `python3 -m venv .venv && source .venv/bin/activate`
2. Have a YouTube Data API v3 key from Google Cloud Console (store in `config/youtube_api_key.txt`, already gitignored)
3. Verify `ANTHROPIC_API_KEY` is NOT set (Claude Code uses Max plan allocation)

---

## File Structure

| File | Purpose |
|------|---------|
| `src/search/youtube.py` | YouTube Data API v3 client — search, video details, caption check, metadata normalization |
| `src/search/queries.py` | Query expansion — derives search keywords from domain config |
| `src/filter/policy.py` | Loads and merges editorial policy template + domain config |
| `src/filter/semantic.py` | Applies merged policy to video metadata batch, returns scored results |
| `src/stage/checkpoint.py` | Writes filtered results to JSON checkpoint file with schema validation |
| `src/stage/schema.py` | Checkpoint file schema definition and validation |
| `src/pipeline.py` | End-to-end orchestrator: search → filter → stage |
| `tests/test_youtube.py` | Tests for YouTube API client (metadata normalization, pagination) |
| `tests/test_policy.py` | Tests for policy loading and merging |
| `tests/test_checkpoint.py` | Tests for JSON staging and schema validation |
| `requirements.txt` | Python dependencies |

---

### Task 1: Project Python Setup

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`
- Create: `src/search/__init__.py`
- Create: `src/filter/__init__.py`
- Create: `src/stage/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
google-api-python-client>=2.100.0
PyYAML>=6.0
pytest>=8.0
```

- [ ] **Step 2: Create __init__.py files**

Create empty `__init__.py` in each directory:
- `src/__init__.py`
- `src/search/__init__.py`
- `src/filter/__init__.py`
- `src/stage/__init__.py`
- `tests/__init__.py`

- [ ] **Step 3: Install dependencies**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 4: Verify pytest runs**

```bash
source .venv/bin/activate
python -m pytest --version
```

Expected: pytest version string, no errors.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt src/__init__.py src/search/__init__.py src/filter/__init__.py src/stage/__init__.py tests/__init__.py
git commit -m "Add Python project setup with dependencies

google-api-python-client for YouTube API, PyYAML for config,
pytest for testing."
```

---

### Task 2: YouTube API Client — Metadata Normalization

**Files:**
- Create: `src/search/youtube.py`
- Create: `tests/test_youtube.py`

- [ ] **Step 1: Write the failing test for metadata normalization**

```python
# tests/test_youtube.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
source .venv/bin/activate
python -m pytest tests/test_youtube.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'src.search.youtube'`

- [ ] **Step 3: Implement normalize_video**

```python
# src/search/youtube.py
"""YouTube Data API v3 client for the research pipeline."""


def normalize_video(search_item: dict, details: dict, captions_available: bool) -> dict:
    """Flatten YouTube API response into our standard video metadata format.

    Args:
        search_item: Item from YouTube search.list response.
        details: Item from YouTube videos.list response (contentDetails + statistics).
        captions_available: Whether captions exist for this video.

    Returns:
        Normalized video metadata dict matching the pipeline schema.
    """
    snippet = search_item["snippet"]
    video_id = search_item["id"]["videoId"]
    description = snippet["description"][:500]
    view_count = int(details.get("statistics", {}).get("viewCount", 0))

    return {
        "video_id": video_id,
        "url": f"https://youtube.com/watch?v={video_id}",
        "title": snippet["title"],
        "channel_name": snippet["channelTitle"],
        "channel_id": snippet["channelId"],
        "publish_date": snippet["publishedAt"],
        "duration": details["contentDetails"]["duration"],
        "view_count": view_count,
        "description": description,
        "has_captions": captions_available,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
source .venv/bin/activate
python -m pytest tests/test_youtube.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/search/youtube.py tests/test_youtube.py
git commit -m "Add YouTube video metadata normalization

Flattens API response into pipeline-standard schema with
description truncation and missing field handling."
```

---

### Task 3: YouTube API Client — Search and Detail Fetching

**Files:**
- Modify: `src/search/youtube.py`

- [ ] **Step 1: Implement the API client functions**

Add to `src/search/youtube.py`:

```python
from googleapiclient.discovery import build


def build_client(api_key: str):
    """Build a YouTube Data API v3 client."""
    return build("youtube", "v3", developerKey=api_key)


def search_videos(client, query: str, max_results: int = 50, **kwargs) -> list[dict]:
    """Search YouTube for videos matching a query.

    Args:
        client: YouTube API client from build_client().
        query: Search query string.
        max_results: Maximum results to return (API max per page is 50).
        **kwargs: Additional search parameters (publishedAfter, videoDuration,
                  relevanceLanguage, etc.)

    Returns:
        List of search result items from YouTube API.
    """
    request = client.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=min(max_results, 50),
        **kwargs,
    )
    response = request.execute()
    return response.get("items", [])


def get_video_details(client, video_ids: list[str]) -> dict[str, dict]:
    """Fetch content details and statistics for a batch of video IDs.

    Args:
        client: YouTube API client.
        video_ids: List of video IDs (max 50 per API call).

    Returns:
        Dict mapping video_id to its details response.
    """
    request = client.videos().list(
        part="contentDetails,statistics",
        id=",".join(video_ids[:50]),
    )
    response = request.execute()
    return {item["id"]: item for item in response.get("items", [])}


def check_captions(client, video_id: str) -> bool:
    """Check whether captions are available for a video.

    Note: This costs 50 quota units per call. Use judiciously.

    Args:
        client: YouTube API client.
        video_id: Single video ID.

    Returns:
        True if at least one caption track exists.
    """
    try:
        request = client.captions().list(part="snippet", videoId=video_id)
        response = request.execute()
        return len(response.get("items", [])) > 0
    except Exception:
        return False


def search_and_normalize(
    client, query: str, max_results: int = 50, skip_captions: bool = False, **kwargs
) -> list[dict]:
    """Full search pipeline: search → get details → check captions → normalize.

    Args:
        client: YouTube API client.
        query: Search query.
        max_results: Max results.
        skip_captions: If True, skip caption checks (saves 50 units/video).
        **kwargs: Additional search parameters.

    Returns:
        List of normalized video metadata dicts.
    """
    search_results = search_videos(client, query, max_results, **kwargs)
    if not search_results:
        return []

    video_ids = [item["id"]["videoId"] for item in search_results]
    details_map = get_video_details(client, video_ids)

    normalized = []
    for item in search_results:
        vid = item["id"]["videoId"]
        if vid not in details_map:
            continue
        captions = False if skip_captions else check_captions(client, vid)
        normalized.append(normalize_video(item, details_map[vid], captions))

    return normalized
```

- [ ] **Step 2: Commit**

```bash
git add src/search/youtube.py
git commit -m "Add YouTube search, detail fetching, and caption checking

search_and_normalize orchestrates the full flow: search → details
→ captions → normalize. Caption checks can be skipped to save quota."
```

Note: API functions are not unit-tested because they wrap the Google API client directly. They will be validated in the end-to-end test (Task 7).

---

### Task 4: Editorial Policy Loading and Merging

**Files:**
- Create: `src/filter/policy.py`
- Create: `tests/test_policy.py`

- [ ] **Step 1: Write the failing test for policy loading**

```python
# tests/test_policy.py
import pytest
import yaml
from src.filter.policy import load_policy, merge_policy


def test_load_policy_reads_yaml(tmp_path):
    """Verify load_policy reads a YAML file and returns a dict."""
    config = {"domain": {"topic": "test topic"}, "version": "0.1.0"}
    path = tmp_path / "test.yaml"
    path.write_text(yaml.dump(config))

    result = load_policy(str(path))

    assert result["domain"]["topic"] == "test topic"
    assert result["version"] == "0.1.0"


def test_merge_policy_fills_template_slots():
    """Verify merge_policy overlays domain config onto the template."""
    template = {
        "system_prompt": "You are a curator.",
        "version": "{version}",
        "domain": {"topic": "{topic}", "field": "{field}", "description": "{desc}"},
        "inclusion_criteria": {"required": []},
        "exclusion_criteria": {"hard_exclude": []},
        "quality_signals": {
            "channel_authority": {
                "description": "Channel credibility",
                "positive_signals": [],
                "negative_signals": [],
            },
        },
        "scoring_rubric": {
            "scale": "1-5",
            "inclusion_threshold": 3,
            "levels": {5: {"label": "Essential", "description": "Top tier"}},
        },
        "output_format": {"description": "Return JSON", "fields": {}},
    }
    domain = {
        "version": "0.1.0",
        "domain": {"topic": "AI video", "field": "CV/ML", "description": "Research"},
        "inclusion_criteria": {"required": ["Must be about AI"]},
        "exclusion_criteria": {"hard_exclude": ["No marketing"]},
        "quality_signals": {
            "channel_authority": {
                "positive_signals": ["University channel"],
                "negative_signals": ["Clickbait"],
            },
        },
        "scoring_rubric": {"inclusion_threshold": 4},
    }

    result = merge_policy(template, domain)

    assert result["version"] == "0.1.0"
    assert result["domain"]["topic"] == "AI video"
    assert result["inclusion_criteria"]["required"] == ["Must be about AI"]
    assert result["exclusion_criteria"]["hard_exclude"] == ["No marketing"]
    assert result["quality_signals"]["channel_authority"]["positive_signals"] == ["University channel"]
    assert result["scoring_rubric"]["inclusion_threshold"] == 4
    # Template-only fields preserved
    assert result["system_prompt"] == "You are a curator."
    assert result["scoring_rubric"]["scale"] == "1-5"
    assert result["scoring_rubric"]["levels"][5]["label"] == "Essential"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
source .venv/bin/activate
python -m pytest tests/test_policy.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement policy loading and merging**

```python
# src/filter/policy.py
"""Load and merge editorial policy template with domain configuration."""

import yaml


def load_policy(path: str) -> dict:
    """Load a YAML policy or domain config file.

    Args:
        path: Path to YAML file.

    Returns:
        Parsed YAML as dict.
    """
    with open(path) as f:
        return yaml.safe_load(f)


def merge_policy(template: dict, domain: dict) -> dict:
    """Merge domain config values into the editorial policy template.

    Domain config values override template values at matching keys.
    Uses recursive dict merge so template-only keys are preserved.

    Args:
        template: Parsed editorial_policy_template.yaml.
        domain: Parsed domain config (e.g., ai_temporal_video.yaml).

    Returns:
        Merged policy dict ready to be used as Claude's evaluation context.
    """
    return _deep_merge(template, domain)


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Lists and scalars are replaced."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_merged_policy(template_path: str, domain_path: str) -> dict:
    """Convenience: load template and domain, return merged policy.

    Args:
        template_path: Path to editorial_policy_template.yaml.
        domain_path: Path to domain config YAML.

    Returns:
        Merged policy dict.
    """
    template = load_policy(template_path)
    domain = load_policy(domain_path)
    return merge_policy(template, domain)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
source .venv/bin/activate
python -m pytest tests/test_policy.py -v
```

Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/filter/policy.py tests/test_policy.py
git commit -m "Add editorial policy loading and merging

Deep-merges domain config into template. Domain values override
template at matching keys; template-only keys are preserved."
```

---

### Task 5: Semantic Filter — Claude Evaluation

**Files:**
- Create: `src/filter/semantic.py`

- [ ] **Step 1: Implement the semantic filter**

This module formats the merged policy + video batch into a prompt and parses Claude's response. Since the filter runs as Claude Code's own reasoning (not via API), the actual Claude call happens at the orchestration layer. This module handles prompt construction and response parsing.

```python
# src/filter/semantic.py
"""Semantic filtering: construct prompts and parse Claude's scoring responses."""

import json
import yaml


def build_filter_prompt(merged_policy: dict, videos: list[dict]) -> str:
    """Build the full prompt for Claude to evaluate a batch of videos.

    Args:
        merged_policy: Merged editorial policy (template + domain config).
        videos: List of normalized video metadata dicts from Stage 1a.

    Returns:
        Formatted prompt string ready for Claude evaluation.
    """
    policy_yaml = yaml.dump(merged_policy, default_flow_style=False, sort_keys=False)

    video_json = json.dumps(videos, indent=2)

    return f"""## Editorial Policy

{policy_yaml}

## Videos to Evaluate

{video_json}

## Instructions

Evaluate each video against the editorial policy above. For each video, return a JSON array where each element has:
- "video_id": the video's ID
- "relevance_score": integer 1-5 per the scoring rubric
- "inclusion_rationale": 1-2 sentences explaining your score
- "included": boolean (true if relevance_score >= {merged_policy['scoring_rubric']['inclusion_threshold']})

Return ONLY the JSON array, no other text."""


def parse_filter_response(response_text: str) -> list[dict]:
    """Parse Claude's filter response into a list of scoring dicts.

    Args:
        response_text: Claude's response (should be a JSON array).

    Returns:
        List of dicts with video_id, relevance_score, inclusion_rationale, included.

    Raises:
        ValueError: If response cannot be parsed as valid JSON.
    """
    text = response_text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        text = text.strip()

    try:
        scores = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Claude's filter response as JSON: {e}")

    if not isinstance(scores, list):
        raise ValueError(f"Expected JSON array, got {type(scores).__name__}")

    return scores


def apply_scores(videos: list[dict], scores: list[dict]) -> list[dict]:
    """Merge Claude's scores back into the video metadata.

    Args:
        videos: Original normalized video metadata.
        scores: Claude's scoring output (from parse_filter_response).

    Returns:
        Videos with relevance_score, inclusion_rationale, and included fields added.
    """
    score_map = {s["video_id"]: s for s in scores}

    result = []
    for video in videos:
        vid = video["video_id"]
        if vid in score_map:
            scored = dict(video)
            scored["relevance_score"] = score_map[vid]["relevance_score"]
            scored["inclusion_rationale"] = score_map[vid]["inclusion_rationale"]
            scored["included"] = score_map[vid]["included"]
            result.append(scored)

    return result
```

- [ ] **Step 2: Commit**

```bash
git add src/filter/semantic.py
git commit -m "Add semantic filter prompt construction and response parsing

build_filter_prompt creates the evaluation prompt from merged policy
and video batch. parse_filter_response handles JSON extraction
including markdown code fence stripping. apply_scores merges results
back into video metadata."
```

Note: The actual Claude evaluation happens at the orchestration layer (Task 7) since it uses Claude Code's own reasoning, not an API call. This module handles the data transformation around it.

---

### Task 6: JSON Staging and Schema Validation

**Files:**
- Create: `src/stage/schema.py`
- Create: `src/stage/checkpoint.py`
- Create: `tests/test_checkpoint.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_checkpoint.py
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
        "videos": [{"video_id": "abc123"}],  # Missing most fields
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
source .venv/bin/activate
python -m pytest tests/test_checkpoint.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement schema validation**

```python
# src/stage/schema.py
"""Checkpoint file schema definition and validation."""

METADATA_REQUIRED_FIELDS = {
    "research_project": str,
    "query_terms": list,
    "research_criteria_version": str,
    "timestamp": str,
    "total_candidates": int,
    "total_included": int,
}

VIDEO_REQUIRED_FIELDS = {
    "video_id": str,
    "url": str,
    "title": str,
    "channel_name": str,
    "channel_id": str,
    "publish_date": str,
    "duration": str,
    "view_count": int,
    "description": str,
    "has_captions": bool,
    "relevance_score": int,
    "inclusion_rationale": str,
    "included": bool,
}


def validate_checkpoint(checkpoint: dict) -> list[str]:
    """Validate a checkpoint dict against the expected schema.

    Args:
        checkpoint: Parsed checkpoint data.

    Returns:
        List of error strings. Empty list means valid.
    """
    errors = []

    if "metadata" not in checkpoint:
        errors.append("Missing top-level 'metadata' key")
    else:
        meta = checkpoint["metadata"]
        for field, expected_type in METADATA_REQUIRED_FIELDS.items():
            if field not in meta:
                errors.append(f"Missing metadata field: {field}")
            elif not isinstance(meta[field], expected_type):
                errors.append(f"metadata.{field}: expected {expected_type.__name__}, got {type(meta[field]).__name__}")

    if "videos" not in checkpoint:
        errors.append("Missing top-level 'videos' key")
    elif not isinstance(checkpoint["videos"], list):
        errors.append("'videos' must be a list")
    else:
        for i, video in enumerate(checkpoint["videos"]):
            for field, expected_type in VIDEO_REQUIRED_FIELDS.items():
                if field not in video:
                    errors.append(f"videos[{i}]: missing field '{field}'")

    return errors
```

- [ ] **Step 4: Implement checkpoint write and read**

```python
# src/stage/checkpoint.py
"""Write and read JSON checkpoint files for the staging pipeline."""

import json
from datetime import datetime, timezone

from src.stage.schema import validate_checkpoint


def write_checkpoint(
    path: str,
    research_project: str,
    query_terms: list[str],
    research_criteria_version: str,
    videos: list[dict],
    included_only: bool = False,
) -> str:
    """Write a checkpoint file to disk.

    Args:
        path: Output file path.
        research_project: Name of the research project.
        query_terms: Search queries used.
        research_criteria_version: Version of the editorial policy used.
        videos: List of scored video metadata dicts.
        included_only: If True, only write videos where included=True.

    Returns:
        Path to the written file.

    Raises:
        ValueError: If the checkpoint data fails schema validation.
    """
    if included_only:
        videos = [v for v in videos if v.get("included")]

    checkpoint = {
        "metadata": {
            "research_project": research_project,
            "query_terms": query_terms,
            "research_criteria_version": research_criteria_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_candidates": len(videos) if not included_only else sum(1 for _ in videos),
            "total_included": sum(1 for v in videos if v.get("included")),
        },
        "videos": videos,
    }

    errors = validate_checkpoint(checkpoint)
    if errors:
        raise ValueError(f"Checkpoint validation failed: {'; '.join(errors)}")

    with open(path, "w") as f:
        json.dump(checkpoint, f, indent=2)

    return path


def read_checkpoint(path: str) -> dict:
    """Read and validate a checkpoint file from disk.

    Args:
        path: Path to checkpoint JSON file.

    Returns:
        Parsed and validated checkpoint dict.

    Raises:
        ValueError: If the file fails schema validation.
    """
    with open(path) as f:
        checkpoint = json.load(f)

    errors = validate_checkpoint(checkpoint)
    if errors:
        raise ValueError(f"Checkpoint validation failed: {'; '.join(errors)}")

    return checkpoint
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
source .venv/bin/activate
python -m pytest tests/test_checkpoint.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/stage/schema.py src/stage/checkpoint.py tests/test_checkpoint.py
git commit -m "Add JSON checkpoint staging with schema validation

write_checkpoint serializes scored videos to disk with metadata.
validate_checkpoint enforces the schema from project_prompt.json.
Supports included_only mode for writing only passing videos."
```

---

### Task 7: Pipeline Orchestrator and End-to-End Test

**Files:**
- Create: `src/pipeline.py`
- Create: `src/search/queries.py`

- [ ] **Step 1: Implement query expansion**

```python
# src/search/queries.py
"""Derive YouTube search queries from domain configuration."""

import yaml


def load_domain_queries(domain_path: str) -> list[str]:
    """Generate search queries from the domain config.

    Extracts the topic and key terms to produce a set of search queries
    that cover the domain from multiple angles.

    Args:
        domain_path: Path to domain config YAML.

    Returns:
        List of search query strings.
    """
    with open(domain_path) as f:
        domain = yaml.safe_load(f)

    topic = domain["domain"]["topic"]
    field = domain["domain"]["field"]

    # Core query is the topic itself
    queries = [topic]

    # Add field-qualified variant
    queries.append(f"{field} {topic}")

    return queries
```

- [ ] **Step 2: Implement the pipeline orchestrator**

```python
# src/pipeline.py
"""End-to-end pipeline orchestrator: search → filter → stage."""

import os
from datetime import datetime, timezone

from src.search.youtube import build_client, search_and_normalize
from src.search.queries import load_domain_queries
from src.filter.policy import load_merged_policy
from src.filter.semantic import build_filter_prompt, parse_filter_response, apply_scores
from src.stage.checkpoint import write_checkpoint


def run_search(
    api_key_path: str,
    domain_path: str,
    max_results_per_query: int = 50,
    skip_captions: bool = False,
) -> list[dict]:
    """Stage 1a: Search YouTube and return normalized video metadata.

    Args:
        api_key_path: Path to file containing YouTube API key.
        domain_path: Path to domain config YAML.
        max_results_per_query: Max results per search query.
        skip_captions: Skip caption checks to save API quota.

    Returns:
        List of normalized video metadata dicts.
    """
    with open(api_key_path) as f:
        api_key = f.read().strip()

    client = build_client(api_key)
    queries = load_domain_queries(domain_path)

    all_videos = []
    seen_ids = set()

    for query in queries:
        results = search_and_normalize(
            client, query, max_results_per_query, skip_captions=skip_captions
        )
        for video in results:
            if video["video_id"] not in seen_ids:
                seen_ids.add(video["video_id"])
                all_videos.append(video)

    return all_videos


def build_filter_context(
    template_path: str, domain_path: str, videos: list[dict]
) -> str:
    """Stage 1b: Build the filter prompt for Claude evaluation.

    Returns the prompt string. The actual Claude evaluation must happen
    outside this function (via Claude Code's reasoning).

    Args:
        template_path: Path to editorial_policy_template.yaml.
        domain_path: Path to domain config YAML.
        videos: Normalized video metadata from run_search().

    Returns:
        Formatted prompt string for Claude.
    """
    merged = load_merged_policy(template_path, domain_path)
    return build_filter_prompt(merged, videos)


def stage_results(
    videos: list[dict],
    research_project: str,
    query_terms: list[str],
    research_criteria_version: str,
    output_dir: str = "data/staged",
    included_only: bool = True,
) -> str:
    """Stage 2: Write scored videos to a checkpoint file.

    Args:
        videos: Scored video metadata (with relevance_score, etc.).
        research_project: Project name for the checkpoint.
        query_terms: Queries used in the search.
        research_criteria_version: Version of the editorial policy.
        output_dir: Directory for checkpoint files.
        included_only: Only write included videos.

    Returns:
        Path to the written checkpoint file.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{research_project}_{timestamp}.json"
    path = os.path.join(output_dir, filename)

    return write_checkpoint(
        path=path,
        research_project=research_project,
        query_terms=query_terms,
        research_criteria_version=research_criteria_version,
        videos=videos,
        included_only=included_only,
    )
```

- [ ] **Step 3: Commit**

```bash
git add src/pipeline.py src/search/queries.py
git commit -m "Add pipeline orchestrator and query expansion

run_search handles Stage 1a (YouTube search with dedup).
build_filter_context handles Stage 1b prompt construction.
stage_results handles Stage 2 (checkpoint file writing).
Query expansion derives search terms from domain config."
```

---

### Task 8: End-to-End Validation Script

**Files:**
- Create: `scripts/run_pipeline.py`

- [ ] **Step 1: Create the validation script**

This script runs the full pipeline interactively, pausing for Claude evaluation at Stage 1b.

```python
#!/usr/bin/env python3
"""Run the full Stage 1-2 pipeline.

Usage:
    python scripts/run_pipeline.py [--skip-captions] [--max-results N]

This script:
1. Searches YouTube using the domain config queries
2. Prints the filter prompt for Claude to evaluate
3. Reads Claude's response from stdin (paste JSON array)
4. Merges scores and writes the checkpoint file

The Claude evaluation step happens manually: copy the prompt output,
have Claude evaluate it, paste the JSON response back.
"""

import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import run_search, build_filter_context, stage_results
from src.filter.semantic import parse_filter_response, apply_scores
from src.filter.policy import load_policy


def main():
    parser = argparse.ArgumentParser(description="Run YouTube Research Pipeline Stages 1-2")
    parser.add_argument("--skip-captions", action="store_true", help="Skip caption checks (saves API quota)")
    parser.add_argument("--max-results", type=int, default=20, help="Max results per query (default: 20)")
    parser.add_argument("--api-key", default="config/youtube_api_key.txt", help="Path to API key file")
    parser.add_argument("--template", default="config/editorial_policy_template.yaml", help="Policy template path")
    parser.add_argument("--domain", default="config/domains/ai_temporal_video.yaml", help="Domain config path")
    args = parser.parse_args()

    # Stage 1a: Search
    print(f"=== Stage 1a: Searching YouTube (max {args.max_results} per query) ===")
    videos = run_search(
        api_key_path=args.api_key,
        domain_path=args.domain,
        max_results_per_query=args.max_results,
        skip_captions=args.skip_captions,
    )
    print(f"Found {len(videos)} unique videos.\n")

    if not videos:
        print("No videos found. Check your API key and search queries.")
        return

    # Stage 1b: Build filter prompt
    print("=== Stage 1b: Building filter prompt ===")
    prompt = build_filter_context(args.template, args.domain, videos)
    print(prompt)
    print("\n=== Paste Claude's JSON response below (Ctrl+D when done) ===\n")

    # Read Claude's response from stdin
    response_lines = []
    try:
        for line in sys.stdin:
            response_lines.append(line)
    except EOFError:
        pass
    response_text = "".join(response_lines)

    # Parse and merge scores
    scores = parse_filter_response(response_text)
    scored_videos = apply_scores(videos, scores)
    included = [v for v in scored_videos if v.get("included")]
    print(f"\n=== Scored {len(scored_videos)} videos, {len(included)} included ===\n")

    # Stage 2: Write checkpoint
    domain = load_policy(args.domain)
    version = domain.get("version", "unknown")
    queries = [domain["domain"]["topic"]]

    path = stage_results(
        videos=scored_videos,
        research_project="ai_temporal_video",
        query_terms=queries,
        research_criteria_version=version,
    )
    print(f"=== Checkpoint written to: {path} ===")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
mkdir -p scripts
git add scripts/run_pipeline.py
git commit -m "Add end-to-end pipeline validation script

Interactive script that runs Stages 1a-2. Pauses for Claude
evaluation at Stage 1b (paste JSON response via stdin)."
```

---

### Task 9: Update CLAUDE.md and Final Commit

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update project status**

Update the Status section in CLAUDE.md:

```
- Stage 0: Editorial policy — COMPLETE
- Stage 1a: YouTube search wrapper — COMPLETE
- Stage 1b: Semantic filter — COMPLETE
- Stage 2: JSON staging — COMPLETE
- Stages 3-7: Not implemented
```

Add to Environment section:

```
- Python 3.11+ in .venv (source .venv/bin/activate)
- Dependencies: google-api-python-client, PyYAML, pytest
- Tests: python -m pytest tests/ -v
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "Mark Stages 1a, 1b, and 2 complete"
```
