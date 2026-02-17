from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.modules.auth.models import RefreshToken
from app.modules.auth.schemas import TokenResponse
from app.modules.users.services.user_service import UserService


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_service = UserService(db)

    def login(self, email: str, password: str) -> tuple:
        user = self.user_service.authenticate(email=email, password=password)
        tokens = self._issue_tokens(user.id, user.role)
        return user, tokens

    def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)

        jti = payload.get("jti")
        sub = payload.get("sub")
        if not jti or not sub:
            raise UnauthorizedException("Malformed refresh token")

        token_record = self._get_valid_refresh_token(jti)
        if not token_record:
            raise UnauthorizedException("Refresh token is invalid or revoked")

        try:
            user_id = UUID(sub)
        except ValueError as exc:
            raise UnauthorizedException("Malformed refresh token") from exc

        user = self.user_service.get_user(user_id)
        if not user.is_active:
            raise UnauthorizedException("User is inactive")

        token_record.revoked_at = datetime.now(UTC)
        self.db.add(token_record)

        new_tokens = self._issue_tokens(user.id, user.role)
        self.db.commit()
        return new_tokens

    def logout(self, refresh_token: str) -> None:
        payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        jti = payload.get("jti")
        if not jti:
            raise UnauthorizedException("Malformed refresh token")

        token_record = self._get_valid_refresh_token(jti)
        if token_record:
            token_record.revoked_at = datetime.now(UTC)
            self.db.add(token_record)
            self.db.commit()

    def _issue_tokens(self, user_id: UUID, role: str) -> TokenResponse:
        access_token = create_access_token(subject=str(user_id), role=role)
        refresh_token = create_refresh_token(subject=str(user_id))

        payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        token_record = RefreshToken(
            user_id=user_id,
            token_jti=payload["jti"],
            expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
        )

        self.db.add(token_record)
        self.db.flush()

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    def _get_valid_refresh_token(self, token_jti: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(
            RefreshToken.token_jti == token_jti,
            RefreshToken.revoked_at.is_(None),
        )
        token = self.db.scalar(stmt)
        if not token:
            return None

        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if expires_at <= datetime.now(UTC):
            return None

        return token
