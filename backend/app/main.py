from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

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


@app.get("/health")
def health():
    return {"ok": True, "service": "gen-backend", "env": os.getenv("ENV", "development")}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI"}


