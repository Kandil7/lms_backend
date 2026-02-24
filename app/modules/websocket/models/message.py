from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field


class WebSocketMessageType(str, Enum):
    """WebSocket message types."""
    
    # System messages
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    
    # Business domain messages
    COURSE_PROGRESS_UPDATE = "course_progress_update"
    QUIZ_ATTEMPT_UPDATE = "quiz_attempt_update"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    
    # User-specific messages
    USER_MESSAGE = "user_message"


class WebSocketMessage(BaseModel):
    """Generic WebSocket message structure."""
    
    type: WebSocketMessageType = Field(..., description="Message type")
    timestamp: float = Field(..., description="Timestamp in seconds since epoch")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for request-response patterns")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Message payload")
    sender_id: Optional[str] = Field(None, description="Sender user ID (for authenticated messages)")
    
    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True