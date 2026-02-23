from tests.helpers import auth_headers, register_user

def test_basic_assignment_creation(client):
    """Test basic assignment creation without complex grading"""
    # Register instructor
    instructor = register_user(
        client,
        email="test-instructor@example.com",
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

    # Create assignment (simplified)
    assignment_data = {
        "title": "Test Assignment",
        "description": "Test assignment description",
        "course_id": course_id,
        "status": "draft",
        "is_published": False,
    }
    
    # Try to create assignment
    response = client.post(
        "/api/v1/assignments",
        headers=instructor_headers,
        json=assignment_data,
    )

    assert response.status_code == 201
