from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.modules.analytics.schemas import (
    CourseProgressItem,
    DailyActivityItem,
    MyDashboardResponse,
    MyProgressSummary,
)
from app.modules.courses.models.course import Course
from app.modules.enrollments.models import Enrollment, LessonProgress
from app.modules.quizzes.models.attempt import QuizAttempt


class StudentAnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_progress_summary(self, student_id: UUID) -> MyProgressSummary:
        enrollment_stats_stmt = select(
            func.count(Enrollment.id),
            func.sum(case((Enrollment.status == "active", 1), else_=0)),
            func.sum(case((Enrollment.status == "completed", 1), else_=0)),
            func.coalesce(func.avg(Enrollment.progress_percentage), 0),
            func.coalesce(func.sum(Enrollment.total_time_spent_seconds), 0),
            func.coalesce(func.sum(Enrollment.completed_lessons_count), 0),
        ).where(Enrollment.student_id == student_id)

        (
            total_enrollments,
            active_enrollments,
            completed_enrollments,
            avg_progress,
            total_time_seconds,
            lessons_completed,
        ) = self.db.execute(enrollment_stats_stmt).one()

        quiz_stats_stmt = (
            select(
                func.count(QuizAttempt.id),
                func.sum(case((QuizAttempt.is_passed.is_(True), 1), else_=0)),
                func.coalesce(func.avg(QuizAttempt.score), 0),
            )
            .join(Enrollment, Enrollment.id == QuizAttempt.enrollment_id)
            .where(Enrollment.student_id == student_id, QuizAttempt.status == "graded")
        )

        quizzes_taken, quizzes_passed, avg_quiz_score = self.db.execute(quiz_stats_stmt).one()

        return MyProgressSummary(
            student_id=student_id,
            total_enrollments=int(total_enrollments or 0),
            active_enrollments=int(active_enrollments or 0),
            completed_enrollments=int(completed_enrollments or 0),
            average_progress=Decimal(str(avg_progress or 0)).quantize(Decimal("0.01")),
            total_time_hours=(Decimal(str(total_time_seconds or 0)) / Decimal("3600")).quantize(Decimal("0.01")),
            total_lessons_completed=int(lessons_completed or 0),
            quizzes_taken=int(quizzes_taken or 0),
            quizzes_passed=int(quizzes_passed or 0),
            average_quiz_score=Decimal(str(avg_quiz_score or 0)).quantize(Decimal("0.01")),
        )

    def get_dashboard(self, student_id: UUID) -> MyDashboardResponse:
        summary = self.get_progress_summary(student_id)

        course_rows = self.db.execute(
            select(
                Course.id,
                Course.title,
                Enrollment.progress_percentage,
                Enrollment.completed_lessons_count,
                Enrollment.total_lessons_count,
                Enrollment.total_time_spent_seconds,
                func.coalesce(func.count(QuizAttempt.id), 0),
                func.coalesce(func.avg(QuizAttempt.score), 0),
            )
            .join(Enrollment, Enrollment.course_id == Course.id)
            .outerjoin(
                QuizAttempt,
                and_(
                    QuizAttempt.enrollment_id == Enrollment.id,
                    QuizAttempt.status == "graded",
                ),
            )
            .where(Enrollment.student_id == student_id)
            .group_by(
                Course.id,
                Course.title,
                Enrollment.progress_percentage,
                Enrollment.completed_lessons_count,
                Enrollment.total_lessons_count,
                Enrollment.total_time_spent_seconds,
            )
            .order_by(Enrollment.enrolled_at.desc())
        ).all()

        courses = [
            CourseProgressItem(
                course_id=row[0],
                course_title=row[1],
                progress_percentage=Decimal(str(row[2] or 0)).quantize(Decimal("0.01")),
                completed_lessons=int(row[3] or 0),
                total_lessons=int(row[4] or 0),
                time_spent_hours=(Decimal(str(row[5] or 0)) / Decimal("3600")).quantize(Decimal("0.01")),
                quizzes_completed=int(row[6] or 0),
                average_quiz_score=Decimal(str(row[7] or 0)).quantize(Decimal("0.01")),
            )
            for row in course_rows
        ]

        recent_activity_start = datetime.now(UTC) - timedelta(days=30)
        activity_rows = self.db.execute(
            select(
                func.date(LessonProgress.completed_at).label("activity_date"),
                func.sum(case((LessonProgress.status == "completed", 1), else_=0)),
                func.coalesce(func.sum(LessonProgress.time_spent_seconds), 0),
            )
            .join(Enrollment, Enrollment.id == LessonProgress.enrollment_id)
            .where(
                Enrollment.student_id == student_id,
                LessonProgress.completed_at.is_not(None),
                LessonProgress.completed_at >= recent_activity_start,
            )
            .group_by(func.date(LessonProgress.completed_at))
            .order_by(func.date(LessonProgress.completed_at).desc())
        ).all()

        activity_by_date = {
            row[0]: DailyActivityItem(
                date=row[0],
                lessons_completed=int(row[1] or 0),
                time_spent_minutes=int((row[2] or 0) / 60),
                quizzes_taken=0,
            )
            for row in activity_rows
        }

        quiz_activity_rows = self.db.execute(
            select(func.date(QuizAttempt.submitted_at), func.count(QuizAttempt.id))
            .join(Enrollment, Enrollment.id == QuizAttempt.enrollment_id)
            .where(
                Enrollment.student_id == student_id,
                QuizAttempt.submitted_at.is_not(None),
                QuizAttempt.submitted_at >= recent_activity_start,
            )
            .group_by(func.date(QuizAttempt.submitted_at))
        ).all()

        for activity_date, quizzes_taken in quiz_activity_rows:
            if activity_date in activity_by_date:
                activity_by_date[activity_date].quizzes_taken = int(quizzes_taken or 0)
            else:
                activity_by_date[activity_date] = DailyActivityItem(
                    date=activity_date,
                    lessons_completed=0,
                    time_spent_minutes=0,
                    quizzes_taken=int(quizzes_taken or 0),
                )

        recent_activity = sorted(activity_by_date.values(), key=lambda item: item.date, reverse=True)

        return MyDashboardResponse(
            student_id=student_id,
            summary=summary,
            courses=courses,
            recent_activity=recent_activity,
        )
