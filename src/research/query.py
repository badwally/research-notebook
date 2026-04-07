"""Shared query execution layer for NotebookLM corpus research."""

import json
import subprocess

NLM_CMD = ["uvx", "--from", "notebooklm-mcp-cli", "nlm"]


def _run_nlm(args: list, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run an nlm CLI command and return the result."""
    cmd = NLM_CMD + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"nlm command failed (exit {result.returncode}): {' '.join(cmd)}\n"
            f"stderr: {result.stderr.strip()}"
        )
    return result


def parse_query_response(raw: dict) -> dict:
    """Parse the raw nlm query response into a clean research result.

    Args:
        raw: Parsed JSON from nlm notebook query output.

    Returns:
        Dict with answer, citations, and sources_used.
    """
    value = raw.get("value", raw)
    return {
        "answer": value.get("answer", ""),
        "citations": value.get("citations", {}),
        "sources_used": value.get("sources_used", []),
    }


def query_notebook(notebook_id: str, question: str, max_retries: int = 2) -> dict:
    """Query the NotebookLM corpus and return parsed results.

    Args:
        notebook_id: NotebookLM notebook ID.
        question: Research question to ask.
        max_retries: Number of attempts (1 retry by default).

    Returns:
        Parsed query result with answer, citations, sources_used.

    Raises:
        RuntimeError: If all retries fail.
    """
    for attempt in range(max_retries):
        try:
            result = _run_nlm(
                ["notebook", "query", notebook_id, question],
                timeout=120,
            )
            raw = json.loads(result.stdout)
            return parse_query_response(raw)
        except (RuntimeError, json.JSONDecodeError) as e:
            if attempt < max_retries - 1:
                print(f"  Query retry {attempt + 1}: {str(e)[:80]}")
                continue
            raise RuntimeError(f"Query failed after {max_retries} attempts: {e}")
