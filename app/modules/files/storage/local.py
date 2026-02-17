from pathlib import Path

from app.core.config import settings
from app.modules.files.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    def __init__(self, root_dir: str | None = None) -> None:
        self.root = Path(root_dir or settings.UPLOAD_DIR)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, *, folder: str, filename: str, content: bytes) -> Path:
        target_dir = self.root / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        path = target_dir / filename
        path.write_bytes(content)
        return path

    def resolve(self, storage_path: str) -> Path:
        path = Path(storage_path)
        if path.is_absolute():
            return path
        return Path.cwd() / storage_path
