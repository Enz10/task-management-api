import uuid
from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.post("/", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
def create_task(
    *,
    db: Session = Depends(deps.get_db),
    task_in: schemas.TaskCreate,
    # current_user: models.User = Depends(deps.get_current_active_user) # TODO: Add authentication
) -> Any:
    """
    Create new task. TEMPORARY: Requires owner_id in request body.
    """
    # TEMPORARY: Get owner from the request body and verify they exist
    owner = crud.crud_user.get_user(db=db, user_id=task_in.owner_id)
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Owner with id {task_in.owner_id} not found.",
        )

    # TODO: Replace task_in.owner_id with current_user.id when auth is implemented
    task = crud.crud_task.create_task_with_owner(db=db, task_in=task_in, owner_id=task_in.owner_id)
    return task

@router.get("/", response_model=List[schemas.Task])
def read_tasks(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    owner_id: uuid.UUID = None # TEMPORARY: Filter by owner_id query param
    # current_user: models.User = Depends(deps.get_current_active_user), # TODO: Add authentication
) -> Any:
    """
    Retrieve tasks. TEMPORARY: Filters by owner_id query parameter.
    """
    # TODO: Remove owner_id query param and filter by current_user.id
    if owner_id:
        owner = crud.crud_user.get_user(db=db, user_id=owner_id)
        if not owner:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Owner with id {owner_id} not found.",
            )
        tasks = crud.crud_task.get_tasks_by_owner(db=db, owner_id=owner_id, skip=skip, limit=limit)
    else:
        # Decide what to do if no owner_id is provided (e.g., error, return all tasks - not recommended without auth)
        # For now, let's require owner_id for this temporary setup
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="owner_id query parameter is required (temporary setup).",
        )
        # tasks = crud.crud_task.get_multi(db, skip=skip, limit=limit) # Example if get_multi existed
    return tasks


@router.get("/{task_id}", response_model=schemas.Task)
def read_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: uuid.UUID,
    # current_user: models.User = Depends(deps.get_current_active_user), # TODO: Add authentication
) -> Any:
    """
    Get task by ID.
    """
    task = crud.crud_task.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    # TODO: Add authorization check: if task.owner_id != current_user.id: raise HTTPException(...)
    return task

@router.put("/{task_id}", response_model=schemas.Task)
def update_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: uuid.UUID,
    task_in: schemas.TaskUpdate,
    # current_user: models.User = Depends(deps.get_current_active_user), # TODO: Add authentication
) -> Any:
    """
    Update a task.
    """
    db_task = crud.crud_task.get_task(db=db, task_id=task_id)
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    # TODO: Add authorization check: if db_task.owner_id != current_user.id: raise HTTPException(...)
    task = crud.crud_task.update_task(db=db, db_task=db_task, task_in=task_in)
    return task

@router.delete("/{task_id}", response_model=schemas.Task)
def delete_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: uuid.UUID,
    # current_user: models.User = Depends(deps.get_current_active_user), # TODO: Add authentication
) -> Any:
    """
    Soft delete a task.
    """
    db_task = crud.crud_task.get_task(db=db, task_id=task_id)
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    # TODO: Add authorization check: if db_task.owner_id != current_user.id: raise HTTPException(...)
    task = crud.crud_task.soft_delete_task(db=db, db_task=db_task)
    return task # Returns the task marked as deleted
