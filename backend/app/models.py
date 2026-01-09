"""Database models for job tracking"""

from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class JobStatus(str, enum.Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class EvaluationJob(Base):
    """Model for tracking evaluation jobs"""
    
    __tablename__ = "evaluation_jobs"
    
    id = Column(String, primary_key=True, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    
    # File paths
    question_paper_path = Column(String, nullable=False)
    answer_key_path = Column(String, nullable=False)
    student_answer_path = Column(String, nullable=False)
    
    # Progress tracking
    current_step = Column(String, default="initialized")
    progress_percentage = Column(Float, default=0.0)
    
    # Results
    mapping_result = Column(JSON, nullable=True)
    evaluation_result = Column(JSON, nullable=True)
    
    # Error tracking
    error_message = Column(String, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Job Metadata
    job_metadata = Column(JSON, nullable=True)
