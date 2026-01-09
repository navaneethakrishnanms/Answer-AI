"""Section and question parsing rules"""

import re
from typing import Dict, List
from app.config import Config

class SectionRules:
    """Rules for section structure and constraints"""
    
    @staticmethod
    def get_section_config() -> Dict[str, dict]:
        """
        Get section configuration from config.yaml
        
        Returns:
            Dictionary with section rules
        """
        sections = Config.get('exam_rules.sections', [])
        
        config = {}
        for section in sections:
            config[section['name']] = {
                'total_questions': section['total_questions'],
                'questions_to_answer': section['questions_to_answer'],
                'max_marks': section['max_marks']
            }
        
        return config
    
    @staticmethod
    def validate_section_structure(section_id: str, questions: List[dict]) -> tuple[bool, List[str]]:
        """
        Validate section structure against rules
        
        Args:
            section_id: Section identifier (A, B, or C)
            questions: List of questions in the section
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        config = SectionRules.get_section_config()
        
        if section_id not in config:
            return False, [f"Invalid section ID: {section_id}"]
        
        section_config = config[section_id]
        errors = []
        
        # Check number of questions
        if len(questions) != section_config['total_questions']:
            errors.append(
                f"Section {section_id} should have {section_config['total_questions']} questions, "
                f"found {len(questions)}"
            )
        
        return len(errors) == 0, errors
    
    @staticmethod
    def get_max_marks_for_section(section_id: str) -> int:
        """Get maximum marks for a section"""
        config = SectionRules.get_section_config()
        return config.get(section_id, {}).get('max_marks', 0)
    
    @staticmethod
    def get_questions_to_answer(section_id: str) -> int:
        """Get number of questions to answer in a section"""
        config = SectionRules.get_section_config()
        return config.get(section_id, {}).get('questions_to_answer', 2)
    
    @staticmethod
    def should_drop_lowest(section_id: str, answered_count: int) -> bool:
        """
        Check if lowest score should be dropped
        
        Args:
            section_id: Section identifier
            answered_count: Number of questions answered
        
        Returns:
            True if lowest should be dropped
        """
        required = SectionRules.get_questions_to_answer(section_id)
        total = SectionRules.get_section_config()[section_id]['total_questions']
        
        # Drop lowest if student answered all questions
        return answered_count == total and required < total

class QuestionParser:
    """Parser for question labels and subdivisions"""
    
    # Pattern for main questions: A1, B2, C3
    MAIN_QUESTION_PATTERN = re.compile(r'^([ABC])(\d+)$')
    
    # Pattern for roman numeral subdivisions: (i), (ii), (iii), (iv)
    ROMAN_SUBDIVISION_PATTERN = re.compile(r'^\(?([ivxIVX]+)\)?\.?$')
    
    # Pattern for alphabetic subdivisions: a, b, c OR (a), (b), (c)
    ALPHA_SUBDIVISION_PATTERN = re.compile(r'^\(?([a-z])\)?\.?$')
    
    # Pattern for numeric subdivisions: 1, 2, 3 OR (1), (2), (3)
    NUMERIC_SUBDIVISION_PATTERN = re.compile(r'^\(?(\d+)\)?\.?$')
    
    @staticmethod
    def parse_main_question_id(text: str) -> tuple[str, str]:
        """
        Parse main question ID
        
        Args:
            text: Question text line
        
        Returns:
            Tuple of (section, number) or (None, None)
        """
        match = QuestionParser.MAIN_QUESTION_PATTERN.match(text.strip())
        if match:
            return match.group(1), match.group(2)
        return None, None
    
    @staticmethod
    def is_roman_subdivision(text: str) -> bool:
        """Check if text is a roman numeral subdivision"""
        return bool(QuestionParser.ROMAN_SUBDIVISION_PATTERN.match(text.strip()))
    
    @staticmethod
    def is_alpha_subdivision(text: str) -> bool:
        """Check if text is an alphabetic subdivision"""
        return bool(QuestionParser.ALPHA_SUBDIVISION_PATTERN.match(text.strip()))
    
    @staticmethod
    def is_numeric_subdivision(text: str) -> bool:
        """Check if text is a numeric subdivision"""
        return bool(QuestionParser.NUMERIC_SUBDIVISION_PATTERN.match(text.strip()))
    
    @staticmethod
    def normalize_label(label: str) -> str:
        """
        Normalize subdivision label (remove parentheses, dots)
        
        Args:
            label: Raw label text
        
        Returns:
            Normalized label
        """
        return re.sub(r'[\(\)\.]', '', label.strip())
    
    @staticmethod
    def extract_marks(text: str) -> tuple[int, str]:
        """
        Extract marks from question text if present
        
        Args:
            text: Question text
        
        Returns:
            Tuple of (marks, text_without_marks)
        """
        # Pattern: [5 marks], (5 marks), [5m], (5), etc.
        patterns = [
            r'\[(\d+)\s*marks?\]',
            r'\((\d+)\s*marks?\)',
            r'\[(\d+)m\]',
            r'\((\d+)\)',
            r'(\d+)\s*marks?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                marks = int(match.group(1))
                text_clean = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
                return marks, text_clean
        
        return None, text
