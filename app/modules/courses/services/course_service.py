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
        search: str | None,
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
            search=search,
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

    def get_course_by_slug(self, slug: str, current_user, *, with_lessons: bool = False):
        course = self.repo.get_by_slug(slug)
        if not course:
            raise NotFoundException("Course not found")

        if with_lessons:
            course = self.repo.get_by_id(course.id, with_lessons=True)
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
            # Enhanced fields for frontend compatibility
            price=payload.price,
            currency=payload.currency,
            is_free=payload.is_free,
            long_description=payload.long_description,
            preview_video_url=payload.preview_video_url,
            requirements=payload.requirements,
            learning_objectives=payload.learning_objectives,
            total_reviews=payload.total_reviews,
            total_quizzes=payload.total_quizzes,
            enrollment_count=payload.enrollment_count,
            average_rating=payload.average_rating,
            status=payload.status,
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

        # Handle enhanced fields for frontend compatibility
        if "price" in updates:
            course.price = updates["price"]
        if "currency" in updates:
            course.currency = updates["currency"]
        if "is_free" in updates:
            course.is_free = updates["is_free"]
        if "long_description" in updates:
            course.long_description = updates["long_description"]
        if "preview_video_url" in updates:
            course.preview_video_url = updates["preview_video_url"]
        if "requirements" in updates:
            course.requirements = updates["requirements"]
        if "learning_objectives" in updates:
            course.learning_objectives = updates["learning_objectives"]
        if "total_reviews" in updates:
            course.total_reviews = updates["total_reviews"]
        if "total_quizzes" in updates:
            course.total_quizzes = updates["total_quizzes"]
        if "enrollment_count" in updates:
            course.enrollment_count = updates["enrollment_count"]
        if "average_rating" in updates:
            course.average_rating = updates["average_rating"]
        if "status" in updates:
            course.status = updates["status"]

        course = self.repo.update(course, **{k: v for k, v in updates.items() if k not in [
            "price", "currency", "is_free", "long_description", "preview_video_url",
            "requirements", "learning_objectives", "total_reviews", "total_quizzes",
            "enrollment_count", "average_rating", "status"
        ]})
        self._commit()
        return course

    def publish_course(self, course_id: UUID, current_user):
        course = self.repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("Course not found")

        self._ensure_manage_access(course, current_user)
        self._ensure_instructor_can_publish(current_user)

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

    def _ensure_instructor_can_publish(self, current_user) -> None:
        if current_user.role != Role.INSTRUCTOR.value:
            return

        from app.modules.instructors.models import Instructor

        instructor = (
            self.db.query(Instructor)
            .filter(Instructor.user_id == current_user.id)
            .first()
        )
        if not instructor or not instructor.is_verified:
            raise ForbiddenException("Instructor verification is required before publishing courses")

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
