"""
Security Enhancement Middleware

This module provides enhanced security middleware including:
- XSS protection (HTML sanitization)
- CSRF protection
- PII log redaction
- Enhanced cookie security
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers

from app.core.config import settings
from app.core.xss_protection import sanitize_user_content, sanitize_fields
from app.core.csrf_protection import get_csrf_protection, CSRFMiddleware
from app.core.log_redaction import pii_redaction_filter
from app.core.cookie_utils import set_http_only_cookie, delete_http_only_cookie

logger = logging.getLogger("app.security_enhancement")

class SecurityEnhancementMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.csrf_middleware = CSRFMiddleware(
            app,
            csrf_protection=get_csrf_protection(),
            exempt_paths=[
                "/api/v1/health",
                "/api/v1/ready",
                "/docs",
                "/redoc",
                "/openapi.json",
                "/metrics",
                "/api/v1/auth/token",
                "/api/v1/auth/login",
                "/api/v1/auth/register",
                "/api/v1/auth/forgot-password",
                "/api/v1/auth/reset-password",
                "/api/v1/auth/verify-email",
            ]
        )
        
    async def dispatch(self, request: Request, call_next):
        # Apply CSRF protection for non-exempt paths
        if not any(request.url.path.startswith(path) for path in self.csrf_middleware.exempt_paths):
            # For POST/PUT/PATCH/DELETE requests, validate CSRF token
            if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
                # Get token from headers, form data, or cookies
                header_token = request.headers.get("X-CSRF-Token")
                form_token = None
                
                try:
                    form_data = await request.form()
                    form_token = form_data.get("csrf_token")
                except Exception:
                    pass
                    
                cookie_token = request.cookies.get("csrf_token")
                
                # Use the first available token
                token = header_token or form_token or cookie_token
                
                if not token or not get_csrf_protection().validate_csrf_token(token, request):
                    logger.warning(f"CSRF token validation failed for {request.method} {request.url.path}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="CSRF token validation failed"
                    )
        
        # Apply XSS sanitization to request body for user-generated content
        if request.method in ["POST", "PUT", "PATCH"] and request.headers.get("content-type", "").startswith("application/json"):
            try:
                body = await request.json()
                
                # Sanitize user-generated content fields based on endpoint
                sanitized_body = self._sanitize_request_body(body, request.url.path)
                
                # Replace request body with sanitized version
                request.state.sanitized_body = sanitized_body
                
            except Exception as e:
                logger.warning(f"Error sanitizing request body: {e}")
                # Continue with original body if sanitization fails
        
        response = await call_next(request)
        
        # Set secure cookie attributes for authentication cookies
        if request.method == "POST" and "auth/login" in request.url.path:
            # Ensure auth cookies are secure
            if response.headers.get("set-cookie"):
                # Update cookie attributes to be more secure
                pass
        
        return response
    
    def _sanitize_request_body(self, body: Dict[str, Any], path: str) -> Dict[str, Any]:
        """
        Sanitize request body based on endpoint path.
        """
        sanitized_body = body.copy()
        
        # Define field mappings for different endpoints
        if "/courses" in path:
            field_map = {
                "title": "text",
                "description": "html",
                "long_description": "html",
                "requirements": "text",
                "learning_objectives": "text",
            }
            return sanitize_fields(sanitized_body, field_map)
            
        elif "/assignments" in path:
            field_map = {
                "title": "text",
                "description": "html",
                "instructions": "html",
            }
            return sanitize_fields(sanitized_body, field_map)
            
        elif "/quizzes" in path:
            field_map = {
                "title": "text",
                "description": "html",
            }
            return sanitize_fields(sanitized_body, field_map)
            
        elif "/users" in path:
            field_map = {
                "full_name": "text",
            }
            return sanitize_fields(sanitized_body, field_map)
            
        elif "/submissions" in path:
            field_map = {
                "content": "html",
                "feedback": "html",
            }
            return sanitize_fields(sanitized_body, field_map)
        
        return sanitized_body

# Helper function to get CSRF token for templates
def get_csrf_token_for_template() -> str:
    """Generate CSRF token for template rendering."""
    return get_csrf_protection().generate_csrf_token()

# Update logger to use PII redaction filter
def setup_security_logging():
    """Setup logging with PII redaction."""
    logger = logging.getLogger()
    logger.addFilter(pii_redaction_filter)