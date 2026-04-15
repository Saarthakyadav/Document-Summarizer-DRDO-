"""
Refine-based summarizer - uses iterative refinement for better coverage
"""
import time
import re
from typing import List, Dict

from generation.groq_summarizer2 import _call_groq, clean_summary_text
from generation.prompts import (
    CHUNK_SUMMARY_PROMPT,
    REFINE_PROMPT,
    FINAL_CLEANUP_PROMPT
)


def summarize_chunk_refine(chunk_text: str) -> str:
    """Summarize a single chunk using the chunk-level prompt"""
    if not chunk_text or not chunk_text.strip():
        return ""
    
    if len(chunk_text) > 6000:
        chunk_text = chunk_text[:6000]
    
    prompt = CHUNK_SUMMARY_PROMPT.format(chunk=chunk_text)
    result = _call_groq(prompt, max_tokens=500, temperature=0.3)
    
    return clean_summary_text(result) if result else ""


def refine_summary(existing_summary: str, new_chunk: str) -> str:
    """Refine existing summary with new chunk information - NO REPETITION"""
    if not existing_summary:
        return summarize_chunk_refine(new_chunk)
    
    if not new_chunk or not new_chunk.strip():
        return existing_summary
    
    if len(new_chunk) > 6000:
        new_chunk = new_chunk[:6000]
    
    # Limit existing summary to avoid token issues
    existing_limit = existing_summary[:3000]
    
    prompt = REFINE_PROMPT.format(
        summary=existing_limit,
        chunk=new_chunk
    )
    result = _call_groq(prompt, max_tokens=800, temperature=0.3)
    
    cleaned = clean_summary_text(result) if result else existing_summary
    
    # Post-process: remove duplicate bullet points
    lines = cleaned.split('\n')
    seen = set()
    unique_lines = []
    for line in lines:
        line_stripped = line.strip()
        # Skip empty lines
        if not line_stripped:
            unique_lines.append(line)
            continue
        # Check for duplicate content
        if line_stripped not in seen:
            seen.add(line_stripped)
            unique_lines.append(line)
        else:
            print(f"    Removed duplicate: {line_stripped[:50]}...")
    
    return '\n'.join(unique_lines)


def final_cleanup(summary: str) -> str:
    """Final cleanup and structuring of the summary - ENFORCE COMPRESSION"""
    if not summary or not summary.strip():
        return ""
    
    if len(summary) > 8000:
        summary = summary[:8000]
    
    prompt = FINAL_CLEANUP_PROMPT.format(content=summary)
    result = _call_groq(prompt, max_tokens=1000, temperature=0.2)
    
    cleaned = clean_summary_text(result) if result else summary
    
    # Additional post-processing: remove any remaining duplicates
    lines = cleaned.split('\n')
    seen = set()
    unique_lines = []
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            unique_lines.append(line)
            continue
        # Normalize for comparison (lowercase, remove punctuation)
        normalized = re.sub(r'[^\w\s]', '', line_stripped.lower())
        if normalized not in seen:
            seen.add(normalized)
            unique_lines.append(line)
    
    return '\n'.join(unique_lines)


def summarize_with_refine(chunks: List[str]) -> str:
    """
    Main refine-based summarization pipeline
    
    Process:
    1. Summarize first chunk
    2. Iteratively refine with each subsequent chunk (no repetition)
    3. Final cleanup with compression
    """
    if not chunks:
        return ""
    
    print(f"  📝 Refine summarization with {len(chunks)} chunks...")
    
    # Step 1: Summarize first chunk
    current_summary = summarize_chunk_refine(chunks[0])
    print(f"    Chunk 1/{len(chunks)} summarized ({len(current_summary)} chars)")
    
    # Step 2: Iteratively refine with remaining chunks
    for i, chunk in enumerate(chunks[1:], 2):
        print(f"    Refining with chunk {i}/{len(chunks)}...")
        current_summary = refine_summary(current_summary, chunk)
        print(f"      Current length: {len(current_summary)} chars")
        time.sleep(0.2)  # Rate limiting
    
    # Step 3: Final cleanup with compression
    print(f"    Final cleanup and compression...")
    final_summary = final_cleanup(current_summary)
    print(f"    Final length: {len(final_summary)} chars (compressed from {len(current_summary)})")
    
    return final_summary