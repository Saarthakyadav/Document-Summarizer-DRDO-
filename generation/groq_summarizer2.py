"""
Groq LLM interface — chunk summarization and direct API access.
"""
import os
import re
import time

import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"

MAX_RETRIES = 5
BASE_BACKOFF = 2.0
MIN_CALL_INTERVAL = 1.0

_last_call_time = 0.0


# ---------------------------------------------------------------------------
# Rate-limit throttle
# ---------------------------------------------------------------------------
def _throttle() -> None:
    global _last_call_time
    elapsed = time.time() - _last_call_time
    if elapsed < MIN_CALL_INTERVAL:
        time.sleep(MIN_CALL_INTERVAL - elapsed)
    _last_call_time = time.time()


# ---------------------------------------------------------------------------
# Low-level API caller (shared by all summarizers)
# ---------------------------------------------------------------------------
def _call_groq(prompt: str, max_tokens: int, temperature: float = 0.3) -> str:
    """Call Groq API with exponential back-off on rate-limit / server errors."""
    _throttle()

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert summarizer. Create well-structured, readable "
                    "summaries with paragraphs, headings, and bullet points as appropriate. "
                    "Write in complete sentences."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "top_p": 0.95,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=60)

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()

            if response.status_code == 429:
                wait = BASE_BACKOFF * (2 ** (attempt - 1))
                print(f"  ⏳ Rate-limited, waiting {wait:.1f}s (attempt {attempt})")
                time.sleep(wait)
                continue

            if response.status_code >= 500:
                time.sleep(BASE_BACKOFF * attempt)
                continue

            return f"[Error {response.status_code}]"

        except requests.exceptions.Timeout:
            time.sleep(BASE_BACKOFF * attempt)
        except Exception as exc:
            if attempt == MAX_RETRIES:
                return f"[Error: {exc}]"
            time.sleep(BASE_BACKOFF * attempt)

    return "[Summary unavailable]"


# ---------------------------------------------------------------------------
# Output cleaner (shared)
# ---------------------------------------------------------------------------
def clean_summary_text(text: str) -> str:
    """Normalise whitespace and spacing without altering content."""
    if not text:
        return ""
    text = re.sub(r"\n{4,}", "\n\n", text)
    text = re.sub(r"(###\s+[^\n]+)\n{1,}", r"\1\n\n", text)
    text = re.sub(r"\.([A-Z])", r". \1", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------
def _build_chunk_prompt(text: str) -> str:
    target_chars = len(text) // 2
    return f"""You are an expert summarizer. Create a COMPLETE yet CONCISE summary.

**CRITICAL: Cover ALL major topics from the original text.**

**FORMAT REQUIREMENTS:**
1. Start with a 1-2 sentence overview
2. Use ### headings for each major topic
3. Use bullet points for lists and definitions
4. Keep paragraphs short (2-3 sentences)

**WHAT TO INCLUDE:**
- ALL section headings and subheadings
- ALL key definitions and formulas
- At least ONE example per major concept

**WHAT TO OMIT:**
- Redundant explanations
- All but the best example per concept

**TARGET LENGTH: ~{target_chars} characters**

**TEXT:**
{text}

**COMPLETE SUMMARY:**"""


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------
def summarize_chunk_groq(text: str) -> str:
    """Summarize a single chunk of text; returns a structured summary string."""
    if not text or not text.strip():
        return ""

    if len(text) > 12_000:
        text = text[:12_000]

    prompt = _build_chunk_prompt(text)
    result = _call_groq(prompt, max_tokens=800, temperature=0.3)
    return clean_summary_text(result)
