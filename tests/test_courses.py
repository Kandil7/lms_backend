from tests.helpers import auth_headers, register_user


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
