from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        # Comprehensive Content Security Policy for production
        # Note: In development, this should be less restrictive
        csp_policy = (
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com; "
            "connect-src 'self' https://api.lms.example.com https://*.lms.example.com; "
            "media-src 'self' https:; "
            "manifest-src 'self'; "
            "worker-src 'self'; "
            "form-action 'self'; "
            "upgrade-insecure-requests;"
        )
        response.headers.setdefault("Content-Security-Policy", csp_policy)

        if request.url.scheme == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

        return response
