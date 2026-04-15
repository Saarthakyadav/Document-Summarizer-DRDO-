"""
Production-ready prompt templates for document summarization
"""

# ============================================================
# CHUNK-LEVEL PROMPT (First Step) - MORE AGGRESSIVE
# ============================================================
CHUNK_SUMMARY_PROMPT = """Summarize the following text into concise bullet points.

Focus ONLY on:
- Key concepts (3-5 per chunk)
- Important definitions
- Core processes or methods
- Critical insights

STRICT RULES:
- Maximum 8 bullet points per chunk
- Each bullet point max 15 words
- NO examples unless absolutely essential
- NO introductory phrases like "This section discusses"
- Be extremely concise

Text:
{chunk}

Concise Summary:"""


# ============================================================
# REFINE PROMPT - WITH STRICT ANTI-REDUNDANCY
# ============================================================
REFINE_PROMPT = """You are merging new information into an existing summary.

CRITICAL RULES:
1. BEFORE adding any new point, CHECK if a similar point already exists in the summary
2. If it exists, DO NOT add it again (no repetition)
3. If it's new, add it concisely
4. Keep the total length under control

GOAL: Update the summary to include NEW important information WITHOUT repeating existing points.

Existing Summary:
{summary}

New Content:
{chunk}

Updated Summary (NO REPETITION):"""


# ============================================================
# FINAL CLEANUP PROMPT - ENFORCE COMPRESSION
# ============================================================
FINAL_CLEANUP_PROMPT = """You are an expert summarization system.

TASK: Clean up and structure the following summary.

REQUIREMENTS:
- Remove ALL redundancy and repetition
- Combine similar ideas into single bullet points
- Ensure each bullet point is unique
- Target length: REDUCE by 30-40% from input
- Keep only essential information

STRUCTURE:
- Start with a 2-sentence overview
- Use ### headings for major sections
- Use bullet points for key concepts
- End with a 1-sentence conclusion

INPUT SUMMARY:
{content}

CLEAN, NON-REDUNDANT SUMMARY:"""


# ============================================================
# ANTI-REDUNDANCY RULE (Append to any prompt)
# ============================================================
ANTI_REDUNDANCY_RULE = """

⚠️ CRITICAL: Before adding any new point, check if it already exists in the summary. 
If the same idea is already present, DO NOT repeat it. Merge similar points instead."""