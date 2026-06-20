import os
import json
from ingestion.ocr_ingestion import extract_text_from_ocr
from ingestion.text_ingestion import load_text
from preprocessing.text_cleaner import clean_text
from chunking.text_chunker import hybrid_chunk_text
from generation.groq_summarizer2 import summarize_chunk_groq


def save_text(text: str, filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)


def save_chunks(chunks, filename):
    with open(filename, "w", encoding="utf-8") as f:
        for i, c in enumerate(chunks):
            f.write(f"\n\n{'='*100}\n")
            f.write(f"CHUNK {i}\n")
            f.write(f"TOKENS: {c.get('token_count', 0)}\n")
            f.write(f"{'='*100}\n\n")
            f.write(c["text"])


def save_summaries(summaries, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=4)


def run_chunk_debug(file_path, output_dir="debug_output"):
    os.makedirs(output_dir, exist_ok=True)
    
    print("📥 Loading document...")
    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_ocr(file_path)
    else:
        text = load_text(file_path)
    
    save_text(text, os.path.join(output_dir, "01_raw_text.txt"))
    print(f"📄 Raw length: {len(text)} chars")
    
    text = clean_text(text)
    save_text(text, os.path.join(output_dir, "02_cleaned_text.txt"))
    print(f"📄 Cleaned length: {len(text)} chars")
    
    print("\n🧠 Running Semantic Chunker...")
    chunks = hybrid_chunk_text(text, max_tokens=600, overlap_sentences=1)
    save_chunks(chunks, os.path.join(output_dir, "03_chunks.txt"))
    print(f"✅ {len(chunks)} chunks created")
    
    print("\n📝 Generating summaries...")
    summaries = []
    for i, chunk in enumerate(chunks):
        print(f"  Summarizing chunk {i+1}/{len(chunks)}...")
        summary = summarize_chunk_groq(chunk["text"], mode="Short Summary")
        summaries.append(summary)
    
    save_summaries(summaries, os.path.join(output_dir, "04_chunk_summaries.json"))
    
    print("\n📄 Creating final summary...")
    final_summary = "\n\n".join(summaries)
    save_text(final_summary, os.path.join(output_dir, "05_final_summary.txt"))
    
    print(f"\n✅ Debug output saved to {output_dir}/")
    print("Files created:")
    for f in os.listdir(output_dir):
        print(f"  - {f}")


if __name__ == "__main__":
    file_path = input("Enter file path: ").strip()
    if not os.path.exists(file_path):
        print("❌ File not found")
    else:
        run_chunk_debug(file_path)