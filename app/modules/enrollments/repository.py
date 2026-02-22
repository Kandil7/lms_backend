from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload

from app.modules.enrollments.models import Enrollment, LessonProgress


class EnrollmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, enrollment_id: UUID) -> Enrollment | None:
        stmt = select(Enrollment).options(joinedload(Enrollment.course)).where(Enrollment.id == enrollment_id)
        return self.db.scalar(stmt)

    def get_by_id_for_update(self, enrollment_id: UUID) -> Enrollment | None:
        stmt = (
            select(Enrollment)
            .where(Enrollment.id == enrollment_id)
            .with_for_update()
        )
        return self.db.scalar(stmt)

    def get_by_student_and_course(self, student_id: UUID, course_id: UUID) -> Enrollment | None:
        stmt = select(Enrollment).where(
            and_(Enrollment.student_id == student_id, Enrollment.course_id == course_id)
        )
        return self.db.scalar(stmt)

    def get_by_student_and_course_for_update(self, student_id: UUID, course_id: UUID) -> Enrollment | None:
        stmt = (
            select(Enrollment)
            .where(and_(Enrollment.student_id == student_id, Enrollment.course_id == course_id))
            .with_for_update()
        )
        return self.db.scalar(stmt)

    def list_by_student(self, student_id: UUID, page: int, page_size: int) -> tuple[list[Enrollment], int]:
        base_filter = Enrollment.student_id == student_id

        total_stmt = select(func.count()).select_from(Enrollment).where(base_filter)
        total = int(self.db.scalar(total_stmt) or 0)

        stmt = (
            select(Enrollment)
            .options(joinedload(Enrollment.course))
            .where(base_filter)
            .order_by(Enrollment.enrolled_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = list(self.db.scalars(stmt).all())
        return items, total

    def list_by_course(self, course_id: UUID, page: int, page_size: int) -> tuple[list[Enrollment], int]:
        base_filter = Enrollment.course_id == course_id

        total_stmt = select(func.count()).select_from(Enrollment).where(base_filter)
        total = int(self.db.scalar(total_stmt) or 0)

        stmt = (
            select(Enrollment)
            .options(joinedload(Enrollment.student))
            .where(base_filter)
            .order_by(Enrollment.enrolled_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = list(self.db.scalars(stmt).all())
        return items, total

    def create(self, student_id: UUID, course_id: UUID) -> Enrollment:
        now = datetime.now(UTC)
        enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id,
            enrolled_at=now,
            started_at=now,
            status="active",
            progress_percentage=Decimal("0.00"),
        )
        self.db.add(enrollment)
        self.db.flush()
        self.db.refresh(enrollment)
        return enrollment

    def update(self, enrollment: Enrollment, **fields) -> Enrollment:
        for key, value in fields.items():
            setattr(enrollment, key, value)
        self.db.add(enrollment)
        self.db.flush()
        self.db.refresh(enrollment)
        return enrollment

    def get_lesson_progress(self, enrollment_id: UUID, lesson_id: UUID) -> LessonProgress | None:
        stmt = select(LessonProgress).where(
            and_(LessonProgress.enrollment_id == enrollment_id, LessonProgress.lesson_id == lesson_id)
        )
        return self.db.scalar(stmt)

    def get_lesson_progress_for_update(self, enrollment_id: UUID, lesson_id: UUID) -> LessonProgress | None:
        stmt = (
            select(LessonProgress)
            .where(and_(LessonProgress.enrollment_id == enrollment_id, LessonProgress.lesson_id == lesson_id))
            .with_for_update()
        )
        return self.db.scalar(stmt)

    def upsert_lesson_progress(self, enrollment_id: UUID, lesson_id: UUID, **fields) -> LessonProgress:
        progress = self.get_lesson_progress(enrollment_id, lesson_id)
        if not progress:
            progress = LessonProgress(enrollment_id=enrollment_id, lesson_id=lesson_id)
            self.db.add(progress)
            self.db.flush()

        for key, value in fields.items():
            if value is not None:
                setattr(progress, key, value)

        self.db.add(progress)
        self.db.flush()
        self.db.refresh(progress)
        return progress

    def get_enrollment_progress_stats(self, enrollment_id: UUID) -> tuple[int, int]:
        completed_stmt = (
            select(func.count())
            .select_from(LessonProgress)
            .where(
                and_(
                    LessonProgress.enrollment_id == enrollment_id,
                    LessonProgress.status == "completed",
                )
            )
        )

        total_time_stmt = (
            select(func.coalesce(func.sum(LessonProgress.time_spent_seconds), 0))
            .select_from(LessonProgress)
            .where(LessonProgress.enrollment_id == enrollment_id)
        )

        completed_lessons = int(self.db.scalar(completed_stmt) or 0)
        total_time = int(self.db.scalar(total_time_stmt) or 0)

        return completed_lessons, total_time

    def get_course_stats(self, course_id: UUID) -> tuple[int, int, int, Decimal]:
        total_stmt = select(func.count()).select_from(Enrollment).where(Enrollment.course_id == course_id)
        active_stmt = (
            select(func.count())
            .select_from(Enrollment)
            .where(and_(Enrollment.course_id == course_id, Enrollment.status == "active"))
        )
        completed_stmt = (
            select(func.count())
            .select_from(Enrollment)
            .where(and_(Enrollment.course_id == course_id, Enrollment.status == "completed"))
        )
        avg_progress_stmt = (
            select(func.coalesce(func.avg(Enrollment.progress_percentage), 0))
            .select_from(Enrollment)
            .where(Enrollment.course_id == course_id)
        )

        total = int(self.db.scalar(total_stmt) or 0)
        active = int(self.db.scalar(active_stmt) or 0)
        completed = int(self.db.scalar(completed_stmt) or 0)
        avg_progress = Decimal(str(self.db.scalar(avg_progress_stmt) or 0)).quantize(Decimal("0.01"))

        return total, active, completed, avg_progress
