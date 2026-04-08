# Research Notebook

Automated research pipeline: multi-source search → Claude semantic filter → NotebookLM corpus → Obsidian knowledge base.

## Architecture

Seven stages, two completed research domains (AI Temporal Video, GLP-1 Reward Modulation).

1. **Multi-Source Search** — YouTube API, arXiv Atom feeds, PubMed MCP. Adapters normalize to shared item format.
2. **Semantic Filter** — Claude scores candidates against domain editorial policy (YAML config). Items below threshold dropped.
3. **JSON Staging** — Checkpoint files decouple search from ingestion. Schema-validated, includes rationale.
4. **NotebookLM Ingestion** — `nlm` CLI batch-adds sources to a notebook. Per-video logging.
5. **Corpus Research** — Taxonomy-driven queries against NotebookLM. Structured investigation with citations.
6. **Obsidian Vault** — Source notes, concept notes, MOCs, synthesis documents. YAML frontmatter, wikilinks.
7. **Semantic Tagging** — Controlled vocabulary from taxonomy. Applied across vault.

## Key Decisions (do not revisit without explicit request)

- Claude is the semantic filter between search sources and NotebookLM
- NotebookLM is in the critical path (Stages 3-5)
- CLI (`nlm`) for batch operations; MCP for interactive research queries
- Filesystem-as-database: YAML configs, JSON checkpoints, Markdown output
- Multi-source: YouTube + arXiv + PubMed with shared normalization layer

## Status

All seven stages complete. Two full pipeline runs delivered:
- AI Temporal Video: 104 sources → 141 Obsidian notes (`data/obsidian/`)
- GLP-1 Reward Modulation: 127 sources → 163 Obsidian notes (`data/obsidian_glp1/`)

NotebookLM presentation outputs (audio overview, briefing doc) accessible via `nlm` CLI.

## Environment

- Python 3.11+ in .venv (`source .venv/bin/activate`)
- Dependencies: google-api-python-client, PyYAML, pytest, feedparser, notebooklm-py
- NotebookLM CLI: `uv tool install notebooklm-mcp-cli` → `nlm login`
- Tests: `python -m pytest tests/ -v`
- YouTube Data API v3 key required (gitignored in `config/`)
- Claude Code on Max plan (no ANTHROPIC_API_KEY)

## Engineering Constraints

- Incremental, reversible steps
- Smallest safe step
- Pragmatic over clever
- YAGNI governs scope
- Surface decisions before implementing
- Domain naming, not implementation naming
