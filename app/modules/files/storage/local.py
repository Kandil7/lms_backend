from pathlib import Path

from app.core.config import settings
from app.modules.files.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    provider = "local"

    def __init__(self, root_dir: str | None = None) -> None:
        self.root = Path(root_dir or settings.UPLOAD_DIR)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, *, folder: str, filename: str, content: bytes, content_type: str | None = None) -> str:
        target_dir = self.root / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        path = target_dir / filename
        path.write_bytes(content)
        return path.as_posix()

    def build_file_url(self, storage_path: str) -> str:
        return "/" + storage_path.replace("\\", "/")

    def resolve_local_path(self, storage_path: str) -> Path | None:
        path = Path(storage_path)
        if path.is_absolute():
            return path
        return Path.cwd() / storage_path

    def create_download_url(self, storage_path: str, *, expires_seconds: int) -> str | None:
        return None
