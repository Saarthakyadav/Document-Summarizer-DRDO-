# import os
# import time
# import re
# import requests
# from dotenv import load_dotenv

# load_dotenv()

# # -------------------------
# # CONFIG
# # -------------------------
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# MODEL = "llama-3.1-8b-instant"

# MAX_RETRIES = 5
# BASE_BACKOFF = 2.0
# MIN_CALL_INTERVAL = 1.0

# _last_call_time = 0.0


# # -------------------------
# # RATE LIMIT CONTROL
# # -------------------------
# def _throttle():
#     global _last_call_time
#     now = time.time()
#     elapsed = now - _last_call_time
#     if elapsed < MIN_CALL_INTERVAL:
#         time.sleep(MIN_CALL_INTERVAL - elapsed)
#     _last_call_time = time.time()


# # -------------------------
# # PROMPT BUILDERS
# # -------------------------
# def build_prompt(text: str, mode: str = "Short Summary") -> str:
#     if mode == "Exam-ready Notes":
#         return f"""You are an expert academic summarizer creating EXAM-READY NOTES.

# TASK: Create structured, concise exam notes from the text below.

# RULES:
# - Use bullet points with clear hierarchy
# - Keep ALL key definitions and examples
# - Group related concepts together
# - Remove repetition and fluff
# - Target length: 30-40% of original

# TEXT:
# {text}""".strip()
    
#     else:
#         return f"""You are an expert summarizer creating a CONCISE SUMMARY.

# TASK: Summarize the following text clearly and completely.

# RULES:
# - Use bullet points
# - Keep key concepts and definitions
# - Remove redundancy
# - Be extremely concise
# - Target length: 30-40% of original

# TEXT:
# {text}""".strip()


# def build_compress_prompt(text: str) -> str:
#     return f"""Compress this summary to be MORE CONCISE.

# RULES:
# - Keep ALL key information
# - Remove redundant phrases
# - Merge similar points
# - Target length: 50% of current

# SUMMARY:
# {text}

# COMPRESSED SUMMARY:""".strip()


# # -------------------------
# # GROQ API CALLER
# # -------------------------
# def _call_groq(prompt: str, max_tokens: int, temperature: float = 0.3) -> str:
#     _throttle()

#     payload = {
#         "model": MODEL,
#         "messages": [
#             {"role": "system", "content": "You generate structured, complete, and accurate summaries. Use bullet points. Be concise."},
#             {"role": "user", "content": prompt}
#         ],
#         "temperature": temperature,
#         "top_p": 0.95,
#         "max_tokens": max_tokens
#     }

#     headers = {
#         "Authorization": f"Bearer {GROQ_API_KEY}",
#         "Content-Type": "application/json"
#     }

#     for attempt in range(1, MAX_RETRIES + 1):
#         try:
#             response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=60)

#             if response.status_code == 200:
#                 data = response.json()
#                 return data["choices"][0]["message"]["content"].strip()

#             if response.status_code == 429:
#                 time.sleep(BASE_BACKOFF * (2 ** (attempt - 1)))
#                 continue

#             if response.status_code >= 500:
#                 time.sleep(BASE_BACKOFF * attempt)
#                 continue

#             return f"[Error {response.status_code}]"

#         except requests.exceptions.Timeout:
#             time.sleep(BASE_BACKOFF * attempt)
#         except Exception as e:
#             if attempt == MAX_RETRIES:
#                 return f"[Error: {str(e)}]"
#             time.sleep(BASE_BACKOFF * attempt)

#     return "[Summary unavailable]"


# # -------------------------
# # CLEAN SUMMARY OUTPUT
# # -------------------------
# def clean_summary_text(text: str) -> str:
#     if not text:
#         return ""
    
#     lines = text.split("\n")
#     cleaned = []

#     for line in lines:
#         line = line.strip()
#         if not line:
#             continue
        
#         # Skip lines that are mostly symbols
#         alpha_ratio = len(re.findall(r'[a-zA-Z]', line)) / max(len(line), 1)
#         if alpha_ratio < 0.3 and len(line) > 5:
#             continue
        
#         # Skip very short lines that are likely artifacts
#         if len(line) < 10 and line.isdigit():
#             continue
        
#         cleaned.append(line)

