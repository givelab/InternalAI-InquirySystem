# src/routers/tasks.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.dependencies.database import get_db
from src.crud.tasks import (
    create_task, get_task, get_tasks, update_task, delete_task
)
from src.schemas.tasks import (
    TaskCreate, TaskUpdate, TaskResponse
)

router = APIRouter()

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def post_task(data: TaskCreate, db: Session = Depends(get_db)):
    task = create_task(db, data)
    return task

@router.get("", response_model=list[TaskResponse])
def read_tasks(db: Session = Depends(get_db)):
    tasks = get_tasks(db)
    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
def read_task(task_id: int, db: Session = Depends(get_db)):
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}", response_model=TaskResponse)
def patch_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    updated = update_task(db, task_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task(task_id: int, db: Session = Depends(get_db)):
    ok = delete_task(db, task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return
