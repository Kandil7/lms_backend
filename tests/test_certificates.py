from tests.helpers import auth_headers, register_user


def _setup_completed_enrollment(client):
    instructor = register_user(
        client,
        email="cert-instructor@example.com",
        password="StrongPass123",
        full_name="Cert Instructor",
        role="instructor",
    )
    student = register_user(
        client,
        email="cert-student@example.com",
        password="StrongPass123",
        full_name="Cert Student",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])

    course = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "Certification Course",
            "description": "Complete to receive certificate",
            "category": "Career",
            "difficulty_level": "beginner",
        },
    )
    assert course.status_code == 201, course.text
    course_id = course.json()["id"]

    lesson = client.post(
        f"/api/v1/courses/{course_id}/lessons",
        headers=instructor_headers,
        json={
            "title": "Certificate Lesson",
            "lesson_type": "video",
            "order_index": 1,
            "duration_minutes": 5,
            "is_preview": True,
        },
    )
    assert lesson.status_code == 201, lesson.text
    lesson_id = lesson.json()["id"]

    publish = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish.status_code == 200, publish.text

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

    return enrollment_id, student_headers


def test_certificate_lifecycle_verify_and_revoke(client):
    admin = register_user(
        client,
        email="cert-admin@example.com",
        password="StrongPass123",
        full_name="Cert Admin",
        role="admin",
    )
    admin_headers = auth_headers(admin["tokens"]["access_token"])

    _, student_headers = _setup_completed_enrollment(client)

    my_certificates = client.get("/api/v1/certificates/my-certificates", headers=student_headers)
    assert my_certificates.status_code == 200, my_certificates.text
    assert my_certificates.json()["total"] == 1

    certificate = my_certificates.json()["certificates"][0]
    certificate_id = certificate["id"]
    certificate_number = certificate["certificate_number"]

    verify = client.get(f"/api/v1/certificates/verify/{certificate_number}")
    assert verify.status_code == 200
    assert verify.json()["valid"] is True

    revoke = client.post(f"/api/v1/certificates/{certificate_id}/revoke", headers=admin_headers)
    assert revoke.status_code == 200, revoke.text
    assert revoke.json()["is_revoked"] is True

    verify_after_revoke = client.get(f"/api/v1/certificates/verify/{certificate_number}")
    assert verify_after_revoke.status_code == 200
    assert verify_after_revoke.json()["valid"] is False


def test_manual_certificate_generation_fails_for_incomplete_enrollment(client):
    instructor = register_user(
        client,
        email="cert-instructor2@example.com",
        password="StrongPass123",
        full_name="Cert Instructor Two",
        role="instructor",
    )
    student = register_user(
        client,
        email="cert-student2@example.com",
        password="StrongPass123",
        full_name="Cert Student Two",
        role="student",
    )

    instructor_headers = auth_headers(instructor["tokens"]["access_token"])
    student_headers = auth_headers(student["tokens"]["access_token"])

    course = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json={
            "title": "Incomplete Certificate Course",
            "description": "Not complete",
            "category": "Career",
            "difficulty_level": "beginner",
        },
    )
    assert course.status_code == 201, course.text
    course_id = course.json()["id"]

    publish = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish.status_code == 200, publish.text

    enrollment = client.post(
        "/api/v1/enrollments",
        headers=student_headers,
        json={"course_id": course_id},
    )
    assert enrollment.status_code == 201, enrollment.text
    enrollment_id = enrollment.json()["id"]

    generate = client.post(
        f"/api/v1/certificates/enrollments/{enrollment_id}/generate",
        headers=student_headers,
    )
    assert generate.status_code == 400
