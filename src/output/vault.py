# src/output/vault.py
"""Orchestrate full Obsidian vault generation from research artifacts."""

import glob
import json
import os
import yaml

from src.output.source_map import fetch_nlm_sources, load_all_videos, build_source_map
from src.output.tags import build_tag_taxonomy, generate_tags_doc
from src.output.source_notes import write_source_notes
from src.output.concept_notes import extract_concepts, write_concept_notes
from src.output.moc_notes import write_moc_notes
from src.output.synthesis_notes import write_synthesis_notes


def generate_vault(
    notebook_id: str,
    taxonomy_path: str = "data/research/taxonomy.yaml",
    findings_dir: str = "data/research/findings",
    synthesis_path: str = "data/research/synthesis.json",
    checkpoint_dir: str = "data/staged",
    output_dir: str = "data/obsidian",
) -> dict:
    """Generate the complete Obsidian vault from research artifacts."""
    print("Generating Obsidian vault...")

    # Load research artifacts
    with open(taxonomy_path) as f:
        taxonomy = yaml.safe_load(f)
    branches = taxonomy.get("branches", [])
    branch_names = [b["name"] for b in branches]

    # Load findings
    findings_map = {}
    for fpath in sorted(glob.glob(os.path.join(findings_dir, "*.json"))):
        with open(fpath) as f:
            finding = json.load(f)
        findings_map[finding["branch"]] = finding

    # Load synthesis
    with open(synthesis_path) as f:
        synthesis = json.load(f)

    # Load videos from checkpoints
    checkpoint_paths = sorted(glob.glob(os.path.join(checkpoint_dir, "*.json")))
    videos = load_all_videos(checkpoint_paths)

    # Build source map (NLM source ID -> video metadata)
    print("  Building source map...")
    nlm_sources = fetch_nlm_sources(notebook_id)
    source_map = build_source_map(nlm_sources, videos)
    print(f"  Mapped {len(source_map)}/{len(nlm_sources)} NLM sources to videos")

    # Build tag taxonomy
    print("  Extracting tags from corpus...")
    tag_taxonomy = build_tag_taxonomy(branches, list(findings_map.values()))

    # Write _tags.md
    tags_path = os.path.join(output_dir, "_tags.md")
    os.makedirs(output_dir, exist_ok=True)
    with open(tags_path, "w") as f:
        f.write(generate_tags_doc(tag_taxonomy))
    print(f"  Tag taxonomy written to {tags_path}")

    # Generate source notes
    print("\n  Generating source notes...")
    source_paths = write_source_notes(
        videos,
        os.path.join(output_dir, "sources"),
    )

    # Generate concept notes
    print("  Generating concept notes...")
    concepts = extract_concepts(taxonomy)
    concept_paths = write_concept_notes(
        concepts,
        os.path.join(output_dir, "concepts"),
    )

    # Generate MOC notes
    print("  Generating MOC notes...")
    moc_paths = write_moc_notes(
        branches,
        os.path.join(output_dir, "mocs"),
        findings_map,
    )

    # Generate synthesis notes
    print("  Generating synthesis notes...")
    synthesis_paths = write_synthesis_notes(
        synthesis,
        os.path.join(output_dir, "synthesis"),
        branch_names,
    )

    summary = {
        "source_notes": len(source_paths),
        "concept_notes": len(concept_paths),
        "moc_notes": len(moc_paths),
        "synthesis_notes": len(synthesis_paths),
        "total": len(source_paths) + len(concept_paths) + len(moc_paths) + len(synthesis_paths) + 1,
    }

    print(f"\n  Vault generated: {summary['total']} notes total")
    print(f"    Sources: {summary['source_notes']}")
    print(f"    Concepts: {summary['concept_notes']}")
    print(f"    MOCs: {summary['moc_notes']}")
    print(f"    Synthesis: {summary['synthesis_notes']}")
    print(f"    Tags doc: 1")

    return summary
