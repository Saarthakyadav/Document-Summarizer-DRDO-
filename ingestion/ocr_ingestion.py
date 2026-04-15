# import os
# import urllib.parse
# import re
# from typing import List
# import cv2  # Add this import at the top
# import fitz  # PyMuPDF
# from PIL import Image
# import pytesseract

# # -------------------------
# # CONFIG
# # -------------------------
# CACHE_ENABLED = True

# # Configure tesseract path if needed (uncomment and set your path)
# # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
# # pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Linux/Mac


# # -------------------------
# # TEXT VALIDATION
# # -------------------------
# def is_text_valid(text: str, min_chars: int = 100) -> bool:
#     """Check if extracted text has reasonable quality"""
#     if not text or len(text) < min_chars:
#         return False
    
#     # Check for reasonable word length (no run-on words)
#     words = text.split()
#     if words:
#         avg_word_len = sum(len(w) for w in words) / len(words)
#         if avg_word_len > 20:  # Words too long - missing spaces
#             return False
    
#     # Check vowel ratio (real text needs vowels)
#     vowel_ratio = len(re.findall(r'[aeiouAEIOU]', text)) / max(len(text), 1)
#     if vowel_ratio < 0.05:
#         return False
    
#     return True


# # -------------------------
# # CLEANING
# # -------------------------
# def clean_ocr_text(text: str) -> str:
#     """Clean up OCR output"""
#     # Remove non-printable characters
#     text = re.sub(r"[^\x20-\x7E\n]", " ", text)
#     # Normalize multiple newlines
#     text = re.sub(r"\n{3,}", "\n\n", text)
#     # Normalize multiple spaces
#     text = re.sub(r"[ \t]{2,}", " ", text)
#     # Fix missing spaces after periods
#     text = re.sub(r'\.([A-Z])', r'. \1', text)
#     return text.strip()


# def correct_common_ocr_errors(text: str) -> str:
#     """Fix common OCR misreads"""
#     fixes = [
#         (r'\b0\b', 'O'),
#         (r'\b1\b', 'I'),
#         (r'\b5\b', 'S'),
#         (r'rn', 'm'),
#         (r'cl', 'd'),
#         (r'vv', 'w'),
#     ]
#     for pattern, repl in fixes:
#         text = re.sub(pattern, repl, text)
#     return text


# # -------------------------
# # IMAGE PREPROCESSING
# # -------------------------
# def preprocess_image(image: Image.Image) -> Image.Image:
#     """Apply preprocessing to improve OCR accuracy"""
#     # Convert to grayscale
#     if image.mode != 'L':
#         image = image.convert('L')
    
#     # Increase contrast (optional)
#     import numpy as np
#     img_array = np.array(image)
    
#     # Apply thresholding for better text detection
#     _, img_array = cv2.threshold(img_array, 150, 255, cv2.THRESH_BINARY)
    
#     return Image.fromarray(img_array)


# # -------------------------
# # PYTESSERACT OCR
# # -------------------------
# def ocr_with_tesseract(image: Image.Image, preprocess: bool = True) -> str:
#     """Extract text using pytesseract"""
#     if preprocess:
#         image = preprocess_image(image)
    
#     # Configure tesseract for better accuracy
#     custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
    
#     try:
#         text = pytesseract.image_to_string(image, config=custom_config)
#         return clean_ocr_text(text)
#     except Exception as e:
#         print(f"⚠️ Tesseract OCR error: {e}")
#         return ""


# # -------------------------
# # PDF EXTRACTION
# # -------------------------
# def extract_native_text_from_pdf(file_path: str) -> str:
#     """Extract native text from PDF (no OCR)"""
#     try:
#         doc = fitz.open(file_path)
#         text = []
#         for page in doc:
#             page_text = page.get_text("text").strip()
#             if page_text:
#                 text.append(page_text)
#         doc.close()
#         return "\n\n".join(text)
#     except Exception as e:
#         print(f"⚠️ Native extraction error: {e}")
#         return ""


