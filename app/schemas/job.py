from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.audio_job import JobStatus


class JobCreateResponse(BaseModel):
    job_id: UUID
    status: JobStatus
    message: str


class JobDetailResponse(BaseModel):
    id: UUID
    file_name: str
    status: JobStatus
    transcription: Optional[str] = None
    keywords: Optional[list[str]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
