"""
Book Summarizer - Chapter-aware summarization for books
"""
import re
import time
from typing import List, Dict

from generation.groq_summarizer2 import summarize_chunk_groq


def summarize_book_structured(text: str, detection: dict = None, max_tokens: int = None) -> dict:
    """
    Chapter-aware summarization for books
    """
    print(f"📚 Using BOOK summarization strategy")
    
    result = {
        "type": "book",
        "title": extract_title(text),
        "author": extract_author(text),
        "total_chapters": 0,
        "chapters": [],
        "overview": "",
        "metadata": detection["metadata"] if detection else {}
    }
    
    # Detect chapters
    chapters = detect_chapters(text)
    result["total_chapters"] = len(chapters)
    
    # Summarize first few chapters (max 5 for performance)
    for i, chapter in enumerate(chapters[:5]):
        chapter_text = "\n".join(chapter.get("content", []))[:4000]
        if chapter_text.strip():
            summary = summarize_chunk_groq(chapter_text)
            result["chapters"].append({
                "number": chapter.get("number", i+1),
                "title": chapter.get("title", f"Chapter {i+1}"),
                "summary": summary[:800] if summary else "[No summary]"
            })
    
    return result


def extract_title(text: str) -> str:
    """Extract book title from first few pages"""
    lines = text.split('\n')[:20]
    for line in lines:
        line = line.strip()
        if len(line) > 10 and len(line) < 100 and line.isupper():
            return line
        if len(line) > 20 and len(line) < 150 and line[0].isupper():
            return line
    return "Unknown Title"


def extract_author(text: str) -> str:
    """Extract author name from book"""
    author_patterns = [
        r'(?:Author|By|Written by):\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
        r'©\s*\d{4}\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
    ]
    
    for pattern in author_patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            return match.group(1)
    return "Unknown Author"


def detect_chapters(text: str) -> List[Dict]:
    """Split book into chapters based on chapter headings"""
    chapters = []
    
    chapter_patterns = [
        r'(?:\n|^)(?:Chapter|CHAPTER|Ch\.)\s+(\d+)[:\s]+([^\n]+)',
        r'(?:\n|^)(\d+)[\.\s]+([A-Z][^\n]+)',
    ]
    
    current_chapter = {"number": "1", "title": "Introduction", "content": []}
    lines = text.split('\n')
    
    for line in lines:
        is_chapter_start = False
        
        for pattern in chapter_patterns:
            match = re.match(pattern, line.strip())
            if match:
                if current_chapter["content"]:
                    chapters.append(current_chapter)
                current_chapter = {
                    "number": match.group(1),
                    "title": match.group(2).strip()[:100],
                    "content": []
                }
                is_chapter_start = True
                break
        
        if not is_chapter_start:
            current_chapter["content"].append(line)
    
    if current_chapter["content"]:
        chapters.append(current_chapter)
    
    return chapters


def format_book_summary(book_summary: dict) -> str:
    """Format book summary as readable text"""
    output = []
    
    output.append(f"# {book_summary['title']}")
    if book_summary['author'] != "Unknown Author":
        output.append(f"**Author:** {book_summary['author']}")
    output.append(f"**Total Chapters:** {book_summary['total_chapters']}")
    output.append("")
    
    output.append("## Chapter Summaries")
    for chapter in book_summary['chapters']:
        output.append(f"\n### Chapter {chapter['number']}: {chapter['title']}")
        output.append(chapter['summary'])
    
    return "\n".join(output)