"""Preprocessing service for cleaning and preparing OCR text"""

import re
import logging
from typing import Dict, List
from app.logger import log_stage_start, log_stage_complete, log_progress

logger = logging.getLogger(__name__)

class PreprocessingService:
    """Service for preprocessing OCR text before mapping"""
    
    @staticmethod
    def clean_ocr_text(text: str, job_id: str = "N/A") -> str:
        """
        Clean OCR text by removing common OCR artifacts
        
        Args:
            text: Raw OCR text
            job_id: Job identifier for logging
        
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        log_progress(job_id, "PREPROCESSING", "Cleaning OCR artifacts")
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page markers if they appear
        text = re.sub(r'PAGE\s+\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'={10,}', '', text)
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive newlines (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    @staticmethod
    def extract_sections(text: str, job_id: str = "N/A") -> Dict[str, str]:
        """
        Extract sections A, B, C from text
        
        Args:
            text: Cleaned text
            job_id: Job identifier for logging
        
        Returns:
            Dictionary with section texts
        """
        log_progress(job_id, "PREPROCESSING", "Extracting sections A, B, C")
        sections = {}
        
        # Patterns for section headers
        patterns = {
            'A': r'SECTION\s*[:\-]?\s*A|PART\s*[:\-]?\s*A',
            'B': r'SECTION\s*[:\-]?\s*B|PART\s*[:\-]?\s*B',
            'C': r'SECTION\s*[:\-]?\s*C|PART\s*[:\-]?\s*C'
        }
        
        # Find section positions
        section_positions = []
        for section_id, pattern in patterns.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                section_positions.append((section_id, matches[0].start()))
        
        # Sort by position
        section_positions.sort(key=lambda x: x[1])
        
        # Extract text for each section
        for i, (section_id, start_pos) in enumerate(section_positions):
            if i < len(section_positions) - 1:
                end_pos = section_positions[i + 1][1]
            else:
                end_pos = len(text)
            
            sections[section_id] = text[start_pos:end_pos].strip()
        
        log_progress(job_id, "PREPROCESSING", f"Extracted {len(sections)} sections: {list(sections.keys())}")
        logger.info(f"Extracted {len(sections)} sections: {list(sections.keys())}")
        
        return sections
    
    @staticmethod
    def normalize_question_labels(text: str) -> str:
        """
        Normalize question labels for consistency
        
        Args:
            text: Text with question labels
        
        Returns:
            Text with normalized labels
        """
        # Normalize A1, A2, etc.
        text = re.sub(r'([ABC])\s*[\.\-]\s*(\d+)', r'\1\2', text)
        
        # Normalize (i), (ii), etc.
        text = re.sub(r'\(\s*([ivxIVX]+)\s*\)', r'(\1)', text)
        
        # Normalize (a), (b), etc.
        text = re.sub(r'\(\s*([a-z])\s*\)', r'(\1)', text)
        
        return text
    
    @staticmethod
    def extract_student_id(text: str) -> str:
        """
        Extract student ID from text
        
        Args:
            text: Text that may contain student ID
        
        Returns:
            Student ID or empty string
        """
        # Common patterns for student IDs
        patterns = [
            r'Student\s*ID\s*[:\-]?\s*([A-Z0-9\-]+)',
            r'Roll\s*No\.?\s*[:\-]?\s*([A-Z0-9\-]+)',
            r'Enrollment\s*No\.?\s*[:\-]?\s*([A-Z0-9\-]+)',
            r'ID\s*[:\-]?\s*([A-Z0-9\-]{5,})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                student_id = match.group(1).strip()
                logger.info(f"Found student ID: {student_id}")
                return student_id
        
        return ""
    
    @staticmethod
    def split_into_pages(text: str) -> List[Dict[str, str]]:
        """
        Split text into individual pages
        
        Args:
            text: Full OCR text with page markers
        
        Returns:
            List of dictionaries with page number and content
        """
        pages = []
        
        # Split by page markers
        page_pattern = r'={10,}\s*PAGE\s+(\d+)\s*={10,}'
        splits = re.split(page_pattern, text, flags=re.IGNORECASE)
        
        # Process splits (odd indices are page numbers, even indices are content)
        for i in range(1, len(splits), 2):
            if i + 1 < len(splits):
                page_num = splits[i]
                content = splits[i + 1].strip()
                pages.append({
                    'page': int(page_num),
                    'content': content
                })
        
        logger.info(f"Split text into {len(pages)} pages")
        
        return pages
    
    @staticmethod
    def prepare_for_mapping(
        question_paper_text: str,
        answer_key_text: str,
        student_answer_text: str,
        job_id: str = "N/A"
    ) -> Dict[str, any]:
        """
        Prepare all texts for mapping service
        
        Args:
            question_paper_text: OCR text from question paper
            answer_key_text: OCR text from answer key
            student_answer_text: OCR text from student answers
            job_id: Job identifier for logging
        
        Returns:
            Dictionary with cleaned and structured data
        """
        log_stage_start(job_id, "PREPROCESSING", "Cleaning and structuring OCR text")
        logger.info("Preparing texts for mapping service")
        
        # Clean all texts
        log_progress(job_id, "PREPROCESSING", "Cleaning OCR artifacts")
        qp_clean = PreprocessingService.clean_ocr_text(question_paper_text, job_id)
        ak_clean = PreprocessingService.clean_ocr_text(answer_key_text, job_id)
        sa_clean = PreprocessingService.clean_ocr_text(student_answer_text, job_id)
        
        # Normalize labels
        log_progress(job_id, "PREPROCESSING", "Normalizing question labels")
        qp_clean = PreprocessingService.normalize_question_labels(qp_clean)
        ak_clean = PreprocessingService.normalize_question_labels(ak_clean)
        sa_clean = PreprocessingService.normalize_question_labels(sa_clean)
        
        # Extract student ID
        student_id = PreprocessingService.extract_student_id(sa_clean)
        if student_id:
            log_progress(job_id, "PREPROCESSING", f"Found student ID: {student_id}")
        
        # Extract sections from question paper
        qp_sections = PreprocessingService.extract_sections(qp_clean, job_id)
        
        log_stage_complete(job_id, "PREPROCESSING", f"{len(qp_sections)} sections structured")
        
        return {
            'question_paper': {
                'full_text': qp_clean,
                'sections': qp_sections
            },
            'answer_key': {
                'full_text': ak_clean
            },
            'student_answers': {
                'full_text': sa_clean,
                'student_id': student_id
            },
            'metadata': {
                'qp_length': len(qp_clean),
                'ak_length': len(ak_clean),
                'sa_length': len(sa_clean),
                'sections_found': list(qp_sections.keys())
            }
        }
