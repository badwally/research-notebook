# Stage 4-5: Corpus Research Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Query the NotebookLM corpus systematically to extract the field's taxonomy, investigate each branch, and synthesize cross-cutting themes — producing structured research artifacts ready for Obsidian conversion.

**Architecture:** Three-phase research pipeline (taxonomy → investigation → synthesis) using `nlm notebook query` CLI via subprocess. A shared query execution layer handles CLI calls, retries, and citation parsing. Each phase has its own module with query templates. All output goes to `data/research/`.

**Tech Stack:** Python 3.9+, notebooklm-mcp-cli (nlm CLI), PyYAML, existing subprocess patterns from `src/ingest/notebooklm.py`

---

## Constants

Notebook ID: `8d7b55c9-907f-4e70-8e08-2514e4a5e2d2`

---

## File Structure

| File | Purpose |
|------|---------|
| `src/research/query.py` | Shared query execution: run nlm queries, parse responses, handle retries |
| `src/research/taxonomy.py` | Phase 1: extract field taxonomy from corpus |
| `src/research/investigate.py` | Phase 2: per-branch structured investigation |
| `src/research/synthesize.py` | Phase 3: cross-cutting theme synthesis |
| `tests/test_query.py` | Tests for query response parsing |
| `scripts/run_research.py` | Orchestrator: runs all three phases |

---

### Task 1: Query Execution Layer (TDD)

**Files:**
- Create: `src/research/query.py`
- Create: `src/research/__init__.py`
- Create: `tests/test_query.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_query.py
import json
import pytest
from src.research.query import parse_query_response


def test_parse_query_response_extracts_answer_and_citations():
    raw = {
        "value": {
            "answer": "TCNs are faster than transformers.",
            "conversation_id": "conv123",
            "sources_used": ["src1", "src2"],
            "citations": {"1": "src1", "2": "src2"},
        }
    }

    result = parse_query_response(raw)

    assert result["answer"] == "TCNs are faster than transformers."
    assert result["citations"] == {"1": "src1", "2": "src2"}
    assert result["sources_used"] == ["src1", "src2"]


def test_parse_query_response_handles_missing_citations():
    raw = {
        "value": {
            "answer": "No sources found.",
            "conversation_id": "conv123",
            "sources_used": [],
        }
    }

    result = parse_query_response(raw)

    assert result["answer"] == "No sources found."
    assert result["citations"] == {}
    assert result["sources_used"] == []


def test_parse_query_response_handles_empty_answer():
    raw = {
        "value": {
            "answer": "",
            "conversation_id": "conv123",
            "sources_used": [],
        }
    }

    result = parse_query_response(raw)

    assert result["answer"] == ""
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
source .venv/bin/activate
python -m pytest tests/test_query.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement the query execution layer**

```python
# src/research/__init__.py
```

```python
# src/research/query.py
"""Shared query execution layer for NotebookLM corpus research."""

import json
import subprocess

NLM_CMD = ["uvx", "--from", "notebooklm-mcp-cli", "nlm"]


