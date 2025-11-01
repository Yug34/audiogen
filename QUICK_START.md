# Quick Start Guide - Testing File Upload Flow

## Prerequisites Check

Make sure you have:

1. ✅ Docker and Docker Compose installed
2. ✅ Python 3.11+ installed
3. ✅ Infrastructure services running (if you ran docker-compose commands)

## Step-by-Step Testing

### 1. Start Infrastructure Services

```bash
# Start only infrastructure (Postgres, Redis, MinIO)
docker-compose up -d postgres redis minio

# Wait ~10 seconds, then verify services are up
docker-compose ps

# Test Redis
docker-compose exec redis redis-cli ping
```

**Initialize MinIO bucket:**

- Go to http://localhost:9001
- Login: `minioadmin` / `minioadmin`
- Create bucket: `audiogen-artifacts`

### 2. Start Backend (Terminal 1)

```bash
cd backend

# Create venv (if not done)
python3 -m venv .venv
source .venv/bin/activate  # Linux/WSL
# or
.\.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env (if not exists)
cp env.example .env

# Update .env for local:
# REDIS_URL=redis://localhost:6379/0

# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:4000
```

**Test backend:**

```bash
curl http://localhost:4000/health
# Should return: {"ok":true,...}
```

### 3. Start Worker (Terminal 2)

```bash
# Stay in project root

# Use same venv as backend or create new one
source backend/.venv/bin/activate  # or create new venv

# Install dependencies (if using new venv)
pip install -r backend/requirements.txt

# Create .env in worker dir (if not exists)
cp worker/env.example worker/.env

# Update worker/.env:
# REDIS_URL=redis://localhost:6379/0
# RQ_QUEUES=audio,default

# Start worker (from project root)
python3 -m worker.worker
```

You should see:

```
INFO: Starting RQ worker on queues: ['audio', 'default']
INFO: Listening on queues: audio, default
```

### 4. Test File Upload

#### Option A: Using the Test Script

```bash
# From project root
python3 test_upload.py /path/to/your/audio.mp3

# Example:
python3 test_upload.py ./test_audio.mp3
```

#### Option B: Using curl

```bash
# Upload file
curl -X POST http://localhost:4000/api/v1/jobs \
  -F "file=@/path/to/your/audio.mp3"

# Response will be: {"id":"<job_id>","status":"queued","estimated_seconds":60}

# Check job status (replace <job_id> with actual ID)
curl http://localhost:4000/api/v1/jobs/<job_id>

# Keep polling until status is "finished"
# When finished, response will include MusicXML in artifacts.content
```

#### Option C: Using Python

```python
import requests

# Upload
with open("test_audio.mp3", "rb") as f:
    response = requests.post(
        "http://localhost:4000/api/v1/jobs",
        files={"file": f}
    )
    job_id = response.json()["id"]
    print(f"Job ID: {job_id}")

# Check status
response = requests.get(f"http://localhost:4000/api/v1/jobs/{job_id}")
print(response.json())

# When status is "finished", MusicXML will be in:
# response.json()["artifacts"]["musicxml"]["content"]
```

### 5. Verify the Complete Flow

What to check:

1. **File Upload:**

   - ✅ File uploads successfully
   - ✅ Returns job_id
   - ✅ Backend saves file to temp directory

2. **Worker Processing:**

   - ✅ Worker picks up job from queue (check worker terminal logs)
   - ✅ Worker calls `worker.tasks.audio_to_musicxml()`
   - ✅ Function processes file and returns MusicXML string

3. **Result Return:**
   - ✅ Job status becomes "finished"
   - ✅ MusicXML string is in response: `artifacts.musicxml.content`
   - ✅ Can retrieve MusicXML via API

## What to Look For

### In Backend Logs:

```
INFO:     127.0.0.1:xxxxx - "POST /api/v1/jobs HTTP/1.1" 200 OK
```

### In Worker Logs:

```
worker.tasks.audio_to_musicxml('/tmp/audiogen_uploads/<file_id>.mp3')
Job <job_id> finished successfully
```

### In API Response (when finished):

```json
{
  "id": "<job_id>",
  "status": "finished",
  "progress": 100,
  "artifacts": {
    "musicxml": {
      "type": "musicxml",
      "url": null,
      "content": "<score-partwise version=\"3.1\"></score-partwise>"
    }
  }
}
```

## Troubleshooting

### Backend can't connect to Redis

- Check: `docker-compose ps` - Redis should be running
- Update: `REDIS_URL=redis://localhost:6379/0` in backend/.env
- Test: `docker-compose exec redis redis-cli ping`

### Worker not processing jobs

- Check worker is running and listening to "audio" queue
- Verify `RQ_QUEUES=audio,default` in worker/.env
- Check Redis connection: worker should show no errors

### File upload fails

- Check file size (< 100MB)
- Check file format (MP3, WAV, FLAC, M4A, OGG)
- Check backend logs for error messages

### Job stuck in "queued"

- Verify worker is running
- Check worker logs for errors
- Verify worker can access the file path (if running in Docker, path might differ)

## Next Steps After Testing

Once basic flow works:

1. Verify MusicXML content is correct
2. Test different audio formats
3. Test error handling
4. Add frontend UI (see frontend/ directory)
