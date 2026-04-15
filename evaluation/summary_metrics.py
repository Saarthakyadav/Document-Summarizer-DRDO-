# import re
# import numpy as np
# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity

# _model = None

# def get_model():
#     global _model
#     if _model is None:
#         _model = SentenceTransformer("all-MiniLM-L6-v2")
#     return _model


# def count_syllables_simple(word: str) -> int:
#     """Simple syllable counter for readability scores"""
#     word = word.lower().strip()
#     if not word or not word[0].isalpha():
#         return 1
#     word = re.sub(r'[^\w]', '', word)
#     if not word:
#         return 1
#     if len(word) <= 3:
#         return 1
#     vowel_count = len(re.findall(r'[aeiouy]+', word))
#     if word.endswith('e') and vowel_count > 1:
#         vowel_count -= 1
#     return max(vowel_count, 1)


# def normalize_for_flesch(text: str) -> str:
#     """
#     FIX: Normalize bullet-point summaries into proper sentences
#     Converts "- item one\n- item two" into "item one. item two."
#     """
#     if not text:
#         return text
    
#     lines = text.splitlines()
#     normalized = []
    
#     for line in lines:
#         line = line.strip()
#         # Remove bullet points, dashes, asterisks, numbers
#         line = re.sub(r'^[\s•*\-*\d+\.\s]+', '', line)
#         line = line.strip()
        
#         if not line:
#             continue
        
#         # Add period if line doesn't end with punctuation
#         if not line.endswith(('.', '!', '?')):
#             line += '.'
        
#         normalized.append(line)
    
#     return ' '.join(normalized)


# def flesch_reading_ease(text: str) -> float:
#     """
#     FIXED: Calculate Flesch Reading Ease score
#     Now properly handles bullet-point summaries
#     """
#     if not text or len(text.strip()) < 50:
#         return 50.0
    
#     # Normalize bullet points into proper sentences
#     text = normalize_for_flesch(text)
    
#     # Split into sentences
#     sentences = re.split(r'[.!?]+', text)
#     sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    
#     if not sentences:
#         return 50.0
    
#     num_sentences = len(sentences)
#     words = re.findall(r'\b[a-zA-Z]+(?:-[a-zA-Z]+)?\b', text)
#     num_words = len(words)
    
#     if num_words < 10:
#         return 50.0
    
#     num_syllables = sum(count_syllables_simple(word) for word in words)
#     flesch = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (num_syllables / max(num_words, 1))
    
#     return max(0.0, min(100.0, flesch))


# def calculate_coverage(original: str, summary: str) -> float:
#     """
#     FIXED: Accurate coverage calculation for technical documents
#     - Now captures short technical terms (≥2 chars instead of ≥4)
#     - Uses higher boost for paraphrased content
#     """
#     if not original or not summary:
#         return 0.0
    
#     # Convert to lowercase
#     orig_lower = original.lower()
#     sum_lower = summary.lower()
    
#     # Common words to ignore (expanded)
#     common_words = {
#         'the', 'a', 'an', 'and', 'of', 'to', 'in', 'for', 'on', 'with', 
#         'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
#         'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'but', 'or',
#         'so', 'for', 'nor', 'yet', 'at', 'by', 'from', 'into', 'through',
#         'during', 'including', 'without', 'within', 'this', 'that', 'these',
#         'those', 'there', 'their', 'they', 'will', 'would', 'could', 'should',
#         'may', 'might', 'must', 'can', 'cannot', 'not', 'no', 'yes', 'also',
#         'very', 'just', 'such', 'each', 'both', 'only', 'over', 'under',
#         'then', 'than', 'when', 'where', 'which', 'while', 'because', 'using',
#         'like', 'enable', 'perform', 'process', 'provide', 'use', 'based',
#         'study', 'research', 'paper', 'article', 'find', 'found', 'show',
#         'demonstrate', 'indicate', 'suggest', 'propose', 'discuss', 'analyze',
#         'data', 'result', 'conclusion', 'example', 'level', 'occur', 'within'
#     }
    
