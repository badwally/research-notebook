#!/usr/bin/env python3
"""Run NotebookLM ingestion from a Stage 2 checkpoint file.

Usage:
    python scripts/run_ingestion.py <checkpoint_path> [--notebook-name NAME]

Examples:
    python scripts/run_ingestion.py data/staged/ai_temporal_video_20260407_170548.json
    python scripts/run_ingestion.py data/staged/ai_temporal_video_20260407_170548.json --notebook-name "AI Video Research"
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingest.notebooklm import ingest_checkpoint
from src.stage.checkpoint import read_checkpoint


def main():
    parser = argparse.ArgumentParser(description="Ingest checkpoint into NotebookLM")
    parser.add_argument("checkpoint", help="Path to Stage 2 checkpoint JSON file")
    parser.add_argument(
        "--notebook-name",
        default=None,
        help="Notebook display name (default: research_project from checkpoint metadata)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.checkpoint):
        print(f"Error: checkpoint file not found: {args.checkpoint}")
        sys.exit(1)

    # Derive notebook name from checkpoint if not provided
    checkpoint = read_checkpoint(args.checkpoint)
    notebook_name = args.notebook_name or checkpoint["metadata"]["research_project"]

    print(f"Checkpoint: {args.checkpoint}")
    print(f"Notebook: {notebook_name}")
    included = [v for v in checkpoint["videos"] if v.get("included")]
    print(f"Videos to ingest: {len(included)}")
    print()

    result = ingest_checkpoint(args.checkpoint, notebook_name)

    if result["notebook_id"]:
        print(f"\nNotebook ID: {result['notebook_id']}")
        print(f"Ingestion log: {result['log_path']}")


if __name__ == "__main__":
    main()
