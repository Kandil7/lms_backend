"""
Cookie-based authentication router for secure HttpOnly token management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.auth.service_cookie import CookieAuthService
from app.modules.users.schemas import UserResponse
from app.tasks.dispatcher import enqueue_task_with_fallback


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login-cookie", status_code=status.HTTP_200_OK)
def login_with_cookies(
    request: Request,
    response: Response,
    payload: dict,  # Using dict for flexibility with different login methods
    db: Session = Depends(get_db),
) -> None:
    """Login and set tokens as HttpOnly cookies"""
    auth_service = CookieAuthService(db)
    
    # Extract email and password from payload (support both traditional and MFA flows)
    email = payload.get("email")
    password = payload.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    try:
        auth_service.login_with_cookies(email, password, request, response)
    except Exception as e:
        # Re-raise as HTTP exception to maintain consistent error handling
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.post("/refresh-cookie", status_code=status.HTTP_200_OK)
def refresh_with_cookies(
    request: Request,
    response: Response,
    payload: dict | None = None,
    db: Session = Depends(get_db),
) -> None:
    """Refresh tokens and set as HttpOnly cookies"""
    auth_service = CookieAuthService(db)
    refresh_token = None
    if payload:
        refresh_token = payload.get("refresh_token")
    if not refresh_token:
        refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token required")
    
    try:
        auth_service.refresh_with_cookies(refresh_token, request, response)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.post("/logout-cookie", status_code=status.HTTP_200_OK)
def logout_with_cookies(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> None:
    """Logout and delete HttpOnly cookies"""
    auth_service = CookieAuthService(db)
    refresh_token = request.cookies.get("refresh_token")
    access_token = request.cookies.get("access_token")
    auth_service.logout_with_cookies(
        request=request,
        response=response,
        refresh_token=refresh_token,
        access_token=access_token,
    )


# Additional endpoints for token info (to allow frontend to read tokens via API)
@router.get("/token-info", status_code=status.HTTP_200_OK)
def get_token_info(
    current_user=Depends(get_current_user),
) -> dict:
    """Get current token information (for frontend to read tokens via API)"""
    # This endpoint should be protected and only return minimal info
    # In production, this would be more restricted
    return {
        "access_token": "available_via_cookie",
        "refresh_token": "available_via_cookie",
        "user_id": str(current_user.id),
        "role": current_user.role,
    }
