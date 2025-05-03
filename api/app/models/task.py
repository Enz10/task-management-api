import uuid
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Boolean, DateTime, Date, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.base_class import Base

if TYPE_CHECKING:
    from .user import User  # noqa: F401
    from .team import Team  # noqa: F401

class Task(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(length=255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    team: Mapped["Team"] = relationship("Team", back_populates="tasks")
    creator: Mapped["User"] = relationship("User", back_populates="created_tasks")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Task(id={self.id!r}, title={self.title!r}, team_id={self.team_id!r}, creator_id={self.creator_id!r})>"
