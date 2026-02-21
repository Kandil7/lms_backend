# Complete File-by-File Documentation

This document provides comprehensive documentation for every single file in the LMS Backend project, explaining its purpose, functionality, and the design decisions behind each implementation.

---

## Root Configuration Files

### requirements.txt

The requirements file defines all Python dependencies for the project. It uses version constraints to ensure compatibility while allowing patch updates within each major version. Each dependency serves a specific purpose in the application stack.

**Core Web Framework**:
- `fastapi>=0.115.0,<1.0.0`: Modern async web framework with automatic OpenAPI documentation. Chosen for its performance, native async support, and excellent type validation through Pydantic integration.
- `uvicorn[standard]>=0.34.0,<1.0.0`: ASGI server implementation required to run FastAPI applications. The standard extras include useful utilities for development.

**Database Layer**:
- `sqlalchemy>=2.0.36,<3.0.0`: SQL toolkit and ORM providing database abstraction. Version 2.0 introduced significant improvements in async support and type safety.
- `alembic>=1.14.0,<2.0.0`: Database migration tool managing schema evolution. Integrates with SQLAlchemy for seamless database versioning.
- `psycopg2-binary>=2.9.10,<3.0.0`: PostgreSQL adapter for Python. The binary distribution simplifies installation without requiring compiler setup.

**Configuration and Validation**:
- `pydantic-settings>=2.7.1,<3.0.0`: Settings management using Pydantic models with environment variable support. Provides automatic type coercion and validation.

**Security**:
- `python-jose[cryptography]>=3.3.0,<4.0.0`: JWT token creation and validation. Includes cryptography extras for secure token signing.
- `passlib[bcrypt]>=1.7.4,<2.0.0`: Password hashing library with bcrypt support. Industry-standard approach for secure password storage.
- `bcrypt>=4.0.1,<4.1.0`: Modern bcrypt implementation. Provides secure password hashing with configurable work factors.
- `email-validator>=2.2.0,<3.0.0`: Email address validation ensuring format correctness.

**Caching and Message Broker**:
- `redis>=5.2.1,<6.0.0`: Redis client for caching, rate limiting, and Celery message broker. Provides high-performance in-memory data operations.

**Observability**:
- `prometheus-client>=0.20.0,<1.0.0`: Prometheus metrics exporter for monitoring application performance and health.
- `sentry-sdk[fastapi]>=2.18.0,<3.0.0`: Error tracking and performance monitoring with FastAPI integration.

**Background Processing**:
- `celery>=5.4.0,<6.0.0`: Distributed task queue for asynchronous processing. Handles long-running operations without blocking API responses.

**Cloud Storage**:
- `azure-storage-blob>=12.26.0,<13.0.0`: Azure Blob Storage SDK for cloud file storage in production environments.

**Templating and PDF**:
- `jinja2>=3.1.5,<4.0.0`: Template engine for email templates and dynamic content generation.
- `fpdf2>=2.8.2,<3.0.0`: Pure Python PDF generation library for creating course completion certificates.

**HTTP Client**:
- `httpx>=0.28.1,<1.0.0`: Async HTTP client for external API calls and webhook delivery.

**Testing**:
- `pytest>=8.3.4,<9.0.0`: Testing framework with extensive plugin ecosystem.
- `pytest-asyncio>=0.25.0,<1.0.0`: Async test support for testing FastAPI endpoints.
- `pytest-cov>=6.0.0,<7.0.0`: Code coverage measurement plugin.
- `faker>=33.1.0,<34.0.0`: Fake data generation for tests.

**Secrets Management**:
- `hvac>=1.2.0,<2.0.0`: HashiCorp Vault client for production secrets management.

---

### alembic.ini

This configuration file controls the Alembic migration system. It defines migration location, SQLAlchemy URL template, and various migration behaviors. The file specifies that migrations are stored in the alembic/ directory and uses a template for generating new migration files.

---

### Dockerfile

The Docker image definition for containerized deployment. It uses Python 3.11 slim base image for minimal size. The build process installs system dependencies, creates a non-root user for security, installs Python dependencies, and configures the application for production use. The final image exposes port 8000 and runs uvicorn as the application server.

---

### docker-compose.yml

Development environment orchestration defining four services. The API service runs the FastAPI application with hot reload enabled. Celery worker and beat services handle background task processing. PostgreSQL and Redis services provide data storage. All services share environment variables and depend on the database services.

