import re
import unicodedata
from collections import Counter


def canonicalize_line(line: str) -> str:
    line = line.lower()
    line = re.sub(r"[^a-z0-9\s]", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def looks_like_boilerplate(original_line: str, canonical_line: str) -> bool:
    if not canonical_line:
        return True
    if len(canonical_line) < 4 or len(canonical_line.split()) <= 2:
        return True
    if canonical_line.isdigit():
        return True
    
    boilerplate_keywords = (
        r"\b(page|copyright|all rights reserved|draft|confidential"
        r"|proprietary|published by|printed in|edition|isbn"
        r"|reproduction|unauthorized|reserved)\b"
    )
    if re.search(boilerplate_keywords, canonical_line):
        return True
    if re.search(r"(www\.|http|https|\.com|\.org|\.edu|\.net|@)", original_line.lower()):
        return True
    tokens = canonical_line.split()
    if len(tokens) <= 10 and re.search(r"\b(19|20)\d{2}\b", canonical_line):
        return True
    if re.search(r"©\s*\d{4}|\(c\)\s*\d{4}", original_line, re.IGNORECASE):
        return True
    return False


def remove_semantically_repeated_lines(text: str, repetition_threshold: float = 0.5, max_removal_ratio: float = 0.2) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return ""
    canonical_lines = [canonicalize_line(l) for l in lines]
    counts = Counter(canonical_lines)
    total = len(canonical_lines)
    repeated = {
        canon
        for orig, canon in zip(lines, canonical_lines)
        if (counts[canon] / total) >= repetition_threshold
        and looks_like_boilerplate(orig, canon)
    }
    if not repeated:
        return text
    cleaned = [line for line in lines if canonicalize_line(line) not in repeated]
    removed_ratio = 1 - (len(cleaned) / len(lines))
    if removed_ratio > max_removal_ratio:
        return text
    return "\n".join(cleaned)


def strip_symbol_lines(text: str) -> str:
    cleaned = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            cleaned.append(line)
            continue
        alnum = len(re.findall(r"[a-zA-Z0-9]", stripped))
        ratio = alnum / len(stripped) if len(stripped) > 0 else 0
        if ratio >= 0.4:
            cleaned.append(line)
    return "\n".join(cleaned)


def is_data_row(line: str) -> bool:
    tokens = line.split()
    if len(tokens) < 4:
        return False
    def is_data_token(t):
        if re.fullmatch(r"\d+", t):
            return True
        if re.fullmatch(r"[A-Z]{1,5}", t):
            return True
        if re.fullmatch(r"[A-Z0-9\-]{2,8}", t) and re.search(r"\d", t):
            return True
        if len(t) >= 4 and not re.search(r"[aeiouAEIOU]", t):
            return True
        return False
    ratio = sum(is_data_token(t) for t in tokens) / len(tokens)
    return ratio > 0.5


def strip_data_rows(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not is_data_row(line.strip()))


def correct_common_ocr_errors(text: str) -> str:
    fixes = [
        (r"\bspeci ed\b", "specified"), (r"\bspeci c\b", "specific"),
        (r"\bspeci cation\b", "specification"), (r"\bsigni cant\b", "significant"),
        (r"\bidenti ed\b", "identified"), (r"\bclassi cation\b", "classification"),
        (r"\bde nition\b", "definition"), (r"\bde ned\b", "defined"),
        (r"\bde nes\b", "defines"), (r"\bcon guration\b", "configuration"),
        (r"\bin nite\b", "infinite"), (r"\bef cient\b", "efficient"),
        (r"\bef ort\b", "effort"), (r"\bdi erent\b", "different"),
        (r"\bof ce\b", "office"),
    ]
    for pattern, repl in fixes:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text


def light_sentence_cleanup(text: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    cleaned = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        alpha_ratio = len(re.findall(r'[a-zA-Z]', s)) / max(len(s), 1)
        if alpha_ratio < 0.2:
            continue
        cleaned.append(s)
    return " ".join(cleaned)


def fix_ocr_text(text: str) -> str:
    """Fix OCR issues WITHOUT removing spaces - ADDED for safety"""
    # Fix missing spaces after punctuation
    text = re.sub(r'\.([A-Z])', r'. \1', text)
    text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
    text = re.sub(r'\.(\d)', r'. \1', text)
    text = re.sub(r',([A-Za-z])', r', \1', text)
    return text

def fix_missing_spaces(text: str) -> str:
    """Fix common OCR missing space issues"""
    # Fix numbers followed by words
    text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)
    
    # Fix words ending with number followed by word
    text = re.sub(r'([A-Za-z])(\d)([A-Za-z])', r'\1 \2\3', text)
    
    # Fix "Made with Gamma" pattern
    text = re.sub(r'Made with Gamma', 'Made with Gamma ', text)
    
    # Fix period-number-word pattern
    text = re.sub(r'\.(\d)([A-Za-z])', r'.\1 \2', text)
    
    # Rest of your existing fixes...
    text = re.sub(r'\.([A-Z])', r'. \1', text)
    text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
    text = re.sub(r'\.(\d)', r'. \1', text)
    text = re.sub(r',([A-Za-z])', r', \1', text)
    
    return text

def clean_text(text: str) -> str:
    if not text:
        return ""
    
    # Normalize newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # CRITICAL: NO SPACE-REMOVING REGEX
    # The old regex that destroyed text has been COMPLETELY REMOVED
    text = fix_missing_spaces(text)
    
    # Fix OCR text issues (adds missing spaces)
    text = fix_ocr_text(text)
    
    # Fix hyphenated line breaks
    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
    
    # Unicode normalization
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[\x00-\x1f\x7f]", "", text)
    
    # Remove symbol noise
    text = strip_symbol_lines(text)
    
    # Remove repeated headers/footers
    text = remove_semantically_repeated_lines(text)
    
    # Remove table/data rows
    text = strip_data_rows(text)
    
    # Fix OCR errors
    text = correct_common_ocr_errors(text)
    
    # Remove page numbers
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            lines.append(line)
            continue
        if s.isdigit():
            continue
        if re.fullmatch(r"\d+\.\d+", s):
            continue
        lines.append(line)
    
    # Reconstruct paragraphs
    paragraphs = []
    buffer = ""
    for line in lines:
        line = line.strip()
        is_heading = (
            line.isupper() or
            bool(re.match(r"^\d+(\.\d+)*\s+[A-Z]", line)) or
            (len(line.split()) <= 6 and line.endswith(":"))
        )
        if not line:
            if buffer:
                paragraphs.append(buffer)
                buffer = ""
        elif buffer and not buffer.endswith((".", "!", "?", ":")) and not is_heading:
            buffer += " " + line
        else:
            if buffer:
                paragraphs.append(buffer)
            buffer = line
    if buffer:
        paragraphs.append(buffer)
    
    text = "\n\n".join(paragraphs)
    
    # Final cleanup
    paragraphs = [light_sentence_cleanup(p) for p in paragraphs]
    text = "\n\n".join(paragraphs)
    text = re.sub(r"[ \t]+", " ", text)
    
    return text.strip()