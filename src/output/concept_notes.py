# src/output/concept_notes.py
"""Generate Obsidian concept notes — one per method/architecture/technique."""

import os
import re
import yaml
from src.output.tags import extract_tags_from_text, slugify_tag


def extract_concepts(taxonomy: dict) -> list:
    """Extract atomic concepts from taxonomy methods and sub-branches."""
    concepts = []
    for branch in taxonomy.get("branches", []):
        for sub in branch.get("sub_branches", []):
            concepts.append({
                "name": sub["name"],
                "description": sub.get("description", ""),
                "branch": branch["name"],
                "concept_type": "technique",
                "methods": sub.get("methods", []),
            })
            for method_raw in sub.get("methods", []):
                method_name = re.sub(r"\s*\[[\d,\s]+\]", "", method_raw).strip()
                concepts.append({
                    "name": method_name,
                    "description": "",
                    "branch": branch["name"],
                    "sub_branch": sub["name"],
                    "concept_type": "method",
                    "methods": [],
                })
    return concepts


def generate_concept_note(
    concept: dict,
    findings_text: str = "",
    source_ids: list = None,
    related_concepts: list = None,
) -> str:
    """Generate a single concept note as markdown string."""
    tags = [slugify_tag(concept["branch"])]
    tags.extend(extract_tags_from_text(
        concept["name"] + " " + concept.get("description", "") + " " + findings_text
    ))
    tags = sorted(set(tags))

    frontmatter = {
        "type": "concept",
        "concept_type": concept["concept_type"],
        "related_branches": [concept["branch"]],
        "tags": tags,
    }

    lines = ["---"]
    lines.append(yaml.dump(frontmatter, default_flow_style=False, sort_keys=False, allow_unicode=True).strip())
    lines.append("---")
    lines.append("")
    lines.append(f"# {concept['name']}")
    lines.append("")

    if concept.get("description"):
        lines.append(concept["description"])
        lines.append("")

    lines.append(f"**Branch:** [[{slugify_tag(concept['branch'])}|{concept['branch']}]]")
    if concept.get("sub_branch"):
        lines.append(f"**Sub-branch:** [[{slugify_tag(concept['sub_branch'])}|{concept['sub_branch']}]]")
    lines.append("")

    if findings_text:
        lines.append("## Research Findings")
        lines.append("")
        lines.append(findings_text)
        lines.append("")

    if concept.get("methods"):
        lines.append("## Methods")
        lines.append("")
        for m in concept["methods"]:
            method_name = re.sub(r"\s*\[[\d,\s]+\]", "", m).strip()
            lines.append(f"- [[{slugify_tag(method_name)}|{method_name}]]")
        lines.append("")

    if source_ids:
        lines.append("## Sources")
        lines.append("")
        for vid in source_ids:
            lines.append(f"- [[{vid}]]")
        lines.append("")

    if related_concepts:
        lines.append("## Related Concepts")
        lines.append("")
        for rc in related_concepts:
            lines.append(f"- [[{slugify_tag(rc)}|{rc}]]")
        lines.append("")

    return "\n".join(lines)


def write_concept_notes(concepts: list, output_dir: str, findings_map: dict = None) -> list:
    """Write all concept notes to disk."""
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    for concept in concepts:
        findings_text = ""
        if findings_map:
            findings_text = findings_map.get(concept["name"], "")

        content = generate_concept_note(concept, findings_text)
        filename = f"{slugify_tag(concept['name'])}.md"
        path = os.path.join(output_dir, filename)

        with open(path, "w") as f:
            f.write(content)
        paths.append(path)

    print(f"  Wrote {len(paths)} concept notes to {output_dir}")
    return paths
