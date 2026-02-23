from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from datetime import UTC, datetime

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import Base, engine, session_scope
from app.core.security import hash_password
from app.modules.certificates.models import Certificate
from app.modules.certificates.service import CertificateService
from app.modules.courses.repositories.course_repository import CourseRepository
from app.modules.courses.repositories.lesson_repository import LessonRepository
from app.modules.enrollments.repository import EnrollmentRepository
from app.modules.enrollments.service import EnrollmentService
from app.modules.quizzes.repositories.attempt_repository import AttemptRepository
from app.modules.quizzes.repositories.question_repository import QuestionRepository
from app.modules.quizzes.repositories.quiz_repository import QuizRepository
from app.modules.quizzes.schemas.attempt import AnswerSubmission, AttemptSubmitRequest
from app.modules.quizzes.services.attempt_service import AttemptService
from app.modules.users.repositories.user_repository import UserRepository


DEMO_USERS = {
    "admin": {
        "email": "admin@lms.local",
        "password": "AdminPass123",
        "full_name": "Demo Admin",
        "role": "admin",
    },
    "instructor": {
        "email": "instructor@lms.local",
        "password": "InstructorPass123",
        "full_name": "Demo Instructor",
        "role": "instructor",
    },
    "student": {
        "email": "student@lms.local",
        "password": "StudentPass123",
        "full_name": "Demo Student",
        "role": "student",
    },
}

COURSE_SLUG = "python-lms-demo-course"
LESSON_BLUEPRINTS = [
    {
        "slug": "welcome-overview",
        "title": "Welcome and Overview",
        "lesson_type": "video",
        "duration_minutes": 12,
        "is_preview": True,
    },
    {
        "slug": "python-basics",
        "title": "Python Basics",
        "lesson_type": "text",
        "duration_minutes": 18,
        "is_preview": False,
    },
    {
        "slug": "final-knowledge-check",
        "title": "Final Knowledge Check",
        "lesson_type": "quiz",
        "duration_minutes": 10,
        "is_preview": False,
    },
]


def _import_models() -> None:
    import app.modules.auth.models  # noqa: F401
    import app.modules.certificates.models  # noqa: F401
    import app.modules.courses.models  # noqa: F401
    import app.modules.enrollments.models  # noqa: F401
    import app.modules.files.models  # noqa: F401
    import app.modules.quizzes.models  # noqa: F401
    import app.modules.users.models  # noqa: F401


def ensure_user(repo: UserRepository, *, email: str, password: str, full_name: str, role: str, reset_password: bool):
    user = repo.get_by_email(email)
    if not user:
        return repo.create(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True,
            email_verified_at=datetime.now(UTC),
        )

    changed = False
    if user.role != role:
        user.role = role
        changed = True
    if user.full_name != full_name:
        user.full_name = full_name
        changed = True
    if not user.is_active:
        user.is_active = True
        changed = True
    if reset_password:
        user.password_hash = hash_password(password)
        changed = True

    if changed:
        if user.email_verified_at is None:
            user.email_verified_at = datetime.now(UTC)
            changed = True
        repo.update(
            user,
            role=user.role,
            full_name=user.full_name,
            is_active=user.is_active,
            password_hash=user.password_hash,
            email_verified_at=user.email_verified_at,
        )

    return user


def ensure_course(course_repo: CourseRepository, instructor_id):
    course = course_repo.get_by_slug(COURSE_SLUG)
    if not course:
        return course_repo.create(
            title="Python LMS Demo Course",
            slug=COURSE_SLUG,
            description="Demo course seeded automatically.",
            instructor_id=instructor_id,
            category="Programming",
            difficulty_level="beginner",
            thumbnail_url=None,
            estimated_duration_minutes=40,
            course_metadata={"seeded": True},
            is_published=True,
        )

    return course_repo.update(
        course,
        title="Python LMS Demo Course",
        description="Demo course seeded automatically.",
        instructor_id=instructor_id,
        category="Programming",
        difficulty_level="beginner",
        estimated_duration_minutes=40,
        course_metadata={"seeded": True},
        is_published=True,
    )


