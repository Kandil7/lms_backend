from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import Role
from app.modules.analytics.schemas import CourseAnalyticsResponse
from app.modules.courses.models.course import Course
from app.modules.enrollments.models import Enrollment


class CourseAnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_course_analytics(self, course_id: UUID, current_user) -> CourseAnalyticsResponse:
        course = self.db.scalar(select(Course).where(Course.id == course_id))
        if not course:
            raise NotFoundException("Course not found")

        if current_user.role not in {Role.ADMIN.value, Role.INSTRUCTOR.value}:
            raise ForbiddenException("Insufficient permissions")

        if current_user.role == Role.INSTRUCTOR.value and course.instructor_id != current_user.id:
            raise ForbiddenException("Not authorized to view analytics for this course")

        row = self.db.execute(
            select(
                func.count(Enrollment.id),
                func.sum(case((Enrollment.status == "active", 1), else_=0)),
                func.sum(case((Enrollment.status == "completed", 1), else_=0)),
                func.coalesce(func.avg(Enrollment.progress_percentage), 0),
                func.coalesce(func.avg(Enrollment.total_time_spent_seconds), 0),
                func.coalesce(func.avg(Enrollment.rating), 0),
                func.sum(case((Enrollment.rating.is_not(None), 1), else_=0)),
            ).where(Enrollment.course_id == course_id)
        ).one()

        total_enrollments = int(row[0] or 0)
        active_students = int(row[1] or 0)
        completed_students = int(row[2] or 0)
        average_progress = Decimal(str(row[3] or 0)).quantize(Decimal("0.01"))
        average_time_hours = (Decimal(str(row[4] or 0)) / Decimal("3600")).quantize(Decimal("0.01"))
        average_rating = Decimal(str(row[5] or 0)).quantize(Decimal("0.01"))
        total_reviews = int(row[6] or 0)

        completion_rate = Decimal("0.00")
        if total_enrollments > 0:
            completion_rate = (
                Decimal(completed_students) / Decimal(total_enrollments) * Decimal("100")
            ).quantize(Decimal("0.01"))

        return CourseAnalyticsResponse(
            course_id=course.id,
            course_title=course.title,
            total_enrollments=total_enrollments,
            active_students=active_students,
            completed_students=completed_students,
            completion_rate=completion_rate,
            average_progress=average_progress,
            average_time_hours=average_time_hours,
            average_rating=average_rating,
            total_reviews=total_reviews,
        )
