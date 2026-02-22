import random
import logging
import copy
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.cache import get_app_cache
from app.core.config import settings
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import Role
from app.core.webhooks import emit_webhook_event
from app.modules.courses.repositories.lesson_repository import LessonRepository
from app.modules.enrollments.repository import EnrollmentRepository
from app.modules.enrollments.service import EnrollmentService
from app.modules.quizzes.repositories.attempt_repository import AttemptRepository
from app.modules.quizzes.repositories.question_repository import QuestionRepository
from app.modules.quizzes.repositories.quiz_repository import QuizRepository
from app.modules.quizzes.schemas.attempt import AnswerSubmission, AttemptSubmitRequest

logger = logging.getLogger("app.quiz.audit")


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

        enrollment = self._get_student_enrollment_for_quiz(quiz, current_user.id, for_update=True)
        now = datetime.now(UTC)
        in_progress = self.attempt_repo.get_in_progress_for_update(enrollment.id, quiz.id)
        if in_progress:
            if self._is_time_limit_exceeded(in_progress, quiz, now):
                self._expire_attempt_due_to_time_limit(in_progress, quiz, now)
            else:
                raise ForbiddenException("You already have an in-progress attempt")

        max_score = self._calculate_total_points(quiz)
        for _ in range(2):
            latest_attempt_number = self.attempt_repo.get_latest_attempt_number_for_update(enrollment.id, quiz.id)
            if quiz.max_attempts and latest_attempt_number >= quiz.max_attempts:
                raise ForbiddenException("Maximum attempts reached")

            try:
                attempt = self.attempt_repo.create(
                    enrollment_id=enrollment.id,
                    quiz_id=quiz.id,
                    attempt_number=latest_attempt_number + 1,
                    status="in_progress",
                    max_score=max_score,
                )
                self.db.commit()
                logger.info(
                    "quiz_attempt_started quiz_id=%s attempt_id=%s enrollment_id=%s student_id=%s attempt_number=%s",
                    quiz.id,
                    attempt.id,
                    enrollment.id,
                    current_user.id,
                    attempt.attempt_number,
                )
                return attempt
            except IntegrityError:
                self.db.rollback()
                existing = self.attempt_repo.get_in_progress_for_update(enrollment.id, quiz.id)
                if existing:
                    if self._is_time_limit_exceeded(existing, quiz, datetime.now(UTC)):
                        self._expire_attempt_due_to_time_limit(existing, quiz, datetime.now(UTC))
                        continue
                    raise ForbiddenException("You already have an in-progress attempt")

        raise ValueError("Could not start quiz attempt, please retry")

    def get_quiz_for_taking(self, quiz_id: UUID, current_user) -> dict:
        quiz = self.quiz_repo.get_by_id(quiz_id, with_questions=True)
        if not quiz:
            raise NotFoundException("Quiz not found")

        if current_user.role == Role.STUDENT.value:
            self._get_student_enrollment_for_quiz(quiz, current_user.id)
            if not quiz.is_published:
                raise ForbiddenException("Quiz is not published")

        payload = copy.deepcopy(self._get_quiz_take_base_payload(quiz))
        questions = payload["questions"]
        if quiz.shuffle_options:
            for question in questions:
                if question.get("options"):
                    random.shuffle(question["options"])
        if quiz.shuffle_questions:
            random.shuffle(questions)

        payload["questions"] = questions
        return payload

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

        attempt = self.attempt_repo.get_by_id_for_update(attempt_id)
        if not attempt or attempt.enrollment_id != enrollment.id or attempt.quiz_id != quiz.id:
            raise NotFoundException("Attempt not found")

        if attempt.status != "in_progress":
            raise ForbiddenException("Attempt is already submitted")

        now = datetime.now(UTC)
        answer_map = self._validate_and_build_answer_map(quiz, payload)
        if self._is_time_limit_exceeded(attempt, quiz, now):
            self._expire_attempt_due_to_time_limit(attempt, quiz, now)
            raise ForbiddenException("Time limit exceeded for this attempt")

        graded_answers: list[dict] = []
        total_score = Decimal("0.00")

        for question in quiz.questions:
            submitted = answer_map.get(str(question.id))
            result = self._grade_question(question, submitted)
            graded_answers.append(result)
            total_score += Decimal(str(result["points_earned"]))

        max_score = self._calculate_total_points(quiz)
        percentage = self.attempt_repo.calculate_percentage(total_score, max_score)
        passed = percentage >= Decimal(str(quiz.passing_score))
        started_at = attempt.started_at
        if started_at and started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=UTC)
        time_taken = int((now - started_at).total_seconds()) if started_at else None

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
        emit_webhook_event(
            "quiz.submitted",
            {
                "attempt_id": str(attempt.id),
                "quiz_id": str(quiz.id),
                "enrollment_id": str(enrollment.id),
                "student_id": str(current_user.id),
                "percentage": str(attempt.percentage) if attempt.percentage is not None else None,
                "is_passed": attempt.is_passed,
                "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
            },
        )
        logger.info(
            "quiz_attempt_submitted quiz_id=%s attempt_id=%s enrollment_id=%s student_id=%s percentage=%s passed=%s",
            quiz.id,
            attempt.id,
            enrollment.id,
            current_user.id,
            attempt.percentage,
            attempt.is_passed,
        )
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

    def build_attempt_result_answers(self, quiz_id: UUID, answers: list[dict] | None) -> list[dict] | None:
        quiz = self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise NotFoundException("Quiz not found")
        return self._mask_attempt_answers(answers, reveal_correct=quiz.show_correct_answers)

    def _get_student_enrollment_for_quiz(self, quiz, student_id: UUID, *, for_update: bool = False):
        lesson = self.lesson_repo.get_by_id(quiz.lesson_id)
        if not lesson:
            raise NotFoundException("Quiz lesson not found")

        if for_update:
            enrollment = self.enrollment_repo.get_by_student_and_course_for_update(student_id, lesson.course_id)
        else:
            enrollment = self.enrollment_repo.get_by_student_and_course(student_id, lesson.course_id)
        if not enrollment:
            raise ForbiddenException("You must enroll in course before attempting quiz")
        if enrollment.status not in {"active", "completed"}:
            raise ForbiddenException("Enrollment status does not allow quiz attempts")

        return enrollment

    def _get_quiz_take_base_payload(self, quiz) -> dict:
        cache = get_app_cache()
        cache_key = f"quiz_take:base:quiz={quiz.id}"
        cached_payload = cache.get_json(cache_key)
        if cached_payload is not None:
            return cached_payload

        payload = {
            "quiz": {
                "id": str(quiz.id),
                "title": quiz.title,
                "time_limit_minutes": quiz.time_limit_minutes,
                "total_questions": len(quiz.questions),
                "total_points": str(self._calculate_total_points(quiz)),
            },
            "questions": [self._sanitize_question(question, False) for question in quiz.questions],
        }
        cache.set_json(cache_key, payload, ttl_seconds=settings.QUIZ_CACHE_TTL_SECONDS)
        return payload

    @staticmethod
    def _validate_and_build_answer_map(quiz, payload: AttemptSubmitRequest) -> dict[str, AnswerSubmission]:
        question_map = {str(question.id): question for question in quiz.questions}
        seen_ids: set[str] = set()
        answer_map: dict[str, AnswerSubmission] = {}

        for answer in payload.answers:
            question_id = str(answer.question_id)
            if question_id in seen_ids:
                raise ValueError("Duplicate answer for the same question is not allowed")
            seen_ids.add(question_id)

            question = question_map.get(question_id)
            if question is None:
                raise ValueError("Answer contains a question that does not belong to this quiz")

            if question.question_type == "multiple_choice":
                if not answer.selected_option_id:
                    raise ValueError("Multiple choice answers require selected_option_id")
                valid_option_ids = {
                    str(option.get("option_id") or option.get("id"))
                    for option in (question.options or [])
                    if option.get("option_id") is not None or option.get("id") is not None
                }
                if str(answer.selected_option_id) not in valid_option_ids:
                    raise ValueError("Selected option does not belong to the question")
            else:
                if answer.selected_option_id is not None:
                    raise ValueError("selected_option_id is only valid for multiple choice questions")
                normalized_answer = (answer.answer_text or "").strip()
                if question.question_type in {"true_false", "short_answer", "essay"} and not normalized_answer:
                    raise ValueError("Answer text is required for this question type")
                if question.question_type == "true_false" and normalized_answer.lower() not in {"true", "false"}:
                    raise ValueError("True/false answers must be either 'true' or 'false'")

            answer_map[question_id] = answer

        return answer_map

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
            "id": str(question.id),
            "question_text": question.question_text,
            "question_type": question.question_type,
            "points": str(question.points),
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

    @staticmethod
    def _calculate_total_points(quiz) -> Decimal:
        total = sum((Decimal(str(question.points)) for question in quiz.questions), Decimal("0.00"))
        return total.quantize(Decimal("0.01"))

    @staticmethod
    def _is_time_limit_exceeded(attempt, quiz, now: datetime) -> bool:
        if not quiz.time_limit_minutes:
            return False
        started_at = attempt.started_at
        if not started_at:
            return False
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=UTC)
        return now > started_at + timedelta(minutes=quiz.time_limit_minutes)

    def _expire_attempt_due_to_time_limit(self, attempt, quiz, now: datetime) -> None:
        started_at = attempt.started_at
        if started_at and started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=UTC)
        time_taken = int((now - started_at).total_seconds()) if started_at else None
        max_score = attempt.max_score if attempt.max_score is not None else self._calculate_total_points(quiz)
        self.attempt_repo.update(
            attempt,
            status="graded",
            submitted_at=now,
            graded_at=now,
            score=Decimal("0.00"),
            max_score=max_score,
            percentage=Decimal("0.00"),
            is_passed=False,
            time_taken_seconds=time_taken,
            answers=attempt.answers or [],
        )
        self.db.commit()
        logger.info(
            "quiz_attempt_expired quiz_id=%s attempt_id=%s enrollment_id=%s started_at=%s expired_at=%s",
            quiz.id,
            attempt.id,
            attempt.enrollment_id,
            started_at,
            now,
        )

    @staticmethod
    def _mask_attempt_answers(answers: list[dict] | None, *, reveal_correct: bool) -> list[dict] | None:
        if answers is None:
            return None
        if reveal_correct:
            return answers

        masked_answers: list[dict] = []
        for answer in answers:
            masked = dict(answer)
            masked.pop("is_correct", None)
            masked.pop("points_earned", None)
            masked_answers.append(masked)
        return masked_answers
