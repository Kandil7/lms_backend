"""
CSRF Protection Utilities

This module provides CSRF token generation, validation, and middleware for protecting against CSRF attacks.
"""

import secrets
import hashlib
import logging
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.datastructures import Headers
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.csrf_protection")

class CSRFProtection:
    def __init__(self, secret_key: str, token_length: int = 32):
        self.secret_key = secret_key
        self.token_length = token_length
        
    def _generate_token(self) -> str:
        """Generate a random CSRF token."""
        return secrets.token_urlsafe(self.token_length)
    
    def _sign_token(self, token: str) -> str:
        """Sign the token with the secret key to prevent tampering."""
        signature = hashlib.sha256(f"{token}:{self.secret_key}".encode()).hexdigest()[:16]
        return f"{token}.{signature}"
    
    def _verify_token(self, signed_token: str) -> bool:
        """Verify the signed token."""
        try:
            token, signature = signed_token.split(".", 1)
            expected_signature = hashlib.sha256(f"{token}:{self.secret_key}".encode()).hexdigest()[:16]
            return signature == expected_signature
        except (ValueError, IndexError):
            return False
    
    def generate_csrf_token(self) -> str:
        """Generate and sign a CSRF token."""
        token = self._generate_token()
        return self._sign_token(token)
    
    
    def validate_csrf_token(self, token: str, request: Request) -> bool:
        """Validate CSRF token from request headers or form data."""
        if not token:
            return False

        # Check if token is valid
        if not self._verify_token(token):
            return False

        # Get token from request (headers, form data, or cookies)
        header_token = request.headers.get("X-CSRF-Token")
        
        # Try to get form data (for form submissions)
        form_token = None
        try:
            form_data = request.form()
            if isinstance(form_data, dict):
                form_token = form_data.get("csrf_token")
        except Exception:
            pass

        # Compare tokens
        if header_token and header_token == token:
            return True
        if form_token and form_token == token:
            return True

        return False

class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, csrf_protection: CSRFProtection, exempt_paths: Optional[list[str]] = None):
        super().__init__(app)
        self.csrf_protection = csrf_protection
        self.exempt_paths = exempt_paths or []
        
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF protection for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            response = await call_next(request)
            return response
            
        # For GET requests, generate CSRF token and set in cookie
        if request.method == "GET":
            csrf_token = self.csrf_protection.generate_csrf_token()
            response = await call_next(request)
            
            # Set CSRF token in cookie (HttpOnly=False for frontend access)
            response.set_cookie(
                key="csrf_token",
                value=csrf_token,
                httponly=False,  # Allow JavaScript access for frontend
                secure=True,  # Only over HTTPS
                samesite="strict",  # Prevent cross-site requests
                max_age=3600 * 24 * 7,  # 7 days
            )
            return response
        
        # For POST/PUT/PATCH/DELETE requests, validate CSRF token
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            # Get token from headers, form data, or cookies
            header_token = request.headers.get("X-CSRF-Token")
            form_token = None
            
            # Try to get form data (for form submissions)
            try:
                form_data = await request.form()
                form_token = form_data.get("csrf_token")
            except Exception:
                pass
                
            cookie_token = request.cookies.get("csrf_token")
            
            # Use the first available token (ensure it's a string)
            token = None
            if header_token:
                token = header_token
            elif form_token and isinstance(form_token, str):
                token = form_token
            elif cookie_token:
                token = cookie_token

            if not token or not self.csrf_protection.validate_csrf_token(token, request):
                logger.warning(f"CSRF token validation failed for {request.method} {request.url.path}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token validation failed"
                )
        
        response = await call_next(request)
        return response

# Global CSRF protection instance
def get_csrf_protection():
    """Get CSRF protection instance with secret key from settings."""
    from app.core.config import settings
    return CSRFProtection(secret_key=settings.SECRET_KEY)

# Helper function to get CSRF token from request
def get_csrf_token_from_request(request: Request) -> Optional[str]:
    """Extract CSRF token from request headers, form data, or cookies."""
    header_token = request.headers.get("X-CSRF-Token")
    if header_token:
        return header_token
    
    # Try form data
    try:
        form_data = request.state.form_data if hasattr(request.state, 'form_data') else None
        if form_data:
            return form_data.get("csrf_token")
    except Exception:
        pass
    
    # Try cookies
    return request.cookies.get("csrf_token")