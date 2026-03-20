from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default="", max_length=1000)
    status: Optional[str] = Field(default="pending", pattern="^(pending|in-progress|completed)$")
    priority: Optional[str] = Field(default="medium", pattern="^(low|medium|high)$")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[str] = Field(default=None, pattern="^(pending|in-progress|completed)$")
    priority: Optional[str] = Field(default=None, pattern="^(low|medium|high)$")


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
