# import time
# import re
# from typing import Generator, List, Dict, Any
# from concurrent.futures import ThreadPoolExecutor, as_completed

# from ingestion.ocr_ingestion import extract_text_from_ocr
# from ingestion.text_ingestion import load_text
# from preprocessing.text_cleaner import clean_text
# from generation.groq_summarizer2 import summarize_chunk_groq
# from chunking.text_chunker import hybrid_chunk_text
# from evaluation.summary_metrics import evaluate_summary

# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity

# dedup_model = SentenceTransformer("all-MiniLM-L6-v2")

# # Enable parallel processing for faster summarization (set to True for large docs)
# PARALLEL_SUMMARIZATION = True  # Set to True for faster processing on large docs
# MAX_PARALLEL_WORKERS = 2


# def is_valid_chunk(text: str) -> bool:
#     """Check if chunk is valid for ANY document type"""
#     if not text or not text.strip():
#         return False
#     text = text.strip()
#     if len(text) < 50:
#         return False
#     words = text.split()
#     if len(words) < 10:
#         return False
#     alpha_num = sum(c.isalnum() for c in text)
#     if len(text) > 0 and alpha_num / len(text) < 0.3:
#         return False
#     return True


# def safe_summarize(text, mode="Short Summary", max_retries=2):
#     for attempt in range(max_retries):
#         try:
#             result = summarize_chunk_groq(text, mode=mode)
#             if result and isinstance(result, str) and len(result.strip()) > 20:
#                 return result
#         except Exception as e:
#             print(f"⚠️ Attempt {attempt + 1} failed: {e}")
#         time.sleep(1)
#     return text[:500] + "..."


# def get_chunk_config(quality, doc_length=None):
#     """Adaptive chunk config based on quality and document length"""
#     if quality == "Fast":
#         base_tokens, base_overlap = 500, 1
#     elif quality == "Balanced":
#         base_tokens, base_overlap = 800, 2
#     else:
#         base_tokens, base_overlap = 1000, 3
    
#     if doc_length and doc_length > 50000:
#         base_tokens = min(1200, base_tokens + 200)
    
#     return base_tokens, base_overlap


# def get_compression_target(original_length: int) -> float:
#     """Return target compression ratio based on document length"""
#     if original_length < 1000:
#         return 2.0
#     elif original_length < 5000:
#         return 4.0
#     elif original_length < 20000:
#         return 6.0
#     elif original_length < 50000:
#         return 8.0
#     else:
#         return 10.0


# def semantic_dedup(summaries, threshold=0.75):
#     """Remove semantically similar summaries"""
#     if not summaries:
#         return summaries
#     embeddings = dedup_model.encode(summaries)
#     unique = []
#     used = set()
#     for i in range(len(summaries)):
#         if i in used:
#             continue
#         unique.append(summaries[i])
#         for j in range(i + 1, len(summaries)):
#             sim = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
#             if sim > threshold:
#                 used.add(j)
#     return unique


# def merge_summaries(summaries: List[str], mode: str, original_length: int) -> str:
#     """Merge multiple summaries into ONE coherent summary"""
#     if not summaries:
#         return ""
#     if len(summaries) == 1:
#         return summaries[0]
    
#     target_ratio = get_compression_target(original_length)
#     combined = "\n\n".join(summaries)
    
#     merge_prompt = f"""
# Merge these summaries into ONE coherent summary.

# TARGET: Compress to 1/{target_ratio} of current length.

# RULES:
# - Remove ALL duplicates
# - Keep key concepts only
# - Remove examples unless critical
# - Output flowing text or bullet points

# SUMMARIES:
# {combined}

# MERGED SUMMARY:
# """
#     # FIX: Use merge_prompt, not combined
#     result = safe_summarize(merge_prompt, mode=mode)
    
#     # Check if we hit target
#     current_len = len(result.split())
#     target_len = len(combined.split()) // target_ratio
    
#     if current_len > target_len * 1.5 and current_len > 300:
#         second_pass = f"Compress this further to {target_len} words:\n\n{result}"
#         result = safe_summarize(second_pass, mode=mode)
    
#     return result if result else combined[:1500]

# def improve_readability(text: str) -> str:
#     """Universal readability improvements"""
#     if not text:
#         return text
    
#     text = re.sub(r'\.([A-Z])', r'. \1', text)
#     text = re.sub(r'\.([a-z])', r'. \1', text)
#     text = re.sub(r':([A-Za-z])', r': \1', text)
#     text = re.sub(r'([.!?])\s+([A-Z][a-z])', r'\1\n\2', text)
#     text = re.sub(r'\n{3,}', '\n\n', text)
    
#     return text.strip()


# def summarize_chunks_parallel(chunks: List[str], mode: str):
#     """
#     Summarize chunks in parallel for faster processing
#     This is a generator function that yields (index, summary) pairs
#     """
#     summaries = [None] * len(chunks)
    
