import pytest
import yaml
from src.filter.policy import load_policy, merge_policy


def test_load_policy_reads_yaml(tmp_path):
    """Verify load_policy reads a YAML file and returns a dict."""
    config = {"domain": {"topic": "test topic"}, "version": "0.1.0"}
    path = tmp_path / "test.yaml"
    path.write_text(yaml.dump(config))

    result = load_policy(str(path))

    assert result["domain"]["topic"] == "test topic"
    assert result["version"] == "0.1.0"


def test_merge_policy_fills_template_slots():
    """Verify merge_policy overlays domain config onto the template."""
    template = {
        "system_prompt": "You are a curator.",
        "version": "{version}",
        "domain": {"topic": "{topic}", "field": "{field}", "description": "{desc}"},
        "inclusion_criteria": {"required": []},
        "exclusion_criteria": {"hard_exclude": []},
        "quality_signals": {
            "channel_authority": {
                "description": "Channel credibility",
                "positive_signals": [],
                "negative_signals": [],
            },
        },
        "scoring_rubric": {
            "scale": "1-5",
            "inclusion_threshold": 3,
            "levels": {5: {"label": "Essential", "description": "Top tier"}},
        },
        "output_format": {"description": "Return JSON", "fields": {}},
    }
    domain = {
        "version": "0.1.0",
        "domain": {"topic": "AI video", "field": "CV/ML", "description": "Research"},
        "inclusion_criteria": {"required": ["Must be about AI"]},
        "exclusion_criteria": {"hard_exclude": ["No marketing"]},
        "quality_signals": {
            "channel_authority": {
                "positive_signals": ["University channel"],
                "negative_signals": ["Clickbait"],
            },
        },
        "scoring_rubric": {"inclusion_threshold": 4},
    }

    result = merge_policy(template, domain)

    assert result["version"] == "0.1.0"
    assert result["domain"]["topic"] == "AI video"
    assert result["inclusion_criteria"]["required"] == ["Must be about AI"]
    assert result["exclusion_criteria"]["hard_exclude"] == ["No marketing"]
    assert result["quality_signals"]["channel_authority"]["positive_signals"] == ["University channel"]
    assert result["scoring_rubric"]["inclusion_threshold"] == 4
    # Template-only fields preserved
    assert result["system_prompt"] == "You are a curator."
    assert result["scoring_rubric"]["scale"] == "1-5"
    assert result["scoring_rubric"]["levels"][5]["label"] == "Essential"
