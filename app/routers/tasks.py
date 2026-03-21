from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import TaskCreate, TaskUpdate, TaskResponse
from app import crud

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db=db, task=task)


@router.get("/", response_model=list[TaskResponse])
def list_tasks(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return crud.get_tasks(db=db, skip=skip, limit=limit, status=status, priority=priority)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_task(db=db, task_id=task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    updated = crud.update_task(db=db, task_id=task_id, task=task)
    if updated is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_task(db=db, task_id=task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return None
