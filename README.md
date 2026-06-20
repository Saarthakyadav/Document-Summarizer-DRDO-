# 📄 Adaptive Multi-Strategy Document Summarizer

A document summarization pipeline that **auto-detects document type** (book, research paper, or general document) and applies the appropriate summarization strategy. Built with Groq's Llama 3.1 8B, semantic chunking, parallel processing, and a refine-chain merge step that works correctly at any document length.

> **How this differs from [QueryBased_PDF_Summarizer](../QueryBased_PDF_Summarizer):**  
> That project is a retrieval-QA system (BM25 + dense retrieval, RRF fusion, cross-encoder reranking, RAGAS eval) — you ask questions and it finds answers. This project is a compression pipeline — you hand it a document and it produces a structured summary. Complementary skills, different architectures.

---

## 🎯 What It Does

- Upload any PDF or TXT document
- Automatic document-type detection: **Book / Research Paper / General**
  - **Book** → chapter-aware summarization with per-chapter summaries merged into an overview
  - **Research Paper** → section-by-section extraction (Abstract, Introduction, Methods, Results, Conclusion) refined into a structured summary; body sections are fully covered, not just abstract + conclusion
  - **General** → iterative refine-chain that handles any length without concatenation fallback
- Real-time progress streaming to the Streamlit UI
- Semantic deduplication across chunk summaries before merging
- Parallel summarization for large documents (configurable worker count)
- Comprehensive quality metrics (Cosine Similarity, Coverage, Compression, Redundancy, Flesch Readability)

---

## 🖥️ Deployed App

<https://intelligentdocumentsummarizer.streamlit.app/>

---

## 🏗️ Architecture

```
PDF / TXT Upload
       │
       ▼
OCR Ingestion (PyMuPDF + Tesseract)
       │
       ▼
Text Cleaning & Preprocessing
       │
       ▼
Document-Type Detection
  ├── confidence score for: book / paper / general
       │
       ▼
Semantic Chunking (boundary-aware, configurable overlap)
       │
       ▼
Chunk Summarization
  ├── ≤4 chunks → sequential (rate-limit safe)
  └── >4 chunks → parallel (ThreadPoolExecutor, 2 workers)
       │
       ▼
Semantic Deduplication (cosine similarity, threshold 0.75)
       │
       ▼
Refine-Chain Merge
  ├── Book:   chapter summaries → refine → overview
  ├── Paper:  section summaries → refine → structured output
  └── General: iterative refine over all deduped summaries + final compression pass
       │
       ▼
Quality Metrics (Cosine Sim, Coverage, Compression, Redundancy, Flesch)
       │
       ▼
Summary Output + Metrics Dashboard
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| PDF Processing | PyMuPDF (`fitz`) + Tesseract OCR |
| Chunking | Semantic boundary detection with configurable overlap |
| Embeddings | `all-MiniLM-L6-v2` (SentenceTransformers) — used for semantic dedup |
| LLM | Llama 3.1 8B Instruct via Groq API |
| Merge strategy | Iterative refine chain (not naive concatenation) |
| Web Interface | Streamlit |
| Metrics | Cosine Similarity, Flesch Readability, Coverage, Redundancy |
| Language | Python 3.10+ |

---

## 📁 Project Structure

```
document-summarizer/
├── app.py                          # Streamlit UI
├── main.py                         # Pipeline orchestrator (streaming)
├── ingestion/
│   ├── ocr_ingestion.py            # PDF/OCR extraction (PyMuPDF + Tesseract)
│   └── text_ingestion.py           # Plain-text loading
├── preprocessing/
│   └── text_cleaner.py             # OCR noise removal & normalisation
├── chunking/
│   └── text_chunker.py             # Semantic boundary-aware chunking
├── generation/
│   ├── groq_summarizer2.py         # Groq API client + chunk summarizer
│   └── prompts.py                  # Prompt templates (chunk, refine, cleanup)
├── summarization/
│   ├── adaptive_summarizer.py      # Document-type router
│   ├── refine_summarizer.py        # Iterative refine chain (core merge logic)
│   ├── general_summarizer.py       # General-doc wrapper over refine chain
│   ├── paper_summarizer.py         # Section-aware paper summarizer
│   └── book_summarizer.py          # Chapter-aware book summarizer
├── utils/
│   └── document_detector.py        # Heuristic doc-type classifier
├── evaluation/
│   └── summary_metrics.py          # Quality metrics
├── tests/
│   ├── test_detector.py            # Document detector tests
│   └── test_chunk_debug.py         # Chunking debug helpers
├── requirements.txt                # Runtime dependencies
├── pyproject.toml                  # Build metadata (mirrors requirements.txt)
├── runtime.txt                     # Python version for Streamlit Cloud
└── packages.txt                    # System packages for Streamlit Cloud
```

---

## 🚀 Setup

```bash
git clone <repo-url>
cd document-summarizer
pip install -r requirements.txt
```

Set your Groq API key:

```bash
echo "GROQ_API_KEY=your_key_here" > .env
```

Run:

```bash
streamlit run app.py
```

---

## ⚙️ Configuration

All tuning knobs are in `main.py`:

| Constant | Default | Effect |
|---|---|---|
| `PARALLEL_THRESHOLD` | 4 | Use parallel workers when chunk count exceeds this |
| `MAX_WORKERS` | 2 | Thread count for parallel summarization |
| `DEDUP_THRESHOLD` | 0.75 | Cosine similarity above which a chunk summary is dropped as duplicate |

Book chapter cap (`MAX_CHAPTERS = 5`) is in `summarization/book_summarizer.py`.

---

## 📊 Quality Metrics

| Metric | What it measures |
|---|---|
| Cosine Similarity | Semantic overlap between original and summary |
| Coverage | Key-term preservation rate |
| Compression | Word-count reduction ratio |
| Redundancy | Repeated n-gram fraction in the summary |
| Readability (Flesch) | Ease of reading score (informational only, not in overall) |
| Overall Score | Weighted composite of the above |
