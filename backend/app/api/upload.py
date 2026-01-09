"""API endpoints for file upload"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List
import os
import uuid
import shutil
import asyncio
from pathlib import Path
from app.config import Config
from app.services import (
    OCRService,
    PreprocessingService,
    QwenMapperService,
    DeepSeekEvaluatorService
)
from app.models import JobStatus
from app.database import get_db, AsyncSessionLocal
from app.models import EvaluationJob
from sqlalchemy import select
import logging
from app.logger import log_stage_start, log_stage_complete, log_progress, log_stage_error, get_job_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])

# Ensure upload directory exists
UPLOAD_DIR = Path(Config.get('storage.upload_dir', './uploads'))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def process_evaluation_job(job_id: str):
    """
    Background task to process evaluation
    
    Args:
        job_id: Job identifier
    """
    job_logger = get_job_logger(job_id, "SYSTEM")
    job_logger.info("="*60)
    job_logger.info("🚀 EVALUATION PIPELINE STARTED")
    job_logger.info("="*60)
    
    async with AsyncSessionLocal() as db:
        try:
            # Get job
            result = await db.execute(
                select(EvaluationJob).where(EvaluationJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            # Update status
            job.status = JobStatus.PROCESSING
            job.current_step = "ocr_extraction"
            job.progress_percentage = 10
            await db.commit()
            
            # ============================================================
            # STAGE 1: OCR EXTRACTION (PARALLEL)
            # ============================================================
            log_stage_start(job_id, "OCR", "Extracting text from 3 PDFs in parallel")
            ocr_service = OCRService()
            
            # Process all 3 PDFs simultaneously for 2x speed
            qp_task = ocr_service.extract_text_from_pdf(
                job.question_paper_path,
                job_id=job_id,
                doc_name="Question Paper"
            )
            ak_task = ocr_service.extract_text_from_pdf(
                job.answer_key_path,
                job_id=job_id,
                doc_name="Answer Key"
            )
            sa_task = ocr_service.extract_text_from_pdf(
                job.student_answer_path,
                job_id=job_id,
                doc_name="Student Answers"
            )
            
            # Wait for all OCR tasks to complete
            results = await asyncio.gather(qp_task, ak_task, sa_task)
            (qp_text, qp_errors), (ak_text, ak_errors), (sa_text, sa_errors) = results
            
            # Check for errors
            if qp_errors:
                raise Exception(f"Failed to extract question paper: {qp_errors}")
            if ak_errors:
                raise Exception(f"Failed to extract answer key: {ak_errors}")
            if sa_errors:
                raise Exception(f"Failed to extract student answers: {sa_errors}")
            
            log_progress(job_id, "OCR", f"Question Paper: {len(qp_text)} chars")
            log_progress(job_id, "OCR", f"Answer Key: {len(ak_text)} chars")
            log_progress(job_id, "OCR", f"Student Answers: {len(sa_text)} chars")
            log_stage_complete(job_id, "OCR", "All 3 PDFs extracted successfully")
            job.progress_percentage = 55
            job.current_step = "preprocessing"
            await db.commit()
            
            # ============================================================
            # STAGE 2: PREPROCESSING
            # ============================================================
            preprocessing_service = PreprocessingService()
            preprocessed_data = preprocessing_service.prepare_for_mapping(
                qp_text, ak_text, sa_text, job_id=job_id
            )
            
            job.progress_percentage = 60
            job.current_step = "mapping"
            await db.commit()
            
            # ============================================================
            # STAGE 3: MAPPING WITH QWEN 2.5 (NO TIMEOUT)
            # ============================================================
            log_stage_start(job_id, "MAPPING", "Qwen 2.5 14B model (no timeout)")
            qwen_service = QwenMapperService()
            
            log_progress(job_id, "MAPPING", "Building comprehensive mapping (async, unlimited time)...")
            mapping_result = await qwen_service.map_exam_data(preprocessed_data, job_id=job_id)
            
            # Validate mapping
            validation = qwen_service.validate_mapping(mapping_result)
            if not validation.is_valid:
                log_progress(job_id, "MAPPING", f"⚠ Validation warnings: {len(validation.warnings)}")
                logger.warning(f"Mapping validation warnings: {validation.warnings}")
            
            log_stage_complete(job_id, "MAPPING", f"✓ Mapped {len(mapping_result.sections)} sections")
            job.mapping_result = mapping_result.model_dump()
            job.progress_percentage = 75
            job.current_step = "evaluation"
            await db.commit()
            
            # ============================================================
            # STAGE 4: EVALUATION WITH DEEPSEEK-R1 (NO TIMEOUT)
            # ============================================================
            log_stage_start(job_id, "EVALUATION", "DeepSeek-R1 7B model (parallel processing)")
            deepseek_service = DeepSeekEvaluatorService()
            
            log_progress(job_id, "EVALUATION", "Evaluating all sections in parallel (no timeout)...")
            evaluation_result = await deepseek_service.evaluate_exam(mapping_result, job_id=job_id)
            
            # Validate evaluation (warnings only, don't block)
            eval_validation = deepseek_service.validate_evaluation(evaluation_result)
            if not eval_validation.is_valid:
                log_progress(job_id, "EVALUATION", f"⚠ Validation warnings: {eval_validation.warnings}")
            
            log_stage_complete(job_id, "EVALUATION", f"✓ Marks: {evaluation_result.total_marks}/{evaluation_result.max_total_marks}")
            job.evaluation_result = evaluation_result.model_dump()
            job.progress_percentage = 100
            job.current_step = "completed"
            job.status = JobStatus.COMPLETED
            await db.commit()
            
            # ============================================================
            # FINALIZATION
            # ============================================================
            log_stage_start(job_id, "FINAL", "Finalizing results")
            log_progress(job_id, "FINAL", f"Total Marks: {evaluation_result.total_marks}")
            log_progress(job_id, "FINAL", f"Sections Evaluated: {len(evaluation_result.sections)}")
            
            job_logger.info("="*60)
            job_logger.info(f"🎉 EVALUATION COMPLETED SUCCESSFULLY")
            job_logger.info(f"📊 Total Marks: {evaluation_result.total_marks}")
            job_logger.info(f"📝 Sections: {len(evaluation_result.sections)}")
            job_logger.info("="*60)
        
        except Exception as e:
            log_stage_error(job_id, "SYSTEM", str(e))
            logger.error(f"Error processing job {job_id}: {str(e)}")
            
            # Update job with error
            result = await db.execute(
                select(EvaluationJob).where(EvaluationJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.current_step = "failed"
                await db.commit()

@router.post("/upload")
async def upload_files(
    background_tasks: BackgroundTasks,
    question_paper: UploadFile = File(...),
    answer_key: UploadFile = File(...),
    student_answers: UploadFile = File(...)
):
    """
    Upload PDF files for evaluation
    
    Args:
        question_paper: Question paper PDF
        answer_key: Answer key PDF
        student_answers: Student answer sheet PDF
    
    Returns:
        Job ID for tracking
    """
    # Validate file types
    for file in [question_paper, answer_key, student_answers]:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} must be a PDF"
            )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create job directory
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Save files
        qp_path = job_dir / f"question_paper.pdf"
        ak_path = job_dir / f"answer_key.pdf"
        sa_path = job_dir / f"student_answers.pdf"
        
        with open(qp_path, "wb") as buffer:
            shutil.copyfileobj(question_paper.file, buffer)
        
        with open(ak_path, "wb") as buffer:
            shutil.copyfileobj(answer_key.file, buffer)
        
        with open(sa_path, "wb") as buffer:
            shutil.copyfileobj(student_answers.file, buffer)
        
        log_stage_start(job_id, "UPLOAD", "Files received and saved")
        log_progress(job_id, "UPLOAD", f"Question Paper: {question_paper.filename}")
        log_progress(job_id, "UPLOAD", f"Answer Key: {answer_key.filename}")
        log_progress(job_id, "UPLOAD", f"Student Answers: {student_answers.filename}")
        log_stage_complete(job_id, "UPLOAD", f"Saved to: {job_dir}")
        
        # Create job record
        async with AsyncSessionLocal() as db:
            job = EvaluationJob(
                id=job_id,
                status=JobStatus.PENDING,
                question_paper_path=str(qp_path),
                answer_key_path=str(ak_path),
                student_answer_path=str(sa_path),
                current_step="initialized",
                progress_percentage=0
            )
            
            db.add(job)
            await db.commit()
        
        # Start background processing
        background_tasks.add_task(process_evaluation_job, job_id)
        
        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "message": "Files uploaded successfully. Processing started.",
                "status": "pending"
            }
        )
    
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        
        # Clean up
        if job_dir.exists():
            shutil.rmtree(job_dir)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload files: {str(e)}"
        )
