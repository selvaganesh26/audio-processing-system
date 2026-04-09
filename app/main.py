import logging

from fastapi import FastAPI

from app.routers import jobs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Audio Job Processing Service",
    description="Upload audio files, process them asynchronously, and retrieve results.",
    version="1.0.0",
)

app.include_router(jobs.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
