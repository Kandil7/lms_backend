from pydantic import BaseModel
from typing import Optional

from app.modules.users.schemas import UserResponse
from app.modules.auth.schemas import TokenResponse as BaseTokenResponse


class TokenResponseWithCookies(BaseModel):
    """Response model for endpoints that use HTTP-only cookies for refresh tokens."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class AuthResponseWithCookies(BaseModel):
    """Auth response for endpoints that use HTTP-only cookies for refresh tokens."""
    user: UserResponse
    tokens: TokenResponseWithCookies