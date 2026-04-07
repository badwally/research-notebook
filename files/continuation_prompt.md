# Continuation Prompt — YouTube Research Pipeline

Use this prompt when starting a new Claude Code session for this project.

---

## Prompt

You are continuing work on the YouTube Research Pipeline project. Read CLAUDE.md and project_prompt.json before taking any action.

### Project Context

This project builds an automated research pipeline with seven stages:

1. **YouTube Search & Filter** — YouTube Data API v3 retrieves candidates; Claude evaluates metadata against research criteria as a semantic filter.
2. **URL Extraction & Staging** — Filtered results written to structured JSON checkpoint file.
3. **NotebookLM Ingestion** — Claude Code ingests URLs into NotebookLM via notebooklm-mcp-cli MCP server.
4. **Corpus Query Layer** — NotebookLM provides persistent semantic index for cross-source research.
5. **Deep Research** — Structured topic investigation against the corpus.
6. **Knowledge Base Output** — Research synthesized into Obsidian-compatible .md files.
7. **Semantic Tagging** — Controlled vocabulary tags applied across the Obsidian vault.

### Key Architectural Decisions Already Made

These decisions were made through deliberate analysis. Do not revisit them unless I explicitly ask:

- **Claude is the semantic filter** between YouTube's keyword retrieval and NotebookLM's corpus analysis. YouTube cannot evaluate research relevance; NotebookLM cannot select its own inputs. Claude bridges this gap using video metadata.
- **NotebookLM is in the critical path** for Stages 3-5. It provides managed RAG with persistent semantic index, cross-source synthesis, and grounded citation. Pro tier supports 300 sources/notebook, sufficient for the target corpus of ~200 videos.
- **MCP is the default automation path** for NotebookLM interaction (notebooklm-mcp-cli). Chosen over Python CLI (notebooklm-py) for the tighter agentic feedback loop. If MCP proves fragile, fall back to CLI. This decision is explicitly logged for re-evaluation.
- **Subtask 1A (Corpus Editorial Policy Prompt)** is a discrete design problem. The filtering criteria Claude uses at Stage 1 constitute the editorial policy of the research corpus. This must be designed with literature-review rigor before running the pipeline against real data.

### Open Subtasks

- **Subtask 1A: Corpus Editorial Policy Prompt** — Not yet designed. Deliverable: reusable prompt template with slots for inclusion criteria, exclusion criteria, quality signals, scoring rubric, and domain-specific configuration. Must be completed before first real pipeline run.

### Implementation Status

- Stages 1-3: Architecturally designed, not yet implemented.
- Stages 4-7: Designed at overview level, not yet specified in detail.
- No code has been written.

### What To Do First

1. Read CLAUDE.md and project_prompt.json in full.
2. Confirm you understand the architecture and decisions by summarizing back to me in one paragraph.
3. Ask me what stage or subtask I want to work on.

### Engineering Constraints

- Incremental, reversible steps. No monolithic builds.
- Smallest safe step. One-sentence check before multi-step plans.
- Pragmatic over clever. Simple, readable, maintainable code.
- YAGNI governs feature scope.
- Surface architectural decisions before implementing.
- Debug root causes, not symptoms. No workarounds.

### Credential Requirements (verify before implementation)

- Claude Code: Authenticated via Max subscription (not API key). Verify with `/status`. Ensure `ANTHROPIC_API_KEY` env var is unset so Claude Code uses Max plan allocation, not API billing.
- YouTube Data API v3: API key from Google Cloud project
- NotebookLM: OAuth browser login via `nlm login`, Pro tier verified

---

## Usage

Copy everything between the `## Prompt` header and this `## Usage` section. Paste it as your first message in a new Claude Code session for this project. Claude Code will read the project files and establish continuity.
