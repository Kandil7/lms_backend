from datetime import datetime
import uuid

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    __table_args__ = (
        Index("ix_uploaded_files_uploader_created_at", "uploader_id", "created_at"),
        Index("ix_uploaded_files_uploader_type_created_at", "uploader_id", "file_type", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)

    file_type: Mapped[str] = mapped_column(String(50), nullable=False, default="other")
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    folder: Mapped[str] = mapped_column(String(100), nullable=False, default="uploads")
    storage_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="local")
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    uploader = relationship("User")
