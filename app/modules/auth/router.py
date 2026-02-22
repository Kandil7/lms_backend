from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, oauth2_scheme, optional_oauth2_scheme
from app.core.exceptions import UnauthorizedException
from app.core.permissions import Role
from app.modules.auth.schemas import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginResponse,
    LogoutRequest,
    MessageResponse,
    MfaChallengeResponse,
    MfaCodeRequest,
    MfaDisableRequest,
    MfaEnableRequest,
    MfaLoginVerifyRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailConfirmRequest,
    VerifyEmailRequest,
)
from app.modules.auth.service import AuthService
from app.tasks.dispatcher import enqueue_task_with_fallback
from app.modules.users.schemas import UserCreate, UserLogin, UserResponse
from app.modules.users.services.user_service import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserService,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
PASSWORD_RESET_REQUEST_MESSAGE = "If the email is registered, a reset link has been sent"
EMAIL_VERIFICATION_REQUEST_MESSAGE = "If the email is registered, a verification link has been sent"
MFA_ENABLE_REQUEST_MESSAGE = "A verification code has been sent to your email"


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> AuthResponse:
    if payload.role != Role.STUDENT and not settings.ALLOW_PUBLIC_ROLE_REGISTRATION:
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
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
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
        verification_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/verify-email?token={verification_token}"
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
    payload: UserLogin,
    db: Session = Depends(get_db)
) -> LoginResponse:
    auth_service = AuthService(db)
    
    # Get client IP address for account lockout
    ip_address = request.client.host if request.client else "127.0.0.1"

    try:
        user, tokens, mfa_challenge = auth_service.login(payload.email, payload.password, ip_address=ip_address)
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

    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/token", response_model=TokenResponse, summary="OAuth2 token endpoint for Swagger Authorize")
def oauth_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenResponse:
    auth_service = AuthService(db)

    try:
        user, tokens, mfa_challenge = auth_service.login(form_data.username, form_data.password)
    except InvalidCredentialsError as exc:
        raise UnauthorizedException(str(exc)) from exc

    if mfa_challenge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is enabled for this account. Use /api/v1/auth/login then /api/v1/auth/login/mfa.",
        )

    return tokens


@router.post("/login/mfa", response_model=AuthResponse)
def verify_mfa_login(payload: MfaLoginVerifyRequest, db: Session = Depends(get_db)) -> AuthResponse:
    auth_service = AuthService(db)
    user, tokens = auth_service.verify_mfa_login(payload.challenge_token, payload.code)
    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/refresh", response_model=AuthResponse)
def refresh_tokens(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
    access_token: str | None = Depends(optional_oauth2_scheme),
) -> AuthResponse:
    auth_service = AuthService(db)
    tokens = auth_service.refresh_tokens(payload.refresh_token, previous_access_token=access_token)

    user = get_current_user(tokens.access_token, db)
    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db),
    access_token: str = Depends(oauth2_scheme),
) -> None:
    auth_service = AuthService(db)
    auth_service.logout(payload.refresh_token, access_token=access_token)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    auth_service = AuthService(db)
    reset_payload = auth_service.request_password_reset(payload.email)

    if reset_payload:
        email, full_name, reset_token = reset_payload
        reset_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/reset-password?token={reset_token}"
        enqueue_task_with_fallback(
            "app.tasks.email_tasks.send_password_reset_email",
            email=email,
            full_name=full_name,
            reset_token=reset_token,
            reset_url=reset_url,
        )

    return MessageResponse(message=PASSWORD_RESET_REQUEST_MESSAGE)


@router.post("/verify-email/request", response_model=MessageResponse)
def request_email_verification(payload: VerifyEmailRequest, db: Session = Depends(get_db)) -> MessageResponse:
    auth_service = AuthService(db)
    verification_payload = auth_service.request_email_verification(payload.email)

    if verification_payload:
        email, full_name, verification_token = verification_payload
        verification_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/verify-email?token={verification_token}"
        enqueue_task_with_fallback(
            "app.tasks.email_tasks.send_email_verification_email",
            email=email,
            full_name=full_name,
            verification_token=verification_token,
            verification_url=verification_url,
        )

    return MessageResponse(message=EMAIL_VERIFICATION_REQUEST_MESSAGE)


@router.post("/verify-email/confirm", response_model=MessageResponse)
def confirm_email_verification(payload: VerifyEmailConfirmRequest, db: Session = Depends(get_db)) -> MessageResponse:
    auth_service = AuthService(db)
    auth_service.confirm_email_verification(payload.token)
    return MessageResponse(message="Email has been verified successfully")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    auth_service = AuthService(db)
    auth_service.reset_password(payload.token, payload.new_password)
    return MessageResponse(message="Password has been reset successfully")


@router.post("/mfa/enable/request", response_model=MessageResponse)
def request_enable_mfa(
    payload: MfaEnableRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    auth_service = AuthService(db)
    email, full_name, code, expires_minutes = auth_service.request_enable_mfa(current_user, payload.password)

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


@router.post("/mfa/disable", response_model=MessageResponse)
def disable_mfa(
    payload: MfaDisableRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    auth_service = AuthService(db)
    auth_service.disable_mfa(current_user, payload.password)
    return MessageResponse(message="MFA has been disabled successfully")


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