---

### docker-compose.prod.yml

Production Docker Compose configuration with additional services for observability. Includes the main API, Celery workers, PostgreSQL, Redis, and optional Prometheus and Grafana for monitoring. Production settings disable debug mode and configure proper logging.

---

## Application Core Files

### app/__init__.py

This empty file marks the app directory as a Python package, allowing imports from the application modules. It serves as the package initialization point for the entire application.

---

### app/main.py

The FastAPI application entry point configuring the entire web server. This file demonstrates several key architectural decisions and serves as the composition root for the application.

**Purpose**: Initializes and configures the FastAPI application with all middleware, routers, and lifespan handlers.

**Key Components**:

The file starts by configuring logging with appropriate format and level based on the DEBUG setting. This ensures consistent log formatting across all application components while allowing verbose output during development.

The `load_all_models()` call ensures all SQLAlchemy models are imported before any database operations occur. This prevents circular import issues and ensures all table definitions are registered with the metadata.

`init_sentry_for_api()` configures the Sentry SDK for error tracking when running in production environments. This provides valuable debugging information for production issues.

**Middleware Configuration**:

The application adds middleware in a specific order that determines how requests are processed:

1. CORS middleware allows cross-origin requests from configured origins. This is essential for frontend applications running on different domains or ports.
2. GZipMiddleware compresses responses larger than 1000 bytes, reducing bandwidth usage and improving response times.
3. TrustedHostMiddleware validates the Host header to prevent HTTP Host header attacks.
4. SecurityHeadersMiddleware adds security headers like HSTS, X-Frame-Options, and Content-Security-Policy when enabled.
5. RequestLoggingMiddleware logs all incoming requests for debugging and audit purposes.
6. MetricsMiddleware tracks request counts and durations for Prometheus when enabled.
7. ResponseEnvelopeMiddleware wraps all responses in a consistent format when enabled.
8. RateLimitMiddleware enforces request rate limits with configurable rules for different endpoint types.

**Lifespan Management**:

The async context manager handles startup and shutdown events. On startup, it creates necessary directories for file uploads and certificates. On shutdown, it can perform cleanup operations.

**Rate Limiting Configuration**:

The application defines rate limiting rules for different endpoint categories. Auth endpoints have stricter limits to prevent brute force attacks. File upload endpoints have per-hour limits to prevent abuse. General API endpoints have per-minute limits balancing usability with protection.

---

### app/core/config.py

The central configuration management system using Pydantic Settings. This file implements environment-based configuration with validation and type coercion.

**Purpose**: Define all application settings with type validation, environment variable support, and production security checks.

**Key Configuration Areas**:

**Application Settings**: Project name, version, environment (development/staging/production), debug mode, API prefix, and documentation visibility. The ENVIRONMENT setting controls many other defaults like API docs availability and strict router imports.

**Database Settings**: Connection URL, pool configuration, and SQLAlchemy echo flag. Pool size and overflow settings are tuned for production workloads.

**Security Settings**: JWT algorithm, token expiration times, MFA configuration, and password reset tokens. These settings balance security with usability.

**Cache Settings**: Redis connection, TTL values for different cache types, and cache key prefixes. Caching is essential for performance with frequently accessed data.

**Rate Limiting Settings**: Request limits, time windows, Redis configuration, and path exclusions. Different limits apply to different endpoint categories.

**File Upload Settings**: Maximum file size, allowed extensions, storage provider selection, and download URL expiration.

**Production Validation**:

The `validate_production_settings` model validator runs after all other validation. It enforces security requirements specific to production environments:

- DEBUG must be disabled
- SECRET_KEY must be strong (32+ characters)
- Token blacklist must fail closed in production
- Tasks cannot run inline in production

The validator also integrates with the secrets manager in production, loading sensitive values from HashiCorp Vault or environment variables instead of configuration files.

**Secrets Management Integration**:

In production, the configuration loads sensitive values from a secrets manager. It first attempts to use HashiCorp Vault, falling back to environment variables. This follows security best practices by not storing secrets in configuration files.

---

### app/core/secrets.py

Implements a secrets management abstraction layer supporting multiple backends. This allows the application to use different secrets sources based on the deployment environment.

**Purpose**: Provide unified interface for retrieving secrets from various sources including environment variables and HashiCorp Vault.

