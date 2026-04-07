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
