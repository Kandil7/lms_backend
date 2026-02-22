import hmac
import secrets
import time
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.cache import get_app_cache
from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import (
    TokenType,
    blacklist_access_token,
    create_access_token,
    create_email_verification_token,
    create_mfa_challenge_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.auth.models import RefreshToken
from app.modules.auth.schemas import TokenResponse
from app.modules.users.services.user_service import UserService


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_service = UserService(db)
        self.cache = get_app_cache()

    def login(self, email: str, password: str, ip_address: str = "127.0.0.1") -> tuple:
        from app.core.account_lockout import check_account_lockout, account_lockout_manager
        
        # Check if account is locked
        check_account_lockout(email, ip_address)
        
        try:
            user = self.user_service.authenticate(email=email, password=password, update_last_login=False)
            
            # Reset failed attempts on successful login
            account_lockout_manager.reset_failed_attempts(email, ip_address)
            
            if user.mfa_enabled:
                challenge_token, code, expires_in_seconds = self._create_mfa_login_challenge(user.id)
                return user, None, {
                    "challenge_token": challenge_token,
                    "code": code,
                    "expires_in_seconds": expires_in_seconds,
                }

            self._touch_last_login(user)
            tokens = self._issue_tokens(user.id, user.role)
            self.db.commit()
            return user, tokens, None
            
        except Exception as exc:
            # Increment failed attempts on authentication failure
            account_lockout_manager.increment_failed_attempts(email, ip_address)
            raise exc

    def refresh_tokens(self, refresh_token: str, previous_access_token: str | None = None) -> TokenResponse:
        payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)

        jti = payload.get("jti")
        sub = payload.get("sub")
        if not jti or not sub:
            raise UnauthorizedException("Malformed refresh token")

        user_id = self._parse_user_id(sub, malformed_message="Malformed refresh token")
        if previous_access_token:
            self._ensure_access_token_matches_user(previous_access_token, user_id)

        token_record = self._get_valid_refresh_token(jti, for_update=True)
        if not token_record:
            raise UnauthorizedException("Refresh token is invalid or revoked")

        if token_record.user_id != user_id:
            raise UnauthorizedException("Malformed refresh token")

        user = self.user_service.get_user(user_id)
        if not user.is_active:
            raise UnauthorizedException("User is inactive")

        token_record.revoked_at = datetime.now(UTC)
        self.db.add(token_record)

        try:
            new_tokens = self._issue_tokens(user.id, user.role)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        if previous_access_token:
            try:
                blacklist_access_token(previous_access_token)
            except UnauthorizedException:
                pass
        return new_tokens

    def logout(self, refresh_token: str, access_token: str | None = None) -> None:
        payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        jti = payload.get("jti")
        sub = payload.get("sub")
        if not jti:
            raise UnauthorizedException("Malformed refresh token")

        user_id = self._parse_user_id(sub, malformed_message="Malformed refresh token")
        if access_token:
            self._ensure_access_token_matches_user(access_token, user_id)

        token_record = self._get_valid_refresh_token(jti, for_update=True)
        if token_record:
            if token_record.user_id != user_id:
                raise UnauthorizedException("Malformed refresh token")
            token_record.revoked_at = datetime.now(UTC)
            self.db.add(token_record)
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()
                raise

        if access_token:
            try:
                blacklist_access_token(access_token)
            except UnauthorizedException:
                # Keep logout idempotent even if the presented access token is already invalid/expired.
                pass

    def request_password_reset(self, email: str) -> tuple[str, str, str] | None:
        user = self.user_service.repo.get_by_email(email.lower())
        if not user or not user.is_active:
            return None

        token = create_password_reset_token(subject=str(user.id))
        return user.email, user.full_name, token

    def request_email_verification(self, email: str) -> tuple[str, str, str] | None:
        user = self.user_service.repo.get_by_email(email.lower())
        if not user or not user.is_active:
            return None

        token = create_email_verification_token(subject=str(user.id))
        return user.email, user.full_name, token

    def confirm_email_verification(self, token: str) -> None:
        payload = decode_token(token, expected_type=TokenType.EMAIL_VERIFICATION, check_blacklist=False)
        user_id = self._parse_user_id(payload.get("sub"), malformed_message="Malformed email verification token")
        user = self.user_service.get_user(user_id)
        if not user.is_active:
            raise UnauthorizedException("User is inactive")

        if user.email_verified_at is not None:
            return

        user.email_verified_at = datetime.now(UTC)
        self.db.add(user)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def reset_password(self, reset_token: str, new_password: str) -> None:
        payload = decode_token(reset_token, expected_type=TokenType.PASSWORD_RESET, check_blacklist=False)
        user_id = self._parse_user_id(payload.get("sub"), malformed_message="Malformed password reset token")
        user = self.user_service.get_user(user_id)
        if not user.is_active:
            raise UnauthorizedException("User is inactive")

        now = datetime.now(UTC)
        user.password_hash = hash_password(new_password)
        self.db.add(user)

        active_tokens = list(
            self.db.scalars(
                select(RefreshToken).where(
                    RefreshToken.user_id == user.id,
                    RefreshToken.revoked_at.is_(None),
                )
            ).all()
        )
        for token_record in active_tokens:
            token_record.revoked_at = now
            self.db.add(token_record)

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def request_enable_mfa(self, current_user, password: str) -> tuple[str, str, str, int]:
        if not verify_password(password, current_user.password_hash):
            raise UnauthorizedException("Invalid password")

        if current_user.mfa_enabled:
            return current_user.email, current_user.full_name, "", settings.MFA_LOGIN_CODE_EXPIRE_MINUTES

        code = self._generate_numeric_code(settings.MFA_LOGIN_CODE_LENGTH)
        ttl_seconds = max(60, settings.MFA_LOGIN_CODE_EXPIRE_MINUTES * 60)
        cache_key = self._mfa_setup_cache_key(current_user.id)
        self.cache.set_json(cache_key, {"code": code}, ttl_seconds=ttl_seconds)
        return current_user.email, current_user.full_name, code, settings.MFA_LOGIN_CODE_EXPIRE_MINUTES

    def confirm_enable_mfa(self, current_user, code: str) -> None:
        cache_key = self._mfa_setup_cache_key(current_user.id)
        payload = self.cache.get_json(cache_key)
        expected_code = payload.get("code") if isinstance(payload, dict) else None
        if not isinstance(expected_code, str) or not hmac.compare_digest(expected_code, code.strip()):
            raise UnauthorizedException("Invalid MFA code")

        current_user.mfa_enabled = True
        self.db.add(current_user)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.cache.delete_by_prefix(cache_key)

    def disable_mfa(self, current_user, password: str) -> None:
        if not verify_password(password, current_user.password_hash):
            raise UnauthorizedException("Invalid password")

        if not current_user.mfa_enabled:
            return

        current_user.mfa_enabled = False
        self.db.add(current_user)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def verify_mfa_login(self, challenge_token: str, code: str) -> tuple:
        payload = decode_token(challenge_token, expected_type=TokenType.MFA_CHALLENGE, check_blacklist=False)
        jti = payload.get("jti")
        sub = payload.get("sub")
        if not jti or not sub:
            raise UnauthorizedException("Malformed MFA challenge token")

        user_id = self._parse_user_id(sub, malformed_message="Malformed MFA challenge token")
        cache_key = self._mfa_login_cache_key(str(jti))
        cached_payload = self.cache.get_json(cache_key)
        if not isinstance(cached_payload, dict):
            raise UnauthorizedException("MFA challenge expired or invalid")

        cached_user_id = str(cached_payload.get("user_id") or "")
        expected_code = cached_payload.get("code")
        if cached_user_id != str(user_id):
            raise UnauthorizedException("MFA challenge is invalid")
        if not isinstance(expected_code, str) or not hmac.compare_digest(expected_code, code.strip()):
            raise UnauthorizedException("Invalid MFA code")

        self.cache.delete_by_prefix(cache_key)
        user = self.user_service.get_user(user_id)
        if not user.is_active:
            raise UnauthorizedException("User is inactive")
        if not user.mfa_enabled:
            raise UnauthorizedException("MFA is not enabled for this account")

        self._touch_last_login(user)
        tokens = self._issue_tokens(user.id, user.role)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return user, tokens

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

    @staticmethod
    def _parse_user_id(sub: str | None, *, malformed_message: str) -> UUID:
        if not sub:
            raise UnauthorizedException(malformed_message)
        try:
            return UUID(sub)
        except ValueError as exc:
            raise UnauthorizedException(malformed_message) from exc

    def _ensure_access_token_matches_user(self, access_token: str, expected_user_id: UUID) -> None:
        access_payload = decode_token(access_token, expected_type=TokenType.ACCESS, check_blacklist=False)
        access_sub = access_payload.get("sub")
        access_user_id = self._parse_user_id(access_sub, malformed_message="Malformed access token")
        if access_user_id != expected_user_id:
            raise UnauthorizedException("Access token does not match refresh token")

    def _touch_last_login(self, user) -> None:
        user.last_login_at = datetime.now(UTC)
        self.db.add(user)

    def _create_mfa_login_challenge(self, user_id: UUID) -> tuple[str, str, int]:
        challenge_token = create_mfa_challenge_token(subject=str(user_id))
        payload = decode_token(challenge_token, expected_type=TokenType.MFA_CHALLENGE, check_blacklist=False)
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or not isinstance(exp, (int, float)):
            raise UnauthorizedException("Malformed MFA challenge token")

        code = self._generate_numeric_code(settings.MFA_LOGIN_CODE_LENGTH)
        ttl_seconds = max(1, int(exp) - int(time.time()))
        cache_key = self._mfa_login_cache_key(str(jti))
        self.cache.set_json(
            cache_key,
            {"user_id": str(user_id), "code": code},
            ttl_seconds=ttl_seconds,
        )
        return challenge_token, code, ttl_seconds

    @staticmethod
    def _generate_numeric_code(length: int) -> str:
        normalized_length = max(4, min(length, 12))
        return "".join(secrets.choice("0123456789") for _ in range(normalized_length))

    @staticmethod
    def _mfa_setup_cache_key(user_id: UUID) -> str:
        return f"auth:mfa:setup:{user_id}"

    @staticmethod
    def _mfa_login_cache_key(challenge_jti: str) -> str:
        return f"auth:mfa:login:{challenge_jti}"
