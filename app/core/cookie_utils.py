from typing import Literal

from fastapi import Response

from app.core.config import settings

def set_http_only_cookie(
    response: Response,
    name: str,
    value: str,
    max_age: int = 30 * 24 * 60 * 60,  # 30 days in seconds
    domain: str | None = None,
    path: str = "/",
    secure: bool = True,
    httponly: bool = True,
    samesite: Literal["lax", "strict", "none"] = "lax",
) -> None:
    """
    Set an HTTP-only cookie with secure defaults for production.
    
    Args:
        response: FastAPI Response object
        name: Cookie name
        value: Cookie value
        max_age: Cookie expiration time in seconds
        domain: Domain for the cookie (optional)
        path: Path for the cookie
        secure: Whether to mark as secure (HTTPS only)
        httponly: Whether to mark as HTTP-only (prevents JavaScript access)
        samesite: SameSite policy ('lax', 'strict', or 'none')
    """
    # Use APP_DOMAIN from settings if available and not overridden
    effective_domain = domain or getattr(settings, 'APP_DOMAIN', None)
    
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age,
        domain=effective_domain,
        path=path,
        secure=secure,
        httponly=httponly,
        samesite=samesite,
        # Additional security headers
        expires=None,  # Use max_age instead
    )


def delete_http_only_cookie(
    response: Response,
    name: str,
    path: str = "/",
    domain: str | None = None,
) -> None:
    """
    Delete an HTTP-only cookie by setting it to empty with max_age=0.
    """
    response.set_cookie(
        key=name,
        value="",
        max_age=0,
        path=path,
        domain=domain,
        secure=True,
        httponly=True,
        samesite="lax",
    )
