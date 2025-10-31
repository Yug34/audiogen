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

4. Run dev server

- `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-4000} --reload`

## Endpoints

- `GET /health` → service status
- `GET /api/hello` → sample data

## CORS

- Set `CORS_ORIGIN` to your frontend URL(s), e.g. `http://localhost:3000`.
- Multiple origins can be comma-separated.