**Key Functions**:

`initialize_secrets_manager()`: Configures which secrets backend to use. In Vault first, falling production, it attempts back to environment variables for development.

`get_secret()`: Retrieves a secret value with optional default. Handles both Vault and environment variable backends transparently.

The secrets manager is used in production to retrieve database passwords, SMTP credentials, Sentry DSN, Azure storage keys, and the JWT secret key. This keeps sensitive values out of configuration files and version control.

---

### app/core/database.py

Database connection and session management. This module provides the SQLAlchemy engine, session factory, and utility functions for database operations.

**Purpose**: Establish database connections, manage sessions, and provide utilities for database operations.

**Engine Configuration**:

The engine is created with settings appropriate for the database type. For PostgreSQL, it configures connection pooling with size and overflow limits. For SQLite (used in testing), it disables thread checking. Pool pre-ping is enabled to detect and recover from stale connections.

**Session Management**:

`get_db()`: FastAPI dependency that provides a database session to route handlers. Sessions are automatically closed after the request completes, ensuring proper resource cleanup.

`session_scope()`: Context manager for programmatic database operations outside of request handlers. It automatically commits on success and rolls back on failure.

**Health Checking**:

`check_database_health()`: Simple connectivity test that executes a SELECT query. Used by the readiness probe to verify database availability.

---

### app/core/security.py

Comprehensive security implementation including JWT token management, password hashing, and token blacklisting. This is the core of the application's authentication system.

**Purpose**: Provide all security-related functionality including token creation, validation, and revocation.

**Password Handling**:

The module uses passlib with bcrypt for password hashing. The CryptContext is configured with bcrypt as the primary scheme, automatically handling salt generation and cost factors. Functions `hash_password()` and `verify_password()` provide the interface for secure password operations.

**JWT Token Management**:

Tokens are created with a standard payload structure including subject (user ID), role, token type, issued at time, expiration time, and a unique JWT ID (jti). The jti enables token blacklisting for immediate session termination.

Different token types have different expiration times:
- Access tokens: 15 minutes for API access
- Refresh tokens: 30 days for session continuation
- Password reset tokens: 30 minutes for security
- Email verification tokens: 24 hours for account activation
- MFA challenge tokens: 10 minutes for quick verification

**Token Blacklisting**:

The `AccessTokenBlacklist` class manages revoked tokens. In production, it uses Redis for distributed blacklisting across multiple API instances. In development, it falls back to in-memory storage. The implementation handles Redis failures gracefully, failing closed in production (rejecting all requests) while allowing continued operation in development.

**Token Validation**:

`decode_token()` validates token signatures, expiration, type, and blacklist status. It raises appropriate exceptions for various failure conditions, which are handled by the exception handlers to return proper HTTP responses.

---

### app/core/permissions.py

Role-based access control (RBAC) implementation defining user roles and permission checking utilities.

**Purpose**: Define user roles and provide decorators/functions for checking permissions in route handlers.

**Role Definitions**:

The `Role` enum defines three user roles:
- ADMIN: Full system access for platform administration
- INSTRUCTOR: Can create and manage courses, view analytics for own content
- STUDENT: Can enroll in courses, take quizzes, track progress

**Permission Checking**:

The module provides functions for checking if a user has appropriate permissions for operations. These are used in route handlers to enforce authorization rules. For example, only instructors and admins can create courses, while only the course owner or admin can modify it.

---

### app/core/cache.py

Redis caching abstraction providing type-safe caching operations with automatic JSON serialization.

**Purpose**: Provide high-level caching interface with support for various data types and TTL management.

**Cache Operations**:

The cache class wraps Redis operations with convenience methods:
- `get()`, `set()`: Basic string cache operations
- `get_json()`, `set_json()`: Automatic JSON serialization for complex types
- `delete_by_prefix()`: Invalidate all keys matching a pattern
- `get_many()`, `set_many()`: Batch operations for efficiency

**Integration with Settings**:

The cache configuration comes from settings including Redis URL, key prefix, and default TTL. Module-specific TTL values allow different caching strategies for different data types (courses, lessons, quizzes).

---

### app/core/exceptions.py

Custom exception classes and global exception handler registration. Provides consistent error responses across the API.

**Purpose**: Define application-specific exceptions and ensure they result in proper HTTP responses.

**Exception Hierarchy**:

