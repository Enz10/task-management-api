import uuid
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.team import Team
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate


def get_team(db: Session, *, team_id: uuid.UUID, include_deleted: bool = False) -> Optional[Team]:
    """Gets a specific team by ID. Optionally includes soft-deleted teams."""
    query = db.query(Team).filter(Team.id == team_id)
    if not include_deleted:
        query = query.filter(Team.is_deleted == False)
    return query.first()

def get_team_by_name(db: Session, *, name: str) -> Optional[Team]:
    """Gets a team by its name."""
    return db.query(Team).filter(Team.name == name).first()

def get_teams(db: Session, skip: int = 0, limit: int = 100) -> List[Team]:
    """Gets a list of all teams."""
    return db.query(Team).offset(skip).limit(limit).all()

def get_user_teams(db: Session, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Team]:
    """Gets a list of teams a specific user is a member of."""
    return db.query(Team).join(Team.members).filter(User.id == user_id).offset(skip).limit(limit).all()

def create_team_with_creator(db: Session, *, team_in: TeamCreate, creator: User) -> Team:
    """Creates a new team and adds the creator as the first member."""
    db_team = Team(**team_in.model_dump())
    db_team.members.append(creator) # Add the creator to the members list
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

def update_team(db: Session, *, db_team: Team, team_in: TeamUpdate) -> Team:
    """Updates an existing team."""
    team_data = team_in.model_dump(exclude_unset=True)
    for field, value in team_data.items():
        setattr(db_team, field, value)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

def delete_team(db: Session, *, db_team: Team) -> Team:
    """Deletes a team (soft delete)."""
    if not db_team.is_deleted:
        db_team.is_deleted = True
        # Optionally clear members? Or rely on filtering?
        # For now, just mark as deleted. Associated tasks will remain.
        db.add(db_team)
        db.commit()
        db.refresh(db_team)
    return db_team

def add_user_to_team(db: Session, *, db_team: Team, db_user: User) -> Team:
    """Adds a user to a team's members list if not already present."""
    if db_user not in db_team.members:
        db_team.members.append(db_user)
        db.add(db_team)
        db.commit()
        db.refresh(db_team)
    return db_team

def remove_user_from_team(db: Session, *, db_team: Team, db_user: User) -> Team:
    """Removes a user from a team's members list if present."""
    if db_user in db_team.members:
        db_team.members.remove(db_user)
        db.add(db_team)
        db.commit()
        db.refresh(db_team)
    return db_team

def is_user_member_of_team(db: Session, *, team_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Checks if a user is a member of a specific team."""
    return db.query(Team).join(Team.members).filter(Team.id == team_id, User.id == user_id).count() > 0
