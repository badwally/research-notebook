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

At filter time (Stage 1b), the pipeline merges the template with the domain
config into a single document. That merged document is passed to Claude as
the complete system context, followed by video metadata as user input.
Claude sees the full populated YAML as one coherent prompt.

## Design Decisions

**Strict over permissive.** The policy instructs Claude to exclude when in
doubt. A smaller, higher-quality corpus produces better downstream research
than a noisy one. False negatives (missing a good video) are recoverable by
running additional searches. False positives (including a bad video) degrade
NotebookLM retrieval quality silently.

**Quality signals are soft indicators, not gated.** A video doesn't need all positive
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

**Variable-length criteria lists.** The template defines empty lists that
domain configs fill with as many criteria as needed. This avoids artificial
constraints on the number of inclusion/exclusion criteria or quality signals.

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

The policy is versioned via the `version` field in the domain config. When
Stage 1b results are reviewed (Stage 1b exit criterion), inclusion/exclusion
decisions that don't match human judgment indicate the policy needs refinement.
Update the domain config, bump the version, and re-run.
