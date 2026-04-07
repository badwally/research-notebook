# Stage 6-7: Obsidian Knowledge Base & Semantic Tagging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform research artifacts from Stages 4-5 into an Obsidian-compatible knowledge base with four note types (source, concept, MOC, synthesis), wiki-links, and a corpus-derived tag taxonomy.

**Architecture:** Python modules read taxonomy.yaml, findings/*.json, synthesis.json, and checkpoint files. Each module generates one note type as .md files with YAML frontmatter and wiki-links. A tag extraction module derives tags from the research content. An orchestrator writes the complete vault to `data/obsidian/`.

**Tech Stack:** Python 3.9+, PyYAML, existing research artifacts, notebooklm-mcp-cli (for source ID mapping)

---

## Data Sources

- `data/research/taxonomy.yaml` — 5 branches with sub-branches and methods
- `data/research/findings/*.json` — 5 files, each with methods/comparisons/open_problems + citations
- `data/research/synthesis.json` — 3 themes with citations
- `data/staged/*.json` — video metadata (video_id, url, title, channel, duration, etc.)
- NotebookLM source list — maps NLM source IDs (in citations) to video titles

## File Structure

| File | Purpose |
|------|---------|
| `src/output/source_map.py` | Build NLM source ID → video metadata mapping |
| `src/output/tags.py` | Extract tags from taxonomy/findings, assign to notes |
| `src/output/source_notes.py` | Generate source notes (one per video) |
| `src/output/concept_notes.py` | Generate concept notes (one per method/architecture) |
| `src/output/moc_notes.py` | Generate MOC notes (one per taxonomy branch) |
| `src/output/synthesis_notes.py` | Generate synthesis notes (one per theme) |
| `src/output/vault.py` | Orchestrator: runs all generators |
| `tests/test_tags.py` | Tests for tag extraction |
| `tests/test_source_map.py` | Tests for source ID mapping |
| `scripts/run_vault.py` | CLI script to generate the vault |

---

### Task 1: Source ID Mapping (TDD)

**Files:**
- Create: `src/output/source_map.py`
- Create: `tests/test_source_map.py`
- Create: `src/output/__init__.py`

Citations in research findings reference NotebookLM source IDs (UUIDs). We need to map these back to video metadata for source note generation and citation links.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_source_map.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
source .venv/bin/activate
python -m pytest tests/test_source_map.py -v
```

Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implement source mapping**

```python
# src/output/__init__.py
```

```python
# src/output/source_map.py
"""Map NotebookLM source IDs to video metadata for citation resolution."""

import json
import subprocess


NLM_CMD = ["uvx", "--from", "notebooklm-mcp-cli", "nlm"]


def fetch_nlm_sources(notebook_id: str) -> list:
    """Fetch the source list from NotebookLM.

    Args:
        notebook_id: NotebookLM notebook ID.

    Returns:
        List of source dicts with id, title, type.
    """
    result = subprocess.run(
        NLM_CMD + ["source", "list", notebook_id, "--json"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch NLM sources: {result.stderr}")
    return json.loads(result.stdout)


def load_all_videos(checkpoint_paths: list) -> list:
    """Load all included videos from checkpoint files.

    Args:
        checkpoint_paths: List of paths to Stage 2 checkpoint JSON files.

    Returns:
        Deduplicated list of video metadata dicts.
    """
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
    """Build a mapping from NLM source ID to video metadata.

    Matches by title (exact match). NLM sources that don't match
    any video are silently skipped.

    Args:
        nlm_sources: List of NLM source dicts (id, title).
        videos: List of video metadata dicts (video_id, title, etc.).

    Returns:
        Dict mapping NLM source ID to video metadata.
    """
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
    """Resolve citation numbers to video metadata.

    Args:
        citations: Dict mapping citation number to NLM source ID.
        source_map: Dict mapping NLM source ID to video metadata.

    Returns:
        Dict mapping citation number to video metadata (or None if unresolved).
    """
    resolved = {}
    for num, nlm_id in citations.items():
        resolved[num] = source_map.get(nlm_id)
    return resolved
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
source .venv/bin/activate
python -m pytest tests/test_source_map.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/output/__init__.py src/output/source_map.py tests/test_source_map.py
git commit -m "Add source ID mapping for citation resolution

Maps NotebookLM source IDs to video metadata via title matching.
Resolves citation numbers in research findings to video_ids."
```

---

### Task 2: Tag Extraction (TDD)

**Files:**
- Create: `src/output/tags.py`
- Create: `tests/test_tags.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_tags.py
import pytest
from src.output.tags import extract_branch_tags, extract_tags_from_text, slugify_tag, build_tag_taxonomy


def test_slugify_tag():
    assert slugify_tag("Action Recognition & Classification") == "action-recognition-classification"
    assert slugify_tag("3D CNN") == "3d-cnn"
    assert slugify_tag("RNN/LSTM") == "rnn-lstm"


def test_extract_branch_tags():
    branches = [
        {"name": "Action Recognition & Classification"},
        {"name": "Video-Language Understanding & Grounding"},
    ]

    tags = extract_branch_tags(branches)

    assert "action-recognition-classification" in tags
    assert "video-language-understanding-grounding" in tags


def test_extract_tags_from_text():
    text = "This method uses a transformer architecture with self-supervised learning on 3D CNN features."

    tags = extract_tags_from_text(text)

    assert "transformer" in tags
    assert "self-supervised" in tags
    assert "cnn-3d" in tags


def test_build_tag_taxonomy():
    branches = [{"name": "Action Recognition", "sub_branches": [
        {"name": "Few-Shot Learning", "methods": ["STRM"]},
    ]}]
    findings = {"methods": {"answer": "Uses transformer and graph neural network architectures"}}

    taxonomy = build_tag_taxonomy(branches, [findings])

    assert "branch" in taxonomy
    assert "architecture" in taxonomy
    assert len(taxonomy["branch"]) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
source .venv/bin/activate
python -m pytest tests/test_tags.py -v
```

Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implement tag extraction**

```python
# src/output/tags.py
"""Extract and assign tags from research content. Tags are corpus-derived, not hardcoded."""

import re


# Architecture patterns to detect in text
ARCHITECTURE_PATTERNS = {
    "transformer": r"\btransformer\b",
    "graph-neural-network": r"\bgraph\s*(neural\s*network|convolutional|attention)\b",
    "cnn-3d": r"\b3d[\s-]?cnn\b|\bc3d\b|\bi3d\b|\bslowfast\b",
    "rnn-lstm": r"\b(rnn|lstm|recurrent)\b",
    "spiking-nn": r"\bspiking\s*(neural\s*network)?\b",
    "attention": r"\b(self-)?attention\s*mechanism\b|\battention-based\b",
    "detr": r"\bdetr\b",
}

# Task patterns to detect in text
TASK_PATTERNS = {
    "classification": r"\bclassif(ication|y)\b",
    "detection": r"\b(action\s*)?detection\b",
    "localization": r"\blocalization\b",
    "segmentation": r"\bsegmentation\b",
    "grounding": r"\bgrounding\b",
    "captioning": r"\bcaptioning\b",
    "tracking": r"\btrack(ing)?\b",
    "recognition": r"\brecognition\b",
}

# Learning paradigm patterns
PARADIGM_PATTERNS = {
    "supervised": r"\bsupervised\b(?!\s*self)",
    "self-supervised": r"\bself-supervised\b",
    "few-shot": r"\bfew-shot\b",
    "unsupervised": r"\bunsupervised\b",
}


def slugify_tag(text: str) -> str:
    """Convert a name to a lowercase hyphenated tag.

    Args:
        text: Raw name string.

    Returns:
        Slugified tag string.
    """
    text = text.lower()
    text = text.replace("&", "").replace("/", "-")
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def extract_branch_tags(branches: list) -> list:
    """Extract branch-level tags from taxonomy branches.

    Args:
        branches: List of branch dicts with name field.

    Returns:
        List of slugified branch tag strings.
    """
    return [slugify_tag(b["name"]) for b in branches]


def extract_tags_from_text(text: str) -> list:
    """Extract architecture, task, and paradigm tags from text content.

    Args:
        text: Research text to scan for tag patterns.

    Returns:
        List of matched tag strings.
    """
    text_lower = text.lower()
    tags = []

    for tag, pattern in ARCHITECTURE_PATTERNS.items():
        if re.search(pattern, text_lower):
            tags.append(tag)

    for tag, pattern in TASK_PATTERNS.items():
        if re.search(pattern, text_lower):
            tags.append(tag)

    for tag, pattern in PARADIGM_PATTERNS.items():
        if re.search(pattern, text_lower):
            tags.append(tag)

    return sorted(set(tags))


def build_tag_taxonomy(branches: list, findings_list: list) -> dict:
    """Build the complete tag taxonomy from research content.

    Args:
        branches: Taxonomy branches.
        findings_list: List of per-branch findings dicts.

    Returns:
        Dict with keys: branch, architecture, task, paradigm.
        Each maps to a list of tag strings found in the corpus.
    """
    branch_tags = extract_branch_tags(branches)

    # Scan all findings text for architecture/task/paradigm tags
    all_text = ""
    for f in findings_list:
        for section in ["methods", "comparisons", "open_problems"]:
            if section in f and isinstance(f[section], dict):
                all_text += " " + f[section].get("answer", "")

    all_tags = extract_tags_from_text(all_text)

    architecture_tags = [t for t in all_tags if t in ARCHITECTURE_PATTERNS]
    task_tags = [t for t in all_tags if t in TASK_PATTERNS]
    paradigm_tags = [t for t in all_tags if t in PARADIGM_PATTERNS]

    return {
        "branch": sorted(branch_tags),
        "architecture": sorted(architecture_tags),
        "task": sorted(task_tags),
        "paradigm": sorted(paradigm_tags),
    }


def generate_tags_doc(taxonomy: dict) -> str:
    """Generate the _tags.md documentation file content.

    Args:
        taxonomy: Tag taxonomy dict from build_tag_taxonomy.

    Returns:
        Markdown string for the tags documentation file.
    """
    lines = ["# Tag Taxonomy", ""]
    lines.append("Tags are derived from the corpus content. Different research domains produce different tags.")
    lines.append("")

    for category, tags in taxonomy.items():
        lines.append(f"## {category.title()} Tags")
        lines.append("")
        for tag in tags:
            lines.append(f"- `{tag}`")
        lines.append("")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
source .venv/bin/activate
python -m pytest tests/test_tags.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/output/tags.py tests/test_tags.py
git commit -m "Add corpus-derived tag extraction

Extracts branch, architecture, task, and paradigm tags from
research text via regex patterns. Tags are derived from content,
not hardcoded."
```

---

### Task 3: Source Note Generation

**Files:**
- Create: `src/output/source_notes.py`

- [ ] **Step 1: Implement source note generator**

```python
# src/output/source_notes.py
"""Generate Obsidian source notes — one per ingested video."""

import os
import yaml
from src.output.tags import extract_tags_from_text, slugify_tag


def generate_source_note(video: dict, branch_tag: str = None, cited_in_concepts: list = None) -> str:
    """Generate a single source note as markdown string.

    Args:
        video: Video metadata dict from checkpoint.
        branch_tag: Primary branch tag if known.
        cited_in_concepts: List of concept note names this source is cited in.

    Returns:
        Markdown string with YAML frontmatter and body.
    """
    tags = []
    if branch_tag:
        tags.append(branch_tag)
    tags.extend(extract_tags_from_text(video.get("title", "") + " " + video.get("description", "")))
    tags = sorted(set(tags))

    frontmatter = {
        "type": "source",
        "video_id": video["video_id"],
        "url": video["url"],
        "title": video["title"],
        "channel": video["channel_name"],
        "duration": video["duration"],
        "publish_date": video["publish_date"],
        "relevance_score": video.get("relevance_score", 0),
        "tags": tags,
    }

    lines = ["---"]
    lines.append(yaml.dump(frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True).strip())
    lines.append("---")
    lines.append("")
    lines.append(f"# {video['title']}")
    lines.append("")
    lines.append(f"**Channel:** {video['channel_name']}  ")
    lines.append(f"**Duration:** {video['duration']}  ")
    lines.append(f"**Views:** {video.get('view_count', 'N/A')}  ")
    lines.append(f"**Published:** {video['publish_date']}  ")
    lines.append(f"**URL:** {video['url']}")
    lines.append("")

    if video.get("description"):
        lines.append("## Description")
        lines.append("")
        lines.append(video["description"])
        lines.append("")

    if video.get("inclusion_rationale"):
        lines.append("## Relevance")
        lines.append("")
        lines.append(f"**Score:** {video.get('relevance_score', 'N/A')}/5  ")
        lines.append(f"{video['inclusion_rationale']}")
        lines.append("")

    if cited_in_concepts:
        lines.append("## Referenced In")
        lines.append("")
        for concept in cited_in_concepts:
            lines.append(f"- [[{concept}]]")
        lines.append("")

    return "\n".join(lines)


def write_source_notes(videos: list, output_dir: str, branch_tags: dict = None, citation_index: dict = None) -> list:
    """Write all source notes to disk.

    Args:
        videos: List of video metadata dicts.
        output_dir: Directory to write notes to (e.g., data/obsidian/sources/).
        branch_tags: Optional dict mapping video_id to branch tag.
        citation_index: Optional dict mapping video_id to list of concept names.

    Returns:
        List of written file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    for video in videos:
        vid = video["video_id"]
        branch_tag = branch_tags.get(vid) if branch_tags else None
        cited_in = citation_index.get(vid, []) if citation_index else []

        content = generate_source_note(video, branch_tag, cited_in)
        filename = f"{vid}.md"
        path = os.path.join(output_dir, filename)

        with open(path, "w") as f:
            f.write(content)
        paths.append(path)

    print(f"  Wrote {len(paths)} source notes to {output_dir}")
    return paths
```

- [ ] **Step 2: Verify all tests pass**

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

- [ ] **Step 3: Commit**

```bash
git add src/output/source_notes.py
git commit -m "Add source note generator for Obsidian vault

One .md file per video with YAML frontmatter, metadata,
description, relevance rationale, and concept back-links."
```

---

### Task 4: Concept Note Generation

**Files:**
- Create: `src/output/concept_notes.py`

- [ ] **Step 1: Implement concept note generator**

```python
# src/output/concept_notes.py
"""Generate Obsidian concept notes — one per method/architecture/technique."""

import os
import re
import yaml
from src.output.tags import extract_tags_from_text, slugify_tag


def extract_concepts(taxonomy: dict) -> list:
    """Extract atomic concepts from taxonomy methods and sub-branches.

    Args:
        taxonomy: Parsed taxonomy.yaml dict.

    Returns:
        List of concept dicts with name, branch, sub_branch, concept_type.
    """
    concepts = []
    for branch in taxonomy.get("branches", []):
        for sub in branch.get("sub_branches", []):
            # Each sub-branch is a technique/approach concept
            concepts.append({
                "name": sub["name"],
                "description": sub.get("description", ""),
                "branch": branch["name"],
                "concept_type": "technique",
                "methods": sub.get("methods", []),
            })
            # Each method is a specific method concept
            for method_raw in sub.get("methods", []):
                # Strip citation references like [2] or [7, 11]
                method_name = re.sub(r"\s*\[[\d,\s]+\]", "", method_raw).strip()
                concepts.append({
                    "name": method_name,
                    "description": "",
                    "branch": branch["name"],
                    "sub_branch": sub["name"],
                    "concept_type": "method",
                    "methods": [],
                })
    return concepts


def generate_concept_note(
    concept: dict,
    findings_text: str = "",
    source_ids: list = None,
    related_concepts: list = None,
) -> str:
    """Generate a single concept note as markdown string.

    Args:
        concept: Concept dict from extract_concepts.
        findings_text: Relevant text from research findings about this concept.
        source_ids: List of video_ids that discuss this concept.
        related_concepts: List of related concept names for cross-linking.

    Returns:
        Markdown string with YAML frontmatter and body.
    """
    tags = [slugify_tag(concept["branch"])]
    tags.extend(extract_tags_from_text(
        concept["name"] + " " + concept.get("description", "") + " " + findings_text
    ))
    tags = sorted(set(tags))

    frontmatter = {
        "type": "concept",
        "concept_type": concept["concept_type"],
        "related_branches": [concept["branch"]],
        "tags": tags,
    }

    lines = ["---"]
    lines.append(yaml.dump(frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True).strip())
    lines.append("---")
    lines.append("")
    lines.append(f"# {concept['name']}")
    lines.append("")

    if concept.get("description"):
        lines.append(concept["description"])
        lines.append("")

    lines.append(f"**Branch:** [[{slugify_tag(concept['branch'])}|{concept['branch']}]]")
    if concept.get("sub_branch"):
        lines.append(f"**Sub-branch:** [[{slugify_tag(concept['sub_branch'])}|{concept['sub_branch']}]]")
    lines.append("")

    if findings_text:
        lines.append("## Research Findings")
        lines.append("")
        lines.append(findings_text)
        lines.append("")

    if concept.get("methods"):
        lines.append("## Methods")
        lines.append("")
        for m in concept["methods"]:
            method_name = re.sub(r"\s*\[[\d,\s]+\]", "", m).strip()
            lines.append(f"- [[{slugify_tag(method_name)}|{method_name}]]")
        lines.append("")

    if source_ids:
        lines.append("## Sources")
        lines.append("")
        for vid in source_ids:
            lines.append(f"- [[{vid}]]")
        lines.append("")

    if related_concepts:
        lines.append("## Related Concepts")
        lines.append("")
        for rc in related_concepts:
            lines.append(f"- [[{slugify_tag(rc)}|{rc}]]")
        lines.append("")

    return "\n".join(lines)


def write_concept_notes(concepts: list, output_dir: str, findings_map: dict = None) -> list:
    """Write all concept notes to disk.

    Args:
        concepts: List of concept dicts from extract_concepts.
        output_dir: Directory to write notes to.
        findings_map: Optional dict mapping concept name to findings text.

    Returns:
        List of written file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    for concept in concepts:
        findings_text = ""
        if findings_map:
            findings_text = findings_map.get(concept["name"], "")

        content = generate_concept_note(concept, findings_text)
        filename = f"{slugify_tag(concept['name'])}.md"
        path = os.path.join(output_dir, filename)

        with open(path, "w") as f:
            f.write(content)
        paths.append(path)

    print(f"  Wrote {len(paths)} concept notes to {output_dir}")
    return paths
```

- [ ] **Step 2: Verify all tests pass**

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

- [ ] **Step 3: Commit**

```bash
git add src/output/concept_notes.py
git commit -m "Add concept note generator for Obsidian vault

Extracts atomic concepts from taxonomy. Generates .md files
with frontmatter, branch links, method links, and source refs."
```

---

### Task 5: MOC and Synthesis Note Generation

**Files:**
- Create: `src/output/moc_notes.py`
- Create: `src/output/synthesis_notes.py`

- [ ] **Step 1: Implement MOC note generator**

```python
# src/output/moc_notes.py
"""Generate Obsidian MOC (Map of Content) notes — one per taxonomy branch."""

import os
import re
import yaml
from src.output.tags import slugify_tag


def generate_moc_note(branch: dict, findings: dict = None) -> str:
    """Generate a MOC note for a taxonomy branch.

    Args:
        branch: Branch dict from taxonomy with name, description, sub_branches.
        findings: Findings dict for this branch (methods, comparisons, open_problems).

    Returns:
        Markdown string with YAML frontmatter and body.
    """
    branch_tag = slugify_tag(branch["name"])

    frontmatter = {
        "type": "moc",
        "branch": branch["name"],
        "tags": [branch_tag],
    }

    lines = ["---"]
    lines.append(yaml.dump(frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True).strip())
    lines.append("---")
    lines.append("")
    lines.append(f"# {branch['name']}")
    lines.append("")

    if branch.get("description"):
        lines.append(branch["description"])
        lines.append("")

    # Sub-branches with concept links
    for sub in branch.get("sub_branches", []):
        lines.append(f"## {sub['name']}")
        lines.append("")
        if sub.get("description"):
            lines.append(sub["description"])
            lines.append("")
        lines.append(f"**Concept:** [[{slugify_tag(sub['name'])}|{sub['name']}]]")
        lines.append("")
        if sub.get("methods"):
            lines.append("**Methods:**")
            for m in sub["methods"]:
                method_name = re.sub(r"\s*\[[\d,\s]+\]", "", m).strip()
                lines.append(f"- [[{slugify_tag(method_name)}|{method_name}]]")
            lines.append("")

    # Open problems from findings
    if findings and "open_problems" in findings:
        answer = findings["open_problems"].get("answer", "")
        if answer:
            lines.append("## Open Problems")
            lines.append("")
            lines.append(answer)
            lines.append("")

    return "\n".join(lines)


def write_moc_notes(branches: list, output_dir: str, findings_map: dict = None) -> list:
    """Write all MOC notes to disk.

    Args:
        branches: List of taxonomy branch dicts.
        output_dir: Directory to write notes to.
        findings_map: Optional dict mapping branch name to findings dict.

    Returns:
        List of written file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    for branch in branches:
        findings = findings_map.get(branch["name"]) if findings_map else None
        content = generate_moc_note(branch, findings)
        filename = f"{slugify_tag(branch['name'])}.md"
        path = os.path.join(output_dir, filename)

        with open(path, "w") as f:
            f.write(content)
        paths.append(path)

    print(f"  Wrote {len(paths)} MOC notes to {output_dir}")
    return paths
```

- [ ] **Step 2: Implement synthesis note generator**

```python
# src/output/synthesis_notes.py
"""Generate Obsidian synthesis notes — one per cross-cutting theme."""

import os
import yaml
from src.output.tags import extract_tags_from_text, slugify_tag


THEME_NAMES = {
    "shared_architectures": "Shared Architectures",
    "common_datasets": "Common Datasets",
    "recurring_tradeoffs": "Recurring Trade-offs",
}


def generate_synthesis_note(theme_key: str, theme_data: dict, branch_names: list) -> str:
    """Generate a synthesis note for a cross-cutting theme.

    Args:
        theme_key: Key from synthesis.json (e.g., "shared_architectures").
        theme_data: Theme dict with answer, citations, sources_used.
        branch_names: List of all branch names for related_branches.

    Returns:
        Markdown string with YAML frontmatter and body.
    """
    theme_name = THEME_NAMES.get(theme_key, theme_key.replace("_", " ").title())
    answer = theme_data.get("answer", "")

    tags = extract_tags_from_text(answer)
    tags = sorted(set(tags))

    frontmatter = {
        "type": "synthesis",
        "theme": theme_name,
        "related_branches": branch_names,
        "tags": tags,
    }

    lines = ["---"]
    lines.append(yaml.dump(frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True).strip())
    lines.append("---")
    lines.append("")
    lines.append(f"# {theme_name}")
    lines.append("")
    lines.append("*Cross-cutting analysis across all research branches.*")
    lines.append("")

    # Branch links
    lines.append("## Related Branches")
    lines.append("")
    for name in branch_names:
        lines.append(f"- [[{slugify_tag(name)}|{name}]]")
    lines.append("")

    # Main content
    if answer:
        lines.append("## Analysis")
        lines.append("")
        lines.append(answer)
        lines.append("")

    return "\n".join(lines)


def write_synthesis_notes(synthesis: dict, output_dir: str, branch_names: list) -> list:
    """Write all synthesis notes to disk.

    Args:
        synthesis: Parsed synthesis.json dict.
        output_dir: Directory to write notes to.
        branch_names: List of all taxonomy branch names.

    Returns:
        List of written file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    for theme_key, theme_data in synthesis.items():
        if not isinstance(theme_data, dict):
            continue
        content = generate_synthesis_note(theme_key, theme_data, branch_names)
        filename = f"{slugify_tag(THEME_NAMES.get(theme_key, theme_key))}.md"
        path = os.path.join(output_dir, filename)

        with open(path, "w") as f:
            f.write(content)
        paths.append(path)

    print(f"  Wrote {len(paths)} synthesis notes to {output_dir}")
    return paths
```

- [ ] **Step 3: Verify all tests pass**

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

- [ ] **Step 4: Commit**

```bash
git add src/output/moc_notes.py src/output/synthesis_notes.py
git commit -m "Add MOC and synthesis note generators

MOC notes link to concept notes and include open problems.
Synthesis notes bridge across branches with cross-cutting analysis."
```

---

### Task 6: Vault Orchestrator

**Files:**
- Create: `src/output/vault.py`
- Create: `scripts/run_vault.py`

- [ ] **Step 1: Implement the vault orchestrator**

```python
# src/output/vault.py
"""Orchestrate full Obsidian vault generation from research artifacts."""

import glob
import json
import os
import yaml

from src.output.source_map import fetch_nlm_sources, load_all_videos, build_source_map
from src.output.tags import build_tag_taxonomy, generate_tags_doc
from src.output.source_notes import write_source_notes
from src.output.concept_notes import extract_concepts, write_concept_notes
from src.output.moc_notes import write_moc_notes
from src.output.synthesis_notes import write_synthesis_notes


def generate_vault(
    notebook_id: str,
    taxonomy_path: str = "data/research/taxonomy.yaml",
    findings_dir: str = "data/research/findings",
    synthesis_path: str = "data/research/synthesis.json",
    checkpoint_dir: str = "data/staged",
    output_dir: str = "data/obsidian",
) -> dict:
    """Generate the complete Obsidian vault from research artifacts.

    Args:
        notebook_id: NotebookLM notebook ID (for source mapping).
        taxonomy_path: Path to taxonomy YAML.
        findings_dir: Directory containing per-branch findings JSON files.
        synthesis_path: Path to synthesis JSON.
        checkpoint_dir: Directory containing Stage 2 checkpoint files.
        output_dir: Root directory for the Obsidian vault.

    Returns:
        Summary dict with counts of generated notes.
    """
    print("Generating Obsidian vault...")

    # Load research artifacts
    with open(taxonomy_path) as f:
        taxonomy = yaml.safe_load(f)
    branches = taxonomy.get("branches", [])
    branch_names = [b["name"] for b in branches]

    # Load findings
    findings_map = {}
    for fpath in sorted(glob.glob(os.path.join(findings_dir, "*.json"))):
        with open(fpath) as f:
            finding = json.load(f)
        findings_map[finding["branch"]] = finding

    # Load synthesis
    with open(synthesis_path) as f:
        synthesis = json.load(f)

    # Load videos from checkpoints
    checkpoint_paths = sorted(glob.glob(os.path.join(checkpoint_dir, "*.json")))
    videos = load_all_videos(checkpoint_paths)

    # Build source map (NLM source ID → video metadata)
    print("  Building source map...")
    nlm_sources = fetch_nlm_sources(notebook_id)
    source_map = build_source_map(nlm_sources, videos)
    print(f"  Mapped {len(source_map)}/{len(nlm_sources)} NLM sources to videos")

    # Build tag taxonomy
    print("  Extracting tags from corpus...")
    tag_taxonomy = build_tag_taxonomy(branches, list(findings_map.values()))

    # Write _tags.md
    tags_path = os.path.join(output_dir, "_tags.md")
    os.makedirs(output_dir, exist_ok=True)
    with open(tags_path, "w") as f:
        f.write(generate_tags_doc(tag_taxonomy))
    print(f"  Tag taxonomy written to {tags_path}")

    # Generate source notes
    print("\n  Generating source notes...")
    source_paths = write_source_notes(
        videos,
        os.path.join(output_dir, "sources"),
    )

    # Generate concept notes
    print("  Generating concept notes...")
    concepts = extract_concepts(taxonomy)
    concept_paths = write_concept_notes(
        concepts,
        os.path.join(output_dir, "concepts"),
    )

    # Generate MOC notes
    print("  Generating MOC notes...")
    moc_paths = write_moc_notes(
        branches,
        os.path.join(output_dir, "mocs"),
        findings_map,
    )

    # Generate synthesis notes
    print("  Generating synthesis notes...")
    synthesis_paths = write_synthesis_notes(
        synthesis,
        os.path.join(output_dir, "synthesis"),
        branch_names,
    )

    summary = {
        "source_notes": len(source_paths),
        "concept_notes": len(concept_paths),
        "moc_notes": len(moc_paths),
        "synthesis_notes": len(synthesis_paths),
        "total": len(source_paths) + len(concept_paths) + len(moc_paths) + len(synthesis_paths) + 1,
    }

    print(f"\n  Vault generated: {summary['total']} notes total")
    print(f"    Sources: {summary['source_notes']}")
    print(f"    Concepts: {summary['concept_notes']}")
    print(f"    MOCs: {summary['moc_notes']}")
    print(f"    Synthesis: {summary['synthesis_notes']}")
    print(f"    Tags doc: 1")

    return summary
```

- [ ] **Step 2: Create the CLI script**

```python
#!/usr/bin/env python3
"""Generate the Obsidian knowledge base from research artifacts.

Usage:
    python scripts/run_vault.py <notebook_id>
    python scripts/run_vault.py 8d7b55c9-907f-4e70-8e08-2514e4a5e2d2
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.output.vault import generate_vault


def main():
    parser = argparse.ArgumentParser(description="Generate Obsidian vault from research artifacts")
    parser.add_argument("notebook_id", help="NotebookLM notebook ID")
    parser.add_argument("--output-dir", default="data/obsidian", help="Output directory for vault")
    args = parser.parse_args()

    summary = generate_vault(args.notebook_id, output_dir=args.output_dir)

    print(f"\nVault ready at: {args.output_dir}/")
    print("Open in Obsidian to view graph.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Make executable and verify**

```bash
chmod +x scripts/run_vault.py
source .venv/bin/activate
python scripts/run_vault.py --help
```

- [ ] **Step 4: Commit**

```bash
git add src/output/vault.py scripts/run_vault.py
git commit -m "Add vault orchestrator and CLI script

Generates complete Obsidian vault: source notes, concept notes,
MOC notes, synthesis notes, and tag taxonomy documentation."
```

---

### Task 7: End-to-End Vault Generation and Status Update

This task is operational — run the vault generator and verify output.

- [ ] **Step 1: Generate the vault**

```bash
source .venv/bin/activate
python scripts/run_vault.py 8d7b55c9-907f-4e70-8e08-2514e4a5e2d2
```

- [ ] **Step 2: Verify output structure**

```bash
ls data/obsidian/
ls data/obsidian/sources/ | wc -l
ls data/obsidian/concepts/ | wc -l
ls data/obsidian/mocs/
ls data/obsidian/synthesis/
cat data/obsidian/_tags.md
head -30 data/obsidian/mocs/*.md | head -60
head -30 data/obsidian/concepts/*.md | head -60
```

Verify:
- `_tags.md` exists with corpus-derived tags
- sources/ has ~86 .md files
- concepts/ has notes for each method and technique
- mocs/ has 5 files (one per branch)
- synthesis/ has 3 files (shared architectures, common datasets, recurring trade-offs)
- Frontmatter has proper YAML with tags
- Wiki-links use `[[slug|Display Name]]` format

- [ ] **Step 3: Update CLAUDE.md**

Update the Status section:

```
- Stage 6-7: Obsidian vault — COMPLETE
```

```bash
git add CLAUDE.md
git commit -m "Mark Stage 6-7 (Obsidian vault) complete — all stages done"
```
