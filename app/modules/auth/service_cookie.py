from fastapi import Request, Response
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.cookie_utils import set_http_only_cookie, delete_http_only_cookie
from app.core.security import (
    TokenType,
    blacklist_access_token,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.modules.auth.models import RefreshToken
from app.modules.auth.schemas_cookie import TokenResponseWithCookies
from app.modules.auth.service import AuthService as BaseAuthService
from app.modules.users.schemas import UserResponse
from app.modules.users.services.user_service import UserService
from app.core.exceptions import UnauthorizedException
from datetime import UTC, datetime


class CookieBasedAuthService(BaseAuthService):
    """
    Extended AuthService that supports HTTP-only cookies for refresh tokens.
    
    This implementation returns refresh tokens in HTTP-only cookies instead of JSON responses
    for enhanced security against XSS attacks.
    """
    
    def __init__(self, db: Session) -> None:
        super().__init__(db)
    
    def _issue_tokens_with_cookies(self, user_id: str, role: str, response: Response) -> TokenResponseWithCookies:
        """Issue tokens and set refresh token in HTTP-only cookie."""
        access_token = create_access_token(subject=user_id, role=role)
        
        # Create refresh token but don't return it in JSON
        refresh_token = create_refresh_token(subject=user_id)
        
        # Store refresh token in HTTP-only cookie
        self._set_refresh_token_cookie(response, refresh_token)
        
        return TokenResponseWithCookies(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(self.user_service.get_user(UUID(user_id))),
        )
    
    def _set_refresh_token_cookie(self, response: Response, refresh_token: str) -> None:
        """Set refresh token in HTTP-only cookie with secure defaults."""
        # Use domain from settings if available, otherwise use default
        domain = settings.APP_DOMAIN if hasattr(settings, 'APP_DOMAIN') and settings.APP_DOMAIN else None
        
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
        domain = settings.APP_DOMAIN if hasattr(settings, 'APP_DOMAIN') and settings.APP_DOMAIN else None
        delete_http_only_cookie(response=response, name="refresh_token", domain=domain)
    
    def login_with_cookies(self, email: str, password: str, response: Response, ip_address: str = "127.0.0.1") -> Tuple:
        """Login with HTTP-only cookie support for refresh tokens."""
        user, tokens, mfa_challenge = self.login(email, password, ip_address=ip_address)
        
        if mfa_challenge:
            return user, None, mfa_challenge
        
        # Issue tokens with cookies
        tokens_with_cookies = self._issue_tokens_with_cookies(str(user.id), user.role, response)
        
        return user, tokens_with_cookies, None
    
    def refresh_tokens_with_cookies(
        self, 
        request: Request, 
        response: Response, 
        previous_access_token: str | None = None
    ) -> TokenResponseWithCookies:
        """Refresh tokens with HTTP-only cookie support."""
        # Get refresh token from cookie
        refresh_token = self._get_refresh_token_from_cookie(request)
        if not refresh_token:
            raise UnauthorizedException("Refresh token missing from cookie")
        
        # Process refresh token normally
        tokens = self.refresh_tokens(refresh_token, previous_access_token)
        
        # Set new refresh token in cookie
        self._set_refresh_token_cookie(response, tokens.refresh_token)
        
        # Return only access token in JSON (refresh token is in cookie)
        user_id = self._parse_user_id_from_access_token(tokens.access_token)
        user = self.user_service.get_user(UUID(user_id))
        return TokenResponseWithCookies(
            access_token=tokens.access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
    
    def _get_refresh_token_from_cookie(self, request: Request) -> Optional[str]:
        """Extract refresh token from HTTP-only cookie."""
        return request.cookies.get("refresh_token")
    
    def logout_with_cookies(self, response: Response, access_token: str | None = None) -> None:
        """Logout with HTTP-only cookie support."""
        # Get refresh token from cookie (router will provide this)
        # For now, we'll handle the cookie deletion here
        self._delete_refresh_token_cookie(response)
        
        # Also blacklist the access token if provided
        if access_token:
            try:
                blacklist_access_token(access_token)
            except UnauthorizedException:
                pass
    
    def _parse_user_id_from_access_token(self, access_token: str) -> str:
        """Parse user ID from access token payload."""
        payload = decode_token(access_token, expected_type=TokenType.ACCESS, check_blacklist=False)
        return payload.get("sub", "")
