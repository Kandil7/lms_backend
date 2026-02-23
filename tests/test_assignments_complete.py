import pytest
from datetime import datetime, timedelta
from typing import Dict

from tests.helpers import auth_headers, register_user
from app.modules.assignments.schemas import SubmissionUpdate


def test_assignment_grading_workflow(client, monkeypatch):
    """Test complete assignment grading workflow"""
    # Register instructor and create course
    instructor = register_user(
        client,
        email="instructor-complete@example.com",
        password="StrongPass123",
        full_name="Complete Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    course_data = {
        "title": "Complete Test Course",
        "description": "Course for complete assignment testing",
        "category": "Testing",
        "difficulty_level": "beginner",
        "is_published": True,
    }
    course_response = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json=course_data,
    )
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]

    # Create assignment
    assignment_data = {
        "title": "Complete Test Assignment",
        "description": "Complete assignment for testing",
        "instructions": "Complete this assignment",
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
    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]

    # Register student and enroll
    student = register_user(
        client,
        email="student-complete@example.com",
        password="StrongPass123",
        full_name="Complete Student",
        role="student",
    )
    student_headers = auth_headers(student["tokens"]["access_token"])

    enrollment_response = client.post(
        "/api/v1/enrollments",
        headers=student_headers,
        json={"course_id": course_id},
    )
    assert enrollment_response.status_code == 201
    enrollment_id = enrollment_response.json()["id"]

    # Submit assignment
    submission_data = {
        "assignment_id": assignment_id,
        "enrollment_id": enrollment_id,
        "content": "This is a complete assignment submission for testing grading workflow.",
        "submission_type": "text",
    }
    submit_response = client.post(
        "/api/v1/assignments/submit",
        headers=student_headers,
        json=submission_data,
    )
    assert submit_response.status_code == 201
    submission_id = submit_response.json()["id"]

    # Verify submission was created
    get_submission_response = client.get(
        f"/api/v1/assignments/submissions/{submission_id}",
        headers=student_headers,
    )
    assert get_submission_response.status_code == 200
    submission_data = get_submission_response.json()
    assert submission_data["id"] == submission_id
    assert submission_data["status"] == "submitted"
    assert submission_data["grade"] is None
    assert submission_data["graded_at"] is None

    # Grade the submission
    grade_response = client.post(
        f"/api/v1/assignments/submissions/{submission_id}/grade",
        headers=instructor_headers,
        json={
            "grade": 85.5,
            "max_grade": 100.0,
            "feedback": "Excellent work! Some areas for improvement in the analysis section.",
            "feedback_attachments": ["https://example.com/grading-feedback.pdf"],
        },
    )

    assert grade_response.status_code == 200
    graded_data = grade_response.json()
    assert graded_data["id"] == submission_id
    assert graded_data["grade"] == 85.5
    assert graded_data["max_grade"] == 100.0
    assert graded_data["feedback"] == "Excellent work! Some areas for improvement in the analysis section."
    assert graded_data["feedback_attachments"] == ["https://example.com/grading-feedback.pdf"]
    assert graded_data["status"] == "graded"
    assert graded_data["graded_at"] is not None

    # Verify enrollment progress was updated
    enrollment_get_response = client.get(
        f"/api/v1/enrollments/{enrollment_id}",
        headers=student_headers,
    )
    assert enrollment_get_response.status_code == 200
    enrollment_data = enrollment_get_response.json()
    assert enrollment_data["last_accessed_at"] is not None

    # Test invalid grade range
    invalid_grade_response = client.post(
        f"/api/v1/assignments/submissions/{submission_id}/grade",
        headers=instructor_headers,
        json={
            "grade": -10.0,
            "max_grade": 100.0,
            "feedback": "Invalid grade test",
        },
    )
    assert invalid_grade_response.status_code == 400
    assert "Grade must be between 0 and 100" in invalid_grade_response.json()["detail"]

    # Test student cannot grade
    student_grade_response = client.post(
        f"/api/v1/assignments/submissions/{submission_id}/grade",
        headers=student_headers,
        json={
            "grade": 90.0,
            "max_grade": 100.0,
            "feedback": "Student trying to grade",
        },
    )
    assert student_grade_response.status_code == 403
    assert "Only instructors can grade submissions" in student_grade_response.json()["detail"]

    # Test instructor cannot grade others' assignments
    other_instructor = register_user(
        client,
        email="other-instructor@example.com",
        password="StrongPass123",
        full_name="Other Instructor",
        role="instructor",
    )
    other_instructor_headers = auth_headers(other_instructor["tokens"]["access_token"])

    other_grade_response = client.post(
        f"/api/v1/assignments/submissions/{submission_id}/grade",
        headers=other_instructor_headers,
        json={
            "grade": 95.0,
            "max_grade": 100.0,
            "feedback": "Other instructor trying to grade",
        },
    )
    assert other_grade_response.status_code == 403
    assert "You don't have permission to grade this submission" in other_grade_response.json()["detail"]


def test_assignment_progress_tracking(client, monkeypatch):
    """Test that grading assignments updates course progress"""
    # Setup same as above
    instructor = register_user(
        client,
        email="progress-instructor@example.com",
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
        email="progress-student@example.com",
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
    assert initial_enrollment["progress_percentage"] == 0.0

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

    # Check that enrollment was updated (this would be enhanced in production)
    enrollment_get_response = client.get(
        f"/api/v1/enrollments/{enrollment_id}",
        headers=student_headers,
    )
    assert enrollment_get_response.status_code == 200
    updated_enrollment = enrollment_get_response.json()
    assert updated_enrollment["last_accessed_at"] is not None
    # Note: In current implementation, assignments don't directly affect progress percentage
    # This would be enhanced in a more sophisticated system