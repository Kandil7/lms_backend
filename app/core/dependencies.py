from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.permissions import Permission, Role, has_permission
from app.core.security import TokenType, decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False)


def get_pagination(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> tuple[int, int]:
    return page, page_size


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    payload = decode_token(token, expected_type=TokenType.ACCESS)

    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedException("Could not validate credentials") from exc

    from app.modules.users.repositories.user_repository import UserRepository

    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise UnauthorizedException("Could not validate credentials")

    return user


def get_current_user_optional(
    token: str | None = Depends(optional_oauth2_scheme),
    db: Session = Depends(get_db),
):
    if not token:
        return None

    try:
        return get_current_user(token=token, db=db)
    except UnauthorizedException:
        return None


def require_roles(*roles: Role) -> Callable:
    def dependency(current_user=Depends(get_current_user)):
        if roles and current_user.role not in {role.value for role in roles}:
            raise ForbiddenException("Not authorized to perform this action")
        return current_user

    return dependency


def require_permissions(*permissions: Permission) -> Callable:
    def dependency(current_user=Depends(get_current_user)):
        if any(not has_permission(current_user.role, permission) for permission in permissions):
            raise ForbiddenException("Insufficient permissions")
        return current_user

    return dependency
