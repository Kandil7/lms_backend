import ipaddress
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.permissions import Role
from app.modules.users.schemas import UserResponse


class AdminBase(BaseModel):
    """Base admin information"""
    security_level: str = Field(default="standard", pattern="^(standard|enhanced|maximum)$")
    mfa_required: bool = True
    ip_whitelist: list[str] = Field(default_factory=list)
    time_restrictions: dict = Field(default_factory=dict)
    emergency_contacts: list[dict] = Field(default_factory=list)


class AdminCreate(AdminBase):
    """Admin creation request"""
    user_id: UUID
    is_setup_complete: bool = False
    setup_completed_at: Optional[datetime] = None
    security_policy_accepted: bool = False
    security_policy_version: str = "1.0"
    last_security_review: Optional[datetime] = None
    security_health_score: int = 50


class AdminUpdate(AdminBase):
    """Admin profile update"""
    security_level: Optional[str] = Field(default=None, pattern="^(standard|enhanced|maximum)$")
    mfa_required: Optional[bool] = None
    ip_whitelist: Optional[list[str]] = None
    time_restrictions: Optional[dict] = None
    emergency_contacts: Optional[list[dict]] = None
    security_policy_accepted: Optional[bool] = None
    security_policy_version: Optional[str] = None
    last_security_review: Optional[datetime] = None
    security_health_score: Optional[int] = None


class AdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    security_level: str
    mfa_required: bool
    ip_whitelist: list[str]
    time_restrictions: dict
    emergency_contacts: list[dict]
    is_setup_complete: bool
    setup_completed_at: Optional[datetime] = None
    security_policy_accepted: bool
    security_policy_version: str
    last_security_review: Optional[datetime] = None
    security_health_score: int
    created_at: datetime
    updated_at: datetime


class AdminOnboardingStatus(BaseModel):
    """Track admin onboarding progress"""
    step: str = "account_setup"  # account_setup, security_config, permissions, verification, complete
    completed_steps: list[str] = Field(default_factory=list)
    current_step: str = "account_setup"
    total_steps: int = 5
    progress_percentage: int = 20
    is_complete: bool = False
    needs_security_config: bool = True
    security_policy_accepted: bool = False
    mfa_configured: bool = False
    emergency_contacts_configured: bool = False
    last_updated: datetime


class AdminSetupRequest(BaseModel):
    """Complete admin setup request"""
    email: EmailStr
    password: str = Field(min_length=12, max_length=128, description="Strong password required for admins")
    full_name: str = Field(min_length=2, max_length=255)
    role: Role = Role.ADMIN
    security_level: str = Field(default="enhanced", pattern="^(standard|enhanced|maximum)$")
    mfa_required: bool = True
    ip_whitelist: list[str] = Field(default_factory=list)
    time_restrictions: dict = Field(default_factory=dict)
    emergency_contacts: list[dict] = Field(default_factory=list)
    security_policy_accepted: bool = False
    security_policy_version: str = "1.0"

    @field_validator("ip_whitelist")
    @classmethod
    def validate_ip_whitelist(cls, value: list[str]) -> list[str]:
        for ip in value:
            try:
                ipaddress.ip_address(ip)
            except ValueError as exc:
                raise ValueError(f"Invalid IP address in ip_whitelist: {ip}") from exc
        return value

    @field_validator("time_restrictions")
    @classmethod
    def validate_time_restrictions(cls, value: dict) -> dict:
        if not value:
            return value

        start_hour = value.get("start_hour")
        end_hour = value.get("end_hour")
        days = value.get("days")

        if start_hour is not None and (not isinstance(start_hour, int) or not 0 <= start_hour <= 23):
            raise ValueError("time_restrictions.start_hour must be an integer between 0 and 23")
        if end_hour is not None and (not isinstance(end_hour, int) or not 0 <= end_hour <= 23):
            raise ValueError("time_restrictions.end_hour must be an integer between 0 and 23")
        if days is not None:
            valid_days = {
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            }
            if not isinstance(days, list) or any(day not in valid_days for day in days):
                raise ValueError("time_restrictions.days contains invalid values")

        return value

    @model_validator(mode="after")
    def validate_security_policy(self):
        if not self.security_policy_accepted:
            raise ValueError("security_policy_accepted must be true")
        return self


class AdminSecurityConfigRequest(BaseModel):
    """Admin security configuration"""
    mfa_method: str = Field(default="totp", pattern="^(totp|sms|email|hardware)$")
    ip_whitelist: list[str] = Field(default_factory=list)
    time_restrictions: dict = Field(default_factory=dict)
    require_password_change: bool = True
    password_expiry_days: int = Field(default=90, ge=30, le=365)
    session_timeout_minutes: int = Field(default=30, ge=5, le=120)
    geo_restrictions: list[str] = Field(default_factory=list)
    anomaly_detection_enabled: bool = True

    @field_validator("ip_whitelist")
    @classmethod
    def validate_ip_whitelist(cls, value: list[str]) -> list[str]:
        for ip in value:
            try:
                ipaddress.ip_address(ip)
            except ValueError as exc:
                raise ValueError(f"Invalid IP address in ip_whitelist: {ip}") from exc
        return value
