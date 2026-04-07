"""Tests for source note generation — paper format."""

import os
import yaml
from src.output.source_notes import generate_paper_note, write_paper_notes


def _make_paper_item(item_id="arxiv:2401.12345", source_type="arxiv"):
    return {
        "item_id": item_id,
        "source_type": source_type,
        "url": "http://arxiv.org/abs/2401.12345",
        "title": "Temporal Video Transformers",
        "authors": [
            {"name": "Alice Smith", "affiliation": "MIT"},
            {"name": "Bob Jones", "affiliation": None},
        ],
        "publish_date": "2024-01-15T00:00:00Z",
        "description": "We propose a novel temporal transformer architecture.",
        "content_type": "preprint",
        "full_text_available": True,
        "relevance_score": 4,
        "inclusion_rationale": "Directly addresses temporal video analysis.",
        "included": True,
        "source_metadata": {
            "arxiv_id": "2401.12345",
            "categories": ["cs.CV", "cs.AI"],
            "pdf_url": "http://arxiv.org/pdf/2401.12345v1.pdf",
            "primary_category": "cs.CV",
            "comment": "8 pages, CVPR 2024",
            "journal_ref": None,
        },
    }


def test_generate_paper_note_frontmatter():
    item = _make_paper_item()
    note = generate_paper_note(item)
    # Extract YAML frontmatter
    parts = note.split("---")
    fm = yaml.safe_load(parts[1])
    assert fm["type"] == "source-paper"
    assert fm["source_type"] == "arxiv"
    assert fm["item_id"] == "arxiv:2401.12345"
    assert fm["authors"] == ["Alice Smith", "Bob Jones"]
    assert fm["content_type"] == "preprint"


def test_generate_paper_note_body_sections():
    item = _make_paper_item()
    note = generate_paper_note(item)
    assert "# Temporal Video Transformers" in note
    assert "**Authors:** Alice Smith, Bob Jones" in note
    assert "**Venue:** Preprint" in note
    assert "## Abstract" in note
    assert "novel temporal transformer" in note
    assert "## Relevance" in note
    assert "**Score:** 4/5" in note
    assert "**PDF:** http://arxiv.org/pdf/2401.12345v1.pdf" in note


def test_generate_paper_note_journal_venue():
    item = _make_paper_item()
    item["source_metadata"]["journal_ref"] = "Nature Machine Intelligence 2024"
    note = generate_paper_note(item)
    assert "**Venue:** Nature Machine Intelligence 2024" in note


def test_generate_paper_note_citation_context():
    item = _make_paper_item()
    item["source_metadata"]["citation_count"] = 42
    item["source_metadata"]["influential_citation_count"] = 8
    item["source_metadata"]["tldr"] = "A new temporal transformer for video."
    note = generate_paper_note(item)
    assert "## Citation Context" in note
    assert "**Citations:** 42 (8 influential)" in note
    assert "**TLDR:** A new temporal transformer for video." in note


def test_generate_paper_note_referenced_in():
    item = _make_paper_item()
    note = generate_paper_note(item, cited_in_concepts=["temporal-transformers", "action-recognition"])
    assert "## Referenced In" in note
    assert "[[temporal-transformers]]" in note
    assert "[[action-recognition]]" in note


def test_generate_paper_note_with_branch_tag():
    item = _make_paper_item()
    note = generate_paper_note(item, branch_tag="action-recognition")
    parts = note.split("---")
    fm = yaml.safe_load(parts[1])
    assert "action-recognition" in fm["tags"]


def test_write_paper_notes(tmp_path):
    items = [_make_paper_item("arxiv:001"), _make_paper_item("arxiv:002")]
    paths = write_paper_notes(items, str(tmp_path))
    assert len(paths) == 2
    assert os.path.exists(paths[0])
    assert "arxiv_001.md" in paths[0]  # colon replaced with underscore
    # Read back and verify content
    with open(paths[0]) as f:
        content = f.read()
    assert "source-paper" in content
