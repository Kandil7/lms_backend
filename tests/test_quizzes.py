from datetime import UTC, datetime, timedelta
import logging
from uuid import UUID
from uuid import uuid4

from sqlalchemy import select

from app.modules.enrollments.models import Enrollment
from app.modules.quizzes.models.attempt import QuizAttempt
from tests.helpers import auth_headers, register_user


def _create_course_lesson_and_quiz(
    client,
    instructor_headers: dict[str, str],
    *,
    show_correct_answers: bool = True,
    max_attempts: int = 2,
) -> tuple[str, str, str]:
    course = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "Quiz Course",
            "description": "Course with quiz",
            "category": "Testing",
            "difficulty_level": "beginner",
        },
    )
    assert course.status_code == 201, course.text
    course_id = course.json()["id"]

    lesson = client.post(
        f"/api/v1/courses/{course_id}/lessons",
        headers=instructor_headers,
        json={
            "title": "Quiz Lesson",
            "lesson_type": "quiz",
            "order_index": 1,
            "is_preview": True,
        },
    )
    assert lesson.status_code == 201, lesson.text
    lesson_id = lesson.json()["id"]

    publish_course = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish_course.status_code == 200, publish_course.text

    quiz = client.post(
        f"/api/v1/courses/{course_id}/quizzes",
        headers=instructor_headers,
        json={
            "lesson_id": lesson_id,
            "title": "Lesson Quiz",
            "quiz_type": "graded",
            "passing_score": 70,
            "max_attempts": max_attempts,
            "show_correct_answers": show_correct_answers,
        },
    )
    assert quiz.status_code == 201, quiz.text
    quiz_id = quiz.json()["id"]

    question = client.post(
        f"/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions",
        headers=instructor_headers,
        json={
            "question_text": "2 + 2 = ?",
            "question_type": "multiple_choice",
            "points": 5,
            "options": [
                {"option_text": "4", "is_correct": True},
                {"option_text": "5", "is_correct": False},
            ],
        },
    )
    assert question.status_code == 201, question.text

    publish_quiz = client.post(
        f"/api/v1/courses/{course_id}/quizzes/{quiz_id}/publish",
        headers=instructor_headers,
    )
    assert publish_quiz.status_code == 200, publish_quiz.text
    return course_id, lesson_id, quiz_id


def _enroll_student(client, student_headers: dict[str, str], course_id: str) -> None:
    enrollment = client.post(
        "/api/v1/enrollments",
        headers=student_headers,
        json={"course_id": course_id},
    )
    assert enrollment.status_code == 201, enrollment.text


def _start_attempt_and_pick_correct_option(client, student_headers: dict[str, str], quiz_id: str) -> tuple[str, str, str]:
    start_attempt = client.post(f"/api/v1/quizzes/{quiz_id}/attempts", headers=student_headers)
    assert start_attempt.status_code == 201, start_attempt.text
    attempt_id = start_attempt.json()["id"]

    questions_payload = client.get(f"/api/v1/quizzes/{quiz_id}/attempts/start", headers=student_headers)
    assert questions_payload.status_code == 200, questions_payload.text
    question_payload = questions_payload.json()["questions"][0]
    option_id = next(
        option["option_id"]
        for option in question_payload["options"]
        if option["option_text"] == "4"
    )
    return attempt_id, question_payload["id"], option_id


def test_quiz_attempt_grading_flow(client):
    instructor = register_user(
        client,
        email="quiz-instructor@example.com",
        password="StrongPass123",
        full_name="Quiz Instructor",
        role="instructor",
    )
    student = register_user(
        client,
        email="quiz-student@example.com",
        password="StrongPass123",
        full_name="Quiz Student",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])
    course_id, _, quiz_id = _create_course_lesson_and_quiz(client, instructor_headers)
    _enroll_student(client, student_headers, course_id)
    attempt_id, question_id, option_id = _start_attempt_and_pick_correct_option(client, student_headers, quiz_id)

    submit = client.post(
        f"/api/v1/quizzes/{quiz_id}/attempts/{attempt_id}/submit",
        headers=student_headers,
        json={"answers": [{"question_id": question_id, "selected_option_id": option_id}]},
    )
    assert submit.status_code == 200, submit.text
    assert submit.json()["status"] == "graded"


