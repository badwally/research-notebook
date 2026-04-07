import pytest
from src.output.tags import extract_branch_tags, extract_tags_from_text, slugify_tag, build_tag_taxonomy


def test_slugify_tag():
    assert slugify_tag("Action Recognition & Classification") == "action-recognition-classification"
    assert slugify_tag("3D CNN") == "3d-cnn"
    assert slugify_tag("RNN/LSTM") == "rnn-lstm"


def test_extract_branch_tags():
    branches = [
        {"name": "Action Recognition & Classification"},
        {"name": "Video-Language Understanding & Grounding"},
    ]
    tags = extract_branch_tags(branches)
    assert "action-recognition-classification" in tags
    assert "video-language-understanding-grounding" in tags


def test_extract_tags_from_text():
    text = "This method uses a transformer architecture with self-supervised learning on 3D CNN features."
    tags = extract_tags_from_text(text)
    assert "transformer" in tags
    assert "self-supervised" in tags
    assert "cnn-3d" in tags


def test_build_tag_taxonomy():
    branches = [{"name": "Action Recognition", "sub_branches": [
        {"name": "Few-Shot Learning", "methods": ["STRM"]},
    ]}]
    findings = {"methods": {"answer": "Uses transformer and graph neural network architectures"}}
    taxonomy = build_tag_taxonomy(branches, [findings])
    assert "branch" in taxonomy
    assert "architecture" in taxonomy
    assert len(taxonomy["branch"]) > 0
