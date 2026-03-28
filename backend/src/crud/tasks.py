# src/crud/tasks.py
from sqlalchemy.orm import Session
from typing import List, Optional
from src.models.tasks import Task
from src.schemas.tasks import TaskCreate, TaskUpdate

def create_task(db: Session, data: TaskCreate) -> Task:
    task = Task(title=data.title)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def get_task(db: Session, task_id: int) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id).first()

def get_tasks(db: Session) -> List[Task]:
    return db.query(Task).all()

def update_task(db: Session, task_id: int, data: TaskUpdate) -> Optional[Task]:
    task = get_task(db, task_id)
    if not task:
        return None
    if data.title is not None:
        task.title = data.title
    if data.is_done is not None:
        task.is_done = data.is_done
    db.commit()
    db.refresh(task)
    return task

def delete_task(db: Session, task_id: int) -> bool:
    task = get_task(db, task_id)
    if not task:
        return False
    db.delete(task)
    db.commit()
    return True
