from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import Role
from app.core.webhooks import emit_webhook_event
from app.modules.courses.repositories.course_repository import CourseRepository
from app.modules.courses.schemas.course import CourseCreate, CourseUpdate
from app.utils.pagination import PageParams, paginate
from app.utils.validators import slugify


class CourseService:
    NON_NULLABLE_UPDATE_FIELDS = {"title", "is_published"}

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CourseRepository(db)

    def list_courses(
        self,
        *,
        page: int,
        page_size: int,
        category: str | None,
        difficulty_level: str | None,
        current_user,
        mine: bool = False,
    ) -> dict:
        published_only = True
        instructor_id = None

        if current_user and current_user.role == Role.ADMIN.value:
            published_only = False
            if mine:
                instructor_id = current_user.id
        elif current_user and current_user.role == Role.INSTRUCTOR.value:
            if mine:
                published_only = False
                instructor_id = current_user.id

        courses, total = self.repo.list(
            page=page,
            page_size=page_size,
            category=category,
            difficulty_level=difficulty_level,
            published_only=published_only,
            instructor_id=instructor_id,
        )

        return paginate(courses, total, PageParams(page=page, page_size=page_size))

    def get_course(self, course_id: UUID, current_user, *, with_lessons: bool = False):
        course = self.repo.get_by_id(course_id, with_lessons=with_lessons)
        if not course:
            raise NotFoundException("Course not found")

        if not course.is_published and not self._can_manage_course(course, current_user):
            raise ForbiddenException("Not authorized to access this course")

        return course

    def create_course(self, payload: CourseCreate, current_user):
        if current_user.role not in {Role.ADMIN.value, Role.INSTRUCTOR.value}:
            raise ForbiddenException("Only instructors or admins can create courses")

        slug = payload.slug or slugify(payload.title)
        if self.repo.get_by_slug(slug):
            raise ValueError("Course slug already exists")

        course = self.repo.create(
            title=payload.title,
            slug=slug,
            description=payload.description,
            instructor_id=current_user.id,
            category=payload.category,
            difficulty_level=payload.difficulty_level,
            thumbnail_url=payload.thumbnail_url,
            estimated_duration_minutes=payload.estimated_duration_minutes,
            course_metadata=payload.metadata,
            is_published=False,
        )
        self._commit()
        return course

    def update_course(self, course_id: UUID, payload: CourseUpdate, current_user):
        course = self.repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("Course not found")

        self._ensure_manage_access(course, current_user)

        updates = payload.model_dump(exclude_unset=True)
        self._validate_nullable_updates(updates)
        if "metadata" in updates:
            updates["course_metadata"] = updates.pop("metadata")

        course = self.repo.update(course, **updates)
        self._commit()
        return course

    def publish_course(self, course_id: UUID, current_user):
        course = self.repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("Course not found")

        self._ensure_manage_access(course, current_user)

        course = self.repo.update(course, is_published=True)
        self._commit()
        emit_webhook_event(
            "course.published",
            {
                "course_id": str(course.id),
                "instructor_id": str(course.instructor_id),
                "published_at": course.updated_at.isoformat(),
            },
        )
        return course

    def delete_course(self, course_id: UUID, current_user) -> None:
        course = self.repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("Course not found")

        self._ensure_manage_access(course, current_user)
        self.repo.delete(course)
        self._commit()

    def _can_manage_course(self, course, current_user) -> bool:
        if not current_user:
            return False
        if current_user.role == Role.ADMIN.value:
            return True
        return current_user.role == Role.INSTRUCTOR.value and course.instructor_id == current_user.id

    def _ensure_manage_access(self, course, current_user) -> None:
        if not self._can_manage_course(course, current_user):
            raise ForbiddenException("Not authorized to manage this course")

    def _commit(self) -> None:
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise
        except Exception:
            self.db.rollback()
            raise

    def _validate_nullable_updates(self, updates: dict) -> None:
        for field in self.NON_NULLABLE_UPDATE_FIELDS:
            if field in updates and updates[field] is None:
                raise ValueError(f"'{field}' cannot be null")
