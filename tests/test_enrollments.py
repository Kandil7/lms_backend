from tests.helpers import auth_headers, register_user


def test_student_enrollment_and_progress_completion(client):
    instructor = register_user(
        client,
        email="instructor2@example.com",
        password="StrongPass123",
        full_name="Instructor Two",
        role="instructor",
    )
    student = register_user(
        client,
        email="student3@example.com",
        password="StrongPass123",
        full_name="Student Three",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])

    create_course = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "Backend API Course",
            "description": "Building APIs",
            "category": "Backend",
            "difficulty_level": "intermediate",
        },
    )
    assert create_course.status_code == 201, create_course.text
    course_id = create_course.json()["id"]

    publish_course = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish_course.status_code == 200, publish_course.text

    create_lesson = client.post(
        f"/api/v1/courses/{course_id}/lessons",
        headers=instructor_headers,
        json={
            "title": "Intro Lesson",
            "lesson_type": "video",
            "order_index": 1,
            "duration_minutes": 10,
            "is_preview": True,
        },
    )
    assert create_lesson.status_code == 201, create_lesson.text
    lesson_id = create_lesson.json()["id"]

    enrollment_response = client.post(
        "/api/v1/enrollments",
        headers=student_headers,
        json={"course_id": course_id},
    )
    assert enrollment_response.status_code == 201, enrollment_response.text
    enrollment_id = enrollment_response.json()["id"]

    progress_response = client.put(
        f"/api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/progress",
        headers=student_headers,
        json={
            "status": "completed",
            "completion_percentage": 100,
            "time_spent_seconds": 600,
        },
    )
    assert progress_response.status_code == 200, progress_response.text

    enrollment_details = client.get(f"/api/v1/enrollments/{enrollment_id}", headers=student_headers)
    assert enrollment_details.status_code == 200
    data = enrollment_details.json()
    assert float(data["progress_percentage"]) == 100.0
    assert data["status"] == "completed"
