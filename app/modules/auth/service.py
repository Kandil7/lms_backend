from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException
from app.core.security import (
    TokenType,
    blacklist_access_token,
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
        self.db.commit()
        return user, tokens

    def refresh_tokens(self, refresh_token: str, previous_access_token: str | None = None) -> TokenResponse:
        payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)

        jti = payload.get("jti")
        sub = payload.get("sub")
        if not jti or not sub:
            raise UnauthorizedException("Malformed refresh token")

        token_record = self._get_valid_refresh_token(jti, for_update=True)
        if not token_record:
            raise UnauthorizedException("Refresh token is invalid or revoked")

        try:
            user_id = UUID(sub)
        except ValueError as exc:
            raise UnauthorizedException("Malformed refresh token") from exc

        if token_record.user_id != user_id:
            raise UnauthorizedException("Malformed refresh token")

        user = self.user_service.get_user(user_id)
        if not user.is_active:
            raise UnauthorizedException("User is inactive")

        token_record.revoked_at = datetime.now(UTC)
        self.db.add(token_record)

        try:
            new_tokens = self._issue_tokens(user.id, user.role)
            if previous_access_token:
                try:
                    blacklist_access_token(previous_access_token)
                except UnauthorizedException:
                    pass
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return new_tokens

    def logout(self, refresh_token: str, access_token: str | None = None) -> None:
        if access_token:
            try:
                blacklist_access_token(access_token)
            except UnauthorizedException:
                # Keep logout idempotent even if the presented access token is already invalid/expired.
                pass

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

    def _get_valid_refresh_token(self, token_jti: str, *, for_update: bool = False) -> RefreshToken | None:
        stmt = select(RefreshToken).where(
            RefreshToken.token_jti == token_jti,
            RefreshToken.revoked_at.is_(None),
        )
        if for_update:
            stmt = stmt.with_for_update()
        token = self.db.scalar(stmt)
        if not token:
            return None

        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if expires_at <= datetime.now(UTC):
            return None

        return token
