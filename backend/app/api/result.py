"""API endpoints for retrieving results"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import EvaluationJob
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["results"])

@router.get("/result/{job_id}")
async def get_result(
    job_id: str,
    include_mapping: bool = Query(False, description="Include mapping data"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get evaluation result for a job
    
    Args:
        job_id: Job identifier
        include_mapping: Whether to include mapping data in response
    
    Returns:
        Evaluation result
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
        
        if job.status.value != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Job is not completed yet. Current status: {job.status.value}"
            )
        
        if not job.evaluation_result:
            raise HTTPException(
                status_code=500,
                detail="Evaluation result not found"
            )
        
        response = {
            "job_id": job.id,
            "status": job.status.value,
            "evaluation": job.evaluation_result
        }
        
        if include_mapping and job.mapping_result:
            response["mapping"] = job.mapping_result
        
        return JSONResponse(content=response)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting result for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get result: {str(e)}"
        )

@router.get("/result/{job_id}/download")
async def download_result(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Download evaluation result as JSON file
    
    Args:
        job_id: Job identifier
    
    Returns:
        JSON file for download
    """
    from fastapi.responses import Response
    import json
    
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
        
        if job.status.value != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Job is not completed yet"
            )
        
        if not job.evaluation_result:
            raise HTTPException(
                status_code=500,
                detail="Evaluation result not found"
            )
        
        # Create filename
        student_id = job.evaluation_result.get("student_id", "unknown")
        filename = f"evaluation_{student_id}_{job_id[:8]}.json"
        
        # Return as downloadable JSON
        return Response(
            content=json.dumps(job.evaluation_result, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading result for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download result: {str(e)}"
        )
