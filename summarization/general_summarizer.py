# """
# General Document Summarizer - For non-book, non-paper documents
# """
# import time
# from typing import List, Dict
# import re
# from chunking.text_chunker import hybrid_chunk_text
# from generation.groq_summarizer2 import summarize_chunk_groq
# from preprocessing.text_cleaner import clean_text

# # def summarize_general(text: str, detection: dict = None, max_tokens: int = None) -> dict:
# #     """
# #     General document summarizer with better completeness
# #     """
# #     print(f"📁 Using GENERAL summarization strategy")
    
# #     if max_tokens is None:
# #         max_tokens = 2000  # Increased for completeness
    
# #     text = clean_text(text)
    
# #     # Use smaller chunks for better detail preservation
# #     chunks = hybrid_chunk_text(text, max_tokens=600, overlap_sentences=2)  # Smaller chunks = more detail
    
# #     if not chunks:
# #         chunks = [{"chunk_id": 0, "text": text[:8000], "token_count": len(text.split())}]
    
# #     print(f"  Processing {len(chunks)} chunks...")
    
# #     # Summarize each chunk with completeness focus
# #     all_summaries = []
# #     for i, chunk in enumerate(chunks):
# #         chunk_text = chunk["text"]
# #         if len(chunk_text) > 8000:
# #             chunk_text = chunk_text[:8000]
        
# #         # Add instruction to preserve details
# #         enhanced_text = f"Preserve ALL key details from this section:\n\n{chunk_text}"
# #         summary = summarize_chunk_groq(enhanced_text)
        
# #         if summary and len(summary.strip()) > 10:
# #             all_summaries.append(summary)
        
# #         print(f"  ✓ Chunk {i+1}/{len(chunks)}")
# #         time.sleep(0.1)
    
# #     # Merge with completeness instruction
# #     if len(all_summaries) > 1:
# #         combined = "\n\n".join(all_summaries)
# #         merge_prompt = f"""Merge these section summaries into ONE complete document summary.

# # CRITICAL: Keep ALL topics and subtopics. Do NOT remove any section.
# # Organize them under appropriate headings. Preserve all definitions, examples, and formulas.

# # SECTIONS:
# # {combined}

# # COMPLETE MERGED SUMMARY:"""
        
# #         # Use a separate call for merging with higher token limit
# #         final_summary = summarize_chunk_groq(merge_prompt)
# #     else:
# #         final_summary = all_summaries[0] if all_summaries else ""
    
# #     return {
# #         "type": "general",
# #         "summary": final_summary,
# #         "chunks_processed": len(chunks),
# #         "summaries_count": len(all_summaries),
# #         "metadata": detection["metadata"] if detection else {}
# #     }

# # def summarize_general(text: str, detection: dict = None, max_tokens: int = None) -> dict:
# #     """
# #     General document summarizer with compression enforcement
# #     """
# #     print(f"📁 Using GENERAL summarization strategy")
    
# #     if max_tokens is None:
# #         max_tokens = 1000  # Reduced from 2000
    
# #     text = clean_text(text)
# #     original_length = len(text)
    
# #     # Use larger chunks for better context
# #     chunks = hybrid_chunk_text(text, max_tokens=1000, overlap_sentences=2)
    
# #     if not chunks:
# #         chunks = [{"chunk_id": 0, "text": text[:8000], "token_count": len(text.split())}]
    
# #     print(f"  Processing {len(chunks)} chunks...")
    
# #     # Summarize each chunk with compression instruction
# #     all_summaries = []
# #     for i, chunk in enumerate(chunks):
# #         chunk_text = chunk["text"]
# #         if len(chunk_text) > 8000:
# #             chunk_text = chunk_text[:8000]
        
# #         # Add compression instruction
# #         compressed_text = f"Summarize concisely (aim for 30% of original length):\n\n{chunk_text}"
# #         summary = summarize_chunk_groq(compressed_text)
        
# #         if summary and len(summary.strip()) > 10:
# #             all_summaries.append(summary)
        
# #         print(f"  ✓ Chunk {i+1}/{len(chunks)}")
# #         time.sleep(0.1)
    
# #     # Merge with compression
# #     if len(all_summaries) > 1:
# #         combined = "\n\n".join(all_summaries)
        
# #         # Only merge if combined is not too large
# #         if len(combined) > 5000:
# #             # Simple concatenation for large documents (faster, no API call)
# #             final_summary = combined
# #             print("  ⚠️ Document large - using concatenated summaries")
# #         else:
# #             merge_prompt = f"""Merge these section summaries into ONE concise document summary.

# # CRITICAL: Be CONCISE. Remove redundant information.
# # Keep key concepts, definitions, and main examples.
# # Target length: 30-40% of the combined length.

# # SECTIONS:
# # {combined}

# # CONCISE MERGED SUMMARY:"""
            
# #             final_summary = summarize_chunk_groq(merge_prompt)
# #     else:
# #         final_summary = all_summaries[0] if all_summaries else ""
    
# #     # Check compression and warn if needed
# #     final_length = len(final_summary)
# #     compression_ratio = original_length / max(final_length, 1)
    
# #     if compression_ratio < 1.0:
# #         print(f"  ⚠️ Warning: Summary is longer than original ({compression_ratio:.1f}x compression)")
# #         print(f"     Original: {original_length} chars, Summary: {final_length} chars")
    
