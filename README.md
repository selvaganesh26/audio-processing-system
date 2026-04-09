# Audio Job Processing Service

A backend service that accepts audio file uploads, processes them asynchronously via a mock external processor, and exposes job status/results through REST APIs.

## Tech Stack

- **Python 3.12** + **FastAPI**
- **PostgreSQL** with async driver (asyncpg)
- **SQLAlchemy 2.0** (async ORM)
- **Alembic** for database migrations
- **Docker Compose** for containerized setup

## Project Structure

```
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py             # Settings and constants
│   ├── database.py           # Async DB engine and session
│   ├── models/
│   │   └── audio_job.py      # SQLAlchemy model
│   ├── schemas/
│   │   └── job.py            # Pydantic request/response schemas
│   ├── routers/
│   │   └── jobs.py           # API route handlers
│   └── services/
│       ├── job_service.py    # Background processing logic with retry
│       └── mock_processor.py # Simulated external audio processor
├── alembic/                  # Database migrations
├── uploads/                  # Uploaded audio files
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Setup & Run

### Option 1: Docker (recommended)

```bash
docker compose up --build
```

This starts both PostgreSQL and the app. Migrations run automatically on startup.

The API will be available at `http://localhost:8000`.

### Option 2: Local Development

1. Start a PostgreSQL instance and create a database:
   ```sql
   CREATE DATABASE audio_jobs_db;
   ```

2. Create a `.env` file (see `.env.example`):
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/audio_jobs_db
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

Interactive docs available at `http://localhost:8000/docs` (Swagger UI).

### POST /jobs

Upload an audio file to create a processing job.

**Constraints:**
- Accepted formats: `.mp3`, `.wav`
- Max file size: 25 MB

**Sample request (curl):**
```bash
curl -X POST http://localhost:8000/jobs \
  -F "file=@sample_audio.mp3"
```

**Sample response (201):**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "PENDING",
  "message": "Job created. Processing will begin shortly."
}
```

### GET /jobs/{job_id}

Retrieve the status and result of a job.

**Sample response (200) — processed:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "file_name": "sample_audio.mp3",
  "status": "PROCESSED",
  "transcription": "Welcome to today's podcast. We'll be discussing the latest trends in artificial intelligence and how they impact everyday life.",
  "keywords": ["artificial intelligence", "trends", "technology", "podcast"],
  "error_message": null,
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:05"
}
```

**Sample response (200) — failed:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "file_name": "sample_audio.mp3",
  "status": "FAILED",
  "transcription": null,
  "keywords": null,
  "error_message": "Processing failed after 3 attempts: External processor unavailable — connection timed out",
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:12"
}
```

## Database Schema

**Table: `audio_jobs`**

| Column        | Type                     | Notes                          |
|---------------|--------------------------|--------------------------------|
| id            | UUID                     | Primary key, auto-generated    |
| file_name     | VARCHAR(255)             | Original uploaded filename     |
| file_path     | VARCHAR(512)             | Local storage path             |
| status        | ENUM (JobStatus)         | PENDING / PROCESSING / PROCESSED / FAILED |
| transcription | TEXT                     | Nullable, populated on success |
| keywords      | TEXT                     | Nullable, comma-separated      |
| error_message | TEXT                     | Nullable, populated on failure |
| created_at    | DATETIME                 | Auto-set on creation           |
| updated_at    | DATETIME                 | Auto-updated on modification   |

## Architecture

```
Client
  │
  ▼
POST /jobs ──► Validate file ──► Save to disk ──► Create DB record (PENDING)
                                                        │
                                                        ▼
                                                  BackgroundTask
                                                        │
                                                        ▼
                                              Update status → PROCESSING
                                                        │
                                                        ▼
                                              Call mock processor (with retry)
                                                   ╱         ╲
                                                 ╱             ╲
                                            Success           Failure
                                               │                 │
                                               ▼                 ▼
                                          PROCESSED           FAILED
                                     (store results)    (store error msg)
```

- **Background processing** uses FastAPI's `BackgroundTasks` — lightweight and sufficient for this scope. For production with high throughput, I'd swap this for Celery + Redis.
- **Retry mechanism** uses exponential backoff (1s, 2s, 4s) with a configurable max of 3 attempts.
- **Mock processor** simulates a real external service with random latency (1-3s) and a 15% failure rate to exercise the retry and error-handling paths.

## Assumptions

- The mock processor is sufficient to demonstrate the async workflow; no real transcription model is used.
- File storage is local (on disk). In production, this would be S3 or similar object storage.
- `BackgroundTasks` is used instead of a task queue (Celery) to keep the setup simple for this scope.
- Keywords are stored as comma-separated text in the DB and returned as a list in the API response.
- UUID is used for job IDs to avoid sequential ID enumeration.
