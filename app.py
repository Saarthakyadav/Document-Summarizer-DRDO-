import os
import tempfile
import streamlit as st

from main import run_pipeline_stream

st.set_page_config(page_title="Document Summarizer", layout="wide")

st.title("📄 Document Summarizer")
st.caption("Upload any PDF and get a well-structured, readable summary.")

st.sidebar.header("⚙️ Settings")

quality = st.sidebar.select_slider(
    "Quality vs Speed", 
    options=["Fast", "Balanced", "High Quality"],
    value="Balanced"
)
chunk_overlap = st.sidebar.slider("Chunk Overlap (sentences)", 0, 5, 2)

if "summary_text" not in st.session_state:
    st.session_state.summary_text = ""
if "chunks_display" not in st.session_state:
    st.session_state.chunks_display = []

uploaded_file = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])

if uploaded_file:
    file_bytes = uploaded_file.read()
    st.success(f"✅ File uploaded: {uploaded_file.name}")
    st.write(f"📄 File size: {len(file_bytes)/1024:.2f} KB")

    if st.button("🚀 Generate Summary", type="primary"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
            tmp.write(file_bytes)
            file_path = tmp.name

        st.subheader("📌 Processing...")
        
        # Create placeholders
        summary_placeholder = st.empty()
        progress_placeholder = st.empty()
        metrics_placeholder = st.empty()
        
        # Reset session state
        st.session_state.summary_text = ""
        st.session_state.chunks_display = []
        
        progress_bar = progress_placeholder.progress(0)
        status_text = progress_placeholder.empty()
        
        final_summary = ""
        metrics_data = {}
        timing_data = {}
        total_chunks = 0
        
        try:
            for item in run_pipeline_stream(
                file_path, 
                quality=quality, 
                chunk_overlap=chunk_overlap
            ):
                if item["type"] == "summary_start":
                    total_chunks = item["total_chunks"]
                    status_text.text(f"Processing {total_chunks} sections...")
                    progress_bar.progress(0)
                
                elif item["type"] == "chunk_summary":
                    # Update progress
                    progress = item["chunk_index"] / item["total_chunks"]
                    progress_bar.progress(progress)
                    status_text.text(f"Processing section {item['chunk_index']}/{item['total_chunks']}...")
                    
                    # Store chunk summary
                    st.session_state.chunks_display.append({
                        "index": item["chunk_index"],
                        "summary": item["summary"]
                    })
                    
                    # Build and display accumulated summary
                    accumulated = "\n\n".join([c["summary"] for c in st.session_state.chunks_display])
                    summary_placeholder.markdown(f"### 📄 Summary (Building...)\n\n{accumulated}")
                    
                    # Also update final summary variable
                    final_summary = accumulated
                
                elif item["type"] == "chunk_error":
                    status_text.text(f"Section {item['chunk_index']} failed, continuing...")
                
                elif item["type"] == "merge_warning":
                    status_text.text(item["message"])
                
                elif item["type"] == "final":
                    # Final summary with metrics
                    final_summary = item["summary"]
                    metrics_data = item.get("metrics", {})
                    timing_data = item.get("timing", {})
                    compression = item.get("compression", 0)
                    
                    # Display final summary
                    summary_placeholder.markdown(f"### 📄 Final Summary\n\n{final_summary}")
                    
                    # Display metrics
                    with metrics_placeholder.container():
                        st.markdown("### 📊 Evaluation Metrics")
                        col1, col2, col3 , col4 = st.columns(4)
                        with col1:
                            st.metric("Cosine Similarity", f"{metrics_data.get('Cosine Similarity', 0):.3f}")
                            st.metric("Compression Ratio", f"{compression:.1f}x")
                        with col2:
                            st.metric("Readability (Flesch)", f"{metrics_data.get('Readability (Flesch)', 0):.1f}")
                            st.metric("Coverage", f"{metrics_data.get('Coverage', 0):.3f}")
                        with col3:
                            st.metric("Overall Score", f"{metrics_data.get('Overall Score', 0):.3f}")
                            st.metric("Sections", f"{item.get('chunks_summarized', 0)}/{item.get('total_chunks', 0)}")
                        with col4:  # NEW COLUMN for Redundancy
                            st.metric("Redundancy", f"{metrics_data.get('Redundancy', 0):.3f}")
                            st.metric("Sections", f"{item.get('total_chunks', 0)}")

                    
                    progress_bar.progress(1.0)
                    status_text.text("Complete!")
                
                elif item["type"] == "error":
                    st.error(f"❌ {item['message']}")
                    break

        except Exception as e:
            st.error(f"❌ Processing failed: {str(e)}")

        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

if st.session_state.summary_text:
    st.divider()
    st.download_button(
        label="📥 Download Summary",
        data=st.session_state.summary_text,
        file_name="summary.txt",
        mime="text/plain"
    )