def test_questions_endpoint_hides_answers_for_students(client):
    instructor = register_user(
        client,
        email="quiz-instructor-2@example.com",
        password="StrongPass123",
        full_name="Quiz Instructor 2",
        role="instructor",
    )
    student = register_user(
        client,
        email="quiz-student-2@example.com",
        password="StrongPass123",
        full_name="Quiz Student 2",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])
    course_id, _, quiz_id = _create_course_lesson_and_quiz(client, instructor_headers)
    _enroll_student(client, student_headers, course_id)

    student_questions = client.get(
        f"/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions",
        headers=student_headers,
    )
    assert student_questions.status_code == 200, student_questions.text
    first_public = student_questions.json()[0]
    assert "correct_answer" not in first_public
    assert all("is_correct" not in option for option in (first_public.get("options") or []))

    manage_questions = client.get(
        f"/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions/manage",
        headers=instructor_headers,
    )
    assert manage_questions.status_code == 200, manage_questions.text
    first_manage = manage_questions.json()[0]
    assert "options" in first_manage
    assert any("is_correct" in option for option in (first_manage.get("options") or []))

    student_manage = client.get(
        f"/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions/manage",
        headers=student_headers,
    )
    assert student_manage.status_code == 403, student_manage.text


def test_show_correct_answers_false_masks_attempt_results(client):
    instructor = register_user(
        client,
        email="quiz-instructor-3@example.com",
        password="StrongPass123",
        full_name="Quiz Instructor 3",
        role="instructor",
    )
    student = register_user(
        client,
        email="quiz-student-3@example.com",
        password="StrongPass123",
        full_name="Quiz Student 3",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])
    course_id, _, quiz_id = _create_course_lesson_and_quiz(
        client,
        instructor_headers,
        show_correct_answers=False,
    )
    _enroll_student(client, student_headers, course_id)
    attempt_id, question_id, option_id = _start_attempt_and_pick_correct_option(client, student_headers, quiz_id)

    submit = client.post(
        f"/api/v1/quizzes/{quiz_id}/attempts/{attempt_id}/submit",
        headers=student_headers,
        json={"answers": [{"question_id": question_id, "selected_option_id": option_id}]},
    )
    assert submit.status_code == 200, submit.text
    first_submit_answer = submit.json()["answers"][0]
    assert "is_correct" not in first_submit_answer
    assert "points_earned" not in first_submit_answer

    attempt_result = client.get(
        f"/api/v1/quizzes/{quiz_id}/attempts/{attempt_id}",
        headers=student_headers,
    )
    assert attempt_result.status_code == 200, attempt_result.text
    first_result_answer = attempt_result.json()["answers"][0]
    assert "is_correct" not in first_result_answer
    assert "points_earned" not in first_result_answer


def test_cannot_start_second_in_progress_attempt(client):
    instructor = register_user(
        client,
        email="quiz-instructor-4@example.com",
        password="StrongPass123",
        full_name="Quiz Instructor 4",
        role="instructor",
    )
    student = register_user(
        client,
        email="quiz-student-4@example.com",
        password="StrongPass123",
        full_name="Quiz Student 4",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])
    course_id, _, quiz_id = _create_course_lesson_and_quiz(client, instructor_headers, max_attempts=3)
    _enroll_student(client, student_headers, course_id)

    start_first = client.post(f"/api/v1/quizzes/{quiz_id}/attempts", headers=student_headers)
    assert start_first.status_code == 201, start_first.text

    start_second = client.post(f"/api/v1/quizzes/{quiz_id}/attempts", headers=student_headers)
    assert start_second.status_code == 403, start_second.text
    assert start_second.json()["detail"] == "You already have an in-progress attempt"


