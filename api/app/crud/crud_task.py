import uuid
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate


def create_task(db: Session, *, task_in: TaskCreate, creator_id: uuid.UUID) -> Task:
    """Creates a new task associated with a creator and team."""
    task_data = task_in.model_dump()
    db_task = Task(
        **task_data,
        creator_id=creator_id,
        is_deleted=False
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_task(db: Session, task_id: uuid.UUID) -> Task | None:
    """Gets a specific task by ID, excluding soft-deleted tasks."""
    return db.query(Task).filter(Task.id == task_id, Task.is_deleted == False).first()

def get_tasks(db: Session) -> list[Task]:
    """Retrieve all tasks (use with caution, consider pagination elsewhere)."""
    return db.query(Task).all()

def get_tasks_by_team(db: Session, *, team_id: uuid.UUID, skip: int = 0, limit: int = 100) -> Tuple[List[Task], int]:
    """
    Gets a list of tasks for a specific team with pagination and total count,
    excluding soft-deleted tasks.
    Returns a tuple: (list_of_tasks, total_count)
    """
    base_query = db.query(Task).filter(Task.team_id == team_id, Task.is_deleted == False)

    # Get total count before applying limit/offset
    total_count = base_query.with_entities(func.count(Task.id)).scalar() or 0

    # Get the items for the current page
    items = base_query.offset(skip).limit(limit).all()

    return items, total_count

def update_task(db: Session, *, db_task: Task, task_in: TaskUpdate) -> Task:
    """Updates an existing task."""
    task_data = task_in.model_dump(exclude_unset=True)
    for field, value in task_data.items():
        if field not in ["team_id", "creator_id"]:
            setattr(db_task, field, value)

    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def soft_delete_task(db: Session, *, db_task: Task) -> Task:
    """Marks a task as deleted (soft delete)."""
    db_task.is_deleted = True
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task
