from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from app.services.job_service import JobService
from app.models.job import JobCreate, JobResponse, JobStatus
from app.config.database import get_database
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/jobs", response_model=JobResponse)
async def create_job(
    job: JobCreate,
    background_tasks: BackgroundTasks,
    db=Depends(get_database)
):
    """Create a new data ingestion job"""
    try:
        job_service = JobService(db)
        job_id = await job_service.create_job(job)
        
        # Start processing in background
        background_tasks.add_task(job_service.process_job, job_id)
        
        return await job_service.get_job(job_id)
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db=Depends(get_database)):
    """Get job status and details"""
    try:
        job_service = JobService(db)
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    status: JobStatus = None,
    limit: int = 10,
    skip: int = 0,
    db=Depends(get_database)
):
    """List all jobs with optional filtering"""
    try:
        job_service = JobService(db)
        return await job_service.list_jobs(status, limit, skip)
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, db=Depends(get_database)):
    """Delete a job and its associated data"""
    try:
        job_service = JobService(db)
        success = await job_service.delete_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"message": "Job deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 