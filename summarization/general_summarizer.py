"""
General Document Summarizer — refine-chain pipeline for arbitrary documents.
"""
from chunking.text_chunker import hybrid_chunk_text
from preprocessing.text_cleaner import clean_text
from summarization.refine_summarizer import summarize_with_refine


def summarize_general(text: str, detection: dict = None, max_tokens: int = None) -> dict:
    """
    Refine-chain summarization for general documents.
    Works correctly at any document length — no naive concatenation fallback.
    """
    print("📁 Using GENERAL summarization strategy (refine chain)")

    text = clean_text(text)
    original_length = len(text)

    chunks = hybrid_chunk_text(text, max_tokens=1_000, overlap_sentences=2)
    if not chunks:
        chunks = [{"chunk_id": 0, "text": text[:8_000], "token_count": len(text.split())}]

    chunk_texts = [c["text"] for c in chunks if c.get("text", "").strip()]
    print(f"  Processing {len(chunk_texts)} chunks via refine chain…")

    final_summary = summarize_with_refine(chunk_texts)

    compression_ratio = original_length / max(len(final_summary), 1)
    print(f"  📊 Compression: {compression_ratio:.1f}x")

    return {
        "type": "general",
        "summary": final_summary,
        "chunks_processed": len(chunk_texts),
        "compression_ratio": round(compression_ratio, 2),
        "metadata": detection["metadata"] if detection else {},
    }
