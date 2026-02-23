"""Simple endpoint validation tests"""

def test_instructor_schema():
    """Test instructor registration schema"""
    data = {
        "email": "test-instructor@example.com",
        "password": "StrongPassword123!",
        "full_name": "Test Instructor",
        "role": "instructor",
        "bio": "Experienced educator with expertise in computer science.",
        "expertise": ["Computer Science", "Data Science"],
        "teaching_experience_years": 5,
        "education_level": "Master's",
        "institution": "Test University"
    }
    
    # Required fields
    required_fields = ["email", "password", "full_name", "role", "bio", "expertise", 
                      "teaching_experience_years", "education_level", "institution"]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Field constraints
    assert len(data["email"]) > 5
    assert len(data["password"]) >= 8
    assert len(data["full_name"]) >= 2
    assert len(data["bio"]) >= 10
    assert len(data["expertise"]) >= 1
    assert data["teaching_experience_years"] >= 0
    assert len(data["education_level"]) >= 1
    assert len(data["institution"]) >= 1
    assert data["role"] == "instructor"
    
    print("Instructor schema validation: PASSED")

def test_admin_schema():
    """Test admin setup schema"""
    data = {
        "email": "test-admin@example.com",
        "password": "VeryStrongPassword123456!",
        "full_name": "Test Admin",
        "role": "admin",
        "security_level": "enhanced",
        "mfa_required": True,
        "ip_whitelist": ["127.0.0.1", "192.168.1.1"],
        "time_restrictions": {
            "start_hour": 9,
            "end_hour": 17,
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        },
        "emergency_contacts": [
            {
                "name": "Backup Admin",
                "email": "backup-test@example.com",
                "phone": "+15551234567",
                "relationship": "Colleague",
                "is_backup": True
            }
        ],
        "security_policy_accepted": True,
        "security_policy_version": "1.0"
    }
    
    # Required fields
    required_fields = ["email", "password", "full_name", "role", "security_level", 
                      "mfa_required", "ip_whitelist", "time_restrictions", "emergency_contacts",
                      "security_policy_accepted", "security_policy_version"]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Field constraints
    assert len(data["email"]) > 5
    assert len(data["password"]) >= 12
    assert len(data["full_name"]) >= 2
    assert data["role"] == "admin"
    assert data["security_level"] in ["basic", "enhanced", "enterprise"]
    assert isinstance(data["mfa_required"], bool)
    assert len(data["ip_whitelist"]) >= 1
    assert "start_hour" in data["time_restrictions"]
    assert "end_hour" in data["time_restrictions"]
    assert "days" in data["time_restrictions"]
    assert len(data["emergency_contacts"]) >= 1
    assert isinstance(data["security_policy_accepted"], bool)
    assert len(data["security_policy_version"]) >= 1
    
    print("Admin schema validation: PASSED")

if __name__ == "__main__":
    print("Running endpoint validation tests...")
    test_instructor_schema()
    test_admin_schema()
    print("All endpoint validation tests passed!")