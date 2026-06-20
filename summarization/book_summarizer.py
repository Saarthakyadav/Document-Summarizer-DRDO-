"""
Book Summarizer — chapter-aware summarization.
Summarizes up to MAX_CHAPTERS chapters individually, then refines into
a single overview using the refine chain.
"""
import re
import time
from typing import Dict, List

from generation.groq_summarizer2 import summarize_chunk_groq, _call_groq, clean_summary_text
from generation.prompts import REFINE_PROMPT

MAX_CHAPTERS = 5   # configurable cap; avoids excessive API cost on very long books


# ---------------------------------------------------------------------------
# Structure extraction
# ---------------------------------------------------------------------------
def extract_title(text: str) -> str:
    for line in text.split("\n")[:20]:
        line = line.strip()
        if line.isupper() and 10 < len(line) < 100:
            return line
        if line and line[0].isupper() and 20 < len(line) < 150:
            return line
    return "Unknown Title"


def extract_author(text: str) -> str:
    for pattern in [
        r"(?:Author|By|Written by):\s*([A-Z][a-z]+ [A-Z][a-z]+)",
        r"©\s*\d{4}\s+([A-Z][a-z]+ [A-Z][a-z]+)",
    ]:
        m = re.search(pattern, text, re.MULTILINE)
        if m:
            return m.group(1)
    return "Unknown Author"


def detect_chapters(text: str) -> List[Dict]:
    """Split book text into chapters based on common heading patterns."""
    chapter_re = re.compile(
        r"(?m)^(?:Chapter|CHAPTER|Ch\.)\s+(\d+)[:\s]+([^\n]+)", re.IGNORECASE
    )
    matches = list(chapter_re.finditer(text))
    if not matches:
        # No explicit chapters — treat whole text as one unit
        return [{"number": "1", "title": "Full Text", "text": text[:8_000]}]

    chapters = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chapters.append({
            "number": m.group(1),
            "title": m.group(2).strip()[:100],
            "text": text[start:end].strip()[:4_000],
        })
    return chapters


# ---------------------------------------------------------------------------
# Summarization
# ---------------------------------------------------------------------------
def summarize_book_structured(text: str, detection: dict = None, max_tokens: int = None) -> dict:
    """
    Chapter-aware book summarization.
    Processes up to MAX_CHAPTERS chapters; refines chapter summaries
    into a single coherent overview using the refine chain.
    """
    print("📚 Using BOOK summarization strategy")

    chapters = detect_chapters(text)
    total_chapters = len(chapters)
    to_process = chapters[:MAX_CHAPTERS]

    print(f"  {total_chapters} chapters detected; summarizing first {len(to_process)}")

    chapter_summaries = []
    for ch in to_process:
        if not ch["text"].strip():
            continue
        print(f"  Summarizing Chapter {ch['number']}: {ch['title']}…")
        summary = summarize_chunk_groq(ch["text"])
        if summary:
            chapter_summaries.append({
                "number": ch["number"],
                "title": ch["title"],
                "summary": summary,
            })
        time.sleep(0.2)

    # Refine chapter summaries into one overview
    running = ""
    for cs in chapter_summaries:
        chunk = f"### Chapter {cs['number']}: {cs['title']}\n{cs['summary']}"
        if not running:
            running = chunk
        else:
            prompt = REFINE_PROMPT.format(summary=running[:3_000], chunk=chunk)
            result = _call_groq(prompt, max_tokens=800, temperature=0.3)
            running = clean_summary_text(result) if result else running + "\n\n" + chunk
        time.sleep(0.2)

    return {
        "type": "book",
        "title": extract_title(text),
        "author": extract_author(text),
        "total_chapters": total_chapters,
        "chapters_summarized": len(chapter_summaries),
        "chapter_summaries": chapter_summaries,
        "overview": running,
        "metadata": detection["metadata"] if detection else {},
    }


def format_book_summary(book_summary: dict) -> str:
    out = [f"# {book_summary['title']}"]
    if book_summary["author"] != "Unknown Author":
        out.append(f"**Author:** {book_summary['author']}")
    out.append(
        f"**Chapters:** {book_summary['total_chapters']} total, "
        f"{book_summary['chapters_summarized']} summarized"
    )
    out.append("")
    out.append(book_summary.get("overview", ""))
    return "\n".join(out)
