# Backend (FastAPI)

## Setup

1. Create a virtual environment

- Linux/WSL:
  - `python3 -m venv .venv && source .venv/bin/activate`
- Windows PowerShell:
  - `py -3 -m venv .venv; .\\.venv\\Scripts\\Activate.ps1`

2. Install dependencies

- `pip install -r requirements.txt`

3. Configure environment

- Copy `env.example` to `.env` and adjust values
  - `REDIS_URL` defaults to `redis://redis:6379/0` in Docker

4. Run dev server

- `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-4000} --reload`

## Endpoints

- `GET /health` → service status
- `GET /api/hello` → sample data
- `POST /api/jobs/audio` → enqueue audio processing job
  - body: `{ "audio_path": "/path/to/audio.wav" }`
- `GET /api/jobs/{job_id}` → job status/result

## CORS

- Set `CORS_ORIGIN` to your frontend URL(s), e.g. `http://localhost:3000`.
- Multiple origins can be comma-separated.

## RQ / Redis

- The API enqueues jobs to the `audio` queue in Redis (`REDIS_URL`).
- The RQ worker runs separately and processes `worker.tasks.audio_to_musicxml`.
