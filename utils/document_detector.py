"""
Document Type Detector - Auto-detects if document is Book, Paper, or General
"""
import re
from typing import Dict, Tuple


class DocumentDetector:
    """
    Automatically detects document type with confidence scoring
    """
    
    def __init__(self):
        # Book indicators
        self.book_indicators = {
            "chapter_patterns": [
                r'(?:\n|^)(?:Chapter|CHAPTER|Ch\.|CH\.)\s+\d+',
                r'(?:\n|^)(?:Part|PART)\s+\w+',
                r'(?:\n|^)(?:Unit|UNIT)\s+\d+',
                r'(?:\n|^)CONTENTS?\s*\n',
                r'(?:\n|^)Table of Contents',
            ],
            "min_pages": 50,
        }
        
        # Research paper indicators
        self.paper_indicators = {
            "sections": [
                r'(?:\n|^)Abstract\b',
                r'(?:\n|^)Introduction\b',
                r'(?:\n|^)Methodology\b',
                r'(?:\n|^)Results?\b',
                r'(?:\n|^)Discussion\b',
                r'(?:\n|^)Conclusion\b',
                r'(?:\n|^)References?\b',
                r'(?:\n|^)Related Work\b',
            ],
            "min_sections": 3,
        }
    
    def detect(self, text: str) -> Dict:
        """
        Detect document type with confidence score
        
        Returns:
            {
                "type": "book" | "paper" | "general",
                "confidence": 0.0-1.0,
                "metadata": {...}
            }
        """
        word_count = len(text.split())
        estimated_pages = word_count / 300  # ~300 words per page
        
        # Calculate book score
        book_score = self._calculate_book_score(text, estimated_pages)
        
        # Calculate paper score
        paper_score = self._calculate_paper_score(text)
        
        # Determine type based on highest score
        if book_score > 0.6 and book_score > paper_score:
            return {
                "type": "book",
                "confidence": round(book_score, 2),
                "metadata": {
                    "pages": round(estimated_pages, 1),
                    "words": word_count,
                    "has_chapters": book_score > 0.7
                }
            }
        elif paper_score > 0.5:
            return {
                "type": "paper",
                "confidence": round(paper_score, 2),
                "metadata": {
                    "pages": round(estimated_pages, 1),
                    "words": word_count,
                    "has_abstract": paper_score > 0.7
                }
            }
        else:
            return {
                "type": "general",
                "confidence": round(1 - max(book_score, paper_score), 2),
                "metadata": {
                    "pages": round(estimated_pages, 1),
                    "words": word_count
                }
            }
    
    def _calculate_book_score(self, text: str, pages: float) -> float:
        """Calculate probability that document is a book"""
        score = 0.0
        
        # Factor 1: Length (books are long)
        if pages >= 100:
            score += 0.3
        elif pages >= 50:
            score += 0.2
        elif pages >= 30:
            score += 0.1
        
        # Factor 2: Chapter patterns
        chapter_matches = 0
        for pattern in self.book_indicators["chapter_patterns"]:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            chapter_matches += matches
        
        if chapter_matches >= 5:
            score += 0.4
        elif chapter_matches >= 3:
            score += 0.3
        elif chapter_matches >= 1:
            score += 0.15
        
        # Factor 3: Sequential chapter numbers
        chapter_nums = re.findall(r'(?:Chapter|CHAPTER|Ch\.)\s+(\d+)', text)
        if chapter_nums:
            nums = [int(n) for n in chapter_nums[:10]]
            if len(nums) > 1 and nums == list(range(nums[0], nums[0] + len(nums))):
                score += 0.2
        
        # Factor 4: Table of contents
        if re.search(r'(?:TABLE OF CONTENTS|CONTENTS)', text, re.IGNORECASE):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_paper_score(self, text: str) -> float:
        """Calculate probability that document is a research paper"""
        score = 0.0
        
        # Factor 1: Academic sections
        section_matches = 0
        for pattern in self.paper_indicators["sections"]:
            if re.search(pattern, text, re.IGNORECASE):
                section_matches += 1
        
        section_score = section_matches / len(self.paper_indicators["sections"])
        score += section_score * 0.5
        
        # Factor 2: Abstract presence
        if re.search(r'\bAbstract\b', text, re.IGNORECASE):
            abstract_match = re.search(r'Abstract\s*\n\s*([A-Z][^A-Z]{100,})', text, re.IGNORECASE | re.DOTALL)
            if abstract_match:
                score += 0.25
            else:
                score += 0.1
        
        # Factor 3: References section
        if re.search(r'\bReferences?\b', text, re.IGNORECASE):
            score += 0.15
        
        # Factor 4: Author patterns
        author_patterns = [
            r'(?:Author|By):\s+[A-Z][a-z]+\s+[A-Z][a-z]+',
            r'[A-Z][a-z]+\s+[A-Z][a-z]+,\s+\d+',
            r'Department of\s+\w+',
        ]
        for pattern in author_patterns:
            if re.search(pattern, text):
                score += 0.05
        
        return min(score, 1.0)


def detect_document_type(text: str) -> Dict:
    """Convenience function for document detection"""
    detector = DocumentDetector()
    return detector.detect(text)