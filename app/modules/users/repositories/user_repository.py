from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.users.models import User

_UNSET = object()


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.scalar(stmt)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        return self.db.scalar(stmt)

    def list(self, page: int, page_size: int) -> tuple[list[User], int]:
        total_stmt = select(func.count()).select_from(User)
        total = int(self.db.scalar(total_stmt) or 0)

        stmt = (
            select(User)
            .order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self.db.scalars(stmt).all())
        return items, total

    def create(
        self,
        *,
        email: str,
        password_hash: str,
        full_name: str,
        role: str,
        is_active: bool = True,
        email_verified_at: datetime | None | object = _UNSET,
    ) -> User:
        if email_verified_at is _UNSET:
            email_verified_at = datetime.now(UTC)

        user = User(
            email=email.lower(),
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            is_active=is_active,
            email_verified_at=email_verified_at,
        )
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def update(self, user: User, **fields) -> User:
        for key, value in fields.items():
            if value is not None:
                setattr(user, key, value)
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user
