from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.modules.quizzes.repositories.question_repository import QuestionRepository
from app.modules.quizzes.schemas.question import QuestionCreate, QuestionUpdate
from app.modules.quizzes.services.quiz_service import QuizService


class QuestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.quiz_service = QuizService(db)
        self.repo = QuestionRepository(db)

    def add_question(self, course_id: UUID, quiz_id: UUID, payload: QuestionCreate, current_user):
        quiz = self.quiz_service.get_quiz(course_id, quiz_id, current_user, with_questions=False)
        course = self.quiz_service.course_repo.get_by_id(course_id)
        self.quiz_service._ensure_manage_course(course, current_user)

        order_index = self.repo.get_next_order_index(quiz_id)
        options = [option.model_dump() for option in payload.options] if payload.options else None
        self._validate_question_payload(
            question_type=payload.question_type,
            options=options,
            correct_answer=payload.correct_answer,
        )

        question = self.repo.create(
            quiz_id=quiz.id,
            question_text=payload.question_text,
            question_type=payload.question_type,
            points=payload.points,
            order_index=order_index,
            explanation=payload.explanation,
            options=options,
            correct_answer=payload.correct_answer,
            question_metadata=payload.metadata,
        )

        self.db.commit()
        return question

    def update_question(
        self,
        course_id: UUID,
        quiz_id: UUID,
        question_id: UUID,
        payload: QuestionUpdate,
        current_user,
    ):
        quiz = self.quiz_service.get_quiz(course_id, quiz_id, current_user, with_questions=False)
        course = self.quiz_service.course_repo.get_by_id(course_id)
        self.quiz_service._ensure_manage_course(course, current_user)

        question = self.repo.get_by_id(question_id)
        if not question or question.quiz_id != quiz.id:
            raise NotFoundException("Question not found")

        updates = payload.model_dump(exclude_unset=True)
        if "options" in updates and updates["options"] is not None:
            normalized_options = []
            for option in updates["options"]:
                if isinstance(option, dict):
                    normalized_options.append(option)
                else:
                    normalized_options.append(option.model_dump())
            updates["options"] = normalized_options
        if "metadata" in updates:
            updates["question_metadata"] = updates.pop("metadata")

        resolved_question_type = updates.get("question_type", question.question_type)
        resolved_options = updates.get("options", question.options)
        resolved_correct_answer = updates.get("correct_answer", question.correct_answer)
        self._validate_question_payload(
            question_type=resolved_question_type,
            options=resolved_options,
            correct_answer=resolved_correct_answer,
        )

        question = self.repo.update(question, **updates)
        self.db.commit()
        return question

    def list_quiz_questions(self, course_id: UUID, quiz_id: UUID, current_user):
        quiz = self.quiz_service.get_quiz(course_id, quiz_id, current_user, with_questions=False)
        return self.repo.list_by_quiz(quiz.id)

    def list_quiz_questions_for_management(self, course_id: UUID, quiz_id: UUID, current_user):
        quiz = self.quiz_service.get_quiz(course_id, quiz_id, current_user, with_questions=False)
        course = self.quiz_service.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("Course not found")
        self.quiz_service._ensure_manage_course(course, current_user)
        return self.repo.list_by_quiz(quiz.id)

    @staticmethod
    def _validate_question_payload(
        *,
        question_type: str,
        options: list[dict] | None,
        correct_answer: str | None,
    ) -> None:
        if question_type == "multiple_choice":
            if not options or len(options) < 2:
                raise ValueError("Multiple choice questions must have at least 2 options")
            option_ids: set[str] = set()
            option_texts: set[str] = set()
            for option in options:
                option_id = str(option.get("option_id") or option.get("id") or "").strip()
                option_text = str(option.get("option_text") or option.get("text") or "").strip()
                if not option_id:
                    raise ValueError("Each multiple choice option must include an option_id")
                if not option_text:
                    raise ValueError("Each multiple choice option must include non-empty option_text")
                if option_id in option_ids:
                    raise ValueError("Multiple choice options must have unique option_id values")
                normalized_text = option_text.lower()
                if normalized_text in option_texts:
                    raise ValueError("Multiple choice options must have unique option_text values")
                option_ids.add(option_id)
                option_texts.add(normalized_text)
            correct_count = sum(1 for option in options if option.get("is_correct") is True)
            if correct_count != 1:
                raise ValueError("Multiple choice questions must have exactly 1 correct option")
            if (correct_answer or "").strip():
                raise ValueError("Multiple choice questions must not set correct_answer directly")
            return

        if question_type == "true_false":
            if options:
                raise ValueError("True/false questions must not include options")
            normalized = (correct_answer or "").strip().lower()
            if normalized not in {"true", "false"}:
                raise ValueError("True/false questions require correct_answer to be 'true' or 'false'")
            return

        if question_type == "short_answer":
            if options:
                raise ValueError("Short answer questions must not include options")
            if not (correct_answer or "").strip():
                raise ValueError("Short answer questions require a non-empty correct_answer")
            return

        if question_type == "essay":
            if options:
                raise ValueError("Essay questions must not include options")
            if (correct_answer or "").strip():
                raise ValueError("Essay questions must not include correct_answer")
