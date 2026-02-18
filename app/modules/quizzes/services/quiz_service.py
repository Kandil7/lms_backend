from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import Role
from app.modules.courses.repositories.course_repository import CourseRepository
from app.modules.courses.repositories.lesson_repository import LessonRepository
from app.modules.quizzes.repositories.quiz_repository import QuizRepository
from app.modules.quizzes.schemas.quiz import QuizCreate, QuizUpdate


class QuizService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.course_repo = CourseRepository(db)
        self.lesson_repo = LessonRepository(db)
        self.quiz_repo = QuizRepository(db)

    def list_course_quizzes(self, course_id: UUID, current_user):
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("Course not found")

        can_manage = self._can_manage_course(course, current_user)
        if not can_manage and not course.is_published:
            raise ForbiddenException("Not authorized to view quizzes for this course")

        quizzes = self.quiz_repo.list_by_course(course_id)
        if can_manage:
            return quizzes

        return [quiz for quiz in quizzes if quiz.is_published]

    def list_course_quiz_items(self, course_id: UUID, current_user) -> list[dict]:
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("Course not found")

        can_manage = self._can_manage_course(course, current_user)
        if not can_manage and not course.is_published:
            raise ForbiddenException("Not authorized to view quizzes for this course")

        return self.quiz_repo.list_by_course_with_stats(course_id, published_only=not can_manage)

    def get_quiz(self, course_id: UUID, quiz_id: UUID, current_user, *, with_questions: bool = False):
        quiz = self.quiz_repo.get_by_id(quiz_id, with_questions=with_questions)
        if not quiz:
            raise NotFoundException("Quiz not found")

        lesson = self.lesson_repo.get_by_id(quiz.lesson_id)
        if not lesson or lesson.course_id != course_id:
            raise NotFoundException("Quiz not found in this course")

        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("Course not found")

        if not quiz.is_published and not self._can_manage_course(course, current_user):
            raise ForbiddenException("Not authorized to access this quiz")

        return quiz

    def create_quiz(self, course_id: UUID, payload: QuizCreate, current_user):
        course = self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("Course not found")

        self._ensure_manage_course(course, current_user)

        lesson = self.lesson_repo.get_by_id(payload.lesson_id)
        if not lesson or lesson.course_id != course_id:
            raise NotFoundException("Lesson not found in this course")

        if self.quiz_repo.get_by_lesson(payload.lesson_id):
            raise ValueError("Lesson already has a quiz")

        quiz = self.quiz_repo.create(
            lesson_id=payload.lesson_id,
            title=payload.title,
            description=payload.description,
            quiz_type=payload.quiz_type,
            time_limit_minutes=payload.time_limit_minutes,
            passing_score=payload.passing_score,
            max_attempts=payload.max_attempts,
            shuffle_questions=payload.shuffle_questions,
            shuffle_options=payload.shuffle_options,
            show_correct_answers=payload.show_correct_answers,
            is_published=False,
        )

        self.db.commit()
        return quiz

    def update_quiz(self, course_id: UUID, quiz_id: UUID, payload: QuizUpdate, current_user):
        quiz = self.get_quiz(course_id, quiz_id, current_user)

        course = self.course_repo.get_by_id(course_id)
        self._ensure_manage_course(course, current_user)

        updates = payload.model_dump(exclude_unset=True)
        quiz = self.quiz_repo.update(quiz, **updates)
        self.db.commit()
        return quiz

    def publish_quiz(self, course_id: UUID, quiz_id: UUID, current_user):
        quiz = self.get_quiz(course_id, quiz_id, current_user, with_questions=True)

        course = self.course_repo.get_by_id(course_id)
        self._ensure_manage_course(course, current_user)

        if len(quiz.questions) == 0:
            raise ValueError("Cannot publish quiz without questions")
        self._validate_questions_for_publish(quiz.questions)

        quiz = self.quiz_repo.update(quiz, is_published=True)
        self.db.commit()
        return quiz

    @staticmethod
    def _can_manage_course(course, current_user) -> bool:
        if not current_user:
            return False
        if current_user.role == Role.ADMIN.value:
            return True
        return current_user.role == Role.INSTRUCTOR.value and course.instructor_id == current_user.id

    def _ensure_manage_course(self, course, current_user) -> None:
        if not self._can_manage_course(course, current_user):
            raise ForbiddenException("Not authorized to manage quizzes for this course")

    @staticmethod
    def _validate_questions_for_publish(questions) -> None:
        for question in questions:
            if question.question_type == "multiple_choice":
                options = question.options or []
                if len(options) < 2:
                    raise ValueError("Cannot publish quiz with invalid multiple choice question options")
                option_ids: set[str] = set()
                option_texts: set[str] = set()
                for option in options:
                    option_id = str(option.get("option_id") or option.get("id") or "").strip()
                    option_text = str(option.get("option_text") or option.get("text") or "").strip()
                    if not option_id or not option_text:
                        raise ValueError("Cannot publish quiz with malformed multiple choice options")
                    if option_id in option_ids or option_text.lower() in option_texts:
                        raise ValueError("Cannot publish quiz with duplicate multiple choice options")
                    option_ids.add(option_id)
                    option_texts.add(option_text.lower())
                correct_count = sum(1 for option in options if option.get("is_correct") is True)
                if correct_count != 1:
                    raise ValueError("Cannot publish quiz with multiple choice questions missing a single correct option")
                if (question.correct_answer or "").strip():
                    raise ValueError("Cannot publish quiz with conflicting multiple choice correct_answer")
            elif question.question_type == "true_false":
                if question.options:
                    raise ValueError("Cannot publish quiz with options on true/false questions")
                normalized = (question.correct_answer or "").strip().lower()
                if normalized not in {"true", "false"}:
                    raise ValueError("Cannot publish quiz with invalid true/false correct answer")
            elif question.question_type == "short_answer":
                if question.options:
                    raise ValueError("Cannot publish quiz with options on short answer questions")
                if not (question.correct_answer or "").strip():
                    raise ValueError("Cannot publish quiz with empty short answer correct answer")
            elif question.question_type == "essay":
                if question.options:
                    raise ValueError("Cannot publish quiz with options on essay questions")
                if (question.correct_answer or "").strip():
                    raise ValueError("Cannot publish quiz with correct_answer on essay questions")
