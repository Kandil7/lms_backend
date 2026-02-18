from decimal import Decimal
from uuid import UUID
import time
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import Role
from app.core.cache import get_app_cache
from app.modules.analytics.schemas import CourseAnalyticsResponse
from app.modules.courses.models.course import Course
from app.modules.enrollments.models import Enrollment


class CourseAnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.cache = get_app_cache()

    def get_course_analytics(self, course_id: UUID, current_user) -> CourseAnalyticsResponse:
        # Generate cache key
        cache_key = f"course_analytics:{course_id}"
        
        # Try to get from cache first
        cached_data = self.cache.get_json(cache_key)
        if cached_data is not None:
            return CourseAnalyticsResponse(**cached_data)
        
        # Execute the query if not in cache
        row = self.db.execute(
            select(
                Course.id,
                Course.title,
                Course.instructor_id,
                func.count(Enrollment.id),
                func.sum(case((Enrollment.status == "active", 1), else_=0)),
                func.sum(case((Enrollment.status == "completed", 1), else_=0)),
                func.coalesce(func.avg(Enrollment.progress_percentage), 0),
                func.coalesce(func.avg(Enrollment.total_time_spent_seconds), 0),
                func.coalesce(func.avg(Enrollment.rating), 0),
                func.sum(case((Enrollment.rating.is_not(None), 1), else_=0)),
            )
            .select_from(Course)
            .outerjoin(Enrollment, Enrollment.course_id == Course.id)
            .where(Course.id == course_id)
            .group_by(Course.id, Course.title, Course.instructor_id)
        ).one_or_none()

        if row is None:
            raise NotFoundException("Course not found")

        if current_user.role not in {Role.ADMIN.value, Role.INSTRUCTOR.value}:
            raise ForbiddenException("Insufficient permissions")

        if current_user.role == Role.INSTRUCTOR.value and row[2] != current_user.id:
            raise ForbiddenException("Not authorized to view analytics for this course")

        total_enrollments = int(row[3] or 0)
        active_students = int(row[4] or 0)
        completed_students = int(row[5] or 0)
        average_progress = Decimal(str(row[6] or 0)).quantize(Decimal("0.01"))
        average_time_hours = (Decimal(str(row[7] or 0)) / Decimal("3600")).quantize(Decimal("0.01"))
        average_rating = Decimal(str(row[8] or 0)).quantize(Decimal("0.01"))
        total_reviews = int(row[9] or 0)

        completion_rate = Decimal("0.00")
        if total_enrollments > 0:
            completion_rate = (
                Decimal(completed_students) / Decimal(total_enrollments) * Decimal("100")
            ).quantize(Decimal("0.01"))

        result = CourseAnalyticsResponse(
            course_id=row[0],
            course_title=row[1],
            total_enrollments=total_enrollments,
            active_students=active_students,
            completed_students=completed_students,
            completion_rate=completion_rate,
            average_progress=average_progress,
            average_time_hours=average_time_hours,
            average_rating=average_rating,
            total_reviews=total_reviews,
        )
        
        # Cache the result (TTL: 5 minutes for analytics data)
        self.cache.set_json(cache_key, result.model_dump(), ttl_seconds=300)
        
        return result

    def invalidate_course_analytics_cache(self, course_id: UUID) -> None:
        """Invalidate cache for a specific course's analytics"""
        cache_key = f"course_analytics:{course_id}"
        self.cache.delete_by_prefix(cache_key)
