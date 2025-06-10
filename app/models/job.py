from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobCreate(BaseModel):
    source_type: str = Field(..., description="Type of data source (e.g., 'csv', 'api')")
    source_config: Dict[str, Any] = Field(..., description="Configuration for the data source")
    description: Optional[str] = Field(None, description="Optional description of the job")

class JobResponse(JobCreate):
    id: str = Field(..., description="Unique identifier for the job")
    status: JobStatus = Field(..., description="Current status of the job")
    created_at: datetime = Field(..., description="Timestamp when the job was created")
    updated_at: datetime = Field(..., description="Timestamp when the job was last updated")
    completed_at: Optional[datetime] = Field(None, description="Timestamp when the job was completed")
    error: Optional[str] = Field(None, description="Error message if the job failed")
    progress: Optional[float] = Field(None, description="Progress percentage of the job")
    result: Optional[Dict[str, Any]] = Field(None, description="Result data from the job execution")

class Job(BaseModel):
    id: str = Field(..., description="Unique job ID")
    filename: str = Field(..., description="Original filename")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current job status")
    created_at: datetime = Field(default_factory=datetime.now, description="When the job was created")
    started_at: Optional[datetime] = Field(None, description="When processing started")
    completed_at: Optional[datetime] = Field(None, description="When processing completed")
    total_records: Optional[int] = Field(None, description="Total records to process")
    processed_records: Optional[int] = Field(None, description="Records processed so far")
    successful_records: Optional[int] = Field(None, description="Successfully processed records")
    failed_records: Optional[int] = Field(None, description="Failed records")
    progress_percentage: Optional[float] = Field(None, description="Processing progress percentage")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    result: Optional[Dict[str, Any]] = Field(None, description="Processing result details") 