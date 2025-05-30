import uuid
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, select
from fastapi import HTTPException, status

from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.crud import crud_team


def create_task(db: Session, *, task_in: TaskCreate, creator_id: uuid.UUID) -> Task:
    """Creates a new task, validating assignee if provided."""
    # Validate assignee if provided
    if task_in.assignee_id:
        # Check if assignee exists
        assignee_exists = db.query(User.id).filter(User.id == task_in.assignee_id).first() is not None
        if not assignee_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignee user with id {task_in.assignee_id} not found."
            )
        # Check if assignee is member of the task's team
        is_member = crud_team.is_user_member_of_team(
            db=db, team_id=task_in.team_id, user_id=task_in.assignee_id
        )
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Assignee user {task_in.assignee_id} is not a member of team {task_in.team_id}"
            )

    # Convert Pydantic schema to dict, excluding unset values if needed
    # creator_id is handled separately
    task_data = task_in.model_dump(exclude_unset=True) # Use exclude_unset for flexibility
    db_task = Task(**task_data, creator_id=creator_id, is_deleted=False)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_task(db: Session, task_id: uuid.UUID, *, include_deleted: bool = False) -> Task | None:
    """Gets a specific task by ID. Optionally includes soft-deleted tasks."""
    query = db.query(Task).filter(Task.id == task_id)
    if not include_deleted:
        query = query.filter(Task.is_deleted == False)
    return query.first()


def get_tasks(db: Session) -> list[Task]:
    """Retrieve all tasks (use with caution, consider pagination elsewhere)."""
    return db.query(Task).all()


def get_tasks_by_team(
    db: Session,
    *,
    team_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    assignee_id: Optional[uuid.UUID] = None,
    completed: Optional[bool] = None,
) -> Tuple[List[Task], int]:
    """
    Gets a list of tasks for a specific team with pagination and total count,
    excluding soft-deleted tasks and applying optional filters.
    Returns a tuple: (list_of_tasks, total_count)
    """
    query = db.query(Task).filter(Task.is_deleted == False)
    query = query.options(joinedload(Task.assignee)) # Eager load assignee
    query = query.filter(Task.team_id == team_id)

    # Apply optional filters
    if assignee_id is not None:
        query = query.filter(Task.assignee_id == assignee_id)
    if completed is not None:
        # Filter based on the boolean completed field
        query = query.filter(Task.completed == completed)

    # Get the total count *after* applying filters
    total_count = query.count()

    # Apply pagination and get items
    items = query.offset(skip).limit(limit).all()

    return items, total_count


def update_task(db: Session, *, db_task: Task, task_in: TaskUpdate) -> Task:
    """Updates an existing task, validating assignee if changed."""
    update_data = task_in.model_dump(exclude_unset=True)

    # Validate assignee if it's being changed
    if "assignee_id" in update_data:
        new_assignee_id = update_data["assignee_id"]
        if new_assignee_id is not None:
            # Check if assignee exists
            assignee_exists = db.query(User.id).filter(User.id == new_assignee_id).first() is not None
            if not assignee_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assignee user with id {new_assignee_id} not found."
                )
            # Check if assignee is member of the task's *current* team
            is_member = crud_team.is_user_member_of_team(
                db=db, team_id=db_task.team_id, user_id=new_assignee_id
            )
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Assignee user {new_assignee_id} is not a member of team {db_task.team_id}"
                )
        # If new_assignee_id is None, it's valid (unassigning)

    for field, value in update_data.items():
        if field not in ["team_id", "creator_id"]:
            setattr(db_task, field, value)

    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def soft_delete_task(db: Session, *, db_task: Task) -> Task:
    """Marks a task as deleted (soft delete)."""
    if not db_task.is_deleted:
        db_task.is_deleted = True
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
    return db_task