def ensure_lessons(lesson_repo: LessonRepository, course_id):
    existing = {lesson.slug: lesson for lesson in lesson_repo.list_by_course(course_id)}
    created_or_updated = []

    for index, blueprint in enumerate(LESSON_BLUEPRINTS, start=1):
        lesson = existing.get(blueprint["slug"])
        if not lesson:
            lesson = lesson_repo.create(
                course_id=course_id,
                title=blueprint["title"],
                slug=blueprint["slug"],
                description=f"{blueprint['title']} lesson",
                content=f"Auto-seeded content for {blueprint['title']}",
                lesson_type=blueprint["lesson_type"],
                order_index=index,
                parent_lesson_id=None,
                duration_minutes=blueprint["duration_minutes"],
                video_url=None,
                is_preview=blueprint["is_preview"],
                lesson_metadata={"seeded": True},
            )
        else:
            lesson = lesson_repo.update(
                lesson,
                title=blueprint["title"],
                lesson_type=blueprint["lesson_type"],
                order_index=index,
                duration_minutes=blueprint["duration_minutes"],
                is_preview=blueprint["is_preview"],
            )

        created_or_updated.append(lesson)

    return created_or_updated


def ensure_quiz_and_questions(quiz_repo: QuizRepository, question_repo: QuestionRepository, lesson_id):
    quiz = quiz_repo.get_by_lesson(lesson_id)
    if not quiz:
        quiz = quiz_repo.create(
            lesson_id=lesson_id,
            title="Final Quiz",
            description="Assess understanding of course basics.",
            quiz_type="graded",
            passing_score=70,
            time_limit_minutes=20,
            max_attempts=3,
            shuffle_questions=True,
            shuffle_options=True,
            show_correct_answers=True,
            is_published=True,
        )
    else:
        quiz = quiz_repo.update(
            quiz,
            title="Final Quiz",
            description="Assess understanding of course basics.",
            quiz_type="graded",
            passing_score=70,
            time_limit_minutes=20,
            max_attempts=3,
            shuffle_questions=True,
            shuffle_options=True,
            show_correct_answers=True,
            is_published=True,
        )

    questions = question_repo.list_by_quiz(quiz.id)
    if not questions:
        question_repo.create(
            quiz_id=quiz.id,
            question_text="What does LMS stand for?",
            question_type="multiple_choice",
            points=5,
            order_index=1,
            explanation="LMS stands for Learning Management System.",
            options=[
                {"option_id": "lms-opt-1", "option_text": "Learning Management System", "is_correct": True},
                {"option_id": "lms-opt-2", "option_text": "Lesson Monitoring Service", "is_correct": False},
                {"option_id": "lms-opt-3", "option_text": "Learning Material Suite", "is_correct": False},
            ],
            correct_answer=None,
            question_metadata={"seeded": True},
        )
        question_repo.create(
            quiz_id=quiz.id,
            question_text="Write the HTTP method used to fetch resources.",
            question_type="short_answer",
            points=5,
            order_index=2,
            explanation="GET is used for retrieving resources.",
            options=None,
            correct_answer="GET",
            question_metadata={"seeded": True},
        )

    return quiz


