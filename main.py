"""
Pipeline orchestrator.

Streams progress events to the Streamlit front-end while running:
  1. Ingestion (PDF/OCR or plain text)
  2. Cleaning
  3. Document-type detection
  4. Chunking
  5. Parallel or sequential per-chunk summarization
  6. Semantic dedup
  7. Refine-chain merge
  8. Quality metrics

Event schema (all items yielded are dicts with a "type" key):
  doc_detected   – document type + confidence
  summary_start  – pipeline stats (ingestion time, chunking time, chunk count)
  chunk_summary  – one chunk done (for progress bar)
  final          – summary + metrics + timing
  error          – fatal failure
"""

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Generator, List

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity as sk_cosine

from chunking.text_chunker import hybrid_chunk_text
from evaluation.summary_metrics import evaluate_summary
from generation.groq_summarizer2 import summarize_chunk_groq, _call_groq, clean_summary_text
from generation.prompts import REFINE_PROMPT, FINAL_CLEANUP_PROMPT
from ingestion.ocr_ingestion import extract_text_from_ocr
from ingestion.text_ingestion import load_text
from preprocessing.text_cleaner import clean_text
from utils.document_detector import detect_document_type

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PARALLEL_THRESHOLD = 4
MAX_WORKERS = 2
DEDUP_THRESHOLD = 0.75
MERGE_MODEL_NAME = "all-MiniLM-L6-v2"

_dedup_model: SentenceTransformer | None = None


def _get_dedup_model() -> SentenceTransformer:
    global _dedup_model
    if _dedup_model is None:
        _dedup_model = SentenceTransformer(MERGE_MODEL_NAME)
    return _dedup_model


# ---------------------------------------------------------------------------
# Chunk helpers
# ---------------------------------------------------------------------------
def is_valid_chunk(text: str) -> bool:
    if not text or not text.strip():
        return False
    text = text.strip()
    if len(text) < 50 or len(text.split()) < 10:
        return False
    alpha = sum(c.isalnum() for c in text)
    return (alpha / len(text)) >= 0.3


def chunk_config(quality: str, doc_length: int) -> int:
    base = {"Fast": 1_000, "Balanced": 800, "High Quality": 600}.get(quality, 800)
    if doc_length > 50_000:
        base = min(1_200, base + 200)
    return base


# ---------------------------------------------------------------------------
# Safe summarizer with retries
# ---------------------------------------------------------------------------
def safe_summarize(text: str, max_retries: int = 2) -> str | None:
    for attempt in range(max_retries):
        try:
            result = summarize_chunk_groq(text)
            if result and len(result.strip()) > 20:
                return result
        except Exception as exc:
            print(f"  ⚠️  Attempt {attempt + 1} failed: {exc}")
        time.sleep(1)
    return None


# ---------------------------------------------------------------------------
# Parallel summarization
# ---------------------------------------------------------------------------
def _summarize_parallel(chunks: List[str]) -> List[tuple[int, str]]:
    results: List[tuple[int, str]] = []

    def _worker(idx: int, chunk: str) -> tuple[int, str | None]:
        return idx, safe_summarize(chunk)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(_worker, i, c): i for i, c in enumerate(chunks)}
        for fut in as_completed(futures):
            idx, summary = fut.result()
            results.append((idx, summary))

    return results


# ---------------------------------------------------------------------------
# Semantic dedup
# ---------------------------------------------------------------------------
def semantic_dedup(summaries: List[str]) -> List[str]:
    if len(summaries) <= 1:
        return summaries
    model = _get_dedup_model()
    embeddings = model.encode(summaries)
    kept, dropped = [], set()
    for i in range(len(summaries)):
        if i in dropped:
            continue
        kept.append(summaries[i])
        for j in range(i + 1, len(summaries)):
            sim = float(sk_cosine([embeddings[i]], [embeddings[j]])[0][0])
            if sim > DEDUP_THRESHOLD:
                dropped.add(j)
    print(f"  Dedup: {len(summaries)} → {len(kept)} summaries kept")
    return kept


# ---------------------------------------------------------------------------
# Merge with refine chain
# ---------------------------------------------------------------------------
def merge_summaries(summaries: List[str]) -> str:
    if not summaries:
        return ""
    if len(summaries) == 1:
        return summaries[0]

    print(f"  🔄 Merging {len(summaries)} summaries via refine chain…")

    running = summaries[0]
    for s in summaries[1:]:
        prompt = REFINE_PROMPT.format(summary=running[:3_000], chunk=s)
        result = _call_groq(prompt, max_tokens=800, temperature=0.3)
        running = clean_summary_text(result) if result else running + "\n\n" + s
        time.sleep(0.2)

    cleanup_prompt = FINAL_CLEANUP_PROMPT.format(content=running[:8_000])
    final = _call_groq(cleanup_prompt, max_tokens=1_000, temperature=0.2)
    return clean_summary_text(final) if final else running