The module defines several exception classes:
- `UnauthorizedException`: 401 responses for authentication failures
- `ForbiddenException`: 403 responses for authorization failures
- `NotFoundException`: 404 responses for missing resources
- `ConflictException`: 409 responses for resource conflicts
- `ValidationException`: 422 responses for input validation failures
- `RateLimitException`: 429 responses for rate limit exceeded
- `InternalServerException`: 500 responses for unexpected errors

**Exception Handler Registration**:

`register_exception_handlers()` configures FastAPI to catch all exceptions and return appropriate responses. This ensures consistent error format across all endpoints.

---

### app/core/dependencies.py

FastAPI dependency injection utilities for common operations like getting the current user.

**Purpose**: Provide reusable dependencies for route handlers.

**Current User Dependencies**:

`get_current_user()`: Requires valid JWT token and returns the current user. Used for endpoints requiring authentication.

`get_current_user_optional()`: Returns current user if authenticated, None otherwise. Used for endpoints that behave differently for authenticated and anonymous users.

These dependencies handle token validation, user lookup, and proper error responses automatically.

---

### app/core/health.py

Health check utilities for verifying service dependencies.

**Purpose**: Provide health and readiness check endpoints for container orchestration.

**Health Checks**:

`check_redis_health()`: Tests Redis connectivity by executing a simple command. Returns boolean indicating availability.

The health endpoint returns overall status and individual service statuses (database, Redis) for container orchestration to determine if the service is ready to receive traffic.

---

### app/core/metrics.py

Prometheus metrics integration for application monitoring.

**Purpose**: Expose application metrics for Prometheus scraping and monitoring.

**Metrics Types**:

The module tracks:
- Request counts by method, path, and status code
- Request durations histogram
- Active connections gauge
- Custom business metrics

**Endpoint**:

`build_metrics_router()` creates a separate router for the metrics endpoint, allowing it to be on a different path and potentially protected differently than the main API.

---

### app/core/observability.py

Sentry SDK integration for error tracking and performance monitoring.

**Purpose**: Initialize and configure Sentry for production error monitoring.

**Configuration**:

The module sets up Sentry with:
- DSN from settings
- Environment from configuration
- Release tracking for deployment correlation
- Performance monitoring sampling rates
- FastAPI integration for automatic error capture
- Celery integration for task error tracking

Sentry is only initialized in production or when DSN is explicitly configured, avoiding unnecessary overhead in development.

---

### app/core/model_registry.py

Utility for ensuring all SQLAlchemy models are imported before database operations.

**Purpose**: Prevent circular import issues and ensure all models are registered with SQLAlchemy metadata.

The module imports all model files, ensuring their Base classes are executed and table metadata is registered. This is called at application startup before any database operations occur.

---

### app/core/webhooks.py

Webhook delivery system for external event notification.

**Purpose**: Send events to registered webhook URLs when significant actions occur.

 Delivery**:

The**Webhook module provides functions to:
- Register webhook URLs with the application
- Queue webhook delivery tasks
- Handle delivery retries and failures

Webhooks are delivered asynchronously via Celery to avoid blocking API responses. The system tracks delivery status and can retry failed deliveries.

---

### app/core/middleware/

This directory contains custom middleware components that modify request/response processing.

#### rate_limit.py

Rate limiting implementation with support for different limits per endpoint category.

**Purpose**: Protect the API from abuse by limiting request rates per user or IP address.

**Implementation**:

The middleware supports multiple rate limiting strategies:
- Per-IP limiting for anonymous requests
- Per-user limiting for authenticated requests
- Custom rules for specific endpoint categories

The implementation uses a sliding window algorithm with either Redis (production) or in-memory (development) storage. Redis-backed limiting works across multiple API instances.

**Configuration**:

Rate limits are configured in settings with different limits for:
- General API endpoints: 100 requests/minute
- Authentication endpoints: 60 requests/minute (stricter to prevent brute force)
- File uploads: 100 requests/hour (expensive operation)

#### security_headers.py

Adds HTTP security headers to all responses.

**Purpose**: Implement defense-in-depth by adding security headers that protect against common web vulnerabilities.

**Headers Added**:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000 (in production)
- Content-Security-Policy (in production)

#### request_logging.py

Logs all incoming requests and outgoing responses.

**Purpose**: Provide audit trail and debugging information for API operations.

