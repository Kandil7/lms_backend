# Full API Documentation

Generated from live FastAPI OpenAPI schema on 2026-02-22 10:02:20 UTC.

## Environment Base URLs
- Production: `https://egylms.duckdns.org`
- Development: `http://localhost:8000`

## Authentication
- Main auth method: Bearer JWT in `Authorization: Bearer <token>`.
- Production auth flow also supports HTTP-only refresh-token cookies.
- OAuth2 token endpoint (Swagger): `POST /api/v1/auth/token`.

## Coverage
- Paths: **57**
- Operations: **68**
- Tags: **13**

## Endpoint Index
| Method | Path | Summary | Tags | Auth |
|---|---|---|---|---|
| `GET` | `/` | Root | Root | No |
| `GET` | `/api/v1/analytics/courses/{course_id}` | Course Analytics | Analytics | Yes |
| `GET` | `/api/v1/analytics/instructors/{instructor_id}/overview` | Instructor Overview | Analytics | Yes |
| `GET` | `/api/v1/analytics/my-dashboard` | My Dashboard | Analytics | Yes |
| `GET` | `/api/v1/analytics/my-progress` | My Progress | Analytics | Yes |
| `GET` | `/api/v1/analytics/system/overview` | System Overview | Analytics | Yes |
| `POST` | `/api/v1/auth/forgot-password` | Forgot Password | Authentication | No |
| `POST` | `/api/v1/auth/login` | Login | Authentication | No |
| `POST` | `/api/v1/auth/login/mfa` | Verify Mfa Login | Authentication | No |
| `POST` | `/api/v1/auth/logout` | Logout | Authentication | Yes |
| `GET` | `/api/v1/auth/me` | Get Me | Authentication | Yes |
| `POST` | `/api/v1/auth/mfa/disable` | Disable Mfa | Authentication | Yes |
| `POST` | `/api/v1/auth/mfa/enable/confirm` | Confirm Enable Mfa | Authentication | Yes |
| `POST` | `/api/v1/auth/mfa/enable/request` | Request Enable Mfa | Authentication | Yes |
| `POST` | `/api/v1/auth/refresh` | Refresh Tokens | Authentication | Yes |
| `POST` | `/api/v1/auth/register` | Register | Authentication | No |
| `POST` | `/api/v1/auth/reset-password` | Reset Password | Authentication | No |
| `POST` | `/api/v1/auth/token` | OAuth2 token endpoint for Swagger Authorize | Authentication | No |
| `POST` | `/api/v1/auth/verify-email/confirm` | Confirm Email Verification | Authentication | No |
| `POST` | `/api/v1/auth/verify-email/request` | Request Email Verification | Authentication | No |
| `POST` | `/api/v1/certificates/enrollments/{enrollment_id}/generate` | Generate Certificate | Certificates | Yes |
| `GET` | `/api/v1/certificates/my-certificates` | My Certificates | Certificates | Yes |
| `GET` | `/api/v1/certificates/verify/{certificate_number}` | Verify Certificate | Certificates | No |
| `GET` | `/api/v1/certificates/{certificate_id}/download` | Download Certificate | Certificates | Yes |
| `POST` | `/api/v1/certificates/{certificate_id}/revoke` | Revoke Certificate | Certificates | Yes |
| `GET` | `/api/v1/courses` | List Courses | Courses | Yes |
| `POST` | `/api/v1/courses` | Create Course | Courses | Yes |
| `GET` | `/api/v1/courses/{course_id}` | Get Course | Courses | Yes |
| `PATCH` | `/api/v1/courses/{course_id}` | Update Course | Courses | Yes |
| `DELETE` | `/api/v1/courses/{course_id}` | Delete Course | Courses | Yes |
| `GET` | `/api/v1/courses/{course_id}/lessons` | List Lessons | Lessons | Yes |
| `POST` | `/api/v1/courses/{course_id}/lessons` | Create Lesson | Lessons | Yes |
| `POST` | `/api/v1/courses/{course_id}/publish` | Publish Course | Courses | Yes |
| `GET` | `/api/v1/courses/{course_id}/quizzes` | List Course Quizzes | Quizzes | Yes |
| `POST` | `/api/v1/courses/{course_id}/quizzes` | Create Quiz | Quizzes | Yes |
| `GET` | `/api/v1/courses/{course_id}/quizzes/{quiz_id}` | Get Quiz | Quizzes | Yes |
| `PATCH` | `/api/v1/courses/{course_id}/quizzes/{quiz_id}` | Update Quiz | Quizzes | Yes |
| `POST` | `/api/v1/courses/{course_id}/quizzes/{quiz_id}/publish` | Publish Quiz | Quizzes | Yes |
| `GET` | `/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions` | List Questions | Quiz Questions | Yes |
| `POST` | `/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions` | Add Question | Quiz Questions | Yes |
| `GET` | `/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions/manage` | List Questions For Management | Quiz Questions | Yes |
| `PATCH` | `/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}` | Update Question | Quiz Questions | Yes |
| `POST` | `/api/v1/enrollments` | Enroll In Course | Enrollments | Yes |
| `GET` | `/api/v1/enrollments/courses/{course_id}` | List Course Enrollments | Enrollments | Yes |
| `GET` | `/api/v1/enrollments/courses/{course_id}/stats` | Get Course Enrollment Stats | Enrollments | Yes |
| `GET` | `/api/v1/enrollments/my-courses` | List My Courses | Enrollments | Yes |
| `GET` | `/api/v1/enrollments/{enrollment_id}` | Get Enrollment | Enrollments | Yes |
| `POST` | `/api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/complete` | Mark Lesson Completed | Enrollments | Yes |
| `PUT` | `/api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/progress` | Update Lesson Progress | Enrollments | Yes |
| `POST` | `/api/v1/enrollments/{enrollment_id}/review` | Add Review | Enrollments | Yes |
| `GET` | `/api/v1/files/download/{file_id}` | Download File | Files | Yes |
| `GET` | `/api/v1/files/my-files` | List My Files | Files | Yes |
| `POST` | `/api/v1/files/upload` | Upload File | Files | Yes |
| `GET` | `/api/v1/health` | Health Check | Health | No |
| `GET` | `/api/v1/lessons/{lesson_id}` | Get Lesson | Lessons | Yes |
| `PATCH` | `/api/v1/lessons/{lesson_id}` | Update Lesson | Lessons | Yes |
| `DELETE` | `/api/v1/lessons/{lesson_id}` | Delete Lesson | Lessons | Yes |
| `POST` | `/api/v1/quizzes/{quiz_id}/attempts` | Start Attempt | Quiz Attempts | Yes |
| `GET` | `/api/v1/quizzes/{quiz_id}/attempts/my-attempts` | List My Attempts | Quiz Attempts | Yes |
| `GET` | `/api/v1/quizzes/{quiz_id}/attempts/start` | Get Quiz For Attempt | Quiz Attempts | Yes |
| `GET` | `/api/v1/quizzes/{quiz_id}/attempts/{attempt_id}` | Get Attempt Result | Quiz Attempts | Yes |
| `POST` | `/api/v1/quizzes/{quiz_id}/attempts/{attempt_id}/submit` | Submit Attempt | Quiz Attempts | Yes |
| `GET` | `/api/v1/ready` | Readiness Check | Health | No |
| `GET` | `/api/v1/users` | List Users | Users | Yes |
| `POST` | `/api/v1/users` | Create User | Users | Yes |
| `GET` | `/api/v1/users/me` | Get My Profile | Users | Yes |
| `GET` | `/api/v1/users/{user_id}` | Get User | Users | Yes |
| `PATCH` | `/api/v1/users/{user_id}` | Update User | Users | Yes |

