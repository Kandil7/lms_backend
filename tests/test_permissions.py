from tests.helpers import auth_headers, register_user


def test_student_cannot_create_course(client):
    student = register_user(
        client,
        email="perm-student@example.com",
        password="StrongPass123",
        full_name="Perm Student",
        role="student",
    )
    student_headers = auth_headers(student["tokens"]["access_token"])

    response = client.post(
        "/api/v1/courses",
        headers=student_headers,
        json={
            "title": "Unauthorized Course",
            "description": "Should fail",
            "category": "Security",
            "difficulty_level": "beginner",
        },
    )
    assert response.status_code == 403


def test_non_admin_cannot_list_users(client):
    instructor = register_user(
        client,
        email="perm-instructor@example.com",
        password="StrongPass123",
        full_name="Perm Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    response = client.get("/api/v1/users", headers=instructor_headers)
    assert response.status_code == 403