#     result = "\n".join(cleaned)
#     result = re.sub(r'\n{3,}', '\n\n', result)
#     result = re.sub(r'\.([A-Z])', r'. \1', result)
    
#     return result.strip()


# # -------------------------
# # MAIN SUMMARIZER
# # -------------------------
# def summarize_chunk_groq(text: str, mode: str = "Short Summary") -> str:
#     if not text or not text.strip():
#         return ""

#     if len(text) > 10000:
#         text = text[:10000]

#     prompt = build_prompt(text, mode)
#     max_tokens = 500 if mode == "Short Summary" else 700
    
#     result = _call_groq(prompt, max_tokens=max_tokens, temperature=0.3)
    
#     return clean_summary_text(result)


# def compress_summary_groq(summary: str) -> str:
#     if not summary or not summary.strip():
#         return summary
    
#     if len(summary.split()) < 50:
#         return summary
    
#     prompt = build_compress_prompt(summary)
#     result = _call_groq(prompt, max_tokens=400, temperature=0.2)
    
#     return clean_summary_text(result) if result else summary


# def final_refine_summary(summary: str, mode: str = "Short Summary") -> str:
#     if not summary or not summary.strip():
#         return summary
    
#     if mode == "Exam-ready Notes":
#         prompt = f"""Refine these exam notes for clarity.

# RULES:
# - Keep ALL key information
# - Ensure bullet points are parallel
# - Remove any remaining redundancy

# NOTES:
# {summary}

# REFINED NOTES:"""
#     else:
#         prompt = f"""Refine this summary to be more concise.

# RULES:
# - Remove redundancy
# - Keep all key information
# - Ensure clarity

# SUMMARY:
# {summary}

# REFINED SUMMARY:"""
    
#     result = _call_groq(prompt, max_tokens=500, temperature=0.2)
    
#     return clean_summary_text(result) if result else summary
import os
import time
import re
import requests
from dotenv import load_dotenv

load_dotenv()

# -------------------------
# CONFIG
# -------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"

MAX_RETRIES = 5
BASE_BACKOFF = 2.0
MIN_CALL_INTERVAL = 1.0

_last_call_time = 0.0


def _throttle():
    global _last_call_time
    now = time.time()
    elapsed = now - _last_call_time
    if elapsed < MIN_CALL_INTERVAL:
        time.sleep(MIN_CALL_INTERVAL - elapsed)
    _last_call_time = time.time()


# def build_prompt(text: str) -> str:
#     """Prompt that preserves ALL key topics"""
    
#     return f"""You are an expert summarizer. Create a COMPLETE, WELL-STRUCTURED summary.

# **CRITICAL: Preserve ALL major topics and subtopics from the original text.**

# **FORMAT REQUIREMENTS:**
# 1. Start with a 2-3 sentence overview
# 2. Use ### headings for each major topic
# 3. For EACH major topic, include:
#    - Key definitions
#    - Important examples
#    - Formulas or metrics (if any)
#    - Sub-topics
# 4. Use bullet points for lists and key takeaways
# 5. End with a brief summary paragraph

# **COMPLETENESS REQUIREMENTS:**
# - DO NOT skip any major section from the original
# - DO NOT summarize too aggressively - keep important details
# - Include numerical examples, formulas, and specific values
# - Preserve ALL key terms and their definitions
# - Aim for 40-50% of original length (not 20-30%)

# **TEXT:**
# {text}

# **COMPLETE SUMMARY:**"""

# def build_prompt(text: str) -> str:
#     """Balanced prompt - complete but concise"""
    
#     return f"""You are an expert summarizer. Create a CONCISE but COMPLETE summary.

# **CRITICAL BALANCE:**
# - Keep ALL key concepts and definitions
# - Keep important examples (1-2 per concept)
# - Keep formulas and metrics
# - BUT be CONCISE - remove redundancy and wordy explanations

# **FORMAT REQUIREMENTS:**
# 1. Start with 1-2 sentence overview
# 2. Use ### headings for major topics
# 3. Use bullet points for lists and definitions
# 4. Keep paragraphs short (2-3 sentences max)
# 5. Aim for 30-40% of original length

# **WHAT TO REMOVE:**
# - Redundant explanations
# - Multiple similar examples (keep only the best one)
# - Wordy transitions
# - Unnecessary adjectives

