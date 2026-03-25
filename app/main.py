"""FastAPI application entry point for TaskFlow API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import tasks
from app.telemetry import TelemetryMiddleware, get_metrics

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TaskFlow API",
    description="Production-grade Task Management API with telemetry and metrics",
    version="1.0.0",
)

app.add_middleware(TelemetryMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)


@app.get("/", tags=["root"])
def root() -> dict:
    """Return a welcome message with a link to the API documentation."""
    return {"message": "Welcome to TaskFlow API", "docs": "/docs"}


@app.get("/metrics", tags=["telemetry"])
def metrics() -> dict:
    """Return collected telemetry metrics for all endpoints."""
    return get_metrics()
