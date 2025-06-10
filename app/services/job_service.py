import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.job import JobCreate, JobResponse, JobStatus
import logging

logger = logging.getLogger(__name__)


class JobService:
    async def update_job_result(self, job_id: str, result: dict):
        """
        Update the result field of a job document.
        """
        await self.db.jobs.update_one(
            {"id": job_id},
            {"$set": {"result": result}}
        )

    async def add_job_error(self, job_id: str, error_msg: str):
        """
        Append an error message to the job's errors list.
        """
        await self.db.jobs.update_one({"_id": job_id}, {"$push": {"errors": error_msg}})

    async def update_job_progress(
        self,
        job_id: str,
        processed_records: int,
        total_records: int,
        successful_records: int = 0,
        failed_records: int = 0,
    ):
        """
        Update the progress and stats of a job.
        """
        progress = (processed_records / total_records) * 100 if total_records else 0
        await self.db.jobs.update_one(
            {"_id": job_id},
            {
                "$set": {
                    "progress": progress,
                    "processed_records": processed_records,
                    "total_records": total_records,
                    "successful_records": successful_records,
                    "failed_records": failed_records,
                }
            },
        )

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.jobs

    async def create_job(self, job: JobCreate) -> str:
        """Create a new job in the database"""
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        job_doc = {
            "id": job_id,
            "source_type": job.source_type,
            "source_config": job.source_config,
            "description": job.description,
            "status": JobStatus.PENDING,
            "created_at": now,
            "updated_at": now,
            "progress": 0.0,
        }

        await self.collection.insert_one(job_doc)
        logger.info(f"Created new job with ID: {job_id}")
        return job_id

    async def get_job(self, job_id: str) -> Optional[JobResponse]:
        """Get a job by its ID"""
        job_doc = await self.collection.find_one({"id": job_id})
        if not job_doc:
            return None
        return JobResponse(**job_doc)

    async def list_jobs(
        self, status: Optional[JobStatus] = None, limit: int = 10, skip: int = 0
    ) -> List[JobResponse]:
        """List jobs with optional filtering"""
        query = {}
        if status:
            query["status"] = status

        cursor = self.collection.find(query).skip(skip).limit(limit)
        jobs = await cursor.to_list(length=limit)
        return [JobResponse(**job) for job in jobs]

    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error: Optional[str] = None,
        progress: Optional[float] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update job status and related fields"""
        update_data = {"status": status, "updated_at": datetime.now(timezone.utc)}

        if error is not None:
            update_data["error"] = error
        if progress is not None:
            update_data["progress"] = progress
        if result is not None:
            update_data["result"] = result
        if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            update_data["completed_at"] = datetime.now(timezone.utc)

        result = await self.collection.update_one({"id": job_id}, {"$set": update_data})
        return result.modified_count > 0

    async def delete_job(self, job_id: str) -> bool:
        """Delete a job and its associated data"""
        result = await self.collection.delete_one({"id": job_id})
        return result.deleted_count > 0

    async def process_job(self, job_id: str):
        """Process a job in the background"""
        try:
            # Update status to processing
            await self.update_job_status(job_id, JobStatus.PROCESSING)

            # Get job details
            job = await self.get_job(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            # Process based on source type
            if job.source_type == "csv":
                # TODO: Implement CSV processing
                pass
            elif job.source_type == "api":
                # TODO: Implement API processing
                pass
            else:
                raise ValueError(f"Unsupported source type: {job.source_type}")

            # Update status to completed
            await self.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                progress=100.0,
                result={"message": "Job completed successfully"},
            )

        except Exception as e:
            logger.error(f"Error processing job {job_id}: {str(e)}")
            await self.update_job_status(job_id, JobStatus.FAILED, error=str(e))
