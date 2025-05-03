import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import Column, String, Boolean, DateTime, Table, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db.base_class import Base

from .team import team_members_table

if TYPE_CHECKING:
    from .team import Team  # noqa: F401
    from .task import Task # noqa: F401


class User(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(length=320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(length=1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    teams: Mapped[List["Team"]] = relationship(
        "Team",
        secondary=team_members_table,
        back_populates="members"
    )

    created_tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="creator"
    )

    def __repr__(self):
        return f"<User(id={self.id!r}, email={self.email!r}, is_active={self.is_active!r})>"
