from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import tasks

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TaskFlow API",
    description="Production-grade Task Management API with telemetry and metrics",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)


@app.get("/", tags=["root"])
def root():
    return {"message": "Welcome to TaskFlow API", "docs": "/docs"}
