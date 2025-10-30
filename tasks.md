# AI Drum Tab Generator — Detailed Task Breakdown

## Phase 1: MVP — Core Pipeline & Basic Frontend

### 1.1 Repository Setup & Infrastructure Foundation

#### 1.1.1 Monorepo Structure

- [x] Create monorepo root with `docker-compose.yml` for local development
- [x] Set up shared `.gitignore` for Python, Node, and IDE files
- [ ] Create `backend/` directory with FastAPI application structure
- [ ] Create `frontend/` directory with React + Vite setup
- [ ] Create `worker/` directory for async job processing
- [ ] Create `infra/` directory for Docker files, k8s manifests (optional)
- [ ] Add root `README.md` with setup instructions and architecture overview
- [ ] Set up `.env.example` files for each service

#### 1.1.2 Docker Infrastructure

- [ ] Create `backend/Dockerfile` with Python 3.11+, install FastAPI dependencies
- [ ] Create `worker/Dockerfile` with ML dependencies (librosa, torch, HTDemucs, ONNX Runtime)
- [ ] Create `docker-compose.yml` with services: api, worker, redis, postgres, minio (S3-compatible)
- [ ] Create `docker-compose.dev.yml` for local development with volume mounts
- [ ] Add Redis service configuration with persistent volume
- [ ] Add Postgres service with initialization SQL schema
- [ ] Add MinIO service with bucket initialization (uploads/, artifacts/)
- [ ] Add healthcheck endpoints for all services
- [ ] Test docker-compose up and verify all services connect

#### 1.1.3 Database Schema

- [ ] Create `jobs` table: id (UUID), status (ENUM), created_at, updated_at, user_id (optional), progress (INT), error_msg (TEXT), estimated_seconds (INT)
- [ ] Create `job_artifacts` table: id, job_id (FK), type (ENUM), s3_key, s3_url, created_at
- [ ] Create `job_options` table: job_id (FK), separate_source (BOOL), quantize_grid (VARCHAR), swing_enabled (BOOL), tempo_override (FLOAT)
- [ ] Add database migration tool (Alembic) and create initial schema
- [ ] Add indexes on job_id, status, created_at

### 1.2 Backend API — Core Endpoints

#### 1.2.1 API Foundation

- [ ] Set up FastAPI app with Pydantic v2
- [ ] Configure CORS middleware with configurable origins
- [ ] Add structured logging (JSON format)
- [ ] Add request ID middleware for tracing
- [ ] Create API router structure: `/api/v1/`
- [ ] Add exception handlers for common errors (400, 404, 422, 500)
- [ ] Add health check endpoint: `GET /health` → `{ ok: true }`
- [ ] Add database connection pooling with SQLAlchemy
- [ ] Add S3 client initialization (boto3 or aioboto3)

#### 1.2.2 Jobs Endpoints

- [ ] Create `POST /api/v1/jobs` endpoint (multipart/form-data)
  - [ ] Parse file upload with size limit (100MB default)
  - [ ] Validate audio format (MP3, WAV, FLAC)
  - [ ] Validate options: `{ separate?, quantize?, swing?, tempo_override? }`
  - [ ] Upload file to S3 with unique key (UUID + timestamp)
  - [ ] Create job record in database with status="queued"
  - [ ] Enqueue job to Redis queue with job_id and S3 key
  - [ ] Return response: `{ id, status: "queued", estimated_seconds }`
- [ ] Create `GET /api/v1/jobs/{id}` endpoint
  - [ ] Query job by ID from database
  - [ ] Check for errors in job record
  - [ ] Build artifact URLs (presigned if private)
  - [ ] Return response: `{ id, status, progress, error?, artifacts: { musicxml?, midi? } }`
- [ ] Create `GET /api/v1/jobs/{id}/artifacts/{type}` endpoint
  - [ ] Validate type: `musicxml`, `midi`, `ascii`
  - [ ] Query artifact by job_id and type
  - [ ] Generate presigned S3 URL (TTL: 1 hour)
  - [ ] Return redirect or stream file