# def ocr_pdf_page(page, dpi: int = 300) -> str:
#     """Run OCR on a single PDF page"""
#     try:
#         # Convert PDF page to image
#         pix = page.get_pixmap(dpi=dpi)
#         img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
#         # Run OCR
#         text = ocr_with_tesseract(img, preprocess=True)
#         return text
#     except Exception as e:
#         print(f"⚠️ Page OCR error: {e}")
#         return ""


# def extract_text_from_pdf(file_path: str, prefer_native: bool = True, dpi: int = 200) -> str:
#     """
#     Extract text from PDF using native extraction + OCR fallback
    
#     Args:
#         file_path: Path to PDF file
#         prefer_native: If True, try native extraction first
#         dpi: Resolution for OCR (higher = better but slower)
#     """
#     try:
#         doc = fitz.open(file_path)
#         total_pages = len(doc)
#         pages_text = []
#         ocr_pages = 0
        
#         for page_num, page in enumerate(doc, 1):
#             print(f"  Processing page {page_num}/{total_pages}...")
            
#             page_text = ""
            
#             # Try native extraction first
#             if prefer_native:
#                 page_text = page.get_text("text").strip()
            
#             # If native extraction failed or returned garbage, use OCR
#             if not is_text_valid(page_text, min_chars=50):
#                 print(f"    📸 Using OCR on page {page_num}")
#                 page_text = ocr_pdf_page(page, dpi=dpi)
#                 ocr_pages += 1
            
#             if page_text:
#                 pages_text.append(page_text)
        
#         doc.close()
        
#         if ocr_pages > 0:
#             print(f"📊 OCR used on {ocr_pages}/{total_pages} pages")
        
#         return "\n\n".join(pages_text)
    
#     except Exception as e:
#         print(f"❌ PDF extraction error: {e}")
#         return ""


# def extract_text_from_image(file_path: str) -> str:
#     """Extract text from image file using pytesseract"""
#     try:
#         image = Image.open(file_path)
#         text = ocr_with_tesseract(image, preprocess=True)
#         return text
#     except Exception as e:
#         print(f"❌ Image OCR error: {e}")
#         return ""


# # -------------------------
# # MAIN OCR PIPELINE
# # -------------------------
# def extract_text_from_ocr(file_path: str, prefer_native: bool = True, dpi: int = 200) -> str:
#     """
#     Main entry point for text extraction
    
#     Args:
#         file_path: Path to PDF or image file
#         prefer_native: If True, try native PDF extraction before OCR
#         dpi: Resolution for OCR (100-300, higher = better but slower)
    
#     Returns:
#         Extracted text as string
#     """
#     # Fix Windows file paths
#     if file_path.startswith("file:///"):
#         file_path = urllib.parse.unquote(file_path.replace("file:///", ""))
    
#     file_path = os.path.abspath(file_path)
    
#     if not os.path.exists(file_path):
#         raise FileNotFoundError(f"File not found: {file_path}")
    
#     # Check cache
#     cache_file = file_path + ".txt"
#     if CACHE_ENABLED and os.path.exists(cache_file):
#         print(f"📦 Loading from cache: {cache_file}")
#         with open(cache_file, "r", encoding="utf-8") as f:
#             return f.read()
    
#     # Extract based on file type
#     file_ext = file_path.lower()
    
#     if file_ext.endswith(".pdf"):
#         print(f"📄 Processing PDF: {os.path.basename(file_path)}")
#         text = extract_text_from_pdf(file_path, prefer_native=prefer_native, dpi=dpi)
    
#     elif file_ext.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
#         print(f"🖼️ Processing image: {os.path.basename(file_path)}")
#         text = extract_text_from_image(file_path)
    
#     else:
#         raise ValueError(f"Unsupported file format: {file_ext}")
    