def test_time_limit_expired_attempt_is_rejected_and_new_attempt_allowed(client, db_session):
    instructor = register_user(
        client,
        email="quiz-instructor-5@example.com",
        password="StrongPass123",
        full_name="Quiz Instructor 5",
        role="instructor",
    )
    student = register_user(
        client,
        email="quiz-student-5@example.com",
        password="StrongPass123",
        full_name="Quiz Student 5",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])

    course_id, _, quiz_id = _create_course_lesson_and_quiz(
        client,
        instructor_headers,
        max_attempts=3,
    )
    _enroll_student(client, student_headers, course_id)

    update_quiz = client.patch(
        f"/api/v1/courses/{course_id}/quizzes/{quiz_id}",
        headers=instructor_headers,
        json={"time_limit_minutes": 1},
    )
    assert update_quiz.status_code == 200, update_quiz.text

    attempt_id, question_id, option_id = _start_attempt_and_pick_correct_option(client, student_headers, quiz_id)

    attempt = db_session.scalar(select(QuizAttempt).where(QuizAttempt.id == UUID(attempt_id)))
    assert attempt is not None
    attempt.started_at = datetime.now(UTC) - timedelta(minutes=2)
    db_session.add(attempt)
    db_session.commit()

    submit = client.post(
        f"/api/v1/quizzes/{quiz_id}/attempts/{attempt_id}/submit",
        headers=student_headers,
        json={"answers": [{"question_id": question_id, "selected_option_id": option_id}]},
    )
    assert submit.status_code == 403, submit.text
    assert submit.json()["detail"] == "Time limit exceeded for this attempt"

    start_new = client.post(f"/api/v1/quizzes/{quiz_id}/attempts", headers=student_headers)
    assert start_new.status_code == 201, start_new.text


def test_cannot_publish_quiz_without_questions(client):
    instructor = register_user(
        client,
        email="quiz-instructor-6@example.com",
        password="StrongPass123",
        full_name="Quiz Instructor 6",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    course = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "Quiz Publish Validation",
            "description": "Validation course",
            "category": "Testing",
            "difficulty_level": "beginner",
        },
    )
    assert course.status_code == 201, course.text
    course_id = course.json()["id"]

    lesson = client.post(
        f"/api/v1/courses/{course_id}/lessons",
        headers=instructor_headers,
        json={
            "title": "No Question Lesson",
            "lesson_type": "quiz",
            "order_index": 1,
            "is_preview": True,
        },
    )
    assert lesson.status_code == 201, lesson.text
    lesson_id = lesson.json()["id"]

    publish_course = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish_course.status_code == 200, publish_course.text

    quiz = client.post(
        f"/api/v1/courses/{course_id}/quizzes",
        headers=instructor_headers,
        json={
            "lesson_id": lesson_id,
            "title": "Empty Quiz",
            "quiz_type": "graded",
            "passing_score": 70,
        },
    )
    assert quiz.status_code == 201, quiz.text
    quiz_id = quiz.json()["id"]

    publish_quiz = client.post(
        f"/api/v1/courses/{course_id}/quizzes/{quiz_id}/publish",
        headers=instructor_headers,
    )
    assert publish_quiz.status_code == 400, publish_quiz.text
    assert publish_quiz.json()["detail"] == "Cannot publish quiz without questions"


