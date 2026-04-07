#!/usr/bin/env python3
"""Run the full corpus research pipeline: taxonomy → investigation → synthesis.

Usage:
    python scripts/run_research.py <notebook_id>
    python scripts/run_research.py 8d7b55c9-907f-4e70-8e08-2514e4a5e2d2

Output is written to data/research/:
  - taxonomy.yaml
  - findings/{branch_name}.json (one per branch)
  - synthesis.json
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.research.taxonomy import extract_taxonomy, save_taxonomy
from src.research.investigate import investigate_branch, save_findings
from src.research.synthesize import synthesize_themes, save_synthesis


def main():
    parser = argparse.ArgumentParser(description="Run corpus research pipeline")
    parser.add_argument("notebook_id", help="NotebookLM notebook ID")
    parser.add_argument("--output-dir", default="data/research", help="Output directory")
    parser.add_argument("--skip-taxonomy", action="store_true", help="Skip taxonomy extraction (use existing)")
    args = parser.parse_args()

    output_dir = args.output_dir
    taxonomy_path = os.path.join(output_dir, "taxonomy.yaml")
    findings_dir = os.path.join(output_dir, "findings")
    synthesis_path = os.path.join(output_dir, "synthesis.json")

    # Phase 1: Taxonomy
    if args.skip_taxonomy and os.path.exists(taxonomy_path):
        import yaml
        print(f"Loading existing taxonomy from {taxonomy_path}")
        with open(taxonomy_path) as f:
            taxonomy = yaml.safe_load(f)
    else:
        taxonomy = extract_taxonomy(args.notebook_id)
        save_taxonomy(taxonomy, taxonomy_path)

    branches = taxonomy.get("branches", [])
    print(f"\nTaxonomy: {len(branches)} branches identified")
    for b in branches:
        subs = len(b.get("sub_branches", []))
        print(f"  - {b['name']} ({subs} sub-branches)")
    print()

    # Phase 2: Per-branch investigation
    print(f"Phase 2: Investigating {len(branches)} branches...\n")
    for branch in branches:
        findings = investigate_branch(args.notebook_id, branch)
        save_findings(findings, findings_dir)
        print()

    # Phase 3: Cross-cutting synthesis
    print()
    synthesis = synthesize_themes(args.notebook_id, taxonomy)
    save_synthesis(synthesis, synthesis_path)

    # Summary
    print(f"\n{'='*60}")
    print(f"Research complete!")
    print(f"  Taxonomy: {taxonomy_path}")
    print(f"  Findings: {findings_dir}/ ({len(branches)} files)")
    print(f"  Synthesis: {synthesis_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
