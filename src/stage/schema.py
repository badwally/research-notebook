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


def validate_checkpoint(checkpoint: dict) -> list[str]:
    """Validate a checkpoint dict against the expected schema.

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

    if "videos" not in checkpoint:
        errors.append("Missing top-level 'videos' key")
    elif not isinstance(checkpoint["videos"], list):
        errors.append("'videos' must be a list")
    else:
        for i, video in enumerate(checkpoint["videos"]):
            for field, expected_type in VIDEO_REQUIRED_FIELDS.items():
                if field not in video:
                    errors.append(f"videos[{i}]: missing field '{field}'")

    return errors
