from tests.helpers import auth_headers, register_user


def _create_published_course_with_lesson(client, instructor_headers):
    course = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "Analytics Course",
            "description": "For analytics tests",
            "category": "Data",
            "difficulty_level": "beginner",
        },
    )
    assert course.status_code == 201, course.text
    course_id = course.json()["id"]

    lesson = client.post(
        f"/api/v1/courses/{course_id}/lessons",
        headers=instructor_headers,
        json={
            "title": "Analytics Lesson",
            "lesson_type": "video",
            "order_index": 1,
            "duration_minutes": 5,
            "is_preview": True,
        },
    )
    assert lesson.status_code == 201, lesson.text

    publish = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish.status_code == 200, publish.text

    return course_id, lesson.json()["id"]


def test_student_and_course_analytics(client):
    instructor = register_user(
        client,
        email="analytics-instructor@example.com",
        password="StrongPass123",
        full_name="Analytics Instructor",
        role="instructor",
    )
    student = register_user(
        client,
        email="analytics-student@example.com",
        password="StrongPass123",
        full_name="Analytics Student",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])

    course_id, lesson_id = _create_published_course_with_lesson(client, instructor_headers)

    enrollment = client.post(
        "/api/v1/enrollments",
        headers=student_headers,
        json={"course_id": course_id},
    )
    assert enrollment.status_code == 201, enrollment.text
    enrollment_id = enrollment.json()["id"]

    progress = client.put(
        f"/api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/progress",
        headers=student_headers,
        json={"status": "completed", "completion_percentage": 100, "time_spent_seconds": 300},
    )
    assert progress.status_code == 200, progress.text

    my_progress = client.get("/api/v1/analytics/my-progress", headers=student_headers)
    assert my_progress.status_code == 200, my_progress.text
    assert my_progress.json()["total_enrollments"] == 1

    course_analytics = client.get(f"/api/v1/analytics/courses/{course_id}", headers=instructor_headers)
    assert course_analytics.status_code == 200, course_analytics.text
    assert course_analytics.json()["total_enrollments"] == 1


def test_system_overview_requires_admin(client):
    admin = register_user(
        client,
        email="analytics-admin@example.com",
        password="StrongPass123",
        full_name="Analytics Admin",
        role="admin",
    )
    student = register_user(
        client,
        email="analytics-student2@example.com",
        password="StrongPass123",
        full_name="Analytics Student Two",
        role="student",
    )

    student_headers = auth_headers(student["tokens"]["access_token"])
    admin_headers = auth_headers(admin["tokens"]["access_token"])

    forbidden = client.get("/api/v1/analytics/system/overview", headers=student_headers)
    assert forbidden.status_code == 403

    allowed = client.get("/api/v1/analytics/system/overview", headers=admin_headers)
    assert allowed.status_code == 200, allowed.text
    assert allowed.json()["total_users"] >= 2


def test_instructor_overview_counts_courses_distinctly(client):
    instructor = register_user(
        client,
        email="overview-instructor@example.com",
        password="StrongPass123",
        full_name="Overview Instructor",
        role="instructor",
    )
    student_one = register_user(
        client,
        email="overview-student1@example.com",
        password="StrongPass123",
        full_name="Overview Student One",
        role="student",
    )
    student_two = register_user(
        client,
        email="overview-student2@example.com",
        password="StrongPass123",
        full_name="Overview Student Two",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_one_headers = auth_headers(student_one["tokens"]["access_token"])
    student_two_headers = auth_headers(student_two["tokens"]["access_token"])

    course_id, _ = _create_published_course_with_lesson(client, instructor_headers)

    enroll_one = client.post("/api/v1/enrollments", headers=student_one_headers, json={"course_id": course_id})
    assert enroll_one.status_code == 201, enroll_one.text
    enroll_two = client.post("/api/v1/enrollments", headers=student_two_headers, json={"course_id": course_id})
    assert enroll_two.status_code == 201, enroll_two.text

    overview = client.get(
        f"/api/v1/analytics/instructors/{instructor['user']['id']}/overview",
        headers=instructor_headers,
    )
    assert overview.status_code == 200, overview.text
    payload = overview.json()
    assert payload["total_courses"] == 1
    assert payload["published_courses"] == 1
    assert payload["total_enrollments"] == 2
