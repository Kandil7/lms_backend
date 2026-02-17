from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    @abstractmethod
    def save(self, *, folder: str, filename: str, content: bytes) -> Path:
        raise NotImplementedError

    @abstractmethod
    def resolve(self, storage_path: str) -> Path:
        raise NotImplementedError