# **WHAT TO KEEP:**
# - All key definitions
# - Important formulas
# - Critical examples
# - Main sub-topics

# **TARGET LENGTH: {len(text)//3} to {len(text)//2} characters**

# **TEXT:**
# {text}

# **CONCISE SUMMARY:**"""

def build_prompt(text: str) -> str:
    """Prompt that maximizes coverage while maintaining compression"""
    
    # Calculate target length (40-50% of original for better coverage)
    target_chars = len(text) // 2
    
    return f"""You are an expert summarizer. Create a COMPLETE yet CONCISE summary.

**CRITICAL: Cover ALL major topics from the original text.**

**BALANCE GOALS:**
- Coverage: Capture 70-80% of key concepts
- Compression: Reduce to 40-50% of original length
- Accuracy: Preserve definitions, formulas, examples

**FORMAT REQUIREMENTS:**
1. Start with a 1-2 sentence overview
2. Use ### headings for each major topic
3. Use bullet points for lists and definitions
4. Keep paragraphs short (2-3 sentences)

**WHAT TO INCLUDE (DO NOT SKIP):**
- ALL section headings and subheadings
- ALL key definitions
- ALL important formulas and metrics
- At least ONE example per major concept
- ALL numerical values and thresholds

**WHAT CAN BE CONCISE:**
- Remove redundant explanations
- Keep only the best example per concept
- Use bullet points instead of paragraphs when possible

**TARGET LENGTH: Approximately {target_chars} characters**

**TEXT:**
{text}

**COMPLETE SUMMARY:**"""

def _call_groq(prompt: str, max_tokens: int, temperature: float = 0.3) -> str:
    """Call Groq API"""
    _throttle()

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert summarizer. Create well-structured, readable summaries with paragraphs, headings, and bullet points as appropriate. Write in complete sentences."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "top_p": 0.95,
        "max_tokens": max_tokens
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=60)

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()

            if response.status_code == 429:
                time.sleep(BASE_BACKOFF * (2 ** (attempt - 1)))
                continue

            if response.status_code >= 500:
                time.sleep(BASE_BACKOFF * attempt)
                continue

            return f"[Error {response.status_code}]"

        except requests.exceptions.Timeout:
            time.sleep(BASE_BACKOFF * attempt)
        except Exception as e:
            if attempt == MAX_RETRIES:
                return f"[Error: {str(e)}]"
            time.sleep(BASE_BACKOFF * attempt)

    return "[Summary unavailable]"


def clean_summary_text(text: str) -> str:
    """Clean output while preserving content structure"""
    if not text:
        return ""
    
    # Remove excessive newlines (but preserve paragraph breaks)
    text = re.sub(r'\n{4,}', '\n\n', text)
    
    # Ensure proper spacing after headings
    text = re.sub(r'(###\s+[^\n]+)\n{1,}', r'\1\n\n', text)
    
    # Fix missing spaces after periods
    text = re.sub(r'\.([A-Z])', r'. \1', text)
    
    return text.strip()


# Add this function to existing groq_summarizer2.py

def summarize_with_refine_pipeline(text: str) -> str:
    """
    Complete refine-based summarization for any text
    """
    from chunking.text_chunker import hybrid_chunk_text
    from summarization.refine_summarizer import summarize_with_refine
    
    # Chunk the text
    chunks = hybrid_chunk_text(text, max_tokens=1000, overlap_sentences=2)
    chunk_texts = [c["text"] for c in chunks if c.get("text", "").strip()]
    
    if not chunk_texts:
        chunk_texts = [text[:8000]]
    
    # Use refine-based summarization
    return summarize_with_refine(chunk_texts)

def summarize_chunk_groq(text: str) -> str:
    """
    Summarize a chunk - produces a well-structured, readable summary
    
    Args:
        text: Input text to summarize
    
    Returns:
        Well-structured summary with paragraphs, headings, and bullet points
    """
    if not text or not text.strip():
        return ""

    if len(text) > 12000:
        text = text[:12000]

    prompt = build_prompt(text)
    max_tokens = 800
    temperature = 0.3
    
    result = _call_groq(prompt, max_tokens=max_tokens, temperature=temperature)
    
    return clean_summary_text(result)