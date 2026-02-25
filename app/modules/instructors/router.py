from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.config import settings
from app.core.database import get_db
from app.core.permissions import Role
from app.core.dependencies import require_roles, get_current_user
from app.modules.auth.service import AuthService
from app.modules.instructors.schemas import (
    InstructorRegistrationRequest,
    InstructorUpdate,
    InstructorVerificationRequest,
    InstructorOnboardingStatus,
)
from app.modules.instructors.service import InstructorService
from app.modules.users.schemas import UserResponse
from app.modules.auth.schemas import TokenResponse


router = APIRouter(prefix="/instructors", tags=["instructors"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_instructor(
    registration_data: InstructorRegistrationRequest,
    db: Session = Depends(get_db),
):
    """Register a new instructor with complete onboarding flow"""
    instructor_service = InstructorService(db)
    
    try:
        result = instructor_service.create_instructor_from_registration(registration_data)
        
        # Return success response with onboarding status
        return {
            "message": "Instructor account created successfully",
            "user": UserResponse.model_validate(result["user"]),
            "onboarding_status": instructor_service.get_onboarding_status(result["user"].id),
            "verification_required": True,
            "verification_expires_at": result["verification_expires_at"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create instructor account: {str(e)}",
        )


@router.get("/onboarding-status", response_model=InstructorOnboardingStatus)
async def get_instructor_onboarding_status(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current instructor onboarding status"""
    instructor_service = InstructorService(db)
    return instructor_service.get_onboarding_status(current_user.id)


@router.put("/profile", response_model=dict)
async def update_instructor_profile(
    profile_data: InstructorUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update instructor profile information"""
    instructor_service = InstructorService(db)
    
    try:
        instructor = instructor_service.update_instructor_profile(
            current_user.id, profile_data
        )
        return {
            "message": "Instructor profile updated successfully",
            "instructor": instructor,
            "onboarding_status": instructor_service.get_onboarding_status(current_user.id),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update instructor profile: {str(e)}",
        )


@router.post("/verify", response_model=dict)
async def submit_instructor_verification(
    verification_data: InstructorVerificationRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit instructor verification documentation"""
    instructor_service = InstructorService(db)
    
    try:
        instructor = instructor_service.submit_verification(
            current_user.id, verification_data
        )
        return {
            "message": "Verification submitted successfully",
            "instructor": instructor,
            "onboarding_status": instructor_service.get_onboarding_status(current_user.id),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to submit verification: {str(e)}",
        )


# Admin endpoints for verification approval/rejection
@router.post("/verify/approve/{instructor_id}")
async def approve_instructor_verification(
    instructor_id: str,
    admin_notes: str = "",
    _: object = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    """Approve instructor verification (admin only)"""
    instructor_service = InstructorService(db)

    try:
        # Convert string UUID to UUID object
        instructor_uuid = UUID(instructor_id)
        instructor = instructor_service.approve_verification(instructor_uuid, admin_notes)
        return {
            "message": "Instructor verification approved",
            "instructor": instructor,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to approve verification: {str(e)}",
        )


@router.post("/verify/reject/{instructor_id}")
async def reject_instructor_verification(
    instructor_id: str,
    rejection_reason: str,
    _: object = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    """Reject instructor verification (admin only)"""
    instructor_service = InstructorService(db)

    try:
        # Convert string UUID to UUID object
        instructor_uuid = UUID(instructor_id)
        instructor = instructor_service.reject_verification(instructor_uuid, rejection_reason)
        return {
            "message": "Instructor verification rejected",
            "instructor": instructor,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to reject verification: {str(e)}",
        )
