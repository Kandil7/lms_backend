from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.courses.models.lesson import Lesson


class LessonRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, lesson_id: UUID) -> Lesson | None:
        stmt = select(Lesson).where(Lesson.id == lesson_id)
        return self.db.scalar(stmt)

    def list_by_course(self, course_id: UUID) -> list[Lesson]:
        stmt = select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.order_index.asc())
        return list(self.db.scalars(stmt).all())

    def count_by_course(self, course_id: UUID) -> int:
        stmt = select(func.count()).select_from(Lesson).where(Lesson.course_id == course_id)
        return int(self.db.scalar(stmt) or 0)

    def get_next_order_index(self, course_id: UUID) -> int:
        stmt = select(func.max(Lesson.order_index)).where(Lesson.course_id == course_id)
        max_value = self.db.scalar(stmt)
        return int(max_value or 0) + 1

    def create(self, **fields) -> Lesson:
        lesson = Lesson(**fields)
        self.db.add(lesson)
        self.db.flush()
        self.db.refresh(lesson)
        return lesson

    def update(self, lesson: Lesson, **fields) -> Lesson:
        for key, value in fields.items():
            setattr(lesson, key, value)

        self.db.add(lesson)
        self.db.flush()
        self.db.refresh(lesson)
        return lesson

    def delete(self, lesson: Lesson) -> None:
        self.db.delete(lesson)
        self.db.flush()
