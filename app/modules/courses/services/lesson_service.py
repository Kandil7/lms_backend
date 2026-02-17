from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, NotFoundException
from app.modules.courses.repositories.course_repository import CourseRepository
from app.modules.courses.repositories.lesson_repository import LessonRepository
from app.modules.courses.schemas.lesson import LessonCreate, LessonUpdate
from app.utils.validators import slugify


class LessonService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.course_repo = CourseRepository(db)
        self.lesson_repo = LessonRepository(db)

    def list_lessons(self, course_id: UUID, current_user):
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("Course not found")

        can_manage = self._can_manage(course, current_user)
        if not course.is_published and not can_manage:
            raise ForbiddenException("Not authorized to view lessons for this course")

        lessons = self.lesson_repo.list_by_course(course_id)
        if can_manage:
            return lessons

        return [lesson for lesson in lessons if lesson.is_preview or course.is_published]

    def get_lesson(self, lesson_id: UUID, current_user):
        lesson = self.lesson_repo.get_by_id(lesson_id)
        if not lesson:
            raise NotFoundException("Lesson not found")

        course = self.course_repo.get_by_id(lesson.course_id)
        if not course:
            raise NotFoundException("Course not found")

        can_manage = self._can_manage(course, current_user)
        if not can_manage and not course.is_published and not lesson.is_preview:
            raise ForbiddenException("Not authorized to view this lesson")

        return lesson

    def create_lesson(self, course_id: UUID, payload: LessonCreate, current_user):
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("Course not found")

        self._ensure_manage_access(course, current_user)

        order_index = payload.order_index or self.lesson_repo.get_next_order_index(course_id)
        lesson = self.lesson_repo.create(
            course_id=course_id,
            title=payload.title,
            slug=payload.slug or slugify(payload.title),
            description=payload.description,
            content=payload.content,
            lesson_type=payload.lesson_type,
            order_index=order_index,
            parent_lesson_id=payload.parent_lesson_id,
            duration_minutes=payload.duration_minutes,
            video_url=payload.video_url,
            is_preview=payload.is_preview,
            lesson_metadata=payload.metadata,
        )
        self.db.commit()
        return lesson

    def update_lesson(self, lesson_id: UUID, payload: LessonUpdate, current_user):
        lesson = self.lesson_repo.get_by_id(lesson_id)
        if not lesson:
            raise NotFoundException("Lesson not found")

        course = self.course_repo.get_by_id(lesson.course_id)
        if not course:
            raise NotFoundException("Course not found")

        self._ensure_manage_access(course, current_user)

        updates = payload.model_dump(exclude_unset=True)
        if "metadata" in updates:
            updates["lesson_metadata"] = updates.pop("metadata")

        lesson = self.lesson_repo.update(lesson, **updates)
        self.db.commit()
        return lesson

    def delete_lesson(self, lesson_id: UUID, current_user) -> None:
        lesson = self.lesson_repo.get_by_id(lesson_id)
        if not lesson:
            raise NotFoundException("Lesson not found")

        course = self.course_repo.get_by_id(lesson.course_id)
        if not course:
            raise NotFoundException("Course not found")

        self._ensure_manage_access(course, current_user)

        self.lesson_repo.delete(lesson)
        self.db.commit()

    @staticmethod
    def _can_manage(course, current_user) -> bool:
        if not current_user:
            return False
        if current_user.role == "admin":
            return True
        return current_user.role == "instructor" and course.instructor_id == current_user.id

    def _ensure_manage_access(self, course, current_user) -> None:
        if not self._can_manage(course, current_user):
            raise ForbiddenException("Not authorized to manage lessons for this course")
