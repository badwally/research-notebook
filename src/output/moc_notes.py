# src/output/moc_notes.py
"""Generate Obsidian MOC (Map of Content) notes — one per taxonomy branch."""

import os
import re
import yaml
from src.output.tags import slugify_tag


def generate_moc_note(branch: dict, findings: dict = None) -> str:
    """Generate a MOC note for a taxonomy branch."""
    branch_tag = slugify_tag(branch["name"])
    frontmatter = {
        "type": "moc",
        "branch": branch["name"],
        "tags": [branch_tag],
    }
    lines = ["---"]
    lines.append(yaml.dump(frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True).strip())
    lines.append("---")
    lines.append("")
    lines.append(f"# {branch['name']}")
    lines.append("")
    if branch.get("description"):
        lines.append(branch["description"])
        lines.append("")
    for sub in branch.get("sub_branches", []):
        lines.append(f"## {sub['name']}")
        lines.append("")
        if sub.get("description"):
            lines.append(sub["description"])
            lines.append("")
        lines.append(f"**Concept:** [[{slugify_tag(sub['name'])}|{sub['name']}]]")
        lines.append("")
        if sub.get("methods"):
            lines.append("**Methods:**")
            for m in sub["methods"]:
                method_name = re.sub(r"\s*\[[\d,\s]+\]", "", m).strip()
                lines.append(f"- [[{slugify_tag(method_name)}|{method_name}]]")
            lines.append("")
    if findings and "open_problems" in findings:
        answer = findings["open_problems"].get("answer", "")
        if answer:
            lines.append("## Open Problems")
            lines.append("")
            lines.append(answer)
            lines.append("")
    return "\n".join(lines)


def write_moc_notes(branches: list, output_dir: str, findings_map: dict = None) -> list:
    """Write all MOC notes to disk."""
    os.makedirs(output_dir, exist_ok=True)
    paths = []
    for branch in branches:
        findings = findings_map.get(branch["name"]) if findings_map else None
        content = generate_moc_note(branch, findings)
        filename = f"{slugify_tag(branch['name'])}.md"
        path = os.path.join(output_dir, filename)
        with open(path, "w") as f:
            f.write(content)
        paths.append(path)
    print(f"  Wrote {len(paths)} MOC notes to {output_dir}")
    return paths
