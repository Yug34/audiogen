from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import uuid
from pathlib import Path
from redis import Redis
from rq import Queue
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import init_db, get_db, engine
from app.models import Song, Transcription

app = FastAPI(title="audiogen-backend")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

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
async def create_job(
    file: UploadFile = File(...), 
    songName: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload audio file and create processing job"""
    print(f"Song name: {songName}")
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
        file_size = len(contents)
        
        # Check file size (30MB limit)
        max_size = 30 * 1024 * 1024  # 30MB
        if file_size > max_size:
            raise HTTPException(status_code=400, detail="File too large. Maximum size: 30MB")
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Save song details to database first
        song = Song(
            name=songName
        )
        db.add(song)
        db.commit()
        db.refresh(song)
        
        # Enqueue job with file path, song name, and song_id
        job = audio_q.enqueue(
            "worker.tasks.audio_to_musicxml",
            str(file_path),
            songName,
            str(song.id),
            job_timeout=3600
        )
        
        # Update song with job_id
        song.job_id = job.get_id()
        db.commit()
        
        return {
            "id": job.get_id(),
            "status": "queued",
            "estimated_seconds": 60,
            "song_id": str(song.id)
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