#     # Final cleaning
#     text = clean_ocr_text(text)
#     text = correct_common_ocr_errors(text)
    
#     # Validate output
#     if not is_text_valid(text):
#         print("⚠️ Warning: Extracted text may be low quality")
    
#     # Cache result
#     if CACHE_ENABLED and text:
#         with open(cache_file, "w", encoding="utf-8") as f:
#             f.write(text)
#         print(f"💾 Cached to: {cache_file}")
    
#     return text


# # -------------------------
# # ENTRY FUNCTION
# # -------------------------
# def ingest_document(file_path: str, prefer_native: bool = True, dpi: int = 200) -> str:
#     """
#     Simple entry point for document ingestion
    
#     Args:
#         file_path: Path to PDF or image file
#         prefer_native: Try native PDF extraction first
#         dpi: OCR resolution
    
#     Returns:
#         Extracted and cleaned text
#     """
#     text = extract_text_from_ocr(file_path, prefer_native=prefer_native, dpi=dpi)
    
#     if not text or len(text.strip()) < 50:
#         print("❌ Failed to extract meaningful text")
#         return ""
    
#     return text
import os
import urllib.parse
import re
from typing import List
import fitz  # PyMuPDF
from PIL import Image, ImageEnhance
import pytesseract

# -------------------------
# CONFIG
# -------------------------
CACHE_ENABLED = True

# Configure tesseract path if needed (uncomment and set your path)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Linux/Mac


# -------------------------
# TEXT VALIDATION
# -------------------------
def is_text_valid(text: str, min_chars: int = 100) -> bool:
    """Check if extracted text has reasonable quality"""
    if not text or len(text) < min_chars:
        return False
    
    # Check for reasonable word length (no run-on words)
    words = text.split()
    if words:
        avg_word_len = sum(len(w) for w in words) / len(words)
        if avg_word_len > 20:
            return False
    
    # Check vowel ratio (real text needs vowels)
    vowel_ratio = len(re.findall(r'[aeiouAEIOU]', text)) / max(len(text), 1)
    if vowel_ratio < 0.05:
        return False
    
    return True


# -------------------------
# CLEANING
# -------------------------
def clean_ocr_text(text: str) -> str:
    """Clean up OCR output"""
    # Remove non-printable characters
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)
    # Normalize multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Normalize multiple spaces
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Fix missing spaces after periods
    text = re.sub(r'\.([A-Z])', r'. \1', text)
    return text.strip()


def correct_common_ocr_errors(text: str) -> str:
    """Fix common OCR misreads"""
    fixes = [
        (r'\b0\b', 'O'),
        (r'\b1\b', 'I'),
        (r'\b5\b', 'S'),
        (r'rn', 'm'),
        (r'cl', 'd'),
        (r'vv', 'w'),
    ]
    for pattern, repl in fixes:
        text = re.sub(pattern, repl, text)
    return text


# -------------------------
# IMAGE PREPROCESSING (NO CV2)
# -------------------------
def preprocess_image(image: Image.Image) -> Image.Image:
    """Apply preprocessing to improve OCR accuracy using PIL only"""
    # Convert to grayscale
    if image.mode != 'L':
        image = image.convert('L')
    
    # Increase contrast using PIL
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    # Increase sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)
    
    return image


# -------------------------
# PYTESSERACT OCR
# -------------------------
def ocr_with_tesseract(image: Image.Image, preprocess: bool = True) -> str:
    """Extract text using pytesseract"""
    if preprocess:
        image = preprocess_image(image)
    
    # Configure tesseract for better accuracy
    custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
    
    try:
        text = pytesseract.image_to_string(image, config=custom_config)
        return clean_ocr_text(text)
    except Exception as e:
        print(f"⚠️ Tesseract OCR error: {e}")
        return ""


