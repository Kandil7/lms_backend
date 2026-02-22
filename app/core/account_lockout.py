from datetime import UTC, datetime, timedelta
from typing import Optional
import logging

from app.core.cache import get_app_cache
from app.core.config import settings
from app.core.exceptions import UnauthorizedException

logger = logging.getLogger("app.account_lockout")

class AccountLockoutManager:
    def __init__(self):
        self.cache = get_app_cache()
    
    def increment_failed_attempts(self, email: str, ip_address: str) -> int:
        """Increment failed login attempts for a user/IP combination."""
        # Use separate keys for user-based and IP-based tracking
        user_key = f"auth:failed_attempts:user:{email}"
        ip_key = f"auth:failed_attempts:ip:{ip_address}"
        
        # Increment both counters
        user_attempts = self.cache.incr(user_key, 1)
        ip_attempts = self.cache.incr(ip_key, 1)
        
        # Set expiration for both (15 minutes)
        self.cache.expire(user_key, 900)  # 15 minutes
        self.cache.expire(ip_key, 900)   # 15 minutes
        
        return max(user_attempts, ip_attempts)
    
    def is_account_locked(self, email: str, ip_address: str) -> bool:
        """Check if account is locked based on failed attempts."""
        user_key = f"auth:failed_attempts:user:{email}"
        ip_key = f"auth:failed_attempts:ip:{ip_address}"
        
        user_attempts = self.cache.get_int(user_key) or 0
        ip_attempts = self.cache.get_int(ip_key) or 0
        
        # Account is locked if either user or IP has exceeded threshold
        return user_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS or ip_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS
    
    def reset_failed_attempts(self, email: str, ip_address: str) -> None:
        """Reset failed login attempts for a user/IP."""
        user_key = f"auth:failed_attempts:user:{email}"
        ip_key = f"auth:failed_attempts:ip:{ip_address}"
        
        self.cache.delete(user_key)
        self.cache.delete(ip_key)
    
    def get_failed_attempts(self, email: str, ip_address: str) -> tuple[int, int]:
        """Get current failed attempts for user and IP."""
        user_key = f"auth:failed_attempts:user:{email}"
        ip_key = f"auth:failed_attempts:ip:{ip_address}"
        
        user_attempts = self.cache.get_int(user_key) or 0
        ip_attempts = self.cache.get_int(ip_key) or 0
        
        return user_attempts, ip_attempts


# Global instance
account_lockout_manager = AccountLockoutManager()

def check_account_lockout(email: str, ip_address: str) -> None:
    """Check if account is locked and raise exception if so."""
    if account_lockout_manager.is_account_locked(email, ip_address):
        raise UnauthorizedException("Account temporarily locked due to multiple failed login attempts. Please try again later.")