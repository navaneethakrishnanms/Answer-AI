"""Schemas for DeepSeek evaluation output - Updated for per-question evaluation"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class SubdivisionEvaluationSchema(BaseModel):
    """Evaluation result for a subdivision"""
    subdivision_ref: str = Field(..., description="Reference (e.g., 'A1.1.i')")
    marks_obtained: float = Field(..., description="Marks awarded")
    max_marks: float = Field(..., description="Maximum possible marks")
    reasoning: str = Field(..., description="Evaluation reasoning")
    feedback: Optional[str] = Field(default=None, description="Specific feedback")


class QuestionEvaluationSchema(BaseModel):
    """Evaluation result for a single question"""
    question_ref: str = Field(..., description="Question reference (e.g., 'A1.1', 'A1.2')")
    marks_obtained: float = Field(..., description="Marks for this question")
    max_marks: float = Field(..., description="Maximum possible marks")
    reasoning: str = Field(..., description="Evaluation reasoning")
    feedback: str = Field(default="", description="Feedback for this question")
    question_type: Optional[str] = Field(default=None, description="1-mark, true-false, or multi-mark")
    subdivisions: Optional[List[SubdivisionEvaluationSchema]] = Field(
        default=None,
        description="Subdivision evaluations if applicable"
    )
    evaluated: bool = Field(default=True, description="Whether this question was evaluated")


class PartEvaluationSchema(BaseModel):
    """Evaluation result for a part (e.g., A1, A2)"""
    part_id: str = Field(..., description="Part ID (e.g., 'A1', 'B2')")
    questions_evaluated: List[QuestionEvaluationSchema] = Field(
        default_factory=list, 
        description="Evaluated questions in this part"
    )
    total_marks_obtained: float = Field(default=0.0, description="Total marks for this part")
    max_marks: float = Field(..., description="Maximum marks for this part")
    attempted: bool = Field(default=True, description="Whether student attempted this part")
    dropped: bool = Field(default=False, description="Whether this part was dropped (lowest)")


class SectionEvaluationSchema(BaseModel):
    """Evaluation result for a section"""
    section_id: str = Field(..., description="Section ID (A, B, or C)")
    parts_evaluated: List[PartEvaluationSchema] = Field(
        default_factory=list,
        description="Evaluated parts in this section"
    )
    # Legacy field for backward compatibility
    questions_evaluated: List[QuestionEvaluationSchema] = Field(
        default_factory=list, 
        description="Flattened list of all evaluated questions"
    )
    total_marks_obtained: float = Field(default=0.0, description="Total marks in this section")
    max_marks: float = Field(..., description="Maximum marks for this section")
    questions_answered: int = Field(default=0, description="Number of questions attempted")
    dropped_question: Optional[str] = Field(default=None, description="Part ID that was dropped")
    remarks: Optional[str] = Field(default=None, description="Section-level remarks")


class EvaluationOutputSchema(BaseModel):
    """
    DEEPSEEK OUTPUT SCHEMA - FINAL EVALUATION WITH MARKS
    """
    student_id: str = Field(default="", description="Student identifier")
    
    sections: Dict[str, SectionEvaluationSchema] = Field(
        ...,
        description="Evaluation results by section"
    )
    
    total_marks: float = Field(..., description="Total marks obtained across all sections")
    max_total_marks: float = Field(default=50.0, description="Maximum possible marks")
    percentage: float = Field(..., description="Percentage score")
    
    remarks: str = Field(..., description="Overall performance remarks")
    
    evaluation_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Evaluation metadata (timestamp, model version, etc.)"
    )


class EvaluationValidationSchema(BaseModel):
    """Schema for validating evaluation output"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Validation checks
    marks_within_limits: bool = Field(default=True)
    section_a_valid: bool = Field(default=True)
    section_b_valid: bool = Field(default=True)
    section_c_valid: bool = Field(default=True)
