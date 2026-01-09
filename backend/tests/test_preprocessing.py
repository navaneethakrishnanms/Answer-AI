"""
Comprehensive tests for Preprocessing Service
"""

import pytest
from pathlib import Path
from tests.test_framework import test, memoize_test, time_test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.preprocessing import PreprocessingService


class TestPreprocessingService:
    """Test suite for Preprocessing Service"""
    
    @time_test
    def test_clean_ocr_text(self):
        """Test OCR text cleaning"""
        service = PreprocessingService()
        
        # Test with messy OCR text
        dirty_text = "  Multiple    spaces\n\n\n\nmany newlines  PAGE 1  ===="
        cleaned = service.clean_ocr_text(dirty_text)
        
        assert "Multiple spaces" in cleaned
        assert "many newlines" in cleaned
        assert "PAGE 1" not in cleaned
        assert "====" not in cleaned
        assert cleaned.count('\n') < dirty_text.count('\n')
    
    @time_test
    def test_extract_sections(self, sample_question_paper):
        """Test section extraction"""
        service = PreprocessingService()
        
        sections = service.extract_sections(sample_question_paper)
        
        assert 'A' in sections
        assert 'B' in sections
        assert 'C' in sections
        assert len(sections) == 3
        
        # Verify section content
        assert 'A1' in sections['A']
        assert 'B1' in sections['B']
        assert 'C1' in sections['C']
    
    @time_test
    def test_normalize_question_labels(self):
        """Test question label normalization"""
        service = PreprocessingService()
        
        text = "A . 1  (i)  ( ii )  (a)"
        normalized = service.normalize_question_labels(text)
        
        assert "A1" in normalized
        assert "(i)" in normalized
        assert "(ii)" in normalized
    
    @time_test
    def test_extract_student_id(self):
        """Test student ID extraction"""
        service = PreprocessingService()
        
        texts = [
            "Student ID: ABC12345",
            "Roll No: XYZ-123",
            "Enrollment No. 12345",
            "ID: STUDENT001"
        ]
        
        for text in texts:
            student_id = service.extract_student_id(text)
            assert student_id != ""
            assert len(student_id) >= 3
    
    @time_test
    def test_split_into_pages(self):
        """Test page splitting"""
        service = PreprocessingService()
        
        text = """
========================================
PAGE 1
========================================
Content of page 1

========================================
PAGE 2
========================================
Content of page 2
"""
        
        pages = service.split_into_pages(text)
        
        assert len(pages) == 2
        assert pages[0]['page'] == 1
        assert "Content of page 1" in pages[0]['content']
        assert pages[1]['page'] == 2
        assert "Content of page 2" in pages[1]['content']
    
    @time_test
    def test_prepare_for_mapping(self, sample_question_paper, 
                                 sample_answer_key, sample_student_answers):
        """Test complete preprocessing pipeline"""
        service = PreprocessingService()
        
        result = service.prepare_for_mapping(
            sample_question_paper,
            sample_answer_key,
            sample_student_answers
        )
        
        # Verify structure
        assert 'question_paper' in result
        assert 'answer_key' in result
        assert 'student_answers' in result
        assert 'metadata' in result
        
        # Verify question paper sections
        assert 'sections' in result['question_paper']
        qp_sections = result['question_paper']['sections']
        assert len(qp_sections) >= 1
        
        # Verify student ID extraction
        assert result['student_answers']['student_id'] == "TEST12345"
        
        # Verify metadata
        metadata = result['metadata']
        assert metadata['qp_length'] > 0
        assert metadata['ak_length'] > 0
        assert metadata['sa_length'] > 0
    
    @time_test
    def test_empty_input_handling(self):
        """Test handling of empty inputs"""
        service = PreprocessingService()
        
        # Empty text
        cleaned = service.clean_ocr_text("")
        assert cleaned == ""
        
        # No sections
        sections = service.extract_sections("No sections here")
        assert len(sections) == 0
        
        # No student ID
        student_id = service.extract_student_id("Just some random text")
        assert student_id == ""


# Register tests with framework
@test("preprocessing_clean_text", priority=8, category="preprocessing")
def test_clean_text():
    """Test text cleaning"""
    print("  Testing text cleaning...")
    service = PreprocessingService()
    text = "  Messy   text\n\n\nwith    spaces  "
    cleaned = service.clean_ocr_text(text)
    assert "Messy text" in cleaned
    return True


@test("preprocessing_sections", priority=7, dependencies=["preprocessing_clean_text"], 
      category="preprocessing")
def test_sections():
    """Test section extraction"""
    print("  Testing section extraction...")
    service = PreprocessingService()
    text = """
    SECTION A
    Question A1
    
    SECTION B
    Question B1
    
    SECTION C
    Question C1
    """
    sections = service.extract_sections(text)
    assert len(sections) == 3
    return True


@test("preprocessing_student_id", priority=7, dependencies=["preprocessing_clean_text"],
      category="preprocessing")
def test_student_id():
    """Test student ID extraction"""
    print("  Testing student ID extraction...")
    service = PreprocessingService()
    text = "Student ID: TEST12345"
    student_id = service.extract_student_id(text)
    assert student_id == "TEST12345"
    return True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
