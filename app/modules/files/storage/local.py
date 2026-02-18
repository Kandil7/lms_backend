from pathlib import Path

from app.core.config import settings
from app.modules.files.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    provider = "local"

    def __init__(self, root_dir: str | None = None) -> None:
        self.root = Path(root_dir or settings.UPLOAD_DIR)
        self.root.mkdir(parents=True, exist_ok=True)
        self._root_resolved = self.root.resolve()

    def save(self, *, folder: str, filename: str, content: bytes, content_type: str | None = None) -> str:
        target_dir = (self.root / folder).resolve()
        if target_dir != self._root_resolved and self._root_resolved not in target_dir.parents:
            raise ValueError("Invalid storage folder path")

        target_dir.mkdir(parents=True, exist_ok=True)

        path = target_dir / filename
        path.write_bytes(content)
        try:
            return path.relative_to(Path.cwd()).as_posix()
        except ValueError:
            return path.as_posix()

    def build_file_url(self, storage_path: str) -> str:
        return "/" + storage_path.replace("\\", "/")

    def resolve_local_path(self, storage_path: str) -> Path | None:
        path = Path(storage_path)
        if path.is_absolute():
            resolved = path.resolve()
            if resolved != self._root_resolved and self._root_resolved not in resolved.parents:
                return None
            return resolved
        resolved = (Path.cwd() / storage_path).resolve()
        if resolved != self._root_resolved and self._root_resolved not in resolved.parents:
            return None
        return resolved

    def create_download_url(self, storage_path: str, *, expires_seconds: int) -> str | None:
        return None
