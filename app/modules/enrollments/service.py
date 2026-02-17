from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import Role
from app.modules.courses.repositories.course_repository import CourseRepository
from app.modules.courses.repositories.lesson_repository import LessonRepository
from app.modules.enrollments.repository import EnrollmentRepository
from app.modules.enrollments.schemas import LessonProgressUpdate, ReviewCreate
from app.utils.pagination import PageParams, paginate


class EnrollmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = EnrollmentRepository(db)
        self.course_repo = CourseRepository(db)
        self.lesson_repo = LessonRepository(db)

    def enroll(self, student_id: UUID, course_id: UUID):
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("Course not found")

        if not course.is_published:
            raise ForbiddenException("Cannot enroll in unpublished course")

        existing = self.repo.get_by_student_and_course(student_id, course_id)
        if existing:
            return existing

        enrollment = self.repo.create(student_id=student_id, course_id=course_id)
        self._refresh_enrollment_summary(enrollment)
        self.db.commit()
        return enrollment

    def list_my_enrollments(self, student_id: UUID, page: int, page_size: int) -> dict:
        items, total = self.repo.list_by_student(student_id, page, page_size)
        return paginate(items, total, PageParams(page=page, page_size=page_size))

    def list_course_enrollments(self, course_id: UUID, current_user, page: int, page_size: int) -> dict:
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("Course not found")

        if not self._can_manage_course(course, current_user):
            raise ForbiddenException("Not authorized to view course enrollments")

        items, total = self.repo.list_by_course(course_id, page, page_size)
        return paginate(items, total, PageParams(page=page, page_size=page_size))

    def get_enrollment(self, enrollment_id: UUID, current_user):
        enrollment = self.repo.get_by_id(enrollment_id)
        if not enrollment:
            raise NotFoundException("Enrollment not found")

        if not self._can_view_enrollment(enrollment, current_user):
            raise ForbiddenException("Not authorized to access this enrollment")

        return enrollment

    def update_lesson_progress(
        self,
        enrollment_id: UUID,
        lesson_id: UUID,
        payload: LessonProgressUpdate,
        current_user,
    ):
        enrollment = self.get_enrollment(enrollment_id, current_user)

        lesson = self.lesson_repo.get_by_id(lesson_id)
        if not lesson or lesson.course_id != enrollment.course_id:
            raise NotFoundException("Lesson not found in this enrollment's course")

        now = datetime.now(UTC)
        updates = payload.model_dump(exclude_unset=True)

        progress = self.repo.get_lesson_progress(enrollment_id, lesson_id)
        started_at = progress.started_at if progress else now
        completed_at = progress.completed_at if progress else None

        status = updates.get("status", progress.status if progress else "in_progress")
        completion_percentage = updates.get(
            "completion_percentage",
            progress.completion_percentage if progress else Decimal("0.00"),
        )

        if status == "in_progress" and not started_at:
            started_at = now

        if status == "completed" or Decimal(str(completion_percentage)) >= Decimal("100"):
            status = "completed"
            completion_percentage = Decimal("100.00")
            completed_at = now

        metadata = progress.progress_metadata if progress else {}
        if updates.get("notes"):
            metadata = {**(metadata or {}), "notes": updates["notes"]}

        progress = self.repo.upsert_lesson_progress(
            enrollment_id=enrollment_id,
            lesson_id=lesson_id,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            time_spent_seconds=updates.get("time_spent_seconds"),
            last_position_seconds=updates.get("last_position_seconds"),
            completion_percentage=completion_percentage,
            progress_metadata=metadata,
        )

        self._refresh_enrollment_summary(enrollment)

        if enrollment.status == "completed" and enrollment.certificate_issued_at is None:
            try:
                from app.modules.certificates.service import CertificateService

                CertificateService(self.db).issue_for_enrollment(enrollment, commit=False)
            except Exception:
                # Certificate generation should not block progress completion.
                pass

        self.db.commit()
        self.db.refresh(progress)
        return progress

    def mark_lesson_completed(self, enrollment_id: UUID, lesson_id: UUID, current_user):
        payload = LessonProgressUpdate(
            status="completed",
            completion_percentage=Decimal("100.00"),
        )
        return self.update_lesson_progress(enrollment_id, lesson_id, payload, current_user)

    def add_review(self, enrollment_id: UUID, payload: ReviewCreate, current_user):
        enrollment = self.get_enrollment(enrollment_id, current_user)

        if current_user.role != Role.ADMIN.value and enrollment.student_id != current_user.id:
            raise ForbiddenException("You can only review your own enrollments")

        if Decimal(enrollment.progress_percentage) < Decimal("20.00"):
            raise ForbiddenException("Complete at least 20% before reviewing")

        enrollment = self.repo.update(enrollment, rating=payload.rating, review=payload.review)
        self.db.commit()
        return enrollment

    def get_course_stats(self, course_id: UUID, current_user):
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("Course not found")

        if not self._can_manage_course(course, current_user):
            raise ForbiddenException("Not authorized to view course stats")

        return self.repo.get_course_stats(course_id)

    def _refresh_enrollment_summary(self, enrollment) -> None:
        total_lessons = self.lesson_repo.count_by_course(enrollment.course_id)
        completed_lessons, total_time = self.repo.get_enrollment_progress_stats(enrollment.id)

        if total_lessons == 0:
            progress_percentage = Decimal("0.00")
        else:
            progress_percentage = (Decimal(completed_lessons) / Decimal(total_lessons) * Decimal("100")).quantize(
                Decimal("0.01")
            )

        status = enrollment.status
        completed_at = enrollment.completed_at
        if total_lessons > 0 and completed_lessons >= total_lessons:
            status = "completed"
            completed_at = completed_at or datetime.now(UTC)
        elif status == "completed":
            status = "active"
            completed_at = None

        self.repo.update(
            enrollment,
            total_lessons_count=total_lessons,
            completed_lessons_count=completed_lessons,
            total_time_spent_seconds=total_time,
            progress_percentage=progress_percentage,
            status=status,
            completed_at=completed_at,
            last_accessed_at=datetime.now(UTC),
        )

    def _can_manage_course(self, course, current_user) -> bool:
        if current_user.role == Role.ADMIN.value:
            return True
        return current_user.role == Role.INSTRUCTOR.value and course.instructor_id == current_user.id

    def _can_view_enrollment(self, enrollment, current_user) -> bool:
        if current_user.role == Role.ADMIN.value:
            return True
        if current_user.role == Role.STUDENT.value and enrollment.student_id == current_user.id:
            return True
        if current_user.role == Role.INSTRUCTOR.value:
            course = self.course_repo.get_by_id(enrollment.course_id)
            return bool(course and course.instructor_id == current_user.id)
        return False