#     # FIX: Extract words with ≥2 characters (captures "AI", "ML", etc.)
#     def extract_words(text):
#         words = set()
#         for word in text.split():
#             word_clean = re.sub(r'[^\w]', '', word)
#             if len(word_clean) >= 2 and word_clean not in common_words:
#                 words.add(word_clean)
#         return words
    
#     orig_words = extract_words(orig_lower)
#     sum_words = extract_words(sum_lower)
    
#     if not orig_words:
#         return 0.5
    
#     # Calculate overlap
#     overlap = len(orig_words.intersection(sum_words))
    
#     # FIX: Higher boost (2.0x) for good paraphrased summaries
#     coverage = min(1.0, (overlap / len(orig_words)) * 2.0)
    
#     return round(coverage, 4)


# def calculate_redundancy(summary: str) -> float:
#     """Estimate redundancy in the summary"""
#     if not summary or len(summary.split()) < 50:
#         return 0.0
    
#     # Normalize bullets first
#     summary_norm = normalize_for_flesch(summary)
#     sentences = re.split(r'[.!?]+', summary_norm)
#     sentences = [s.strip().lower() for s in sentences if len(s.strip()) > 15]
    
#     if len(sentences) < 2:
#         return 0.0
    
#     seen = set()
#     duplicate_count = 0
#     for s in sentences:
#         if s in seen:
#             duplicate_count += 1
#         else:
#             seen.add(s)
    
#     return round(duplicate_count / len(sentences), 4)


# def calculate_density(summary: str) -> float:
#     """Calculate information density"""
#     if not summary:
#         return 0.0
    
#     key_terms = re.findall(r'\b[a-zA-Z]{3,}\b', summary.lower())
#     unique_terms = len(set(key_terms))
#     total_words = len(summary.split())
    
#     if total_words == 0:
#         return 0.0
    
#     density = min(1.0, unique_terms / total_words * 2.0)
#     return round(density, 4)


# def evaluate_summary(original: str, summary: str) -> dict:
#     """
#     Evaluate summary quality - FULLY FIXED
#     """
#     if not original or not summary:
#         return {
#             "Cosine Similarity": 0.0,
#             "Compression Ratio": 0.0,
#             "Readability (Flesch)": 50.0,
#             "Coverage": 0.0,
#             "Redundancy": 0.0,
#             "Density": 0.0,
#             "Overall Score": 0.0
#         }
    
#     # 1. Cosine Similarity
#     try:
#         model = get_model()
#         orig_trunc = original[:8000] if len(original) > 8000 else original
#         sum_trunc = summary[:8000] if len(summary) > 8000 else summary
#         orig_embed = model.encode([orig_trunc])[0]
#         sum_embed = model.encode([sum_trunc])[0]
#         cosine_sim = float(cosine_similarity([orig_embed], [sum_embed])[0][0])
#     except Exception:
#         cosine_sim = 0.5
    
#     # 2. Compression Ratio
#     orig_words = len(original.split())
#     sum_words = len(summary.split())
#     compression = orig_words / max(sum_words, 1)
#     compression_score = min(1.0, compression / 20)
    
#     # 3. Coverage - FIXED
#     coverage = calculate_coverage(original, summary)
    
#     # 4. Redundancy
#     redundancy = calculate_redundancy(summary)
#     redundancy_penalty = 1 - min(0.3, redundancy)
    
#     # 5. Density
#     density = calculate_density(summary)
    
#     # 6. Readability - FIXED
#     readability = flesch_reading_ease(summary)
    
#     # Overall Score
#     overall = (
#         cosine_sim * 0.50 +
#         coverage * 0.25 +
#         compression_score * 0.15 +
#         density * 0.05 +
#         redundancy_penalty * 0.05
#     )
#     overall = max(0.0, min(1.0, overall))
    
#     return {
#         "Cosine Similarity": round(cosine_sim, 4),
#         "Compression Ratio": round(compression, 2),
#         "Coverage": round(coverage, 4),
#         "Overall Score": round(overall, 4),
#         "Readability (Flesch)": round(readability, 2),
#         "Redundancy": round(redundancy, 4),
#         "Density": round(density, 4)
#     }


