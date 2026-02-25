"""
Cookie-based authentication router for secure HttpOnly token management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.cookie_utils import delete_http_only_cookie, set_http_only_cookie
from app.core.database import get_db
from app.core.dependencies import (
    get_current_user,
    get_current_user_optional,
    optional_oauth2_scheme,
)
from app.core.exceptions import UnauthorizedException
from app.core.permissions import Role
from app.modules.auth.router import _get_client_ip
from app.modules.auth.schemas import (
    AuthResponse,
    LoginResponse,
    MessageResponse,
    MfaChallengeResponse,
    MfaCodeRequest,
    MfaEnableRequest,
    MfaLoginVerifyRequest,
    RefreshTokenRequest,
)
from app.modules.auth.service import AuthService
from app.modules.users.schemas import UserCreate, UserLogin, UserResponse
from app.modules.users.services.user_service import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserService,
)
from app.tasks.dispatcher import enqueue_task_with_fallback


router = APIRouter(prefix="/auth", tags=["authentication"])
MFA_ENABLE_REQUEST_MESSAGE = "A verification code has been sent to your email"


def _set_auth_cookies(response: Response, *, access_token: str, refresh_token: str) -> None:
    set_http_only_cookie(
        response=response,
        name="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="strict",
        secure=settings.ENVIRONMENT != "development",
    )
    set_http_only_cookie(
        response=response,
        name="refresh_token",
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="strict",
        secure=settings.ENVIRONMENT != "development",
    )


def _delete_auth_cookies(response: Response) -> None:
    delete_http_only_cookie(response=response, name="access_token")
    delete_http_only_cookie(response=response, name="refresh_token")


@router.post(
    "/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> AuthResponse:
    if payload.role != Role.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration is limited to student accounts",
        )

    user_service = UserService(db)
    auth_service = AuthService(db)

    try:
        user = user_service.create_user(payload, commit=False)
        tokens = auth_service._issue_tokens(user.id, user.role)
        db.commit()
        db.refresh(user)
    except UserAlreadyExistsError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except Exception:
        db.rollback()
        raise

    enqueue_task_with_fallback(
        "app.tasks.email_tasks.send_welcome_email",
        email=user.email,
        full_name=user.full_name,
    )
    verification_payload = auth_service.request_email_verification(user.email)
    if verification_payload:
        email, full_name, verification_token = verification_payload
        verification_url = (
            f"{settings.FRONTEND_BASE_URL.rstrip('/')}/verify-email?token={verification_token}"
        )
        enqueue_task_with_fallback(
            "app.tasks.email_tasks.send_email_verification_email",
            email=email,
            full_name=full_name,
            verification_token=verification_token,
            verification_url=verification_url,
        )

    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/login", response_model=LoginResponse)
def login(
    request: Request,
    response: Response,
    payload: UserLogin,
    db: Session = Depends(get_db),
) -> LoginResponse:
    auth_service = AuthService(db)
    ip_address = _get_client_ip(request)

    try:
        user, tokens, mfa_challenge = auth_service.login(
            payload.email, payload.password, ip_address=ip_address
        )
    except InvalidCredentialsError as exc:
        raise UnauthorizedException(str(exc)) from exc

    if mfa_challenge:
        enqueue_task_with_fallback(
            "app.tasks.email_tasks.send_mfa_login_code_email",
            email=user.email,
            full_name=user.full_name,
            code=mfa_challenge["code"],
            expires_minutes=settings.MFA_LOGIN_CODE_EXPIRE_MINUTES,
        )
        return MfaChallengeResponse(
            challenge_token=mfa_challenge["challenge_token"],
            expires_in_seconds=mfa_challenge["expires_in_seconds"],
        )

    if tokens is None:
        raise UnauthorizedException("Authentication failed")

    _set_auth_cookies(
        response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )
    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest | None = None,
    db: Session = Depends(get_db),
    access_token: str | None = Depends(optional_oauth2_scheme),
) -> dict:
    refresh_token = payload.refresh_token if payload else request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token required")

    auth_service = AuthService(db)
    tokens = auth_service.refresh_tokens(
        refresh_token, previous_access_token=access_token
    )
    _set_auth_cookies(
        response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )

    user = get_current_user_optional(token=tokens.access_token, db=db)
    if not user:
        raise UnauthorizedException("Could not validate credentials")

    return {
        "access_token": tokens.access_token,
        "token_type": tokens.token_type,
        "user": UserResponse.model_validate(user).model_dump(mode="json"),
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest | None = None,
    db: Session = Depends(get_db),
    access_token: str | None = Depends(optional_oauth2_scheme),
) -> None:
    refresh_token = payload.refresh_token if payload else request.cookies.get("refresh_token")
    auth_service = AuthService(db)

    if refresh_token:
        try:
            auth_service.logout(refresh_token, access_token=access_token)
        except UnauthorizedException:
            pass

    _delete_auth_cookies(response)


@router.post("/login/mfa", status_code=status.HTTP_200_OK)
def verify_mfa_login(
    payload: MfaLoginVerifyRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    auth_service = AuthService(db)
    user, tokens = auth_service.verify_mfa_login(payload.challenge_token, payload.code)

    _set_auth_cookies(
        response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )

    # Keep refresh token only in cookie for this endpoint.
    return {
        "user": UserResponse.model_validate(user).model_dump(mode="json"),
        "tokens": {
            "access_token": tokens.access_token,
            "token_type": tokens.token_type,
            "expires_in": tokens.expires_in,
        },
    }


@router.post("/mfa/enable/request", response_model=MessageResponse)
def request_enable_mfa(
    payload: MfaEnableRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    auth_service = AuthService(db)
    email, full_name, code, expires_minutes = auth_service.request_enable_mfa(
        current_user, payload.password
    )

    if code:
        enqueue_task_with_fallback(
            "app.tasks.email_tasks.send_mfa_setup_code_email",
            email=email,
            full_name=full_name,
            code=code,
            expires_minutes=expires_minutes,
        )

    return MessageResponse(message=MFA_ENABLE_REQUEST_MESSAGE)


@router.post("/mfa/enable/confirm", response_model=MessageResponse)
def confirm_enable_mfa(
    payload: MfaCodeRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    auth_service = AuthService(db)
    auth_service.confirm_enable_mfa(current_user, payload.code)
    return MessageResponse(message="MFA has been enabled successfully")


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/login-cookie", status_code=status.HTTP_200_OK)
def login_with_cookies(
    request: Request,
    response: Response,
    payload: dict,  # Using dict for flexibility with different login methods
    db: Session = Depends(get_db),
) -> None:
    """Login and set tokens as HttpOnly cookies"""
    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    # Backward-compatible alias.
    _ = login(
        request=request,
        response=response,
        payload=UserLogin(email=email, password=password),
        db=db,
    )


@router.post("/refresh-cookie", status_code=status.HTTP_200_OK)
def refresh_with_cookies(
    request: Request,
    response: Response,
    payload: dict | None = None,
    db: Session = Depends(get_db),
) -> None:
    """Refresh tokens and set as HttpOnly cookies"""
    refresh_payload = (
        RefreshTokenRequest(refresh_token=payload["refresh_token"])
        if payload and payload.get("refresh_token")
        else None
    )
    _ = refresh(
        request=request,
        response=response,
        payload=refresh_payload,
        db=db,
        access_token=None,
    )


@router.post("/logout-cookie", status_code=status.HTTP_200_OK)
def logout_with_cookies(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> None:
    """Logout and delete HttpOnly cookies"""
    logout(
        request=request,
        response=response,
        payload=None,
        db=db,
        access_token=request.cookies.get("access_token"),
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
