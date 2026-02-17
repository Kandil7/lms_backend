from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.core.security import hash_password, verify_password
from app.modules.users.models import User
from app.modules.users.repositories.user_repository import UserRepository
from app.modules.users.schemas import UserCreate, UserUpdate


class UserAlreadyExistsError(ValueError):
    pass


class InvalidCredentialsError(ValueError):
    pass


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def create_user(self, payload: UserCreate) -> User:
        existing = self.repo.get_by_email(payload.email)
        if existing:
            raise UserAlreadyExistsError("Email is already registered")

        user = self.repo.create(
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            role=payload.role.value,
        )
        self.db.commit()
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            raise InvalidCredentialsError("User account is disabled")

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
