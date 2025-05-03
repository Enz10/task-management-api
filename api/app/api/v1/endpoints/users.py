from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas 
from app.api import deps
from app.crud import crud_user 

router = APIRouter()

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
):
    """
    Create new user.
    """
    user = crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    user = crud_user.create_user(db=db, user_in=user_in)
    return user

# Add other user endpoints here later (e.g., get user, update user)