def ensure_quiz_attempt(attempt_service: AttemptService, attempt_repo: AttemptRepository, question_repo: QuestionRepository, *, enrollment_id, quiz_id, student):
    attempts = attempt_repo.list_by_enrollment(enrollment_id, quiz_id)
    graded_exists = any(attempt.status == "graded" for attempt in attempts)
    if graded_exists:
        return

    in_progress = next((attempt for attempt in attempts if attempt.status == "in_progress"), None)
    if not in_progress:
        in_progress = attempt_service.start_attempt(quiz_id, student)

    questions = question_repo.list_by_quiz(quiz_id)
    answers: list[AnswerSubmission] = []

    for question in questions:
        if question.question_type == "multiple_choice":
            options = question.options or []
            correct = next((item for item in options if item.get("is_correct") is True), None)
            if not correct:
                continue
            option_id = correct.get("option_id") or correct.get("id")
            answers.append(AnswerSubmission(question_id=question.id, selected_option_id=str(option_id)))
        elif question.question_type in {"true_false", "short_answer"}:
            answers.append(AnswerSubmission(question_id=question.id, answer_text=str(question.correct_answer or "")))

    payload = AttemptSubmitRequest(answers=answers)
    attempt_service.submit_attempt(quiz_id, in_progress.id, payload, student)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed demo LMS data")
    parser.add_argument("--create-tables", action="store_true", help="Create tables before seeding")
    parser.add_argument("--reset-passwords", action="store_true", help="Reset demo user passwords if they exist")
    parser.add_argument("--skip-attempt", action="store_true", help="Skip creating quiz attempt")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Optional output path for seed snapshot JSON (relative to repo root if not absolute)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    _import_models()
    if args.create_tables:
        Base.metadata.create_all(bind=engine)

    with session_scope() as db:
        user_repo = UserRepository(db)
        course_repo = CourseRepository(db)
        lesson_repo = LessonRepository(db)
        enrollment_repo = EnrollmentRepository(db)
        quiz_repo = QuizRepository(db)
        question_repo = QuestionRepository(db)
        attempt_repo = AttemptRepository(db)

        admin = ensure_user(user_repo, reset_password=args.reset_passwords, **DEMO_USERS["admin"])
        instructor = ensure_user(user_repo, reset_password=args.reset_passwords, **DEMO_USERS["instructor"])
        student = ensure_user(user_repo, reset_password=args.reset_passwords, **DEMO_USERS["student"])

        course = ensure_course(course_repo, instructor.id)
        lessons = ensure_lessons(lesson_repo, course.id)
        quiz_lesson = next(lesson for lesson in lessons if lesson.lesson_type == "quiz")
        quiz = ensure_quiz_and_questions(quiz_repo, question_repo, quiz_lesson.id)

        db.commit()

        enrollment_service = EnrollmentService(db)
        enrollment = enrollment_service.enroll(student.id, course.id)

        for lesson in lessons:
            if lesson.lesson_type != "quiz":
                enrollment_service.mark_lesson_completed(enrollment.id, lesson.id, student)

        if not args.skip_attempt:
            attempt_service = AttemptService(db)
            ensure_quiz_attempt(
                attempt_service,
                attempt_repo,
                question_repo,
                enrollment_id=enrollment.id,
                quiz_id=quiz.id,
                student=student,
            )

        db.commit()

        attempts = attempt_repo.list_by_enrollment(enrollment.id, quiz.id)
        latest_attempt = attempts[-1] if attempts else None
        questions = question_repo.list_by_quiz(quiz.id)
        db.refresh(enrollment)
        certificate = db.scalar(select(Certificate).where(Certificate.enrollment_id == enrollment.id))
        if enrollment.status == "completed" and certificate is None:
            certificate = CertificateService(db).issue_for_enrollment(enrollment, commit=False)

        db.commit()
        seed_snapshot = {
            "generated_at": datetime.now(UTC).isoformat(),
            "credentials": {
                "admin": DEMO_USERS["admin"],
                "instructor": DEMO_USERS["instructor"],
                "student": DEMO_USERS["student"],
            },
            "users": {
                "admin": {"id": str(admin.id), "email": admin.email, "full_name": admin.full_name},
                "instructor": {"id": str(instructor.id), "email": instructor.email, "full_name": instructor.full_name},
                "student": {"id": str(student.id), "email": student.email, "full_name": student.full_name},
            },
            "course": {
                "id": str(course.id),
                "slug": course.slug,
                "title": course.title,
            },
            "lessons": [
                {
                    "id": str(lesson.id),
                    "slug": lesson.slug,
                    "title": lesson.title,
                    "lesson_type": lesson.lesson_type,
                }
                for lesson in lessons
            ],
            "quiz": {
                "id": str(quiz.id),
                "lesson_id": str(quiz.lesson_id),
                "title": quiz.title,
            },
            "questions": [
                {
                    "id": str(question.id),
                    "question_type": question.question_type,
                    "question_text": question.question_text,
                }
                for question in questions
            ],
            "enrollment": {
                "id": str(enrollment.id),
                "student_id": str(enrollment.student_id),
                "course_id": str(enrollment.course_id),
                "status": enrollment.status,
            },
            "attempt": (
                {
                    "id": str(latest_attempt.id),
                    "attempt_number": latest_attempt.attempt_number,
                    "status": latest_attempt.status,
                }
                if latest_attempt
                else None
            ),
            "certificate": (
                {
                    "id": str(certificate.id),
                    "certificate_number": certificate.certificate_number,
                    "is_revoked": certificate.is_revoked,
                    "pdf_path": certificate.pdf_path,
                }
                if certificate
                else None
            ),
        }

        if args.json_output is not None:
            output_path = args.json_output
            if not output_path.is_absolute():
                output_path = ROOT / output_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(seed_snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Seed snapshot written to: {output_path}")

        print("Demo seed completed successfully.")
        print("Credentials:")
        print(f"- admin: {DEMO_USERS['admin']['email']} / {DEMO_USERS['admin']['password']}")
        print(f"- instructor: {DEMO_USERS['instructor']['email']} / {DEMO_USERS['instructor']['password']}")
        print(f"- student: {DEMO_USERS['student']['email']} / {DEMO_USERS['student']['password']}")
        print("Generated IDs:")
        print(f"- course_id: {course.id}")
        print(f"- enrollment_id: {enrollment.id}")
        print(f"- quiz_id: {quiz.id}")


if __name__ == "__main__":
    main()
