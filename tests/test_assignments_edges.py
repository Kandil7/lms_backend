from __future__ import annotations

from uuid import uuid4

from tests.helpers import auth_headers, register_user


def _create_instructor_with_course(client, *, suffix: str) -> tuple[dict, dict[str, str], str]:
    instructor = register_user(
        client,
        email=f"instructor-{suffix}@example.com",
        password="StrongPass123",
        full_name=f"Instructor {suffix}",
        role="instructor",
    )
    headers = auth_headers(instructor["tokens"]["access_token"])
    course_response = client.post(
        "/api/v1/courses",
        headers=headers,
        json={
            "title": f"Course {suffix}",
            "description": "Edge-case course",
            "category": "Testing",
            "difficulty_level": "beginner",
            "is_published": True,
        },
    )
    assert course_response.status_code == 201, course_response.text
    course_id = course_response.json()["id"]
    publish_response = client.post(f"/api/v1/courses/{course_id}/publish", headers=headers)
    assert publish_response.status_code == 200, publish_response.text
    return instructor, headers, course_id


def _create_assignment(client, *, headers: dict[str, str], course_id: str, title: str) -> str:
    response = client.post(
        "/api/v1/assignments",
        headers=headers,
        json={
            "title": title,
            "course_id": course_id,
            "status": "published",
            "is_published": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _enroll_student(client, *, suffix: str, course_id: str) -> tuple[dict, dict[str, str], str]:
    student = register_user(
        client,
        email=f"student-{suffix}@example.com",
        password="StrongPass123",
        full_name=f"Student {suffix}",
        role="student",
    )
    headers = auth_headers(student["tokens"]["access_token"])
    enrollment_response = client.post(
        "/api/v1/enrollments",
        headers=headers,
        json={"course_id": course_id},
    )
    assert enrollment_response.status_code == 201, enrollment_response.text
    return student, headers, enrollment_response.json()["id"]


def test_create_assignment_access_errors(client) -> None:
    _, instructor_headers, _ = _create_instructor_with_course(client, suffix="a1")
    response = client.post(
        "/api/v1/assignments",
        headers=instructor_headers,
        json={"title": "Missing Course", "course_id": str(uuid4())},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Course not found"

    _, owner_headers, owner_course_id = _create_instructor_with_course(client, suffix="a2")
    _, other_headers, _ = _create_instructor_with_course(client, suffix="a3")
    assignment_response = client.post(
        "/api/v1/assignments",
        headers=other_headers,
        json={"title": "Forbidden", "course_id": owner_course_id},
    )
    assert assignment_response.status_code == 403
    assert "permission" in assignment_response.json()["detail"].lower()

    # control assertion to ensure owner can create on the same course
    control = client.post(
        "/api/v1/assignments",
        headers=owner_headers,
        json={"title": "Allowed", "course_id": owner_course_id},
    )
    assert control.status_code == 201


def test_assignments_listing_requires_course_access(client) -> None:
    _, instructor_headers, course_id = _create_instructor_with_course(client, suffix="b1")
    _create_assignment(client, headers=instructor_headers, course_id=course_id, title="A1")

    _, student_headers, _ = _enroll_student(client, suffix="b2", course_id=course_id)
    allowed_response = client.get(f"/api/v1/assignments/course/{course_id}", headers=student_headers)
    assert allowed_response.status_code == 200

    other_student = register_user(
        client,
        email="student-b3@example.com",
        password="StrongPass123",
        full_name="Student b3",
        role="student",
    )
    other_student_headers = auth_headers(other_student["tokens"]["access_token"])
    forbidden_response = client.get(f"/api/v1/assignments/course/{course_id}", headers=other_student_headers)
    assert forbidden_response.status_code == 403


def test_submit_assignment_error_paths(client) -> None:
    _, instructor_headers, course_a = _create_instructor_with_course(client, suffix="c1")
    course_b_response = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "Course c1-b",
            "description": "Second course for mismatch path",
            "category": "Testing",
            "difficulty_level": "beginner",
            "is_published": True,
        },
    )
    assert course_b_response.status_code == 201, course_b_response.text
    course_b = course_b_response.json()["id"]
    publish_b = client.post(f"/api/v1/courses/{course_b}/publish", headers=instructor_headers)
    assert publish_b.status_code == 200, publish_b.text

    assignment_b = _create_assignment(client, headers=instructor_headers, course_id=course_b, title="CourseB Assignment")

    _, student_headers, enrollment_a = _enroll_student(client, suffix="c3", course_id=course_a)

    non_student_submit = client.post(
        "/api/v1/assignments/submit",
        headers=instructor_headers,
        json={"assignment_id": assignment_b, "enrollment_id": enrollment_a, "content": "x"},
    )
    assert non_student_submit.status_code == 403

    missing_enrollment = client.post(
        "/api/v1/assignments/submit",
        headers=student_headers,
        json={"assignment_id": assignment_b, "enrollment_id": str(uuid4()), "content": "x"},
    )
    assert missing_enrollment.status_code == 404
    assert missing_enrollment.json()["detail"] == "Enrollment not found"

    mismatched_assignment = client.post(
        "/api/v1/assignments/submit",
        headers=student_headers,
        json={"assignment_id": assignment_b, "enrollment_id": enrollment_a, "content": "x"},
    )
    assert mismatched_assignment.status_code == 400
    assert "does not belong to the course" in mismatched_assignment.json()["detail"]


def test_submission_and_assignment_access_controls(client) -> None:
    _, instructor_headers, course_id = _create_instructor_with_course(client, suffix="d1")
    assignment_id = _create_assignment(client, headers=instructor_headers, course_id=course_id, title="Access Assignment")

    _, student1_headers, enrollment1_id = _enroll_student(client, suffix="d2", course_id=course_id)
    submit_response = client.post(
        "/api/v1/assignments/submit",
        headers=student1_headers,
        json={
            "assignment_id": assignment_id,
            "enrollment_id": enrollment1_id,
            "content": "student1 submission",
        },
    )
    assert submit_response.status_code == 201
    submission_id = submit_response.json()["id"]

    student2 = register_user(
        client,
        email="student-d3@example.com",
        password="StrongPass123",
        full_name="Student d3",
        role="student",
    )
    student2_headers = auth_headers(student2["tokens"]["access_token"])

    missing_submission = client.get(f"/api/v1/assignments/submissions/{uuid4()}", headers=instructor_headers)
    assert missing_submission.status_code == 404

    forbidden_submission = client.get(f"/api/v1/assignments/submissions/{submission_id}", headers=student2_headers)
    assert forbidden_submission.status_code == 403

    forbidden_enrollment_list = client.get(
        f"/api/v1/assignments/submissions/enrollment/{enrollment1_id}",
        headers=student2_headers,
    )
    assert forbidden_enrollment_list.status_code == 403

    student_update_attempt = client.put(
        f"/api/v1/assignments/submissions/{submission_id}",
        headers=student1_headers,
        json={"status": "graded"},
    )
    assert student_update_attempt.status_code == 403

    other_instructor, other_instructor_headers, _ = _create_instructor_with_course(client, suffix="d4")
    del other_instructor

    assignment_update_forbidden = client.put(
        f"/api/v1/assignments/{assignment_id}",
        headers=other_instructor_headers,
        json={"title": "not allowed"},
    )
    assert assignment_update_forbidden.status_code == 403

    assignment_delete_forbidden = client.delete(
        f"/api/v1/assignments/{assignment_id}",
        headers=other_instructor_headers,
    )
    assert assignment_delete_forbidden.status_code == 403
