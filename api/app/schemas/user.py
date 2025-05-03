from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None

# Properties stored in DB
class UserInDBBase(UserBase):
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Additional properties to return to client
class User(UserInDBBase):
    pass

# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