The middleware logs request method, path, query parameters, and user information when available. Response status codes and timing information are logged on completion.

#### response_envelope.py

Wraps all API responses in a consistent envelope format.

**Purpose**: Ensure consistent response structure across all endpoints.

**Envelope Format**:
```json
{
  "success": true,
  "message": "Success",
  "data": { ... },
  "meta": { ... }
}
```

This allows clients to handle responses uniformly and provides space for metadata like pagination info.

---

## Module Structure

### app/modules/__init__.py

Empty file marking the modules directory as a Python package.

---

### app/modules/auth/

Authentication module handling user registration, login, and session management.

#### models.py

**RefreshToken**: Model for storing refresh tokens.

The model includes:
- id: Primary key UUID
- user_id: Foreign key to user
- token: The actual refresh token value
- expires_at: Expiration timestamp
- created_at: Creation timestamp
- revoked: Boolean flag for manual revocation
- revoked_at: Revocation timestamp

The user relationship enables cascade deletion when users are removed.

#### schemas.py

Pydantic schemas for authentication request and response validation.

**UserRegistration**: Email (validated), password (with strength requirements), full name. All fields have appropriate validators for format and length.

**LoginRequest**: Email and password for authentication.

**TokenResponse**: Access token, refresh token, token type (Bearer), and expiration times.

**MFAEnableRequest**: Validates TOTP code when enabling MFA.

**MFALoginRequest**: Contains login credentials and MFA code.

**MFAChallengeResponse**: Returns MFA challenge status and required information.

#### service.py

**AuthService**: Core authentication logic.

**Registration**: Creates new user with hashed password, optional email verification token generation.

**Login**: Validates credentials, checks MFA status, creates tokens. Returns different responses based on MFA requirement.

**Token Refresh**: Validates refresh token, creates new access token. Handles token rotation for security.

**Logout**: Blacklists the access token to prevent further use.

**MFA Management**: Enables/disables MFA with TOTP validation. Generates secret for authenticator app setup.

The service implements comprehensive security measures including rate limiting integration and token blacklisting.

#### router.py

API routes for authentication endpoints.

**POST /auth/register**: Create new user account.
**POST /auth/login**: Authenticate and receive tokens.
**POST /auth/refresh**: Exchange refresh token for new access token.
**POST /auth/logout**: Invalidate current session.
**POST /auth/mfa/enable**: Enable MFA for account.
**POST /auth/mfa/disable**: Disable MFA for account.
**POST /auth/mfa/login**: Verify MFA code during login.

---

### app/modules/users/

User management module handling profiles and account settings.

#### models.py

**User**: Core user model with comprehensive fields.

Fields include:
- id: UUID primary key
- email: Unique, indexed email address
- password_hash: Bcrypt hashed password
- full_name: User's display name
- role: admin/instructor/student with check constraint
- is_active: Account status
- mfa_enabled: MFA configuration
- metadata: JSON field for profile data
- created_at, updated_at: Timestamps with automatic management
- last_login_at: Track login activity
- email_verified_at: Email verification status

Relationships:
- refresh_tokens: One-to-many with refresh tokens
- courses: One-to-many with created courses (for instructors)
- enrollments: One-to-many with enrollments (for students)

#### schemas.py

Pydantic schemas for user operations.

**UserCreate**: For admin user creation.
**UserResponse**: Public user data (excludes password hash).
**UserUpdate**: Fields that users can update themselves.
**PasswordChangeRequest**: Current and new password with validation.

#### repositories/user_repository.py

**UserRepository**: Data access layer for users.

Methods:
- create(): Insert new user
- get_by_id(): Find by UUID
- get_by_email(): Find by email address
- update(): Modify user fields
- delete(): Remove user

#### services/user_service.py

**UserService**: Business logic for user management.

Methods:
- get_current_profile(): Retrieve authenticated user's profile
- update_profile(): Modify own profile
- change_password(): Update password with verification
- get_by_id(): Admin user lookup

#### router.py

User profile endpoints.

**GET /users/me**: Retrieve current user's profile.
**PATCH /users/me**: Update current user's profile.
**POST /users/me/password**: Change password.

---

### app/modules/courses/

Course management module with full CRUD and lesson content.

#### models/course.py

**Course**: Course entity with rich metadata.

