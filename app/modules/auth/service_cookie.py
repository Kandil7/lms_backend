from typing import Optional, Tuple
from uuid import UUID

from fastapi import Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.cookie_utils import delete_http_only_cookie, set_http_only_cookie
from app.core.exceptions import UnauthorizedException
from app.core.security import (
    TokenType,
    blacklist_access_token,
    decode_token,
)
from app.modules.auth.schemas_cookie import TokenResponseWithCookies
from app.modules.auth.service import AuthService as BaseAuthService
from app.modules.users.schemas import UserResponse
from urllib.parse import urlparse


class CookieBasedAuthService(BaseAuthService):
    """
    Extended AuthService that supports HTTP-only cookies for refresh tokens.
    
    This implementation returns refresh tokens in HTTP-only cookies instead of JSON responses
    for enhanced security against XSS attacks.
    """
    
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    @staticmethod
    def _resolve_cookie_domain() -> str | None:
        raw_domain = (settings.APP_DOMAIN or "").strip()
        if not raw_domain:
            return None

        parsed = urlparse(raw_domain if "://" in raw_domain else f"https://{raw_domain}")
        return parsed.hostname or raw_domain

    @staticmethod
    def _build_cookie_token_response(*, access_token: str, user) -> TokenResponseWithCookies:
        return TokenResponseWithCookies(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    def _set_refresh_token_cookie(self, response: Response, refresh_token: str) -> None:
        """Set refresh token in HTTP-only cookie with secure defaults."""
        domain = self._resolve_cookie_domain()

        # Set HTTP-only cookie with secure defaults
        set_http_only_cookie(
            response=response,
            name="refresh_token",
            value=refresh_token,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # Convert days to seconds
            domain=domain,
            secure=settings.ENVIRONMENT == "production",
            httponly=True,
            samesite="strict" if settings.ENVIRONMENT == "production" else "lax",
        )

    def _delete_refresh_token_cookie(self, response: Response) -> None:
        """Delete the refresh token cookie."""
        domain = self._resolve_cookie_domain()
        delete_http_only_cookie(response=response, name="refresh_token", domain=domain)

    def login_with_cookies(self, email: str, password: str, response: Response, ip_address: str = "127.0.0.1") -> Tuple:
        """Login with HTTP-only cookie support for refresh tokens."""
        user, tokens, mfa_challenge = self.login(email, password, ip_address=ip_address)

        if mfa_challenge:
            return user, None, mfa_challenge

        # Reuse the refresh token already issued/revoked by base flow.
        self._set_refresh_token_cookie(response, tokens.refresh_token)
        tokens_with_cookies = self._build_cookie_token_response(
            access_token=tokens.access_token,
            user=user,
        )
        return user, tokens_with_cookies, None

    def refresh_tokens_with_cookies(
        self,
        request: Request,
        response: Response,
        previous_access_token: str | None = None,
        fallback_refresh_token: str | None = None,
    ) -> TokenResponseWithCookies:
        """Refresh tokens with HTTP-only cookie support."""
        refresh_token = self._get_refresh_token_from_cookie(request) or fallback_refresh_token
        if not refresh_token:
            raise UnauthorizedException("Refresh token missing from cookie")

        # Process refresh token normally
        tokens = self.refresh_tokens(refresh_token, previous_access_token)

        # Set new refresh token in cookie
        self._set_refresh_token_cookie(response, tokens.refresh_token)

        # Return only access token in JSON (refresh token is in cookie)
        user_id = self._parse_user_id_from_access_token(tokens.access_token)
        user = self.user_service.get_user(UUID(user_id))
        return self._build_cookie_token_response(
            access_token=tokens.access_token,
            user=user,
        )

    def _get_refresh_token_from_cookie(self, request: Request) -> Optional[str]:
        """Extract refresh token from HTTP-only cookie."""
        return request.cookies.get("refresh_token")

    def logout_with_cookies(
        self,
        request: Request,
        response: Response,
        access_token: str | None = None,
        fallback_refresh_token: str | None = None,
    ) -> None:
        """Logout with HTTP-only cookie support."""
        refresh_token = self._get_refresh_token_from_cookie(request) or fallback_refresh_token

        if refresh_token:
            try:
                self.logout(refresh_token, access_token=access_token)
            except UnauthorizedException:
                # Keep logout idempotent even if refresh token is stale/invalid.
                pass
        elif access_token:
            try:
                blacklist_access_token(access_token)
            except UnauthorizedException:
                pass

        self._delete_refresh_token_cookie(response)

    def _parse_user_id_from_access_token(self, access_token: str) -> str:
        """Parse user ID from access token payload."""
        payload = decode_token(access_token, expected_type=TokenType.ACCESS, check_blacklist=False)
        return payload.get("sub", "")
