
from datetime import datetime, timezone
import json
import logging
from typing import Dict, List, Optional, Tuple, Set

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.modules.websocket.models import WebSocketConnection

logger = logging.getLogger("app.websocket.client_registry")


class WebSocketClientRegistry:
    """Redis-backed registry for managing WebSocket connections."""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self._initialize_redis()
        self.connection_prefix = "ws:connections"
        self.user_connections_prefix = "ws:user_connections"
        self.session_connections_prefix = "ws:session_connections"
        
    def _initialize_redis(self) -> None:
        """Initialize Redis client with connection pooling."""
        try:
            if settings.REDIS_URL:
                self.redis_client = Redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=2.0,
                    socket_connect_timeout=2.0,
                    max_connections=10,
                )
                # Test connection
                if self.redis_client:
                    self.redis_client.ping()
                    logger.info("WebSocket client registry connected to Redis successfully")
            else:
                logger.warning("REDIS_URL not configured, falling back to in-memory storage")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis for WebSocket registry: {e}")
            self.redis_client = None
    
    async def register_connection(
        self,
        connection_id: str,
        user_id: str,
        session_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        client_type: str = "web"
    ) -> WebSocketConnection:
        """Register a new WebSocket connection."""
        try:
            connection = WebSocketConnection(
                connection_id=connection_id,
                user_id=user_id,
                session_id=session_id,
                client_type=client_type,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            
            if self.redis_client:
                # Store connection data in Redis
                connection_key = f"{self.connection_prefix}:{connection_id}"
                user_connections_key = f"{self.user_connections_prefix}:{user_id}"
                session_connections_key = f"{self.session_connections_prefix}:{session_id}"
                
                # Store connection details
                self.redis_client.setex(
                    connection_key,
                    settings.WEBSOCKET_CONNECTION_TTL_SECONDS or 3600,
                    json.dumps(connection.dict())
                )
                
                # Add to user's connection set
                self.redis_client.sadd(user_connections_key, connection_id)
                self.redis_client.expire(user_connections_key, settings.WEBSOCKET_CONNECTION_TTL_SECONDS or 3600)
                
                # Add to session's connection set
                self.redis_client.sadd(session_connections_key, connection_id)
                self.redis_client.expire(session_connections_key, settings.WEBSOCKET_CONNECTION_TTL_SECONDS or 3600)
                
                # Update last activity timestamp
                self.redis_client.setex(
                    f"{self.connection_prefix}:last_activity:{connection_id}",
                    settings.WEBSOCKET_CONNECTION_TTL_SECONDS or 3600,
                    str(datetime.now(timezone.utc).timestamp())
                )
                
            return connection
            
        except RedisError as e:
            logger.error(f"Failed to register WebSocket connection in Redis: {e}")
            raise UnauthorizedException("Failed to establish WebSocket connection")
    
    async def get_connection(self, connection_id: str) -> Optional[WebSocketConnection]:
        """Get connection by ID."""
        try:
            if self.redis_client:
                connection_key = f"{self.connection_prefix}:{connection_id}"
                connection_data = self.redis_client.get(connection_key)
                if connection_data:
                    # connection_data is str from redis.get() with decode_responses=True
                    return WebSocketConnection(**json.loads(connection_data))  # type: ignore
            return None
        except RedisError as e:
            logger.error(f"Failed to get WebSocket connection from Redis: {e}")
            return None
    
    async def get_user_connections(self, user_id: str) -> List[WebSocketConnection]:
        """Get all active connections for a user."""
        try:
            if self.redis_client:
                user_connections_key = f"{self.user_connections_prefix}:{user_id}"
                connection_ids = self.redis_client.smembers(user_connections_key)  # type: ignore
                
                connections = []
                # Explicitly cast to Set[str] to satisfy type checker
                for conn_id in connection_ids:  # type: ignore
                    connection = await self.get_connection(conn_id)
                    if connection and connection.is_active:
                        connections.append(connection)
                
                return connections
            return []
        except RedisError as e:
            logger.error(f"Failed to get user connections from Redis: {e}")
            return []
    
    async def update_last_activity(self, connection_id: str) -> bool:
        """Update last activity timestamp for a connection."""
        try:
            if self.redis_client:
                key = f"{self.connection_prefix}:last_activity:{connection_id}"
                self.redis_client.setex(
                    key,
                    settings.WEBSOCKET_CONNECTION_TTL_SECONDS or 3600,
                    str(datetime.now(timezone.utc).timestamp())
                )
                return True
            return False
        except RedisError as e:
            logger.error(f"Failed to update last activity for WebSocket connection: {e}")
            return False
    
    async def remove_connection(self, connection_id: str) -> bool:
        """Remove a connection from registry."""
        try:
            if self.redis_client:
                connection_key = f"{self.connection_prefix}:{connection_id}"
                user_connections_key = f"{self.user_connections_prefix}:{self.connection_id_to_user_id(connection_id)}"
                session_connections_key = f"{self.session_connections_prefix}:{self.connection_id_to_session_id(connection_id)}"
                
                # Remove connection data
                self.redis_client.delete(connection_key)
                
                # Remove from user connections set
                if user_connections_key:
                    self.redis_client.srem(user_connections_key, connection_id)
                
                # Remove from session connections set
                if session_connections_key:
                    self.redis_client.srem(session_connections_key, connection_id)
                
                # Remove last activity timestamp
                self.redis_client.delete(f"{self.connection_prefix}:last_activity:{connection_id}")
                
                return True
            return False
        except RedisError as e:
            logger.error(f"Failed to remove WebSocket connection from Redis: {e}")
            return False
    
    def connection_id_to_user_id(self, connection_id: str) -> str:
        """Extract user ID from connection ID (assuming format: user_id:connection_uuid)."""
        parts = connection_id.split(":", 1)
        return parts[0] if len(parts) > 0 else ""
    
    def connection_id_to_session_id(self, connection_id: str) -> str:
        """Extract session ID from connection ID (assuming format: user_id:session_id:connection_uuid)."""
        parts = connection_id.split(":", 2)
        return parts[1] if len(parts) > 1 else ""
    
    async def cleanup_expired_connections(self) -> int:
        """Cleanup expired connections (called periodically)."""
        try:
            if not self.redis_client:
                return 0
                
            # Get all connection keys (using scan to avoid blocking)
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = self.redis_client.scan(cursor=cursor, match=f"{self.connection_prefix}:*", count=100)  # type: ignore
                if not keys:
                    break
                    
                # Check each connection for expiration
                for key in keys:
                    if key.endswith(":last_activity"):
                        continue
                        
                    # Check if connection is expired by checking last activity
                    last_activity_key = f"{key}:last_activity"
                    last_activity_str = self.redis_client.get(last_activity_key)
                    if last_activity_str:
                        try:
                            last_activity = float(last_activity_str)  # type: ignore
                            current_time = datetime.now(timezone.utc).timestamp()
                            if current_time - last_activity > (settings.WEBSOCKET_CONNECTION_TTL_SECONDS or 3600):
                                # Connection expired, clean up
                                connection_id = key.replace(f"{self.connection_prefix}:", "")
                                await self.remove_connection(connection_id)
                                deleted_count += 1
                        except ValueError:
                            continue
                
                if cursor == 0:
                    break
            
            return deleted_count
            
        except RedisError as e:
            logger.error(f"Failed to cleanup expired WebSocket connections: {e}")
            return 0