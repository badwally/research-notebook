# src/output/synthesis_notes.py
"""Generate Obsidian synthesis notes — one per cross-cutting theme."""

import os
import yaml
from src.output.tags import extract_tags_from_text, slugify_tag

THEME_NAMES = {
    "shared_architectures": "Shared Architectures",
    "common_datasets": "Common Datasets",
    "recurring_tradeoffs": "Recurring Trade-offs",
}


def generate_synthesis_note(theme_key: str, theme_data: dict, branch_names: list) -> str:
    """Generate a synthesis note for a cross-cutting theme."""
    theme_name = THEME_NAMES.get(theme_key, theme_key.replace("_", " ").title())
    answer = theme_data.get("answer", "")
    tags = extract_tags_from_text(answer)
    tags = sorted(set(tags))
    frontmatter = {
        "type": "synthesis",
        "theme": theme_name,
        "related_branches": branch_names,
        "tags": tags,
    }
    lines = ["---"]
    lines.append(yaml.dump(frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True).strip())
    lines.append("---")
    lines.append("")
    lines.append(f"# {theme_name}")
    lines.append("")
    lines.append("*Cross-cutting analysis across all research branches.*")
    lines.append("")
    lines.append("## Related Branches")
    lines.append("")
    for name in branch_names:
        lines.append(f"- [[{slugify_tag(name)}|{name}]]")
    lines.append("")
    if answer:
        lines.append("## Analysis")
        lines.append("")
        lines.append(answer)
        lines.append("")
    return "\n".join(lines)


def write_synthesis_notes(synthesis: dict, output_dir: str, branch_names: list) -> list:
    """Write all synthesis notes to disk."""
    os.makedirs(output_dir, exist_ok=True)
    paths = []
    for theme_key, theme_data in synthesis.items():
        if not isinstance(theme_data, dict):
            continue
        content = generate_synthesis_note(theme_key, theme_data, branch_names)
        filename = f"{slugify_tag(THEME_NAMES.get(theme_key, theme_key))}.md"
        path = os.path.join(output_dir, filename)
        with open(path, "w") as f:
            f.write(content)
        paths.append(path)
    print(f"  Wrote {len(paths)} synthesis notes to {output_dir}")
    return paths
