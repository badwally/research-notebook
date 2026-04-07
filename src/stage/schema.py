"""Checkpoint file schema definition and validation."""

METADATA_REQUIRED_FIELDS = {
    "research_project": str,
    "query_terms": list,
    "research_criteria_version": str,
    "timestamp": str,
    "total_candidates": int,
    "total_included": int,
}

VIDEO_REQUIRED_FIELDS = {
    "video_id": str,
    "url": str,
    "title": str,
    "channel_name": str,
    "channel_id": str,
    "publish_date": str,
    "duration": str,
    "view_count": int,
    "description": str,
    "has_captions": bool,
    "relevance_score": int,
    "inclusion_rationale": str,
    "included": bool,
}

ITEM_REQUIRED_FIELDS = {
    "item_id": str,          # e.g. "yt:dQw4w9WgXcQ", "arxiv:2401.12345", "pmid:39876543"
    "source_type": str,      # "youtube" | "arxiv" | "pubmed" | "semantic_scholar"
    "url": str,
    "title": str,
    "authors": list,         # [{"name": str, "affiliation": str|None}]
    "publish_date": str,     # ISO 8601
    "description": str,      # abstract or video description
    "content_type": str,     # "video" | "preprint" | "journal_article" | "review" | "meta_analysis" | "conference_paper"
    "full_text_available": bool,
    "relevance_score": int,  # populated by filter (default 0 pre-filter)
    "inclusion_rationale": str,  # default "" pre-filter
    "included": bool,        # default False pre-filter
}


def validate_checkpoint(checkpoint: dict) -> list[str]:
    """Validate a checkpoint dict against the expected schema.

    Auto-detects format based on presence of 'videos' or 'items' key.

    Args:
        checkpoint: Parsed checkpoint data.

    Returns:
        List of error strings. Empty list means valid.
    """
    errors = []

    if "metadata" not in checkpoint:
        errors.append("Missing top-level 'metadata' key")
    else:
        meta = checkpoint["metadata"]
        for field, expected_type in METADATA_REQUIRED_FIELDS.items():
            if field not in meta:
                errors.append(f"Missing metadata field: {field}")
            elif not isinstance(meta[field], expected_type):
                errors.append(f"metadata.{field}: expected {expected_type.__name__}, got {type(meta[field]).__name__}")

    if "items" in checkpoint:
        if not isinstance(checkpoint["items"], list):
            errors.append("'items' must be a list")
        else:
            for i, item in enumerate(checkpoint["items"]):
                for field, expected_type in ITEM_REQUIRED_FIELDS.items():
                    if field not in item:
                        errors.append(f"items[{i}]: missing field '{field}'")
                    elif not isinstance(item[field], expected_type):
                        errors.append(f"items[{i}].{field}: expected {expected_type.__name__}, got {type(item[field]).__name__}")
    elif "videos" in checkpoint:
        if not isinstance(checkpoint["videos"], list):
            errors.append("'videos' must be a list")
        else:
            for i, video in enumerate(checkpoint["videos"]):
                for field, expected_type in VIDEO_REQUIRED_FIELDS.items():
                    if field not in video:
                        errors.append(f"videos[{i}]: missing field '{field}'")
                    elif not isinstance(video[field], expected_type):
                        errors.append(f"videos[{i}].{field}: expected {expected_type.__name__}, got {type(video[field]).__name__}")
    else:
        errors.append("Missing 'videos' or 'items' key")

    return errors
