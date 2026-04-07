# src/filter/semantic.py
"""Semantic filtering: construct prompts and parse Claude's scoring responses."""

import json
import yaml


def build_filter_prompt(merged_policy: dict, videos: list[dict]) -> str:
    """Build the full prompt for Claude to evaluate a batch of videos.

    Args:
        merged_policy: Merged editorial policy (template + domain config).
        videos: List of normalized video metadata dicts from Stage 1a.

    Returns:
        Formatted prompt string ready for Claude evaluation.
    """
    policy_yaml = yaml.dump(merged_policy, default_flow_style=False, sort_keys=False)

    video_json = json.dumps(videos, indent=2)

    return f"""## Editorial Policy

{policy_yaml}

## Videos to Evaluate

{video_json}

## Instructions

Evaluate each video against the editorial policy above. For each video, return a JSON array where each element has:
- "video_id": the video's ID
- "relevance_score": integer 1-5 per the scoring rubric
- "inclusion_rationale": 1-2 sentences explaining your score
- "included": boolean (true if relevance_score >= {merged_policy['scoring_rubric']['inclusion_threshold']})

Return ONLY the JSON array, no other text."""


def parse_filter_response(response_text: str) -> list[dict]:
    """Parse Claude's filter response into a list of scoring dicts.

    Args:
        response_text: Claude's response (should be a JSON array).

    Returns:
        List of dicts with video_id, relevance_score, inclusion_rationale, included.

    Raises:
        ValueError: If response cannot be parsed as valid JSON.
    """
    text = response_text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        text = text.strip()

    try:
        scores = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Claude's filter response as JSON: {e}")

    if not isinstance(scores, list):
        raise ValueError(f"Expected JSON array, got {type(scores).__name__}")

    return scores


def apply_scores(videos: list[dict], scores: list[dict]) -> list[dict]:
    """Merge Claude's scores back into the video metadata.

    Args:
        videos: Original normalized video metadata.
        scores: Claude's scoring output (from parse_filter_response).

    Returns:
        Videos with relevance_score, inclusion_rationale, and included fields added.
    """
    score_map = {s["video_id"]: s for s in scores}

    result = []
    for video in videos:
        vid = video["video_id"]
        if vid in score_map:
            scored = dict(video)
            scored["relevance_score"] = score_map[vid]["relevance_score"]
            scored["inclusion_rationale"] = score_map[vid]["inclusion_rationale"]
            scored["included"] = score_map[vid]["included"]
            result.append(scored)

    return result
