# Staged Development Plan — YouTube Research Pipeline

## Overview

This document defines the staged development process for the YouTube Research Pipeline. The pipeline automates research corpus construction: YouTube search, Claude semantic filtering, NotebookLM ingestion, structured research, and Obsidian knowledge base output.

Development follows the pipeline stages sequentially, with a full integration validation after Stage 3. The first target domain is **AI for longitudinal temporal video analysis**.

## Development Approach

- Stages mirror the pipeline architecture (Stages 0-7)
- Each stage is built, tested, and validated before proceeding
- Credential and environment setup is handled inline as part of each stage — not a separate engineering stage
- Editorial policy (Stage 0) is completed first as the quality standard for everything downstream

## Stages

### Stage 0: Editorial Policy (Subtask 1A)

**Type:** Research design
**Goal:** Define the corpus quality standard before any code exists.

- Design reusable prompt template with: inclusion criteria, exclusion criteria, quality signals, scoring rubric (1-5 with threshold), domain config
- Calibrate against the target domain: AI for longitudinal temporal video analysis
- Deliverable: prompt template file in `config/`, committed and versioned

**Exit criterion:** The policy would correctly include/exclude videos if applied manually to a YouTube search results page.

### Stage 1a: YouTube Search Wrapper

**Type:** Engineering
**Goal:** Retrieve candidate videos from YouTube with normalized metadata.

- YouTube Data API v3 client: keyword search, pagination, metadata normalization
- Credential setup (API key, quota verification) happens here naturally
- Output: raw candidate array with standardized metadata fields

**Exit criterion:** Real query for the target domain returns normalized metadata. Quota consumption is understood.

### Stage 1b: Semantic Filter

**Type:** Engineering
**Goal:** Apply the editorial policy as a semantic filter on search results.

- Claude evaluates each candidate's metadata against the Stage 0 editorial policy prompt
- Adds relevance_score, inclusion_rationale, included boolean to each video object
- Iterate on the policy prompt if the filter makes bad calls

**Exit criterion:** Given search results for the target domain, the filter correctly identifies research-quality videos. Inclusion/exclusion decisions match your judgment.

### Stage 2: JSON Staging & Checkpoint

**Type:** Engineering
**Goal:** Write filtered results to disk as the pipeline's first durable artifact.

- Serialize Stage 1 output to JSON checkpoint file at `data/staged/{project}_{timestamp}.json`
- Schema validation against the spec in `project_prompt.json`
- Include research criteria version hash for traceability

**Exit criterion:** Stage 1-2 runs end-to-end. Checkpoint file round-trips with schema integrity. Stage 2 can re-run without re-running Stage 1.

### Stage 3: NotebookLM Ingestion

**Type:** Engineering + integration
**Goal:** Ingest staged URLs into NotebookLM as a research corpus.

- Install and authenticate notebooklm-mcp-cli (inline ops)
- Create NotebookLM notebook, batch-ingest URLs from Stage 2 checkpoint
- Per-video error handling: log failures, skip, continue
- Auth/rate-limit handling per spec
- Output: populated notebook + ingestion log at `logs/ingestion_{project}_{timestamp}.json`
- If MCP proves fragile, evaluate notebooklm-py fallback here

**Exit criterion:** Full Stage 1-3 pipeline validated end-to-end. NotebookLM notebook contains ~20+ research-quality videos on the target domain, queryable conversationally.

### Stage 4: Corpus Query Layer

**Type:** Exploratory
**Goal:** Establish reliable patterns for querying the NotebookLM corpus.

- Develop query templates: topic exploration, claim extraction, cross-source comparison
- Test retrieval quality — grounded citations, corpus coverage vs. clustering
- Document NotebookLM's retrieval behavior: what works, what doesn't

**Exit criterion:** Structured research findings can be reliably extracted with source attribution. NotebookLM's strengths and limitations for this use case are understood.

### Stage 5: Deep Research

**Type:** Research
**Goal:** Structured investigation of the target domain against the corpus.

- Research question templates that decompose broad topics into sub-questions
- Systematic queries: claims, arguments, evidence, counter-arguments with attribution
- Cross-source synthesis: agreement, disagreement, unique coverage
- Output: structured research artifacts in `data/research/`

**Exit criterion:** Research findings on AI for longitudinal temporal video analysis are well-sourced, cross-referenced, and literature-review quality.

### Stage 6: Knowledge Base Output

**Type:** Design + engineering
**Goal:** Synthesize research into an Obsidian-compatible knowledge base.

- Design Obsidian note schema from scratch: YAML frontmatter, note types (source, topic, synthesis), internal linking conventions
- Frontmatter fields, links, and tags must be designed to produce useful graph topology in Obsidian's graph view — this is a first-class constraint
- Transform Stage 5 artifacts into .md files at `data/obsidian/`
- Every claim traceable back to source video

**Exit criterion:** Vault is browsable in Obsidian. Notes navigate via links and tags. Claims trace to source videos. Graph view shows meaningful structure.

### Stage 7: Semantic Tagging

**Type:** Design + engineering
**Goal:** Apply controlled vocabulary across the vault for structured navigation and graph coherence.

- Derive tag taxonomy from corpus content — extracted from emergent themes, not imposed top-down
- Controlled vocabulary: defined tags with clear scope, no synonym proliferation
- Consistent application via frontmatter across all note types
- Tags create meaningful graph clusters — related notes pull together, distinct topics separate
- Documented taxonomy in the vault for consistent tagging of future additions

**Exit criterion:** Obsidian graph view shows meaningful structure — topic clusters, cross-cutting themes, inter-area relationships. Taxonomy is documented.

## Sequencing Notes

- Stage 0 before any code — it defines the quality standard
- Stages 1-3 build and test incrementally, with full pipeline validation after Stage 3
- Stages 4-5 are empirical — shaped by what NotebookLM does with real data
- Stages 6-7 are tightly coupled (graph view depends on both schema and tags) but designed sequentially

## Target Domain

**AI for longitudinal temporal video analysis** — encompasses computer vision approaches to analyzing video data across extended time periods, including applications in surveillance, sports analytics, medical imaging, autonomous systems, and related fields.
