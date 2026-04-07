# Stage 0: Editorial Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Design a reusable prompt template that defines the corpus editorial policy — the criteria Claude uses to semantically filter YouTube search results for research relevance.

**Architecture:** A single YAML prompt template with clearly separated slots: domain configuration, inclusion criteria, exclusion criteria, quality signals, and scoring rubric. The template is domain-agnostic by design; a companion domain config file instantiates it for a specific research topic. Claude receives both at filter time.

**Tech Stack:** YAML for structured template, Markdown for documentation. No code — this is research design work.

---

## File Structure

| File | Purpose |
|------|---------|
| `config/editorial_policy_template.yaml` | Domain-agnostic prompt template with slot definitions |
| `config/domains/ai_temporal_video.yaml` | Domain config for AI longitudinal temporal video analysis |
| `config/editorial_policy.md` | Human-readable documentation of the policy design and rationale |

---

### Task 1: Design the Editorial Policy Template

**Files:**
- Create: `config/editorial_policy_template.yaml`

- [ ] **Step 1: Write the template structure**

This is the reusable skeleton. Each section has a slot description explaining what goes there and how it's used during filtering.

```yaml
# Editorial Policy Template — YouTube Research Pipeline
#
# This template defines the criteria Claude uses to evaluate YouTube video
# metadata for research corpus inclusion. It is domain-agnostic; pair it
# with a domain config file to instantiate for a specific research topic.
#
# Usage: At filter time, Claude receives this template (populated with
# domain config values) plus a batch of video metadata objects. Claude
# evaluates each video and returns a relevance score + rationale.

system_prompt: |
  You are a research corpus curator. Your job is to evaluate YouTube video
  metadata and decide whether each video belongs in a research corpus on
  the specified topic. You are applying editorial standards equivalent to
  a literature review — not a keyword search.

  You will receive:
  1. The research domain and inclusion/exclusion criteria below
  2. A batch of video metadata objects (title, description, channel, etc.)

  For each video, you must return:
  - relevance_score: integer 1-5 (see rubric below)
  - inclusion_rationale: 1-2 sentences explaining your decision
  - included: boolean (true if relevance_score >= inclusion_threshold)

  Apply the criteria strictly. When in doubt, exclude. A smaller, higher-quality
  corpus is better than a larger, noisy one.

domain:
  topic: "{topic}"
  field: "{field}"
  description: "{domain_description}"

inclusion_criteria:
  # Videos MUST meet ALL of these to be considered for inclusion
  required:
    - "{inclusion_criterion_1}"
    - "{inclusion_criterion_2}"
    - "{inclusion_criterion_3}"

exclusion_criteria:
  # Videos matching ANY of these are excluded regardless of other criteria
  hard_exclude:
    - "{exclusion_criterion_1}"
    - "{exclusion_criterion_2}"
    - "{exclusion_criterion_3}"

quality_signals:
  # These are weighted indicators, not hard gates. A video can score well
  # without all of them, but more signals = higher confidence.
  channel_authority:
    description: "Signals that the channel produces credible research content"
    positive_signals:
      - "{authority_signal_1}"
      - "{authority_signal_2}"
    negative_signals:
      - "{authority_negative_1}"
      - "{authority_negative_2}"

  speaker_expertise:
    description: "Signals that the presenter has domain knowledge"
    positive_signals:
      - "{expertise_signal_1}"
      - "{expertise_signal_2}"
    negative_signals:
      - "{expertise_negative_1}"
      - "{expertise_negative_2}"

  content_depth:
    description: "Signals that the content goes beyond surface-level treatment"
    positive_signals:
      - "{depth_signal_1}"
      - "{depth_signal_2}"
    negative_signals:
      - "{depth_negative_1}"
      - "{depth_negative_2}"

scoring_rubric:
  scale: "1-5"
  inclusion_threshold: 3
  levels:
    5:
      label: "Essential"
      description: "Directly addresses the research topic with expert-level depth. Would be cited in a literature review."
    4:
      label: "Strong"
      description: "Substantially relevant with good depth. Credible source with clear research value."
    3:
      label: "Relevant"
      description: "Addresses the topic with adequate depth. Meets inclusion bar but not a standout."
    2:
      label: "Marginal"
      description: "Tangentially related or shallow treatment. Does not meet inclusion threshold."
    1:
      label: "Irrelevant"
      description: "Off-topic, clickbait, or no research value."

output_format:
  description: "For each video in the input batch, return a JSON object with these fields added"
  fields:
    relevance_score: "integer 1-5 per rubric above"
    inclusion_rationale: "1-2 sentences explaining the score"
    included: "boolean — true if relevance_score >= {inclusion_threshold}"
```