# if __name__ == "__main__":
#     # Test with bullet-point summary
#     test_summary = """- AI simulates human thought
#     - Performs cognitive tasks
#     - Used in healthcare and finance"""
    
#     test_original = "Artificial Intelligence simulates human thought processes and performs cognitive tasks like learning and problem-solving. AI is used in healthcare and finance."
    
#     results = evaluate_summary(test_original, test_summary)
#     print("Test Results:")
#     for key, value in results.items():
#         print(f"  {key}: {value}")


import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def normalize_for_flesch(text: str) -> str:
    """Normalize bullet-point summaries into proper sentences"""
    if not text:
        return text
    
    lines = text.splitlines()
    normalized = []
    
    for line in lines:
        line = line.strip()
        line = re.sub(r'^[\s•*\-*\d+\.\s]+', '', line)
        line = line.strip()
        
        if not line:
            continue
        
        if not line.endswith(('.', '!', '?')):
            line += '.'
        
        normalized.append(line)
    
    return ' '.join(normalized)


def flesch_reading_ease(text: str) -> float:
    """Calculate Flesch Reading Ease score"""
    if not text or len(text.strip()) < 50:
        return 50.0
    
    text = normalize_for_flesch(text)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    
    if not sentences:
        return 50.0
    
    num_sentences = len(sentences)
    words = re.findall(r'\b[a-zA-Z]+(?:-[a-zA-Z]+)?\b', text)
    num_words = len(words)
    
    if num_words < 10:
        return 50.0
    
    def count_syllables(word: str) -> int:
        word = word.lower().strip()
        word = re.sub(r'[^\w]', '', word)
        if not word:
            return 1
        if len(word) <= 3:
            return 1
        vowel_count = len(re.findall(r'[aeiouy]+', word))
        if word.endswith('e') and vowel_count > 1:
            vowel_count -= 1
        return max(vowel_count, 1)
    
    num_syllables = sum(count_syllables(word) for word in words)
    flesch = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (num_syllables / max(num_words, 1))
    
    return max(0.0, min(100.0, flesch))


def calculate_coverage(original: str, summary: str) -> float:
    """
    FIXED: Coverage with controlled boost (1.3x, not 2.0x)
    Rewards abstraction, not listing
    """
    if not original or not summary:
        return 0.0
    
    orig_lower = original.lower()
    sum_lower = summary.lower()
    
    common_words = {
        'the', 'a', 'an', 'and', 'of', 'to', 'in', 'for', 'on', 'with', 
        'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
        'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'but', 'or',
        'so', 'for', 'nor', 'yet', 'at', 'by', 'from', 'into', 'through',
        'during', 'including', 'without', 'within', 'this', 'that', 'these',
        'those', 'there', 'their', 'they', 'will', 'would', 'could', 'should',
        'may', 'might', 'must', 'can', 'cannot', 'not', 'no', 'yes', 'also',
        'very', 'just', 'such', 'each', 'both', 'only', 'over', 'under',
        'then', 'than', 'when', 'where', 'which', 'while', 'because', 'using',
        'like', 'enable', 'perform', 'process', 'provide', 'use', 'based',
        'study', 'research', 'paper', 'article', 'find', 'found', 'show'
    }
    
    def extract_words(text):
        words = set()
        for word in text.split():
            word_clean = re.sub(r'[^\w]', '', word)
            if len(word_clean) >= 3 and word_clean not in common_words:
                words.add(word_clean)
        return words
    
    orig_words = extract_words(orig_lower)
    sum_words = extract_words(sum_lower)
    
    if not orig_words:
        return 0.5
    
    overlap = len(orig_words.intersection(sum_words))
    
    # FIXED: 1.3x boost instead of 2.0x
    # Rewards abstraction, penalizes listing everything
    coverage = min(1.0, (overlap / len(orig_words)) * 1.3)
    
    return round(coverage, 4)


def calculate_redundancy(summary: str) -> float:
    """Estimate redundancy in the summary"""
    if not summary or len(summary.split()) < 50:
        return 0.0
    
    summary_norm = normalize_for_flesch(summary)
    sentences = re.split(r'[.!?]+', summary_norm)
    sentences = [s.strip().lower() for s in sentences if len(s.strip()) > 15]
    
    if len(sentences) < 2:
        return 0.0
    
    seen = set()
    duplicate_count = 0
    for s in sentences:
        if s in seen:
            duplicate_count += 1
        else:
            seen.add(s)
    
    return round(duplicate_count / len(sentences), 4)


