from typing import Generator
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.crud import crud_user
from app.schemas import token as token_schema

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

def get_db() -> Generator:
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    """Dependency to get the current user based on JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception # Invalid UUID format in token

    token_data = token_schema.TokenData(sub=user_id_str) # Validate payload structure (optional but good practice)

    user = crud_user.get_user(db, user_id=user_id)
    if user is None:
        raise credentials_exception # User ID from token doesn't exist
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to get the current active user. Rejects inactive users."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
