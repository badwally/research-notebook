# Stage 4-5: Corpus Research — Design Spec

## Overview

Stages 4 and 5 are collapsed into a single stage. The corpus (104 sources in NotebookLM) is queried systematically to extract the field's natural taxonomy, investigate each branch, and synthesize cross-cutting themes. Output: structured research artifacts ready for Obsidian conversion in Stage 6.

## Architecture

Three-phase approach, all using `nlm notebook query` CLI:

1. **Taxonomy extraction** — Broad queries discover sub-domains, methods, and relationships. Output: taxonomy tree (YAML).
2. **Per-branch investigation** — Structured queries per taxonomy branch: key methods, comparisons, open problems, landmark results. Output: per-branch findings (JSON) with citations.
3. **Cross-cutting synthesis** — Identify themes spanning branches: shared architectures, common datasets, recurring trade-offs. Output: synthesis findings with cross-references.

## Components

### Research Module (`src/research/`)

**`taxonomy.py`** — Taxonomy extraction
- `extract_taxonomy(notebook_id: str) -> dict` — Queries corpus for field structure, returns parsed taxonomy
- `save_taxonomy(taxonomy: dict, path: str)` — Writes taxonomy as YAML
- Query template: "What are the major sub-fields, method categories, and architectural families discussed across these sources? Organize them hierarchically."

**`investigate.py`** — Per-branch investigation
- `investigate_branch(notebook_id: str, branch: dict) -> dict` — Runs 3 structured queries per branch, returns findings with citations
- `save_findings(findings: dict, path: str)` — Writes per-branch findings as JSON
- Query templates:
  - Methods: "For [branch], what specific methods and architectures are discussed? List each with its key contribution."
  - Comparisons: "For [branch], how do these methods compare in terms of accuracy, efficiency, and limitations?"
  - Open problems: "For [branch], what unsolved problems, limitations, or future directions are identified?"

**`synthesize.py`** — Cross-cutting synthesis
- `synthesize_themes(notebook_id: str, taxonomy: dict) -> dict` — Identifies cross-cutting themes
- `save_synthesis(synthesis: dict, path: str)` — Writes synthesis as JSON
- Query templates:
  - Shared architectures: "What architectures or techniques appear across multiple sub-fields in this corpus?"
  - Common datasets: "What benchmark datasets are referenced across multiple research areas?"
  - Recurring trade-offs: "What fundamental trade-offs (accuracy vs speed, local vs global, etc.) recur across different methods?"

### Query Execution (`src/research/query.py`)

Shared query execution layer:
- `query_notebook(notebook_id: str, question: str) -> dict` — Runs `nlm notebook query`, returns parsed response with answer, citations, and source references
- Handles retry (once) on failure
- Preserves full citation chain for Stage 6 traceability

### Output Schema

**`data/research/taxonomy.yaml`**
```yaml
field: "AI for Longitudinal Temporal Video Analysis"
branches:
  - name: "Temporal Action Detection"
    description: "..."
    sub_branches:
      - name: "Proposal-based methods"
        description: "..."
      - name: "Anchor-free methods"
        description: "..."
  - name: "Video Transformers"
    description: "..."
    sub_branches: [...]
```

**`data/research/findings/{branch_name}.json`**
```json
{
  "branch": "Temporal Action Detection",
  "methods": {
    "answer": "...",
    "citations": {"1": "source_id", ...}
  },
  "comparisons": {
    "answer": "...",
    "citations": {"1": "source_id", ...}
  },
  "open_problems": {
    "answer": "...",
    "citations": {"1": "source_id", ...}
  }
}
```

**`data/research/synthesis.json`**
```json
{
  "shared_architectures": {
    "answer": "...",
    "citations": {"1": "source_id", ...}
  },
  "common_datasets": {
    "answer": "...",
    "citations": {"1": "source_id", ...}
  },
  "recurring_tradeoffs": {
    "answer": "...",
    "citations": {"1": "source_id", ...}
  }
}
```

### Orchestrator Script (`scripts/run_research.py`)

Runs all three phases sequentially:
1. Extract taxonomy → save to `data/research/taxonomy.yaml`
2. For each branch in taxonomy → investigate → save to `data/research/findings/`
3. Run synthesis → save to `data/research/synthesis.json`

Takes notebook ID as argument. Prints progress and summary.

## Practical Constraints

- **Query budget:** ~40-50 queries per full run. Pro tier allows 500/day. Well within limits.
- **Query failures:** Retry once, log failure, continue. Missing branch findings don't block others.
- **Citation preservation:** Every finding preserves NotebookLM's citation mapping (citation number → source ID) for Stage 6 traceability.

## Notebook Reference

- Notebook: "AI Temporal Video Analysis"
- ID: `8d7b55c9-907f-4e70-8e08-2514e4a5e2d2`
- Sources: 104

## Exit Criterion

- Taxonomy YAML exists with the field's natural structure
- Each taxonomy branch has investigation findings with citations
- Cross-cutting synthesis identifies shared themes
- All artifacts in `data/research/` ready for Stage 6
