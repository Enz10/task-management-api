import uuid
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.crud import crud_team, crud_user
from app.models import user as models_user
from app.models import team as models_team

router = APIRouter()

@router.post("/", response_model=schemas.Team, status_code=status.HTTP_201_CREATED)
def create_team(
    *,
    db: Session = Depends(deps.get_db),
    team_in: schemas.TeamCreate,
    current_user: models_user.User = Depends(deps.get_current_active_user)
) -> models_team.Team:
    """
    Create new team. The user creating the team becomes the first member.
    """
    # Check if team name already exists
    existing_team = crud_team.get_team_by_name(db=db, name=team_in.name)
    if existing_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A team with this name already exists.",
        )
    team = crud_team.create_team_with_creator(db=db, team_in=team_in, creator=current_user)
    return team


@router.get("/", response_model=List[schemas.Team])
def read_teams(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models_user.User = Depends(deps.get_current_active_user)
) -> List[models_team.Team]:
    """
    Retrieve teams the current user is a member of.
    """
    teams = crud_team.get_user_teams(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return teams


@router.get("/{team_id}", response_model=schemas.Team)
def read_team(
    *,
    db: Session = Depends(deps.get_db),
    team_id: uuid.UUID,
    current_user: models_user.User = Depends(deps.get_current_active_user)
) -> models_team.Team:
    """
    Get team by ID. User must be a member of the team.
    """
    team = crud_team.get_team(db=db, team_id=team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    # Check if current user is a member
    is_member = crud_team.is_user_member_of_team(db=db, team_id=team_id, user_id=current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this team",
        )
    return team


@router.put("/{team_id}", response_model=schemas.Team)
def update_team(
    *,
    db: Session = Depends(deps.get_db),
    team_id: uuid.UUID,
    team_in: schemas.TeamUpdate,
    current_user: models_user.User = Depends(deps.get_current_active_user)
) -> models_team.Team:
    """
    Update a team. User must be a member. (Future: Add admin roles).
    """
    team = crud_team.get_team(db=db, team_id=team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    # Check membership
    is_member = crud_team.is_user_member_of_team(db=db, team_id=team_id, user_id=current_user.id)
    if not is_member:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this team",
        )
    # Check if new name conflicts
    if team_in.name:
        existing_team = crud_team.get_team_by_name(db=db, name=team_in.name)
        if existing_team and existing_team.id != team_id:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another team with this name already exists.",
            )

    team = crud_team.update_team(db=db, db_team=team, team_in=team_in)
    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    *,
    db: Session = Depends(deps.get_db),
    team_id: uuid.UUID,
    current_user: models_user.User = Depends(deps.get_current_active_user)
) -> None:
    """
    Delete a team. User must be a member. (Future: Add admin roles).
    Tasks associated with the team will be cascade deleted by the DB relationship.
    """
    team = crud_team.get_team(db=db, team_id=team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    # Check membership
    is_member = crud_team.is_user_member_of_team(db=db, team_id=team_id, user_id=current_user.id)
    if not is_member:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this team",
        )
    crud_team.delete_team(db=db, db_team=team)
    return None


# --- Team Member Management ---

@router.post("/{team_id}/members/{user_id}", response_model=schemas.Team)
def add_team_member(
    *,
    db: Session = Depends(deps.get_db),
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: models_user.User = Depends(deps.get_current_active_user)
) -> models_team.Team:
    """
    Add a user to a team. Current user must be a member of the team.
    """
    team = crud_team.get_team(db=db, team_id=team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    # Check if current user is a member (authorization to add others)
    is_current_user_member = crud_team.is_user_member_of_team(db=db, team_id=team_id, user_id=current_user.id)
    if not is_current_user_member:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add members to this team",
        )
    # Get the user to add
    user_to_add = crud_user.get_user(db=db, user_id=user_id)
    if not user_to_add:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User to add not found")

    updated_team = crud_team.add_user_to_team(db=db, db_team=team, db_user=user_to_add)
    return updated_team


@router.delete("/{team_id}/members/{user_id}", response_model=schemas.Team)
def remove_team_member(
    *,
    db: Session = Depends(deps.get_db),
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: models_user.User = Depends(deps.get_current_active_user)
) -> models_team.Team:
    """
    Remove a user from a team. Current user must be a member.
    Users can remove themselves. (Future: Add admin logic for removing others).
    """
    team = crud_team.get_team(db=db, team_id=team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Check if current user is a member (authorization)
    is_current_user_member = crud_team.is_user_member_of_team(db=db, team_id=team_id, user_id=current_user.id)
    if not is_current_user_member:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to remove members from this team",
        )

    # Check if user to remove exists
    user_to_remove = crud_user.get_user(db=db, user_id=user_id)
    if not user_to_remove:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User to remove not found")

    # Prevent removing the last member? Or should deleting the team handle this?
    # For now, allow removal. Deleting the team requires a member.

    updated_team = crud_team.remove_user_from_team(db=db, db_team=team, db_user=user_to_remove)
    return updated_team
