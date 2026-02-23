import pytest
from datetime import datetime, timedelta
from typing import Dict

from tests.helpers import auth_headers, register_user


def test_create_assignment(client, monkeypatch):
    """Test creating a new assignment"""
    # Register instructor
    instructor = register_user(
        client,
        email="instructor@example.com",
        password="StrongPass123",
        full_name="Test Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    # Create course first
    course_data = {
        "title": "Test Course",
        "description": "Test course for assignments",
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
        "title": "Test Assignment",
        "description": "Test assignment description",
        "instructions": "Complete this assignment",
        "course_id": course_id,
        "status": "draft",
        "is_published": False,
    }
    response = client.post(
        "/api/v1/assignments",
        headers=instructor_headers,
        json=assignment_data,
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Assignment"
    assert data["course_id"] == course_id
    assert data["instructor_id"] == instructor["user"]["id"]
    assert data["status"] == "draft"
    assert data["is_published"] is False


def test_get_assignment(client, monkeypatch):
    """Test getting an assignment"""
    # Register instructor and create course
    instructor = register_user(
        client,
        email="instructor2@example.com",
        password="StrongPass123",
        full_name="Test Instructor 2",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    course_data = {
        "title": "Test Course 2",
        "description": "Another test course",
        "category": "Testing",
        "difficulty_level": "intermediate",
        "is_published": True,
    }
    course_response = client.post(
        "/api/v1/courses",
        headers=instructor_headers,
        json=course_data,
    )
    course_id = course_response.json()["id"]

    # Create assignment
    assignment_data = {
        "title": "Test Assignment 2",
        "course_id": course_id,
        "status": "published",
        "is_published": True,
    }
    assignment_response = client.post(
        "/api/v1/assignments",
        headers=instructor_headers,
        json=assignment_data,
    )
    assignment_id = assignment_response.json()["id"]

    # Get assignment
    response = client.get(
        f"/api/v1/assignments/{assignment_id}",
        headers=instructor_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == assignment_id
    assert data["title"] == "Test Assignment 2"


def test_student_cannot_create_assignment(client, monkeypatch):
    """Test that students cannot create assignments"""
    # Register student
    student = register_user(
        client,
        email="student@example.com",
        password="StrongPass123",
        full_name="Test Student",
        role="student",
    )
    student_headers = auth_headers(student["tokens"]["access_token"])

    # Try to create assignment (should fail)
    assignment_data = {
        "title": "Student Assignment",
        "course_id": "some-id",
        "status": "draft",
        "is_published": False,
    }
    response = client.post(
        "/api/v1/assignments",
        headers=student_headers,
        json=assignment_data,
    )
    
    assert response.status_code == 403
    assert "Only instructors can create assignments" in response.json()["detail"]


def test_submit_assignment(client, monkeypatch):
    """Test submitting an assignment"""
    # Register instructor and create course
    instructor = register_user(
        client,
        email="instructor3@example.com",
        password="StrongPass123",
        full_name="Instructor 3",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    course_data = {
        "title": "Course for Submission",
        "description": "Course for testing submissions",
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

    # Create assignment
    assignment_data = {
        "title": "Submission Test Assignment",
        "course_id": course_id,
        "status": "published",
        "is_published": True,
    }
    assignment_response = client.post(
        "/api/v1/assignments",
        headers=instructor_headers,
        json=assignment_data,
    )
    assignment_id = assignment_response.json()["id"]

    # Register student and enroll in course
    student = register_user(
        client,
        email="student2@example.com",
        password="StrongPass123",
        full_name="Student 2",
        role="student",
    )
    student_headers = auth_headers(student["tokens"]["access_token"])

    # Enroll student in course
    enrollment_data = {"course_id": course_id}
    enrollment_response = client.post(
        "/api/v1/enrollments",
        headers=student_headers,
        json=enrollment_data,
    )
    enrollment_id = enrollment_response.json()["id"]

    # Submit assignment
    submission_data = {
        "assignment_id": assignment_id,
        "enrollment_id": enrollment_id,
        "content": "This is my assignment submission",
        "submission_type": "text",
    }
    response = client.post(
        "/api/v1/assignments/submit",
        headers=student_headers,
        json=submission_data,
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["assignment_id"] == assignment_id
    assert data["enrollment_id"] == enrollment_id
    assert data["content"] == "This is my assignment submission"
    assert data["status"] == "submitted"


def test_instructor_can_view_submissions(client, monkeypatch):
    """Test that instructors can view submissions for their assignments"""
    # Register instructor and create course
    instructor = register_user(
        client,
        email="instructor4@example.com",
        password="StrongPass123",
        full_name="Instructor 4",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    course_data = {
        "title": "Course for Submissions",
        "description": "Course for testing submissions viewing",
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

    # Create assignment
    assignment_data = {
        "title": "View Submissions Assignment",
        "course_id": course_id,
        "status": "published",
        "is_published": True,
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
        email="student3@example.com",
        password="StrongPass123",
        full_name="Student 3",
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
        "content": "Test submission content",
    }
    client.post(
        "/api/v1/assignments/submit",
        headers=student_headers,
        json=submission_data,
    )

    # Instructor views submissions for assignment
    response = client.get(
        f"/api/v1/assignments/submissions/assignment/{assignment_id}",
        headers=instructor_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["submissions"]) == 1
    assert data["submissions"][0]["assignment_id"] == assignment_id
    assert data["submissions"][0]["enrollment_id"] == enrollment_id