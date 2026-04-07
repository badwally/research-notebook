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
