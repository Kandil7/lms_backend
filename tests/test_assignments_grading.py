
from tests.helpers import auth_headers, register_user


def test_grade_submission_success(client, monkeypatch):
    """Test successful grading of a submission"""
    # Register instructor and create course
    instructor = register_user(
        client,
        email="instructor-grade@example.com",
        password="StrongPass123",
        full_name="Grading Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    course_data = {
        "title": "Grading Test Course",
        "description": "Course for testing assignment grading",
        "category": "Testing",
        "difficulty_level": "beginner",
        "is_published": True,
    }
    course_response = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json=course_data,
    )
    course_id = course_response.json()["id"]
    publish_response = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish_response.status_code == 200, publish_response.text

    # Create assignment
    assignment_data = {
        "title": "Grading Test Assignment",
        "course_id": course_id,
        "status": "published",
        "is_published": True,
        "max_points": 100,
    }
    assignment_response = client.post(
        "/api/v1/assignments",
        headers=instructor_headers,
        json=assignment_data,
    )
    assignment_id = assignment_response.json()["id"]

    # Register student and enroll
    student = register_user(
        client,
        email="student-grade@example.com",
        password="StrongPass123",
        full_name="Grading Student",
        role="student",
    )
    student_headers = auth_headers(student["tokens"]["access_token"])

    enrollment_response = client.post(
        "/api/v1/enrollments",
        headers=student_headers,
        json={"course_id": course_id},
    )
    enrollment_id = enrollment_response.json()["id"]

    # Submit assignment
    submission_data = {
        "assignment_id": assignment_id,
        "enrollment_id": enrollment_id,
        "content": "This is my graded assignment submission",
        "submission_type": "text",
    }
    submit_response = client.post(
        "/api/v1/assignments/submit",
        headers=student_headers,
        json=submission_data,
    )
    assert submit_response.status_code == 201
    submission_id = submit_response.json()["id"]

    # Grade the submission
    grade_response = client.post(
        f"/api/v1/assignments/submissions/{submission_id}/grade",
        headers=instructor_headers,
        json={
            "grade": 85.5,
            "max_grade": 100.0,
            "feedback": "Good work! Some areas for improvement.",
            "feedback_attachments": ["https://example.com/feedback.pdf"],
        },
    )

    assert grade_response.status_code == 200
    data = grade_response.json()
    assert data["id"] == submission_id
    assert data["grade"] == 85.5
    assert data["max_grade"] == 100.0
    assert data["feedback"] == "Good work! Some areas for improvement."
    assert data["feedback_attachments"] == ["https://example.com/feedback.pdf"]
    assert data["status"] == "graded"
    assert data["graded_at"] is not None


def test_grade_submission_invalid_grade_range(client, monkeypatch):
    """Test grading with invalid grade range"""
    # Setup same as above
    instructor = register_user(
        client,
        email="instructor-invalid-grade@example.com",
        password="StrongPass123",
        full_name="Invalid Grade Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    course_data = {
        "title": "Invalid Grade Test Course",
        "description": "Course for testing invalid grading",
        "category": "Testing",
        "difficulty_level": "beginner",
        "is_published": True,
    }
    course_response = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json=course_data,
    )
    course_id = course_response.json()["id"]
    publish_response = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish_response.status_code == 200, publish_response.text

    assignment_data = {
        "title": "Invalid Grade Assignment",
        "course_id": course_id,
        "status": "published",
        "is_published": True,
        "max_points": 100,
    }
    assignment_response = client.post(
        "/api/v1/assignments",
        headers=instructor_headers,
        json=assignment_data,
    )
    assignment_id = assignment_response.json()["id"]

    student = register_user(
        client,
        email="student-invalid-grade@example.com",
        password="StrongPass123",
        full_name="Invalid Grade Student",
        role="student",
    )
    student_headers = auth_headers(student["tokens"]["access_token"])

    enrollment_response = client.post(
        "/api/v1/enrollments",
        headers=student_headers,
        json={"course_id": course_id},
    )
    enrollment_id = enrollment_response.json()["id"]

    submission_data = {
        "assignment_id": assignment_id,
        "enrollment_id": enrollment_id,
        "content": "Submission for invalid grading test",
    }
    submit_response = client.post(
        "/api/v1/assignments/submit",
        headers=student_headers,
        json=submission_data,
    )
    submission_id = submit_response.json()["id"]

    # Try to grade with invalid grade (negative)
    grade_response = client.post(
        f"/api/v1/assignments/submissions/{submission_id}/grade",
        headers=instructor_headers,
        json={
            "grade": -10.0,
            "max_grade": 100.0,
            "feedback": "Invalid grade test",
        },
    )
    assert grade_response.status_code == 400
    assert "Grade must be between 0 and 100" in grade_response.json()["detail"]

    # Try to grade with grade > max_grade
    grade_response = client.post(
        f"/api/v1/assignments/submissions/{submission_id}/grade",
        headers=instructor_headers,
        json={
            "grade": 150.0,
            "max_grade": 100.0,
            "feedback": "Invalid grade test",
        },
    )
    assert grade_response.status_code == 400
    assert "Grade must be between 0 and 100" in grade_response.json()["detail"]


