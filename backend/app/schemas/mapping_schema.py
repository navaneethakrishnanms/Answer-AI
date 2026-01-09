"""Schemas for Qwen mapping output - Updated for Section → Part → Question hierarchy"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any


class SubdivisionSchema(BaseModel):
    """Schema for nested subdivisions (a, b, c or 1, 2, 3)"""
    label: Optional[str] = Field(default=None, description="Original label (e.g., 'a', '1', 'i')")
    content: Optional[str] = Field(default="", description="Subdivision question text")
    marks: Optional[float] = Field(default=None, description="Marks if explicitly stated")
    children: Optional[List['SubdivisionSchema']] = Field(default=None, description="Nested subdivisions")
    # Accept alternate field names from LLM
    subdivision_id: Optional[str] = Field(default=None, exclude=True)
    question_type: Optional[str] = Field(default=None, exclude=True)  # LLM sometimes adds this
    
    @model_validator(mode='before')
    @classmethod
    def normalize_fields(cls, data):
        """Accept subdivision_id as alias for label"""
        if isinstance(data, dict):
            # If LLM returned subdivision_id instead of label, use it
            if 'subdivision_id' in data and not data.get('label'):
                data['label'] = data.get('subdivision_id', '').split('.')[-1] if data.get('subdivision_id') else 'a'
            # Ensure label has a default
            if not data.get('label'):
                data['label'] = 'a'
            # Ensure content has a default
            if not data.get('content'):
                data['content'] = ""
        return data


SubdivisionSchema.model_rebuild()


class QuestionSchema(BaseModel):
    """
    Schema for individual questions within a part.
    Example: A 1-mark question, 2-mark question, 4-mark question within Part A1.
    """
    question_id: str = Field(..., description="Question ID (e.g., 'A1.1', 'A1.2')")
    content: str = Field(..., description="Question text")
    marks: float = Field(..., description="Marks for this question")
    question_type: Optional[str] = Field(
        default=None, 
        description="Type: '1-mark', 'true-false', 'multi-mark'"
    )
    subdivisions: Optional[List[SubdivisionSchema]] = Field(
        default=None, 
        description="Subdivisions if any (i, ii, iii)"
    )


class PartSchema(BaseModel):
    """
    Schema for parts within a section.
    Example: A1, A2, A3 are three parts in Section A.
    Student answers 2 out of 3 parts.
    """
    part_id: str = Field(..., description="Part ID (e.g., 'A1', 'A2', 'B1')")
    title: Optional[str] = Field(default=None, description="Part title if any")
    questions: List[QuestionSchema] = Field(..., description="Questions within this part")
    total_marks: float = Field(..., description="Total marks for this part")
    attempted: bool = Field(default=False, description="Whether student attempted this part")


class SectionSchema(BaseModel):
    """Schema for exam sections (A, B, C)"""
    section_id: str = Field(..., description="Section ID (A, B, or C)")
    parts: List[PartSchema] = Field(..., description="Parts in this section (e.g., A1, A2, A3)")
    max_marks: float = Field(..., description="Maximum marks for this section")
    parts_to_answer: int = Field(default=2, description="Number of parts student must answer")


class StudentAnswerSchema(BaseModel):
    """Schema for student's answer to a specific question/subdivision"""
    question_ref: str = Field(..., description="Reference to question (e.g., 'A1.1', 'A1.1.i')")
    answer_text: str = Field(..., description="Student's answer text from OCR")
    part_id: Optional[str] = Field(default=None, description="Part this answer belongs to (e.g., 'A1')")


class AnswerKeyItemSchema(BaseModel):
    """Schema for answer key entry"""
    question_ref: str = Field(..., description="Reference to question (e.g., 'A1.1', 'A1.1.i')")
    expected_answer: str = Field(..., description="Expected answer text")
    marks: float = Field(..., description="Marks for this answer")
    keywords: Optional[List[str]] = Field(default=None, description="Key concepts to look for")


class MappingOutputSchema(BaseModel):
    """
    QWEN OUTPUT SCHEMA - MAPPING ONLY
    Maps: Section → Part → Question
    NO EVALUATION, NO MARKS ASSIGNMENT, NO FEEDBACK
    """
    student_id: str = Field(default="", description="Student identifier if found")
    
    sections: Dict[str, SectionSchema] = Field(
        default_factory=dict,
        description="Mapped sections with parts and questions"
    )
    
    student_answers: Dict[str, List[StudentAnswerSchema]] = Field(
        default_factory=dict,
        description="Student answers grouped by section (e.g., 'A': [...])"
    )
    
    answer_key: Dict[str, List[AnswerKeyItemSchema]] = Field(
        default_factory=dict,
        description="Answer key entries grouped by section"
    )
    
    attempted_parts: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Which parts the student attempted per section (e.g., {'A': ['A1', 'A3']})"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (exam name, date, etc.)"
    )
    
    @model_validator(mode='before')
    @classmethod
    def normalize_response(cls, data):
        """Normalize LLM response and fill missing fields"""
        if isinstance(data, dict):
            # Remove unexpected root-level fields
            unexpected_fields = ['total_marks', 'max_marks', 'percentage']
            for field in unexpected_fields:
                if field in data:
                    # Store in metadata if present
                    if 'metadata' not in data:
                        data['metadata'] = {}
                    data['metadata'][field] = data.pop(field)
            
            # Ensure required dict fields exist
            if 'sections' not in data or data['sections'] is None:
                data['sections'] = {}
            if 'student_answers' not in data or data['student_answers'] is None:
                data['student_answers'] = {}
            if 'answer_key' not in data or data['answer_key'] is None:
                data['answer_key'] = {}
            if 'attempted_parts' not in data or data['attempted_parts'] is None:
                data['attempted_parts'] = {}
            if 'metadata' not in data or data['metadata'] is None:
                data['metadata'] = {}
        return data


class MappingValidationSchema(BaseModel):
    """Schema for validating mapping output"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
