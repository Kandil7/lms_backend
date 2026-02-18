from tests.helpers import auth_headers, register_user


def test_course_list_uses_cache_for_repeated_requests(client, monkeypatch):
    instructor = register_user(
        client,
        email="cache-instructor@example.com",
        password="StrongPass123",
        full_name="Cache Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    create_response = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "Cached Course",
            "description": "Caching list test",
            "category": "Programming",
            "difficulty_level": "beginner",
        },
    )
    assert create_response.status_code == 201, create_response.text
    course_id = create_response.json()["id"]

    publish_response = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish_response.status_code == 200, publish_response.text

    first_list = client.get("/api/v1/courses")
    assert first_list.status_code == 200, first_list.text
    assert first_list.json()["total"] == 1

    from app.modules.courses.services.course_service import CourseService

    def _raise_if_called(*args, **kwargs):
        raise RuntimeError("CourseService.list_courses should not be called on cache hit")

    monkeypatch.setattr(CourseService, "list_courses", _raise_if_called)

    second_list = client.get("/api/v1/courses")
    assert second_list.status_code == 200, second_list.text
    assert second_list.json()["total"] == 1


def test_course_list_cache_invalidates_after_publish(client):
    instructor = register_user(
        client,
        email="invalidate-instructor@example.com",
        password="StrongPass123",
        full_name="Invalidate Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    first_course = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "First Cached Course",
            "description": "First",
            "category": "Programming",
            "difficulty_level": "beginner",
        },
    )
    assert first_course.status_code == 201, first_course.text
    first_course_id = first_course.json()["id"]
    first_publish = client.post(f"/api/v1/courses/{first_course_id}/publish", headers=instructor_headers)
    assert first_publish.status_code == 200, first_publish.text

    first_list = client.get("/api/v1/courses")
    assert first_list.status_code == 200, first_list.text
    assert first_list.json()["total"] == 1

    second_course = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "Second Cached Course",
            "description": "Second",
            "category": "Programming",
            "difficulty_level": "beginner",
        },
    )
    assert second_course.status_code == 201, second_course.text
    second_course_id = second_course.json()["id"]
    second_publish = client.post(f"/api/v1/courses/{second_course_id}/publish", headers=instructor_headers)
    assert second_publish.status_code == 200, second_publish.text

    second_list = client.get("/api/v1/courses")
    assert second_list.status_code == 200, second_list.text
    assert second_list.json()["total"] == 2


def test_instructor_can_create_publish_course_and_students_can_list(client):
    instructor = register_user(
        client,
        email="instructor@example.com",
        password="StrongPass123",
        full_name="Instructor",
        role="instructor",
    )
    student = register_user(
        client,
        email="student2@example.com",
        password="StrongPass123",
        full_name="Student Two",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])

    create_response = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "Python Fundamentals",
            "description": "Learn core Python",
            "category": "Programming",
            "difficulty_level": "beginner",
        },
    )
    assert create_response.status_code == 201, create_response.text
    course_id = create_response.json()["id"]

    publish_response = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish_response.status_code == 200, publish_response.text

    list_response = client.get("/api/v1/courses", headers=student_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1


def test_non_manager_cannot_access_draft_lesson_even_if_preview(client):
    instructor = register_user(
        client,
        email="draft-instructor@example.com",
        password="StrongPass123",
        full_name="Draft Instructor",
        role="instructor",
    )
    student = register_user(
        client,
        email="draft-student@example.com",
        password="StrongPass123",
        full_name="Draft Student",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])

    course_response = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "Draft Course",
            "description": "Not published yet",
            "category": "Drafts",
            "difficulty_level": "beginner",
        },
    )
    assert course_response.status_code == 201, course_response.text
    course_id = course_response.json()["id"]

    lesson_response = client.post(
        f"/api/v1/courses/{course_id}/lessons",
        headers=instructor_headers,
        json={
            "title": "Draft Preview Lesson",
            "lesson_type": "video",
            "order_index": 1,
            "is_preview": True,
        },
    )
    assert lesson_response.status_code == 201, lesson_response.text
    lesson_id = lesson_response.json()["id"]

    student_fetch = client.get(f"/api/v1/lessons/{lesson_id}", headers=student_headers)
    assert student_fetch.status_code == 403, student_fetch.text

    anonymous_fetch = client.get(f"/api/v1/lessons/{lesson_id}")
    assert anonymous_fetch.status_code == 403, anonymous_fetch.text


