#!/usr/bin/env python3
"""Run the full Stage 1-2 pipeline.

Usage:
    python scripts/run_pipeline.py [--skip-captions] [--max-results N]

This script:
1. Searches YouTube using the domain config queries
2. Prints the filter prompt for Claude to evaluate
3. Reads Claude's response from stdin (paste JSON array)
4. Merges scores and writes the checkpoint file

The Claude evaluation step happens manually: copy the prompt output,
have Claude evaluate it, paste the JSON response back.
"""

import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import run_search, build_filter_context, stage_results
from src.filter.semantic import parse_filter_response, apply_scores
from src.filter.policy import load_policy


def main():
    parser = argparse.ArgumentParser(description="Run YouTube Research Pipeline Stages 1-2")
    parser.add_argument("--skip-captions", action="store_true", help="Skip caption checks (saves API quota)")
    parser.add_argument("--max-results", type=int, default=20, help="Max results per query (default: 20)")
    parser.add_argument("--api-key", default="config/youtube_api_key.txt", help="Path to API key file")
    parser.add_argument("--template", default="config/editorial_policy_template.yaml", help="Policy template path")
    parser.add_argument("--domain", default="config/domains/ai_temporal_video.yaml", help="Domain config path")
    args = parser.parse_args()

    # Stage 1a: Search
    print(f"=== Stage 1a: Searching YouTube (max {args.max_results} per query) ===")
    videos = run_search(
        api_key_path=args.api_key,
        domain_path=args.domain,
        max_results_per_query=args.max_results,
        skip_captions=args.skip_captions,
    )
    print(f"Found {len(videos)} unique videos.\n")

    if not videos:
        print("No videos found. Check your API key and search queries.")
        return

    # Stage 1b: Build filter prompt
    print("=== Stage 1b: Building filter prompt ===")
    prompt = build_filter_context(args.template, args.domain, videos)
    print(prompt)
    print("\n=== Paste Claude's JSON response below (Ctrl+D when done) ===\n")

    # Read Claude's response from stdin
    response_lines = []
    try:
        for line in sys.stdin:
            response_lines.append(line)
    except EOFError:
        pass
    response_text = "".join(response_lines)

    # Parse and merge scores
    scores = parse_filter_response(response_text)
    scored_videos = apply_scores(videos, scores)
    included = [v for v in scored_videos if v.get("included")]
    print(f"\n=== Scored {len(scored_videos)} videos, {len(included)} included ===\n")

    # Stage 2: Write checkpoint
    domain = load_policy(args.domain)
    version = domain.get("version", "unknown")
    queries = [domain["domain"]["topic"]]

    path = stage_results(
        videos=scored_videos,
        research_project="ai_temporal_video",
        query_terms=queries,
        research_criteria_version=version,
    )
    print(f"=== Checkpoint written to: {path} ===")


if __name__ == "__main__":
    main()
