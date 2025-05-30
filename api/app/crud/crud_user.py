import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

def get_user_by_email(db: Session, *, email: str) -> Optional[User]:
    """Gets a user by their email address."""
    return db.query(User).filter(User.email == email).first()

def get_user(db: Session, *, user_id: uuid.UUID) -> Optional[User]:
    """Gets a user by their ID."""
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, *, user_in: UserCreate) -> User:
    """Creates a new user in the database."""
    hashed_pwd = get_password_hash(user_in.password)
    # Create a dictionary of the data for the User model
    # Exclude the plain password, include the hashed one
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        is_active=user_in.is_active if user_in.is_active is not None else True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user) # Refresh to get DB-generated fields like id, created_at
    return db_user

def update_user(db: Session, *, db_user: User, user_in: UserUpdate) -> User:
    user_data = user_in.model_dump(exclude_unset=True)
    if user_data.get("password"):
        hashed_password = get_password_hash(user_data["password"])
        db_user.hashed_password = hashed_password
        del user_data["password"]

    for field, value in user_data.items():
        setattr(db_user, field, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