#     def summarize_at_index(i, chunk):
#         return i, safe_summarize(chunk, mode=mode)
    
#     with ThreadPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as executor:
#         futures = {executor.submit(summarize_at_index, i, chunk): i 
#                    for i, chunk in enumerate(chunks)}
        
#         for future in as_completed(futures):
#             i, summary = future.result()
#             summaries[i] = summary
#             yield i, summary  # Yield index and summary as a tuple
    
#     # Return all valid summaries
#     return [s for s in summaries if s and len(s.strip()) > 10]


# def run_pipeline_stream(file_path, mode="Short Summary", quality="Balanced", chunk_overlap=2) -> Generator:
#     start_total = time.time()
    
#     # Ingestion
#     t1 = time.time()
#     if file_path.lower().endswith(".pdf"):
#         text = extract_text_from_ocr(file_path)
#     else:
#         text = load_text(file_path)
    
#     text = clean_text(text)
#     t2 = time.time()
    
#     doc_length = len(text)
#     doc_words = len(text.split())
#     print(f"📥 Ingestion: {t2 - t1:.2f}s | {doc_length} chars, {doc_words} words")
    
#     if not text or len(text) < 100:
#         yield {"index": "final", "total": 1, "summary": "Failed to extract text.", "metrics": {}, "timing": {}}
#         return
    
#     # Chunking
#     t3 = time.time()
#     max_tokens, overlap_sentences = get_chunk_config(quality, doc_length)
#     chunk_objects = hybrid_chunk_text(text, max_tokens=max_tokens, overlap_sentences=chunk_overlap)
#     t4 = time.time()
#     print(f"🧩 Chunking: {t4 - t3:.2f}s | {len(chunk_objects)} chunks")
    
#     if not chunk_objects:
#         chunk_objects = [{"chunk_id": 0, "text": text[:8000], "token_count": doc_words}]
    
#     clean_groups = [c["text"] for c in chunk_objects if is_valid_chunk(c.get("text", ""))]
#     print(f"📊 Valid chunks: {len(clean_groups)}")
    
#     # Summarize each chunk (parallel or sequential)
#     t5 = time.time()
    
#     if PARALLEL_SUMMARIZATION and len(clean_groups) > 3:
#         print(f"⚡ Using parallel summarization ({MAX_PARALLEL_WORKERS} workers)...")
#         all_summaries = []
#         # The generator yields (index, summary) pairs
#         for idx, summary in summarize_chunks_parallel(clean_groups, mode):
#             if summary and len(summary.strip()) > 10:
#                 all_summaries.append(summary)
#             yield {"index": idx + 1, "total": len(clean_groups), "summary": summary if summary else "[Failed]"}
#     else:
#         print("📝 Using sequential summarization...")
#         all_summaries = []
#         for i, chunk in enumerate(clean_groups):
#             if len(chunk) > 8000:
#                 chunk = chunk[:8000]
#             summary = safe_summarize(chunk, mode=mode)
#             if summary and len(summary.strip()) > 10:
#                 all_summaries.append(summary)
#             yield {"index": i + 1, "total": len(clean_groups), "summary": summary if summary else "[Failed]"}
#             time.sleep(0.3)
    
#     t6 = time.time()
#     print(f"🧠 Summarization: {t6 - t5:.2f}s | {len(all_summaries)} summaries")
    
#     # Deduplicate
#     deduped = semantic_dedup(all_summaries, threshold=0.75)
#     print(f"📊 Dedup: {len(all_summaries)} → {len(deduped)}")
    
#     # Merge into final summary
#     if len(deduped) > 1:
#         print(f"🔄 Merging {len(deduped)} summaries...")
#         final_summary = merge_summaries(deduped, mode, doc_words)
#     else:
#         final_summary = deduped[0] if deduped else ""
    
#     # Improve readability
#     final_summary = improve_readability(final_summary)
    
#     # Metrics
#     try:
#         results = evaluate_summary(text, final_summary)
#     except Exception as e:
#         print(f"⚠️ Metrics error: {e}")
#         results = {}
    
#     end_total = time.time()
#     final_words = len(final_summary.split())
#     compression = doc_words / max(final_words, 1)
#     print(f"🚀 Total: {end_total - start_total:.2f}s | Compression: {compression:.1f}x")
    
#     yield {
#         "index": "final",
#         "total": len(clean_groups),
#         "summary": final_summary,
#         "metrics": results,
#         "timing": {
#             "ingestion": round(t2 - t1, 2),
#             "chunking": round(t4 - t3, 2),
#             "summarization": round(t6 - t5, 2),
#             "total": round(end_total - start_total, 2)
#         }
#     }
import time
import re
from typing import Generator, List

from ingestion.ocr_ingestion import extract_text_from_ocr
from ingestion.text_ingestion import load_text
from preprocessing.text_cleaner import clean_text
from generation.groq_summarizer2 import summarize_chunk_groq
from chunking.text_chunker import hybrid_chunk_text
from evaluation.summary_metrics import evaluate_summary

