from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException
from app.core.permissions import Role
from app.modules.analytics.schemas import InstructorOverviewResponse
from app.modules.courses.models.course import Course
from app.modules.enrollments.models import Enrollment


class InstructorAnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_instructor_overview(self, instructor_id: UUID, current_user) -> InstructorOverviewResponse:
        if current_user.role not in {Role.ADMIN.value, Role.INSTRUCTOR.value}:
            raise ForbiddenException("Insufficient permissions")

        if current_user.role == Role.INSTRUCTOR.value and current_user.id != instructor_id:
            raise ForbiddenException("Not authorized to view this instructor overview")

        rows = self.db.execute(
            select(
                func.count(func.distinct(Course.id)),
                func.count(func.distinct(case((Course.is_published.is_(True), Course.id), else_=None))),
                func.count(Enrollment.id),
                func.count(func.distinct(Enrollment.student_id)),
                func.coalesce(func.avg(Enrollment.rating), 0),
            )
            .select_from(Course)
            .outerjoin(Enrollment, Enrollment.course_id == Course.id)
            .where(Course.instructor_id == instructor_id)
        ).one()

        total_courses = int(rows[0] or 0)
        published_courses = int(rows[1] or 0)
        total_enrollments = int(rows[2] or 0)
        total_students = int(rows[3] or 0)
        average_course_rating = Decimal(str(rows[4] or 0)).quantize(Decimal("0.01"))

        return InstructorOverviewResponse(
            instructor_id=instructor_id,
            total_courses=total_courses,
            published_courses=published_courses,
            total_students=total_students,
            total_enrollments=total_enrollments,
            average_course_rating=average_course_rating,
        )
