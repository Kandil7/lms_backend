from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException
from app.core.permissions import Role
from app.modules.analytics.schemas import SystemOverviewResponse
from app.modules.courses.models.course import Course
from app.modules.enrollments.models import Enrollment
from app.modules.users.models import User


class SystemAnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_system_overview(self, current_user) -> SystemOverviewResponse:
        if current_user.role != Role.ADMIN.value:
            raise ForbiddenException("Only admins can access system overview")

        user_row = self.db.execute(
            select(
                func.count(User.id),
                func.sum(case((User.role == Role.STUDENT.value, 1), else_=0)),
                func.sum(case((User.role == Role.INSTRUCTOR.value, 1), else_=0)),
            )
        ).one()
        total_users = int(user_row[0] or 0)
        total_students = int(user_row[1] or 0)
        total_instructors = int(user_row[2] or 0)

        course_row = self.db.execute(
            select(
                func.count(Course.id),
                func.sum(case((Course.is_published.is_(True), 1), else_=0)),
            )
        ).one()
        total_courses = int(course_row[0] or 0)
        published_courses = int(course_row[1] or 0)

        enrollment_row = self.db.execute(
            select(
                func.count(Enrollment.id),
                func.sum(case((Enrollment.status == "active", 1), else_=0)),
            )
        ).one()
        total_enrollments = int(enrollment_row[0] or 0)
        active_enrollments = int(enrollment_row[1] or 0)

        return SystemOverviewResponse(
            total_users=total_users,
            total_students=total_students,
            total_instructors=total_instructors,
            total_courses=total_courses,
            published_courses=published_courses,
            total_enrollments=total_enrollments,
            active_enrollments=active_enrollments,
        )
