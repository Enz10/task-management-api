from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel
from app.schemas.user import User as UserSchema

# Shared properties
class TeamBase(BaseModel):
    name: str

# Properties to receive via API on creation
class TeamCreate(TeamBase):
    pass # Currently just the name

# Properties to receive via API on update (optional)
class TeamUpdate(TeamBase):
    name: Optional[str] = None # Allow partial updates


# Properties stored in DB
class TeamInDBBase(TeamBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Additional properties to return to client
class Team(TeamInDBBase):
    members: List[UserSchema] = []

    class Config:
        orm_mode = True


# Additional properties stored in DB
class TeamInDB(TeamInDBBase):
    pass # Currently same as TeamInDBBase
