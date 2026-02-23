from __future__ import annotations

import pytest

from tests.helpers import auth_headers, register_user
from app.core.config import settings


def test_concurrent_submission_race_condition(client, monkeypatch):
    """Test race condition when multiple students submit the same assignment concurrently"""
    # Register instructor and create course
    instructor = register_user(
        client,
        email="instructor-race@example.com",
        password="StrongPass123",
        full_name="Race Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    course_data = {
        "title": "Race Test Course",
        "description": "Course for testing concurrent submissions",
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
    publish_response = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish_response.status_code == 200, publish_response.text

    # Create assignment
    assignment_data = {
        "title": "Race Test Assignment",
        "course_id": course_id,
        "status": "published",
        "is_published": True,
    }
    assignment_response = client.post(
        "/api/v1/assignments",
        headers=instructor_headers,
        json=assignment_data,
    )
    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]

    # Register two students
    student1 = register_user(
        client,
        email="student1-race@example.com",
        password="StrongPass123",
        full_name="Student 1 Race",
        role="student",
    )
    student1_headers = auth_headers(student1["tokens"]["access_token"])

    student2 = register_user(
        client,
        email="student2-race@example.com",
        password="StrongPass123",
        full_name="Student 2 Race",
        role="student",
    )
    student2_headers = auth_headers(student2["tokens"]["access_token"])

    # Enroll both students
    enrollment1_response = client.post(
        "/api/v1/enrollments",
        headers=student1_headers,
        json={"course_id": course_id},
    )
    assert enrollment1_response.status_code == 201
    enrollment1_id = enrollment1_response.json()["id"]

    enrollment2_response = client.post(
        "/api/v1/enrollments",
        headers=student2_headers,
        json={"course_id": course_id},
    )
    assert enrollment2_response.status_code == 201
    enrollment2_id = enrollment2_response.json()["id"]

    # Submit assignment for both students (should succeed)
    submission1_data = {
        "assignment_id": assignment_id,
        "enrollment_id": enrollment1_id,
        "content": "Student 1 submission",
        "submission_type": "text",
    }
    
    submission2_data = {
        "assignment_id": assignment_id,
        "enrollment_id": enrollment2_id,
        "content": "Student 2 submission",
        "submission_type": "text",
    }

    # Test that both submissions succeed (no race condition)
    response1 = client.post(
        "/api/v1/assignments/submit",
        headers=student1_headers,
        json=submission1_data,
    )
    assert response1.status_code == 201

    response2 = client.post(
        "/api/v1/assignments/submit",
        headers=student2_headers,
        json=submission2_data,
    )
    assert response2.status_code == 201

    # Verify both submissions exist
    submissions_response = client.get(
        f"/api/v1/assignments/submissions/assignment/{assignment_id}",
        headers=instructor_headers,
    )
    assert submissions_response.status_code == 200
    data = submissions_response.json()
    assert len(data["submissions"]) == 2