#### 1.2.3 API Schemas & Validation

- [ ] Define `JobCreateRequest` schema: file (FileUpload), options (optional dict)
- [ ] Define `JobOptions` schema: separate (bool), quantize ("1/8"|"1/16"|"1/32"), swing (bool), tempo_override (float)
- [ ] Define `JobResponse` schema: id, status, progress, error?, artifacts?, estimated_seconds
- [ ] Define `ArtifactResponse` schema: type, url, created_at
- [ ] Define `JobStatus` enum: queued, processing, completed, failed
- [ ] Add file type validation (content-type or magic bytes)

#### 1.2.4 Error Handling

- [ ] Handle `FileNotFoundError` for invalid job IDs → 404
- [ ] Handle `ValueError` for invalid options → 422
- [ ] Handle `FileTooLargeError` → 413
- [ ] Handle S3 upload failures → 500 with retry logic
- [ ] Handle Redis connection failures → 503
- [ ] Return structured error responses: `{ error: string, code: string, details? }`

### 1.3 Worker Pipeline — Audio Processing

#### 1.3.1 Worker Setup

- [ ] Create `worker/main.py` entry point
- [ ] Connect to Redis queue (RQ or Celery)
- [ ] Register job handler function for drum transcription
- [ ] Add worker logging and progress reporting
- [ ] Add worker health monitoring (heartbeat)
- [ ] Handle worker shutdown gracefully (finish current job)

#### 1.3.2 Source Separation

- [ ] Install HTDemucs (torchaudio or demucs package)
- [ ] Implement `separate_audio()` function with error handling
- [ ] Load HTDemucs model (CPU or GPU)
- [ ] Separate audio to stems: drums, bass, other, vocals
- [ ] Extract drums stem to temporary file
- [ ] Cache separated stems (store in S3 with TTL)
- [ ] Fallback: if separation fails, use original mix
- [ ] Log separation duration and quality metrics

#### 1.3.3 Feature Extraction

- [ ] Install librosa and madmom
- [ ] Implement tempo estimation:
  - [ ] Use madmom's DBNBeatTracker or Essentia's RhythmExtractor
  - [ ] Handle variable tempo (return tempo map or single BPM)
  - [ ] Store tempo in job options or separate field
- [ ] Implement onset detection:
  - [ ] Use librosa's onset detection or madmom's onset detection
  - [ ] Return time stamps and confidence scores
- [ ] Optional: Extract mel spectrograms for model input
- [ ] Log feature extraction duration

#### 1.3.4 Drum Transcription Model

- [ ] Research and select open-weights drum transcription model (e.g., OpenDrums, HybridNAS-Drums, or custom ONNX model)
- [ ] Download model weights to `worker/models/` directory
- [ ] Implement `load_drum_model()` function with ONNX Runtime
- [ ] Implement `transcribe_drums()` function:
  - [ ] Preprocess audio (normalize, resample if needed)
  - [ ] Generate spectrograms or mel features
  - [ ] Run inference on ONNX model
  - [ ] Parse output: instrument class + confidence + onset time
  - [ ] Filter low-confidence detections (<0.5 threshold)
- [ ] Map raw detections to drum classes: kick, snare, hh-closed, hh-open, hh-pedal, hi-tom, mid-tom, floor-tom, ride, ride-bell, crash1, crash2
- [ ] Log inference duration and accuracy metrics

#### 1.3.5 Post-Processing Pipeline

- [ ] Implement quantization:
  - [ ] Parse grid from options: "1/8", "1/16", "1/32"
  - [ ] Calculate grid size in samples (tempo-dependent)
  - [ ] Snap onset times to nearest grid position
  - [ ] Handle tuplets (3:2, 3:4) if needed
- [ ] Implement swing quantization:
  - [ ] Detect if swing is enabled in options
  - [ ] Apply swing pattern to 1/8 or 1/16 grid (shift off-beats by swing_ratio)
  - [ ] Use common swing ratios: 1.33 (16th-triplet), 1.5 (8th-triplet)
