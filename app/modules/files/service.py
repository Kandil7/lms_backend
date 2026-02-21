import logging
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenException, NotFoundException
from app.modules.files.models import UploadedFile
from app.modules.files.storage import AzureBlobStorageBackend, LocalStorageBackend
from app.modules.files.storage.base import StorageBackend
from app.utils.validators import ensure_allowed_extension, normalize_storage_folder

logger = logging.getLogger(__name__)


class FileService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.backends = self._build_backends()
        self.default_provider = self._select_default_provider()

    def upload_file(self, uploader_id: UUID, file: UploadFile, folder: str = "uploads", is_public: bool = False) -> UploadedFile:
        content = file.file.read()
        file_size = len(content)
        if file_size == 0:
            raise ValueError("Uploaded file is empty")
        if file_size > settings.MAX_UPLOAD_BYTES:
            raise ValueError(f"File too large. Max size is {settings.MAX_UPLOAD_MB}MB")

        safe_folder = normalize_storage_folder(folder)
        ext = ensure_allowed_extension(file.filename or "", settings.ALLOWED_UPLOAD_EXTENSIONS)
        safe_filename = f"{uuid4().hex}.{ext}"

        mime_type = file.content_type or "application/octet-stream"
        file_type = self._detect_file_type(mime_type, ext)
        backend = self._get_backend(self.default_provider)

        storage_path = backend.save(folder=safe_folder, filename=safe_filename, content=content, content_type=mime_type)
        file_url = self._build_file_url(backend, storage_path)

        uploaded_file = UploadedFile(
            uploader_id=uploader_id,
            filename=safe_filename,
            original_filename=file.filename or safe_filename,
            file_url=file_url,
            storage_path=storage_path,
            file_type=file_type,
            mime_type=mime_type,
            file_size=file_size,
            folder=safe_folder,
            storage_provider=backend.provider,
            is_public=is_public,
        )

        self.db.add(uploaded_file)
        self.db.flush()

        if backend.provider == "local":
            uploaded_file.file_url = self._build_local_download_url(uploaded_file.id)
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

    def get_download_target(self, uploaded_file: UploadedFile) -> tuple[str, str]:
        backend = self._get_backend(uploaded_file.storage_provider)

        local_path = backend.resolve_local_path(uploaded_file.storage_path)
        if local_path is not None:
            if not local_path.exists():
                raise NotFoundException("File no longer exists")
            return "local", str(local_path)

        remote_url = backend.create_download_url(
            uploaded_file.storage_path,
            expires_seconds=settings.FILE_DOWNLOAD_URL_EXPIRE_SECONDS,
        )
        if remote_url:
            return "remote", remote_url

        if uploaded_file.is_public:
            return "remote", backend.build_file_url(uploaded_file.storage_path)

        raise NotFoundException("Unable to generate file download target")

    def _build_backends(self) -> dict[str, StorageBackend]:
        backends: dict[str, StorageBackend] = {
            "local": LocalStorageBackend(settings.UPLOAD_DIR),
        }

        try:
            if settings.AZURE_STORAGE_CONTAINER_NAME:
                backends["azure"] = AzureBlobStorageBackend(
                    container_name=settings.AZURE_STORAGE_CONTAINER_NAME,
                    connection_string=settings.AZURE_STORAGE_CONNECTION_STRING,
                    account_url=settings.AZURE_STORAGE_ACCOUNT_URL,
                    account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
                    account_key=settings.AZURE_STORAGE_ACCOUNT_KEY,
                    container_url=settings.AZURE_STORAGE_CONTAINER_URL,
                )
        except Exception as exc:
            logger.warning("Azure storage backend is not available, falling back to local storage: %s", exc)

        return backends

    def _select_default_provider(self) -> str:
        if settings.FILE_STORAGE_PROVIDER in self.backends:
            return settings.FILE_STORAGE_PROVIDER

        if settings.FILE_STORAGE_PROVIDER != "local":
            logger.warning(
                "Configured FILE_STORAGE_PROVIDER='%s' is unavailable. Falling back to local.",
                settings.FILE_STORAGE_PROVIDER,
            )
        return "local"

    def _get_backend(self, provider: str) -> StorageBackend:
        backend = self.backends.get(provider)
        if backend:
            return backend
        raise NotFoundException(f"Storage provider '{provider}' is unavailable")

    @staticmethod
    def _build_local_download_url(file_id: UUID) -> str:
        return f"{settings.API_V1_PREFIX}/files/download/{file_id}"

    def _build_file_url(self, backend: StorageBackend, storage_path: str) -> str:
        if backend.provider == "local":
            return ""
        return backend.build_file_url(storage_path)

    @staticmethod
    def _detect_file_type(mime_type: str, extension: str) -> str:
        if mime_type.startswith("video/") or extension in {"mp4", "avi", "mov"}:
            return "video"
        if mime_type.startswith("image/") or extension in {"jpg", "jpeg", "png"}:
            return "image"
        if mime_type in {"application/pdf", "application/msword"} or extension in {"pdf", "doc", "docx"}:
            return "document"
        return "other"
