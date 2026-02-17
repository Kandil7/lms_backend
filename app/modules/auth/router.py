from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import UnauthorizedException
from app.modules.auth.schemas import AuthResponse, LogoutRequest, RefreshTokenRequest
from app.modules.auth.service import AuthService
from app.modules.users.schemas import UserCreate, UserLogin, UserResponse
from app.modules.users.services.user_service import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserService,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> AuthResponse:
    user_service = UserService(db)
    auth_service = AuthService(db)

    try:
        user = user_service.create_user(payload)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    tokens = auth_service._issue_tokens(user.id, user.role)
    db.commit()
    db.refresh(user)
    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/login", response_model=AuthResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> AuthResponse:
    auth_service = AuthService(db)

    try:
        user, tokens = auth_service.login(payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise UnauthorizedException(str(exc)) from exc

    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/refresh", response_model=AuthResponse)
def refresh_tokens(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> AuthResponse:
    auth_service = AuthService(db)
    tokens = auth_service.refresh_tokens(payload.refresh_token)

    user = get_current_user(tokens.access_token, db)
    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> None:
    auth_service = AuthService(db)
    auth_service.logout(payload.refresh_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
