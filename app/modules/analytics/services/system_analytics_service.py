from sqlalchemy import and_, func, select
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

        total_users = int(self.db.scalar(select(func.count()).select_from(User)) or 0)
        total_students = int(
            self.db.scalar(select(func.count()).select_from(User).where(User.role == Role.STUDENT.value)) or 0
        )
        total_instructors = int(
            self.db.scalar(select(func.count()).select_from(User).where(User.role == Role.INSTRUCTOR.value)) or 0
        )

        total_courses = int(self.db.scalar(select(func.count()).select_from(Course)) or 0)
        published_courses = int(
            self.db.scalar(select(func.count()).select_from(Course).where(Course.is_published.is_(True))) or 0
        )

        total_enrollments = int(self.db.scalar(select(func.count()).select_from(Enrollment)) or 0)
        active_enrollments = int(
            self.db.scalar(
                select(func.count()).select_from(Enrollment).where(Enrollment.status == "active")
            )
            or 0
        )

        return SystemOverviewResponse(
            total_users=total_users,
            total_students=total_students,
            total_instructors=total_instructors,
            total_courses=total_courses,
            published_courses=published_courses,
            total_enrollments=total_enrollments,
            active_enrollments=active_enrollments,
        )
