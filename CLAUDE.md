# YouTube Research Pipeline

Automated research pipeline: YouTube search → Claude semantic filter → NotebookLM corpus → Obsidian knowledge base.

## Architecture

Seven stages. See `files/project_prompt.json` for full spec.

1. **YouTube Search & Filter** — API retrieves candidates, Claude filters by research criteria
2. **URL Extraction & Staging** — Filtered results → JSON checkpoint
3. **NotebookLM Ingestion** — MCP server ingests URLs into NotebookLM
4. **Corpus Query Layer** — NotebookLM semantic index for cross-source research
5. **Deep Research** — Structured investigation against corpus
6. **Knowledge Base Output** — Obsidian-compatible .md files
7. **Semantic Tagging** — Controlled vocabulary tags across vault

## Key Decisions (do not revisit without explicit request)

- Claude is the semantic filter between YouTube and NotebookLM
- NotebookLM is in the critical path (Stages 3-5)
- MCP is the default automation path (fallback: notebooklm-py CLI)
- Subtask 1A (editorial policy prompt) must be designed before first real pipeline run

## Status

- Stage 0: Editorial policy — COMPLETE
- Stage 1a: YouTube search wrapper — COMPLETE
- Stage 1b: Semantic filter — COMPLETE
- Stage 2: JSON staging — COMPLETE
- Stages 3-7: Not implemented

## Environment

- Python 3.11+ in .venv (source .venv/bin/activate)
- Dependencies: google-api-python-client, PyYAML, pytest
- Tests: python -m pytest tests/ -v
- YouTube Data API v3 key required (gitignored in `config/`)
- NotebookLM Pro tier, auth via `nlm login`
- Claude Code on Max plan (no ANTHROPIC_API_KEY)

## Engineering Constraints

- Incremental, reversible steps
- Smallest safe step
- Pragmatic over clever
- YAGNI governs scope
- Surface decisions before implementing
- Domain naming, not implementation naming