- [ ] **Step 2: Review the template for completeness**

Verify the template covers all deliverable requirements from the spec:
- Inclusion criteria slots: YES (inclusion_criteria.required)
- Exclusion criteria slots: YES (exclusion_criteria.hard_exclude)
- Quality signals (channel authority, speaker expertise, content depth): YES (quality_signals section)
- Scoring rubric (1-5 with threshold): YES (scoring_rubric section)
- Domain-specific configuration: YES (domain section)
- Output format: YES (output_format section)

- [ ] **Step 3: Commit the template**

```bash
git add config/editorial_policy_template.yaml
git commit -m "Add editorial policy prompt template (Stage 0)

Domain-agnostic template with slots for inclusion/exclusion criteria,
quality signals, scoring rubric, and domain configuration."
```

---

### Task 2: Instantiate Domain Config for AI Temporal Video Analysis

**Files:**
- Create: `config/domains/ai_temporal_video.yaml`

- [ ] **Step 1: Write the domain configuration**

This fills every slot in the template for the target research domain.

```yaml
# Domain Configuration: AI for Longitudinal Temporal Video Analysis
#
# Instantiates editorial_policy_template.yaml for this research domain.
# Paired with the template at filter time.

domain:
  topic: "AI for longitudinal temporal video analysis"
  field: "Computer Vision / Machine Learning"
  description: >
    Research and applied work on using artificial intelligence — particularly
    deep learning and computer vision — to analyze video data across extended
    time periods. This includes temporal pattern recognition, activity detection
    over long durations, change detection across video sequences, and systems
    that reason about video content longitudinally rather than frame-by-frame.

inclusion_criteria:
  required:
    - "Video discusses AI/ML methods applied to video analysis across time (not single-frame image analysis)"
    - "Content addresses temporal reasoning, longitudinal patterns, or multi-frame analysis"
    - "Presentation includes technical substance — methods, architectures, results, or detailed applications"

exclusion_criteria:
  hard_exclude:
    - "Pure product demos or marketing with no technical content"
    - "Tutorials on basic video editing or video production tools"
    - "News segments that mention AI + video without technical depth (under 2 minutes of substance)"
    - "Content focused exclusively on real-time/streaming inference with no longitudinal component"
    - "Duplicate or re-uploaded content from another channel already in the corpus"

quality_signals:
  channel_authority:
    positive_signals:
      - "University, research lab, or conference channel (e.g., CVPR, NeurIPS, ICCV, ECCV)"
      - "Channel regularly publishes technical AI/ML content with consistent quality"
      - "Channel associated with a known research group or company research division"
    negative_signals:
      - "Channel primarily produces clickbait or sensationalist AI content"
      - "No other technical videos on the channel — isolated upload"

  speaker_expertise:
    positive_signals:
      - "Speaker identifies as researcher, engineer, or practitioner in CV/ML"
      - "Speaker references specific papers, methods, or datasets by name"
      - "Presentation is from a conference, workshop, or academic seminar"
    negative_signals:
      - "Speaker provides no credentials and makes only general claims"
      - "Content is narrated AI-generated voiceover with no identified author"

  content_depth:
    positive_signals:
      - "Discusses specific architectures (transformers, RNNs, 3D CNNs, etc.) for temporal analysis"
      - "References or presents benchmark results, datasets, or evaluation metrics"
      - "Covers failure modes, limitations, or open problems"
      - "Duration >= 10 minutes (longer content correlates with depth for technical material)"
    negative_signals:
      - "Surface-level overview with no technical specifics"
      - "Duration < 5 minutes (unlikely to cover technical depth adequately)"

scoring_rubric:
  inclusion_threshold: 3
```

- [ ] **Step 2: Cross-check domain config against template slots**

Verify every slot in the template has a corresponding value:
- domain.topic: YES
- domain.field: YES
- domain.description: YES
- inclusion_criteria.required: YES (3 criteria)
- exclusion_criteria.hard_exclude: YES (5 criteria)
- quality_signals (all 3 categories with positive + negative): YES
- scoring_rubric.inclusion_threshold: YES

- [ ] **Step 3: Commit the domain config**

```bash
mkdir -p config/domains
git add config/domains/ai_temporal_video.yaml
git commit -m "Add domain config for AI temporal video analysis

Instantiates editorial policy template for the first target domain:
AI for longitudinal temporal video analysis."
```

