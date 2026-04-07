"""Derive YouTube search queries from domain configuration."""

import yaml


def load_domain_queries(domain_path: str) -> list[str]:
    """Generate search queries from the domain config.

    Extracts the topic and key terms to produce a set of search queries
    that cover the domain from multiple angles.

    Args:
        domain_path: Path to domain config YAML.

    Returns:
        List of search query strings.
    """
    with open(domain_path) as f:
        domain = yaml.safe_load(f)

    topic = domain["domain"]["topic"]
    field = domain["domain"]["field"]

    # Core query is the topic itself
    queries = [topic]

    # Add field-qualified variant
    queries.append(f"{field} {topic}")

    return queries
