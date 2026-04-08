# YouTube Research Pipeline

## Project Overview

An automated research pipeline that uses Claude Code as the orchestration layer to search YouTube for videos matching semantic research criteria, filter results using Claude as an intermediate semantic analysis layer, ingest filtered videos into Google NotebookLM for corpus-based research, and produce structured knowledge base output as Obsidian-compatible markdown files with semantic tags.

## Architecture

### Pipeline Stages

```
Stage 1: YouTube Search & Filter
  YouTube Data API v3 → keyword search → candidate video metadata
  Claude → semantic evaluation of metadata against research criteria → scored/filtered results

Stage 2: URL Extraction & Staging
  Filtered results → structured JSON checkpoint file
  Fields: video_id, url, title, channel, publish_date, duration, relevance_score, inclusion_rationale

Stage 3: NotebookLM Ingestion
  Claude Code → notebooklm-mcp-cli MCP server → create notebook → batch-ingest URLs from Stage 2 JSON
  Failures logged and surfaced for review

Stage 4: Corpus Query Layer
  NotebookLM provides persistent semantic index over ingested videos
  Cross-source synthesis, grounded citations, queryable via MCP

Stage 5: Deep Research
  Structured investigation of specific topics against the corpus
  Extract claims, arguments, evidence with source attribution

Stage 6: Knowledge Base Output
  Synthesize research outputs into .md files for Obsidian vault
  Standardized frontmatter, consistent structure

Stage 7: Semantic Tagging
  Controlled vocabulary derived from semantic analysis of video content
  Applied consistently across Obsidian vault via frontmatter tags
```

### Key Architectural Decisions

**Claude as semantic filter (Stages 1-2):** YouTube's search API returns results ranked by engagement metrics and keyword match. It cannot evaluate whether a video contains substantive, research-grade content on a given topic. NotebookLM provides semantic search and synthesis over sources already ingested — it cannot select its own inputs. Claude sits between these two systems as the semantic filter: it reads candidate video metadata (title, description, channel, duration) and evaluates it against natural-language research criteria. This pre-filtering protects NotebookLM's downstream retrieval quality by preventing irrelevant sources from diluting the vector space.

**NotebookLM in the critical path (Stage 3-5):** NotebookLM provides a managed RAG system with persistent vector index, cross-source synthesis, and grounded citation — capabilities that would require building an embedding pipeline, vector store, and retrieval layer from scratch. On Pro tier ($19.99/month), the 300-source-per-notebook limit comfortably handles the target corpus size of ~200 videos. The decision to keep NotebookLM in the critical path rather than building a standalone RAG pipeline was made deliberately: the research-quality advantages outweigh the dependency cost.

**MCP for NotebookLM automation (Stage 3):** The `notebooklm-mcp-cli` MCP server provides programmatic access to NotebookLM from Claude Code, eliminating the manual ingestion bottleneck. This was chosen over the Python CLI path (`notebooklm-py`) for the tighter agentic feedback loop — Claude can react to ingestion failures in real time. **Fallback:** If the MCP path proves fragile (undocumented API changes, auth issues), fall back to `notebooklm-py` CLI scripts. This decision is logged for re-evaluation if needed.

**Corpus editorial policy as a discrete design problem (Subtask 1A):** The filtering criteria provided to Claude at Stage 1 constitute the editorial policy of the research corpus. This is not a configuration detail — it's the highest-leverage design decision in the pipeline, because errors here silently degrade everything downstream. The filtering prompt requires its own iteration cycle, separate from pipeline engineering. See Subtask 1A below.

## Dependencies & Credentials

### APIs and Keys

| Service | Credential Type | What It Authenticates | Rate Limits / Cost |
|---------|----------------|----------------------|-------------------|
| YouTube Data API v3 | API Key (Google Cloud project) | Search and metadata retrieval | 10,000 units/day. Search = 100 units, video details = 1 unit, captions list = 50 units. ~2 substantive sessions/day at 100 videos each. |
| NotebookLM (via MCP) | OAuth browser login | Notebook creation, source ingestion, querying | Pro tier: 300 sources/notebook, 500 notebooks, 500 daily queries. Auth token may expire; re-login required. |
| Claude Code (Max subscription) | Max plan login (no separate API key) | All Claude Code orchestration: semantic filtering, synthesis, tagging, pipeline logic | Max plan usage allocation (shared across claude.ai, Claude Desktop, and Claude Code). No per-token billing. No separate Anthropic API key required. |

**Note on Claude authentication:** Claude Code's semantic filtering at Stage 1 runs as part of Claude Code's own reasoning — it reads YouTube API results, applies the editorial policy prompt, and scores candidates directly. This consumes Max plan allocation, not API credits. A separate Anthropic API key would only be required if the filtering needed to run headlessly outside Claude Code (e.g., as a standalone Python script calling the Anthropic API). That is not the current architecture.

