"""API endpoints for job status"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import EvaluationJob
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["status"])

@router.get("/status/{job_id}")
async def get_status(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get status of an evaluation job
    
    Args:
        job_id: Job identifier
    
    Returns:
        Job status and progress
    """
    try:
        result = await db.execute(
            select(EvaluationJob).where(EvaluationJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        response = {
            "job_id": job.id,
            "status": job.status.value,
            "current_step": job.current_step,
            "progress_percentage": job.progress_percentage,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None
        }
        
        # Include error if failed
        if job.status.value == "failed":
            response["error"] = {
                "message": job.error_message,
                "details": job.error_details
            }
        
        # Include result preview if completed
        if job.status.value == "completed" and job.evaluation_result:
            response["result_preview"] = {
                "student_id": job.evaluation_result.get("student_id", ""),
                "total_marks": job.evaluation_result.get("total_marks", 0),
                "max_total_marks": job.evaluation_result.get("max_total_marks", 0),
                "percentage": job.evaluation_result.get("percentage", 0)
            }
        
        return JSONResponse(content=response)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )
