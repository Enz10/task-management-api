import uuid
from typing import List, Optional
import math

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.crud import crud_task, crud_team
from app.models import user as models_user
from app.schemas.task import Task, TaskCreate, TaskUpdate, TaskPage
from app.utils.pagination import create_page

router = APIRouter()


@router.post("/", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
def create_task(
    *,
    db: Session = Depends(deps.get_db),
    task_in: schemas.TaskCreate,
    current_user: models_user.User = Depends(deps.get_current_active_user),
) -> schemas.Task:
    """
    Create new task for a specific team. User must be a member of the team.
    """
    # Check if the target team exists
    team = crud_team.get_team(db=db, team_id=task_in.team_id)
    if not team:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with id {task_in.team_id} not found.",
        )
    # Check if the current user is a member of the target team
    is_member = crud_team.is_user_member_of_team(db=db, team_id=task_in.team_id, user_id=current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create tasks for this team",
        )
    # Use the updated CRUD function, passing creator_id
    task = crud_task.create_task(db=db, task_in=task_in, creator_id=current_user.id)
    return task


@router.get("/", response_model=TaskPage)
def read_tasks(
    *,
    db: Session = Depends(deps.get_db),
    team_id: uuid.UUID = Query(..., description="The ID of the team whose tasks to retrieve"),
    skip: int = Query(0, ge=0, description="Number of items to skip (0-based index)"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of items per page"),
    current_user: models_user.User = Depends(deps.get_current_active_user),
    # Optional Filters
    assignee_id: Optional[uuid.UUID] = Query(None, description="Filter tasks by assignee user ID"),
    completed: Optional[bool] = Query(None, description="Filter tasks by completion status (true=completed, false=pending)")
) -> TaskPage:
    """Retrieve tasks for a specific team with pagination and optional filters. User must be a member of the team."""
    # Check if the team exists
    team = crud_team.get_team(db=db, team_id=team_id)
    if not team:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with id {team_id} not found.",
        )
    # Check if the current user is a member of the requested team
    is_member = crud_team.is_user_member_of_team(db=db, team_id=team_id, user_id=current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view tasks for this team",
        )

    # Call CRUD function to get items and total count, passing filters
    tasks_list, total_items = crud_task.get_tasks_by_team(
        db=db,
        team_id=team_id,
        skip=skip,
        limit=limit,
        assignee_id=assignee_id, # Pass filter
        completed=completed # Pass filter
    )

    return create_page(items=tasks_list, total_items=total_items, skip=skip, limit=limit)


@router.get("/{task_id}", response_model=schemas.Task)
def read_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: uuid.UUID,
    current_user: models_user.User = Depends(deps.get_current_active_user),
) -> schemas.Task:
    """
    Get task by ID. User must be a member of the task's team.
    """
    task = crud_task.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    # Check if the current user is a member of the task's team
    is_member = crud_team.is_user_member_of_team(db=db, team_id=task.team_id, user_id=current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this task",
        )
    return task


@router.put("/{task_id}", response_model=schemas.Task)
def update_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: uuid.UUID,
    task_in: schemas.TaskUpdate,
    current_user: models_user.User = Depends(deps.get_current_active_user),
) -> schemas.Task:
    """
    Update a task. User must be a member of the task's team.
    """
    task = crud_task.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    # Check if the current user is a member of the task's team
    is_member = crud_team.is_user_member_of_team(db=db, team_id=task.team_id, user_id=current_user.id)
    if not is_member:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this task",
        )
    # Prevent changing team_id via this endpoint - handled by create/move operations if needed
    if hasattr(task_in, 'team_id') and task_in.team_id is not None:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change team_id via update. Create a new task or implement a move feature.",
        )
    updated_task = crud_task.update_task(db=db, db_task=task, task_in=task_in)
    return updated_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: uuid.UUID,
    current_user: models_user.User = Depends(deps.get_current_active_user),
) -> None:
    """
    Soft delete a task. User must be a member of the task's team.
    """
    task = crud_task.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    # Check if the current user is a member of the task's team
    is_member = crud_team.is_user_member_of_team(db=db, team_id=task.team_id, user_id=current_user.id)
    if not is_member:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this task",
        )
    crud_task.soft_delete_task(db=db, db_task=task)
    return None
