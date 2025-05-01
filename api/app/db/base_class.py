from typing import Any
from sqlalchemy.orm import declared_attr, DeclarativeBase

class Base(DeclarativeBase):
    id: Any
    # Generate __tablename__ automatically
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s" # Simple pluralization (e.g., User -> users)
