from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenException, NotFoundException
from app.modules.files.models import UploadedFile
from app.modules.files.storage.local import LocalStorageBackend
from app.utils.validators import ensure_allowed_extension


class FileService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.storage = LocalStorageBackend(settings.UPLOAD_DIR)

    def upload_file(self, uploader_id: UUID, file: UploadFile, folder: str = "uploads", is_public: bool = False) -> UploadedFile:
        content = file.file.read()
        file_size = len(content)
        if file_size == 0:
            raise ValueError("Uploaded file is empty")
        if file_size > settings.MAX_UPLOAD_BYTES:
            raise ValueError(f"File too large. Max size is {settings.MAX_UPLOAD_MB}MB")

        ext = ensure_allowed_extension(file.filename or "", settings.ALLOWED_UPLOAD_EXTENSIONS)
        safe_filename = f"{uuid4().hex}.{ext}"
        path = self.storage.save(folder=folder, filename=safe_filename, content=content)

        mime_type = file.content_type or "application/octet-stream"
        file_type = self._detect_file_type(mime_type, ext)

        relative_path = path.as_posix()
        file_url = "/" + relative_path.replace("\\", "/")

        uploaded_file = UploadedFile(
            uploader_id=uploader_id,
            filename=safe_filename,
            original_filename=file.filename or safe_filename,
            file_url=file_url,
            storage_path=relative_path,
            file_type=file_type,
            mime_type=mime_type,
            file_size=file_size,
            folder=folder,
            storage_provider="local",
            is_public=is_public,
        )

        self.db.add(uploaded_file)
        self.db.commit()
        self.db.refresh(uploaded_file)
        return uploaded_file

    def list_user_files(self, user_id: UUID, file_type: str | None = None) -> list[UploadedFile]:
        stmt = select(UploadedFile).where(UploadedFile.uploader_id == user_id)
        if file_type:
            stmt = stmt.where(UploadedFile.file_type == file_type)

        stmt = stmt.order_by(UploadedFile.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def get_file_for_user(self, file_id: UUID, current_user) -> UploadedFile:
        uploaded_file = self.db.scalar(select(UploadedFile).where(UploadedFile.id == file_id))
        if not uploaded_file:
            raise NotFoundException("File not found")

        if not uploaded_file.is_public and current_user.role != "admin" and uploaded_file.uploader_id != current_user.id:
            raise ForbiddenException("Not authorized to access this file")

        return uploaded_file

    def resolve_file_path(self, uploaded_file: UploadedFile) -> Path:
        path = self.storage.resolve(uploaded_file.storage_path)
        if not path.exists():
            raise NotFoundException("File no longer exists")
        return path

    @staticmethod
    def _detect_file_type(mime_type: str, extension: str) -> str:
        if mime_type.startswith("video/") or extension in {"mp4", "avi", "mov"}:
            return "video"
        if mime_type.startswith("image/") or extension in {"jpg", "jpeg", "png"}:
            return "image"
        if mime_type in {"application/pdf", "application/msword"} or extension in {"pdf", "doc", "docx"}:
            return "document"
        return "other"