def test_lesson_parent_must_be_in_same_course(client):
    instructor = register_user(
        client,
        email="parent-instructor@example.com",
        password="StrongPass123",
        full_name="Parent Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    course_a = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "Course A",
            "description": "A",
            "category": "CatA",
            "difficulty_level": "beginner",
        },
    )
    assert course_a.status_code == 201, course_a.text
    course_a_id = course_a.json()["id"]

    parent_lesson = client.post(
        f"/api/v1/courses/{course_a_id}/lessons",
        headers=instructor_headers,
        json={
            "title": "Parent Lesson A",
            "lesson_type": "text",
            "order_index": 1,
        },
    )
    assert parent_lesson.status_code == 201, parent_lesson.text
    parent_lesson_id = parent_lesson.json()["id"]

    course_b = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "Course B",
            "description": "B",
            "category": "CatB",
            "difficulty_level": "beginner",
        },
    )
    assert course_b.status_code == 201, course_b.text
    course_b_id = course_b.json()["id"]

    invalid_child = client.post(
        f"/api/v1/courses/{course_b_id}/lessons",
        headers=instructor_headers,
        json={
            "title": "Child In B",
            "lesson_type": "text",
            "order_index": 1,
            "parent_lesson_id": parent_lesson_id,
        },
    )
    assert invalid_child.status_code == 400, invalid_child.text
    assert "same course" in invalid_child.json()["detail"].lower()


def test_course_update_allows_clearing_nullable_fields(client):
    instructor = register_user(
        client,
        email="nullable-course-instructor@example.com",
        password="StrongPass123",
        full_name="Nullable Course Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    create_response = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "Nullable Course",
            "description": "Original description",
            "category": "Programming",
            "difficulty_level": "intermediate",
            "thumbnail_url": "https://example.com/thumb.png",
            "estimated_duration_minutes": 120,
        },
    )
    assert create_response.status_code == 201, create_response.text
    course_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/courses/{course_id}",
        headers=instructor_headers,
        json={
            "description": None,
            "category": None,
            "thumbnail_url": None,
            "estimated_duration_minutes": None,
        },
    )
    assert update_response.status_code == 200, update_response.text

    payload = update_response.json()
    assert payload["description"] is None
    assert payload["category"] is None
    assert payload["thumbnail_url"] is None
    assert payload["estimated_duration_minutes"] is None


def test_duplicate_lesson_order_index_returns_conflict(client):
    instructor = register_user(
        client,
        email="order-instructor@example.com",
        password="StrongPass123",
        full_name="Order Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    create_course = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "Order Course",
            "description": "Order checks",
            "category": "Backend",
            "difficulty_level": "beginner",
        },
    )
    assert create_course.status_code == 201, create_course.text
    course_id = create_course.json()["id"]

    first_lesson = client.post(
        f"/api/v1/courses/{course_id}/lessons",
        headers=instructor_headers,
        json={
            "title": "Lesson 1",
            "lesson_type": "video",
            "order_index": 1,
        },
    )
    assert first_lesson.status_code == 201, first_lesson.text

    duplicate_lesson = client.post(
        f"/api/v1/courses/{course_id}/lessons",
        headers=instructor_headers,
        json={
            "title": "Lesson 2",
            "lesson_type": "video",
            "order_index": 1,
        },
    )
    assert duplicate_lesson.status_code == 409, duplicate_lesson.text