def calculate_density(summary: str) -> float:
    """Calculate information density"""
    if not summary:
        return 0.0
    
    key_terms = re.findall(r'\b[a-zA-Z]{4,}\b', summary.lower())
    unique_terms = len(set(key_terms))
    total_words = len(summary.split())
    
    if total_words == 0:
        return 0.0
    
    density = min(1.0, unique_terms / total_words * 2.0)
    return round(density, 4)


def evaluate_summary(original: str, summary: str) -> dict:
    """
    FIXED: Balanced evaluation that rewards abstraction, not copying
    
    New weights:
    - Cosine Similarity: 25% (down from 50%)
    - Coverage: 25% (same)
    - Compression: 20% (up from 15%)
    - Density: 10% (same)
    - Redundancy: 10% (up from 5%)
    - Length Penalty: 10% (NEW - discourages overly long summaries)
    - Readability: removed from overall (informational only)
    """
    if not original or not summary:
        return {
            "Cosine Similarity": 0.0,
            "Compression Ratio": 0.0,
            "Readability (Flesch)": 50.0,
            "Coverage": 0.0,
            "Redundancy": 0.0,
            "Density": 0.0,
            "Overall Score": 0.0
        }
    
    # 1. Cosine Similarity
    try:
        model = get_model()
        orig_trunc = original[:8000] if len(original) > 8000 else original
        sum_trunc = summary[:8000] if len(summary) > 8000 else summary
        orig_embed = model.encode([orig_trunc])[0]
        sum_embed = model.encode([sum_trunc])[0]
        cosine_sim = float(cosine_similarity([orig_embed], [sum_embed])[0][0])
    except Exception:
        cosine_sim = 0.5
    
    # 2. Compression Ratio
    orig_words = len(original.split())
    sum_words = len(summary.split())
    compression = orig_words / max(sum_words, 1)
    compression_score = min(1.0, compression / 5)  # Ideal: 5x compression
    
    # 3. Coverage (FIXED: 1.3x boost)
    coverage = calculate_coverage(original, summary)
    
    # 4. Redundancy
    redundancy = calculate_redundancy(summary)
    redundancy_penalty = 1 - min(0.3, redundancy)
    
    # 5. Density
    density = calculate_density(summary)
    
    # 6. Readability (informational only - NOT in overall score)
    readability = flesch_reading_ease(summary)
    
    # ============================================================
    # NEW: Length Penalty (discourages overly long summaries)
    # ============================================================
    # Ideal summary should be ~15% of original length
    ideal_ratio = 0.15
    actual_ratio = sum_words / max(orig_words, 1)
    length_penalty = max(0, 1 - abs(actual_ratio - ideal_ratio) * 3)
    # Clamp to reasonable range
    length_penalty = min(1.0, length_penalty)
    
    # ============================================================
    # NEW WEIGHTS - Balanced for abstraction, not copying
    # ============================================================
    overall = (
        cosine_sim * 0.20 +          # ↓ further reduce copying bias
        coverage * 0.25 +            # keep important
        compression_score * 0.20 +   # enforce conciseness
        density * 0.15 +             # ↑ reward info richness
        redundancy_penalty * 0.10 +
        length_penalty * 0.10
    )
    
    overall = max(0.0, min(1.0, overall))
    
    return {
        "Cosine Similarity": round(cosine_sim, 4),
        "Compression Ratio": round(compression, 2),
        "Coverage": round(coverage, 4),
        "Overall Score": round(overall, 4),
        "Readability (Flesch)": round(readability, 2),
        "Redundancy": round(redundancy, 4),
        "Density": round(density, 4),
        "Length Penalty": round(length_penalty, 4),
        "Original Words": orig_words,
        "Summary Words": sum_words,
        "Compression %": f"{round(100 / compression, 1) if compression > 0 else 0}%"
    }