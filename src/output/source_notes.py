# src/output/source_notes.py
"""Generate Obsidian source notes — one per ingested video."""

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
