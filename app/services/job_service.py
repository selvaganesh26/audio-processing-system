import asyncio
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.models.audio_job import AudioJob, JobStatus
from app.services.mock_processor import process_audio

logger = logging.getLogger(__name__)


async def run_job(job_id):
    """
    Background task: processes the audio file with retries,
    then updates the job record accordingly.
    """
    async with async_session() as db:
        job = await db.get(AudioJob, job_id)
        if not job:
            logger.error(f"Job {job_id} not found in database")
            return

        job.status = JobStatus.PROCESSING
        job.updated_at = datetime.utcnow()
        await db.commit()
        logger.info(f"Job {job_id} status -> PROCESSING")

        result = None
        last_error = None

        for attempt in range(1, settings.max_retries + 1):
            try:
                result = await process_audio(job.file_path)
                break
            except Exception as exc:
                last_error = str(exc)
                delay = settings.retry_base_delay * (2 ** (attempt - 1))
                logger.warning(
                    f"Job {job_id} attempt {attempt}/{settings.max_retries} failed: {exc}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)

        if result:
            job.transcription = result["transcription"]
            job.keywords = ",".join(result["keywords"])
            job.status = JobStatus.PROCESSED
            logger.info(f"Job {job_id} status -> PROCESSED")
        else:
            job.status = JobStatus.FAILED
            job.error_message = f"Processing failed after {settings.max_retries} attempts: {last_error}"
            logger.error(f"Job {job_id} status -> FAILED: {last_error}")

        job.updated_at = datetime.utcnow()
        await db.commit()