# #     return {
# #         "type": "general",
# #         "summary": final_summary,
# #         "chunks_processed": len(chunks),
# #         "summaries_count": len(all_summaries),
# #         "compression_ratio": round(compression_ratio, 2),
# #         "metadata": detection["metadata"] if detection else {}
# #     }

# def summarize_general(text: str, detection: dict = None, max_tokens: int = None) -> dict:
#     """
#     General document summarizer with coverage enforcement
#     """
#     print(f"📁 Using GENERAL summarization strategy")
    
#     if max_tokens is None:
#         max_tokens = 2000  # Balanced for coverage and compression
    
#     text = clean_text(text)
#     original_length = len(text)
    
#     # Count major topics in original (headings/sections)
#     headings = re.findall(r'(?m)^(?:#+\s+)?([A-Z][A-Za-z\s]+)', text)
#     num_topics = len(headings) if headings else 5
#     print(f"  Detected ~{num_topics} major topics to cover")
    
#     # Use medium chunks for balance
#     chunks = hybrid_chunk_text(text, max_tokens=800, overlap_sentences=2)
    
#     if not chunks:
#         chunks = [{"chunk_id": 0, "text": text[:8000], "token_count": len(text.split())}]
    
#     print(f"  Processing {len(chunks)} chunks...")
    
#     # Summarize each chunk with coverage instruction
#     all_summaries = []
#     for i, chunk in enumerate(chunks):
#         chunk_text = chunk["text"]
#         if len(chunk_text) > 8000:
#             chunk_text = chunk_text[:8000]
        
#         # Instruction to preserve all topics in this chunk
#         enhanced_text = f"Cover ALL key topics in this section. Be thorough but concise:\n\n{chunk_text}"
#         summary = summarize_chunk_groq(enhanced_text)
        
#         if summary and len(summary.strip()) > 10:
#             all_summaries.append(summary)
        
#         print(f"  ✓ Chunk {i+1}/{len(chunks)}")
#         time.sleep(0.1)
    
#     # Merge with coverage check
#     if len(all_summaries) > 1:
#         combined = "\n\n".join(all_summaries)
        
#         # Check if combined is too long
#         if len(combined) > 8000:
#             # Intelligent merge - keep all headings
#             merge_prompt = f"""Merge these section summaries into ONE complete summary.

# IMPORTANT: 
# - Keep ALL section headings and their content
# - Remove only exact duplicate information
# - Do NOT remove any major topic
# - Preserve all definitions, formulas, and examples

# SECTIONS:
# {combined}

# COMPLETE MERGED SUMMARY:"""
            
#             final_summary = summarize_chunk_groq(merge_prompt)
#         else:
#             final_summary = combined
#     else:
#         final_summary = all_summaries[0] if all_summaries else ""
    
#     # Calculate metrics
#     final_length = len(final_summary)
#     compression_ratio = original_length / max(final_length, 1)
    
#     # Estimate coverage based on heading preservation
#     summary_headings = re.findall(r'(?m)^(?:###\s+)?([A-Z][A-Za-z\s]+)', final_summary)
#     coverage_estimate = len(set(headings[:10]).intersection(set(summary_headings))) / max(len(headings[:10]), 1)
    
#     print(f"  📊 Compression: {compression_ratio:.1f}x, Coverage estimate: {coverage_estimate:.0%}")
    
#     return {
#         "type": "general",
#         "summary": final_summary,
#         "chunks_processed": len(chunks),
#         "summaries_count": len(all_summaries),
#         "compression_ratio": round(compression_ratio, 2),
#         "coverage_estimate": round(coverage_estimate, 2),
#         "metadata": detection["metadata"] if detection else {}
#     }

"""
General Document Summarizer - With refine-based summarization
"""
import time
from typing import List, Dict

from chunking.text_chunker import hybrid_chunk_text
from preprocessing.text_cleaner import clean_text
from summarization.refine_summarizer import summarize_with_refine


def summarize_general(text: str, detection: dict = None, max_tokens: int = None) -> dict:
    """
    General document summarizer using refine-based approach
    """
    print(f"📁 Using GENERAL summarization strategy (Refine-based)")
    
    # Clean text
    text = clean_text(text)
    original_length = len(text)
    
    # Chunk the document - larger chunks for better context
    chunks = hybrid_chunk_text(text, max_tokens=1000, overlap_sentences=2)
    
    if not chunks:
        chunks = [{"chunk_id": 0, "text": text[:8000], "token_count": len(text.split())}]
    
    # Extract just the text from chunks
    chunk_texts = [c["text"] for c in chunks if c.get("text", "").strip()]
    
    print(f"  Processing {len(chunk_texts)} chunks using refine chain...")
    
    # Use refine-based summarization
    final_summary = summarize_with_refine(chunk_texts)
    
    # Calculate compression
    final_length = len(final_summary)
    compression_ratio = original_length / max(final_length, 1)
    
    print(f"  📊 Compression: {compression_ratio:.1f}x")
    
    return {
        "type": "general",
        "summary": final_summary,
        "chunks_processed": len(chunk_texts),
        "compression_ratio": round(compression_ratio, 2),
        "metadata": detection["metadata"] if detection else {}
    }