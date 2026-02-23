from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from tests.helpers import auth_headers, register_user
from app.core.config import settings
from app.utils.cache import cache_manager


def test_assignment_list_caching(client, monkeypatch):
    """Test that assignment listing is cached"""
    # Skip if caching is disabled
    if not settings.CACHE_ENABLED:
        pytest.skip("Caching is disabled in configuration")
    
    # Register instructor and create course
    instructor = register_user(
        client,
        email="instructor-cache@example.com",
        password="StrongPass123",
        full_name="Cache Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    course_data = {
        "title": "Cache Test Course",
        "description": "Course for testing assignment caching",
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
        "title": "Cache Test Assignment",
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

    # Get assignments list (should populate cache)
    response1 = client.get(
        f"/api/v1/assignments/course/{course_id}",
        headers=instructor_headers,
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1["assignments"]) == 1
    assert data1["assignments"][0]["id"] == assignment_id

    # Clear any existing cache for this key
    cache_key = f"{settings.CACHE_KEY_PREFIX}:assignments:list:{course_id}:0:100:anonymous"
    cache_manager.delete(cache_key)

    # Get assignments list again (should hit database and repopulate cache)
    response2 = client.get(
        f"/api/v1/assignments/course/{course_id}",
        headers=instructor_headers,
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["assignments"]) == 1
    assert data2["assignments"][0]["id"] == assignment_id

    # Verify cache was populated
    cached_data = cache_manager.get_json(cache_key)
    assert cached_data is not None
    assert len(cached_data.get("assignments", [])) == 1
    assert cached_data.get("total") == 1

    # Update assignment (should invalidate cache)
    update_response = client.put(
        f"/api/v1/assignments/{assignment_id}",
        headers=instructor_headers,
        json={"title": "Updated Cache Assignment"},
    )
    assert update_response.status_code == 200

    # Get assignments list again (should bypass cache due to invalidation)
    response3 = client.get(
        f"/api/v1/assignments/course/{course_id}",
        headers=instructor_headers,
    )
    assert response3.status_code == 200
    data3 = response3.json()
    assert len(data3["assignments"]) == 1
    assert data3["assignments"][0]["title"] == "Updated Cache Assignment"

    # Verify cache now reflects the updated assignment state
    cached_data_after_update = cache_manager.get_json(cache_key)
    if cached_data_after_update:
        assert cached_data_after_update.get("assignments", [])[0].get("title") == "Updated Cache Assignment"


def test_assignment_cache_invalidation_on_create(client, monkeypatch):
    """Test that cache is invalidated when new assignments are created"""
    # Skip if caching is disabled
    if not settings.CACHE_ENABLED:
        pytest.skip("Caching is disabled in configuration")
    
    # Register instructor and create course
    instructor = register_user(
        client,
        email="instructor-invalidate@example.com",
        password="StrongPass123",
        full_name="Invalidate Instructor",
        role="instructor",
    )
    instructor_headers = auth_headers(instructor["tokens"]["access_token"])

    course_data = {
        "title": "Invalidate Test Course",
        "description": "Course for testing cache invalidation",
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

    # Get initial assignments list (empty)
    response1 = client.get(
        f"/api/v1/assignments/course/{course_id}",
        headers=instructor_headers,
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1["assignments"]) == 0

    # Create first assignment
    assignment1_data = {
        "title": "First Assignment",
        "course_id": course_id,
        "status": "published",
        "is_published": True,
    }
    assignment1_response = client.post(
        "/api/v1/assignments",
        headers=instructor_headers,
        json=assignment1_data,
    )
    assert assignment1_response.status_code == 201
    assignment1_id = assignment1_response.json()["id"]

    # Get assignments list again (should have 1 assignment)
    response2 = client.get(
        f"/api/v1/assignments/course/{course_id}",
        headers=instructor_headers,
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["assignments"]) == 1
    assert data2["assignments"][0]["id"] == assignment1_id

    # Create second assignment
    assignment2_data = {
        "title": "Second Assignment",
        "course_id": course_id,
        "status": "published",
        "is_published": True,
    }
    assignment2_response = client.post(
        "/api/v1/assignments",
        headers=instructor_headers,
        json=assignment2_data,
    )
    assert assignment2_response.status_code == 201
    assignment2_id = assignment2_response.json()["id"]

    # Get assignments list again (should have 2 assignments)
    response3 = client.get(
        f"/api/v1/assignments/course/{course_id}",
        headers=instructor_headers,
    )
    assert response3.status_code == 200
    data3 = response3.json()
    assert len(data3["assignments"]) == 2
    assignment_ids = [a["id"] for a in data3["assignments"]]
    assert assignment1_id in assignment_ids
    assert assignment2_id in assignment_ids
