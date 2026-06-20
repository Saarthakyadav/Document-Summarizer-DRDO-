"""
Standalone test script for Document Detector
Run this to test classification on any text file or PDF
"""
import os
import sys

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.document_detector import DocumentDetector
from ingestion.ocr_ingestion import extract_text_from_ocr
from ingestion.text_ingestion import load_text


def test_detector_on_text(text: str, source_name: str = "Document"):
    """Test detector on a text string"""
    print("\n" + "=" * 60)
    print(f"📄 Testing: {source_name}")
    print("=" * 60)
    
    detector = DocumentDetector()
    result = detector.detect(text)
    
    print(f"\n📊 DETECTION RESULT:")
    print(f"   Type: {result['type'].upper()}")
    print(f"   Confidence: {result['confidence']*100:.1f}%")
    print(f"\n📈 METADATA:")
    print(f"   Pages: ~{result['metadata']['pages']}")
    print(f"   Words: {result['metadata']['words']:,}")
    
    if result['type'] == 'book':
        print(f"   Has Chapters: {result['metadata'].get('has_chapters', False)}")
    elif result['type'] == 'paper':
        print(f"   Has Abstract: {result['metadata'].get('has_abstract', False)}")
    
    print("=" * 60)
    return result


def test_detector_on_file(file_path: str):
    """Test detector on a file (PDF or TXT)"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    print(f"\n📂 Loading file: {file_path}")
    
    # Extract text based on file type
    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_ocr(file_path)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    
    if not text or len(text) < 100:
        print("⚠️ Could not extract enough text from file")
        return None
    
    return test_detector_on_text(text, os.path.basename(file_path))


def quick_test():
    """Run quick tests with sample texts"""
    
    # Test 1: Book-like text
    book_text = """
    Chapter 1: Introduction to Programming
    This chapter introduces the basic concepts of programming.
    
    Chapter 2: Variables and Data Types
    This chapter covers variables, data types, and operators.
    
    Chapter 3: Control Structures
    This chapter explains if-else, loops, and switch statements.
    
    Chapter 4: Functions
    This chapter discusses function definition, parameters, and return values.
    
    Chapter 5: Arrays and Strings
    This chapter covers array manipulation and string handling.
    """
    
    # Test 2: Research paper-like text
    paper_text = """
    Abstract
    This paper presents a novel approach to machine learning...
    
    Introduction
    Machine learning has become increasingly important...
    
    Methodology
    We propose a new algorithm that combines...
    
    Results
    Our experiments show a 15% improvement...
    
    Discussion
    The results indicate that our approach outperforms...
    
    Conclusion
    We have demonstrated the effectiveness of...
    
    References
    [1] Smith et al. 2020
    [2] Johnson et al. 2021
    """
    
    # Test 3: General document-like text
    general_text = """
    This is a simple business document about capital budgeting.
    Capital budgeting is the process of evaluating long-term investments.
    Companies use NPV, IRR, and payback period to make decisions.
    The goal is to maximize shareholder value.
    """
    
    print("\n" + "🔬 DOCUMENT DETECTOR TEST SUITE" + "\n")
    
    test_detector_on_text(book_text * 10, "BOOK SAMPLE (with chapters)")
    test_detector_on_text(paper_text, "PAPER SAMPLE (with abstract/sections)")
    test_detector_on_text(general_text, "GENERAL SAMPLE (business doc)")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("📋 DOCUMENT DETECTOR TESTER")
    print("=" * 60)
    print("\nOptions:")
    print("  1. Run quick tests with sample texts")
    print("  2. Test on a specific file")
    print("  3. Enter custom text")
    
    choice = input("\nEnter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        quick_test()
    
    elif choice == "2":
        file_path = input("Enter file path (PDF or TXT): ").strip()
        test_detector_on_file(file_path)
    
    elif choice == "3":
        print("Enter your text (press Enter twice when done):")
        lines = []
        while True:
            line = input()
            if line == "" and len(lines) > 0 and lines[-1] == "":
                break
            lines.append(line)
        text = "\n".join(lines)
        test_detector_on_text(text, "Custom Text")
    
    else:
        print("Invalid choice. Running quick tests...")
        quick_test()
    
    print("\n✅ Test complete!")