- [ ] Implement velocity smoothing:
  - [ ] Map raw velocities to MIDI range (0-127)
  - [ ] Apply median filter or moving average
  - [ ] Prevent unrealistic jumps
- [ ] Implement hi-hat state machine:
  - [ ] Track open/closed/pedal state
  - [ ] Auto-correct misclassifications based on temporal constraints
  - [ ] Enforce: open → can go to closed or pedal; closed → can go to open or pedal
- [ ] Implement flam/roll detection and deduplication:
  - [ ] Detect simultaneous hits (within 10ms window) of same instrument
  - [ ] Keep only one note or merge as grace note
  - [ ] Detect roll patterns (rapid succession) and mark with tremolo
- [ ] Implement GM mapping:
  - [ ] Map instrument → General MIDI pitch (channel 10)
  - [ ] Reference: kick(36), snare(38), hi-tom(48), mid-tom(47), floor-tom(41), hh-closed(42), hh-open(46), hh-pedal(44), ride(51), ride-bell(53), crash1(49), crash2(57)

#### 1.3.6 MIDI Writer

- [ ] Install `mido` or `music21` for MIDI writing
- [ ] Implement `write_midi()` function:
  - [ ] Create MIDI file with tempo map (from post-processing)
  - [ ] Create single track with channel 10
  - [ ] Add tempo change events
  - [ ] Convert quantized events to MIDI notes (pitch, velocity, start, duration)
  - [ ] Set note durations (default: 100ms or until next note)
  - [ ] Add rests where needed
  - [ ] Write to bytes buffer
- [ ] Upload MIDI file to S3 under `artifacts/{job_id}/output.mid`
- [ ] Create artifact record in database (type="midi", s3_key, s3_url)
- [ ] Test MIDI playback in DAW or MuseScore

#### 1.3.7 MusicXML Writer (Core Implementation)

- [ ] Install `music21` or `musicxml` for MusicXML generation
- [ ] Create drum percussion mapping constant:
  ```python
  DRUM_MAPPING = {
    "kick": { "line": 2, "notehead": "x", "voice": 1, "stem": "down" },
    "snare": { "line": 1, "notehead": "x", "voice": 1, "stem": "down" },
    # ... (complete for all instruments)
  }
  ```
- [ ] Implement `write_musicxml()` function:
  - [ ] Create score element with metadata
  - [ ] Set divisions (e.g., 480 ticks per quarter note)
  - [ ] Add tempo direction from tempo map
  - [ ] Create single 5-line unpitched staff
  - [ ] Create two voices (1: up-stem cymbals/hats, 2: down-stem drums/toms)
  - [ ] Map each drum event to staff position (display-step, display-octave)
  - [ ] Add articulations (open, closed, pedal) as notation
  - [ ] Add notations (tremolo for rolls, grace for flams)
  - [ ] Set notehead type (x, circled-x, diamond, etc.)
  - [ ] Add MIDI unpitched elements with GM pitch
  - [ ] Add beams and rests to complete measures
  - [ ] Serialize to XML string
- [ ] Test MusicXML import in MuseScore, Sibelius, Finale, Dorico
- [ ] Verify playback syncing with MIDI
- [ ] Upload MusicXML file to S3 under `artifacts/{job_id}/output.musicxml`
- [ ] Create artifact record in database (type="musicxml", s3_key, s3_url)

### 1.4 Frontend — Upload & Results Viewer

#### 1.4.1 Frontend Setup

- [ ] Initialize React + Vite project in `frontend/`
- [ ] Install UI framework (shadcn/ui or custom with Tailwind)
- [ ] Install routing (React Router)
- [ ] Install state management (Zustand or Context API)
- [ ] Install HTTP client (axios or fetch wrapper)
- [ ] Configure Tailwind CSS with shadcn theme
- [ ] Set up TypeScript with strict mode
- [ ] Add ESLint and Prettier
- [ ] Create component structure: `components/`, `pages/`, `hooks/`, `lib/`

