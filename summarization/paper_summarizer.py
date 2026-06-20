"""
Research Paper Summarizer
Extracts Abstract, body sections, and Conclusion, then refines into a
structured summary. Fixes the original bug where body sections were
detected but never summarized.
"""
import re
import time
from typing import Dict, List

from generation.groq_summarizer2 import summarize_chunk_groq, _call_groq, clean_summary_text
from generation.prompts import REFINE_PROMPT


# ---------------------------------------------------------------------------
# Section extraction helpers
# ---------------------------------------------------------------------------
SECTION_HEADERS = [
    "Abstract", "Introduction", "Related Work", "Background",
    "Methodology", "Method", "Approach", "Experiments", "Results",
    "Discussion", "Conclusion", "Conclusions", "References",
]

_HEADER_RE = re.compile(
    r"(?m)^(?:" + "|".join(re.escape(h) for h in SECTION_HEADERS) + r")\s*$",
    re.IGNORECASE,
)


def extract_sections(text: str) -> Dict[str, str]:
    """Split paper into named sections. Falls back to full text if no headers found."""
    matches = list(_HEADER_RE.finditer(text))
    if not matches:
        return {"body": text}

    sections: Dict[str, str] = {}
    for i, match in enumerate(matches):
        name = match.group(0).strip().title()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            sections[name] = content[:4_000]   # cap per section to avoid token blow-up

    return sections


def extract_title(text: str) -> str:
    for line in text.split("\n")[:10]:
        line = line.strip()
        if 20 <= len(line) <= 200 and line[0].isupper():
            return line[:150]
    return "Unknown Title"


def extract_authors(text: str) -> List[str]:
    patterns = [
        r"(?:Author|By):\s*([A-Z][a-z]+ [A-Z][a-z]+)",
        r"([A-Z][a-z]+ [A-Z][a-z]+),\s+\d+",
    ]
    authors: List[str] = []
    for p in patterns:
        authors.extend(re.findall(p, text, re.MULTILINE))
    return list(dict.fromkeys(authors))[:3]


# ---------------------------------------------------------------------------
# Summarization
# ---------------------------------------------------------------------------
def summarize_paper_structured(text: str, detection: dict = None, max_tokens: int = None) -> dict:
    """
    Structured summarization for research papers.
    Summarizes every detected section (not just abstract + conclusion),
    then refines into a single coherent summary.
    """
    print("📄 Using PAPER summarization strategy")

    sections = extract_sections(text)
    print(f"  Detected sections: {list(sections.keys())}")

    # Summarize each section individually
    section_summaries: Dict[str, str] = {}
    for name, content in sections.items():
        if name.lower() == "references":
            continue    # skip bibliography
        print(f"  Summarizing '{name}' ({len(content)} chars)…")
        summary = summarize_chunk_groq(content)
        if summary:
            section_summaries[name] = summary
        time.sleep(0.2)

    # Refine all section summaries into one flowing summary
    running = ""
    for name, s_summary in section_summaries.items():
        if not running:
            running = s_summary
        else:
            prompt = REFINE_PROMPT.format(summary=running[:3_000], chunk=s_summary)
            result = _call_groq(prompt, max_tokens=800, temperature=0.3)
            running = clean_summary_text(result) if result else running + "\n\n" + s_summary
        time.sleep(0.2)

    return {
        "type": "paper",
        "title": extract_title(text),
        "authors": extract_authors(text),
        "sections_found": list(section_summaries.keys()),
        "summary": running,
        "metadata": detection["metadata"] if detection else {},
    }


def format_paper_summary(paper_summary: dict) -> str:
    out = [f"**Title:** {paper_summary['title']}"]
    if paper_summary.get("authors"):
        out.append(f"**Authors:** {', '.join(paper_summary['authors'])}")
    out.append("")
    if paper_summary.get("sections_found"):
        out.append(f"*Sections covered: {', '.join(paper_summary['sections_found'])}*")
        out.append("")
    out.append(paper_summary.get("summary", ""))
    return "\n".join(out)
