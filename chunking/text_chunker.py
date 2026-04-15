import re
import numpy as np
from typing import List, Dict

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

try:
    import tiktoken
    tokenizer = tiktoken.get_encoding("cl100k_base")
except:
    tokenizer = None


def count_tokens(text: str) -> int:
    if tokenizer:
        return len(tokenizer.encode(text))
    return len(text.split())


_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def clean_text(text: str) -> str:
    text = re.sub(r"[^\w\s.,;:()\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_paragraphs(text: str) -> List[str]:
    text = re.sub(r'\n{3,}', '\n\n', text)
    paragraphs = re.split(r'\n\s*\n+', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    if len(paragraphs) >= 3:
        return paragraphs
    
    section_pattern = r'(?=\n\d+\.\d+\s+[A-Z])'
    sections = re.split(section_pattern, text)
    sections = [s.strip() for s in sections if s.strip()]
    
    if len(sections) >= 2:
        return sections
    
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sentences if s.strip()]


def split_sentences(text: str) -> List[str]:
    abbreviations = r'\b(?:Mr|Mrs|Ms|Dr|Prof|Rev|Hon|St|Ave|Blvd|Rd|Fig|e\.g|i\.e|vs|etc|al)\.'
    text = re.sub(abbreviations, lambda m: m.group(0).replace('.', '___DOT___'), text)
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    sentences = [s.replace('___DOT___', '.') for s in sentences]
    return [s.strip() for s in sentences if s.strip()]


def semantic_group(sentences: List[str]) -> List[List[str]]:
    if not sentences:
        return []
    if len(sentences) == 1:
        return [sentences]
    if len(sentences) <= 3:
        return [sentences]

    model = get_model()
    embeddings = model.encode(sentences, show_progress_bar=False)

    sims = [
        cosine_similarity([embeddings[i - 1]], [embeddings[i]])[0][0]
        for i in range(1, len(embeddings))
    ]
    
    if len(sims) == 0 or np.std(sims) == 0:
        threshold = 0.4
    else:
        threshold = max(0.35, np.mean(sims) - 0.15 * np.std(sims))

    groups = []
    current_group = [sentences[0]]
    current_embeds = [embeddings[0]]

    for i in range(1, len(sentences)):
        centroid = np.mean(current_embeds, axis=0)
        sim = cosine_similarity([centroid], [embeddings[i]])[0][0]

        if sim < threshold:
            if len(current_group) >= 2:
                groups.append(current_group)
                current_group = [sentences[i]]
                current_embeds = [embeddings[i]]
            else:
                current_group.append(sentences[i])
                current_embeds.append(embeddings[i])
        else:
            current_group.append(sentences[i])
            current_embeds.append(embeddings[i])

    if current_group:
        groups.append(current_group)

    return groups


def build_chunks(groups: List[List[str]], max_tokens: int = 800, overlap_sentences: int = 2) -> List[Dict]:
    chunks = []
    current_chunk = []
    current_tokens = 0
    chunk_id = 0

    def finalize(chunk_sentences, is_last=False):
        text = " ".join(chunk_sentences).strip()
        if not is_last and text and text[-1] not in '.!?':
            text += '.'
        return {
            "chunk_id": None,
            "text": text,
            "token_count": count_tokens(text)
        }

    for group_idx, group in enumerate(groups):
        group_tokens = count_tokens(" ".join(group))

        if group_tokens > max_tokens:
            sentences = group
            temp_chunk = []
            temp_tokens = 0
            
            for sent in sentences:
                sent_tokens = count_tokens(sent)
                if temp_tokens + sent_tokens > max_tokens and temp_chunk:
                    chunk = finalize(temp_chunk)
                    chunk["chunk_id"] = chunk_id
                    chunks.append(chunk)
                    chunk_id += 1
                    overlap = temp_chunk[-overlap_sentences:] if overlap_sentences > 0 else []
                    temp_chunk = overlap
                    temp_tokens = sum(count_tokens(s) for s in temp_chunk)
                
                temp_chunk.append(sent)
                temp_tokens += sent_tokens
            
            if temp_chunk:
                chunk = finalize(temp_chunk, is_last=(group_idx == len(groups)-1))
                chunk["chunk_id"] = chunk_id
                chunks.append(chunk)
                chunk_id += 1
        
        elif current_tokens + group_tokens > max_tokens:
            if current_chunk:
                chunk = finalize(current_chunk)
                chunk["chunk_id"] = chunk_id
                chunks.append(chunk)
                chunk_id += 1

            overlap = current_chunk[-overlap_sentences:] if current_chunk and overlap_sentences > 0 else []
            current_chunk = overlap + group
            current_tokens = sum(count_tokens(s) for s in current_chunk)
        else:
            current_chunk.extend(group)
            current_tokens += group_tokens

    if current_chunk:
        chunk = finalize(current_chunk, is_last=True)
        chunk["chunk_id"] = chunk_id
        chunks.append(chunk)

    return chunks


def merge_small_chunks(chunks: List[Dict], min_tokens: int = 200) -> List[Dict]:
    if not chunks or len(chunks) <= 1:
        return chunks
    
    chunks = [chunk.copy() for chunk in chunks]
    
    i = 0
    while i < len(chunks):
        if chunks[i]["token_count"] < min_tokens:
            if i > 0:
                chunks[i-1]["text"] += " " + chunks[i]["text"]
                chunks[i-1]["token_count"] = count_tokens(chunks[i-1]["text"])
                chunks.pop(i)
                continue
            elif i < len(chunks) - 1:
                chunks[i+1]["text"] = chunks[i]["text"] + " " + chunks[i+1]["text"]
                chunks[i+1]["token_count"] = count_tokens(chunks[i+1]["text"])
                chunks.pop(i)
                continue
        i += 1
    
    for i, chunk in enumerate(chunks):
        chunk["chunk_id"] = i
    
    return chunks


def hybrid_chunk_text(text: str, max_tokens: int = 800, overlap_sentences: int = 2) -> List[Dict]:
    text = clean_text(text)
    if not text:
        return []

    paragraphs = split_paragraphs(text)
    all_chunks = []

    for para in paragraphs:
        if len(para.split()) < 5:
            continue
            
        sentences = split_sentences(para)
        if not sentences:
            continue

        groups = semantic_group(sentences)
        chunks = build_chunks(groups, max_tokens=max_tokens, overlap_sentences=overlap_sentences)
        all_chunks.extend(chunks)

    all_chunks = merge_small_chunks(all_chunks, min_tokens=150)

    for i, c in enumerate(all_chunks):
        c["chunk_id"] = i

    return all_chunks