from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    original_filename: str
    file_url: str
    file_type: str
    mime_type: str
    file_size: int
    storage_provider: str
    created_at: datetime

    @property
    def file_size_mb(self) -> float:
        return round(self.file_size / (1024 * 1024), 2)


class FileListResponse(BaseModel):
    files: list[FileResponse]
    total: int
