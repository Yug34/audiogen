# AI Drum Tab Generator

An AI-powered application that automatically generates drum tablature (sheet music) from audio files. This monorepo contains the full stack: FastAPI backend, React frontend, async worker for audio processing, and infrastructure configurations.

## Architecture Overview

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Frontend  │────▶│   Backend   │─────▶│   Worker    │
│  (React)    │      │  (FastAPI)  │      │ (ML Tasks)  │
└─────────────┘      └─────────────┘      └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  Postgres   │     │    Redis    │
                    │  (Database) │     │   (Queue)   │
                    └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   MinIO     │
                    │  (S3 Store) │
                    └─────────────┘
```

### Components

- **Backend** (`backend/`): FastAPI application handling REST API requests, file uploads, and job management
- **Frontend** (`frontend/`): React + Vite + Tailwind UI for uploading audio and viewing results
- **Worker** (`worker/`): Async task processor using RQ/Celery for audio separation, drum transcription, and format generation (MIDI, MusicXML)
- **Infra** (`infra/`): Kubernetes manifests and deployment configurations (optional, for production)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Docker Compose Setup

The easiest way to get started is using Docker Compose:

1. **Clone the repository** (if not already done):

   ```bash
   git clone <repository-url>
   cd gen
   ```

2. **Set up environment variables**:
   Create a `.env` file in the root directory (optional, defaults are provided):

   ```env
   # Database
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=gen

   # Redis
   REDIS_URL=redis://redis:6379/0

   # API
   PORT=4000
   CORS_ORIGIN=*
   ENV=development
   DATABASE_URL=postgresql+psycopg2://postgres:postgres@postgres:5432/gen

   # MinIO (S3)
   MINIO_ROOT_USER=minioadmin
   MINIO_ROOT_PASSWORD=minioadmin
   S3_ENDPOINT=http://minio:9000
   S3_ACCESS_KEY=minioadmin
   S3_SECRET_KEY=minioadmin
   S3_BUCKET=gen-artifacts
   ```

3. **Start all services**:

   ```bash
   docker-compose up -d
   ```

4. **Initialize MinIO buckets** (first time only):

   Option A - Using MinIO Console (Recommended):

   - Access MinIO Console at http://localhost:9001
   - Login with `minioadmin` / `minioadmin`
   - Create bucket: `gen-artifacts`
   - Set bucket policy to "public" if needed

   Option B - Using MinIO Client (if `mc` is installed locally):

   ```bash
   mc alias set local http://localhost:9000 minioadmin minioadmin
   mc mb local/gen-artifacts
   mc anonymous set public local/gen-artifacts
   ```

5. **Verify services are running**:

   - API: http://localhost:4000
   - API Health: http://localhost:4000/health
   - API Docs: http://localhost:4000/docs
   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
   - Postgres: localhost:5432
   - Redis: localhost:6379

6. **Run database migrations** (if applicable):

   ```bash
   docker-compose exec api alembic upgrade head
   ```

7. **Start frontend** (in a separate terminal, see Frontend section below)

### Development Setup (Local)

#### Backend

1. Navigate to `backend/`:

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

4. Copy environment file:

   ```bash
   cp env.example .env
   ```

5. Update `.env` with your local settings:

   ```env
   REDIS_URL=redis://localhost:6379/0
   DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/gen
   ```

6. Run migrations (if using Alembic):

   ```bash
   alembic upgrade head
   ```

7. Start development server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
   ```

For detailed backend documentation, see [backend/README.md](backend/README.md).

#### Frontend

1. Navigate to `frontend/`:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   # or
   bun install
   ```

3. Create `.env` file (optional):

   ```env
   VITE_API_URL=http://localhost:4000
   ```

4. Start development server:
   ```bash
   npm run dev
   # or
   bun run dev
   ```

The frontend will be available at http://localhost:5173 (or Vite's default port).

For detailed frontend documentation, see [frontend/README.md](frontend/README.md).

#### Worker

1. Ensure Redis is running (via Docker Compose or locally).

2. Navigate to `worker/`:

   ```bash
   cd worker
   ```

3. Create virtual environment (same as backend):

   ```bash
   # Use the same venv as backend or create a new one
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:

   ```bash
   pip install -r ../backend/requirements.txt  # Worker reuses backend deps
   # Additional ML dependencies may be needed
   pip install librosa torch demucs mido music21
   ```