#### 1.4.2 Upload UI

- [ ] Create `UploadPage` component:
  - [ ] Drag-and-drop zone with file input
  - [ ] Display accepted formats: MP3, WAV, FLAC
  - [ ] File size limit indicator (100MB)
  - [ ] Preview selected file (name, size, duration)
  - [ ] Options panel:
    - [ ] Checkbox: "Separate audio sources" (default: true)
    - [ ] Select: "Quantization" (1/8, 1/16, 1/32)
    - [ ] Checkbox: "Swing quantization" (default: false)
    - [ ] Input: "Tempo override (optional)"
  - [ ] Submit button (disabled if no file)
- [ ] Implement file upload logic:
  - [ ] Use FormData for multipart encoding
  - [ ] Show progress bar (native or custom)
  - [ ] Handle errors (file too large, invalid format)
  - [ ] Redirect to job status page on success
- [ ] Create API client function: `uploadAudio(file, options)`
- [ ] Add loading states and error messages

#### 1.4.3 Job Status Page

- [ ] Create `JobStatusPage` component:
  - [ ] Fetch job status on mount (polling every 2s until completed or failed)
  - [ ] Display progress indicator (percentage or spinner)
  - [ ] Show ETA if available
  - [ ] Display error message if failed
  - [ ] Auto-redirect to results page when completed
- [ ] Create API client function: `getJobStatus(jobId)`
- [ ] Add polling logic with `useInterval` hook or `setInterval`
- [ ] Handle "not found" errors

#### 1.4.4 Results Viewer Page

- [ ] Create `ResultsPage` component with tabs/views:
  - [ ] Tab 1: Sheet music viewer (SVG render)
  - [ ] Tab 2: MIDI playback controls
  - [ ] Tab 3: Export options
- [ ] Implement MusicXML SVG renderer:
  - [ ] Option A: Install `opensheetmusicdisplay` (OSMD) library
  - [ ] Option B: Build lightweight SVG renderer (parse MusicXML, draw staff, notes, stems, beams)
  - [ ] Display sheet music with zoom controls
  - [ ] Add measure navigation (jump to measure)
  - [ ] Add staff drawing: 5 lines, clef, time signature, key signature (none for percussion)
  - [ ] Add note rendering: position, notehead, stems, beams, articulations
- [ ] Implement MIDI playback:
  - [ ] Install `tone.js` or `WebMIDI` API
  - [ ] Add play/pause/stop controls
  - [ ] Load MIDI file from artifact URL
  - [ ] Parse MIDI events and play with Tone.js synthesis
  - [ ] Sync playback cursor with score scroll (visual indicator)
  - [ ] Add tempo adjustment slider
  - [ ] Add volume control
- [ ] Add export UI:
  - [ ] Download button for MusicXML
  - [ ] Download button for MIDI
  - [ ] Copy share link (optional)
- [ ] Create API client function: `getJobArtifacts(jobId)`

### 1.5 Integration & Testing

#### 1.5.1 End-to-End Pipeline

- [ ] Test full flow: upload → queue → process → download artifacts
- [ ] Verify job status updates in real-time
- [ ] Verify MIDI and MusicXML files are valid
- [ ] Check MusicXML import in multiple notation software
- [ ] Verify MIDI playback matches transcriptions

#### 1.5.2 Error Scenarios

- [ ] Test invalid file uploads (text, oversized, wrong format)
- [ ] Test failed source separation (use corrupted audio)
- [ ] Test S3 bucket unavailable
- [ ] Test Redis connection failure
- [ ] Test worker crash during processing (job should mark as failed)
- [ ] Verify error messages are user-friendly

#### 1.5.3 Performance & Monitoring

- [ ] Add basic metrics (Prometheus or custom):
  - [ ] Job count by status
  - [ ] Average processing time
  - [ ] Error rate
  - [ ] S3 upload/download latency
