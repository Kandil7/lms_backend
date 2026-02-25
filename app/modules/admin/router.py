from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.permissions import Role
from app.core.dependencies import require_admin_setup_complete, require_roles
from app.modules.admin.models import Admin
from app.modules.admin.schemas import (
    AdminResponse,
    AdminOnboardingStatus,
    AdminSecurityConfigRequest,
    AdminSetupRequest,
    AdminUpdate,
)
from app.modules.admin.service import AdminService
from app.modules.users.schemas import UserResponse


router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/setup", status_code=status.HTTP_201_CREATED)
async def setup_admin_account(
    setup_data: AdminSetupRequest,
    _: object = Depends(require_admin_setup_complete),
    db: Session = Depends(get_db),
):
    """Setup a new admin account with enhanced security"""
    admin_service = AdminService(db)

    try:
        result = admin_service.create_admin_from_setup(setup_data)

        return {
            "message": "Admin account created successfully",
            "user": UserResponse.model_validate(result["user"]),
            "admin": AdminResponse.model_validate(result["admin"]),
            "onboarding_status": result["onboarding_status"],
            "setup_expires_at": result["setup_expires_at"],
        }
    except AppException:
        raise
    except Exception as e:
        # Log the actual error internally but don't expose details to client
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create admin account. Please try again.",
        )


@router.get("/onboarding-status", response_model=AdminOnboardingStatus)
async def get_admin_onboarding_status(
    current_user=Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    """Get current admin onboarding status"""
    admin_service = AdminService(db)
    return admin_service.get_onboarding_status(current_user.id)


@router.put("/profile", response_model=dict)
async def update_admin_profile(
    profile_data: AdminUpdate,
    current_user=Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    """Update admin profile information"""
    admin_service = AdminService(db)

    try:
        admin = admin_service.update_admin_profile(current_user.id, profile_data)
        return {
            "message": "Admin profile updated successfully",
            "admin": AdminResponse.model_validate(admin),
            "onboarding_status": admin_service.get_onboarding_status(current_user.id),
        }
    except AppException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update admin profile. Please try again.",
        )


@router.post("/security-config", response_model=dict)
async def configure_admin_security(
    security_config: AdminSecurityConfigRequest,
    current_user=Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    """Configure admin security settings"""
    admin_service = AdminService(db)

    try:
        admin = admin_service.configure_admin_security(current_user.id, security_config)
        return {
            "message": "Admin security configuration updated successfully",
            "admin": AdminResponse.model_validate(admin),
            "onboarding_status": admin_service.get_onboarding_status(current_user.id),
        }
    except AppException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to configure admin security. Please try again.",
        )


@router.post("/complete-setup", response_model=dict)
async def complete_admin_setup(
    current_user=Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    """Complete admin setup process"""
    admin_service = AdminService(db)

    try:
        admin = admin_service.complete_admin_setup(current_user.id)
        return {
            "message": "Admin setup completed successfully",
            "admin": AdminResponse.model_validate(admin),
            "onboarding_status": admin_service.get_onboarding_status(current_user.id),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to complete admin setup: {str(e)}",
        )


# Special endpoint for initial admin creation (requires special permissions)
@router.post("/create-initial", status_code=status.HTTP_201_CREATED)
async def create_initial_admin(
    setup_data: AdminSetupRequest,
    db: Session = Depends(get_db),
):
    """Create the first admin account (bypasses role requirements)"""
    if settings.ENVIRONMENT == "production" and not settings.ALLOW_INITIAL_ADMIN_CREATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Initial admin creation is disabled",
        )

    if settings.ENVIRONMENT == "production":
        existing_admin = db.query(Admin).first()
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Initial admin already exists",
            )

    admin_service = AdminService(db)

    try:
        result = admin_service.create_admin_from_setup(setup_data)

        return {
            "message": "Initial admin account created successfully",
            "user": UserResponse.model_validate(result["user"]),
            "admin": AdminResponse.model_validate(result["admin"]),
            "onboarding_status": result["onboarding_status"],
            "setup_expires_at": result["setup_expires_at"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create initial admin account: {str(e)}",
        )
