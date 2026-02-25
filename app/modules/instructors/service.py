from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.instructors.models import Instructor
from app.modules.instructors.schemas import (
    InstructorCreate,
    InstructorUpdate,
    InstructorRegistrationRequest,
    InstructorVerificationRequest,
)
from app.modules.users.schemas import UserCreate
from app.modules.users.services.user_service import UserService
from app.modules.auth.service import AuthService


class InstructorService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_service = UserService(db)
        self.auth_service = AuthService(db)

    def create_instructor_from_registration(
        self, registration_data: InstructorRegistrationRequest
    ) -> dict:
        """Create instructor account with complete registration flow"""
        try:
            # Step 1: Create user account
            user_create_data = UserCreate(
                email=registration_data.email,
                full_name=registration_data.full_name,
                role=registration_data.role,
                password=registration_data.password,
            )

            user = self.user_service.create_user(user_create_data)

            # Step 2: Create instructor profile
            instructor_data = InstructorCreate(
                user_id=user.id,
                bio=registration_data.bio,
                expertise=registration_data.expertise,
                teaching_experience_years=registration_data.teaching_experience_years,
                education_level=registration_data.education_level,
                institution=registration_data.institution,
                is_verified=False,
                verification_status="pending",
            )

            instructor = Instructor(**instructor_data.model_dump())
            self.db.add(instructor)
            self.db.commit()
            self.db.refresh(instructor)

            # Step 3: Generate verification token and set expiration
            verification_expires_at = datetime.utcnow() + timedelta(days=7)
            instructor.verification_expires_at = verification_expires_at
            self.db.commit()

            return {
                "user": user,
                "instructor": instructor,
                "verification_token": self._generate_verification_token(user.id),
                "verification_expires_at": verification_expires_at,
            }

        except Exception as e:
            self.db.rollback()
            raise e

    def get_instructor_by_user_id(self, user_id: UUID) -> Optional[Instructor]:
        """Get instructor by user ID"""
        return self.db.query(Instructor).filter(Instructor.user_id == user_id).first()

    def update_instructor_profile(self, user_id: UUID, update_data: InstructorUpdate) -> Instructor:
        """Update instructor profile"""
        instructor = self.get_instructor_by_user_id(user_id)
        if not instructor:
            raise ValueError("Instructor not found")

        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(instructor, field, value)

        instructor.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(instructor)
        return instructor

    def submit_verification(
        self, user_id: UUID, verification_data: InstructorVerificationRequest
    ) -> Instructor:
        """Submit instructor verification"""
        instructor = self.get_instructor_by_user_id(user_id)
        if not instructor:
            raise ValueError("Instructor not found")

        instructor.verification_status = "submitted"
        instructor.verification_document_url = verification_data.document_url
        instructor.verification_notes = verification_data.verification_notes
        instructor.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(instructor)
        return instructor

    def approve_verification(self, instructor_id: UUID, admin_notes: str = "") -> Instructor:
        """Approve instructor verification (admin only)"""
        instructor = self.db.query(Instructor).filter(Instructor.id == instructor_id).first()
        if not instructor:
            raise ValueError("Instructor not found")

        instructor.is_verified = True
        instructor.verification_status = "verified"
        instructor.verification_notes = f"Approved by admin. {admin_notes}"
        instructor.verification_expires_at = None
        instructor.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(instructor)
        return instructor

    def reject_verification(self, instructor_id: UUID, rejection_reason: str) -> Instructor:
        """Reject instructor verification (admin only)"""
        instructor = self.db.query(Instructor).filter(Instructor.id == instructor_id).first()
        if not instructor:
            raise ValueError("Instructor not found")

        instructor.verification_status = "rejected"
        instructor.verification_notes = rejection_reason
        instructor.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(instructor)
        return instructor

    def get_onboarding_status(self, user_id: UUID) -> dict:
        """Get instructor onboarding status"""
        user = self.user_service.get_user(user_id)
        instructor = self.get_instructor_by_user_id(user_id)

        if not instructor:
            return {
                "step": "account_setup",
                "completed_steps": [],
                "current_step": "account_setup",
                "total_steps": 4,
                "progress_percentage": 25,
                "is_complete": False,
                "needs_verification": True,
                "verification_required": True,
                "verification_submitted": False,
                "verification_approved": False,
                "last_updated": datetime.utcnow(),
            }

        completed_steps = ["account_setup"]
        if instructor.bio and instructor.expertise:
            completed_steps.append("profile")

        if instructor.verification_status == "submitted":
            completed_steps.append("verification")

        if instructor.is_verified:
            completed_steps.append("complete")

        progress_percentage = (len(completed_steps) / 4) * 100
        is_complete = instructor.is_verified

        return {
            "step": "complete"
            if is_complete
            else "verification"
            if "verification" in completed_steps
            else "profile"
            if "profile" in completed_steps
            else "account_setup",
            "completed_steps": completed_steps,
            "current_step": completed_steps[-1] if completed_steps else "account_setup",
            "total_steps": 4,
            "progress_percentage": int(progress_percentage),
            "is_complete": is_complete,
            "needs_verification": not instructor.is_verified,
            "verification_required": True,
            "verification_submitted": instructor.verification_status == "submitted",
            "verification_approved": instructor.is_verified,
            "last_updated": datetime.utcnow(),
        }

    def _generate_verification_token(self, user_id: UUID) -> str:
        """Generate verification token for instructor"""
        # In production, use JWT or secure token generation
        return f"instructor_verify_{user_id}_{datetime.utcnow().timestamp()}"
