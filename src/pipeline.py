"""End-to-end pipeline orchestrator: search → filter → stage."""

import os
from datetime import datetime, timezone

from src.search.youtube import build_client, search_and_normalize
from src.search.queries import load_domain_queries
from src.filter.policy import load_merged_policy
from src.filter.semantic import build_filter_prompt, parse_filter_response, apply_scores
from src.stage.checkpoint import write_checkpoint


def run_search(
    api_key_path: str,
    domain_path: str,
    max_results_per_query: int = 50,
    skip_captions: bool = False,
) -> list[dict]:
    """Stage 1a: Search YouTube and return normalized video metadata.

    Args:
        api_key_path: Path to file containing YouTube API key.
        domain_path: Path to domain config YAML.
        max_results_per_query: Max results per search query.
        skip_captions: Skip caption checks to save API quota.

    Returns:
        List of normalized video metadata dicts.
    """
    with open(api_key_path) as f:
        api_key = f.read().strip()

    client = build_client(api_key)
    queries = load_domain_queries(domain_path)

    all_videos = []
    seen_ids = set()

    for query in queries:
        results = search_and_normalize(
            client, query, max_results_per_query, skip_captions=skip_captions
        )
        for video in results:
            if video["video_id"] not in seen_ids:
                seen_ids.add(video["video_id"])
                all_videos.append(video)

    return all_videos


def build_filter_context(
    template_path: str, domain_path: str, videos: list[dict]
) -> str:
    """Stage 1b: Build the filter prompt for Claude evaluation.

    Returns the prompt string. The actual Claude evaluation must happen
    outside this function (via Claude Code's reasoning).

    Args:
        template_path: Path to editorial_policy_template.yaml.
        domain_path: Path to domain config YAML.
        videos: Normalized video metadata from run_search().

    Returns:
        Formatted prompt string for Claude.
    """
    merged = load_merged_policy(template_path, domain_path)
    return build_filter_prompt(merged, videos)


def stage_results(
    videos: list[dict],
    research_project: str,
    query_terms: list[str],
    research_criteria_version: str,
    output_dir: str = "data/staged",
    included_only: bool = True,
) -> str:
    """Stage 2: Write scored videos to a checkpoint file.

    Args:
        videos: Scored video metadata (with relevance_score, etc.).
        research_project: Project name for the checkpoint.
        query_terms: Queries used in the search.
        research_criteria_version: Version of the editorial policy.
        output_dir: Directory for checkpoint files.
        included_only: Only write included videos.

    Returns:
        Path to the written checkpoint file.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{research_project}_{timestamp}.json"
    path = os.path.join(output_dir, filename)

    return write_checkpoint(
        path=path,
        research_project=research_project,
        query_terms=query_terms,
        research_criteria_version=research_criteria_version,
        videos=videos,
        included_only=included_only,
    )
