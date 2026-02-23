from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.permissions import Role
from app.modules.users.schemas import UserResponse


class InstructorBase(BaseModel):
    """Base instructor information"""
    bio: str = Field(min_length=10, max_length=2000)
    expertise: list[str] = Field(default_factory=list, min_length=1, max_length=10)
    teaching_experience_years: int = Field(ge=0, le=50)
    education_level: str = Field(max_length=100)
    institution: str = Field(max_length=255)


class InstructorCreate(InstructorBase):
    """Instructor creation request"""
    user_id: UUID
    is_verified: bool = False
    verification_status: str = "pending"  # pending, verified, rejected
    verification_notes: Optional[str] = None
    verification_document_url: Optional[str] = None
    verification_expires_at: Optional[datetime] = None


class InstructorUpdate(InstructorBase):
    """Instructor profile update"""
    bio: Optional[str] = Field(default=None, min_length=10, max_length=2000)
    expertise: Optional[list[str]] = Field(default=None, min_length=1, max_length=10)
    teaching_experience_years: Optional[int] = Field(default=None, ge=0, le=50)
    education_level: Optional[str] = Field(default=None, max_length=100)
    institution: Optional[str] = Field(default=None, max_length=255)
    verification_status: Optional[str] = None
    verification_notes: Optional[str] = None
    verification_document_url: Optional[str] = None
    verification_expires_at: Optional[datetime] = None


class InstructorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    bio: str
    expertise: list[str]
    teaching_experience_years: int
    education_level: str
    institution: str
    is_verified: bool
    verification_status: str
    verification_notes: Optional[str] = None
    verification_document_url: Optional[str] = None
    verification_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class InstructorOnboardingStatus(BaseModel):
    """Track instructor onboarding progress"""
    step: str = "account_setup"  # account_setup, profile, verification, complete
    completed_steps: list[str] = Field(default_factory=list)
    current_step: str = "account_setup"
    total_steps: int = 4
    progress_percentage: int = 25
    is_complete: bool = False
    needs_verification: bool = True
    verification_required: bool = True
    verification_submitted: bool = False
    verification_approved: bool = False
    last_updated: datetime


class InstructorRegistrationRequest(BaseModel):
    """Complete instructor registration request"""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    role: Role = Role.INSTRUCTOR
    bio: str = Field(min_length=10, max_length=2000)
    expertise: list[str] = Field(default_factory=list, min_length=1, max_length=10)
    teaching_experience_years: int = Field(ge=0, le=50)
    education_level: str = Field(max_length=100)
    institution: str = Field(max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    website: Optional[str] = Field(default=None, max_length=255)
    social_media: Optional[dict] = Field(default_factory=dict)


class InstructorVerificationRequest(BaseModel):
    """Instructor verification submission"""
    document_type: str = Field(max_length=50)  # resume, certificate, ID, etc.
    document_url: str = Field(max_length=1000)
    verification_notes: Optional[str] = None
    consent_to_verify: bool = True