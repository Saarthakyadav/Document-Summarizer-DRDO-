"""
Adaptive Summarizer — routes to the correct strategy based on document type
and returns a normalised (type, summary_text, metadata) result.

This is the single entry point that main.py calls. It is NOT a streaming
function; main.py wraps calls here with its own progress-yield loop.
"""
from utils.document_detector import detect_document_type
from summarization.general_summarizer import summarize_general
from summarization.paper_summarizer import summarize_paper_structured, format_paper_summary
from summarization.book_summarizer import summarize_book_structured, format_book_summary


def adaptive_summarize(text: str) -> dict:
    """
    Detect document type, route to the matching strategy, and return:
        {
            "doc_type": "book" | "paper" | "general",
            "confidence": float,
            "summary": str,
            "metadata": dict,
        }
    """
    detection = detect_document_type(text)
    doc_type = detection["type"]
    confidence = detection["confidence"]

    print(f"\n{'='*50}")
    print("📊 DOCUMENT ANALYSIS")
    print(f"   Type:       {doc_type.upper()}")
    print(f"   Confidence: {confidence*100:.0f}%")
    print(f"   Words:      {detection['metadata']['words']:,}")
    print(f"   Pages (est): ~{detection['metadata']['pages']}")
    print(f"{'='*50}\n")

    if doc_type == "book" and confidence > 0.6:
        result = summarize_book_structured(text, detection)
        summary = format_book_summary(result)
        metadata = {**result["metadata"],
                    "chapters_summarized": result["chapters_summarized"],
                    "total_chapters": result["total_chapters"]}

    elif doc_type == "paper" and confidence > 0.5:
        result = summarize_paper_structured(text, detection)
        summary = format_paper_summary(result)
        metadata = {**result["metadata"],
                    "sections_found": result.get("sections_found", [])}

    else:
        # General: refine-chain pipeline (handles any size correctly)
        result = summarize_general(text, detection)
        summary = result.get("summary", "")
        metadata = result.get("metadata", {})

    return {
        "doc_type": doc_type,
        "confidence": confidence,
        "summary": summary,
        "metadata": metadata,
    }