def test_reject_invalid_multiple_choice_question(client):
    instructor = register_user(
        client,
        email="quiz-instructor-7@example.com",
        password="StrongPass123",
        full_name="Quiz Instructor 7",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    course_id, _, quiz_id = _create_course_lesson_and_quiz(client, instructor_headers)

    invalid_question = client.post(
        f"/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions",
        headers=instructor_headers,
        json={
            "question_text": "Invalid MCQ",
            "question_type": "multiple_choice",
            "points": 1,
            "options": [
                {"option_text": "A", "is_correct": False},
                {"option_text": "B", "is_correct": False},
            ],
        },
    )
    assert invalid_question.status_code == 400, invalid_question.text
    assert invalid_question.json()["detail"] == "Multiple choice questions must have exactly 1 correct option"


def test_quiz_list_uses_cache(client, monkeypatch):
    instructor = register_user(
        client,
        email="quiz-cache-instructor@example.com",
        password="StrongPass123",
        full_name="Quiz Cache Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    course_id, _, _ = _create_course_lesson_and_quiz(client, instructor_headers)

    first_list = client.get(f"/api/v1/courses/{course_id}/quizzes")
    assert first_list.status_code == 200, first_list.text
    assert first_list.json()["total"] == 1

    from app.modules.quizzes.services.quiz_service import QuizService

    def _raise_if_called(*args, **kwargs):
        raise RuntimeError("QuizService.list_course_quiz_items should not be called on cache hit")

    monkeypatch.setattr(QuizService, "list_course_quiz_items", _raise_if_called)

    second_list = client.get(f"/api/v1/courses/{course_id}/quizzes")
    assert second_list.status_code == 200, second_list.text
    assert second_list.json()["total"] == 1


def test_quiz_cache_invalidates_after_question_change(client):
    instructor = register_user(
        client,
        email="quiz-invalidate-instructor@example.com",
        password="StrongPass123",
        full_name="Quiz Invalidate Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    course_id, _, quiz_id = _create_course_lesson_and_quiz(client, instructor_headers)

    first_list = client.get(f"/api/v1/courses/{course_id}/quizzes", headers=instructor_headers)
    assert first_list.status_code == 200, first_list.text
    assert first_list.json()["quizzes"][0]["total_questions"] == 1

    add_question = client.post(
        f"/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions",
        headers=instructor_headers,
        json={
            "question_text": "3 + 3 = ?",
            "question_type": "multiple_choice",
            "points": 2,
            "options": [
                {"option_text": "6", "is_correct": True},
                {"option_text": "7", "is_correct": False},
            ],
        },
    )
    assert add_question.status_code == 201, add_question.text

    second_list = client.get(f"/api/v1/courses/{course_id}/quizzes", headers=instructor_headers)
    assert second_list.status_code == 200, second_list.text
    assert second_list.json()["quizzes"][0]["total_questions"] == 2


def test_dropped_enrollment_cannot_start_quiz_attempt(client, db_session):
    instructor = register_user(
        client,
        email="quiz-enrollment-instructor@example.com",
        password="StrongPass123",
        full_name="Quiz Enrollment Instructor",
        role="instructor",
    )
    student = register_user(
        client,
        email="quiz-enrollment-student@example.com",
        password="StrongPass123",
        full_name="Quiz Enrollment Student",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])
    course_id, _, quiz_id = _create_course_lesson_and_quiz(client, instructor_headers)
    _enroll_student(client, student_headers, course_id)

    enrollment = db_session.scalar(
        select(Enrollment).where(
            Enrollment.student_id == UUID(student["user"]["id"]),
            Enrollment.course_id == UUID(course_id),
        )
    )
    assert enrollment is not None
    enrollment.status = "dropped"
    db_session.add(enrollment)
    db_session.commit()

    start_attempt = client.post(f"/api/v1/quizzes/{quiz_id}/attempts", headers=student_headers)
    assert start_attempt.status_code == 403, start_attempt.text
    assert start_attempt.json()["detail"] == "Enrollment status does not allow quiz attempts"


def test_submit_rejects_invalid_selected_option(client):
    instructor = register_user(
        client,
        email="quiz-invalid-option-instructor@example.com",
        password="StrongPass123",
        full_name="Quiz Invalid Option Instructor",
        role="instructor",
    )
    student = register_user(
        client,
        email="quiz-invalid-option-student@example.com",
        password="StrongPass123",
        full_name="Quiz Invalid Option Student",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])
    course_id, _, quiz_id = _create_course_lesson_and_quiz(client, instructor_headers)
    _enroll_student(client, student_headers, course_id)
    attempt_id, question_id, _ = _start_attempt_and_pick_correct_option(client, student_headers, quiz_id)

    submit = client.post(
        f"/api/v1/quizzes/{quiz_id}/attempts/{attempt_id}/submit",
        headers=student_headers,
        json={"answers": [{"question_id": question_id, "selected_option_id": "invalid-option-id"}]},
    )
    assert submit.status_code == 400, submit.text
    assert submit.json()["detail"] == "Selected option does not belong to the question"


def test_submit_rejects_duplicate_answer_for_same_question(client):
    instructor = register_user(
        client,
        email="quiz-duplicate-answer-instructor@example.com",
        password="StrongPass123",
        full_name="Quiz Duplicate Answer Instructor",
        role="instructor",
    )
    student = register_user(
        client,
        email="quiz-duplicate-answer-student@example.com",
        password="StrongPass123",
        full_name="Quiz Duplicate Answer Student",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])
    course_id, _, quiz_id = _create_course_lesson_and_quiz(client, instructor_headers)
    _enroll_student(client, student_headers, course_id)
    attempt_id, question_id, option_id = _start_attempt_and_pick_correct_option(client, student_headers, quiz_id)

    submit = client.post(
        f"/api/v1/quizzes/{quiz_id}/attempts/{attempt_id}/submit",
        headers=student_headers,
        json={
            "answers": [
                {"question_id": question_id, "selected_option_id": option_id},
                {"question_id": question_id, "selected_option_id": option_id},
            ]
        },
    )
    assert submit.status_code == 400, submit.text
    assert submit.json()["detail"] == "Duplicate answer for the same question is not allowed"


