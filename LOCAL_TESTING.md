# Local Testing Guide

This guide will help you run the project locally and test the complete file upload → worker processing → MusicXML return flow.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for running backend/worker locally if not using Docker)
- Node.js 18+ (for frontend, if testing frontend)

## Step 1: Start Infrastructure Services

Start only the infrastructure services (Postgres, Redis, MinIO) using Docker Compose:

```bash
docker-compose up -d postgres redis minio
```

Wait for services to be ready (about 10-30 seconds), then verify:

```bash
# Check services are running
docker-compose ps

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Check MinIO is accessible
curl http://localhost:9000/minio/health/live
```

### Initialize MinIO Bucket

1. Access MinIO Console at http://localhost:9001
2. Login with:
   - Username: `minioadmin`
   - Password: `minioadmin`
3. Click "Create Bucket"
4. Name: `audiogen-artifacts`
5. Click "Create Bucket"

Alternatively, if you have `mc` (MinIO Client) installed:

```bash
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/audiogen-artifacts
```

## Step 2: Setup Backend

### Option A: Run Backend in Docker

```bash
docker-compose up -d api
```

### Option B: Run Backend Locally (Recommended for Testing)

1. Navigate to backend directory:

```bash
cd backend
```

2. Create virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/WSL
# or
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create `.env` file:

```bash
cp env.example .env
```

5. Update `.env` for local development:

```env
PORT=4000
CORS_ORIGIN=*
ENV=development
REDIS_URL=redis://localhost:6379/0
```

6. Start backend server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
```

The backend should now be running at http://localhost:4000

Verify:

```bash
curl http://localhost:4000/health
# Should return: {"ok":true,"service":"audiogen-backend","env":"development"}
```

## Step 3: Setup Worker

### Option A: Run Worker in Docker

```bash
docker-compose up -d worker
```

### Option B: Run Worker Locally (Recommended for Testing)

1. **Stay in project root** (don't cd into worker directory)

2. Use the same virtual environment as backend (or create new one):

```bash
# If using same venv as backend, just activate it
# Otherwise create new venv
python3 -m venv backend/.venv
source backend/.venv/bin/activate  # Linux/WSL
# or
backend\.venv\Scripts\Activate.ps1  # Windows PowerShell
```

3. Install dependencies (from backend):

```bash
pip install -r backend/requirements.txt
```

4. Create `.env` file in worker directory:

```bash
cp worker/env.example worker/.env
```

5. Update `worker/.env`:

```env
REDIS_URL=redis://localhost:6379/0
RQ_QUEUES=audio,default
RQ_JOB_TIMEOUT=3600
```

6. Start worker (from project root):

```bash
python -m worker.worker
```

You should see output like:

```
INFO: Starting RQ worker on queues: ['audio', 'default']
INFO: Listening on queues: audio, default
```

## Step 4: Testing File Upload Flow

### Test 1: Upload a File via API

#### Using curl:

```bash
# Upload an audio file
curl -X POST http://localhost:4000/api/v1/jobs \
  -F "file=@/path/to/your/audio.mp3" \
  -F "options={\"separate\": false}"

# Example response:
# {"id":"<job_id>","status":"queued","estimated_seconds":60}
```

#### Using Python script:

Create a test script `test_upload.py`:

```python
import requests
import time
import sys

# Upload file
with open(sys.argv[1] if len(sys.argv) > 1 else "test_audio.mp3", "rb") as f:
    files = {"file": f}
    data = {"options": '{"separate": false}'}

    response = requests.post(
        "http://localhost:4000/api/v1/jobs",
        files=files,
        data=data
    )

    print(f"Upload Response: {response.json()}")
    job_id = response.json()["id"]

    # Poll for job status
    print(f"\nPolling job {job_id}...")
    while True:
        status_response = requests.get(f"http://localhost:4000/api/v1/jobs/{job_id}")
        status_data = status_response.json()
        print(f"Status: {status_data.get('status')}, Progress: {status_data.get('progress', 0)}%")

        if status_data.get("status") == "completed":
            print(f"\n✅ Job completed!")
            print(f"MusicXML: {status_data.get('artifacts', {}).get('musicxml', {}).get('url', 'N/A')}")
            break
        elif status_data.get("status") == "failed":
            print(f"\n❌ Job failed: {status_data.get('error', 'Unknown error')}")
            break

        time.sleep(2)
```

Run it:

```bash
python test_upload.py /path/to/your/audio.mp3
```

### Test 2: Check Worker Logs

While testing, watch the worker logs to see processing:

```bash
# If using Docker
docker-compose logs -f worker

# If running locally, check the terminal where worker is running
```

You should see:

- Job picked up from queue
- Processing message
- MusicXML generation completion

### Test 3: Verify MusicXML Result

Once job completes, get the MusicXML string:

```bash
# Get job status (includes MusicXML URL in artifacts)
curl http://localhost:4000/api/v1/jobs/<job_id>

# Or directly download MusicXML
curl http://localhost:4000/api/v1/jobs/<job_id>/artifacts/musicxml
```

## Step 5: Test with Frontend (Optional)

If you want to test with the frontend:

1. Navigate to frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
# or
bun install
```

3. Create `.env` file:

```env
VITE_API_URL=http://localhost:4000
```

4. Start frontend dev server:

```bash
npm run dev
# or
bun run dev
```

5. Open browser to http://localhost:5173
6. Upload an audio file through the UI
7. Monitor the job status page for results

## Troubleshooting

### Backend can't connect to Redis

- Ensure Redis is running: `docker-compose ps`
- Check REDIS_URL in backend `.env`: should be `redis://localhost:6379/0` for local
- Test Redis: `docker-compose exec redis redis-cli ping`

### Worker not processing jobs

- Check worker is running: `docker-compose ps` or check worker terminal
- Verify worker can connect to Redis
- Check worker logs for errors
- Ensure RQ_QUEUES includes "audio": `RQ_QUEUES=audio,default`

### File upload fails

- Check file size (default limit: 100MB)
- Verify file format (MP3, WAV, FLAC)
- Check backend logs for error messages
- Ensure MinIO bucket exists

### Job stuck in "queued" status

- Verify worker is running and listening to "audio" queue
- Check Redis connection
- Look at worker logs for errors
- Check if worker has necessary dependencies installed

## Testing Checklist

- [ ] Infrastructure services running (Postgres, Redis, MinIO)
- [ ] MinIO bucket created
- [ ] Backend API running on port 4000
- [ ] Worker running and listening to queues
- [ ] File upload endpoint accepts files
- [ ] Job created and queued successfully
- [ ] Worker picks up job from queue
- [ ] Worker processes file through `worker/tasks.py`
- [ ] MusicXML string generated and returned
- [ ] MusicXML string accessible via API
- [ ] Frontend can display results (if testing frontend)

## Monitoring Endpoints

- Backend Health: http://localhost:4000/health
- API Docs: http://localhost:4000/docs
- MinIO Console: http://localhost:9001
- Redis CLI: `docker-compose exec redis redis-cli`

## Next Steps

Once basic flow works:

1. Verify MusicXML content is correct
2. Test with different audio formats
3. Test error handling (invalid files, large files)
4. Add more detailed logging
5. Implement frontend UI for upload and status display
