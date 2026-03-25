"""SQLAlchemy ORM models for TaskFlow API entities."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base


class Task(Base):
    """Represents a task in the task management system."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True, default="")
    status = Column(String(20), nullable=False, default="pending")
    priority = Column(String(10), nullable=False, default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
