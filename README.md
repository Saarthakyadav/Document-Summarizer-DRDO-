# 📄 Intelligent Document Summarizer

An adaptive, RAG-based document summarization system that automatically detects document type (**Book**, **Research Paper**, or **General**) and generates high-quality, well-structured summaries with comprehensive quality metrics.

---

## 🎯 What It Does

- Upload any PDF document (technical papers, books, reports, business docs)
- Get a well-structured, readable summary with proper headings and bullet points
- Automatic document type detection (Book / Paper / General) with adaptive summarization
- Real-time processing logs and progress tracking
- Comprehensive quality metrics (Cosine Similarity, Compression Ratio, Coverage, Redundancy)
- Zero redundancy with anti-duplication refinement chain

---

## 🖥️ Deployed Link

https://intelligentdocumentsummarizer.streamlit.app/

---

## 🏗️ Architecture

```
PDF Upload
    │
    ▼
OCR Ingestion (PyMuPDF + Tesseract)
    │
    ▼
Text Cleaning & Preprocessing
    │
    ▼
Semantic Chunking (Boundary Detection)
    │
    ▼
Document Type Detection
    ├── Book     → Chapter-wise summarization
    ├── Paper    → Abstract + Sections + Conclusion
    └── General  → Refine-based summarization
    │
    ▼
LLM Summarization (Groq Llama 3.1 8B)
    │
    ▼
Anti-Redundancy Refine Chain
    │
    ▼
Final Cleanup & Structuring
    │
    ▼
Quality Metrics Calculation
    │
    ▼
Summary Output + Metrics Dashboard
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| PDF Processing | PyMuPDF (`fitz`) + Tesseract OCR |
| Chunking | Semantic boundary detection |
| Embeddings | `all-MiniLM-L6-v2` (SentenceTransformers) |
| LLM | Llama 3.1 8B Instruct via Groq API |
| Web Interface | Streamlit |
| Metrics | Cosine Similarity, Flesch Readability |
| Language | Python 3.10+ |

---

## 📁 Project Structure

```
document_summarizer/
├── app.py                        # Streamlit web application
├── main.py                       # Pipeline orchestration
├── preprocessing/
│   └── text_cleaner.py           # OCR cleaning & normalization
├── chunking/
│   └── text_chunker.py           # Semantic chunking with boundary detection
├── generation/
│   ├── groq_summarizer2.py       # LLM summarization
│   └── prompts.py                # Production prompt templates
├── ingestion/
│   ├── ocr_ingestion.py          # PDF/OCR text extraction
│   └── text_ingestion.py         # TXT file loading
├── evaluation/
│   └── summary_metrics.py        # Quality metrics calculation
├── summarization/
│   ├── adaptive_summarizer.py    # Document type routing
│   ├── general_summarizer.py     # Refine-based summarization
│   ├── refine_summarizer.py      # Anti-redundancy refinement
│   ├── paper_summarizer.py       # Research paper strategy
│   └── book_summarizer.py        # Book chapter strategy
├── utils/
│   └── document_detector.py      # Document type detection
├── requirements.txt
└── .gitignore
```

---

## ⚡ Getting Started

### Prerequisites

- Python 3.8 or higher
- Tesseract OCR installed on your system

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/Saarthakyadav/Document-Summarizer-DRDO-.git
cd Document-Summarizer-DRDO-
```

**2. Create a virtual environment**

