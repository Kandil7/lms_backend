from datetime import datetime, timezone
from typing import Optional, Union

from pydantic import BaseModel, Field


class WebSocketConnection(BaseModel):
    """Represents a WebSocket connection with authentication and metadata."""
    
    connection_id: str = Field(..., description="Unique connection ID")
    user_id: str = Field(..., description="Authenticated user ID")
    session_id: str = Field(..., description="Session ID for connection tracking")
    client_type: str = Field(default="web", description="Client type (web, mobile, etc.)")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    connected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Connection timestamp")
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last activity timestamp")
    is_active: bool = Field(default=True, description="Whether connection is active")
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }