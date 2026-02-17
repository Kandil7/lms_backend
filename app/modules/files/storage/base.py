from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    provider: str

    @abstractmethod
    def save(self, *, folder: str, filename: str, content: bytes, content_type: str | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def build_file_url(self, storage_path: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def resolve_local_path(self, storage_path: str) -> Path | None:
        raise NotImplementedError

    @abstractmethod
    def create_download_url(self, storage_path: str, *, expires_seconds: int) -> str | None:
        raise NotImplementedError
