"""CRUD service layer implementing core business logic for task operations."""

from sqlalchemy.orm import Session

from app.models import Task
from app.schemas import TaskCreate, TaskUpdate


def create_task(db: Session, task: TaskCreate) -> Task:
    """Create a new task and persist it to the database."""
    db_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_task(db: Session, task_id: int) -> Task | None:
    """Retrieve a single task by primary key, or None if not found."""
    return db.query(Task).filter(Task.id == task_id).first()


def get_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    priority: str | None = None,
) -> list[Task]:
    """Retrieve a paginated and optionally filtered list of tasks."""
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    return query.offset(skip).limit(limit).all()


def update_task(db: Session, task_id: int, task: TaskUpdate) -> Task | None:
    """Partially update an existing task. Returns None if the task does not exist."""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        return None
    update_data = task.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int) -> bool:
    """Delete a task by primary key. Returns True if deleted, False if not found."""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        return False
    db.delete(db_task)
    db.commit()
    return True
