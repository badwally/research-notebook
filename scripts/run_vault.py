#!/usr/bin/env python3
"""Generate the Obsidian knowledge base from research artifacts.

Usage:
    python scripts/run_vault.py <notebook_id>
    python scripts/run_vault.py 8d7b55c9-907f-4e70-8e08-2514e4a5e2d2
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.output.vault import generate_vault


def main():
    parser = argparse.ArgumentParser(description="Generate Obsidian vault from research artifacts")
    parser.add_argument("notebook_id", help="NotebookLM notebook ID")
    parser.add_argument("--output-dir", default="data/obsidian", help="Output directory for vault")
    args = parser.parse_args()

    summary = generate_vault(args.notebook_id, output_dir=args.output_dir)

    print(f"\nVault ready at: {args.output_dir}/")
    print("Open in Obsidian to view graph.")


if __name__ == "__main__":
    main()
