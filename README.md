# Document-Summarizer-DRDO
# 📄 Adaptive Multi-Strategy Document Summarizer

An intelligent document summarization pipeline that **auto-detects document type** (book, research paper, or general document) and applies the matching summarization strategy. Upload a PDF or TXT file and get a structured, high-quality summary — backed by semantic chunking, parallel processing, semantic deduplication, and a refine-chain merge step that scales correctly to any document length.

> Companion project: a separate retrieval-QA system (RAG, BM25 + dense retrieval, citations) answers questions *about* documents. This project instead *compresses* a whole document into a structured summary — different architecture, complementary use case.

---

## 🎯 What it does

- Upload a PDF or TXT document
- Automatic document-type detection with a confidence score: **Book / Research Paper / General**
  - **Book** → chapter-aware summarization, with per-chapter summaries merged into an overview
  - **Research Paper** → section-by-section extraction (Abstract, Introduction, Methodology, Results, Discussion, Conclusion) refined into a structured summary
  - **General** → iterative refine-chain that handles any document length without a naive concatenation fallback
- Real-time progress streaming in the Streamlit UI (detection → chunking → summarization → merge)
- Semantic deduplication across chunk summaries before merging
- Parallel summarization for large documents (configurable worker count)
- Quality metrics dashboard: Coverage, Compression, Redundancy, Readability, and an overall weighted score

---

```
Input:  research_paper.pdf  (18 pages)

Detected type: Research Paper (92% confidence)
Chunks: 14 → summarized in parallel (2 workers)
Deduplication: 3 redundant chunk summaries removed

Output Summary:
• Abstract & Introduction — problem statement and motivation condensed to 2 sentences
• Methodology — key approach and experimental setup
• Results — main findings with quantitative highlights preserved
• Conclusion — contributions and future work

Metrics: Coverage 0.81 | Compression 4.6x | Redundancy 0.06 | Overall Score 0.78
```

---

## 🖥️ Deployed Link
https://intelligentdocumentsummarizer.streamlit.app/

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
  ├── ≤4 chunks  → sequential (rate-limit safe)
  └── >4 chunks  → parallel (ThreadPoolExecutor, 2 workers)
       │
       ▼
Semantic Deduplication (cosine similarity, threshold 0.75)
       │
       ▼
Refine-Chain Merge
  ├── Book:    chapter summaries → refine → overview
  ├── Paper:   section summaries → refine → structured output
  └── General: iterative refine over deduped summaries + final compression pass
       │
       ▼
Quality Metrics (Coverage, Compression, Redundancy, Flesch Readability)
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
| LLM | Llama 3.1 8B Instant via Groq API |
| Merge strategy | Iterative refine chain (not naive concatenation) |
| Web Interface | Streamlit |
| Metrics | Coverage, Compression, Redundancy, Flesch Readability |
| Language | Python 3.10+ |

---

## 📁 Project Structure

```
Document-Summarizer-DRDO/
├── app.py                          # Streamlit web application
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
├── packages.txt                    # System packages for Streamlit Cloud (Tesseract, Poppler)
└── .gitignore
```

---

## ⚡ Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/Document-Summarizer-DRDO.git
cd Document-Summarizer-DRDO
```

### 2. Create a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# or
source .venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

On Linux/Streamlit Cloud, Tesseract OCR and Poppler are also required as system packages (see `packages.txt`):
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils
```

### 4. Set up your API key

Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
```

Get your key here:
- **Groq API key:** https://console.groq.com

### 5. Run the app
```bash
streamlit run app.py
```

---

## 🔧 Configuration

Core tuning knobs are in `main.py`:

| Constant | Default | Effect |
|---|---|---|
| `PARALLEL_THRESHOLD` | `4` | Use parallel workers when chunk count exceeds this |
| `MAX_WORKERS` | `2` | Thread count for parallel summarization |
| `DEDUP_THRESHOLD` | `0.75` | Cosine similarity above which a chunk summary is dropped as duplicate |

Book chapter cap (`MAX_CHAPTERS = 5`) is in `summarization/book_summarizer.py`.

The UI also exposes a **Quality vs Speed** slider and a **Chunk Overlap** slider in the sidebar at runtime.

---

## 📖 How to Use

1. **Open the app** at `https://intelligentdocumentsummarizer.streamlit.app/`
2. **Upload a PDF or TXT** file using the file uploader
3. Optionally adjust **Quality vs Speed** and **Chunk Overlap** in the sidebar
4. **Click "Generate Summary"** — watch live progress (detection → chunking → summarization → merge)
5. **View the summary**, along with the quality metrics dashboard (Coverage, Compression, Redundancy, Readability, Overall Score)

---

## ✨ Features

- **Auto document-type detection** — book, research paper, or general, with a confidence score
- **Strategy-specific summarization** — chapter-aware, section-aware, or iterative refine, depending on type
- **Refine-chain merge** — avoids the quality loss of naive concatenation at any document length
- **Semantic deduplication** — removes redundant chunk summaries before merging
- **Parallel processing** — configurable worker count for large documents
- **OCR support** — handles scanned PDFs via Tesseract
- **Live progress streaming** — see each pipeline stage as it runs
- **Built-in quality metrics** — objective scoring instead of just trusting the LLM's output

---

## 🔑 API Keys Required

| Service | Purpose | Get it at |
|---|---|---|
| Groq | LLM inference (chunk summarization + refine chain) | https://console.groq.com |

---

## 📋 Requirements

```
streamlit>=1.28.0
PyMuPDF>=1.24.0
pytesseract>=0.3.10
Pillow>=10.0.0
sentence-transformers>=2.2.0
scikit-learn>=1.3.0
numpy>=1.24.0
tiktoken>=0.5.0
requests>=2.31.0
python-dotenv>=1.0.0
```

System packages (Streamlit Cloud / Linux): `tesseract-ocr`, `tesseract-ocr-eng`, `poppler-utils`, `libsm6`, `libxext6`, `libxrender-dev`, `libgomp1`

---

## ⚠️ Limitations

- Scanned/image-only PDFs rely on Tesseract OCR accuracy, which can degrade on poor-quality scans
- Book chapter summarization is capped at `MAX_CHAPTERS = 5` to control API cost on very long books
- Document-type detection is heuristic (pattern-based), not ML-based, so atypically formatted documents may be misclassified
- English language documents only
- Subject to Groq API rate limits on free-tier keys

---

## 👨‍💻 Author

**Saarthak Yadav**
BTech Software Engineering
Delhi Technological University

---

## 🙏 Acknowledgements
- [Groq](https://groq.com) for low-latency LLM inference
- [Hugging Face](https://huggingface.co) for the sentence transformer model
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for scanned-document text extraction