def _run_nlm(args: list, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run an nlm CLI command and return the result."""
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


def parse_query_response(raw: dict) -> dict:
    """Parse the raw nlm query response into a clean research result.

    Args:
        raw: Parsed JSON from nlm notebook query output.

    Returns:
        Dict with answer, citations, and sources_used.
    """
    value = raw.get("value", raw)
    return {
        "answer": value.get("answer", ""),
        "citations": value.get("citations", {}),
        "sources_used": value.get("sources_used", []),
    }


def query_notebook(notebook_id: str, question: str, max_retries: int = 2) -> dict:
    """Query the NotebookLM corpus and return parsed results.

    Args:
        notebook_id: NotebookLM notebook ID.
        question: Research question to ask.
        max_retries: Number of attempts (1 retry by default).

    Returns:
        Parsed query result with answer, citations, sources_used.

    Raises:
        RuntimeError: If all retries fail.
    """
    for attempt in range(max_retries):
        try:
            result = _run_nlm(
                ["notebook", "query", notebook_id, question],
                timeout=120,
            )
            raw = json.loads(result.stdout)
            return parse_query_response(raw)
        except (RuntimeError, json.JSONDecodeError) as e:
            if attempt < max_retries - 1:
                print(f"  Query retry {attempt + 1}: {str(e)[:80]}")
                continue
            raise RuntimeError(f"Query failed after {max_retries} attempts: {e}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
source .venv/bin/activate
python -m pytest tests/test_query.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/research/__init__.py src/research/query.py tests/test_query.py
git commit -m "Add query execution layer for corpus research

parse_query_response extracts answer and citations.
query_notebook runs nlm queries with retry."
```

---

### Task 2: Taxonomy Extraction

**Files:**
- Create: `src/research/taxonomy.py`

- [ ] **Step 1: Implement taxonomy extraction**

```python
# src/research/taxonomy.py
"""Phase 1: Extract field taxonomy from the NotebookLM corpus."""

import os
import yaml
from src.research.query import query_notebook


TAXONOMY_PROMPT = """Analyze all sources in this notebook and identify the major research areas, method categories, and architectural families discussed.

Organize your response as a structured hierarchy with these levels:
1. Top-level research areas (e.g., "Temporal Action Detection", "Video Object Tracking")
2. For each area, list the sub-categories or method families
3. For each sub-category, name 1-3 specific methods or papers discussed in the sources

Format your response as a structured list using this exact pattern for each area:

AREA: [area name]
DESCRIPTION: [1-2 sentence description]
  SUB: [sub-category name]
  DESCRIPTION: [1 sentence description]
    METHOD: [specific method name]
    METHOD: [specific method name]
  SUB: [sub-category name]
  DESCRIPTION: [1 sentence description]
    METHOD: [specific method name]

Cover ALL major areas discussed in the sources. Be comprehensive."""


def extract_taxonomy(notebook_id: str) -> dict:
    """Query corpus for field structure and parse into taxonomy dict.

    Args:
        notebook_id: NotebookLM notebook ID.

    Returns:
        Taxonomy dict with field name, branches, and citations.
    """
    print("Phase 1: Extracting taxonomy from corpus...")
    result = query_notebook(notebook_id, TAXONOMY_PROMPT)

    branches = _parse_taxonomy_response(result["answer"])

    return {
        "field": "AI for Longitudinal Temporal Video Analysis",
        "branches": branches,
        "citations": result["citations"],
        "sources_used": result["sources_used"],
    }


def _parse_taxonomy_response(answer: str) -> list:
    """Parse the structured taxonomy response into a list of branches.

    Args:
        answer: NotebookLM's structured response text.

    Returns:
        List of branch dicts with name, description, and sub_branches.
    """
    branches = []
    current_branch = None
    current_sub = None

    for line in answer.split("\n"):
        line = line.strip()
        if not line:
            continue

        if line.startswith("AREA:"):
            if current_branch:
                if current_sub:
                    current_branch["sub_branches"].append(current_sub)
                    current_sub = None
                branches.append(current_branch)
            current_branch = {
                "name": line.split(":", 1)[1].strip().strip("*"),
                "description": "",
                "sub_branches": [],
            }
        elif line.startswith("DESCRIPTION:") and current_branch:
            desc = line.split(":", 1)[1].strip()
            if current_sub:
                current_sub["description"] = desc
            else:
                current_branch["description"] = desc
        elif line.startswith("SUB:") and current_branch:
            if current_sub:
                current_branch["sub_branches"].append(current_sub)
            current_sub = {
                "name": line.split(":", 1)[1].strip().strip("*"),
                "description": "",
                "methods": [],
            }
        elif line.startswith("METHOD:") and current_sub:
            current_sub["methods"].append(line.split(":", 1)[1].strip())

    # Flush remaining
    if current_sub and current_branch:
        current_branch["sub_branches"].append(current_sub)
    if current_branch:
        branches.append(current_branch)

    return branches


def save_taxonomy(taxonomy: dict, path: str) -> str:
    """Write taxonomy to YAML file.

    Args:
        taxonomy: Taxonomy dict from extract_taxonomy.
        path: Output file path.

    Returns:
        Path to written file.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(taxonomy, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    print(f"  Taxonomy saved to {path}")
    return path
```

- [ ] **Step 2: Verify all tests pass**

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

Expected: All 16 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add src/research/taxonomy.py
git commit -m "Add taxonomy extraction from NotebookLM corpus

Queries corpus for field structure, parses structured response
into branch hierarchy, saves as YAML."
```

---

### Task 3: Per-Branch Investigation

**Files:**
- Create: `src/research/investigate.py`

- [ ] **Step 1: Implement per-branch investigation**

```python
# src/research/investigate.py
"""Phase 2: Per-branch structured investigation of the corpus."""

import json
import os
from src.research.query import query_notebook


METHODS_TEMPLATE = """For the research area "{branch_name}" ({branch_description}), what specific methods and architectures are discussed in the sources? For each method, describe:
- Its name and key contribution
- The core technical approach
- Any reported benchmark results

Be specific and cite sources."""

COMPARISONS_TEMPLATE = """For the research area "{branch_name}", how do the different methods compare? Consider:
- Accuracy and performance differences
- Computational efficiency and speed
- Scalability to longer videos or larger datasets
- Strengths and weaknesses of each approach

Be specific about which methods you are comparing and cite sources."""

OPEN_PROBLEMS_TEMPLATE = """For the research area "{branch_name}", what unsolved problems, limitations, or future research directions are identified in the sources? What gaps remain? What challenges do current methods still face?

Be specific and cite sources."""


def investigate_branch(notebook_id: str, branch: dict) -> dict:
    """Run structured queries for a single taxonomy branch.

    Args:
        notebook_id: NotebookLM notebook ID.
        branch: Branch dict with name and description.

    Returns:
        Findings dict with methods, comparisons, and open_problems.
    """
    name = branch["name"]
    desc = branch.get("description", name)
    print(f"  Investigating: {name}")

    findings = {"branch": name}

    # Methods query
    print(f"    Querying methods...")
    try:
        methods = query_notebook(
            notebook_id,
            METHODS_TEMPLATE.format(branch_name=name, branch_description=desc),
        )
        findings["methods"] = methods
    except RuntimeError as e:
        print(f"    Methods query failed: {str(e)[:80]}")
        findings["methods"] = {"answer": "", "citations": {}, "sources_used": [], "error": str(e)}

    # Comparisons query
    print(f"    Querying comparisons...")
    try:
        comparisons = query_notebook(
            notebook_id,
            COMPARISONS_TEMPLATE.format(branch_name=name),
        )
        findings["comparisons"] = comparisons
    except RuntimeError as e:
        print(f"    Comparisons query failed: {str(e)[:80]}")
        findings["comparisons"] = {"answer": "", "citations": {}, "sources_used": [], "error": str(e)}

    # Open problems query
    print(f"    Querying open problems...")
    try:
        open_problems = query_notebook(
            notebook_id,
            OPEN_PROBLEMS_TEMPLATE.format(branch_name=name),
        )
        findings["open_problems"] = open_problems
    except RuntimeError as e:
        print(f"    Open problems query failed: {str(e)[:80]}")
        findings["open_problems"] = {"answer": "", "citations": {}, "sources_used": [], "error": str(e)}

    return findings


def save_findings(findings: dict, output_dir: str) -> str:
    """Write per-branch findings to JSON file.

    Args:
        findings: Findings dict from investigate_branch.
        output_dir: Directory for findings files.

    Returns:
        Path to written file.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = findings["branch"].lower().replace(" ", "_").replace("/", "_") + ".json"
    path = os.path.join(output_dir, filename)

    with open(path, "w") as f:
        json.dump(findings, f, indent=2)

    print(f"    Saved to {path}")
    return path
```

- [ ] **Step 2: Verify all tests pass**

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

Expected: All 16 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add src/research/investigate.py
git commit -m "Add per-branch investigation module

Three structured queries per branch: methods, comparisons,
and open problems. Each with citation preservation."
```

---

### Task 4: Cross-Cutting Synthesis

**Files:**
- Create: `src/research/synthesize.py`

- [ ] **Step 1: Implement synthesis module**

```python
# src/research/synthesize.py
"""Phase 3: Cross-cutting synthesis across taxonomy branches."""

import json
import os
from src.research.query import query_notebook


SHARED_ARCHITECTURES_PROMPT = """Looking across ALL research areas in this corpus, what architectures or techniques appear in multiple sub-fields? For example, do transformers appear in both action detection and video captioning? Do graph neural networks appear in both tracking and action recognition?

Identify the cross-cutting architectures and explain how they are adapted for different tasks. Cite sources."""

COMMON_DATASETS_PROMPT = """What benchmark datasets are referenced across multiple research areas in this corpus? For each dataset, describe:
- What it contains (video types, annotations)
- Which research areas use it
- Why it is considered important

Cite sources."""

RECURRING_TRADEOFFS_PROMPT = """What fundamental trade-offs recur across different methods and research areas in this corpus? Consider:
- Accuracy vs computational efficiency
- Local temporal modeling vs global temporal modeling
- Supervised vs self-supervised approaches
- Model complexity vs generalization
- Real-time capability vs offline accuracy

For each trade-off, give specific examples from different research areas. Cite sources."""


def synthesize_themes(notebook_id: str, taxonomy: dict) -> dict:
    """Run cross-cutting synthesis queries across the full corpus.

    Args:
        notebook_id: NotebookLM notebook ID.
        taxonomy: Taxonomy dict (used for context, not directly queried).

    Returns:
        Synthesis dict with shared_architectures, common_datasets, recurring_tradeoffs.
    """
    print("Phase 3: Synthesizing cross-cutting themes...")
    synthesis = {}

    # Shared architectures
    print("  Querying shared architectures...")
    try:
        synthesis["shared_architectures"] = query_notebook(notebook_id, SHARED_ARCHITECTURES_PROMPT)
    except RuntimeError as e:
        print(f"  Failed: {str(e)[:80]}")
        synthesis["shared_architectures"] = {"answer": "", "citations": {}, "sources_used": [], "error": str(e)}

    # Common datasets
    print("  Querying common datasets...")
    try:
        synthesis["common_datasets"] = query_notebook(notebook_id, COMMON_DATASETS_PROMPT)
    except RuntimeError as e:
        print(f"  Failed: {str(e)[:80]}")
        synthesis["common_datasets"] = {"answer": "", "citations": {}, "sources_used": [], "error": str(e)}

    # Recurring trade-offs
    print("  Querying recurring trade-offs...")
    try:
        synthesis["recurring_tradeoffs"] = query_notebook(notebook_id, RECURRING_TRADEOFFS_PROMPT)
    except RuntimeError as e:
        print(f"  Failed: {str(e)[:80]}")
        synthesis["recurring_tradeoffs"] = {"answer": "", "citations": {}, "sources_used": [], "error": str(e)}

    return synthesis


def save_synthesis(synthesis: dict, path: str) -> str:
    """Write synthesis results to JSON file.

    Args:
        synthesis: Synthesis dict from synthesize_themes.
        path: Output file path.

    Returns:
        Path to written file.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(synthesis, f, indent=2)
    print(f"  Synthesis saved to {path}")
    return path
```

- [ ] **Step 2: Verify all tests pass**

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

Expected: All 16 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add src/research/synthesize.py
git commit -m "Add cross-cutting synthesis module

Three synthesis queries: shared architectures, common datasets,
and recurring trade-offs across the full corpus."
```

---

### Task 5: Research Orchestrator Script

**Files:**
- Create: `scripts/run_research.py`

- [ ] **Step 1: Create the orchestrator**

```python
#!/usr/bin/env python3
"""Run the full corpus research pipeline: taxonomy → investigation → synthesis.

Usage:
    python scripts/run_research.py <notebook_id>
    python scripts/run_research.py 8d7b55c9-907f-4e70-8e08-2514e4a5e2d2

Output is written to data/research/:
  - taxonomy.yaml
  - findings/{branch_name}.json (one per branch)
  - synthesis.json
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.research.taxonomy import extract_taxonomy, save_taxonomy
from src.research.investigate import investigate_branch, save_findings
from src.research.synthesize import synthesize_themes, save_synthesis


def main():
    parser = argparse.ArgumentParser(description="Run corpus research pipeline")
    parser.add_argument("notebook_id", help="NotebookLM notebook ID")
    parser.add_argument("--output-dir", default="data/research", help="Output directory")
    parser.add_argument("--skip-taxonomy", action="store_true", help="Skip taxonomy extraction (use existing)")
    args = parser.parse_args()

    output_dir = args.output_dir
    taxonomy_path = os.path.join(output_dir, "taxonomy.yaml")
    findings_dir = os.path.join(output_dir, "findings")
    synthesis_path = os.path.join(output_dir, "synthesis.json")

    # Phase 1: Taxonomy
    if args.skip_taxonomy and os.path.exists(taxonomy_path):
        import yaml
        print(f"Loading existing taxonomy from {taxonomy_path}")
        with open(taxonomy_path) as f:
            taxonomy = yaml.safe_load(f)
    else:
        taxonomy = extract_taxonomy(args.notebook_id)
        save_taxonomy(taxonomy, taxonomy_path)

    branches = taxonomy.get("branches", [])
    print(f"\nTaxonomy: {len(branches)} branches identified")
    for b in branches:
        subs = len(b.get("sub_branches", []))
        print(f"  - {b['name']} ({subs} sub-branches)")
    print()

    # Phase 2: Per-branch investigation
    print(f"Phase 2: Investigating {len(branches)} branches...\n")
    for branch in branches:
        findings = investigate_branch(args.notebook_id, branch)
        save_findings(findings, findings_dir)
        print()

    # Phase 3: Cross-cutting synthesis
    print()
    synthesis = synthesize_themes(args.notebook_id, taxonomy)
    save_synthesis(synthesis, synthesis_path)

    # Summary
    print(f"\n{'='*60}")
    print(f"Research complete!")
    print(f"  Taxonomy: {taxonomy_path}")
    print(f"  Findings: {findings_dir}/ ({len(branches)} files)")
    print(f"  Synthesis: {synthesis_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make executable and verify**

```bash
chmod +x scripts/run_research.py
source .venv/bin/activate
python scripts/run_research.py --help
```

Expected: Help text showing notebook_id argument and options.

- [ ] **Step 3: Commit**

```bash
git add scripts/run_research.py
git commit -m "Add research orchestrator script

Runs all three phases: taxonomy extraction, per-branch
investigation, cross-cutting synthesis. Output to data/research/."
```

---

### Task 6: End-to-End Research Run and Status Update

This task is operational — run the research pipeline against the real corpus.

- [ ] **Step 1: Run the full research pipeline**

```bash
source .venv/bin/activate
python scripts/run_research.py 8d7b55c9-907f-4e70-8e08-2514e4a5e2d2
```

This will take several minutes (40-50 queries). Monitor output for failures.

- [ ] **Step 2: Verify output artifacts**

```bash
cat data/research/taxonomy.yaml | head -30
ls data/research/findings/
cat data/research/synthesis.json | python -m json.tool | head -20
```

Verify:
- taxonomy.yaml has branches with sub_branches
- findings/ has one JSON per branch
- synthesis.json has all three theme sections

- [ ] **Step 3: Update CLAUDE.md**

Update the Status section:

```
- Stage 4-5: Corpus research — COMPLETE
```

```bash
git add CLAUDE.md
git commit -m "Mark Stage 4-5 (corpus research) complete"
```
