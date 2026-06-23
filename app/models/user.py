from datetime import datetime

from sqlalchemy import Integer, String, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

from typing import TYPE_CHECKING

# Avoid circular imports by using TYPE_CHECKING to import the File model only for type hints
if TYPE_CHECKING:
    from app.models.file import File 

# User model    
class User(Base):
    __tablename__ = "users"
    
    # Columns
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
        )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
        )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
        )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    files: Mapped[list["File"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