from sentence_transformers import SentenceTransformer

dedup_model = SentenceTransformer("all-MiniLM-L6-v2")


def is_valid_chunk(text: str) -> bool:
    """Check if chunk is valid"""
    if not text or not text.strip():
        return False
    text = text.strip()
    if len(text) < 50:
        return False
    words = text.split()
    if len(words) < 10:
        return False
    return True


def safe_summarize(text, max_retries=2):
    """Safe summarization with retries"""
    for attempt in range(max_retries):
        try:
            result = summarize_chunk_groq(text)
            if result and isinstance(result, str) and len(result.strip()) > 20:
                return result
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
        time.sleep(1)
    return None


def run_pipeline_stream(file_path, quality="Balanced", chunk_overlap=2) -> Generator:
    start_total = time.time()
    
    # Ingestion
    t1 = time.time()
    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_ocr(file_path)
    else:
        text = load_text(file_path)
    
    text = clean_text(text)
    t2 = time.time()
    
    doc_words = len(text.split())
    print(f"📥 Ingestion: {t2 - t1:.2f}s | {doc_words} words")
    
    if not text or len(text) < 100:
        yield {"type": "error", "message": "Failed to extract text."}
        return
    
    # Chunking
    t3 = time.time()
    
    # Adjust chunk size based on quality
    if quality == "Fast":
        max_tokens = 1000
    elif quality == "Balanced":
        max_tokens = 800
    else:
        max_tokens = 600
    
    chunks = hybrid_chunk_text(text, max_tokens=max_tokens, overlap_sentences=chunk_overlap)
    t4 = time.time()
    
    if not chunks:
        chunks = [{"chunk_id": 0, "text": text[:8000], "token_count": len(text.split())}]
    
    clean_groups = [c["text"] for c in chunks if is_valid_chunk(c.get("text", ""))]
    total_chunks = len(clean_groups)
    print(f"🧩 Chunking: {t4 - t3:.2f}s | {total_chunks} chunks")
    
    # Yield start of summary
    yield {
        "type": "summary_start",
        "total_chunks": total_chunks,
        "message": f"Processing {total_chunks} sections..."
    }
    
    # Summarize each chunk and yield immediately
    t5 = time.time()
    all_summaries = []
    accumulated_summary = ""
    
    for i, chunk in enumerate(clean_groups):
        chunk_start = time.time()
        
        # Truncate if too long
        if len(chunk) > 8000:
            chunk = chunk[:8000]
        
        # Summarize chunk
        summary = safe_summarize(chunk)
        
        chunk_time = time.time() - chunk_start
        print(f"  Chunk {i+1}/{total_chunks}: {chunk_time:.1f}s")
        
        if summary and len(summary.strip()) > 10:
            all_summaries.append(summary)
            
            # Yield this chunk's summary immediately
            yield {
                "type": "chunk_summary",
                "chunk_index": i + 1,
                "total_chunks": total_chunks,
                "summary": summary,
                "is_last": (i == total_chunks - 1)
            }
        else:
            # Yield error for this chunk but continue
            yield {
                "type": "chunk_error",
                "chunk_index": i + 1,
                "total_chunks": total_chunks,
                "message": "Failed to summarize this section"
            }
        
        # Small delay to avoid rate limiting
        time.sleep(0.2)
    
    t6 = time.time()
    print(f"🧠 Summarization: {t6 - t5:.2f}s | {len(all_summaries)} summaries")
    
    # Merge all summaries into final
    if len(all_summaries) > 1:
        print("🔄 Merging summaries...")
        combined = "\n\n".join(all_summaries)
        
        # For large documents, do a simple merge without API call
        if len(combined) > 10000:
            # Simple concatenation is fine
            final_summary = combined
            yield {
                "type": "merge_warning",
                "message": "Document was large - summaries are concatenated"
            }
        else:
            # Try to merge with API
            merge_result = safe_summarize(f"Combine these into one coherent summary:\n\n{combined}")
            final_summary = merge_result if merge_result else combined
    else:
        final_summary = all_summaries[0] if all_summaries else ""
    
    # Calculate metrics (don't let this block)
    t7 = time.time()
    try:
        results = evaluate_summary(text, final_summary)
    except Exception as e:
        print(f"⚠️ Metrics error: {e}")
        results = {}
    t8 = time.time()
    
    end_total = time.time()
    final_words = len(final_summary.split())
    compression = doc_words / max(final_words, 1)
    
    # Yield final summary with metrics
    yield {
        "type": "final",
        "summary": final_summary,
        "metrics": results,
        "timing": {
            "ingestion": round(t2 - t1, 2),
            "chunking": round(t4 - t3, 2),
            "summarization": round(t6 - t5, 2),
            "metrics": round(t8 - t7, 2),
            "total": round(end_total - start_total, 2)
        },
        "compression": round(compression, 1),
        "total_chunks": total_chunks,
        "chunks_summarized": len(all_summaries)
    }