"""
Cookie-based authentication service for secure token management.

This service handles setting tokens as HttpOnly cookies instead of returning them in JSON responses.
"""

from fastapi import Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.cookie_utils import set_http_only_cookie, delete_http_only_cookie
from app.core.exceptions import UnauthorizedException
from app.modules.auth.service import AuthService


class CookieAuthService:
    def __init__(self, db: Session) -> None:
        self.auth_service = AuthService(db)
        self.db = db

    def login_with_cookies(self, email: str, password: str, request: Request, response: Response) -> None:
        """Login and set tokens as HttpOnly cookies"""
        ip_address = request.client.host if request.client and request.client.host else "127.0.0.1"
        user, tokens, mfa_challenge = self.auth_service.login(email, password, ip_address=ip_address)
        
        if mfa_challenge:
            # MFA challenge - don't set tokens yet
            return
        
        # Set access token as HttpOnly cookie
        set_http_only_cookie(
            response=response,
            name="access_token",
            value=tokens.access_token,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="strict",
            secure=settings.ENVIRONMENT != "development",
        )
        
        # Set refresh token as HttpOnly cookie  
        set_http_only_cookie(
            response=response,
            name="refresh_token",
            value=tokens.refresh_token,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            samesite="strict",
            secure=settings.ENVIRONMENT != "development",
        )

    def refresh_with_cookies(self, refresh_token: str, request: Request, response: Response) -> None:
        """Refresh tokens and set as HttpOnly cookies"""
        previous_access_token = request.cookies.get("access_token")
        tokens = self.auth_service.refresh_tokens(
            refresh_token,
            previous_access_token=previous_access_token,
        )
        
        # Set new access token as HttpOnly cookie
        set_http_only_cookie(
            response=response,
            name="access_token",
            value=tokens.access_token,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="strict",
            secure=settings.ENVIRONMENT != "development",
        )
        
        # Set new refresh token as HttpOnly cookie
        set_http_only_cookie(
            response=response,
            name="refresh_token",
            value=tokens.refresh_token,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            samesite="strict",
            secure=settings.ENVIRONMENT != "development",
        )

    def logout_with_cookies(
        self,
        request: Request,
        response: Response,
        refresh_token: str | None = None,
        access_token: str | None = None,
    ) -> None:
        """Logout and delete HttpOnly cookies"""
        if refresh_token:
            try:
                self.auth_service.logout(refresh_token, access_token=access_token)
            except UnauthorizedException:
                # Keep cookie logout idempotent even if token is already expired/invalid.
                pass

        # Delete access token cookie
        delete_http_only_cookie(response=response, name="access_token")
        # Delete refresh token cookie
        delete_http_only_cookie(response=response, name="refresh_token")