# -------------------------
# PDF EXTRACTION
# -------------------------
def extract_native_text_from_pdf(file_path: str) -> str:
    """Extract native text from PDF (no OCR)"""
    try:
        doc = fitz.open(file_path)
        text = []
        for page in doc:
            page_text = page.get_text("text").strip()
            if page_text:
                text.append(page_text)
        doc.close()
        return "\n\n".join(text)
    except Exception as e:
        print(f"⚠️ Native extraction error: {e}")
        return ""


def ocr_pdf_page(page, dpi: int = 300) -> str:
    """Run OCR on a single PDF page"""
    try:
        # Convert PDF page to image
        pix = page.get_pixmap(dpi=dpi)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Run OCR
        text = ocr_with_tesseract(img, preprocess=True)
        return text
    except Exception as e:
        print(f"⚠️ Page OCR error: {e}")
        return ""


def extract_text_from_pdf(file_path: str, prefer_native: bool = True, dpi: int = 200) -> str:
    """Extract text from PDF using native extraction + OCR fallback"""
    try:
        doc = fitz.open(file_path)
        total_pages = len(doc)
        pages_text = []
        ocr_pages = 0
        
        for page_num, page in enumerate(doc, 1):
            print(f"  Processing page {page_num}/{total_pages}...")
            
            page_text = ""
            
            if prefer_native:
                page_text = page.get_text("text").strip()
            
            if not is_text_valid(page_text, min_chars=50):
                print(f"    📸 Using OCR on page {page_num}")
                page_text = ocr_pdf_page(page, dpi=dpi)
                ocr_pages += 1
            
            if page_text:
                pages_text.append(page_text)
        
        doc.close()
        
        if ocr_pages > 0:
            print(f"📊 OCR used on {ocr_pages}/{total_pages} pages")
        
        return "\n\n".join(pages_text)
    
    except Exception as e:
        print(f"❌ PDF extraction error: {e}")
        return ""


def extract_text_from_image(file_path: str) -> str:
    """Extract text from image file using pytesseract"""
    try:
        image = Image.open(file_path)
        text = ocr_with_tesseract(image, preprocess=True)
        return text
    except Exception as e:
        print(f"❌ Image OCR error: {e}")
        return ""


# -------------------------
# MAIN OCR PIPELINE
# -------------------------
def extract_text_from_ocr(file_path: str, prefer_native: bool = True, dpi: int = 200) -> str:
    """Main entry point for text extraction"""
    # Fix Windows file paths
    if file_path.startswith("file:///"):
        file_path = urllib.parse.unquote(file_path.replace("file:///", ""))
    
    file_path = os.path.abspath(file_path)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Check cache
    cache_file = file_path + ".txt"
    if CACHE_ENABLED and os.path.exists(cache_file):
        print(f"📦 Loading from cache: {cache_file}")
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()
    
    # Extract based on file type
    file_ext = file_path.lower()
    
    if file_ext.endswith(".pdf"):
        print(f"📄 Processing PDF: {os.path.basename(file_path)}")
        text = extract_text_from_pdf(file_path, prefer_native=prefer_native, dpi=dpi)
    
    elif file_ext.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
        print(f"🖼️ Processing image: {os.path.basename(file_path)}")
        text = extract_text_from_image(file_path)
    
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")
    
    # Final cleaning
    text = clean_ocr_text(text)
    text = correct_common_ocr_errors(text)
    
    # Validate output
    if not is_text_valid(text):
        print("⚠️ Warning: Extracted text may be low quality")
    
    # Cache result
    if CACHE_ENABLED and text:
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"💾 Cached to: {cache_file}")
    
    return text


# -------------------------
# ENTRY FUNCTION
# -------------------------
def ingest_document(file_path: str, prefer_native: bool = True, dpi: int = 200) -> str:
    """Simple entry point for document ingestion"""
    text = extract_text_from_ocr(file_path, prefer_native=prefer_native, dpi=dpi)
    
    if not text or len(text.strip()) < 50:
        print("❌ Failed to extract meaningful text")
        return ""
    
    return text