```bash
# Create environment
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — Mac/Linux
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Install Tesseract OCR**

| OS | Command |
|----|---------|
| Windows | Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) |
| macOS | `brew install tesseract` |
| Linux | `sudo apt-get install tesseract-ocr` |

**5. Set up API Keys**

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

> Get your free API key at [console.groq.com](https://console.groq.com)

**6. Run the app**

```bash
streamlit run app.py
```

---

## 📖 How to Use

1. Open the Streamlit app in your browser
2. Upload a PDF file using the file uploader
3. Select **quality** and **chunk overlap** settings in the sidebar
4. Click **"Generate Summary"**
5. View the well-structured summary with real-time progress
6. Review quality metrics (Cosine Similarity, Compression, Coverage, Redundancy)

---

## 🔧 Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| Quality | Balanced | Fast / Balanced / High Quality |
| Chunk Overlap | 2 sentences | Overlap between chunks |
| Max Tokens | 800 | Maximum output tokens |
| Temperature | 0.3 | LLM creativity (lower = more accurate) |

---

## 📊 Evaluation Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Cosine Similarity | Semantic similarity with original document | > 0.75 |
| Compression Ratio | Original length / Summary length | 2–5× |
| Coverage | Percentage of key concepts preserved | > 0.60 |
| Redundancy | Amount of duplicate content | < 0.10 |
| Readability | Flesch Reading Ease score | 30–50 |

---

## 📈 Performance Results

| Document Type | Cosine Similarity | Compression Ratio | Redundancy |
|---------------|:-----------------:|:-----------------:|:----------:|
| Research Paper (BERT) | 0.866 | 3.1× | 0.005 |
| Business Document (Five Forces) | 0.778 | 1.5× | 0.000 |
| Management Principles | 0.789 | 2.7× | 0.000 |
| NLP Textbook Chapter | 0.719 | 1.6× | 0.064 |

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| Document Type Detection | Automatically identifies Books, Papers, and General documents |
| Adaptive Summarization | Uses optimal strategy for each document type |
| Anti-Redundancy | Refine chain prevents repetition |
| Quality Metrics | Cosine Similarity, Compression, Coverage, Redundancy, Readability |
| Real-time Logs | Processing progress displayed in terminal |
| Multiple Formats | Supports PDF and TXT files |

---

## 🔑 API Keys

| Service | Purpose | Link |
|---------|---------|------|
| Groq | LLM inference for summarization | [console.groq.com](https://console.groq.com) |

---

## 📋 Requirements

```text
streamlit>=1.28.0
PyMuPDF>=1.23.0
pytesseract>=0.3.10
Pillow>=10.0.0
opencv-python>=4.8.0
sentence-transformers>=2.2.0
scikit-learn>=1.3.0
numpy>=1.24.0
tiktoken>=0.5.0
requests>=2.31.0
python-dotenv>=1.0.0
textstat>=0.7.0
opencv-python-headless>=4.8.0
```

---

## ⚠️ Limitations

- Scanned PDFs (images of text) require OCR which may have accuracy issues
- Technical documents with complex formatting may have lower coverage scores
- Processing time depends on document length and quality settings
- English language documents only

---

## 🔮 Future Scope

- Image and table extraction and description
- Multi-document comparison summarization
- Custom fine-tuning for domain-specific documents
- ROUGE score integration for academic benchmarking
- Parallel processing for faster summarization

---

## 👨‍💻 Author

**Saarthak Yadav**   
B.Tech Software Engineering — 3rd Year DTU DRDO Internship 2025
GitHub: [@Saarthakyadav](https://github.com/Saarthakyadav) 
---

## 📄 License

This project was developed as part of a DRDO internship. All rights reserved.

---

## 🙏 Acknowledgements
- [DRDO](https://www.drdo.gov.in/drdo/) - for the internship opportunity
- [Groq](https://groq.com) — for low-latency LLM inference
- [Sentence Transformers](https://www.sbert.net) — for embedding models
- [Streamlit](https://streamlit.io) — for the web framework
- [PyMuPDF](https://pymupdf.readthedocs.io) — for PDF processing
- [Tesseract](https://github.com/tesseract-ocr/tesseract) — for OCR capabilities

---

## 📚 Citation

If you use this project in your research, please cite:

```bibtex
@software{document_summarizer_2025,
  author = {Yadav, Saarthak},
  title  = {Intelligent Document Summarizer},
  year   = {2025},
  url    = {https://github.com/Saarthakyadav/Document-Summarizer-DRDO-}
}
```

---

⭐ **Star this repository if you found it useful!**
