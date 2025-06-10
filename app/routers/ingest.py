from fastapi import APIRouter, UploadFile, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.services.csv_service import CSVService
from app.services.job_service import JobService
from app.models.job import JobCreate, JobStatus
from app.config.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
import aiofiles
import os
import logging
from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/ingest-csv")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_period}")
async def ingest_csv(
    request: Request, file: UploadFile, db: AsyncIOMotorDatabase = Depends(get_database)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    try:
        # Create a temporary file to store the uploaded CSV
        temp_file_path = f"temp_{file.filename}"
        async with aiofiles.open(temp_file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        # Create a job for tracking the ingestion process
        job_service = JobService(db)
        job = JobCreate(
            source_type="csv",
            source_config={
                "filename": file.filename,
                "content_type": file.content_type
            },
            description=f"Ingesting CSV file: {file.filename}"
        )
        job_id = await job_service.create_job(job)

        # Process the CSV file with job tracking
        csv_service = CSVService(db)
        result = await csv_service.process_csv_with_job(temp_file_path, job_id)

        # Update job status
        await job_service.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            progress=100.0,
            result=result
        )

        # Clean up the temporary file
        os.remove(temp_file_path)

        return {
            "message": "CSV processing completed",
            "job_id": job_id,
            "details": result
        }

    except Exception as e:
        logger.error(f"Error processing CSV file: {str(e)}")
        if 'job_id' in locals():
            await job_service.update_job_status(
                job_id,
                JobStatus.FAILED,
                error=str(e)
            )
        raise HTTPException(status_code=500, detail=str(e))
