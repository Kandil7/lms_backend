from collections.abc import Callable
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.permissions import Permission, Role, has_permission
from app.core.security import TokenType, decode_token

# Import User model only for type hints (avoid circular imports)
if TYPE_CHECKING:
    from app.modules.users.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/token")
optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/token", auto_error=False
)


def get_pagination(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> tuple[int, int]:
    return page, page_size


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> "User":
    """Get the current authenticated user from JWT token."""
    payload = decode_token(token, expected_type=TokenType.ACCESS)

    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedException("Could not validate credentials") from exc

    from app.modules.users.repositories.user_repository import UserRepository

    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise UnauthorizedException("Could not validate credentials")
    if settings.REQUIRE_EMAIL_VERIFICATION_FOR_LOGIN and user.email_verified_at is None:
        raise UnauthorizedException("Email is not verified")

    return user


def get_current_user_optional(
    token: str | None = Depends(optional_oauth2_scheme),
    db: Session = Depends(get_db),
) -> "User | None":
    """Get the current user if authenticated, None otherwise."""
    if not token:
        return None

    try:
        return get_current_user(token=token, db=db)
    except UnauthorizedException:
        return None


def require_roles(*roles: Role) -> Callable:
    """Dependency that requires specific roles for access."""

    def dependency(current_user: "User" = Depends(get_current_user)) -> "User":
        if roles and current_user.role not in {role.value for role in roles}:
            raise ForbiddenException("Not authorized to perform this action")
        return current_user

    return dependency


def require_permissions(*permissions: Permission) -> Callable:
    """Dependency that requires specific permissions for access."""

    def dependency(current_user: "User" = Depends(get_current_user)) -> "User":
        if any(
            not has_permission(current_user.role, permission)
            for permission in permissions
        ):
            raise ForbiddenException("Insufficient permissions")
        return current_user

    return dependency