def test_student_cannot_grade_submission(client, monkeypatch):
    """Test that students cannot grade submissions"""
    # Setup
    instructor = register_user(
        client,
        email="instructor-student-grade@example.com",
        password="StrongPass123",
        full_name="Student Grade Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    course_data = {
        "title": "Student Grade Test Course",
        "description": "Course for testing student grading attempts",
        "category": "Testing",
        "difficulty_level": "beginner",
        "is_published": True,
    }
    course_response = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json=course_data,
    )
    course_id = course_response.json()["id"]
    publish_response = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish_response.status_code == 200, publish_response.text

    assignment_data = {
        "title": "Student Grade Assignment",
        "course_id": course_id,
        "status": "published",
        "is_published": True,
        "max_points": 100,
    }
    assignment_response = client.post(
        "/api/v1/assignments",
        headers=instructor_headers,
        json=assignment_data,
    )
    assignment_id = assignment_response.json()["id"]

    student = register_user(
        client,
        email="student-attempt-grade@example.com",
        password="StrongPass123",
        full_name="Student Attempting Grade",
        role="student",
    )
    student_headers = auth_headers(student["tokens"]["access_token"])

    enrollment_response = client.post(
        "/api/v1/enrollments",
        headers=student_headers,
        json={"course_id": course_id},
    )
    enrollment_id = enrollment_response.json()["id"]

    submission_data = {
        "assignment_id": assignment_id,
        "enrollment_id": enrollment_id,
        "content": "Submission for student grading attempt",
    }
    submit_response = client.post(
        "/api/v1/assignments/submit",
        headers=student_headers,
        json=submission_data,
    )
    submission_id = submit_response.json()["id"]

    # Student tries to grade their own submission
    grade_response = client.post(
        f"/api/v1/assignments/submissions/{submission_id}/grade",
        headers=student_headers,
        json={
            "grade": 90.0,
            "max_grade": 100.0,
            "feedback": "Student trying to grade",
        },
    )
    assert grade_response.status_code == 403
    assert "Only instructors can grade submissions" in grade_response.json()["detail"]