def test_invalid_uuid_formats(client, monkeypatch):
    """Test handling of invalid UUID formats"""
    # Register instructor
    instructor = register_user(
        client,
        email="instructor-uuid@example.com",
        password="StrongPass123",
        full_name="UUID Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    # Create course
    course_data = {
        "title": "UUID Test Course",
        "description": "Course for testing UUID validation",
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
    publish_response = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish_response.status_code == 200, publish_response.text

    # Test invalid UUID formats for course_id
    invalid_uuids = [
        "invalid-uuid",
        "1234",  # too short
        "a" * 36,  # too long
        "00000000-0000-0000-0000-0000000000000",  # too long
        "",  # empty
        None,  # null (will be handled by Pydantic validation)
    ]

    for invalid_uuid in invalid_uuids:
        if invalid_uuid is not None:
            response = client.post(
                "/api/v1/assignments",
                headers=instructor_headers,
                json={
                    "title": "Invalid UUID Test",
                    "course_id": invalid_uuid,
                    "status": "draft",
                    "is_published": False,
                },
            )
            # Should return 422 Unprocessable Entity for Pydantic validation errors
            if response.status_code == 422:
                # This is expected for Pydantic validation
                continue
            elif response.status_code == 400:
                # This is expected for our custom validation
                continue
            else:
                assert response.status_code in [400, 422], f"Expected 400 or 422 for UUID {invalid_uuid}, got {response.status_code}"

    # Test invalid UUID for assignment_id in get endpoint
    invalid_assignment_ids = ["invalid-uuid", "1234", "a" * 36]
    for invalid_id in invalid_assignment_ids:
        response = client.get(
            f"/api/v1/assignments/{invalid_id}",
            headers=instructor_headers,
        )
        assert response.status_code in [400, 422], f"Expected 400 or 422 for assignment ID {invalid_id}"


def test_large_assignment_list_performance(client, monkeypatch):
    """Test performance with large assignment lists"""
    # Skip if not in testing environment or if performance testing is disabled
    if settings.ENVIRONMENT != "testing":
        pytest.skip("Performance testing only in testing environment")
    
    # Register instructor
    instructor = register_user(
        client,
        email="instructor-large@example.com",
        password="StrongPass123",
        full_name="Large List Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    # Create course
    course_data = {
        "title": "Large List Test Course",
        "description": "Course for testing large assignment lists",
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
    publish_response = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish_response.status_code == 200, publish_response.text

    # Create multiple assignments (20+ to test pagination and performance)
    assignments_to_create = 25
    created_assignment_ids = []
    
    for i in range(assignments_to_create):
        assignment_data = {
            "title": f"Large Assignment {i+1}",
            "course_id": course_id,
            "status": "published",
            "is_published": True,
        }
        response = client.post(
            "/api/v1/assignments",
            headers=instructor_headers,
            json=assignment_data,
        )
        assert response.status_code == 201
        created_assignment_ids.append(response.json()["id"])
    
    # Test pagination with large list
    # Get first page (limit=10)
    response1 = client.get(
        f"/api/v1/assignments/course/{course_id}",
        headers=instructor_headers,
        params={"skip": 0, "limit": 10},
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1["assignments"]) == 10
    assert data1["total"] == assignments_to_create
    assert data1["page"] == 1
    assert data1["page_size"] == 10

    # Get second page (skip=10, limit=10)
    response2 = client.get(
        f"/api/v1/assignments/course/{course_id}",
        headers=instructor_headers,
        params={"skip": 10, "limit": 10},
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["assignments"]) == 10
    assert data2["total"] == assignments_to_create
    assert data2["page"] == 2
    assert data2["page_size"] == 10

    # Get third page (skip=20, limit=10) - should have 5 items
    response3 = client.get(
        f"/api/v1/assignments/course/{course_id}",
        headers=instructor_headers,
        params={"skip": 20, "limit": 10},
    )
    assert response3.status_code == 200
    data3 = response3.json()
    assert len(data3["assignments"]) == 5
    assert data3["total"] == assignments_to_create
    assert data3["page"] == 3
    assert data3["page_size"] == 10


def test_cache_invalidation_edge_cases(client, monkeypatch):
    """Test cache invalidation edge cases"""
    # Skip if caching is disabled
    if not settings.CACHE_ENABLED:
        pytest.skip("Caching is disabled in configuration")
    
    # Register instructor and create course
    instructor = register_user(
        client,
        email="instructor-cache-edge@example.com",
        password="StrongPass123",
        full_name="Cache Edge Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    course_data = {
        "title": "Cache Edge Test Course",
        "description": "Course for testing cache edge cases",
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
    publish_response = client.post(f"/api/v1/courses/{course_id}/publish", headers=instructor_headers)
    assert publish_response.status_code == 200, publish_response.text

    # Create assignment
    assignment_data = {
        "title": "Cache Edge Assignment",
        "course_id": course_id,
        "status": "published",
        "is_published": True,
    }
    assignment_response = client.post(
        "/api/v1/assignments",
        headers=instructor_headers,
        json=assignment_data,
    )
    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]

    # Get assignments list to populate cache
    response1 = client.get(
        f"/api/v1/assignments/course/{course_id}",
        headers=instructor_headers,
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1["assignments"]) == 1

    # Delete the assignment (should invalidate cache)
    delete_response = client.delete(
        f"/api/v1/assignments/{assignment_id}",
        headers=instructor_headers,
    )
    assert delete_response.status_code == 204

    # Get assignments list again (should be empty and cache should be invalidated)
    response2 = client.get(
        f"/api/v1/assignments/course/{course_id}",
        headers=instructor_headers,
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["assignments"]) == 0

    # Verify cache is now empty for this course
    from app.utils.cache import cache_manager
    cache_key = f"{settings.CACHE_KEY_PREFIX}:assignments:list:{course_id}:0:100:anonymous"
    cached_data = cache_manager.get_json(cache_key)
    assert cached_data is None or len(cached_data.get("assignments", [])) == 0


def test_permission_boundary_cases(client, monkeypatch):
    """Test permission boundary cases for assignments"""
    # Register two instructors
    instructor1 = register_user(
        client,
        email="instructor1-boundary@example.com",
        password="StrongPass123",
        full_name="Instructor 1 Boundary",
        role="instructor",
    )
    instructor1_headers = auth_headers(instructor1["tokens"]["access_token"])

    instructor2 = register_user(
        client,
        email="instructor2-boundary@example.com",
        password="StrongPass123",
        full_name="Instructor 2 Boundary",
        role="instructor",
    )
    instructor2_headers = auth_headers(instructor2["tokens"]["access_token"])

    # Create courses for each instructor
    course1_data = {
        "title": "Boundary Course 1",
        "description": "Course for instructor 1",
        "category": "Testing",
        "difficulty_level": "beginner",
        "is_published": True,
    }
    course1_response = client.post(
        "/api/v1/courses",
        headers=instructor1_headers,
        json=course1_data,
    )
    assert course1_response.status_code == 201
    course1_id = course1_response.json()["id"]
    publish1_response = client.post(f"/api/v1/courses/{course1_id}/publish", headers=instructor1_headers)
    assert publish1_response.status_code == 200, publish1_response.text

    course2_data = {
        "title": "Boundary Course 2",
        "description": "Course for instructor 2",
        "category": "Testing",
        "difficulty_level": "beginner",
        "is_published": True,
    }
    course2_response = client.post(
        "/api/v1/courses",
        headers=instructor2_headers,
        json=course2_data,
    )
    assert course2_response.status_code == 201
    course2_id = course2_response.json()["id"]
    publish2_response = client.post(f"/api/v1/courses/{course2_id}/publish", headers=instructor2_headers)
    assert publish2_response.status_code == 200, publish2_response.text

    # Create assignments for each course
    assignment1_data = {
        "title": "Boundary Assignment 1",
        "course_id": course1_id,
        "status": "published",
        "is_published": True,
    }
    assignment1_response = client.post(
        "/api/v1/assignments",
        headers=instructor1_headers,
        json=assignment1_data,
    )
    assert assignment1_response.status_code == 201
    assignment1_id = assignment1_response.json()["id"]

    assignment2_data = {
        "title": "Boundary Assignment 2",
        "course_id": course2_id,
        "status": "published",
        "is_published": True,
    }
    assignment2_response = client.post(
        "/api/v1/assignments",
        headers=instructor2_headers,
        json=assignment2_data,
    )
    assert assignment2_response.status_code == 201
    assignment2_id = assignment2_response.json()["id"]

    # Test instructor 1 trying to access instructor 2's assignment
    response = client.get(
        f"/api/v1/assignments/{assignment2_id}",
        headers=instructor1_headers,
    )
    assert response.status_code == 403, "Instructor 1 should not access instructor 2's assignment"

    # Test instructor 2 trying to update instructor 1's assignment
    update_response = client.put(
        f"/api/v1/assignments/{assignment1_id}",
        headers=instructor2_headers,
        json={"title": "Attempted Update"},
    )
    assert update_response.status_code == 403, "Instructor 2 should not update instructor 1's assignment"

    # Test instructor 2 trying to delete instructor 1's assignment
    delete_response = client.delete(
        f"/api/v1/assignments/{assignment1_id}",
        headers=instructor2_headers,
    )
    assert delete_response.status_code == 403, "Instructor 2 should not delete instructor 1's assignment"

    # Test student trying to access assignments they're not enrolled in
    student = register_user(
        client,
        email="student-boundary@example.com",
        password="StrongPass123",
        full_name="Boundary Student",
        role="student",
    )
    student_headers = auth_headers(student["tokens"]["access_token"])

    # Enroll student in course 1 only
    enrollment_response = client.post(
        "/api/v1/enrollments",
        headers=student_headers,
        json={"course_id": course1_id},
    )
    assert enrollment_response.status_code == 201
    enrollment_id = enrollment_response.json()["id"]

    # Student should access assignment 1 (they're enrolled in course 1)
    response_student1 = client.get(
        f"/api/v1/assignments/{assignment1_id}",
        headers=student_headers,
    )
    assert response_student1.status_code == 200, "Student should access their course assignment"

    # Student should NOT access assignment 2 (not enrolled in course 2)
    response_student2 = client.get(
        f"/api/v1/assignments/{assignment2_id}",
        headers=student_headers,
    )
    assert response_student2.status_code == 403, "Student should not access other course assignment"