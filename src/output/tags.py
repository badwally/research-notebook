"""Extract and assign tags from research content. Tags are corpus-derived, not hardcoded."""

import re

ARCHITECTURE_PATTERNS = {
    "transformer": r"\btransformer\b",
    "graph-neural-network": r"\bgraph\s*(neural\s*network|convolutional|attention)\b",
    "cnn-3d": r"\b3d[\s-]?cnn\b|\bc3d\b|\bi3d\b|\bslowfast\b",
    "rnn-lstm": r"\b(rnn|lstm|recurrent)\b",
    "spiking-nn": r"\bspiking\s*(neural\s*network)?\b",
    "attention": r"\b(self-)?attention\s*mechanism\b|\battention-based\b",
    "detr": r"\bdetr\b",
}

TASK_PATTERNS = {
    "classification": r"\bclassif(ication|y)\b",
    "detection": r"\b(action\s*)?detection\b",
    "localization": r"\blocalization\b",
    "segmentation": r"\bsegmentation\b",
    "grounding": r"\bgrounding\b",
    "captioning": r"\bcaptioning\b",
    "tracking": r"\btrack(ing)?\b",
    "recognition": r"\brecognition\b",
}

PARADIGM_PATTERNS = {
    "supervised": r"\bsupervised\b(?!\s*self)",
    "self-supervised": r"\bself-supervised\b",
    "few-shot": r"\bfew-shot\b",
    "unsupervised": r"\bunsupervised\b",
}


def slugify_tag(text: str) -> str:
    """Convert a name to a lowercase hyphenated tag."""
    text = text.lower()
    text = text.replace("&", "").replace("/", "-")
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def extract_branch_tags(branches: list) -> list:
    """Extract branch-level tags from taxonomy branches."""
    return [slugify_tag(b["name"]) for b in branches]


def extract_tags_from_text(text: str) -> list:
    """Extract architecture, task, and paradigm tags from text content."""
    text_lower = text.lower()
    tags = []
    for tag, pattern in ARCHITECTURE_PATTERNS.items():
        if re.search(pattern, text_lower):
            tags.append(tag)
    for tag, pattern in TASK_PATTERNS.items():
        if re.search(pattern, text_lower):
            tags.append(tag)
    for tag, pattern in PARADIGM_PATTERNS.items():
        if re.search(pattern, text_lower):
            tags.append(tag)
    return sorted(set(tags))


def build_tag_taxonomy(branches: list, findings_list: list) -> dict:
    """Build the complete tag taxonomy from research content."""
    branch_tags = extract_branch_tags(branches)
    all_text = ""
    for f in findings_list:
        for section in ["methods", "comparisons", "open_problems"]:
            if section in f and isinstance(f[section], dict):
                all_text += " " + f[section].get("answer", "")
    all_tags = extract_tags_from_text(all_text)
    architecture_tags = [t for t in all_tags if t in ARCHITECTURE_PATTERNS]
    task_tags = [t for t in all_tags if t in TASK_PATTERNS]
    paradigm_tags = [t for t in all_tags if t in PARADIGM_PATTERNS]
    return {
        "branch": sorted(branch_tags),
        "architecture": sorted(architecture_tags),
        "task": sorted(task_tags),
        "paradigm": sorted(paradigm_tags),
    }


def generate_tags_doc(taxonomy: dict) -> str:
    """Generate the _tags.md documentation file content."""
    lines = ["# Tag Taxonomy", ""]
    lines.append("Tags are derived from the corpus content. Different research domains produce different tags.")
    lines.append("")
    for category, tags in taxonomy.items():
        lines.append(f"## {category.title()} Tags")
        lines.append("")
        for tag in tags:
            lines.append(f"- `{tag}`")
        lines.append("")
    return "\n".join(lines)
