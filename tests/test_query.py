import json
import pytest
from src.research.query import parse_query_response


def test_parse_query_response_extracts_answer_and_citations():
    raw = {
        "value": {
            "answer": "TCNs are faster than transformers.",
            "conversation_id": "conv123",
            "sources_used": ["src1", "src2"],
            "citations": {"1": "src1", "2": "src2"},
        }
    }

    result = parse_query_response(raw)

    assert result["answer"] == "TCNs are faster than transformers."
    assert result["citations"] == {"1": "src1", "2": "src2"}
    assert result["sources_used"] == ["src1", "src2"]


def test_parse_query_response_handles_missing_citations():
    raw = {
        "value": {
            "answer": "No sources found.",
            "conversation_id": "conv123",
            "sources_used": [],
        }
    }

    result = parse_query_response(raw)

    assert result["answer"] == "No sources found."
    assert result["citations"] == {}
    assert result["sources_used"] == []


def test_parse_query_response_handles_empty_answer():
    raw = {
        "value": {
            "answer": "",
            "conversation_id": "conv123",
            "sources_used": [],
        }
    }

    result = parse_query_response(raw)

    assert result["answer"] == ""
