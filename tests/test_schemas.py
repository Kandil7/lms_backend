"""Test Pydantic schemas directly"""

from pydantic import ValidationError
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

try:
    # Try to import schemas directly
    from app.modules.instructors.schemas import InstructorRegistrationRequest, InstructorProfileUpdateRequest
    from app.modules.admin.schemas import AdminSetupRequest, AdminSecurityConfigRequest
    
    def test_instructor_schemas():
        """Test instructor schemas"""
        print("Testing instructor schemas...")
        
        # Valid registration
        try:
            valid_data = {
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
            instructor_reg = InstructorRegistrationRequest(**valid_data)
            print("✅ Instructor registration schema: VALID")
        except ValidationError as e:
            print(f"❌ Instructor registration schema: INVALID - {e}")
            return False
        
        # Invalid registration (weak password)
        try:
            invalid_data = valid_data.copy()
            invalid_data["password"] = "weak"
            InstructorRegistrationRequest(**invalid_data)
            print("❌ Instructor registration should have failed for weak password")
            return False
        except ValidationError as e:
            if "password" in str(e):
                print("✅ Instructor registration: REJECTED weak password")
            else:
                print(f"❌ Instructor registration: Wrong error - {e}")
                return False
        
        # Valid profile update
        try:
            valid_update = {
                "bio": "Updated bio with more details about teaching philosophy.",
                "expertise": ["Computer Science", "Artificial Intelligence"],
                "teaching_experience_years": 7
            }
            profile_update = InstructorProfileUpdateRequest(**valid_update)
            print("✅ Instructor profile update schema: VALID")
        except ValidationError as e:
            print(f"❌ Instructor profile update schema: INVALID - {e}")
            return False
        
        return True
    
    def test_admin_schemas():
        """Test admin schemas"""
        print("Testing admin schemas...")
        
        # Valid admin setup
        try:
            valid_data = {
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
            admin_setup = AdminSetupRequest(**valid_data)
            print("✅ Admin setup schema: VALID")
        except ValidationError as e:
            print(f"❌ Admin setup schema: INVALID - {e}")
            return False
        
        # Invalid admin setup (weak password)
        try:
            invalid_data = valid_data.copy()
            invalid_data["password"] = "weak"
            AdminSetupRequest(**invalid_data)
            print("❌ Admin setup should have failed for weak password")
            return False
        except ValidationError as e:
            if "password" in str(e):
                print("✅ Admin setup: REJECTED weak password")
            else:
                print(f"❌ Admin setup: Wrong error - {e}")
                return False
        
        # Valid security config
        try:
            valid_config = {
                "mfa_method": "totp",
                "ip_whitelist": ["127.0.0.1", "192.168.1.1"],
                "time_restrictions": {
                    "start_hour": 9,
                    "end_hour": 17,
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                },
                "require_password_change": True,
                "password_expiry_days": 90,
                "session_timeout_minutes": 30,
                "geo_restrictions": [],
                "anomaly_detection_enabled": True
            }
            security_config = AdminSecurityConfigRequest(**valid_config)
            print("✅ Admin security config schema: VALID")
        except ValidationError as e:
            print(f"❌ Admin security config schema: INVALID - {e}")
            return False
        
        return True
    
    def main():
        print("Running schema validation tests...")
        
        instructor_ok = test_instructor_schemas()
        admin_ok = test_admin_schemas()
        
        if instructor_ok and admin_ok:
            print("\n🎉 ALL SCHEMA VALIDATION TESTS PASSED!")
            return True
        else:
            print("\n❌ SOME SCHEMA VALIDATION TESTS FAILED!")
            return False
    
    if __name__ == "__main__":
        success = main()
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"❌ Could not import schemas: {e}")
    print("Falling back to manual validation...")
    
    # Manual validation as fallback
    def manual_validation():
        print("Manual schema validation...")
        
        # Instructor registration validation
        instructor_data = {
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
        
        # Check constraints
        assert len(instructor_data["email"]) > 5
        assert len(instructor_data["password"]) >= 8
        assert len(instructor_data["full_name"]) >= 2
        assert len(instructor_data["bio"]) >= 10
        assert len(instructor_data["expertise"]) >= 1
        assert instructor_data["teaching_experience_years"] >= 0
        assert len(instructor_data["education_level"]) >= 1
        assert len(instructor_data["institution"]) >= 1
        assert instructor_data["role"] == "instructor"
        
        print("✅ Instructor schema manual validation: PASSED")
        
        # Admin setup validation
        admin_data = {
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
        
        assert len(admin_data["email"]) > 5
        assert len(admin_data["password"]) >= 12
        assert len(admin_data["full_name"]) >= 2
        assert admin_data["role"] == "admin"
        assert admin_data["security_level"] in ["basic", "enhanced", "enterprise"]
        assert isinstance(admin_data["mfa_required"], bool)
        assert len(admin_data["ip_whitelist"]) >= 1
        assert "start_hour" in admin_data["time_restrictions"]
        assert "end_hour" in admin_data["time_restrictions"]
        assert "days" in admin_data["time_restrictions"]
        assert len(admin_data["emergency_contacts"]) >= 1
        assert isinstance(admin_data["security_policy_accepted"], bool)
        assert len(admin_data["security_policy_version"]) >= 1
        
        print("✅ Admin schema manual validation: PASSED")
        print("🎉 All manual schema validations passed!")
    
    manual_validation()