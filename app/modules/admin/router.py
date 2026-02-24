from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppException, NotFoundException
from app.core.permissions import Role
from app.core.dependencies import require_roles
from app.modules.auth.service import AuthService
from app.modules.admin.schemas import (
    AdminSetupRequest,
    AdminSecurityConfigRequest,
    AdminOnboardingStatus,
    AdminUpdate,
)
from app.modules.admin.service import AdminService
from app.modules.users.schemas import UserResponse
from app.modules.auth.schemas import TokenResponse
from app.core.dependencies import get_current_user


router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/setup", status_code=status.HTTP_201_CREATED)
@require_roles(Role.ADMIN)
async def setup_admin_account(
    setup_data: AdminSetupRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Setup a new admin account with enhanced security"""
    admin_service = AdminService(db)

    try:
        result = admin_service.create_admin_from_setup(setup_data)

        return {
            "message": "Admin account created successfully",
            "user": UserResponse.model_validate(result["user"]),
            "admin": result["admin"],
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
@require_roles(Role.ADMIN)
async def get_admin_onboarding_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current admin onboarding status"""
    admin_service = AdminService(db)
    return admin_service.get_onboarding_status(current_user["id"])


@router.put("/profile", response_model=dict)
@require_roles(Role.ADMIN)
async def update_admin_profile(
    profile_data: AdminUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update admin profile information"""
    admin_service = AdminService(db)

    try:
        admin = admin_service.update_admin_profile(current_user["id"], profile_data)
        return {
            "message": "Admin profile updated successfully",
            "admin": admin,
            "onboarding_status": admin_service.get_onboarding_status(current_user["id"]),
        }
    except AppException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update admin profile. Please try again.",
        )


@router.post("/security-config", response_model=dict)
@require_roles(Role.ADMIN)
async def configure_admin_security(
    security_config: AdminSecurityConfigRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Configure admin security settings"""
    admin_service = AdminService(db)

    try:
        admin = admin_service.configure_admin_security(current_user["id"], security_config)
        return {
            "message": "Admin security configuration updated successfully",
            "admin": admin,
            "onboarding_status": admin_service.get_onboarding_status(current_user["id"]),
        }
    except AppException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to configure admin security. Please try again.",
        )


@router.post("/complete-setup", response_model=dict)
@require_roles(Role.ADMIN)
async def complete_admin_setup(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Complete admin setup process"""
    admin_service = AdminService(db)

    try:
        admin = admin_service.complete_admin_setup(current_user["id"])
        return {
            "message": "Admin setup completed successfully",
            "admin": admin,
            "onboarding_status": admin_service.get_onboarding_status(current_user["id"]),
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
    # This endpoint should only be used during initial system setup
    # In production, this should be protected by environment variables or special tokens

    if not settings.DEBUG and not settings.ALLOW_INITIAL_ADMIN_CREATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Initial admin creation is disabled in production",
        )

    admin_service = AdminService(db)

    try:
        result = admin_service.create_admin_from_setup(setup_data)

        return {
            "message": "Initial admin account created successfully",
            "user": UserResponse.model_validate(result["user"]),
            "admin": result["admin"],
            "onboarding_status": result["onboarding_status"],
            "setup_expires_at": result["setup_expires_at"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create initial admin account: {str(e)}",
        )