Fields:
- id: UUID primary key
- title, slug: Course identification (slug is URL-friendly)
- description: Course overview
- instructor_id: Foreign key to user (restrict delete)
- category: Course category for filtering
- difficulty_level: beginner/intermediate/advanced
- is_published: Draft/published status
- thumbnail_url: Cover image
- estimated_duration_minutes: Duration estimate
- metadata: JSON for extensibility
- timestamps

Indexes on:
- slug (unique)
- instructor_id + created_at
- is_published + created_at
- category, difficulty_level

Relationships:
- instructor: User relationship
- lessons: Cascade delete with lessons
- enrollments: Cascade delete with enrollments
- quizzes: Cascade delete with quizzes

#### models/lesson.py

**Lesson**: Individual lesson within a course.

Fields:
- id: UUID primary key
- course_id: Foreign key to course (cascade delete)
- title, content: Lesson content
- content_type: video/text/document
- video_url: Video hosting URL
- duration_minutes: Length estimate
- order: Position in course
- metadata: JSON extensibility
- timestamps

Indexes on course_id + order for efficient lesson ordering.

#### schemas/course.py

Course Pydantic schemas.

**CourseCreate**: title, description, category, difficulty, metadata. Requires slug or generates from title.

**CourseUpdate**: Partial update fields.

**CourseResponse**: Full course data for API responses.

**CourseListResponse**: Paginated course list with metadata.

#### schemas/lesson.py

Lesson Pydantic schemas with content type support.

#### repositories/course_repository.py

**CourseRepository**: Data access for courses.

Methods include filtering by category, difficulty, published status, instructor. Supports pagination and ordering.

#### repositories/lesson_repository.py

**LessonRepository**: Data access for lessons.

Methods for course-scoped lesson retrieval with ordering.

#### services/course_service.py

**CourseService**: Business logic for courses.

- create_course(): Validate permissions, generate unique slug
- get_course(): Retrieve with authorization check
- list_courses(): Filtering and pagination
- update_course(): Modify with permission check
- publish_course(): Change published status
- delete_course(): Remove with cascade handling

#### services/lesson_service.py

**LessonService**: Business logic for lessons.

- create_lesson(): Add to course
- update_lesson(): Modify with permission
- reorder_lessons(): Change lesson order
- delete_lesson(): Remove from course

#### routers/course_router.py

Course endpoints.

**GET /courses**: List with filtering and pagination.
**POST /courses**: Create (instructor/admin).
**GET /courses/{id}**: Retrieve single course.
**PATCH /courses/{id}**: Update (owner/admin).
**POST /courses/{id}/publish**: Publish (owner/admin).
**DELETE /courses/{id}**: Delete (owner/admin).

#### routers/lesson_router.py

Lesson endpoints.

**GET /courses/{id}/lessons**: List lessons.
**POST /courses/{id}/lessons**: Create (owner/admin).
**GET /lessons/{id}**: Retrieve.
**PATCH /lessons/{id}**: Update.
**DELETE /lessons/{id}**: Delete.
**PATCH /lessons/reorder**: Change order.

---

### app/modules/enrollments/

Student enrollment and progress tracking module.

#### models.py

**Enrollment**: Student-course relationship.

Fields:
- id: UUID primary key
- student_id: Foreign key to user
- course_id: Foreign key to course
- enrolled_at: Enrollment timestamp
- completed_at: Completion timestamp
- timestamps

Unique constraint on student + course to prevent duplicate enrollments.

Indexes on student_id, course_id for efficient lookups.

**LessonProgress**: Per-lesson progress tracking.

Fields:
- id: UUID primary key
- enrollment_id: Foreign key to enrollment
- lesson_id: Foreign key to lesson
- completed: Boolean completion status
- completed_at: Completion timestamp
- timestamps

Unique constraint prevents duplicate progress records.

#### schemas.py

**EnrollmentCreate**: Course ID for enrollment.
**EnrollmentResponse**: Full enrollment data with course info.
**EnrollmentListResponse**: Paginated list.
**LessonProgressUpdate**: Mark lesson complete.

#### repository.py

**EnrollmentRepository**: Data access.

Methods for finding enrollments by student, course, checking existing enrollments.

#### service.py

**EnrollmentService**: Business logic.

- enroll_student(): Create enrollment with progress records
- get_enrollments(): Student's courses
- complete_lesson(): Update progress, check completion
- calculate_completion(): Percentage of completed lessons
- check_enrolled(): Verify enrollment status

