"""
Cookie-based authentication service for secure token management.

This service handles setting tokens as HttpOnly cookies instead of returning them in JSON responses.
"""

from fastapi import Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.cookie_utils import set_http_only_cookie, delete_http_only_cookie
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import TokenResponse


class CookieAuthService:
    def __init__(self, db: Session) -> None:
        self.auth_service = AuthService(db)
        self.db = db

    def login_with_cookies(self, email: str, password: str, request: Request, response: Response, ip_address: str = "127.0.0.1") -> None:
        """Login and set tokens as HttpOnly cookies"""
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
        tokens = self.auth_service.refresh_tokens(refresh_token)
        
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

    def logout_with_cookies(self, request: Request, response: Response) -> None:
        """Logout and delete HttpOnly cookies"""
        # Delete access token cookie
        delete_http_only_cookie(response=response, name="access_token")
        # Delete refresh token cookie
        delete_http_only_cookie(response=response, name="refresh_token")