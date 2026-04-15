"""
Adaptive Summarizer - Routes to appropriate strategy based on document type
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.document_detector import detect_document_type
from summarization.general_summarizer import summarize_general
from summarization.paper_summarizer import summarize_paper_structured, format_paper_summary
from summarization.book_summarizer import summarize_book_structured, format_book_summary


def adaptive_summarize(text: str, return_structured: bool = False, max_tokens: int = None):
    """
    Main entry point for adaptive summarization
    
    Args:
        text: Input text to summarize
        return_structured: If True, return dict; if False, return formatted string
        max_tokens: Maximum tokens for output (default: 1500)
    """
    if max_tokens is None:
        max_tokens = 1500
    
    # Detect document type
    detection = detect_document_type(text)
    
    print("\n" + "=" * 50)
    print("📊 DOCUMENT ANALYSIS")
    print("=" * 50)
    print(f"   Type: {detection['type'].upper()}")
    print(f"   Confidence: {detection['confidence']*100:.0f}%")
    print(f"   Pages: ~{detection['metadata']['pages']}")
    print(f"   Words: {detection['metadata']['words']:,}")
    print("=" * 50 + "\n")
    
    # Route to appropriate summarizer
    if detection["type"] == "book" and detection["confidence"] > 0.6:
        result = summarize_book_structured(text, detection, max_tokens)
        
        if return_structured:
            return result
        else:
            return format_book_summary(result)
    
    elif detection["type"] == "paper" and detection["confidence"] > 0.5:
        result = summarize_paper_structured(text, detection, max_tokens)
        
        if return_structured:
            return result
        else:
            return format_paper_summary(result)
    
    else:
        result = summarize_general(text, detection, max_tokens)
        
        if return_structured:
            return result
        else:
            return result.get("summary", "No summary generated")


def summarize(text: str, max_tokens: int = None) -> str:
    """Quick summary - returns formatted string"""
    return adaptive_summarize(text, return_structured=False, max_tokens=max_tokens)


def summarize_structured(text: str, max_tokens: int = None) -> dict:
    """Structured summary - returns dict with metadata"""
    return adaptive_summarize(text, return_structured=True, max_tokens=max_tokens)


__all__ = ['adaptive_summarize', 'summarize', 'summarize_structured']