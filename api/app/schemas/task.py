import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

# Shared properties
class TaskBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    completed: Optional[bool] = False
    priority: Optional[int] = None

# Properties to receive via API on creation
# Note: owner_id will likely be set based on the authenticated user, not directly in the request body.
class TaskCreate(TaskBase):
    title: str # Title is required on creation
    due_date: date # Due date is required on creation
    owner_id: uuid.UUID # TEMPORARY: Add owner_id for now

# Properties to receive via API on update
class TaskUpdate(TaskBase):
    pass # All fields in TaskBase are optional for update

# Properties shared by models stored in DB
class TaskInDBBase(TaskBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str # Title is always present in DB
    due_date: date # Due date is always present in DB
    completed: bool # Completed is always present in DB
    is_deleted: bool # Include soft delete status
    created_at: datetime
    updated_at: datetime

    # Pydantic V2 uses model_config
    model_config = ConfigDict(from_attributes=True)

# Properties to return to client
class Task(TaskInDBBase):
    pass # Inherits all necessary fields

# Properties stored in DB
class TaskInDB(TaskInDBBase):
    pass # Currently same as TaskInDBBase