# ---------------------------------------------------------------------------
# Readability post-processor
# ---------------------------------------------------------------------------
def improve_readability(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"\.([A-Z])", r". \1", text)
    text = re.sub(r":([A-Za-z])", r": \1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Main streaming pipeline
# ---------------------------------------------------------------------------
def run_pipeline_stream(
    file_path: str,
    quality: str = "Balanced",
    chunk_overlap: int = 2,
) -> Generator:
    start_total = time.time()

    # 1. Ingestion
    t1 = time.time()
    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_ocr(file_path)
    else:
        text = load_text(file_path)

    text = clean_text(text)
    t2 = time.time()

    doc_length = len(text)
    doc_words = len(text.split())
    ingestion_time = round(t2 - t1, 2)
    print(f"📥 Ingestion: {ingestion_time}s | {doc_words} words")

    if not text or doc_length < 100:
        yield {"type": "error", "message": "Failed to extract text from document."}
        return

    # 2. Document-type detection
    detection = detect_document_type(text)
    doc_type = detection["type"]
    confidence = detection["confidence"]
    print(f"🔍 Detected: {doc_type.upper()} ({confidence*100:.0f}% confidence)")

    yield {
        "type": "doc_detected",
        "doc_type": doc_type,
        "confidence": confidence,
        "words": doc_words,
    }

    # 3. Chunking
    t3 = time.time()
    max_tokens = chunk_config(quality, doc_length)
    raw_chunks = hybrid_chunk_text(text, max_tokens=max_tokens, overlap_sentences=chunk_overlap)
    t4 = time.time()

    if not raw_chunks:
        raw_chunks = [{"chunk_id": 0, "text": text[:8_000], "token_count": doc_words}]

    clean_chunks = [c["text"] for c in raw_chunks if is_valid_chunk(c.get("text", ""))]
    total_chunks = len(clean_chunks)
    chunking_time = round(t4 - t3, 2)
    print(f"🧩 Chunking: {chunking_time}s | {total_chunks} valid chunks")

    yield {
        "type": "summary_start",
        "total_chunks": total_chunks,
        "doc_type": doc_type,
        "confidence": confidence,
        "words": doc_words,
        "ingestion_time": ingestion_time,
        "chunking_time": chunking_time,
        "message": f"Processing {total_chunks} sections…",
    }

    # 4. Summarize chunks
    t5 = time.time()
    all_summaries: List[str | None] = [None] * total_chunks

    if total_chunks > PARALLEL_THRESHOLD:
        print(f"⚡ Parallel summarization ({MAX_WORKERS} workers) for {total_chunks} chunks")
        completed_pairs = _summarize_parallel(clean_chunks)
        for idx, summary in sorted(completed_pairs, key=lambda p: p[0]):
            all_summaries[idx] = summary
            yield {
                "type": "chunk_summary",
                "chunk_index": idx + 1,
                "total_chunks": total_chunks,
                "summary": summary or "[Failed]",
                "is_last": idx == total_chunks - 1,
            }
    else:
        print(f"📝 Sequential summarization for {total_chunks} chunks")
        for i, chunk in enumerate(clean_chunks):
            if len(chunk) > 8_000:
                chunk = chunk[:8_000]
            summary = safe_summarize(chunk)
            all_summaries[i] = summary
            yield {
                "type": "chunk_summary",
                "chunk_index": i + 1,
                "total_chunks": total_chunks,
                "summary": summary or "[Failed]",
                "is_last": i == total_chunks - 1,
            }
            time.sleep(0.2)

    t6 = time.time()
    valid_summaries = [s for s in all_summaries if s and len(s.strip()) > 10]
    print(f"🧠 Summarization: {t6-t5:.2f}s | {len(valid_summaries)}/{total_chunks} succeeded")

    # 5. Semantic dedup + merge
    deduped = semantic_dedup(valid_summaries)
    final_summary = merge_summaries(deduped)
    final_summary = improve_readability(final_summary)

    # 6. Metrics
    t7 = time.time()
    try:
        metrics = evaluate_summary(text, final_summary)
    except Exception as exc:
        print(f"⚠️  Metrics error: {exc}")
        metrics = {}
    t8 = time.time()

    end_total = time.time()
    final_words = len(final_summary.split())
    compression = doc_words / max(final_words, 1)

    print(f"✅ Done: {end_total-start_total:.1f}s total | {compression:.1f}x compression")

    yield {
        "type": "final",
        "summary": final_summary,
        "metrics": metrics,
        "doc_type": doc_type,
        "confidence": confidence,
        "compression": round(compression, 1),
        "total_chunks": total_chunks,
        "chunks_summarized": len(valid_summaries),
        "timing": {
            "ingestion": ingestion_time,
            "chunking": chunking_time,
            "summarization": round(t6 - t5, 2),
            "metrics": round(t8 - t7, 2),
            "total": round(end_total - start_total, 2),
        },
    }