#### router.py

Enrollment endpoints.

**POST /enrollments**: Enroll in course.
**GET /enrollments/my-courses**: Student's enrollments.
**GET /enrollments/{id}**: Single enrollment.
**POST /enrollments/{id}/lessons/{lesson_id}/complete**: Mark complete.

---

### app/modules/quizzes/

Assessment system with questions, quizzes, and attempts.

#### models/quiz.py

**Quiz**: Quiz configuration.

Fields:
- id: UUID primary key
- course_id, lesson_id: Optional associations
- title, description: Quiz info
- time_limit_minutes: Optional time limit
- passing_score_percentage: Required score
- shuffle_questions: Randomize order
- is_published: Availability
- metadata: Extensibility
- timestamps

#### models/question.py

**QuizQuestion**: Question entity.

Fields:
- id: UUID primary key
- quiz_id: Foreign key
- question_text: The question
- question_type: multiple_choice/true_false/short_answer
- options: JSON array of choices
- correct_answer: The answer
- points: Point value
- order: Position in quiz
- metadata: Extensibility
- timestamps

#### models/attempt.py

**QuizAttempt**: Student attempt tracking.

Fields:
- id: UUID primary key
- quiz_id: Foreign key
- student_id: Foreign key
- started_at: Attempt start
- ended_at: Completion time
- answers: JSON with responses
- score: Calculated score
- passed: Pass/fail status
- metadata: Extensibility
- timestamps

#### schemas/

Quiz, question, and attempt schemas with validation.

**QuizCreate**: title, description, time limit, passing score, shuffle option.

**QuestionCreate**: question text, type, options, correct answer, points.

**AttemptStart**: Begin attempt, validates quiz availability.

**AttemptSubmit**: Submit answers for grading.

**AttemptResponse**: Full attempt data with results.

#### repositories/

**QuizRepository**: Quiz CRUD operations.
**QuestionRepository**: Question CRUD with ordering.
**AttemptRepository**: Attempt tracking and scoring.

#### services/

**QuizService**: Quiz management.
**QuestionService**: Question management.
**AttemptService**: Attempt lifecycle, grading, time enforcement.

#### routers/

**quiz_router.py**: Quiz CRUD.
**question_router.py**: Question management within quiz.
**attempt_router.py**: Start, retrieve, submit attempts.

---

### app/modules/analytics/

Three-tier analytics for students, instructors, and administrators.

#### schemas.py

Response schemas for different analytics levels.

#### services/

**StudentAnalyticsService**: Individual progress, course completions, quiz scores.

**InstructorAnalyticsService**: Course enrollments, completion rates, student engagement.

**CourseAnalyticsService**: Detailed course metrics, lesson popularity, performance distribution.

**SystemAnalyticsService**: Platform-wide metrics, user counts, revenue.

#### router.py

Analytics endpoints with role-based access.

**GET /analytics/student**: Personal analytics.
**GET /analytics/instructor**: Instructor's courses analytics.
**GET /analytics/courses/{id}/analytics**: Specific course analytics.
**GET /analytics/system**: Platform-wide analytics (admin only).

---

### app/modules/files/

File upload and storage with multiple backend support.

#### models.py

**File**: File metadata.

Fields:
- id: UUID primary key
- original_filename: User-facing name
- stored_filename: UUID-based storage name
- file_path: Storage location
- file_size: Bytes
- content_type: MIME type
- uploaded_by_id: Uploader
- timestamps

#### storage/base.py

**StorageBackend**: Abstract interface for storage implementations.

Defines methods:
- upload(): Save file
- download(): Retrieve file
- delete(): Remove file
- get_download_url(): Generate temporary download URL

#### storage/local.py

**LocalStorageBackend**: Filesystem storage implementation.

Stores files in configured upload directory with UUID names. Provides file:// URLs for local access.

#### storage/azure_blob.py

**AzureBlobStorageBackend**: Cloud storage implementation.

Uploads to Azure Blob Storage with container management. Generates SAS URLs for secure downloads.

#### service.py

**FileService**: Orchestrates file operations.

- upload_file(): Handle upload, store, create metadata
- get_file(): Retrieve metadata
- download_file(): Get file or generate URL
- delete_file(): Remove from storage and database

#### router.py

File endpoints.

