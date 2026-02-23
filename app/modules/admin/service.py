from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.admin.models import Admin
from app.modules.admin.schemas import (
    AdminCreate,
    AdminUpdate,
    AdminSetupRequest,
    AdminSecurityConfigRequest,
    AdminOnboardingStatus,
)
from app.modules.users.service import UserService
from app.modules.auth.service import AuthService
from app.modules.users.models import User
from app.core.permissions import Role


class AdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_service = UserService(db)
        self.auth_service = AuthService(db)

    def create_admin_from_setup(
        self, setup_data: AdminSetupRequest
    ) -> dict:
        """Create admin account with enhanced security setup"""
        try:
            # Step 1: Create user account with strict validation
            if len(setup_data.password) < 12:
                raise ValueError("Admin passwords must be at least 12 characters")
            
            user_create_data = {
                "email": setup_data.email,
                "full_name": setup_data.full_name,
                "role": setup_data.role,
                "password": setup_data.password,
            }
            
            user = self.user_service.create_user(user_create_data)
            
            # Step 2: Create admin profile with enhanced security
            admin_data = AdminCreate(
                user_id=user.id,
                security_level=setup_data.security_level,
                mfa_required=setup_data.mfa_required,
                ip_whitelist=setup_data.ip_whitelist,
                time_restrictions=setup_data.time_restrictions,
                emergency_contacts=setup_data.emergency_contacts,
                is_setup_complete=False,
                security_policy_accepted=setup_data.security_policy_accepted,
                security_policy_version=setup_data.security_policy_version,
            )
            
            admin = Admin(**admin_data.model_dump())
            self.db.add(admin)
            self.db.commit()
            self.db.refresh(admin)
            
            # Step 3: Generate setup token and set expiration
            setup_expires_at = datetime.utcnow() + timedelta(hours=24)
            
            return {
                "user": user,
                "admin": admin,
                "setup_token": self._generate_setup_token(user.id),
                "setup_expires_at": setup_expires_at,
                "onboarding_status": self.get_onboarding_status(user.id),
            }
            
        except Exception as e:
            self.db.rollback()
            raise e

    def get_admin_by_user_id(self, user_id: UUID) -> Optional[Admin]:
        """Get admin by user ID"""
        return self.db.query(Admin).filter(Admin.user_id == user_id).first()

    def update_admin_profile(
        self, user_id: UUID, update_data: AdminUpdate
    ) -> Admin:
        """Update admin profile"""
        admin = self.get_admin_by_user_id(user_id)
        if not admin:
            raise ValueError("Admin not found")
        
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(admin, field, value)
        
        admin.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def configure_admin_security(
        self, user_id: UUID, security_config: AdminSecurityConfigRequest
    ) -> Admin:
        """Configure admin security settings"""
        admin = self.get_admin_by_user_id(user_id)
        if not admin:
            raise ValueError("Admin not found")
        
        # Update security configuration
        admin.mfa_required = True  # Always require MFA for admins
        admin.ip_whitelist = security_config.ip_whitelist
        admin.time_restrictions = security_config.time_restrictions
        admin.security_health_score = self._calculate_security_score(security_config)
        
        # Update other security settings
        if hasattr(admin, 'security_level'):
            admin.security_level = security_config.mfa_method == "hardware" and "maximum" or "enhanced"
        
        admin.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def complete_admin_setup(self, user_id: UUID) -> Admin:
        """Complete admin setup process"""
        admin = self.get_admin_by_user_id(user_id)
        if not admin:
            raise ValueError("Admin not found")
        
        admin.is_setup_complete = True
        admin.setup_completed_at = datetime.utcnow()
        admin.security_health_score = self._calculate_security_score({
            "mfa_method": "totp",
            "ip_whitelist": admin.ip_whitelist,
            "time_restrictions": admin.time_restrictions,
            "require_password_change": True,
            "password_expiry_days": 90,
            "session_timeout_minutes": 30,
            "geo_restrictions": [],
            "anomaly_detection_enabled": True,
        })
        
        admin.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def get_onboarding_status(self, user_id: UUID) -> AdminOnboardingStatus:
        """Get admin onboarding status"""
        user = self.user_service.get_user_by_id(user_id)
        admin = self.get_admin_by_user_id(user_id)
        
        if not admin:
            return AdminOnboardingStatus(
                step="account_setup",
                completed_steps=[],
                current_step="account_setup",
                total_steps=5,
                progress_percentage=20,
                is_complete=False,
                needs_security_config=True,
                security_policy_accepted=False,
                mfa_configured=False,
                emergency_contacts_configured=False,
                last_updated=datetime.utcnow(),
            )
        
        completed_steps = ["account_setup"]
        if admin.security_policy_accepted:
            completed_steps.append("security_config")
        if admin.mfa_required:
            completed_steps.append("permissions")
        if admin.emergency_contacts:
            completed_steps.append("verification")
        
        if admin.is_setup_complete:
            completed_steps.append("complete")
        
        progress_percentage = (len(completed_steps) / 5) * 100
        is_complete = admin.is_setup_complete
        
        return AdminOnboardingStatus(
            step="complete" if is_complete else "verification" if "verification" in completed_steps else "permissions" if "permissions" in completed_steps else "security_config" if "security_config" in completed_steps else "account_setup",
            completed_steps=completed_steps,
            current_step=completed_steps[-1] if completed_steps else "account_setup",
            total_steps=5,
            progress_percentage=int(progress_percentage),
            is_complete=is_complete,
            needs_security_config=not admin.security_policy_accepted,
            security_policy_accepted=admin.security_policy_accepted,
            mfa_configured=admin.mfa_required,
            emergency_contacts_configured=bool(admin.emergency_contacts),
            last_updated=datetime.utcnow(),
        )

    def _generate_setup_token(self, user_id: UUID) -> str:
        """Generate setup token for admin"""
        return f"admin_setup_{user_id}_{datetime.utcnow().timestamp()}"

    def _calculate_security_score(self, config: dict) -> int:
        """Calculate security health score based on configuration"""
        score = 50
        
        # MFA requirement (always required for admins)
        score += 20
        
        # IP whitelisting
        if config.get('ip_whitelist') and len(config['ip_whitelist']) > 0:
            score += 15
        
        # Time restrictions
        if config.get('time_restrictions') and config['time_restrictions']:
            score += 10
        
        # Password expiry
        if config.get('password_expiry_days', 90) <= 90:
            score += 5
        
        # Session timeout
        if config.get('session_timeout_minutes', 30) <= 60:
            score += 5
        
        # Geo restrictions
        if config.get('geo_restrictions') and len(config['geo_restrictions']) > 0:
            score += 5
        
        # Anomaly detection
        if config.get('anomaly_detection_enabled', True):
            score += 10
        
        return min(score, 100)