---

### Task 3: Write Policy Documentation

**Files:**
- Create: `config/editorial_policy.md`

- [ ] **Step 1: Write the policy documentation**

```markdown
# Editorial Policy — YouTube Research Pipeline

## Purpose

This document explains the design rationale for the corpus editorial policy.
The policy defines how Claude evaluates YouTube video metadata to decide what
belongs in a research corpus. It is the highest-leverage design decision in
the pipeline: errors here silently degrade all downstream stages.

## Architecture

Two files work together:

- **`editorial_policy_template.yaml`** — Domain-agnostic prompt template.
  Defines the structure: what criteria exist, how scoring works, what output
  Claude produces. Reusable across any research domain.

- **`domains/{domain}.yaml`** — Domain-specific configuration. Fills every
  slot in the template for a particular research topic. One file per domain.

At filter time (Stage 1b), Claude receives the template populated with the
domain config, plus a batch of video metadata from YouTube. Claude returns
each video with a relevance score, rationale, and include/exclude decision.

## Design Decisions

**Strict over permissive.** The policy instructs Claude to exclude when in
doubt. A smaller, higher-quality corpus produces better downstream research
than a noisy one. False negatives (missing a good video) are recoverable by
running additional searches. False positives (including a bad video) degrade
NotebookLM retrieval quality silently.

**Quality signals are weighted, not gated.** A video doesn't need all positive
signals to score well. Conference talks score high on authority and expertise
but may lack detailed architecture discussion. Practitioner deep-dives may
lack academic credentials but deliver excellent content depth. The rubric
handles this via holistic scoring.

**Exclusion criteria are hard gates.** Any match on the exclusion list means
the video is out, regardless of other qualities. This prevents high-production-
value marketing content from scoring well on surface signals.

**Duration as a quality signal, not a gate.** Longer videos correlate with
depth for technical content, but short videos aren't automatically excluded.
A 7-minute conference spotlight can be more valuable than a 45-minute
rambling tutorial.

## Scoring Rubric

| Score | Label | Meaning |
|-------|-------|---------|
| 5 | Essential | Would be cited in a literature review |
| 4 | Strong | Clear research value, credible source |
| 3 | Relevant | Meets inclusion bar, adequate depth |
| 2 | Marginal | Tangential or shallow — excluded |
| 1 | Irrelevant | Off-topic or no research value |

**Inclusion threshold: 3.** Videos scoring 3 or above are included.

## Iteration

The policy is versioned. When Stage 1b results are reviewed (Stage 1b exit
criterion), inclusion/exclusion decisions that don't match human judgment
indicate the policy needs refinement. Update the domain config, bump the
version, and re-run.
```

- [ ] **Step 2: Commit the documentation**

```bash
git add config/editorial_policy.md
git commit -m "Add editorial policy design documentation

Explains the rationale behind the template structure, scoring rubric,
and design decisions for the corpus editorial policy."
```

---

### Task 4: Validate the Policy (Manual Desk Check)

This task has no file output — it's a validation step.

- [ ] **Step 1: Construct a test scenario**

Open YouTube in a browser and search for: `AI longitudinal temporal video analysis`

Pick 5 videos from the results that represent different quality levels:
1. A conference talk from CVPR/NeurIPS on temporal video understanding
2. A university lecture on video transformers or temporal CNNs
3. A short news clip mentioning AI + video
4. A product demo for a video analytics tool
5. A practitioner deep-dive on implementing temporal analysis

- [ ] **Step 2: Apply the policy mentally**

For each video, read the title, description, channel name, and duration. Apply the editorial policy criteria and assign a score. Check:
- Does the 5-score conference talk actually score 4-5?
- Does the news clip score 1-2?
- Does the product demo hit the exclusion criteria?
- Are the inclusion criteria specific enough to distinguish research content from general AI hype?

- [ ] **Step 3: Adjust criteria if needed**

If the policy produces wrong decisions on the test videos, update `config/domains/ai_temporal_video.yaml` and commit:

```bash
git add config/domains/ai_temporal_video.yaml
git commit -m "Refine domain config based on desk check validation"
```

- [ ] **Step 4: Mark Stage 0 complete**

Update `CLAUDE.md` status section:

```
- Stage 0: Editorial policy — COMPLETE
```

```bash
git add CLAUDE.md
git commit -m "Mark Stage 0 (editorial policy) complete"
```
