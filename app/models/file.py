from datetime import datetime

from sqlalchemy import Integer, String, func, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

from typing import TYPE_CHECKING

# Avoid circular imports
if TYPE_CHECKING:
    from app.models.file_share import FileShare
    from app.models.file_version import FileVersion
    from app.models.user import User   

class File(Base):
    __tablename__ = "files"
    
    # Columns
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    stored_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )

    size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship to the User model
    owner: Mapped["User"] = relationship(
        back_populates="files",
    )

    # Relationship to the File Share model
    shares: Mapped[list["FileShare"]] = relationship(
        back_populates="file",
        cascade="all, delete-orphan",
    )

    versions: Mapped[list["FileVersion"]] = relationship(
        back_populates="file",
        cascade="all, delete-orphan",
    )