from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from redis import Redis
from rq import Queue
from pydantic import BaseModel

app = FastAPI(title="gen-backend")

cors_origins_env = os.getenv("CORS_ORIGIN", "*")
origins = [o.strip() for o in cors_origins_env.split(",")] if cors_origins_env else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Redis / RQ setup
redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
audio_q = Queue("audio", connection=redis_conn)


@app.get("/health")
def health():
    return {"ok": True, "service": "gen-backend", "env": os.getenv("ENV", "development")}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI"}



class AudioJobRequest(BaseModel):
    audio_path: str


@app.post("/api/jobs/audio")
def create_audio_job(req: AudioJobRequest):
    job = audio_q.enqueue("worker.tasks.audio_to_musicxml", req.audio_path, job_timeout=3600)
    return {"job_id": job.get_id()}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    from rq.job import Job

    job = Job.fetch(job_id, connection=redis_conn)
    return {"status": job.get_status(), "result": job.result}

