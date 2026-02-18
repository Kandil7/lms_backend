from pydantic import BaseModel, EmailStr, Field

from app.modules.users.schemas import UserResponse


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse


class MfaChallengeResponse(BaseModel):
    mfa_required: bool = True
    challenge_token: str
    expires_in_seconds: int
    message: str = "MFA verification required"


LoginResponse = AuthResponse | MfaChallengeResponse


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class MessageResponse(BaseModel):
    message: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr


class VerifyEmailConfirmRequest(BaseModel):
    token: str


class MfaEnableRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class MfaCodeRequest(BaseModel):
    code: str = Field(min_length=4, max_length=12)


class MfaDisableRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class MfaLoginVerifyRequest(BaseModel):
    challenge_token: str
    code: str = Field(min_length=4, max_length=12)
