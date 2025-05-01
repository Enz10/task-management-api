import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr # Make email required for creation
    password: str

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None # Allow password update optionally

# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: uuid.UUID
    email: EmailStr # Email is always present in DB
    is_active: bool # is_active is always present in DB
    created_at: datetime
    updated_at: datetime

    # Pydantic V2 uses model_config
    model_config = ConfigDict(from_attributes=True) # Allows creating schema from ORM model

# Properties to return to client (doesn't include hashed_password)
class User(UserInDBBase):
    pass # Inherits all necessary fields from UserInDBBase

# Properties stored in DB (includes hashed_password)
class UserInDB(UserInDBBase):
    hashed_password: str
