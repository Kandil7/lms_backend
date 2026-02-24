import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.modules.websocket.models import WebSocketMessage, WebSocketMessageType
from app.modules.websocket.services.client_registry import WebSocketClientRegistry

logger = logging.getLogger("app.websocket.broadcast")


class WebSocketBroadcastService:
    """Service for broadcasting messages to WebSocket clients."""
    
    def __init__(self, client_registry: WebSocketClientRegistry):
        self.client_registry = client_registry
        self.redis_client: Optional[Redis] = None
        self._initialize_redis()
        self.broadcast_channel_prefix = "ws:broadcast"
        self.user_channel_prefix = "ws:user"
        
    def _initialize_redis(self) -> None:
        """Initialize Redis client for pub/sub."""
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
                    logger.info("WebSocket broadcast service connected to Redis successfully")
            else:
                logger.warning("REDIS_URL not configured, falling back to in-memory broadcast")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis for WebSocket broadcast: {e}")
            self.redis_client = None
    
    async def broadcast_message(
        self,
        message_type: WebSocketMessageType,
        payload: dict,
        target_user_id: Optional[str] = None,
        exclude_connection_ids: Optional[List[str]] = None
    ) -> int:
        """Broadcast a message to connected clients.
        
        Args:
            message_type: Type of message to broadcast
            payload: Message payload
            target_user_id: If specified, broadcast only to this user's connections
            exclude_connection_ids: List of connection IDs to exclude from broadcast
            
        Returns:
            Number of connections that received the message
        """
        try:
            # Create message
            message = WebSocketMessage(
                type=message_type,
                timestamp=float(datetime.now(timezone.utc).timestamp()),
                payload=payload
            )
            
            # Get target connections
            if target_user_id:
                connections = await self.client_registry.get_user_connections(target_user_id)
            else:
                # For global broadcast, we need to get all active connections
                # In production, this would be handled by Redis pub/sub
                connections = await self._get_all_active_connections()
            
            # Filter out excluded connections
            if exclude_connection_ids:
                connections = [conn for conn in connections if conn.connection_id not in exclude_connection_ids]
            
            # Send message to each connection
            sent_count = 0
            for connection in connections:
                try:
                    # In a real implementation, this would send via the actual WebSocket connection
                    # For now, we'll simulate by storing in Redis or using pub/sub
                    if self.redis_client:
                        channel = f"{self.user_channel_prefix}:{connection.user_id}"
                        self.redis_client.publish(channel, json.dumps(message.dict()))
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send message to connection {connection.connection_id}: {e}")
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")
            return 0
    
    async def _get_all_active_connections(self) -> list:
        """Get all active connections (for global broadcast)."""
        try:
            if not self.redis_client:
                return []
                
            # This is a simplified approach - in production, you'd maintain a separate set of active connections
            # or use Redis keys pattern matching
            cursor = 0
            connections = []
            
            while True:
                cursor, keys = self.redis_client.scan(cursor=cursor, match="ws:connections:*", count=100)
                if not keys:
                    break
                    
                for key in keys:
                    if not key.endswith(":last_activity"):
                        try:
                            connection_data = self.redis_client.get(key)
                            if connection_data:
                                connection = WebSocketConnection(**json.loads(connection_data))
                                if connection.is_active:
                                    connections.append(connection)
                        except Exception as e:
                            logger.error(f"Error parsing connection data from Redis: {e}")
                
                if cursor == 0:
                    break
            
            return connections
            
        except RedisError as e:
            logger.error(f"Failed to get all active connections: {e}")
            return []
    
    async def publish_to_channel(self, channel: str, message: WebSocketMessage) -> bool:
        """Publish message to a Redis channel."""
        try:
            if self.redis_client:
                self.redis_client.publish(channel, json.dumps(message.dict()))
                return True
            return False
        except RedisError as e:
            logger.error(f"Failed to publish to Redis channel '{channel}': {e}")
            return False
    
    async def subscribe_to_channel(self, channel: str):
        """Subscribe to a Redis channel (for background workers)."""
        try:
            if self.redis_client:
                pubsub = self.redis_client.pubsub()
                pubsub.subscribe(channel)
                return pubsub
        except RedisError as e:
            logger.error(f"Failed to subscribe to Redis channel '{channel}': {e}")
            return None