# Research Notebook

Automated research pipeline: multi-source search → Claude semantic filter → NotebookLM corpus → Obsidian knowledge base.

Given a research domain, this system searches YouTube and academic sources (arXiv, PubMed), filters candidates through Claude's semantic evaluation, ingests them into Google NotebookLM for corpus-based synthesis, and produces a structured Obsidian vault with source notes, concept notes, maps of content, and synthesis documents.

## Pipeline

```
Search (YouTube, arXiv, PubMed)
  → Claude semantic filter (score + rationale per candidate)
  → JSON checkpoint (audit trail, pipeline decoupling)
  → NotebookLM ingestion (create notebook, batch-add sources)
  → Corpus research (structured queries against NotebookLM index)
  → Obsidian vault (source notes, concept notes, MOCs, synthesis, tags)
```

## Research Domains

Two domains have been run through the full pipeline:

| Domain | Config | Sources | Vault |
|--------|--------|---------|-------|
| AI Temporal Video Analysis | `config/domains/ai_temporal_video.yaml` | 104 YouTube videos | `data/obsidian/` (86 sources, 46 concepts, 5 MOCs, 3 synthesis) |
| GLP-1 Reward Modulation | `config/domains/glp1_reward_modulation.yaml` | 127 YouTube + PubMed + arXiv | `data/obsidian_glp1/` (127 sources, 28 concepts, 5 MOCs, 3 synthesis) |

## Project Structure

```
src/
  search/         YouTube, arXiv adapters + shared normalization
  filter/         Editorial policy + semantic scoring
  stage/          JSON checkpoint schema and writers
  ingest/         NotebookLM CLI integration
  research/       Taxonomy, queries, investigation, synthesis
  output/         Obsidian vault: source notes, concepts, MOCs, synthesis, tags
  pipeline.py     Orchestrator for multi-source search + staging

config/
  domains/        Per-domain YAML config (search queries, criteria, taxonomy seeds)
  research_queries_glp1.yaml

scripts/
  run_pipeline.py       Full pipeline execution
  run_ingestion.py      NotebookLM ingestion from checkpoint
  run_research.py       Corpus research against NotebookLM
  run_vault.py          Obsidian vault generation from research
  normalize_pubmed.py   PubMed result normalization
  score_glp1_candidates.py  GLP-1 candidate scoring

data/
  staged/         JSON checkpoints (gitignored, regenerable)
  research/       Taxonomy YAML, intermediate findings JSON
  obsidian/       Obsidian vault output (AI temporal video)
  obsidian_glp1/  Obsidian vault output (GLP-1)

tests/            pytest suite covering all pipeline stages
docs/             Design specs and implementation plans
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install google-api-python-client PyYAML pytest feedparser

# NotebookLM CLI
uv tool install notebooklm-mcp-cli
nlm login              # OAuth browser auth (required)
nlm doctor             # Verify Pro tier access

# NotebookLM Python library (for programmatic access)
pip install notebooklm-py
```

### Requirements

- Python 3.11+
- YouTube Data API v3 key (in `config/`, gitignored)
- Google NotebookLM Pro tier
- Claude Code on Max plan (no separate API key needed)

## Usage

```bash
# Run tests
python -m pytest tests/ -v

# Full pipeline for a domain
python scripts/run_pipeline.py config/domains/ai_temporal_video.yaml

# Individual stages
python scripts/run_ingestion.py data/staged/checkpoint.json
python scripts/run_research.py <notebook_id>
python scripts/run_vault.py data/research/synthesis.json

# NotebookLM presentation outputs
nlm audio create <notebook_id> -f deep_dive --confirm
nlm report create <notebook_id> -f "Briefing Doc" --confirm
nlm download audio <notebook_id> -o output.m4a
nlm download report <notebook_id> -o output.md
```

## Key Design Decisions

- **Claude as semantic filter** — YouTube/academic search ranks by engagement or keyword match, not research relevance. Claude evaluates metadata against natural-language criteria before anything enters NotebookLM.
- **NotebookLM in the critical path** — Provides managed RAG with persistent semantic index and cross-source synthesis. Building equivalent capabilities from scratch is not justified for this use case.
- **CLI over MCP for batch operations** — Scriptable, inspectable, doesn't require a live Claude Code session. MCP is reserved for interactive research queries.
- **Filesystem as database** — YAML configs, JSON checkpoints, Markdown output. Version-controlled, human-readable, debuggable with standard tools.
