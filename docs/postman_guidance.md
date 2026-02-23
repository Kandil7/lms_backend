# Postman Testing Guidance for LMS Backend

This guide provides comprehensive instructions for testing the LMS backend API using Postman, with special focus on the enhanced instructor and admin account creation flows.

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Authentication Flow](#authentication-flow)
4. [Instructor Account Testing](#instructor-account-testing)
5. [Admin Account Testing](#admin-account-testing)
6. [Advanced Testing Scenarios](#advanced-testing-scenarios)
7. [Troubleshooting](#troubleshooting)

## 🛠️ Prerequisites

### Required Tools
- **Postman** (v10+ recommended)
- **LMS Backend** running (development or production)
- **Test accounts** (email/password combinations)

### Files to Import
- `postman/LMS Backend Production.postman_collection.json`
- `postman/LMS Backend Production.postman_environment.json`

## 🌐 Environment Setup

### Importing Collection and Environment
1. Open Postman
2. Click **Import** (top-left corner)
3. Select **File** → Choose the collection JSON file
4. Repeat for environment JSON file
5. Select the imported environment from the dropdown (top-right)

### Environment Variables Configuration
| Variable | Default Value | Purpose |
|----------|---------------|---------|
| `base_url` | `https://egylms.duckdns.org` | API base URL |
| `access_token` | *(empty)* | JWT access token |
| `refresh_token` | *(empty)* | JWT refresh token |
| `test_email` | `test@example.com` | Test email address |
| `test_password` | `TestPassword123!` | Test password |
| `course_id` | `123e4567-e89b-12d3-a456-426614174000` | Sample course ID |

> **Note**: Update these values for your specific test environment

## 🔑 Authentication Flow

### Standard JWT Token Flow
1. Navigate to: **Auth** → **Login**
2. Update request body:
   ```json
   {
     "email": "your-test-email@example.com",
     "password": "your-test-password"
   }
   ```
3. Send request
4. Copy the `access_token` from response
5. Update environment variable `access_token`

### Cookie-Based Authentication Flow
1. Navigate to: **Auth** → **Login Cookie**
2. Use same credentials as above
3. The backend will set HttpOnly cookies automatically
4. For subsequent requests, ensure "Include cookies" is enabled in Postman settings

## 👩‍🏫 Instructor Account Testing

### Step 1: Register Instructor
**Endpoint**: `POST /api/v1/instructors/register`
- Navigate to: **Instructors** → **Register Instructor**
- Update request body with test data:
  ```json
  {
    "email": "instructor-test@example.com",
    "password": "StrongPassword123!",
    "full_name": "Test Instructor",
    "role": "instructor",
    "bio": "Experienced educator with expertise in computer science.",
    "expertise": ["Computer Science", "Data Science"],
    "teaching_experience_years": 5,
    "education_level": "Master's",
    "institution": "Test University"
  }
  ```
- Expected response: `201 Created`
- Verify: Onboarding status and verification requirements

### Step 2: Check Onboarding Status
**Endpoint**: `GET /api/v1/instructors/onboarding-status`
- Navigate to: **Instructors** → **Get Onboarding Status**
- Ensure `access_token` is set
- Verify: Progress percentage and current step

### Step 3: Update Instructor Profile
**Endpoint**: `PUT /api/v1/instructors/profile`
- Navigate to: **Instructors** → **Update Instructor Profile**
- Update profile information as needed
- Verify: Profile updates are reflected

### Step 4: Submit Verification
**Endpoint**: `POST /api/v1/instructors/verify`
- Navigate to: **Instructors** → **Submit Verification**
- Provide document URL and consent:
  ```json
  {
    "document_type": "resume",
    "document_url": "https://example.com/test-resume.pdf",
    "verification_notes": "Please verify my credentials for instructor status.",
    "consent_to_verify": true
  }
  ```
- Expected: Verification submitted successfully

## 👮 Admin Account Testing

### Step 1: Setup Admin Account
**Endpoint**: `POST /api/v1/admin/setup`
- Navigate to: **Admin** → **Setup Admin Account**
- Update with admin credentials:
  ```json
  {
    "email": "admin-test@example.com",
    "password": "VeryStrongPassword123456!",
    "full_name": "Test Admin",
    "role": "admin",
    "security_level": "enhanced",
    "mfa_required": true,
    "ip_whitelist": ["127.0.0.1"],
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
        "is_backup": true
      }
    ],
    "security_policy_accepted": true,
    "security_policy_version": "1.0"
  }
  ```
- Expected: `201 Created` with security configuration

### Step 2: Get Admin Onboarding Status
**Endpoint**: `GET /api/v1/admin/onboarding-status`
- Navigate to: **Admin** → **Get Admin Onboarding Status**
- Verify: Security health score and completion status

### Step 3: Configure Admin Security
**Endpoint**: `POST /api/v1/admin/security-config`
- Navigate to: **Admin** → **Configure Admin Security**
- Update security settings as needed
- Verify: Security configuration updates

### Step 4: Complete Admin Setup
**Endpoint**: `POST /api/v1/admin/complete-setup`
- Navigate to: **Admin** → **Complete Admin Setup**
- Finalize the admin setup process

## 🧪 Advanced Testing Scenarios

### Cookie-Based Authentication Testing
1. Use **Auth** → **Login Cookie** instead of standard login
2. For all subsequent requests, ensure Postman includes cookies
3. Verify HttpOnly cookie behavior

### Error Condition Testing
| Scenario | Expected Response | Endpoint |
|----------|-------------------|----------|
| Invalid credentials | `401 Unauthorized` | Auth endpoints |
| Missing required fields | `400 Bad Request` | Instructor/Admin setup |
| Invalid email format | `400 Bad Request` | All registration endpoints |
| Insufficient permissions | `403 Forbidden` | Admin endpoints |

### Production vs Development Testing
- **Production**: Use `base_url: https://egylms.duckdns.org`
- **Development**: Use `base_url: http://localhost:8000` (after starting backend)

## 🚨 Troubleshooting

### Common Issues and Solutions

#### **401 Unauthorized**
- ✅ Check `access_token` in environment variables
- ✅ Verify authentication was performed first
- ✅ Check token expiration time

#### **400 Bad Request**
- ✅ Validate JSON format (use JSON validator)
- ✅ Check required fields are present
- ✅ Verify field constraints (password length, etc.)

#### **ECONNREFUSED**
- ✅ Ensure backend server is running
- ✅ Verify port number matches (8000 for development)
- ✅ Check network connectivity

#### **CORS Errors**
- ✅ Check backend CORS configuration
- ✅ Ensure `base_url` matches configured origins
- ✅ For development, use `http://localhost:3000` in CORS origins

### Debugging Tips
1. **Enable Postman Console**: View → Show Postman Console
2. **Check Headers**: Verify auth headers are included
3. **Validate Responses**: Use JSON schema validation
4. **Use Tests Tab**: Add automated tests for response validation

## 📊 Testing Checklist

### Instructor Flow
- [ ] Login successful
- [ ] Instructor registration returns 201
- [ ] Onboarding status shows correct progress
- [ ] Profile update works
- [ ] Verification submission successful

### Admin Flow  
- [ ] Admin setup returns 201
- [ ] Security configuration applied
- [ ] Onboarding status complete
- [ ] Emergency contacts configured
- [ ] Security health score calculated

## 📝 Additional Resources

- **API Documentation**: `https://egylms.duckdns.org/docs` (when enabled)
- **Health Check**: `GET /api/v1/ready`
- **Metrics**: `GET /metrics` (if exposed)

This guidance document provides comprehensive instructions for testing all aspects of the LMS backend API, with special emphasis on the enhanced instructor and admin account creation flows.