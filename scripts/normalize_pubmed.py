"""
Normalize PubMed article metadata from MCP tool result files into pipeline item format.
Reads 6 JSON files, deduplicates by PMID, and saves to data/staged/pubmed_glp1_raw.json.
"""

import json
import html
import os
from pathlib import Path

SOURCE_FILES = [
    "/Users/andrewgrant/.claude/projects/-Users-andrewgrant-code-research-notebook/82701f85-592f-43b3-803c-5d3e63f8451f/tool-results/toolu_01LUjEoTJzewfwmV1kohJ7LN.txt",
    "/Users/andrewgrant/.claude/projects/-Users-andrewgrant-code-research-notebook/82701f85-592f-43b3-803c-5d3e63f8451f/tool-results/toolu_014Aa1Jxw6hP5d5FRwRLZAdw.txt",
    "/Users/andrewgrant/.claude/projects/-Users-andrewgrant-code-research-notebook/82701f85-592f-43b3-803c-5d3e63f8451f/tool-results/mcp-claude_ai_PubMed-get_article_metadata-1775605483489.txt",
    "/Users/andrewgrant/.claude/projects/-Users-andrewgrant-code-research-notebook/82701f85-592f-43b3-803c-5d3e63f8451f/tool-results/mcp-claude_ai_PubMed-get_article_metadata-1775605483174.txt",
    "/Users/andrewgrant/.claude/projects/-Users-andrewgrant-code-research-notebook/82701f85-592f-43b3-803c-5d3e63f8451f/tool-results/toolu_012FqYFa75bFjDti9tCWAZEU.txt",
    "/Users/andrewgrant/.claude/projects/-Users-andrewgrant-code-research-notebook/82701f85-592f-43b3-803c-5d3e63f8451f/tool-results/toolu_01BfkT3ymX2BrurjoRp7eZTG.txt",
]

OUTPUT_PATH = Path("/Users/andrewgrant/code/research-notebook/data/staged/pubmed_glp1_raw.json")


def format_pub_date(publication_date):
    """Convert publication_date dict to a human-readable string."""
    if not publication_date:
        return ""
    parts = []
    year = publication_date.get("year", "")
    month = publication_date.get("month", "")
    day = publication_date.get("day", "")
    if year:
        parts.append(year)
    if month:
        parts.append(month)
    if day:
        parts.append(day)
    return " ".join(parts)


def determine_content_type(article):
    """Map article_types to pipeline content_type."""
    types = article.get("article_types", [])
    types_lower = [t.lower() for t in types]
    if any("meta-analysis" in t for t in types_lower):
        return "meta_analysis"
    if any("systematic review" in t for t in types_lower):
        return "review"
    if any("review" in t for t in types_lower):
        return "review"
    if any("clinical trial" in t for t in types_lower):
        return "journal_article"
    return "journal_article"


def normalize_author(a):
    fore = a.get("fore_name", "").strip()
    last = a.get("last_name", "").strip()
    name = f"{fore} {last}".strip() if fore else last
    affiliations = a.get("affiliations") or []
    affiliation = affiliations[0] if affiliations else None
    return {"name": name, "affiliation": affiliation}


def normalize_article(article):
    identifiers = article.get("identifiers", {})
    pmid = identifiers.get("pmid", "")
    pmc = identifiers.get("pmc")
    doi = identifiers.get("doi")

    abstract_raw = article.get("abstract", "") or ""
    abstract = html.unescape(abstract_raw)[:1000]

    title_raw = article.get("title", "") or ""
    title = html.unescape(title_raw)

    pub_date = format_pub_date(article.get("publication_date"))

    mesh_terms = article.get("mesh_terms", []) or []
    # mesh_terms is a flat list of strings in this dataset
    mesh_names = [m if isinstance(m, str) else m.get("descriptor_name", "") for m in mesh_terms]

    full_text_url = (
        f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/" if pmc else None
    )

    return {
        "item_id": f"pmid:{pmid}",
        "source_type": "pubmed",
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "title": title,
        "authors": [normalize_author(a) for a in article.get("authors", [])],
        "publish_date": pub_date,
        "description": abstract,
        "content_type": determine_content_type(article),
        "full_text_available": bool(pmc),
        "relevance_score": 0,
        "inclusion_rationale": "",
        "included": False,
        "source_metadata": {
            "pmid": pmid,
            "doi": doi,
            "journal": article.get("journal", {}).get("title", ""),
            "peer_reviewed": True,
            "publication_type": article.get("article_types", []),
            "mesh_terms": mesh_names,
            "pmc_id": pmc,
            "full_text_url": full_text_url,
        },
    }


def main():
    seen_pmids = {}  # pmid -> article (dedup)
    total_loaded = 0

    for filepath in SOURCE_FILES:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        articles = data.get("articles", [])
        total_loaded += len(articles)
        for article in articles:
            pmid = article.get("identifiers", {}).get("pmid", "")
            if pmid and pmid not in seen_pmids:
                seen_pmids[pmid] = article

    print(f"Loaded {total_loaded} articles from {len(SOURCE_FILES)} files")
    print(f"Unique by PMID: {len(seen_pmids)}")

    normalized = [normalize_article(a) for a in seen_pmids.values()]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(normalized)} items to {OUTPUT_PATH}")
    print("\nSample titles (first 10):")
    for i, item in enumerate(normalized[:10], 1):
        print(f"  {i:2d}. [{item['content_type']}] {item['title'][:90]}")


if __name__ == "__main__":
    main()