### Tools and Libraries

| Tool | Role | Install |
|------|------|---------|
| `notebooklm-mcp-cli` | MCP server for NotebookLM automation | `pip install notebooklm-mcp-cli` or `uv tool install notebooklm-mcp-cli` |
| `notebooklm-py` | Fallback: Python CLI for NotebookLM | `pip install notebooklm-py` |
| YouTube Data API v3 client | YouTube search and metadata | `pip install google-api-python-client` |
| Claude Code | Orchestration environment (authenticated via Max subscription) | Already installed |

### Setup Sequence

1. Verify Claude Code is authenticated via Max subscription (not an API key). Run `/status` to confirm plan allocation. If an `ANTHROPIC_API_KEY` environment variable is set, Claude Code will use API billing instead of the Max plan — unset it if present.
2. Create Google Cloud project (or use existing)
3. Enable YouTube Data API v3
4. Generate API key for YouTube
5. Install `notebooklm-mcp-cli` and authenticate via browser login (`nlm login`)
6. Verify NotebookLM Pro tier access (300 sources/notebook)
7. Configure MCP server connection in Claude Code

## Integration Seams

These are the handoff points between stages. Data format at each boundary:

| Boundary | From → To | Data Format | Notes |
|----------|-----------|-------------|-------|
| 1 → 2 | YouTube API → Claude filter | JSON array of video metadata objects | Raw API response, transformed to normalized schema |
| 2 → 3 | Claude filter → NotebookLM ingestion | JSON file on disk | Checkpoint file. Contains only videos that passed filtering. Each entry has URL, metadata, score, rationale. |
| 3 → 4 | NotebookLM ingestion → Corpus queries | NotebookLM internal index | Opaque. No direct data access. Queried via MCP `ask` commands. |
| 4 → 5 | Corpus queries → Research synthesis | Structured query results (text) | Claude receives NotebookLM responses, structures into research findings |
| 5 → 6 | Research synthesis → Obsidian .md files | Markdown with YAML frontmatter | Follows Obsidian conventions. Tags in frontmatter. |
| 6 → 7 | .md files → Tagged knowledge base | Same .md files, enriched | Tags drawn from controlled vocabulary. Applied during Stage 6 or as a refinement pass. |

## Subtask 1A: Corpus Editorial Policy Prompt

**Status:** Not yet designed. Must be completed before first pipeline run.

**Deliverable:** A reusable prompt template with explicit slots for:
- **Inclusion criteria:** What makes a video worth ingesting (topic relevance, depth of treatment, speaker authority)
- **Exclusion criteria:** What disqualifies a video (clickbait, beginner tutorials, product demos, tangential mentions, low production quality as proxy for low rigor)
- **Quality signals:** Channel authority, speaker expertise indicators, content depth markers, engagement-to-substance ratio
- **Scoring rubric:** Consistent scale Claude applies across all candidates (e.g., 1-5 relevance, with threshold for inclusion)
- **Domain-specific configuration:** Slots that change per research project (topic, field, key terms, known authoritative channels)

This prompt is the editorial policy of the research corpus. It propagates through every downstream stage. Design it with the same rigor as inclusion criteria for a literature review.

## Project Constraints

- **Incremental, reversible steps.** No monolithic builds. Each stage should be testable independently.
- **Surface architectural decisions before implementing.** If a design choice is hard to reverse or significantly alters system structure, discuss it before committing.
- **Smallest safe step.** One-sentence check before multi-step plans. Confirm before major shifts.
- **Pragmatic over clever.** Simple, readable, maintainable code. YAGNI governs feature scope.
- **Debug root causes, not symptoms.** No workarounds. Reproduce, hypothesize, test minimally, verify.

## File Structure (Target)

```
youtube-research-pipeline/
├── CLAUDE.md                    # Project governance (generated from this README)
├── README.md                    # This file
├── config/
│   ├── youtube_api_key.env      # YouTube API key (gitignored)
│   └── research_criteria/       # Subtask 1A prompt templates per research project
├── src/
│   ├── search/                  # Stage 1: YouTube search
│   ├── filter/                  # Stage 1: Semantic filtering
│   ├── stage/                   # Stage 2: JSON staging
│   ├── ingest/                  # Stage 3: NotebookLM ingestion
│   ├── research/                # Stage 5: Research synthesis
│   └── output/                  # Stage 6-7: Obsidian output and tagging
├── data/
│   ├── staged/                  # Stage 2 JSON checkpoint files
│   ├── research/                # Stage 5 intermediate outputs
│   └── obsidian/                # Stage 6-7 final .md files
└── logs/                        # Ingestion logs, error reports
```

## Current Status

Stages 1-3 are architecturally designed. Implementation has not begun. Begin with Stage 1 (YouTube search + semantic filtering), validate with real data, then proceed sequentially.
