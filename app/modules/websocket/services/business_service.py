from datetime import datetime, timezone
import logging
from typing import Dict, Optional, Union

from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.enrollments.models import Enrollment, LessonProgress
from app.modules.quizzes.models import QuizAttempt
from app.modules.websocket.models import WebSocketMessageType
from app.modules.websocket.services.broadcast_service import WebSocketBroadcastService
from app.modules.users.models import User

logger = logging.getLogger("app.websocket.business")


class WebSocketBusinessService:
    """Business service for handling real-time updates for course progress, quiz attempts, and notifications."""
    
    def __init__(self, broadcast_service: WebSocketBroadcastService):
        self.broadcast_service = broadcast_service
    
    async def notify_course_progress_update(
        self,
        db: Session,
        enrollment_id: str,
        user_id: str,
        progress_data: Dict[str, Union[int, float, str]],
        message: str = "Course progress updated"
    ) -> bool:
        """Notify connected clients about course progress updates."""
        try:
            # Get enrollment to verify it exists
            enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
            if not enrollment or str(enrollment.student_id) != user_id:
                logger.warning(f"Invalid enrollment ID {enrollment_id} for user {user_id}")
                return False
            
            # Prepare payload
            payload = {
                "enrollment_id": str(enrollment_id),
                "course_id": str(enrollment.course_id),
                "student_id": str(user_id),
                "progress_percentage": progress_data.get("progress_percentage"),
                "completed_lessons_count": progress_data.get("completed_lessons_count"),
                "total_lessons_count": progress_data.get("total_lessons_count"),
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **progress_data
            }
            
            # Broadcast to user's connections
            sent_count = await self.broadcast_service.broadcast_message(
                message_type=WebSocketMessageType.COURSE_PROGRESS_UPDATE,
                payload=payload,
                target_user_id=user_id
            )
            
            logger.info(f"Sent course progress update to {sent_count} connections for user {user_id}")
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"Failed to notify course progress update: {e}")
            return False
    
    async def notify_quiz_attempt_update(
        self,
        db: Session,
        quiz_attempt_id: str,
        user_id: str,
        attempt_data: Dict[str, Union[int, float, str, bool]],
        message: str = "Quiz attempt updated"
    ) -> bool:
        """Notify connected clients about quiz attempt updates."""
        try:
            # Get quiz attempt to verify it exists
            quiz_attempt = db.query(QuizAttempt).filter(QuizAttempt.id == quiz_attempt_id).first()
            if not quiz_attempt:
                logger.warning(f"Invalid quiz attempt ID {quiz_attempt_id}")
                return False
            
            # Verify user owns the attempt
            enrollment = db.query(Enrollment).filter(Enrollment.id == quiz_attempt.enrollment_id).first()
            if not enrollment or str(enrollment.student_id) != user_id:
                logger.warning(f"Quiz attempt {quiz_attempt_id} does not belong to user {user_id}")
                return False
            
            # Prepare payload
            payload = {
                "quiz_attempt_id": str(quiz_attempt_id),
                "quiz_id": str(quiz_attempt.quiz_id),
                "enrollment_id": str(quiz_attempt.enrollment_id),
                "student_id": str(user_id),
                "status": quiz_attempt.status,
                "score": float(quiz_attempt.score) if quiz_attempt.score else None,
                "max_score": float(quiz_attempt.max_score) if quiz_attempt.max_score else None,
                "percentage": float(quiz_attempt.percentage) if quiz_attempt.percentage else None,
                "is_passed": quiz_attempt.is_passed,
                "time_taken_seconds": quiz_attempt.time_taken_seconds,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **attempt_data
            }
            
            # Broadcast to user's connections
            sent_count = await self.broadcast_service.broadcast_message(
                message_type=WebSocketMessageType.QUIZ_ATTEMPT_UPDATE,
                payload=payload,
                target_user_id=user_id
            )
            
            logger.info(f"Sent quiz attempt update to {sent_count} connections for user {user_id}")
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"Failed to notify quiz attempt update: {e}")
            return False
    
    async def notify_notification(
        self,
        user_id: str,
        notification_data: Dict[str, Union[str, int, bool]],
        message: str = "New notification"
    ) -> bool:
        """Notify connected clients about new notifications."""
        try:
            # Prepare payload
            payload = {
                "notification_id": notification_data.get("id"),
                "type": notification_data.get("type", "general"),
                "title": notification_data.get("title", "Notification"),
                "message": notification_data.get("message", message),
                "read": notification_data.get("read", False),
                "created_at": datetime.now(timezone.utc).isoformat(),
                **notification_data
            }
            
            # Broadcast to user's connections
            sent_count = await self.broadcast_service.broadcast_message(
                message_type=WebSocketMessageType.NOTIFICATION,
                payload=payload,
                target_user_id=user_id
            )
            
            logger.info(f"Sent notification to {sent_count} connections for user {user_id}")
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"Failed to notify notification: {e}")
            return False
    
    async def broadcast_system_message(
        self,
        message_type: WebSocketMessageType,
        payload: Dict[str, Union[str, int, bool]],
        exclude_user_ids: Optional[list] = None
    ) -> int:
        """Broadcast system-wide messages to all connected clients (except excluded users)."""
        try:
            # Prepare payload
            payload.update({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "system"
            })
            
            # Broadcast to all connections (excluding specified users)
            sent_count = await self.broadcast_service.broadcast_message(
                message_type=message_type,
                payload=payload,
                exclude_connection_ids=None  # Will be handled by business logic
            )
            
            logger.info(f"Broadcast system message to {sent_count} connections")
            return sent_count
            
        except Exception as e:
            logger.error(f"Failed to broadcast system message: {e}")
            return 0