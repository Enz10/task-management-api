from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict, computed_field
from .common import Page
from .user import User as UserSchema

# Shared properties
class TaskBase(BaseModel):
    title: Optional[str] = None
    assignee_id: Optional[uuid.UUID] = Field(None, description="ID of the user this task is assigned to")
    description: Optional[str] = None
    due_date: Optional[date] = None
    completed: Optional[bool] = False
    priority: Optional[int] = None
    # Add team_id - needed when creating a task within a team context
    team_id: Optional[uuid.UUID] = None # Make it optional here, but required in Create


# Properties to receive via API on creation
class TaskCreate(TaskBase):
    title: str # Required on creation
    due_date: date # Required on creation
    team_id: uuid.UUID # Required on creation

class TaskUpdate(TaskBase):
    pass

class TaskInDBBase(TaskBase):
    id: uuid.UUID
    team_id: uuid.UUID
    creator_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    # Pydantic V2 configuration
    model_config = ConfigDict(from_attributes=True)

# Properties to return to client
class Task(BaseModel):

    id: uuid.UUID
    title: Optional[str]
    description: Optional[str]
    due_date: date
    completed: bool
    priority: Optional[int]
    team_id: uuid.UUID
    creator_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    assignee: Optional[UserSchema] = None

    # Pydantic V2 configuration, ensuring it can be created from ORM model instance
    model_config = ConfigDict(from_attributes=True)

class TaskInDB(TaskInDBBase):
    pass

class TaskPage(Page[Task]):
    pass
