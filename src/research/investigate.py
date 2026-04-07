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