- [ ] Add structured logging with correlation IDs
- [ ] Set up log aggregation (optional: ELK, Loki)
- [ ] Profile worker (CPU, memory usage)
- [ ] Optimize slow components (model inference, MusicXML writing)

#### 1.5.4 Documentation

- [ ] Write `backend/README.md` with API documentation (FastAPI auto-docs link)
- [ ] Write `worker/README.md` with model and processing details
- [ ] Write `frontend/README.md` with setup and build instructions
- [ ] Update root `README.md` with quickstart guide
- [ ] Document environment variables
- [ ] Add inline code comments for complex logic

---

## Phase 2: Enhancements & Polish

### 2.1 ASCII Drum Tab Export

- [ ] Research ASCII tab format (drum tab standards)
- [ ] Implement `write_ascii_tab()` function in worker:
  - [ ] Parse quantized events
  - [ ] Render measures with ASCII art (staff lines: ---, HH: o, Snare: S, Kick: K, etc.)
  - [ ] Handle time signatures (4/4, 3/4, 6/8)
  - [ ] Add measure boundaries
  - [ ] Add repeat signs if needed
- [ ] Upload ASCII file to S3
- [ ] Add artifact type "ascii" to database
- [ ] Add ASCII preview in frontend results page
- [ ] Add download button for ASCII export

### 2.2 Improved Drum Detection

- [ ] Fine-tune model or use ensemble (multiple models, vote)
- [ ] Add technique detection:
  - [ ] Ride bell detection (separate from ride edge)
  - [ ] Choke (short decay on crash/cymbal)
  - [ ] Rim shot (loud snare with different timbre)
- [ ] Add confidence thresholds per instrument
- [ ] Add manual hinting UI (user selects dominant instruments)

### 2.3 Security & Production Readiness

- [ ] Add rate limiting (10 jobs/hour per IP, optional: per user)
- [ ] Add authentication (optional: JWT or OAuth)
- [ ] Add file validation (magic bytes, not just extension)
- [ ] Implement retention policy:
  - [ ] Background job to delete jobs older than 72 hours
  - [ ] Delete S3 artifacts when job deleted
  - [ ] Add cleanup job in worker or cron
- [ ] Add presigned URL rotation (expire after 1 hour)
- [ ] Add CORS origin whitelist (remove wildcard \*)
- [ ] Add HTTPS/TLS in production
- [ ] Add input sanitization (prevent path traversal in S3 keys)

### 2.4 User Experience Improvements

- [ ] Add progress bar with stage indicators (separating → transcribing → exporting)
- [ ] Add preview before processing (show waveform)
- [ ] Add "cancel job" button (if status is queued or processing)
- [ ] Add dark mode
- [ ] Add mobile responsive layout
- [ ] Improve error messages (actionable suggestions)
- [ ] Add keyboard shortcuts (play/pause: space, previous/next measure: arrows)

---

## Phase 3: Advanced Features

### 3.1 Guitar Pro Export

- [ ] Research GP format specification or use library (gpio or custom)
- [ ] Implement `write_gp()` function in worker
- [ ] Map MIDI events to GP drum staff layout
- [ ] Test import in Guitar Pro, TuxGuitar
- [ ] Add GP download in frontend

### 3.2 Editing Tools

- [ ] Add clickable note editing in SVG viewer
- [ ] Add drag-and-drop note repositioning
- [ ] Add instrument addition/removal
- [ ] Add velocity editing
- [ ] Add tempo editing with stretch
- [ ] Add undo/redo
- [ ] Persist edits to database (new artifact: edited.musicxml)

### 3.3 Project Persistence

- [ ] Create `projects` table: id, user_id, name, description, audio_url, created_at
- [ ] Link jobs to projects (add `project_id` to jobs table)
- [ ] Add project list page (show all user projects)
- [ ] Add project detail page (show job history, artifacts)
- [ ] Add project sharing (public links or invite codes)
- [ ] Add import existing projects (re-run transcription with new settings)

