import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Column, String, DateTime, Table, ForeignKey, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base_class import Base

# Association Table for Many-to-Many User <-> Team relationship
team_members_table = Table(
    "team_members",
    Base.metadata,
    Column("team_id", UUID(as_uuid=True), ForeignKey("teams.id"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
)

if TYPE_CHECKING:
    from .user import User  # noqa: F401
    from .task import Task  # noqa: F401

class Team(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(length=100), index=True, nullable=False, unique=True) # Team names should be unique

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    members: Mapped[List["User"]] = relationship(
        "User",
        secondary=team_members_table,
        back_populates="teams"
    )
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="team",
        cascade="all, delete-orphan" # If a team is deleted, delete its tasks
    )

    def __repr__(self):
        return f"<Team(id={self.id!r}, name={self.name!r})>"
