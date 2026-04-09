import logging
import os
import uuid

import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy import select

from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB, UPLOAD_DIR
from app.database import async_session
from app.models.audio_job import AudioJob, JobStatus
from app.schemas.job import JobCreateResponse, JobDetailResponse
from app.services.job_service import run_job

router = APIRouter(prefix="/jobs", tags=["Jobs"])
logger = logging.getLogger(__name__)


@router.post("", response_model=JobCreateResponse, status_code=201)
async def create_job(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # validate file size by reading content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB}MB.",
        )

    # save file locally with unique name to avoid collisions
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = UPLOAD_DIR / unique_name

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    logger.info(f"Saved uploaded file: {file_path}")

    # create db record
    job = AudioJob(
        file_name=file.filename,
        file_path=str(file_path),
        status=JobStatus.PENDING,
    )

    async with async_session() as db:
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = job.id

    logger.info(f"Created job {job_id} for file '{file.filename}'")

    # trigger background processing
    background_tasks.add_task(run_job, job_id)

    return JobCreateResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Job created. Processing will begin shortly.",
    )


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: uuid.UUID):
    async with async_session() as db:
        job = await db.get(AudioJob, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    keywords_list = job.keywords.split(",") if job.keywords else None

    return JobDetailResponse(
        id=job.id,
        file_name=job.file_name,
        status=job.status,
        transcription=job.transcription,
        keywords=keywords_list,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
