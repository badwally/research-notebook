"""Write and read JSON checkpoint files for the staging pipeline."""

import json
from datetime import datetime, timezone

from src.stage.schema import validate_checkpoint


def write_checkpoint(
    path: str,
    research_project: str,
    query_terms: list[str],
    research_criteria_version: str,
    videos: list[dict],
    included_only: bool = False,
) -> str:
    """Write a checkpoint file to disk.

    Args:
        path: Output file path.
        research_project: Name of the research project.
        query_terms: Search queries used.
        research_criteria_version: Version of the editorial policy used.
        videos: List of scored video metadata dicts.
        included_only: If True, only write videos where included=True.

    Returns:
        Path to the written file.

    Raises:
        ValueError: If the checkpoint data fails schema validation.
    """
    if included_only:
        videos = [v for v in videos if v.get("included")]

    checkpoint = {
        "metadata": {
            "research_project": research_project,
            "query_terms": query_terms,
            "research_criteria_version": research_criteria_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_candidates": len(videos),
            "total_included": sum(1 for v in videos if v.get("included")),
        },
        "videos": videos,
    }

    errors = validate_checkpoint(checkpoint)
    if errors:
        raise ValueError(f"Checkpoint validation failed: {'; '.join(errors)}")

    with open(path, "w") as f:
        json.dump(checkpoint, f, indent=2)

    return path


def write_item_checkpoint(
    path: str,
    research_project: str,
    query_terms: list[str],
    research_criteria_version: str,
    items: list[dict],
    sources_used: list[str],
    included_only: bool = False,
) -> str:
    """Write an item-format checkpoint file to disk.

    Args:
        path: Output file path.
        research_project: Name of the research project.
        query_terms: Search queries used.
        research_criteria_version: Version of the editorial policy used.
        items: List of scored item metadata dicts (ITEM_REQUIRED_FIELDS format).
        sources_used: List of source types queried, e.g. ["youtube", "arxiv"].
        included_only: If True, only write items where included=True.

    Returns:
        Path to the written file.

    Raises:
        ValueError: If the checkpoint data fails schema validation.
    """
    if included_only:
        items = [item for item in items if item.get("included")]

    checkpoint = {
        "metadata": {
            "research_project": research_project,
            "query_terms": query_terms,
            "research_criteria_version": research_criteria_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_candidates": len(items),
            "total_included": sum(1 for item in items if item.get("included")),
            "sources_used": sources_used,
        },
        "items": items,
    }

    errors = validate_checkpoint(checkpoint)
    if errors:
        raise ValueError(f"Checkpoint validation failed: {'; '.join(errors)}")

    with open(path, "w") as f:
        json.dump(checkpoint, f, indent=2)

    return path


def read_checkpoint(path: str) -> dict:
    """Read and validate a checkpoint file from disk.

    Args:
        path: Path to checkpoint JSON file.

    Returns:
        Parsed and validated checkpoint dict.

    Raises:
        ValueError: If the file fails schema validation.
    """
    with open(path) as f:
        checkpoint = json.load(f)

    errors = validate_checkpoint(checkpoint)
    if errors:
        raise ValueError(f"Checkpoint validation failed: {'; '.join(errors)}")

    return checkpoint
