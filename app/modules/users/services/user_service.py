from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.modules.users.models import User
from app.modules.users.repositories.user_repository import UserRepository
from app.modules.users.schemas import UserCreate, UserUpdate


class UserAlreadyExistsError(ValueError):
    pass


class InvalidCredentialsError(ValueError):
    pass


def _is_duplicate_email_error(exc: IntegrityError) -> bool:
    message = str(exc.orig or exc).lower()
    return ("unique" in message and "email" in message) or "users_email_key" in message


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def create_user(self, payload: UserCreate, *, commit: bool = True) -> User:
        existing = self.repo.get_by_email(payload.email)
        if existing:
            raise UserAlreadyExistsError("Email is already registered")

        try:
            user = self.repo.create(
                email=payload.email,
                password_hash=hash_password(payload.password),
                full_name=payload.full_name,
                role=payload.role.value,
            )
        except IntegrityError as exc:
            self.db.rollback()
            if _is_duplicate_email_error(exc):
                raise UserAlreadyExistsError("Email is already registered") from exc
            raise

        if not commit:
            return user

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            if _is_duplicate_email_error(exc):
                raise UserAlreadyExistsError("Email is already registered") from exc
            raise
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str, *, update_last_login: bool = True) -> User:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            raise InvalidCredentialsError("User account is disabled")
        if settings.REQUIRE_EMAIL_VERIFICATION_FOR_LOGIN and user.email_verified_at is None:
            raise InvalidCredentialsError("Email is not verified")

        if not update_last_login:
            return user

        user.last_login_at = datetime.now(UTC)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user_id: UUID, payload: UserUpdate) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        updates = payload.model_dump(exclude_unset=True)
        password = updates.pop("password", None)
        if password:
            updates["password_hash"] = hash_password(password)

        if "role" in updates and updates["role"] is not None:
            updates["role"] = updates["role"].value

        user = self.repo.update(user, **updates)
        self.db.commit()
        return user

    def list_users(self, page: int, page_size: int) -> tuple[list[User], int]:
        return self.repo.list(page, page_size)

    def get_user(self, user_id: UUID) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        return user