## Endpoints By Tag
## Analytics

### GET `/api/v1/analytics/courses/{course_id}`
- Summary: Course Analytics
- Tags: Analytics
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `CourseAnalyticsResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/analytics/instructors/{instructor_id}/overview`
- Summary: Instructor Overview
- Tags: Analytics
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `instructor_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `InstructorOverviewResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/analytics/my-dashboard`
- Summary: My Dashboard
- Tags: Analytics
- Authentication Required: Yes

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `MyDashboardResponse` |

### GET `/api/v1/analytics/my-progress`
- Summary: My Progress
- Tags: Analytics
- Authentication Required: Yes

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `MyProgressSummary` |

### GET `/api/v1/analytics/system/overview`
- Summary: System Overview
- Tags: Analytics
- Authentication Required: Yes

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `SystemOverviewResponse` |

## Authentication

### POST `/api/v1/auth/forgot-password`
- Summary: Forgot Password
- Tags: Authentication
- Authentication Required: No

**Request Body**
- Content-Type: `application/json`
- Schema: `ForgotPasswordRequest`
```json
{
  "email": "user@example.com"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `MessageResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/auth/login`
- Summary: Login
- Tags: Authentication
- Authentication Required: No

**Request Body**
- Content-Type: `application/json`
- Schema: `UserLogin`
```json
{
  "email": "user@example.com",
  "password": "string"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `AuthResponse | MfaChallengeResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/auth/login/mfa`
- Summary: Verify Mfa Login
- Tags: Authentication
- Authentication Required: No

**Request Body**
- Content-Type: `application/json`
- Schema: `MfaLoginVerifyRequest`
```json
{
  "challenge_token": "string",
  "code": "string"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `AuthResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/auth/logout`
- Summary: Logout
- Tags: Authentication
- Authentication Required: Yes

**Request Body**
- Content-Type: `application/json`
- Schema: `LogoutRequest`
```json
{
  "refresh_token": "string"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `204` | Successful Response | - | - |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/auth/me`
- Summary: Get Me
- Tags: Authentication
- Authentication Required: Yes

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `UserResponse` |

### POST `/api/v1/auth/mfa/disable`
- Summary: Disable Mfa
- Tags: Authentication
- Authentication Required: Yes

**Request Body**
- Content-Type: `application/json`
- Schema: `MfaDisableRequest`
```json
{
  "password": "string"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `MessageResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/auth/mfa/enable/confirm`
- Summary: Confirm Enable Mfa
- Tags: Authentication
- Authentication Required: Yes

**Request Body**
- Content-Type: `application/json`
- Schema: `MfaCodeRequest`
```json
{
  "code": "string"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `MessageResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/auth/mfa/enable/request`
- Summary: Request Enable Mfa
- Tags: Authentication
- Authentication Required: Yes

**Request Body**
- Content-Type: `application/json`
- Schema: `MfaEnableRequest`
```json
{
  "password": "string"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `MessageResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/auth/refresh`
- Summary: Refresh Tokens
- Tags: Authentication
- Authentication Required: Yes

**Request Body**
- Content-Type: `application/json`
- Schema: `RefreshTokenRequest`
```json
{
  "refresh_token": "string"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `AuthResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/auth/register`
- Summary: Register
- Tags: Authentication
- Authentication Required: No

**Request Body**
- Content-Type: `application/json`
- Schema: `UserCreate`
```json
{
  "email": "user@example.com",
  "full_name": "string",
  "role": "admin",
  "password": "string"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `201` | Successful Response | `application/json` | `AuthResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/auth/reset-password`
- Summary: Reset Password
- Tags: Authentication
- Authentication Required: No

**Request Body**
- Content-Type: `application/json`
- Schema: `ResetPasswordRequest`
```json
{
  "token": "string",
  "new_password": "string"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `MessageResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/auth/token`
- Summary: OAuth2 token endpoint for Swagger Authorize
- Tags: Authentication
- Authentication Required: No

**Request Body**
- Content-Type: `application/x-www-form-urlencoded`
- Schema: `Body_oauth_token_api_v1_auth_token_post`

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `TokenResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/auth/verify-email/confirm`
- Summary: Confirm Email Verification
- Tags: Authentication
- Authentication Required: No

**Request Body**
- Content-Type: `application/json`
- Schema: `VerifyEmailConfirmRequest`
```json
{
  "token": "string"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `MessageResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/auth/verify-email/request`
- Summary: Request Email Verification
- Tags: Authentication
- Authentication Required: No

**Request Body**
- Content-Type: `application/json`
- Schema: `VerifyEmailRequest`
```json
{
  "email": "user@example.com"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `MessageResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

## Certificates

### POST `/api/v1/certificates/enrollments/{enrollment_id}/generate`
- Summary: Generate Certificate
- Tags: Certificates
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `enrollment_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `201` | Successful Response | `application/json` | `CertificateResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/certificates/my-certificates`
- Summary: My Certificates
- Tags: Certificates
- Authentication Required: Yes

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `CertificateListResponse` |

### GET `/api/v1/certificates/verify/{certificate_number}`
- Summary: Verify Certificate
- Tags: Certificates
- Authentication Required: No

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `certificate_number` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `CertificateVerifyResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/certificates/{certificate_id}/download`
- Summary: Download Certificate
- Tags: Certificates
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `certificate_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `-` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/certificates/{certificate_id}/revoke`
- Summary: Revoke Certificate
- Tags: Certificates
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `certificate_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `CertificateResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

## Courses

### GET `/api/v1/courses`
- Summary: List Courses
- Tags: Courses
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `page` | `query` | No | `integer` |  |
| `page_size` | `query` | No | `integer` |  |
| `category` | `query` | No | `string | null` |  |
| `difficulty_level` | `query` | No | `string | null` |  |
| `mine` | `query` | No | `boolean` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `CourseListResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/courses`
- Summary: Create Course
- Tags: Courses
- Authentication Required: Yes

**Request Body**
- Content-Type: `application/json`
- Schema: `CourseCreate`
```json
{
  "title": "string",
  "slug": "string",
  "description": "string",
  "category": "string",
  "difficulty_level": "string",
  "thumbnail_url": "string",
  "estimated_duration_minutes": 1,
  "metadata": {}
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `201` | Successful Response | `application/json` | `CourseResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/courses/{course_id}`
- Summary: Get Course
- Tags: Courses
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `CourseResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### PATCH `/api/v1/courses/{course_id}`
- Summary: Update Course
- Tags: Courses
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |

**Request Body**
- Content-Type: `application/json`
- Schema: `CourseUpdate`
```json
{
  "title": "string",
  "description": "string",
  "category": "string",
  "difficulty_level": "string",
  "thumbnail_url": "string",
  "estimated_duration_minutes": 1,
  "is_published": false,
  "metadata": {}
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `CourseResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### DELETE `/api/v1/courses/{course_id}`
- Summary: Delete Course
- Tags: Courses
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `204` | Successful Response | - | - |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/courses/{course_id}/publish`
- Summary: Publish Course
- Tags: Courses
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `CourseResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

## Enrollments

### POST `/api/v1/enrollments`
- Summary: Enroll In Course
- Tags: Enrollments
- Authentication Required: Yes

**Request Body**
- Content-Type: `application/json`
- Schema: `EnrollmentCreate`
```json
{
  "course_id": "00000000-0000-0000-0000-000000000000"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `201` | Successful Response | `application/json` | `EnrollmentResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/enrollments/courses/{course_id}`
- Summary: List Course Enrollments
- Tags: Enrollments
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |
| `page` | `query` | No | `integer` |  |
| `page_size` | `query` | No | `integer` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `EnrollmentListResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/enrollments/courses/{course_id}/stats`
- Summary: Get Course Enrollment Stats
- Tags: Enrollments
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `CourseEnrollmentStats` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/enrollments/my-courses`
- Summary: List My Courses
- Tags: Enrollments
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `page` | `query` | No | `integer` |  |
| `page_size` | `query` | No | `integer` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `EnrollmentListResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/enrollments/{enrollment_id}`
- Summary: Get Enrollment
- Tags: Enrollments
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `enrollment_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `EnrollmentResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/complete`
- Summary: Mark Lesson Completed
- Tags: Enrollments
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `enrollment_id` | `path` | Yes | `string` |  |
| `lesson_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `LessonProgressResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### PUT `/api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/progress`
- Summary: Update Lesson Progress
- Tags: Enrollments
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `enrollment_id` | `path` | Yes | `string` |  |
| `lesson_id` | `path` | Yes | `string` |  |

**Request Body**
- Content-Type: `application/json`
- Schema: `LessonProgressUpdate`
```json
{
  "status": "string",
  "time_spent_seconds": 1,
  "last_position_seconds": 1,
  "completion_percentage": 1,
  "notes": "string"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `LessonProgressResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/enrollments/{enrollment_id}/review`
- Summary: Add Review
- Tags: Enrollments
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `enrollment_id` | `path` | Yes | `string` |  |

**Request Body**
- Content-Type: `application/json`
- Schema: `ReviewCreate`
```json
{
  "rating": 1,
  "review": "string"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `EnrollmentResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

## Files

### GET `/api/v1/files/download/{file_id}`
- Summary: Download File
- Tags: Files
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `file_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `-` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/files/my-files`
- Summary: List My Files
- Tags: Files
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `file_type` | `query` | No | `string | null` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `FileListResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/files/upload`
- Summary: Upload File
- Tags: Files
- Authentication Required: Yes

**Request Body**
- Content-Type: `multipart/form-data`
- Schema: `Body_upload_file_api_v1_files_upload_post`

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `201` | Successful Response | `application/json` | `FileResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

## Health

### GET `/api/v1/health`
- Summary: Health Check
- Tags: Health
- Authentication Required: No

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `object` |

### GET `/api/v1/ready`
- Summary: Readiness Check
- Tags: Health
- Authentication Required: No

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `object` |

## Lessons

### GET `/api/v1/courses/{course_id}/lessons`
- Summary: List Lessons
- Tags: Lessons
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `LessonListResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/courses/{course_id}/lessons`
- Summary: Create Lesson
- Tags: Lessons
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |

**Request Body**
- Content-Type: `application/json`
- Schema: `LessonCreate`
```json
{
  "title": "string",
  "slug": "string",
  "description": "string",
  "content": "string",
  "lesson_type": "string",
  "order_index": 1,
  "parent_lesson_id": "00000000-0000-0000-0000-000000000000",
  "duration_minutes": 1,
  "video_url": "string",
  "is_preview": false,
  "metadata": {}
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `201` | Successful Response | `application/json` | `LessonResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/lessons/{lesson_id}`
- Summary: Get Lesson
- Tags: Lessons
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `lesson_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `LessonResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### PATCH `/api/v1/lessons/{lesson_id}`
- Summary: Update Lesson
- Tags: Lessons
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `lesson_id` | `path` | Yes | `string` |  |

**Request Body**
- Content-Type: `application/json`
- Schema: `LessonUpdate`
```json
{
  "title": "string",
  "description": "string",
  "content": "string",
  "lesson_type": "string",
  "order_index": 1,
  "parent_lesson_id": "00000000-0000-0000-0000-000000000000",
  "duration_minutes": 1,
  "video_url": "string",
  "is_preview": false,
  "metadata": {}
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `LessonResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### DELETE `/api/v1/lessons/{lesson_id}`
- Summary: Delete Lesson
- Tags: Lessons
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `lesson_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `204` | Successful Response | - | - |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

## Quiz Attempts

### POST `/api/v1/quizzes/{quiz_id}/attempts`
- Summary: Start Attempt
- Tags: Quiz Attempts
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `quiz_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `201` | Successful Response | `application/json` | `AttemptStartResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/quizzes/{quiz_id}/attempts/my-attempts`
- Summary: List My Attempts
- Tags: Quiz Attempts
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `quiz_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `array[AttemptResponse]` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/quizzes/{quiz_id}/attempts/start`
- Summary: Get Quiz For Attempt
- Tags: Quiz Attempts
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `quiz_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `QuizTakeResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/quizzes/{quiz_id}/attempts/{attempt_id}`
- Summary: Get Attempt Result
- Tags: Quiz Attempts
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `quiz_id` | `path` | Yes | `string` |  |
| `attempt_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `AttemptResultResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/quizzes/{quiz_id}/attempts/{attempt_id}/submit`
- Summary: Submit Attempt
- Tags: Quiz Attempts
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `quiz_id` | `path` | Yes | `string` |  |
| `attempt_id` | `path` | Yes | `string` |  |

**Request Body**
- Content-Type: `application/json`
- Schema: `AttemptSubmitRequest`
```json
{
  "answers": [
    {
      "question_id": "00000000-0000-0000-0000-000000000000",
      "selected_option_id": "string",
      "answer_text": "string"
    }
  ]
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `AttemptResultResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

## Quiz Questions

### GET `/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions`
- Summary: List Questions
- Tags: Quiz Questions
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |
| `quiz_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `array[QuestionPublicResponse]` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions`
- Summary: Add Question
- Tags: Quiz Questions
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |
| `quiz_id` | `path` | Yes | `string` |  |

**Request Body**
- Content-Type: `application/json`
- Schema: `QuestionCreate`
```json
{
  "question_text": "string",
  "question_type": "string",
  "points": 1,
  "explanation": "string",
  "options": [
    {
      "option_id": "string",
      "option_text": "string",
      "is_correct": false
    }
  ],
  "correct_answer": "string",
  "metadata": {}
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `201` | Successful Response | `application/json` | `QuestionResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions/manage`
- Summary: List Questions For Management
- Tags: Quiz Questions
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |
| `quiz_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `array[QuestionResponse]` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### PATCH `/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}`
- Summary: Update Question
- Tags: Quiz Questions
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |
| `quiz_id` | `path` | Yes | `string` |  |
| `question_id` | `path` | Yes | `string` |  |

**Request Body**
- Content-Type: `application/json`
- Schema: `QuestionUpdate`
```json
{
  "question_text": "string",
  "question_type": "string",
  "points": 1,
  "explanation": "string",
  "options": [
    {
      "option_id": "string",
      "option_text": "string",
      "is_correct": false
    }
  ],
  "correct_answer": "string",
  "metadata": {}
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `QuestionResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

## Quizzes

### GET `/api/v1/courses/{course_id}/quizzes`
- Summary: List Course Quizzes
- Tags: Quizzes
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `QuizListResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/courses/{course_id}/quizzes`
- Summary: Create Quiz
- Tags: Quizzes
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |

**Request Body**
- Content-Type: `application/json`
- Schema: `QuizCreate`
```json
{
  "lesson_id": "00000000-0000-0000-0000-000000000000",
  "title": "string",
  "description": "string",
  "quiz_type": "string",
  "time_limit_minutes": 1,
  "passing_score": 1,
  "max_attempts": 1,
  "shuffle_questions": false,
  "shuffle_options": false,
  "show_correct_answers": false
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `201` | Successful Response | `application/json` | `QuizResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/courses/{course_id}/quizzes/{quiz_id}`
- Summary: Get Quiz
- Tags: Quizzes
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |
| `quiz_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `QuizResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### PATCH `/api/v1/courses/{course_id}/quizzes/{quiz_id}`
- Summary: Update Quiz
- Tags: Quizzes
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |
| `quiz_id` | `path` | Yes | `string` |  |

**Request Body**
- Content-Type: `application/json`
- Schema: `QuizUpdate`
```json
{
  "title": "string",
  "description": "string",
  "quiz_type": "string",
  "time_limit_minutes": 1,
  "passing_score": 1,
  "max_attempts": 1,
  "shuffle_questions": false,
  "shuffle_options": false,
  "show_correct_answers": false,
  "is_published": false
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `QuizResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/courses/{course_id}/quizzes/{quiz_id}/publish`
- Summary: Publish Quiz
- Tags: Quizzes
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `course_id` | `path` | Yes | `string` |  |
| `quiz_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `QuizResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

## Root

### GET `/`
- Summary: Root
- Tags: Root
- Authentication Required: No

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `object` |

## Users

### GET `/api/v1/users`
- Summary: List Users
- Tags: Users
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `page` | `query` | No | `integer` | Page number |
| `page_size` | `query` | No | `integer` | Items per page |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `UserListResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### POST `/api/v1/users`
- Summary: Create User
- Tags: Users
- Authentication Required: Yes

**Request Body**
- Content-Type: `application/json`
- Schema: `UserCreate`
```json
{
  "email": "user@example.com",
  "full_name": "string",
  "role": "admin",
  "password": "string"
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `201` | Successful Response | `application/json` | `UserResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### GET `/api/v1/users/me`
- Summary: Get My Profile
- Tags: Users
- Authentication Required: Yes

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `UserResponse` |

### GET `/api/v1/users/{user_id}`
- Summary: Get User
- Tags: Users
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `user_id` | `path` | Yes | `string` |  |

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `UserResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

### PATCH `/api/v1/users/{user_id}`
- Summary: Update User
- Tags: Users
- Authentication Required: Yes

**Parameters**
| Name | In | Required | Type | Description |
|---|---|---|---|---|
| `user_id` | `path` | Yes | `string` |  |

**Request Body**
- Content-Type: `application/json`
- Schema: `UserUpdate`
```json
{
  "full_name": "string",
  "role": "admin",
  "password": "string",
  "is_active": false
}
```

**Responses**
| Status | Description | Content-Type | Schema |
|---|---|---|---|
| `200` | Successful Response | `application/json` | `UserResponse` |
| `422` | Validation Error | `application/json` | `HTTPValidationError` |

## Data Models

### AnswerSubmission
- Type: `object`
- Required fields: `question_id`

| Field | Type | Required | Description |
|---|---|---|---|
| `question_id` | `string` | Yes |  |
| `selected_option_id` | `string | null` | No |  |
| `answer_text` | `string | null` | No |  |

### AttemptResponse
- Type: `object`
- Required fields: `attempt_number`, `enrollment_id`, `graded_at`, `id`, `is_passed`, `max_score`, `percentage`, `quiz_id`, `score`, `started_at`, `status`, `submitted_at`, `time_taken_seconds`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `enrollment_id` | `string` | Yes |  |
| `quiz_id` | `string` | Yes |  |
| `attempt_number` | `integer` | Yes |  |
| `status` | `string` | Yes |  |
| `started_at` | `string` | Yes |  |
| `submitted_at` | `string | null` | Yes |  |
| `graded_at` | `string | null` | Yes |  |
| `score` | `string | null` | Yes |  |
| `max_score` | `string | null` | Yes |  |
| `percentage` | `string | null` | Yes |  |
| `is_passed` | `boolean | null` | Yes |  |
| `time_taken_seconds` | `integer | null` | Yes |  |

### AttemptResultResponse
- Type: `object`
- Required fields: `answers`, `attempt_number`, `enrollment_id`, `graded_at`, `id`, `is_passed`, `max_score`, `percentage`, `quiz_id`, `score`, `started_at`, `status`, `submitted_at`, `time_taken_seconds`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `enrollment_id` | `string` | Yes |  |
| `quiz_id` | `string` | Yes |  |
| `attempt_number` | `integer` | Yes |  |
| `status` | `string` | Yes |  |
| `started_at` | `string` | Yes |  |
| `submitted_at` | `string | null` | Yes |  |
| `graded_at` | `string | null` | Yes |  |
| `score` | `string | null` | Yes |  |
| `max_score` | `string | null` | Yes |  |
| `percentage` | `string | null` | Yes |  |
| `is_passed` | `boolean | null` | Yes |  |
| `time_taken_seconds` | `integer | null` | Yes |  |
| `answers` | `array[object] | null` | Yes |  |

### AttemptStartResponse
- Type: `object`
- Required fields: `attempt_number`, `id`, `max_score`, `quiz_id`, `started_at`, `status`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `quiz_id` | `string` | Yes |  |
| `attempt_number` | `integer` | Yes |  |
| `status` | `string` | Yes |  |
| `started_at` | `string` | Yes |  |
| `max_score` | `string` | Yes |  |

### AttemptSubmitRequest
- Type: `object`
- Required fields: None

| Field | Type | Required | Description |
|---|---|---|---|
| `answers` | `array[AnswerSubmission]` | No |  |

### AuthResponse
- Type: `object`
- Required fields: `tokens`, `user`

| Field | Type | Required | Description |
|---|---|---|---|
| `user` | `UserResponse` | Yes |  |
| `tokens` | `TokenResponse` | Yes |  |

### Body_oauth_token_api_v1_auth_token_post
- Type: `object`
- Required fields: `password`, `username`

| Field | Type | Required | Description |
|---|---|---|---|
| `grant_type` | `string | null` | No |  |
| `username` | `string` | Yes |  |
| `password` | `string` | Yes |  |
| `scope` | `string` | No |  |
| `client_id` | `string | null` | No |  |
| `client_secret` | `string | null` | No |  |

### Body_upload_file_api_v1_files_upload_post
- Type: `object`
- Required fields: `file`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | `string` | Yes |  |
| `folder` | `string` | No |  |
| `is_public` | `boolean` | No |  |

### CertificateListResponse
- Type: `object`
- Required fields: `certificates`, `total`

| Field | Type | Required | Description |
|---|---|---|---|
| `certificates` | `array[CertificateResponse]` | Yes |  |
| `total` | `integer` | Yes |  |

### CertificateResponse
- Type: `object`
- Required fields: `certificate_number`, `completion_date`, `course_id`, `id`, `is_revoked`, `issued_at`, `pdf_url`, `student_id`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `certificate_number` | `string` | Yes |  |
| `student_id` | `string` | Yes |  |
| `course_id` | `string` | Yes |  |
| `completion_date` | `string` | Yes |  |
| `issued_at` | `string` | Yes |  |
| `pdf_url` | `string` | Yes |  |
| `is_revoked` | `boolean` | Yes |  |

### CertificateVerifyResponse
- Type: `object`
- Required fields: `certificate`, `message`, `valid`

| Field | Type | Required | Description |
|---|---|---|---|
| `valid` | `boolean` | Yes |  |
| `certificate` | `CertificateResponse | null` | Yes |  |
| `message` | `string` | Yes |  |

### CourseAnalyticsResponse
- Type: `object`
- Required fields: `active_students`, `average_progress`, `average_rating`, `average_time_hours`, `completed_students`, `completion_rate`, `course_id`, `course_title`, `total_enrollments`, `total_reviews`

| Field | Type | Required | Description |
|---|---|---|---|
| `course_id` | `string` | Yes |  |
| `course_title` | `string` | Yes |  |
| `total_enrollments` | `integer` | Yes |  |
| `active_students` | `integer` | Yes |  |
| `completed_students` | `integer` | Yes |  |
| `completion_rate` | `string` | Yes |  |
| `average_progress` | `string` | Yes |  |
| `average_time_hours` | `string` | Yes |  |
| `average_rating` | `string` | Yes |  |
| `total_reviews` | `integer` | Yes |  |

### CourseCreate
- Type: `object`
- Required fields: `title`

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | `string` | Yes |  |
| `slug` | `string | null` | No |  |
| `description` | `string | null` | No |  |
| `category` | `string | null` | No |  |
| `difficulty_level` | `string | null` | No |  |
| `thumbnail_url` | `string | null` | No |  |
| `estimated_duration_minutes` | `integer | null` | No |  |
| `metadata` | `object | null` | No |  |

### CourseEnrollmentStats
- Type: `object`
- Required fields: `active_enrollments`, `average_progress`, `completed_enrollments`, `course_id`, `total_enrollments`

| Field | Type | Required | Description |
|---|---|---|---|
| `course_id` | `string` | Yes |  |
| `total_enrollments` | `integer` | Yes |  |
| `active_enrollments` | `integer` | Yes |  |
| `completed_enrollments` | `integer` | Yes |  |
| `average_progress` | `string` | Yes |  |

### CourseListResponse
- Type: `object`
- Required fields: `items`, `page`, `page_size`, `total`, `total_pages`

| Field | Type | Required | Description |
|---|---|---|---|
| `items` | `array[CourseResponse]` | Yes |  |
| `total` | `integer` | Yes |  |
| `page` | `integer` | Yes |  |
| `page_size` | `integer` | Yes |  |
| `total_pages` | `integer` | Yes |  |

### CourseProgressItem
- Type: `object`
- Required fields: `average_quiz_score`, `completed_lessons`, `course_id`, `course_title`, `progress_percentage`, `quizzes_completed`, `time_spent_hours`, `total_lessons`

| Field | Type | Required | Description |
|---|---|---|---|
| `course_id` | `string` | Yes |  |
| `course_title` | `string` | Yes |  |
| `progress_percentage` | `string` | Yes |  |
| `completed_lessons` | `integer` | Yes |  |
| `total_lessons` | `integer` | Yes |  |
| `time_spent_hours` | `string` | Yes |  |
| `quizzes_completed` | `integer` | Yes |  |
| `average_quiz_score` | `string` | Yes |  |

### CourseResponse
- Type: `object`
- Required fields: `category`, `created_at`, `description`, `difficulty_level`, `estimated_duration_minutes`, `id`, `instructor_id`, `is_published`, `slug`, `thumbnail_url`, `title`, `updated_at`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `title` | `string` | Yes |  |
| `slug` | `string` | Yes |  |
| `description` | `string | null` | Yes |  |
| `instructor_id` | `string` | Yes |  |
| `category` | `string | null` | Yes |  |
| `difficulty_level` | `string | null` | Yes |  |
| `is_published` | `boolean` | Yes |  |
| `thumbnail_url` | `string | null` | Yes |  |
| `estimated_duration_minutes` | `integer | null` | Yes |  |
| `created_at` | `string` | Yes |  |
| `updated_at` | `string` | Yes |  |

### CourseUpdate
- Type: `object`
- Required fields: None

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | `string | null` | No |  |
| `description` | `string | null` | No |  |
| `category` | `string | null` | No |  |
| `difficulty_level` | `string | null` | No |  |
| `thumbnail_url` | `string | null` | No |  |
| `estimated_duration_minutes` | `integer | null` | No |  |
| `is_published` | `boolean | null` | No |  |
| `metadata` | `object | null` | No |  |

### DailyActivityItem
- Type: `object`
- Required fields: `date`, `lessons_completed`, `quizzes_taken`, `time_spent_minutes`

| Field | Type | Required | Description |
|---|---|---|---|
| `date` | `string` | Yes |  |
| `lessons_completed` | `integer` | Yes |  |
| `time_spent_minutes` | `integer` | Yes |  |
| `quizzes_taken` | `integer` | Yes |  |

### EnrollmentCreate
- Type: `object`
- Required fields: `course_id`

| Field | Type | Required | Description |
|---|---|---|---|
| `course_id` | `string` | Yes |  |

### EnrollmentListResponse
- Type: `object`
- Required fields: `items`, `page`, `page_size`, `total`, `total_pages`

| Field | Type | Required | Description |
|---|---|---|---|
| `items` | `array[EnrollmentResponse]` | Yes |  |
| `total` | `integer` | Yes |  |
| `page` | `integer` | Yes |  |
| `page_size` | `integer` | Yes |  |
| `total_pages` | `integer` | Yes |  |

### EnrollmentResponse
- Type: `object`
- Required fields: `certificate_issued_at`, `completed_at`, `completed_lessons_count`, `course_id`, `enrolled_at`, `id`, `last_accessed_at`, `progress_percentage`, `rating`, `review`, `started_at`, `status`, `student_id`, `total_lessons_count`, `total_time_spent_seconds`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `student_id` | `string` | Yes |  |
| `course_id` | `string` | Yes |  |
| `enrolled_at` | `string` | Yes |  |
| `started_at` | `string | null` | Yes |  |
| `completed_at` | `string | null` | Yes |  |
| `status` | `string` | Yes |  |
| `progress_percentage` | `string` | Yes |  |
| `completed_lessons_count` | `integer` | Yes |  |
| `total_lessons_count` | `integer` | Yes |  |
| `total_time_spent_seconds` | `integer` | Yes |  |
| `last_accessed_at` | `string | null` | Yes |  |
| `certificate_issued_at` | `string | null` | Yes |  |
| `rating` | `integer | null` | Yes |  |
| `review` | `string | null` | Yes |  |

### FileListResponse
- Type: `object`
- Required fields: `files`, `total`

| Field | Type | Required | Description |
|---|---|---|---|
| `files` | `array[FileResponse]` | Yes |  |
| `total` | `integer` | Yes |  |

### FileResponse
- Type: `object`
- Required fields: `created_at`, `file_size`, `file_type`, `file_url`, `filename`, `id`, `mime_type`, `original_filename`, `storage_provider`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `filename` | `string` | Yes |  |
| `original_filename` | `string` | Yes |  |
| `file_url` | `string` | Yes |  |
| `file_type` | `string` | Yes |  |
| `mime_type` | `string` | Yes |  |
| `file_size` | `integer` | Yes |  |
| `storage_provider` | `string` | Yes |  |
| `created_at` | `string` | Yes |  |

### ForgotPasswordRequest
- Type: `object`
- Required fields: `email`

| Field | Type | Required | Description |
|---|---|---|---|
| `email` | `string` | Yes |  |

### HTTPValidationError
- Type: `object`
- Required fields: None

| Field | Type | Required | Description |
|---|---|---|---|
| `detail` | `array[ValidationError]` | No |  |

### InstructorOverviewResponse
- Type: `object`
- Required fields: `average_course_rating`, `instructor_id`, `published_courses`, `total_courses`, `total_enrollments`, `total_students`

| Field | Type | Required | Description |
|---|---|---|---|
| `instructor_id` | `string` | Yes |  |
| `total_courses` | `integer` | Yes |  |
| `published_courses` | `integer` | Yes |  |
| `total_students` | `integer` | Yes |  |
| `total_enrollments` | `integer` | Yes |  |
| `average_course_rating` | `string` | Yes |  |

### LessonCreate
- Type: `object`
- Required fields: `lesson_type`, `title`

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | `string` | Yes |  |
| `slug` | `string | null` | No |  |
| `description` | `string | null` | No |  |
| `content` | `string | null` | No |  |
| `lesson_type` | `string` | Yes |  |
| `order_index` | `integer | null` | No |  |
| `parent_lesson_id` | `string | null` | No |  |
| `duration_minutes` | `integer | null` | No |  |
| `video_url` | `string | null` | No |  |
| `is_preview` | `boolean` | No |  |
| `metadata` | `object | null` | No |  |

### LessonListResponse
- Type: `object`
- Required fields: `items`, `total`

| Field | Type | Required | Description |
|---|---|---|---|
| `items` | `array[LessonResponse]` | Yes |  |
| `total` | `integer` | Yes |  |

### LessonProgressResponse
- Type: `object`
- Required fields: `completed_at`, `completion_percentage`, `enrollment_id`, `id`, `last_position_seconds`, `lesson_id`, `started_at`, `status`, `time_spent_seconds`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `enrollment_id` | `string` | Yes |  |
| `lesson_id` | `string` | Yes |  |
| `status` | `string` | Yes |  |
| `started_at` | `string | null` | Yes |  |
| `completed_at` | `string | null` | Yes |  |
| `time_spent_seconds` | `integer` | Yes |  |
| `last_position_seconds` | `integer` | Yes |  |
| `completion_percentage` | `string` | Yes |  |

### LessonProgressUpdate
- Type: `object`
- Required fields: None

| Field | Type | Required | Description |
|---|---|---|---|
| `status` | `string | null` | No |  |
| `time_spent_seconds` | `integer | null` | No |  |
| `last_position_seconds` | `integer | null` | No |  |
| `completion_percentage` | `number | string | null` | No |  |
| `notes` | `string | null` | No |  |

### LessonResponse
- Type: `object`
- Required fields: `content`, `course_id`, `created_at`, `description`, `duration_minutes`, `id`, `is_preview`, `lesson_type`, `order_index`, `parent_lesson_id`, `slug`, `title`, `updated_at`, `video_url`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `course_id` | `string` | Yes |  |
| `title` | `string` | Yes |  |
| `slug` | `string` | Yes |  |
| `description` | `string | null` | Yes |  |
| `content` | `string | null` | Yes |  |
| `lesson_type` | `string` | Yes |  |
| `order_index` | `integer` | Yes |  |
| `parent_lesson_id` | `string | null` | Yes |  |
| `duration_minutes` | `integer | null` | Yes |  |
| `video_url` | `string | null` | Yes |  |
| `is_preview` | `boolean` | Yes |  |
| `created_at` | `string` | Yes |  |
| `updated_at` | `string` | Yes |  |

### LessonUpdate
- Type: `object`
- Required fields: None

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | `string | null` | No |  |
| `description` | `string | null` | No |  |
| `content` | `string | null` | No |  |
| `lesson_type` | `string | null` | No |  |
| `order_index` | `integer | null` | No |  |
| `parent_lesson_id` | `string | null` | No |  |
| `duration_minutes` | `integer | null` | No |  |
| `video_url` | `string | null` | No |  |
| `is_preview` | `boolean | null` | No |  |
| `metadata` | `object | null` | No |  |

### LogoutRequest
- Type: `object`
- Required fields: `refresh_token`

| Field | Type | Required | Description |
|---|---|---|---|
| `refresh_token` | `string` | Yes |  |

### MessageResponse
- Type: `object`
- Required fields: `message`

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | `string` | Yes |  |

### MfaChallengeResponse
- Type: `object`
- Required fields: `challenge_token`, `expires_in_seconds`

| Field | Type | Required | Description |
|---|---|---|---|
| `mfa_required` | `boolean` | No |  |
| `challenge_token` | `string` | Yes |  |
| `expires_in_seconds` | `integer` | Yes |  |
| `message` | `string` | No |  |

### MfaCodeRequest
- Type: `object`
- Required fields: `code`

| Field | Type | Required | Description |
|---|---|---|---|
| `code` | `string` | Yes |  |

### MfaDisableRequest
- Type: `object`
- Required fields: `password`

| Field | Type | Required | Description |
|---|---|---|---|
| `password` | `string` | Yes |  |

### MfaEnableRequest
- Type: `object`
- Required fields: `password`

| Field | Type | Required | Description |
|---|---|---|---|
| `password` | `string` | Yes |  |

### MfaLoginVerifyRequest
- Type: `object`
- Required fields: `challenge_token`, `code`

| Field | Type | Required | Description |
|---|---|---|---|
| `challenge_token` | `string` | Yes |  |
| `code` | `string` | Yes |  |

### MyDashboardResponse
- Type: `object`
- Required fields: `courses`, `recent_activity`, `student_id`, `summary`

| Field | Type | Required | Description |
|---|---|---|---|
| `student_id` | `string` | Yes |  |
| `summary` | `MyProgressSummary` | Yes |  |
| `courses` | `array[CourseProgressItem]` | Yes |  |
| `recent_activity` | `array[DailyActivityItem]` | Yes |  |

### MyProgressSummary
- Type: `object`
- Required fields: `active_enrollments`, `average_progress`, `average_quiz_score`, `completed_enrollments`, `quizzes_passed`, `quizzes_taken`, `student_id`, `total_enrollments`, `total_lessons_completed`, `total_time_hours`

| Field | Type | Required | Description |
|---|---|---|---|
| `student_id` | `string` | Yes |  |
| `total_enrollments` | `integer` | Yes |  |
| `active_enrollments` | `integer` | Yes |  |
| `completed_enrollments` | `integer` | Yes |  |
| `average_progress` | `string` | Yes |  |
| `total_time_hours` | `string` | Yes |  |
| `total_lessons_completed` | `integer` | Yes |  |
| `quizzes_taken` | `integer` | Yes |  |
| `quizzes_passed` | `integer` | Yes |  |
| `average_quiz_score` | `string` | Yes |  |

### QuestionCreate
- Type: `object`
- Required fields: `question_text`, `question_type`

| Field | Type | Required | Description |
|---|---|---|---|
| `question_text` | `string` | Yes |  |
| `question_type` | `string` | Yes |  |
| `points` | `number | string` | No |  |
| `explanation` | `string | null` | No |  |
| `options` | `array[QuestionOptionCreate] | null` | No |  |
| `correct_answer` | `string | null` | No |  |
| `metadata` | `object | null` | No |  |

### QuestionOptionCreate
- Type: `object`
- Required fields: `option_text`

| Field | Type | Required | Description |
|---|---|---|---|
| `option_id` | `string` | No |  |
| `option_text` | `string` | Yes |  |
| `is_correct` | `boolean` | No |  |

### QuestionOptionResponse
- Type: `object`
- Required fields: `option_id`, `option_text`

| Field | Type | Required | Description |
|---|---|---|---|
| `option_id` | `string` | Yes |  |
| `option_text` | `string` | Yes |  |

### QuestionPublicResponse
- Type: `object`
- Required fields: `id`, `options`, `points`, `question_text`, `question_type`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `question_text` | `string` | Yes |  |
| `question_type` | `string` | Yes |  |
| `points` | `string` | Yes |  |
| `options` | `array[QuestionOptionResponse] | null` | Yes |  |

### QuestionResponse
- Type: `object`
- Required fields: `correct_answer`, `explanation`, `id`, `options`, `order_index`, `points`, `question_text`, `question_type`, `quiz_id`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `quiz_id` | `string` | Yes |  |
| `question_text` | `string` | Yes |  |
| `question_type` | `string` | Yes |  |
| `points` | `string` | Yes |  |
| `order_index` | `integer` | Yes |  |
| `explanation` | `string | null` | Yes |  |
| `options` | `array[object] | null` | Yes |  |
| `correct_answer` | `string | null` | Yes |  |

### QuestionUpdate
- Type: `object`
- Required fields: None

| Field | Type | Required | Description |
|---|---|---|---|
| `question_text` | `string | null` | No |  |
| `question_type` | `string | null` | No |  |
| `points` | `number | string | null` | No |  |
| `explanation` | `string | null` | No |  |
| `options` | `array[QuestionOptionCreate] | null` | No |  |
| `correct_answer` | `string | null` | No |  |
| `metadata` | `object | null` | No |  |

### QuizCreate
- Type: `object`
- Required fields: `lesson_id`, `title`

| Field | Type | Required | Description |
|---|---|---|---|
| `lesson_id` | `string` | Yes |  |
| `title` | `string` | Yes |  |
| `description` | `string | null` | No |  |
| `quiz_type` | `string` | No |  |
| `time_limit_minutes` | `integer | null` | No |  |
| `passing_score` | `number | string` | No |  |
| `max_attempts` | `integer | null` | No |  |
| `shuffle_questions` | `boolean` | No |  |
| `shuffle_options` | `boolean` | No |  |
| `show_correct_answers` | `boolean` | No |  |

### QuizListItem
- Type: `object`
- Required fields: `description`, `id`, `is_published`, `max_attempts`, `passing_score`, `quiz_type`, `time_limit_minutes`, `title`, `total_points`, `total_questions`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `title` | `string` | Yes |  |
| `description` | `string | null` | Yes |  |
| `quiz_type` | `string` | Yes |  |
| `time_limit_minutes` | `integer | null` | Yes |  |
| `passing_score` | `string` | Yes |  |
| `max_attempts` | `integer | null` | Yes |  |
| `total_questions` | `integer` | Yes |  |
| `total_points` | `string` | Yes |  |
| `is_published` | `boolean` | Yes |  |

### QuizListResponse
- Type: `object`
- Required fields: `quizzes`, `total`

| Field | Type | Required | Description |
|---|---|---|---|
| `quizzes` | `array[QuizListItem]` | Yes |  |
| `total` | `integer` | Yes |  |

### QuizResponse
- Type: `object`
- Required fields: `created_at`, `description`, `id`, `is_published`, `lesson_id`, `max_attempts`, `passing_score`, `quiz_type`, `show_correct_answers`, `shuffle_options`, `shuffle_questions`, `time_limit_minutes`, `title`, `updated_at`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `lesson_id` | `string` | Yes |  |
| `title` | `string` | Yes |  |
| `description` | `string | null` | Yes |  |
| `quiz_type` | `string` | Yes |  |
| `time_limit_minutes` | `integer | null` | Yes |  |
| `passing_score` | `string` | Yes |  |
| `max_attempts` | `integer | null` | Yes |  |
| `shuffle_questions` | `boolean` | Yes |  |
| `shuffle_options` | `boolean` | Yes |  |
| `show_correct_answers` | `boolean` | Yes |  |
| `is_published` | `boolean` | Yes |  |
| `created_at` | `string` | Yes |  |
| `updated_at` | `string` | Yes |  |

### QuizTakeResponse
- Type: `object`
- Required fields: `questions`, `quiz`

| Field | Type | Required | Description |
|---|---|---|---|
| `quiz` | `object` | Yes |  |
| `questions` | `array[QuestionPublicResponse]` | Yes |  |

### QuizUpdate
- Type: `object`
- Required fields: None

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | `string | null` | No |  |
| `description` | `string | null` | No |  |
| `quiz_type` | `string | null` | No |  |
| `time_limit_minutes` | `integer | null` | No |  |
| `passing_score` | `number | string | null` | No |  |
| `max_attempts` | `integer | null` | No |  |
| `shuffle_questions` | `boolean | null` | No |  |
| `shuffle_options` | `boolean | null` | No |  |
| `show_correct_answers` | `boolean | null` | No |  |
| `is_published` | `boolean | null` | No |  |

### RefreshTokenRequest
- Type: `object`
- Required fields: `refresh_token`

| Field | Type | Required | Description |
|---|---|---|---|
| `refresh_token` | `string` | Yes |  |

### ResetPasswordRequest
- Type: `object`
- Required fields: `new_password`, `token`

| Field | Type | Required | Description |
|---|---|---|---|
| `token` | `string` | Yes |  |
| `new_password` | `string` | Yes |  |

### ReviewCreate
- Type: `object`
- Required fields: `rating`, `review`

| Field | Type | Required | Description |
|---|---|---|---|
| `rating` | `integer` | Yes |  |
| `review` | `string` | Yes |  |

### Role
- Type: `string`
- Required fields: None

### SystemOverviewResponse
- Type: `object`
- Required fields: `active_enrollments`, `published_courses`, `total_courses`, `total_enrollments`, `total_instructors`, `total_students`, `total_users`

| Field | Type | Required | Description |
|---|---|---|---|
| `total_users` | `integer` | Yes |  |
| `total_students` | `integer` | Yes |  |
| `total_instructors` | `integer` | Yes |  |
| `total_courses` | `integer` | Yes |  |
| `published_courses` | `integer` | Yes |  |
| `total_enrollments` | `integer` | Yes |  |
| `active_enrollments` | `integer` | Yes |  |

### TokenResponse
- Type: `object`
- Required fields: `access_token`, `refresh_token`

| Field | Type | Required | Description |
|---|---|---|---|
| `access_token` | `string` | Yes |  |
| `refresh_token` | `string` | Yes |  |
| `token_type` | `string` | No |  |

### UserCreate
- Type: `object`
- Required fields: `email`, `full_name`, `password`

| Field | Type | Required | Description |
|---|---|---|---|
| `email` | `string` | Yes |  |
| `full_name` | `string` | Yes |  |
| `role` | `Role` | No |  |
| `password` | `string` | Yes |  |

### UserListResponse
- Type: `object`
- Required fields: `items`, `page`, `page_size`, `total`, `total_pages`

| Field | Type | Required | Description |
|---|---|---|---|
| `items` | `array[UserResponse]` | Yes |  |
| `total` | `integer` | Yes |  |
| `page` | `integer` | Yes |  |
| `page_size` | `integer` | Yes |  |
| `total_pages` | `integer` | Yes |  |

### UserLogin
- Type: `object`
- Required fields: `email`, `password`

| Field | Type | Required | Description |
|---|---|---|---|
| `email` | `string` | Yes |  |
| `password` | `string` | Yes |  |

### UserResponse
- Type: `object`
- Required fields: `created_at`, `email`, `full_name`, `id`, `is_active`, `role`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes |  |
| `email` | `string` | Yes |  |
| `full_name` | `string` | Yes |  |
| `role` | `string` | Yes |  |
| `is_active` | `boolean` | Yes |  |
| `mfa_enabled` | `boolean` | No |  |
| `created_at` | `string` | Yes |  |
| `email_verified_at` | `string | null` | No |  |

### UserUpdate
- Type: `object`
- Required fields: None

| Field | Type | Required | Description |
|---|---|---|---|
| `full_name` | `string | null` | No |  |
| `role` | `Role | null` | No |  |
| `password` | `string | null` | No |  |
| `is_active` | `boolean | null` | No |  |

### ValidationError
- Type: `object`
- Required fields: `loc`, `msg`, `type`

| Field | Type | Required | Description |
|---|---|---|---|
| `loc` | `array[string | integer]` | Yes |  |
| `msg` | `string` | Yes |  |
| `type` | `string` | Yes |  |
| `input` | `unknown` | No |  |
| `ctx` | `object` | No |  |

### VerifyEmailConfirmRequest
- Type: `object`
- Required fields: `token`

| Field | Type | Required | Description |
|---|---|---|---|
| `token` | `string` | Yes |  |

### VerifyEmailRequest
- Type: `object`
- Required fields: `email`

| Field | Type | Required | Description |
|---|---|---|---|
| `email` | `string` | Yes |  |
