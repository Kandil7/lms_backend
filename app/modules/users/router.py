from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_pagination, require_roles
from app.core.permissions import Role
from app.modules.users.schemas import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.modules.users.services.user_service import UserService
from app.utils.pagination import PageParams, paginate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user=Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get("", response_model=UserListResponse)
def list_users(
    pagination: tuple[int, int] = Depends(get_pagination),
    _: object = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> UserListResponse:
    page, page_size = pagination
    service = UserService(db)
    users, total = service.list_users(page, page_size)
    payload = paginate([UserResponse.model_validate(user) for user in users], total, PageParams(page, page_size))
    return UserListResponse.model_validate(payload)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    _: object = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> UserResponse:
    user = UserService(db).get_user(user_id)
    return UserResponse.model_validate(user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    _: object = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> UserResponse:
    user = UserService(db).create_user(payload)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    _: object = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> UserResponse:
    user = UserService(db).update_user(user_id, payload)
    return UserResponse.model_validate(user)
