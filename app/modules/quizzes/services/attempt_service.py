import random
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import Role
from app.modules.courses.repositories.lesson_repository import LessonRepository
from app.modules.enrollments.repository import EnrollmentRepository
from app.modules.enrollments.service import EnrollmentService
from app.modules.quizzes.repositories.attempt_repository import AttemptRepository
from app.modules.quizzes.repositories.question_repository import QuestionRepository
from app.modules.quizzes.repositories.quiz_repository import QuizRepository
from app.modules.quizzes.schemas.attempt import AttemptSubmitRequest


class AttemptService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.quiz_repo = QuizRepository(db)
        self.question_repo = QuestionRepository(db)
        self.attempt_repo = AttemptRepository(db)
        self.lesson_repo = LessonRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)

    def start_attempt(self, quiz_id: UUID, current_user):
        if current_user.role != Role.STUDENT.value:
            raise ForbiddenException("Only students can start quiz attempts")

        quiz = self.quiz_repo.get_by_id(quiz_id, with_questions=True)
        if not quiz:
            raise NotFoundException("Quiz not found")

        if not quiz.is_published:
            raise ForbiddenException("Quiz is not published")

        enrollment = self._get_student_enrollment_for_quiz(quiz, current_user.id)

        latest_attempt_number = self.attempt_repo.get_latest_attempt_number(enrollment.id, quiz.id)
        if quiz.max_attempts and latest_attempt_number >= quiz.max_attempts:
            raise ForbiddenException("Maximum attempts reached")

        max_score = self.quiz_repo.total_points(quiz.id)
        attempt = self.attempt_repo.create(
            enrollment_id=enrollment.id,
            quiz_id=quiz.id,
            attempt_number=latest_attempt_number + 1,
            status="in_progress",
            max_score=max_score,
        )
        self.db.commit()
        return attempt

    def get_quiz_for_taking(self, quiz_id: UUID, current_user) -> dict:
        quiz = self.quiz_repo.get_by_id(quiz_id, with_questions=True)
        if not quiz:
            raise NotFoundException("Quiz not found")

        if current_user.role == Role.STUDENT.value:
            self._get_student_enrollment_for_quiz(quiz, current_user.id)
            if not quiz.is_published:
                raise ForbiddenException("Quiz is not published")

        questions = [self._sanitize_question(question, quiz.shuffle_options) for question in quiz.questions]
        if quiz.shuffle_questions:
            random.shuffle(questions)

        return {
            "quiz": {
                "id": quiz.id,
                "title": quiz.title,
                "time_limit_minutes": quiz.time_limit_minutes,
                "total_questions": len(questions),
                "total_points": self.quiz_repo.total_points(quiz.id),
            },
            "questions": questions,
        }

    def submit_attempt(
        self,
        quiz_id: UUID,
        attempt_id: UUID,
        payload: AttemptSubmitRequest,
        current_user,
    ):
        if current_user.role != Role.STUDENT.value:
            raise ForbiddenException("Only students can submit attempts")

        quiz = self.quiz_repo.get_by_id(quiz_id, with_questions=True)
        if not quiz:
            raise NotFoundException("Quiz not found")

        enrollment = self._get_student_enrollment_for_quiz(quiz, current_user.id)

        attempt = self.attempt_repo.get_by_id(attempt_id)
        if not attempt or attempt.enrollment_id != enrollment.id or attempt.quiz_id != quiz.id:
            raise NotFoundException("Attempt not found")

        if attempt.status != "in_progress":
            raise ForbiddenException("Attempt is already submitted")

        now = datetime.now(UTC)
        answer_map = {str(answer.question_id): answer for answer in payload.answers}

        graded_answers: list[dict] = []
        total_score = Decimal("0.00")

        for question in quiz.questions:
            submitted = answer_map.get(str(question.id))
            result = self._grade_question(question, submitted)
            graded_answers.append(result)
            total_score += Decimal(str(result["points_earned"]))

        max_score = self.quiz_repo.total_points(quiz.id)
        percentage = self.attempt_repo.calculate_percentage(total_score, max_score)
        passed = percentage >= Decimal(str(quiz.passing_score))
        time_taken = int((now - attempt.started_at).total_seconds()) if attempt.started_at else None

        attempt = self.attempt_repo.update(
            attempt,
            status="graded",
            submitted_at=now,
            graded_at=now,
            score=total_score,
            max_score=max_score,
            percentage=percentage,
            is_passed=passed,
            time_taken_seconds=time_taken,
            answers=graded_answers,
        )

        if passed:
            EnrollmentService(self.db).mark_lesson_completed(enrollment.id, quiz.lesson_id, current_user)

        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def list_my_attempts(self, quiz_id: UUID, current_user):
        if current_user.role != Role.STUDENT.value:
            raise ForbiddenException("Only students can access own attempts")

        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise NotFoundException("Quiz not found")

        enrollment = self._get_student_enrollment_for_quiz(quiz, current_user.id)
        return self.attempt_repo.list_by_enrollment(enrollment.id, quiz_id)

    def get_attempt(self, quiz_id: UUID, attempt_id: UUID, current_user):
        if current_user.role != Role.STUDENT.value:
            raise ForbiddenException("Only students can access own attempts")

        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise NotFoundException("Quiz not found")

        enrollment = self._get_student_enrollment_for_quiz(quiz, current_user.id)

        attempt = self.attempt_repo.get_by_id(attempt_id)
        if not attempt or attempt.enrollment_id != enrollment.id or attempt.quiz_id != quiz_id:
            raise NotFoundException("Attempt not found")

        return attempt

    def _get_student_enrollment_for_quiz(self, quiz, student_id: UUID):
        lesson = self.lesson_repo.get_by_id(quiz.lesson_id)
        if not lesson:
            raise NotFoundException("Quiz lesson not found")

        enrollment = self.enrollment_repo.get_by_student_and_course(student_id, lesson.course_id)
        if not enrollment:
            raise ForbiddenException("You must enroll in course before attempting quiz")

        return enrollment

    @staticmethod
    def _sanitize_question(question, shuffle_options: bool) -> dict:
        options = None
        if question.options:
            options = [
                {
                    "option_id": option.get("option_id") or option.get("id"),
                    "option_text": option.get("option_text") or option.get("text"),
                }
                for option in question.options
            ]
            if shuffle_options:
                random.shuffle(options)

        return {
            "id": question.id,
            "question_text": question.question_text,
            "question_type": question.question_type,
            "points": question.points,
            "options": options,
        }

    @staticmethod
    def _grade_question(question, submitted_answer) -> dict:
        is_correct = False
        points_earned = Decimal("0.00")

        selected_option_id = submitted_answer.selected_option_id if submitted_answer else None
        answer_text = submitted_answer.answer_text.strip() if submitted_answer and submitted_answer.answer_text else None

        if question.question_type == "multiple_choice":
            options = question.options or []
            correct_option = next((option for option in options if option.get("is_correct") is True), None)
            if correct_option:
                correct_id = correct_option.get("option_id") or correct_option.get("id")
                is_correct = selected_option_id == correct_id

        elif question.question_type == "true_false":
            is_correct = bool(answer_text) and answer_text.lower() == str(question.correct_answer or "").strip().lower()

        elif question.question_type == "short_answer":
            is_correct = bool(answer_text) and answer_text.lower() == str(question.correct_answer or "").strip().lower()

        elif question.question_type == "essay":
            is_correct = False

        if is_correct:
            points_earned = Decimal(str(question.points))

        return {
            "question_id": str(question.id),
            "selected_option_id": selected_option_id,
            "answer_text": answer_text,
            "is_correct": is_correct,
            "points_earned": float(points_earned),
        }
