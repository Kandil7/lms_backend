from tests.helpers import auth_headers, register_user


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

    enrollment = client.post(
        "/api/v1/enrollments",
        headers=student_headers,
        json={"course_id": course_id},
    )
    assert enrollment.status_code == 201, enrollment.text

    quiz = client.post(
        f"/api/v1/courses/{course_id}/quizzes",
        headers=instructor_headers,
        json={
            "lesson_id": lesson_id,
            "title": "Lesson Quiz",
            "quiz_type": "graded",
            "passing_score": 70,
            "max_attempts": 2,
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

    start_attempt = client.post(f"/api/v1/quizzes/{quiz_id}/attempts", headers=student_headers)
    assert start_attempt.status_code == 201, start_attempt.text
    attempt_id = start_attempt.json()["id"]

    questions_payload = client.get(f"/api/v1/quizzes/{quiz_id}/attempts/start", headers=student_headers)
    assert questions_payload.status_code == 200, questions_payload.text
    question_payload = questions_payload.json()["questions"][0]
    option_id = question_payload["options"][0]["option_id"]

    submit = client.post(
        f"/api/v1/quizzes/{quiz_id}/attempts/{attempt_id}/submit",
        headers=student_headers,
        json={"answers": [{"question_id": question_payload["id"], "selected_option_id": option_id}]},
    )
    assert submit.status_code == 200, submit.text
    assert submit.json()["status"] == "graded"
