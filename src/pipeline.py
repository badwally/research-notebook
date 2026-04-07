"""End-to-end pipeline orchestrator: search → filter → stage."""

import os
from datetime import datetime, timezone

import yaml

from src.search.queries import load_domain_queries
from src.filter.policy import load_merged_policy
from src.filter.semantic import build_filter_prompt, parse_filter_response, apply_scores
from src.stage.checkpoint import write_checkpoint, write_item_checkpoint
from src.search.arxiv import search_and_normalize as arxiv_search
from src.search.normalize import deduplicate_items


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
    from src.search.youtube import build_client, search_and_normalize

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


def _make_checkpoint_path(output_dir: str, research_project: str) -> str:
    """Create a timestamped checkpoint file path."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{research_project}_{timestamp}.json"
    return os.path.join(output_dir, filename)


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
    path = _make_checkpoint_path(output_dir, research_project)

    return write_checkpoint(
        path=path,
        research_project=research_project,
        query_terms=query_terms,
        research_criteria_version=research_criteria_version,
        videos=videos,
        included_only=included_only,
    )


def run_multi_source_search(
    sources: list[str],
    domain_path: str,
    max_results_per_query: int = 50,
) -> list[dict]:
    """Stage 1a: Search academic sources and return unified items.

    Searches sources that emit the ITEM_REQUIRED_FIELDS format.
    YouTube is handled separately via run_search() (legacy format).

    Args:
        sources: List of source types to search, e.g. ["arxiv"].
            Currently supports: "arxiv". ("pubmed" planned for Phase G.)
        domain_path: Path to domain config YAML.
        max_results_per_query: Max results per search query.

    Returns:
        List of normalized item dicts (ITEM_REQUIRED_FIELDS format).

    Raises:
        ValueError: If an unsupported source type is requested.
    """
    supported = {"arxiv"}
    unsupported = set(sources) - supported
    if unsupported:
        raise ValueError(f"Unsupported source types: {unsupported}")

    with open(domain_path) as f:
        domain = yaml.safe_load(f)

    all_items = []

    if "arxiv" in sources:
        topic = domain["domain"]["topic"]
        arxiv_config = domain.get("academic_sources", {}).get("arxiv", {})
        categories = arxiv_config.get("categories")
        results = arxiv_search(topic, max_results=max_results_per_query, categories=categories)
        all_items.extend(results)

    return deduplicate_items(all_items)


def stage_items(
    items: list[dict],
    research_project: str,
    query_terms: list[str],
    research_criteria_version: str,
    sources_used: list[str],
    output_dir: str = "data/staged",
    included_only: bool = True,
) -> str:
    """Stage 2: Write scored items to a checkpoint file (item format).

    Args:
        items: Scored item metadata (with relevance_score, etc.).
        research_project: Project name for the checkpoint.
        query_terms: Queries used in the search.
        research_criteria_version: Version of the editorial policy.
        sources_used: List of source types searched, e.g. ["arxiv"].
        output_dir: Directory for checkpoint files.
        included_only: Only write included items.

    Returns:
        Path to the written checkpoint file.
    """
    path = _make_checkpoint_path(output_dir, research_project)

    return write_item_checkpoint(
        path=path,
        research_project=research_project,
        query_terms=query_terms,
        research_criteria_version=research_criteria_version,
        items=items,
        sources_used=sources_used,
        included_only=included_only,
    )
