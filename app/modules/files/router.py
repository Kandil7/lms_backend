from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.files.schemas import FileListResponse, FileResponse
from app.modules.files.service import FileService

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
def upload_file(
    file: UploadFile = File(...),
    folder: str = Form(default="uploads"),
    is_public: bool = Form(default=False),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    uploaded_file = FileService(db).upload_file(current_user.id, file, folder, is_public)
    return FileResponse.model_validate(uploaded_file)


@router.get("/my-files", response_model=FileListResponse)
def list_my_files(
    file_type: str | None = Query(default=None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileListResponse:
    files = FileService(db).list_user_files(current_user.id, file_type)
    return FileListResponse(files=[FileResponse.model_validate(item) for item in files], total=len(files))


@router.get("/download/{file_id}")
def download_file(
    file_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FastAPIFileResponse:
    service = FileService(db)
    uploaded_file = service.get_file_for_user(file_id, current_user)
    path = service.resolve_file_path(uploaded_file)

    return FastAPIFileResponse(path=str(path), filename=uploaded_file.original_filename, media_type=uploaded_file.mime_type)