5. Copy environment file:

   ```bash
   cp env.example .env
   ```

6. Update `.env`:

   ```env
   REDIS_URL=redis://localhost:6379/0
   RQ_QUEUES=audio,default
   RQ_JOB_TIMEOUT=3600
   ```

7. Start worker:
   ```bash
   python -m worker.worker
   ```

### Infrastructure

The `infra/` directory contains Kubernetes manifests for production deployments.

- **k8s/**: Minimal Kubernetes manifests for API, Worker, Postgres, Redis, and MinIO
- Deploy using: `kubectl apply -f infra/k8s/`

For detailed infrastructure documentation, see [infra/README.md](infra/README.md).

## Service Ports

| Service   | Port | Description         |
| --------- | ---- | ------------------- |
| API       | 4000 | FastAPI backend     |
| Frontend  | 5173 | Vite dev server     |
| Postgres  | 5432 | PostgreSQL database |
| Redis     | 6379 | Redis queue         |
| MinIO API | 9000 | S3-compatible API   |
| MinIO UI  | 9001 | MinIO web console   |

## Project Structure

```
gen/
├── backend/              # FastAPI application
│   ├── app/              # Application code
│   ├── Dockerfile        # Backend container
│   ├── requirements.txt  # Python dependencies
│   └── README.md         # Backend docs
├── frontend/             # React + Vite application
│   ├── src/              # React components
│   ├── package.json      # Node dependencies
│   └── README.md         # Frontend docs
├── worker/               # Async task processor
│   ├── worker.py         # Worker entry point
│   ├── tasks.py          # Task definitions
│   ├── Dockerfile        # Worker container
│   └── README.md         # Worker docs
├── infra/                # Infrastructure configs
│   ├── k8s/              # Kubernetes manifests
│   └── README.md         # Infra docs
├── docker-compose.yml    # Local development setup
└── README.md             # This file
```

## API Endpoints

- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger)
- `POST /api/v1/jobs` - Upload audio and create transcription job
- `GET /api/v1/jobs/{id}` - Get job status and artifacts
- `GET /api/v1/jobs/{id}/artifacts/{type}` - Download artifact (midi, musicxml, ascii)

## Development Workflow

1. **Start infrastructure services** (Postgres, Redis, MinIO):

   ```bash
   docker-compose up -d postgres redis minio
   ```

2. **Run backend locally** (with hot reload):

   ```bash
   cd backend && uvicorn app.main:app --reload
   ```

3. **Run worker locally**:

   ```bash
   cd worker && python -m worker.worker
   ```

4. **Run frontend locally**:
   ```bash
   cd frontend && npm run dev
   ```

## Environment Variables

See `.env.example` files in each service directory:

- `backend/env.example` - Backend configuration
- `worker/env.example` - Worker configuration

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Integration Tests

```bash
# Run full stack tests
docker-compose up -d
pytest tests/integration/
```

## Troubleshooting

### Services not connecting

- Ensure all services are running: `docker-compose ps`
- Check service logs: `docker-compose logs <service-name>`
- Verify environment variables are set correctly

### Worker not processing jobs

- Check Redis connection: `docker-compose exec redis redis-cli ping`
- Verify worker is listening to correct queue: Check `RQ_QUEUES` in worker `.env`
- Check worker logs: `docker-compose logs worker`

### MinIO access issues

- Access console at http://localhost:9001
- Default credentials: `minioadmin` / `minioadmin`
- Ensure buckets are created (see Quick Start step 4)

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests if applicable
4. Submit a pull request

## License

[Add your license here]

## Additional Resources

- [Backend Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)
- [Infrastructure Documentation](infra/README.md)
- [Task Breakdown](tasks.md)
