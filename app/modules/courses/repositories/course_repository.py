from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.courses.models.course import Course


class CourseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, course_id: UUID, *, with_lessons: bool = False) -> Course | None:
        stmt = select(Course).where(Course.id == course_id)
        if with_lessons:
            stmt = stmt.options(selectinload(Course.lessons))
        return self.db.scalar(stmt)

    def get_by_slug(self, slug: str) -> Course | None:
        stmt = select(Course).where(Course.slug == slug)
        return self.db.scalar(stmt)

    def list(
        self,
        *,
        page: int,
        page_size: int,
        category: str | None = None,
        difficulty_level: str | None = None,
        published_only: bool = False,
        instructor_id: UUID | None = None,
    ) -> tuple[list[Course], int]:
        filters = []
        if category:
            filters.append(Course.category == category)
        if difficulty_level:
            filters.append(Course.difficulty_level == difficulty_level)
        if published_only:
            filters.append(Course.is_published.is_(True))
        if instructor_id:
            filters.append(Course.instructor_id == instructor_id)

        total_stmt = select(func.count()).select_from(Course)
        if filters:
            total_stmt = total_stmt.where(*filters)
        total = int(self.db.scalar(total_stmt) or 0)

        stmt = select(Course)
        if filters:
            stmt = stmt.where(*filters)
        stmt = stmt.order_by(Course.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        items = list(self.db.scalars(stmt).all())
        return items, total

    def create(self, **fields) -> Course:
        course = Course(**fields)
        self.db.add(course)
        self.db.flush()
        self.db.refresh(course)
        return course

    def update(self, course: Course, **fields) -> Course:
        for key, value in fields.items():
            if value is not None:
                setattr(course, key, value)

        self.db.add(course)
        self.db.flush()
        self.db.refresh(course)
        return course

    def delete(self, course: Course) -> None:
        self.db.delete(course)
        self.db.flush()
