# src/output/source_notes.py
"""Generate Obsidian source notes — one per ingested source."""

import os
import yaml
from src.output.tags import extract_tags_from_text, slugify_tag


def generate_source_note(video: dict, branch_tag: str = None, cited_in_concepts: list = None) -> str:
    """Generate a single source note as markdown string."""
    tags = []
    if branch_tag:
        tags.append(branch_tag)
    tags.extend(extract_tags_from_text(video.get("title", "") + " " + video.get("description", "")))
    tags = sorted(set(tags))

    frontmatter = {
        "type": "source",
        "video_id": video["video_id"],
        "url": video["url"],
        "title": video["title"],
        "channel": video["channel_name"],
        "duration": video["duration"],
        "publish_date": video["publish_date"],
        "relevance_score": video.get("relevance_score", 0),
        "tags": tags,
    }

    lines = ["---"]
    lines.append(yaml.dump(frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True).strip())
    lines.append("---")
    lines.append("")
    lines.append(f"# {video['title']}")
    lines.append("")
    lines.append(f"**Channel:** {video['channel_name']}  ")
    lines.append(f"**Duration:** {video['duration']}  ")
    lines.append(f"**Views:** {video.get('view_count', 'N/A')}  ")
    lines.append(f"**Published:** {video['publish_date']}  ")
    lines.append(f"**URL:** {video['url']}")
    lines.append("")

    if video.get("description"):
        lines.append("## Description")
        lines.append("")
        lines.append(video["description"])
        lines.append("")

    if video.get("inclusion_rationale"):
        lines.append("## Relevance")
        lines.append("")
        lines.append(f"**Score:** {video.get('relevance_score', 'N/A')}/5  ")
        lines.append(f"{video['inclusion_rationale']}")
        lines.append("")

    if cited_in_concepts:
        lines.append("## Referenced In")
        lines.append("")
        for concept in cited_in_concepts:
            lines.append(f"- [[{concept}]]")
        lines.append("")

    return "\n".join(lines)


def write_source_notes(videos: list, output_dir: str, branch_tags: dict = None, citation_index: dict = None) -> list:
    """Write all source notes to disk."""
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    for video in videos:
        vid = video["video_id"]
        branch_tag = branch_tags.get(vid) if branch_tags else None
        cited_in = citation_index.get(vid, []) if citation_index else []

        content = generate_source_note(video, branch_tag, cited_in)
        filename = f"{vid}.md"
        path = os.path.join(output_dir, filename)

        with open(path, "w") as f:
            f.write(content)
        paths.append(path)

    print(f"  Wrote {len(paths)} source notes to {output_dir}")
    return paths


def generate_paper_note(item: dict, branch_tag: str = None, cited_in_concepts: list = None) -> str:
    """Generate an Obsidian source note for an academic paper.

    Args:
        item: Normalized item dict (ITEM_REQUIRED_FIELDS format) with source_metadata.
        branch_tag: Optional branch tag to include.
        cited_in_concepts: List of concept note names this paper is referenced in.

    Returns:
        Markdown string for the Obsidian note.
    """
    meta = item.get("source_metadata", {})

    tags = []
    if branch_tag:
        tags.append(branch_tag)
    tags.extend(extract_tags_from_text(item.get("title", "") + " " + item.get("description", "")))
    tags = sorted(set(tags))

    # Authors as list of name strings for frontmatter
    author_names = [a["name"] for a in (item.get("authors") or [])]

    frontmatter = {
        "type": "source-paper",
        "source_type": item["source_type"],
        "item_id": item["item_id"],
        "url": item["url"],
        "title": item["title"],
        "authors": author_names,
        "publish_date": item["publish_date"],
        "content_type": item.get("content_type", "preprint"),
        "relevance_score": item.get("relevance_score", 0),
        "tags": tags,
    }
    if meta.get("citation_count") is not None:
        frontmatter["citation_count"] = meta["citation_count"]
    if meta.get("doi"):
        frontmatter["doi"] = meta["doi"]

    lines = ["---"]
    lines.append(yaml.dump(frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True).strip())
    lines.append("---")
    lines.append("")
    lines.append(f"# {item['title']}")
    lines.append("")

    # Authors line
    if author_names:
        lines.append(f"**Authors:** {', '.join(author_names)}  ")

    lines.append(f"**Published:** {item['publish_date']}  ")

    # Venue: journal_ref > venue > "Preprint"
    venue = meta.get("journal_ref") or meta.get("venue") or "Preprint"
    lines.append(f"**Venue:** {venue}  ")

    # DOI if available
    doi = meta.get("doi")
    if doi:
        lines.append(f"**DOI:** {doi}  ")

    # PDF link if available
    pdf_url = meta.get("pdf_url")
    if pdf_url:
        lines.append(f"**PDF:** {pdf_url}")

    lines.append("")

    # Abstract
    if item.get("description"):
        lines.append("## Abstract")
        lines.append("")
        lines.append(item["description"])
        lines.append("")

    # Relevance
    if item.get("inclusion_rationale"):
        lines.append("## Relevance")
        lines.append("")
        lines.append(f"**Score:** {item.get('relevance_score', 'N/A')}/5  ")
        lines.append(item["inclusion_rationale"])
        lines.append("")

    # Citation context (from Semantic Scholar enrichment, if available)
    citation_count = meta.get("citation_count")
    influential_count = meta.get("influential_citation_count")
    tldr = meta.get("tldr")
    if citation_count is not None or tldr:
        lines.append("## Citation Context")
        lines.append("")
        if citation_count is not None:
            influential_str = f" ({influential_count} influential)" if influential_count is not None else ""
            lines.append(f"**Citations:** {citation_count}{influential_str}  ")
        if tldr:
            lines.append(f"**TLDR:** {tldr}")
        lines.append("")

    # Referenced In
    if cited_in_concepts:
        lines.append("## Referenced In")
        lines.append("")
        for concept in cited_in_concepts:
            lines.append(f"- [[{concept}]]")
        lines.append("")

    return "\n".join(lines)


def write_paper_notes(items: list, output_dir: str, branch_tags: dict = None, citation_index: dict = None) -> list:
    """Write paper source notes to disk.

    Args:
        items: List of item dicts (ITEM_REQUIRED_FIELDS format).
        output_dir: Directory to write notes to.
        branch_tags: Dict mapping item_id to branch tag.
        citation_index: Dict mapping item_id to list of concept names.

    Returns:
        List of written file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    for item in items:
        iid = item["item_id"]
        branch_tag = branch_tags.get(iid) if branch_tags else None
        cited_in = citation_index.get(iid, []) if citation_index else []

        content = generate_paper_note(item, branch_tag, cited_in)
        # Use item_id as filename, replacing : with _ for filesystem safety
        filename = f"{iid.replace(':', '_')}.md"
        path = os.path.join(output_dir, filename)

        with open(path, "w") as f:
            f.write(content)
        paths.append(path)

    print(f"  Wrote {len(paths)} paper notes to {output_dir}")
    return paths
