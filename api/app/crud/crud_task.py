import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate

def create_task_with_owner(db: Session, *, task_in: TaskCreate, owner_id: uuid.UUID) -> Task:
    """Creates a new task associated with an owner."""
    # Exclude 'owner_id' when dumping, as we set it explicitly
    task_data = task_in.model_dump(exclude={'owner_id'})
    db_task = Task(
        **task_data,          # Unpack TaskCreate data (without owner_id)
        owner_id=owner_id,      # Set owner_id explicitly from the function arg
        is_deleted=False # Ensure new tasks are not deleted
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_task(db: Session, *, task_id: uuid.UUID) -> Optional[Task]:
    """Gets a specific task by ID, excluding soft-deleted tasks."""
    return db.query(Task).filter(Task.id == task_id, Task.is_deleted == False).first()

def get_tasks_by_owner(db: Session, *, owner_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Task]:
    """Gets a list of tasks for a specific owner, excluding soft-deleted tasks."""
    return db.query(Task)\
        .filter(Task.owner_id == owner_id, Task.is_deleted == False)\
        .order_by(Task.due_date)\
        .offset(skip)\
        .limit(limit)\
        .all()

def update_task(db: Session, *, db_task: Task, task_in: TaskUpdate) -> Task:
    """Updates an existing task."""
    task_data = task_in.model_dump(exclude_unset=True) # Get only fields that were set
    for field, value in task_data.items():
        setattr(db_task, field, value)

    db.add(db_task) # Add the updated object to the session
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

# You might also want a function to permanently delete if needed
# def delete_task(db: Session, *, task_id: uuid.UUID) -> Optional[Task]:
#     """Permanently deletes a task."""
#     db_task = db.query(Task).filter(Task.id == task_id).first()
#     if db_task:
#         db.delete(db_task)
#         db.commit()
#     return db_task