def test_instructor_cannot_grade_others_assignment(client, monkeypatch):
    """Test that instructors cannot grade assignments they don't own"""
    # Create two instructors
    instructor1 = register_user(
        client,
        email="instructor1@example.com",
        password="StrongPass123",
        full_name="Instructor 1",
        role="instructor",
    )
    instructor1_headers = auth_headers(instructor1["tokens"]["access_token"])

    instructor2 = register_user(
        client,
        email="instructor2@example.com",
        password="StrongPass123",
        full_name="Instructor 2",
        role="instructor",
    )
    instructor2_headers = auth_headers(instructor2["tokens"]["access_token"])

    # Instructor 1 creates course and assignment
    course_data = {
        "title": "Instructor 1 Course",
        "description": "Course created by instructor 1",
        "category": "Testing",
        "difficulty_level": "beginner",
        "is_published": True,
    }
    course_response = client.post(
        "/api/v1/courses",
        headers=instructor1_headers,
        json=course_data,
    )
    course_id = course_response.json()["id"]
    publish_response = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor1_headers)
    assert publish_response.status_code == 200, publish_response.text

    assignment_data = {
        "title": "Instructor 1 Assignment",
        "course_id": course_id,
        "status": "published",
        "is_published": True,
        "max_points": 100,
    }
    assignment_response = client.post(
        "/api/v1/assignments",
        headers=instructor1_headers,
        json=assignment_data,
    )
    assignment_id = assignment_response.json()["id"]

    # Student enrolls and submits
    student = register_user(
        client,
        email="student-others-assignment@example.com",
        password="StrongPass123",
        full_name="Student for others assignment",
        role="student",
    )
    student_headers = auth_headers(student["tokens"]["access_token"])

    enrollment_response = client.post(
        "/api/v1/enrollments",
        headers=student_headers,
        json={"course_id": course_id},
    )
    enrollment_id = enrollment_response.json()["id"]

    submission_data = {
        "assignment_id": assignment_id,
        "enrollment_id": enrollment_id,
        "content": "Submission for others assignment test",
    }
    submit_response = client.post(
        "/api/v1/assignments/submit",
        headers=student_headers,
        json=submission_data,
    )
    submission_id = submit_response.json()["id"]

    # Instructor 2 tries to grade instructor 1's assignment
    grade_response = client.post(
        f"/api/v1/assignments/submissions/{submission_id}/grade",
        headers=instructor2_headers,
        json={
            "grade": 85.0,
            "max_grade": 100.0,
            "feedback": "Instructor 2 trying to grade",
        },
    )
    assert grade_response.status_code == 403
    assert "You don't have permission to grade this submission" in grade_response.json()["detail"]


def test_grade_submission_updates_enrollment_progress(client, monkeypatch):
    """Test that grading a submission updates enrollment progress"""
    # Setup
    instructor = register_user(
        client,
        email="instructor-progress@example.com",
        password="StrongPass123",
        full_name="Progress Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    course_data = {
        "title": "Progress Test Course",
        "description": "Course for testing progress updates",
        "category": "Testing",
        "difficulty_level": "beginner",
        "is_published": True,
    }
    course_response = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json=course_data,
    )
    course_id = course_response.json()["id"]
    publish_response = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish_response.status_code == 200, publish_response.text

    assignment_data = {
        "title": "Progress Test Assignment",
        "course_id": course_id,
        "status": "published",
        "is_published": True,
        "max_points": 100,
    }
    assignment_response = client.post(
        "/api/v1/assignments",
        headers=instructor_headers,
        json=assignment_data,
    )
    assignment_id = assignment_response.json()["id"]

    student = register_user(
        client,
        email="student-progress@example.com",
        password="StrongPass123",
        full_name="Progress Student",
        role="student",
    )
    student_headers = auth_headers(student["tokens"]["access_token"])

    enrollment_response = client.post(
        "/api/v1/enrollments",
        headers=student_headers,
        json={"course_id": course_id},
    )
    enrollment_id = enrollment_response.json()["id"]

    # Get initial enrollment status
    enrollment_get_response = client.get(
        f"/api/v1/enrollments/{enrollment_id}",
        headers=student_headers,
    )
    assert enrollment_get_response.status_code == 200
    initial_enrollment = enrollment_get_response.json()
    assert initial_enrollment["status"] == "active"
    assert float(initial_enrollment["progress_percentage"]) == 0.0

    # Submit assignment
    submission_data = {
        "assignment_id": assignment_id,
        "enrollment_id": enrollment_id,
        "content": "Submission for progress test",
    }
    submit_response = client.post(
        "/api/v1/assignments/submit",
        headers=student_headers,
        json=submission_data,
    )
    submission_id = submit_response.json()["id"]

    # Grade the submission
    grade_response = client.post(
        f"/api/v1/assignments/submissions/{submission_id}/grade",
        headers=instructor_headers,
        json={
            "grade": 85.5,
            "max_grade": 100.0,
            "feedback": "Good work!",
        },
    )
    assert grade_response.status_code == 200

    # Check that enrollment was updated
    enrollment_get_response = client.get(
        f"/api/v1/enrollments/{enrollment_id}",
        headers=student_headers,
    )
    assert enrollment_get_response.status_code == 200
    updated_enrollment = enrollment_get_response.json()
    assert updated_enrollment["last_accessed_at"] is not None
    # Note: In our current implementation, assignments don't directly affect progress percentage
    # This would be enhanced in a more sophisticated system