def test_submit_rejects_answer_for_unknown_question(client):
    instructor = register_user(
        client,
        email="quiz-unknown-question-instructor@example.com",
        password="StrongPass123",
        full_name="Quiz Unknown Question Instructor",
        role="instructor",
    )
    student = register_user(
        client,
        email="quiz-unknown-question-student@example.com",
        password="StrongPass123",
        full_name="Quiz Unknown Question Student",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])
    course_id, _, quiz_id = _create_course_lesson_and_quiz(client, instructor_headers)
    _enroll_student(client, student_headers, course_id)
    attempt_id, _, _ = _start_attempt_and_pick_correct_option(client, student_headers, quiz_id)

    submit = client.post(
        f"/api/v1/quizzes/{quiz_id}/attempts/{attempt_id}/submit",
        headers=student_headers,
        json={"answers": [{"question_id": str(uuid4()), "selected_option_id": "x"}]},
    )
    assert submit.status_code == 400, submit.text
    assert submit.json()["detail"] == "Answer contains a question that does not belong to this quiz"


def test_quiz_attempt_audit_logging(client, caplog):
    instructor = register_user(
        client,
        email="quiz-audit-instructor@example.com",
        password="StrongPass123",
        full_name="Quiz Audit Instructor",
        role="instructor",
    )
    student = register_user(
        client,
        email="quiz-audit-student@example.com",
        password="StrongPass123",
        full_name="Quiz Audit Student",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])
    course_id, _, quiz_id = _create_course_lesson_and_quiz(client, instructor_headers)
    _enroll_student(client, student_headers, course_id)

    caplog.set_level(logging.INFO, logger="app.quiz.audit")
    attempt_id, question_id, option_id = _start_attempt_and_pick_correct_option(client, student_headers, quiz_id)

    submit = client.post(
        f"/api/v1/quizzes/{quiz_id}/attempts/{attempt_id}/submit",
        headers=student_headers,
        json={"answers": [{"question_id": question_id, "selected_option_id": option_id}]},
    )
    assert submit.status_code == 200, submit.text

    messages = [record.message for record in caplog.records if record.name == "app.quiz.audit"]
    assert any("quiz_attempt_started" in message for message in messages)
    assert any("quiz_attempt_submitted" in message for message in messages)
