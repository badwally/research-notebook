# Stage 6-7: Obsidian Knowledge Base & Semantic Tagging — Design Spec

## Overview

Stages 6 and 7 are collapsed into a single stage. Transform research artifacts from Stage 4-5 into an Obsidian-compatible knowledge base with four note types, internal wiki-links, and a controlled tag taxonomy. Graph view is a first-class constraint — the note structure and linking strategy are designed to produce meaningful graph topology.

## Note Types

### 1. Source Notes (`sources/`)

One per ingested video. The evidence layer.

**Frontmatter:**
```yaml
---
type: source
video_id: "abc123"
url: "https://youtube.com/watch?v=abc123"
title: "Full video title"
channel: "Channel Name"
duration: "PT25M30S"
publish_date: "2021-06-15T00:00:00Z"
relevance_score: 4
tags:
  - action-recognition
  - transformer
---
```

**Body:** Video title as H1, channel and metadata summary, key claims/contributions extracted from research findings that cite this source. Links to concept notes via `[[concept-name]]`.

### 2. Concept Notes (`concepts/`)

One per atomic idea, method, or architecture. The knowledge layer — most densely linked.

**Frontmatter:**
```yaml
---
type: concept
concept_type: method | architecture | technique | dataset
related_branches:
  - "Action Recognition & Classification"
tags:
  - graph-neural-network
  - action-recognition
  - classification
---
```

**Body:** What it is, how it works, strengths/limitations. Links to source notes that discuss it via `[[source-name]]`. Links to related concept notes via `[[concept-name]]`.

### 3. MOC Notes (`mocs/`)

One per taxonomy branch (5 total). Navigation hubs.

**Frontmatter:**
```yaml
---
type: moc
branch: "Action Recognition & Classification"
tags:
  - action-recognition
---
```

**Body:** Branch description, organized links to concept notes in this domain, sub-branch sections, open problems from investigation findings.

### 4. Synthesis Notes (`synthesis/`)

One per cross-cutting theme (3 total). Bridge nodes.

**Frontmatter:**
```yaml
---
type: synthesis
theme: "Shared Architectures"
related_branches:
  - "Action Recognition & Classification"
  - "Temporal Action Detection & Localization"
  - "Video Object Tracking & Trajectory Prediction"
tags:
  - transformer
  - graph-neural-network
---
```

**Body:** Cross-cutting analysis from synthesis.json, with links to concept notes and source notes across multiple branches.

## Tag Taxonomy

Tags are derived from the corpus content at generation time — not hardcoded. Different research domains will produce different tag values. The tag *categories* are the reusable structure; the values within each category are extracted from the taxonomy and research findings.

Four categories, with example values from the current corpus:

**Branch tags** (derived from taxonomy branch names): e.g., `action-recognition`, `temporal-action-detection`, `video-tracking`, `video-language`, `spatio-temporal-computing`

**Architecture tags** (extracted from methods/architectures in findings): e.g., `transformer`, `graph-neural-network`, `cnn-3d`, `rnn-lstm`, `spiking-nn`

**Task tags** (extracted from sub-branch descriptions and method contexts): e.g., `classification`, `detection`, `localization`, `segmentation`, `grounding`, `captioning`, `tracking`

**Learning paradigm tags** (extracted from sub-branch names and method descriptions): e.g., `supervised`, `self-supervised`, `few-shot`, `unsupervised`

**Rules:**
- Lowercase, hyphenated
- No synonyms — one canonical tag per concept
- Every note gets at least one branch tag and one architecture or task tag
- Tags live in YAML frontmatter as a list

**Taxonomy documentation:** A `_tags.md` file in the vault root documents all tags with descriptions.

## Linking Strategy

- Source notes → concept notes they support
- Concept notes → related concept notes + source notes (evidence)
- MOCs → all concept notes in their branch
- Synthesis notes → concept and source notes across branches
- All links use Obsidian wiki-link syntax: `[[note-name]]`

## Graph Topology

- MOCs as major hubs (5 nodes, highly connected)
- Concept notes densely interlinked (method A relates to method B)
- Source notes as evidence backbone (many-to-many with concepts)
- Synthesis notes as bridges across clusters
- Branch tags create major clusters; architecture/task tags create cross-cutting connections

## Generation Strategy

Hybrid approach: all notes generated programmatically from existing research artifacts. The research findings already contain quality prose from NotebookLM. The generation step is transformation (JSON/YAML → Obsidian markdown), not new content creation.

**Input artifacts:**
- `data/research/taxonomy.yaml` — branch structure, method names
- `data/research/findings/*.json` — per-branch methods, comparisons, open problems with citations
- `data/research/synthesis.json` — cross-cutting themes with citations
- `data/staged/*.json` — video metadata for source notes
- NotebookLM source list — source ID to video mapping for citation resolution

**Citation resolution:** Research findings reference NotebookLM source IDs in citations. These must be mapped back to video IDs (from the staged checkpoint) to create proper source note links.

## Components

### Output Module (`src/output/`)

- `source_notes.py` — Generate source notes from checkpoint video metadata + research citation data
- `concept_notes.py` — Extract atomic concepts from research findings, generate concept notes with links
- `moc_notes.py` — Generate MOC notes from taxonomy branches with links to concepts
- `synthesis_notes.py` — Generate synthesis notes from synthesis.json
- `tags.py` — Tag assignment logic and taxonomy documentation generation
- `vault.py` — Orchestrator: runs all generators, writes to `data/obsidian/`

### Orchestrator Script

`scripts/run_vault.py` — Generates the full Obsidian vault from research artifacts.

## File Output Structure

```
data/obsidian/
  _tags.md              # Tag taxonomy documentation
  sources/
    {video_id}.md       # One per video (up to 104)
  concepts/
    {concept-name}.md   # One per method/architecture/technique/dataset
  mocs/
    {branch-name}.md    # One per taxonomy branch (5)
  synthesis/
    {theme-name}.md     # One per cross-cutting theme (3)
```

## Exit Criterion

Obsidian vault at `data/obsidian/` contains all four note types with proper YAML frontmatter, internal wiki-links, and tags from the controlled taxonomy. Opening the vault in Obsidian shows meaningful graph topology: MOCs as hubs, concept notes interlinked, source notes as evidence backbone, synthesis notes bridging across branches. Tag taxonomy documented in `_tags.md`.