### 3.4 Advanced Notations

- [ ] Add dynamics markings (from velocity or model confidence)
- [ ] Add ghost notes (low-velocity snare)
- [ ] Add accents (high-velocity hits)
- [ ] Add buzz rolls notation
- [ ] Add drags and drag-triplets
- [ ] Add cross-stick notation for snare
- [ ] Add cymbal stacking (splash on crash)

### 3.5 Collaboration

- [ ] Add real-time collaboration (WebSockets) for editing
- [ ] Add comments on measures or notes
- [ ] Add version history (git-like for projects)
- [ ] Add export to cloud storage (Google Drive, Dropbox)

---

## Infrastructure & DevOps

### 4.1 Production Deployment

- [ ] Create Kubernetes manifests (optional):
  - [ ] Deployment for API (replicas: 3)
  - [ ] Deployment for Worker (replicas: 2, resource limits)
  - [ ] Service for API (LoadBalancer or Ingress)
  - [ ] StatefulSet for Postgres (with PVC)
  - [ ] StatefulSet for Redis (with PVC)
  - [ ] ConfigMap and Secrets management
- [ ] Add Helm charts for easier deployment
- [ ] Set up CI/CD pipeline (GitHub Actions or GitLab CI):
  - [ ] Run tests on PR
  - [ ] Build Docker images
  - [ ] Push to container registry
  - [ ] Deploy to staging
  - [ ] Deploy to production (manual approval)
- [ ] Add environment-specific configs (dev, staging, prod)

### 4.2 Observability

- [ ] Integrate distributed tracing (OpenTelemetry, Jaeger)
- [ ] Add custom metrics dashboards (Grafana)
- [ ] Set up alerting (Prometheus Alertmanager):
  - [ ] High error rate
  - [ ] Worker queue backlog
  - [ ] S3 storage quota
- [ ] Add APM (Application Performance Monitoring)
- [ ] Add uptime monitoring (external health checks)

### 4.3 Scaling

- [ ] Add horizontal scaling for API (auto-scaling based on CPU/requests)
- [ ] Add queue priority system (VIP users, small files first)
- [ ] Add GPU worker nodes (separate pool for GPU jobs)
- [ ] Add region-based deployments (multi-region S3 replication)
- [ ] Add CDN for static frontend assets
- [ ] Add caching layer (Redis for frequently accessed artifacts)

---

## Research & Optimization

### 5.1 Model Improvements

- [ ] Evaluate state-of-the-art drum transcription models (2024-2025 papers)
- [ ] Fine-tune model on custom dataset (if dataset available)
- [ ] A/B test different model architectures
- [ ] Add ensemble voting (run 2-3 models, aggregate results)
- [ ] Quantize models (INT8) for faster inference

### 5.2 Performance Optimization

- [ ] Profile CPU-bound operations (MusicXML serialization, quantization)
- [ ] Optimize with multiprocessing or async I/O
- [ ] Add result caching (same audio hash → return cached artifacts)
- [ ] Optimize S3 uploads (multipart, streaming)
- [ ] Reduce worker memory footprint (stream audio processing)

### 5.3 Quality Improvements

- [ ] Collect user feedback on transcription accuracy
- [ ] Build evaluation dataset (manual transcriptions)
- [ ] Add automatic quality scoring (confidence-weighted)
- [ ] Implement iterative refinement (post-edit detection, re-run)

---

## Notes

- **Priority order**: Phase 1 is must-have for MVP; Phase 2 adds polish; Phase 3 is nice-to-have.
- **Model selection**: Start with existing open-weights model; upgrade later if needed.
- **MusicXML mapping**: Critical for compatibility across notation software; test extensively.
- **Testing**: Each feature should have unit tests (backend), integration tests (worker), and E2E tests (frontend).
- **Documentation**: Update README files as features are added.
- **Feedback loop**: Deploy early, iterate based on user feedback.
