"""
Streamlit front-end for the Adaptive Multi-Strategy Document Summarizer.
"""
import os
import tempfile

import streamlit as st

from main import run_pipeline_stream

st.set_page_config(page_title="Document Summarizer", layout="wide")

st.title("📄 Adaptive Document Summarizer")
st.caption(
    "Upload a PDF or TXT — auto-detects book, research paper, or general document "
    "and applies the matching summarization strategy."
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.header("⚙️ Settings")
quality = st.sidebar.select_slider(
    "Quality vs Speed",
    options=["Fast", "Balanced", "High Quality"],
    value="Balanced",
)
chunk_overlap = st.sidebar.slider("Chunk Overlap (sentences)", 0, 5, 2)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "summary_text" not in st.session_state:
    st.session_state.summary_text = ""
if "chunks_display" not in st.session_state:
    st.session_state.chunks_display = []

# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
uploaded_file = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])

if uploaded_file:
    file_bytes = uploaded_file.read()
    st.success(f"✅ {uploaded_file.name}  ({len(file_bytes)/1024:.1f} KB)")

    if st.button("🚀 Generate Summary", type="primary"):
        suffix = f".{uploaded_file.name.rsplit('.', 1)[-1]}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_bytes)
            file_path = tmp.name

        st.subheader("📌 Processing…")

        pipeline_stats = st.empty()       # ingestion / detection / chunking panel
        progress_placeholder = st.empty()
        status_text = st.empty()
        summary_placeholder = st.empty()
        metrics_placeholder = st.empty()

        st.session_state.summary_text = ""
        st.session_state.chunks_display = []

        progress_bar = progress_placeholder.progress(0)

        final_summary = ""
        metrics_data: dict = {}
        timing_data: dict = {}
        total_chunks = 0

        try:
            for item in run_pipeline_stream(
                file_path, quality=quality, chunk_overlap=chunk_overlap
            ):
                event_type = item.get("type")

                if event_type == "doc_detected":
                    doc_label = item["doc_type"].title()
                    pct = int(item["confidence"] * 100)
                    # Show partial stats — chunking not done yet
                    pipeline_stats.info(
                        f"🔍 Detected: **{doc_label}** ({pct}% confidence) "
                        f"| {item['words']:,} words"
                    )

                elif event_type == "summary_start":
                    total_chunks = item["total_chunks"]
                    progress_bar.progress(0)
                    status_text.text(item["message"])

                    # Now we have all three stats — show the full panel
                    pipeline_stats.info(
                        f"📥 Ingestion: **{item['ingestion_time']}s** "
                        f"| {item['words']:,} words  \n"
                        f"🔍 Detected: **{item['doc_type'].upper()}** "
                        f"({int(item['confidence']*100)}% confidence)  \n"
                        f"🧩 Chunking: **{item['chunking_time']}s** "
                        f"| {total_chunks} valid chunk{'s' if total_chunks != 1 else ''}"
                    )

                elif event_type == "chunk_summary":
                    progress = item["chunk_index"] / max(item["total_chunks"], 1)
                    progress_bar.progress(progress)
                    status_text.text(
                        f"Summarizing section {item['chunk_index']}/{item['total_chunks']}…"
                    )
                    st.session_state.chunks_display.append(
                        {"index": item["chunk_index"], "summary": item["summary"]}
                    )
                    accumulated = "\n\n".join(
                        c["summary"] for c in st.session_state.chunks_display
                    )
                    summary_placeholder.markdown(
                        f"### 📄 Summary (building…)\n\n{accumulated}"
                    )
                    final_summary = accumulated

                elif event_type == "chunk_error":
                    status_text.text(
                        f"Section {item['chunk_index']} failed, continuing…"
                    )

                elif event_type == "final":
                    final_summary = item["summary"]
                    metrics_data = item.get("metrics", {})
                    timing_data = item.get("timing", {})
                    compression = item.get("compression", 0)
                    doc_type = item.get("doc_type", "general")
                    confidence = item.get("confidence", 0)

                    summary_placeholder.markdown(
                        f"### 📄 Final Summary\n\n{final_summary}"
                    )

                    with metrics_placeholder.container():
                        st.markdown("### 📊 Evaluation Metrics")
                        st.caption(
                            f"Strategy: **{doc_type.title()}** "
                            f"({int(confidence*100)}% confidence)"
                        )

                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Cosine Similarity",
                                      f"{metrics_data.get('Cosine Similarity', 0):.3f}")
                            st.metric("Compression", f"{compression:.1f}x")
                        with col2:
                            st.metric("Readability (Flesch)",
                                      f"{metrics_data.get('Readability (Flesch)', 0):.1f}")
                            st.metric("Coverage",
                                      f"{metrics_data.get('Coverage', 0):.3f}")
                        with col3:
                            st.metric("Overall Score",
                                      f"{metrics_data.get('Overall Score', 0):.3f}")
                            st.metric("Sections",
                                      f"{item.get('chunks_summarized', 0)}"
                                      f"/{item.get('total_chunks', 0)}")
                        with col4:
                            st.metric("Redundancy",
                                      f"{metrics_data.get('Redundancy', 0):.3f}")
                            st.metric("Total Time", f"{timing_data.get('total', 0)}s")

                    progress_bar.progress(1.0)
                    status_text.text("✅ Complete!")
                    st.session_state.summary_text = final_summary

                elif event_type == "error":
                    st.error(f"❌ {item['message']}")
                    break

        except Exception as exc:
            st.error(f"❌ Processing failed: {exc}")

        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------
if st.session_state.summary_text:
    st.divider()
    st.download_button(
        label="📥 Download Summary",
        data=st.session_state.summary_text,
        file_name="summary.txt",
        mime="text/plain",
    )