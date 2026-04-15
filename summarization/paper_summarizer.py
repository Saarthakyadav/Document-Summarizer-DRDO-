"""
Research Paper Summarizer - Extracts Abstract, Sections, Conclusion
"""
import re
import time
from typing import Dict, List

from generation.groq_summarizer2 import summarize_chunk_groq


def summarize_paper_structured(text: str, detection: dict = None, max_tokens: int = None) -> dict:
    """
    Structured summarization for research papers
    """
    print(f"📄 Using PAPER/ARTICLE summarization strategy")
    
    result = {
        "type": "paper",
        "title": extract_title(text),
        "authors": extract_authors(text),
        "abstract": "",
        "sections": {},
        "conclusion": "",
        "key_findings": [],
        "metadata": detection["metadata"] if detection else {}
    }
    
    # Extract abstract
    abstract_text = extract_section(text, "Abstract")
    if abstract_text:
        print("  Summarizing Abstract...")
        result["abstract"] = summarize_chunk_groq(abstract_text)
    
    # Extract conclusion
    conclusion_text = extract_section(text, "Conclusion")
    if conclusion_text:
        print("  Summarizing Conclusion...")
        result["conclusion"] = summarize_chunk_groq(conclusion_text)
    
    return result


def extract_title(text: str) -> str:
    """Extract paper title from first few lines"""
    lines = text.split('\n')[:10]
    for line in lines:
        line = line.strip()
        if len(line) > 20 and len(line) < 200 and line[0].isupper():
            return line[:150]
    return "Unknown Title"


def extract_authors(text: str) -> List[str]:
    """Extract author names from paper"""
    authors = []
    author_patterns = [
        r'(?:Author|By):\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
        r'([A-Z][a-z]+\s+[A-Z][a-z]+),\s+\d+',
    ]
    
    for pattern in author_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        authors.extend(matches)
    
    return list(dict.fromkeys(authors))[:3]


def extract_section(text: str, section_name: str) -> str:
    """Extract a specific section from the paper"""
    pattern = rf'{section_name}\s*\n\s*(.*?)(?=\n(?:Abstract|Introduction|Methodology|Results|Discussion|Conclusion|References|$))'
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    
    if match:
        content = match.group(1).strip()
        if len(content) > 3000:
            content = content[:3000]
        return content
    return ""


def format_paper_summary(paper_summary: dict) -> str:
    """Format paper summary as readable text"""
    output = []
    
    output.append(f"**Title:** {paper_summary['title']}")
    if paper_summary['authors']:
        output.append(f"**Authors:** {', '.join(paper_summary['authors'])}")
    output.append("")
    
    if paper_summary['abstract']:
        output.append("## Abstract")
        output.append(paper_summary['abstract'])
        output.append("")
    
    if paper_summary['conclusion']:
        output.append("## Conclusion")
        output.append(paper_summary['conclusion'])
    
    return "\n".join(output)