"""Pydantic schemas for request validation and response serialization."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Schema for creating a new task. Title is required; other fields have defaults."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default="", max_length=1000)
    status: Optional[str] = Field(default="pending", pattern="^(pending|in-progress|completed)$")
    priority: Optional[str] = Field(default="medium", pattern="^(low|medium|high)$")


class TaskUpdate(BaseModel):
    """Schema for partial task updates. All fields are optional."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[str] = Field(default=None, pattern="^(pending|in-progress|completed)$")
    priority: Optional[str] = Field(default=None, pattern="^(low|medium|high)$")


class TaskResponse(BaseModel):
    """Schema for task responses returned by the API."""

    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
