from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import uuid
from pathlib import Path
from redis import Redis
from rq import Queue
from pydantic import BaseModel

app = FastAPI(title="audiogen-backend")

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
redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
audio_q = Queue("audio", connection=redis_conn)

# Temporary file storage for local testing
TEMP_UPLOAD_DIR = Path(tempfile.gettempdir()) / "audiogen_uploads"
TEMP_UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/health")
def health():
    return {"ok": True, "service": "audiogen-backend", "env": os.getenv("ENV", "development")}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI"}

class AudioJobRequest(BaseModel):
    audio_path: str


@app.post("/api/v1/jobs")
async def create_job(file: UploadFile = File(...)):
    """Upload audio file and create processing job"""
    # Validate file extension
    allowed_extensions = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file to temporary directory
    file_id = str(uuid.uuid4())
    file_path = TEMP_UPLOAD_DIR / f"{file_id}{file_ext}"
    
    try:
        # Read and save file
        contents = await file.read()
        
        # Check file size (30MB limit)
        max_size = 30 * 1024 * 1024  # 30MB
        if len(contents) > max_size:
            raise HTTPException(status_code=400, detail="File too large. Maximum size: 30MB")
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Enqueue job with file path
        job = audio_q.enqueue(
            "worker.tasks.audio_to_musicxml",
            str(file_path),
            job_timeout=3600
        )
        
        return {
            "id": job.get_id(),
            "status": "queued",
            "estimated_seconds": 60
        }
    
    except HTTPException:
        # Clean up file on validation error
        if file_path.exists():
            file_path.unlink()
        raise
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    """Get job status and result"""
    from rq.job import Job
    
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        status = job.get_status()
        
        response = {
            "id": job_id,
            "status": status,
            "progress": 0
        }
        
        if status == "finished":
            response["result"] = job.result
            response["progress"] = 100
            # Return MusicXML string in artifacts format
            response["artifacts"] = {
                "musicxml": {
                    "type": "musicxml",
                    "url": None,  # Would be S3 URL in production
                    "content": job.result  # Return MusicXML string directly for testing
                }
            }
        elif status == "failed":
            response["error"] = str(job.exc_info) if job.exc_info else "Unknown error"
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Job not found: {str(e)}")


@app.get("/api/v1/jobs/{job_id}")
def get_job_v1(job_id: str):
    """Get job status with v1 API format"""
    return get_job(job_id)

@app.get("/api/v1/allTracks")
def all_tracks():
    return {"message": "All tracks"}