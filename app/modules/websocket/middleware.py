from typing import Optional, Tuple
import logging
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token, TokenType
from app.core.database import get_db
from app.modules.users.models import User
from app.modules.users.repositories.user_repository import UserRepository

logger = logging.getLogger("app.websocket.middleware")

# OAuth2 scheme for WebSocket authentication (using query params or headers)
websocket_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/token")


async def authenticate_websocket(
    websocket: WebSocket,
    db: Session,
    token: Optional[str] = None
) -> Tuple[str, str]:
    """Authenticate WebSocket connection using JWT token.
    
    Args:
        websocket: The WebSocket connection
        db: Database session
        token: Token from query parameter or header
        
    Returns:
        Tuple of (user_id, session_id)
        
    Raises:
        WebSocketException: If authentication fails
    """
    try:
        # Try to get token from query parameters first
        if not token:
            token = websocket.query_params.get("token")
        
        # If not in query params, try Authorization header
        if not token and "Authorization" in websocket.headers:
            auth_header = websocket.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
        
        if not token:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Authentication token required"
            )
        
        # Decode and validate token
        payload = decode_token(token, expected_type=TokenType.ACCESS, check_blacklist=True)
        
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Invalid token: missing subject"
            )
        
        # Verify user exists and is active
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(user_id_str)
        if not user or not user.is_active:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="User not found or inactive"
            )
        
        if settings.REQUIRE_EMAIL_VERIFICATION_FOR_LOGIN and user.email_verified_at is None:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Email not verified"
            )
        
        # Generate session ID (could be from token or new UUID)
        session_id = payload.get("jti", f"session_{user_id_str}_{int(datetime.now(timezone.utc).timestamp())}")
        
        return user_id_str, session_id
        
    except JWTError as e:
        logger.warning(f"JWT decode error in WebSocket auth: {e}")
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid authentication token"
        ) from e
    except UnauthorizedException as e:
        logger.warning(f"Unauthorized WebSocket connection: {e}")
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=str(e)
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket authentication: {e}")
        raise WebSocketException(
            code=status.WS_1011_UNEXPECTED_ERROR,
            reason="Internal server error"
        ) from e