**POST /files/upload**: Multipart file upload.
**GET /files**: List uploads.
**GET /files/{id}**: Get metadata.
**GET /files/{id}/download**: Download file.
**DELETE /files/{id}**: Delete file.

---

### app/modules/certificates/

PDF certificate generation for course completions.

#### models.py

**Certificate**: Completion certificate.

Fields:
- id: UUID primary key
- enrollment_id: Link to completed course
- certificate_number: Unique identifier
- issued_at: Issue date
- pdf_path: File location
- timestamps

#### schemas.py

**CertificateGenerateRequest**: Course or enrollment reference.
**CertificateResponse**: Full certificate data.

#### service.py

**CertificateService**: Certificate generation logic.

- generate_certificate(): Creates PDF, saves, updates enrollment
- get_certificate(): Retrieve certificate
- verify_certificate(): Validate by certificate number

PDF generation uses FPDF2 to create formatted certificates with:
- Course name
- Student name
- Instructor name
- Completion date
- Unique certificate number

#### router.py

Certificate endpoints.

**POST /certificates/generate**: Create certificate.
**GET /certificates/{id}**: Get certificate.
**GET /certificates/{id}/download**: Download PDF.
**GET /certificates/my-certificates**: List certificates.

---

## Background Tasks

### app/tasks/celery_app.py

Celery application configuration. Defines the Celery instance, broker, result backend, and task serialization.

---

### app/tasks/dispatcher.py

Task dispatching utilities for queuing background jobs from API endpoints.

---

### app/tasks/email_tasks.py

Email sending tasks:

- send_welcome_email(): New user welcome
- send_password_reset_email(): Password reset link
- send_enrollment_confirmation(): Enrollment notification
- send_course_completion_email(): Completion notification

---

### app/tasks/certificate_tasks.py

- generate_certificate_async(): Async PDF generation

---

### app/tasks/progress_tasks.py

- update_enrollment_progress(): Recalculate completion
- update_course_statistics(): Update analytics cache

---

### app/tasks/webhook_tasks.py

- deliver_webhook(): Async webhook delivery

---

## Utility Modules

### app/utils/pagination.py

Pagination utilities for list endpoints. Creates consistent pagination response format with page numbers, total counts, and page size.

---

### app/utils/constants.py

Application constants including role names, file size limits, and configuration defaults.

---

### app/utils/validators.py

Custom validators for Pydantic models, file extension validation, URL validation, and other domain-specific validation logic.

---

## API Structure

### app/api/v1/api.py

Main API router aggregating all module routers. Includes health check endpoints and uses safe router loading to handle optional modules gracefully.

The _safe_include function attempts to load each router, logging warnings for missing modules but not failing startup unless strict mode is enabled.

---

## Database Migrations

### alembic/env.py

Alembic environment configuration connecting to the database and loading models.

---

### alembic/versions/

Migration files (0001_initial_schema.py through 0007_...) tracking database schema evolution. Each migration is atomic and can be applied or rolled back independently.

---

## Testing Infrastructure

### tests/conftest.py

Pytest fixtures and configuration including:
- Database session fixture
- TestClient fixture
- Sample user creation
- Authentication helpers

---

### tests/helpers.py

Test utility functions for common operations like creating test data and helper methods.

---

### tests/test_*.py

Individual test files for each module:
- test_auth.py: Authentication flows
- test_courses.py: Course operations
- test_quizzes.py: Quiz functionality
- test_enrollments.py: Enrollment logic
- test_analytics.py: Analytics endpoints
- test_certificates.py: Certificate generation
- test_files.py: File upload handling
- test_permissions.py: RBAC verification
- test_rate_limit_rules.py: Rate limiting
- test_response_envelope.py: Response formatting
- test_webhooks.py: Webhook delivery
- test_secrets.py: Secrets management
- test_health.py: Health checks

---

## Summary

This file-by-file documentation covers every component of the LMS Backend project. Each file serves a specific purpose within the application's architecture, following consistent patterns for organization, error handling, and security. The modular structure allows for independent development of features while maintaining coherence across the system.

The design decisions throughout the codebase prioritize:
- Security through proper authentication, authorization, and data protection
- Performance through caching, connection pooling, and async operations
- Maintainability through clear separation of concerns and consistent patterns
- Testability through dependency injection and interface-based design
- Production-readiness through monitoring, error tracking, and graceful degradation
