# Complete File-by-File Documentation

This document provides exhaustive documentation of every file in the LMS Backend project. Each file is explained in terms of its purpose, functionality, and how it interacts with other parts of the system. This documentation serves as a complete reference for developers working on any part of the codebase.

---

## Root Directory Configuration Files

### requirements.txt

The requirements.txt file contains all Python dependencies required by the project. This file uses version specifiers with inclusive ranges to ensure compatibility while allowing patch updates. The dependencies are organized by their primary purpose in the application.

FastAPI serves as the web framework and provides async support, automatic OpenAPI documentation, and high performance. Uvicorn is the ASGI server that runs the FastAPI application. SQLAlchemy 2.0 is the ORM for database operations, while Alembic handles database migrations. Psycopg2-binary provides PostgreSQL connectivity.

Pydantic-settings manages configuration through environment variables with type validation. Python-jose handles JWT token creation and validation, while Passlib with bcrypt provides secure password hashing. Python-multipart enables file upload handling, and email-validator validates email addresses.

Redis serves as both a cache and message broker for Celery. Prometheus-client exposes application metrics for monitoring. Sentry-sdk integrates error tracking. Celery handles asynchronous background tasks. Firebase-admin enables Firebase authentication integration. Azure-storage-blob provides cloud storage capabilities. Jinja2 templates rendering, fpdf2 generates PDF certificates, and httpx makes HTTP requests. Testing dependencies include pytest, pytest-asyncio, and pytest-cov. Python-magic detects file MIME types. HVAC interfaces with HashiCorp Vault, and Azure-identity provides Azure authentication.

### .env.example

This file provides a template for all environment variables needed by the application. It documents each configuration option with comments explaining its purpose and default values. Developers copy this file to .env and customize values for their environment. The file demonstrates the expected format for each variable and provides safe default values for development.

### .env

The actual environment configuration file (not committed to version control). Contains sensitive values like database passwords, API keys, and secret keys. Loaded by pydantic-settings at application startup. The presence of this file is required for the application to run.

### .dockerignore

This file specifies patterns for files that should not be included in Docker build context. It excludes Python cache files, test files, documentation, and other artifacts that are not needed in the production container. This reduces image size and build time.

### alembic.ini

Configuration file for Alembic database migration tool. Specifies the migration location, SQLAlchemy database URL, and various migration options. Defines the directory structure for migration scripts and configures the revision and downgrade label styles.

### README.md

The main project README providing quick start instructions, architecture overview, implemented modules, and common commands. Serves as the entry point for new developers. Contains links to detailed documentation and explains deployment options.

---

## Application Core Module (app/core/)

The core module contains infrastructure code that is shared across all application modules. This includes configuration, database connections, security utilities, middleware, and cross-cutting concerns.

### app/__init__.py

Empty init file that marks the app directory as a Python package. Enables imports from the app module.

### app/main.py

The main FastAPI application entry point. This file initializes and configures the FastAPI application with all middleware, routers, and lifecycle management. It imports all core modules, sets up CORS middleware, adds security headers, configures rate limiting, registers exception handlers, and includes all API routers.

The application uses a lifespan context manager to handle startup and shutdown events. On startup, it creates necessary directories for uploads and certificates. The middleware stack is configured in a specific order: CORS first, then GZip, TrustedHosts, SecurityHeaders, RequestLogging, Metrics, ResponseEnvelope, and finally RateLimiting.

Rate limiting is configured with different rules for authentication endpoints versus general endpoints. Auth endpoints have stricter limits (60 requests per minute) while general endpoints allow 100 requests per minute. The configuration supports Redis-backed rate limiting with in-memory fallback for development.

### app/core/__init__.py

Empty init file for the core module. Exports commonly used functions and classes for convenient importing throughout the application.

### app/core/config.py

The central configuration management file using Pydantic-settings. Defines all configuration options with type validation, default values, and documentation. The Settings class includes validators for list fields like CORS_ORIGINS and TRUSTED_HOSTS.

Key configuration sections include application settings (name, version, environment), API settings (prefix, docs enabled), database settings (URL, pool size), security settings (JWT secret, token expiration), email settings (SMTP configuration), Firebase settings, Azure storage settings, caching settings, rate limiting settings, and file upload settings.

The configuration implements property methods for computed values like MAX_UPLOAD_BYTES (calculated from MAX_UPLOAD_MB) and API_DOCS_EFFECTIVE_ENABLED (which disables docs in production regardless of other settings).

Production validation ensures that SECRET_KEY is sufficiently long, DEBUG is false, and various security settings are properly configured. The file also initializes secrets management for production environments, loading sensitive values from Azure Key Vault or HashiCorp Vault.

### app/core/database.py

Database connection and session management. Creates SQLAlchemy engine with appropriate configuration for PostgreSQL or SQLite. Implements connection pooling with configurable pool size and max overflow. Provides the get_db generator function for dependency injection in FastAPI routes, and a session_scope context manager for manual session handling.

The check_database_health function verifies database connectivity for health checks. The Base class serves as the declarative base for all ORM models.

### app/core/security.py

Security utilities including password hashing, JWT token creation and validation, and token blacklist management. Uses bcrypt through passlib for password hashing. Implements multiple token types: access tokens (short-lived, 15 minutes), refresh tokens (long-lived, 30 days), password reset tokens, email verification tokens, and MFA challenge tokens.

The AccessTokenBlacklist class manages revoked access tokens using Redis with in-memory fallback. In production with fail-closed mode enabled, if Redis is unavailable, the system will reject all requests rather than allowing potentially revoked tokens.

Token creation includes jti (JWT ID), typ (token type), iat (issued at), and exp (expiration) claims. The decode_token function validates token signature, type, and blacklist status.

### app/core/dependencies.py

FastAPI dependency functions used throughout the application. Provides get_current_user dependency that extracts and validates JWT tokens from requests. Implements role-based access control through the require_role dependency. These dependencies are injected into route handlers to provide authenticated user context.

### app/core/exceptions.py

Custom exception classes and global exception handlers. Defines HTTPException subclasses for common error scenarios: UnauthorizedException, ForbiddenException, NotFoundException, ValidationException, and ConflictException. Registers global exception handlers that return consistent error responses with appropriate HTTP status codes.

### app/core/permissions.py

Role-based permission system. Defines permission constants and role hierarchies. The check_permission function evaluates whether a user role has access to a specific resource or action. Used by route handlers to enforce authorization rules.

### app/core/dependencies.py (Additional)

Beyond authentication, this file provides caching dependencies, pagination helpers, and database session management. The cache dependency provides Redis-backed caching with configurable TTL.

### app/core/middleware/__init__.py

Middleware module exports. Provides convenient imports for all custom middleware classes: RateLimitMiddleware, RequestLoggingMiddleware, ResponseEnvelopeMiddleware, SecurityHeadersMiddleware.

### app/core/middleware/security_headers.py

HTTP security headers middleware. Adds recommended security headers to all responses: X-Content-Type-Options (prevents MIME type sniffing), X-Frame-Options (prevents clickjacking), X-XSS-Protection (XSS filter), Referrer-Policy (controls referrer information), and Strict-Transport-Security (enforces HTTPS).

### app/core/middleware/rate_limit.py

Rate limiting middleware using token bucket algorithm. Supports both in-memory and Redis-backed storage. Allows configurable per-path rate limit rules with different limits for authentication endpoints and file uploads. Implements user-based or IP-based rate limiting keys.

The RateLimitRule class defines custom rules for specific path prefixes. The middleware tracks request counts and returns 429 Too Many Requests when limits are exceeded.

### app/core/middleware/request_logging.py

Request/response logging middleware. Logs all incoming requests with method, path, client IP, and user agent. Logs response status codes and execution times. Provides structured logging for request tracing in production environments.

### app/core/middleware/response_envelope.py

Response envelope middleware that wraps all API responses in a consistent format. Adds metadata like success status, message, and timestamp to responses. Can be disabled for specific paths like health checks and documentation endpoints.

### app/core/cache.py

Redis caching utilities. Provides cache_get, cache_set, and cache_delete functions. Implements cache key generation with prefix support. Used by various modules for caching frequently accessed data like course details and quiz questions.

### app/core/metrics.py

Prometheus metrics integration. Defines custom metrics for request counts, response times, and active users. Provides MetricsMiddleware that tracks request metrics. Includes a metrics endpoint router that serves Prometheus-formatted metrics.

### app/core/observability.py

Sentry error tracking initialization. Configures Sentry based on environment settings. Provides separate configuration for API and Celery workers. Supports sampling rates for traces and profiles. Masks sensitive data to protect user privacy.

### app/core/health.py

Health check implementations. check_redis_health verifies Redis connectivity. Used by the readiness endpoint to determine if all dependencies are available. The /api/v1/health endpoint provides basic status, while /api/v1/ready provides detailed dependency status.

### app/core/cookie_utils.py

Cookie manipulation utilities for authentication. Handles secure cookie creation with appropriate attributes (HttpOnly, Secure, SameSite). Supports cookie signing and verification for session management. Used by the cookie-based authentication router in production.

### app/core/account_lockout.py

Account lockout functionality for failed login attempts. Tracks failed login attempts per user and locks accounts after configurable threshold (default 5 attempts). Implements exponential backoff for repeated failures. Uses Redis for distributed lockout state.

### app/core/model_registry.py

Model loading system that ensures all SQLAlchemy models are imported before database operations. load_all_models function imports all model modules, which triggers model registration with SQLAlchemy's metadata. Called at application startup before any database operations.

### app/core/firebase.py

Firebase authentication integration. Initializes Firebase Admin SDK when enabled. Provides token verification for Firebase-authenticated users. Allows Firebase as an alternative authentication method.

### app/core/secrets.py

Secrets management interface. Provides get_secret and initialize_secrets_manager functions. Supports multiple backends: Azure Key Vault (production preferred), HashiCorp Vault, and environment variables (development fallback). Centralizes sensitive value retrieval for production deployments.

### app/core/webhooks.py

Webhook delivery system. Sends event notifications to registered webhook URLs. Signs payloads with HMAC-SHA256 for verification. Implements retry logic with exponential backoff. Supports multiple webhook targets with individual configuration.

---

## Authentication Module (app/modules/auth/)

The authentication module handles all authentication-related functionality including registration, login, logout, token refresh, password reset, email verification, and optional MFA.

### app/modules/auth/__init__.py

Empty init file for the auth module.

### app/modules/auth/models.py

SQLAlchemy models for authentication. Defines User model with authentication-related fields: email, password_hash, role, is_active, email_verified_at, mfa_secret, failed_login_attempts, locked_until. Includes password reset and email verification token models.

### app/modules/auth/schemas.py

Pydantic schemas for authentication request and response validation. Defines UserCreate, UserLogin, TokenResponse, PasswordResetRequest, PasswordResetConfirm, EmailVerificationRequest, and related schemas. Includes validation for email format, password strength, and token formats.

### app/modules/auth/schemas_cookie.py

Cookie-based authentication schemas. Extends base schemas with cookie-specific options. Used in production environment for enhanced security through HTTP-only cookies rather than client-side token storage.

### app/modules/auth/service.py

Authentication business logic. Implements user registration, login validation, token generation, password reset workflow, email verification, and MFA challenge generation. Contains core authentication logic separate from HTTP handling.

### app/modules/auth/service_cookie.py

Cookie-based authentication service. Extends base service with cookie creation and management. Handles secure cookie lifecycle including creation, refreshing, and deletion. Used in production for improved security.

### app/modules/auth/router.py

FastAPI routes for authentication (token-based). Exposes endpoints for registration, login, logout, token refresh, password reset, and email verification. Uses bearer token authentication. Development-appropriate implementation.

### app/modules/auth/router_cookie.py

FastAPI routes for authentication (cookie-based). Production version that uses HTTP-only cookies instead of bearer tokens. Provides same functionality as base router but with enhanced security through cookie-only transport.

---

## Users Module (app/modules/users/)

The users module manages user profiles and administrative user management functionality.

### app/modules/users/__init__.py

Empty init file for the users module.

### app/modules/users/models.py

SQLAlchemy User model with profile fields. Extends authentication User with full_name, avatar_url, bio, created_at, updated_at. Provides profile information for all user types (admin, instructor, student).

### app/modules/users/schemas.py

Pydantic schemas for user profiles. UserResponse, UserUpdate, UserListResponse schemas for API validation. Admin schemas for user management including role changes and account activation/deactivation.

### app/modules/users/router.py

FastAPI routes for user profile management and admin functionality. Profile endpoints allow users to view and update their own profiles. Admin endpoints provide user listing, creation, update, and deletion with authorization checks.

### app/modules/users/repositories/__init__.py

Empty init file for repositories package.

### app/modules/users/repositories/user_repository.py

Data access layer for User operations. Provides CRUD operations: get_by_email, get_by_id, create, update, delete. Implements pagination for user listing. Handles soft delete and user search functionality.

---

## Courses Module (app/modules/courses/)

The courses module handles course and lesson management, the core content functionality of the LMS.

### app/modules/courses/__init__.py

Empty init file for the courses module.

### app/modules/courses/models.py

SQLAlchemy models for Course and Lesson. Course model includes title, slug, description, instructor_id, category, difficulty_level, thumbnail_url, estimated_duration_minutes, is_published. Lesson model includes course_id, title, slug, content, lesson_type (video, text, quiz), duration_minutes, order_index, video_url, is_preview.

### app/modules/courses/schemas.py

Pydantic schemas for course and lesson validation. CourseCreate, CourseUpdate, CourseResponse, LessonCreate, LessonUpdate, LessonResponse schemas. Includes validation for slug format, content types, and ordering.

### app/modules/courses/repositories/course_repository.py

Data access for Course operations. CRUD operations, get_by_slug, list_by_instructor, list_published, search functionality.

### app/modules/courses/repositories/lesson_repository.py

Data access for Lesson operations. CRUD operations, list_by_course, get_by_slug, reorder lessons within a course.

### app/modules/courses/services/course_service.py

Business logic for course operations. Create course with validation, update course ownership checks, publish/unpublish workflow, enrollment count tracking.

### app/modules/courses/services/lesson_service.py

Business logic for lesson operations. Create lesson with ordering, update with parent lesson handling, completion tracking integration.

### app/modules/courses/routers/course_router.py

FastAPI routes for course management. Public course listing, authenticated course creation, instructor course management, course detail with enrollment status.

### app/modules/courses/routers/lesson_router.py

FastAPI routes for lesson management. Course lesson listing, lesson detail, lesson creation and update by instructors, lesson content delivery.

---

## Enrollments Module (app/modules/enrollments/)

The enrollments module tracks student enrollment in courses and lesson progress.

### app/modules/enrollments/__init__.py

Empty init file for the enrollments module.

### app/modules/enrollments/models.py

SQLAlchemy Enrollment model. Links students to courses with status tracking (active, completed, dropped). Tracks enrollment date, completion date, overall progress percentage. Includes review and rating fields.

### app/modules/enrollments/schemas.py

Pydantic schemas for enrollment validation. EnrollmentCreate, EnrollmentResponse, EnrollmentUpdate schemas. Progress tracking schemas.

### app/modules/enrollments/repository.py

Data access for Enrollment operations. CRUD, get_by_student, get_by_course, get_by_student_and_course, list_enrolled_courses.

### app/modules/enrollments/service.py

Business logic for enrollment management. Student enrollment, automatic progress calculation, lesson completion marking, course completion detection, certificate eligibility checking.

### app/modules/enrollments/router.py

FastAPI routes for enrollment operations. Student enrollment in courses, progress tracking, completion status, course reviews and ratings.

---

## Quizzes Module (app/modules/quizzes/)

The quizzes module handles quiz creation, question management, attempt tracking, and automatic grading.

### app/modules/quizzes/__init__.py

Empty init file for the quizzes module.

### app/modules/quizzes/models/__init__.py

Empty init file for models package.

### app/modules/quizzes/models/quiz.py

SQLAlchemy Quiz model. Links to lesson, includes title, description, quiz_type (practice, graded), passing_score, time_limit_minutes, max_attempts, shuffle_questions, shuffle_options, show_correct_answers, is_published.

### app/modules/quizzes/models/question.py

SQLAlchemy Question model. Links to quiz with question_text, question_type (multiple_choice, true_false, short_answer), points, options (JSON), correct_answer (for short_answer), explanation, order_index.

### app/modules/quizzes/models/attempt.py

SQLAlchemy Attempt model. Links to enrollment and quiz, tracks status (in_progress, submitted, graded), score, started_at, submitted_at, graded_at, answers (JSON).

### app/modules/quizzes/schemas/__init__.py

Empty init file for schemas package.

### app/modules/quizzes/schemas/quiz.py

Pydantic schemas for Quiz validation and response. QuizCreate, QuizUpdate, QuizResponse schemas.

### app/modules/quizzes/schemas/question.py

Pydantic schemas for Question validation. QuestionCreate, QuestionUpdate, QuestionResponse, OptionSchema for multiple choice options.

### app/modules/quizzes/schemas/attempt.py

Pydantic schemas for Attempt operations. AttemptStart, AttemptSubmit, AnswerSubmission, AttemptResponse schemas.

### app/modules/quizzes/repositories/__init__.py

Empty init file for repositories package.

### app/modules/quizzes/repositories/quiz_repository.py

Data access for Quiz operations. CRUD, get_by_lesson, list_by_course, published quizzes only.

### app/modules/quizzes/repositories/question_repository.py

Data access for Question operations. CRUD, list_by_quiz, reorder questions, bulk create.

### app/modules/quizzes/repositories/attempt_repository.py

Data access for Attempt operations. CRUD, list_by_enrollment, list_by_quiz, in_progress attempts, latest attempt.

### app/modules/quizzes/services/__init__.py

Empty init file for services package.

### app/modules/quizzes/services/quiz_service.py

Business logic for Quiz management. Quiz creation with validation, question management, publishing workflow.

### app/modules/quizzes/services/question_service.py

Business logic for Question operations. Question creation with options, validation, bulk operations.

### app/modules/quizzes/services/attempt_service.py

Business logic for Attempt handling. Start attempt (create new or resume), submit attempt (calculate score, grade), time limit enforcement.

### app/modules/quizzes/routers/__init__.py

Empty init file for routers package.

### app/modules/quizzes/routers/quiz_router.py

FastAPI routes for Quiz management. Quiz CRUD by instructors, published quiz listing.

### app/modules/quizzes/routers/question_router.py

FastAPI routes for Question management. Question CRUD within quizzes by instructors.

### app/modules/quizzes/routers/attempt_router.py

FastAPI routes for Quiz attempts. Start quiz, submit answers, view results and history.

---

## Analytics Module (app/modules/analytics/)

The analytics module provides dashboards and reporting for students, instructors, and administrators.

### app/modules/analytics/__init__.py

Empty init file for the analytics module.

### app/modules/analytics/schemas.py

Pydantic schemas for analytics data. Response schemas for various analytics endpoints with proper data types for metrics.

### app/modules/analytics/router.py

FastAPI routes for analytics. Combines all analytics services into unified API endpoints with role-based access.

### app/modules/analytics/services/__init__.py

Empty init file for services package.

### app/modules/analytics/services/student_analytics_service.py

Student dashboard analytics. Enrolled courses, progress per course, completed courses, quiz scores, recent activity.

### app/modules/analytics/services/instructor_analytics_service.py

Instructor analytics. Course enrollment counts, completion rates, average scores, student activity, revenue (if applicable).

### app/modules/analytics/services/course_analytics_service.py

Course-specific analytics. Enrollment trends, lesson completion rates, quiz performance, drop-off points, ratings and reviews.

### app/modules/analytics/services/system_analytics_service.py

System-wide analytics for administrators. Total users, active users, course counts, enrollment counts, system health metrics.

---

## Files Module (app/modules/files/)

The files module handles file uploads, storage, and delivery for course materials.

### app/modules/files/__init__.py

Empty init file for the files module.

### app/modules/files/models.py

SQLAlchemy File model. Tracks uploaded files with original_filename, stored_filename, file_path, file_size, mime_type, uploaded_by_id, course_id (optional), created_at.

### app/modules/files/schemas.py

Pydantic schemas for file operations. FileUploadResponse, FileListResponse schemas.

### app/modules/files/router.py

FastAPI routes for file operations. Upload endpoint with size and type validation, list files, download files, delete files. Supports both local storage and Azure Blob storage backends.

---

## Certificates Module (app/modules/certificates/)

The certificates module handles automatic certificate generation upon course completion.

### app/modules/certificates/__init__.py

Empty init file for the certificates module.

### app/modules/certificates/models.py

SQLAlchemy Certificate model. Links to enrollment with certificate_number (unique), pdf_path, issued_at, is_revoked, revoked_at, revoked_reason.

### app/modules/certificates/schemas.py

Pydantic schemas for certificate operations. CertificateResponse, CertificateVerify schema.

### app/modules/certificates/service.py

Certificate business logic. Check eligibility (course completed with passing grade), generate certificate PDF, issue certificate with unique number, verify certificate validity, revoke certificate.

### app/modules/certificates/router.py

FastAPI routes for certificates. Download certificate PDF, verify certificate by number, list student certificates.

---

## Assignments Module (app/modules/assignments/)

The assignments module handles student assignments and grading by instructors.

### app/modules/assignments/__init__.py

Empty init file for the assignments module.

### app/modules/assignments/models.py

SQLAlchemy Assignment and Submission models. Assignment links to course/lesson with title, description, due_date, max_points. Submission links to assignment and student with submitted_at, content, grade, feedback, graded_at.

### app/modules/assignments/schemas.py

Pydantic schemas for assignment operations. AssignmentCreate, AssignmentUpdate, SubmissionCreate, SubmissionGrade schemas.

### app/modules/assignments/repositories.py

Data access for Assignment and Submission operations. CRUD for assignments, submission tracking.

### app/modules/assignments/services.py

Business logic for assignment operations. Assignment creation, submission handling, grading workflow.

### app/modules/assignments/routers.py

FastAPI routes for assignments. Assignment CRUD, submission upload, grading by instructors.

---

## API Module (app/api/)

The API module aggregates all route routers and provides the API prefix configuration.

### app/api/__init__.py

Empty init file for the API module.

### app/api/v1/__init__.py

Empty init file for v1 API package.

### app/api/v1/api.py

API router aggregation. Imports all module routers and includes them with appropriate prefixes. Implements health check and readiness endpoints. Provides dynamic router loading with graceful degradation for optional modules.

Uses _safe_include function that attempts to import routers and logs warnings on failure. In production with STRICT_ROUTER_IMPORTS enabled, router failures cause startup to fail rather than silently skipping.

Automatically selects cookie-based auth router for production and token-based for development.

---

## Tasks Module (app/tasks/)

The tasks module contains Celery background tasks for asynchronous processing.

### app/tasks/__init__.py

Empty init file for the tasks module.

### app/tasks/celery_app.py

Celery application configuration. Initializes Celery with broker and backend URLs. Lists task modules for worker import. Configures task routes (queues for emails, progress, certificates, webhooks). Sets worker options like prefetch multiplier, task acknowledgment, and time limits.

### app/tasks/dispatcher.py

Task dispatching utilities. Provides functions to queue various task types with appropriate parameters. Handles retry logic and error handling for task dispatch.

### app/tasks/email_tasks.py

Email sending tasks. Celery tasks for sending welcome emails, password reset emails, enrollment notifications, course completion certificates. Uses SMTP configuration or Firebase Cloud Functions as delivery backend.

### app/tasks/progress_tasks.py

Progress tracking tasks. Celery tasks for updating enrollment progress after lesson completion, calculating course completion percentages, triggering certificate generation on completion.

### app/tasks/certificate_tasks.py

Certificate generation tasks. Celery task for PDF certificate generation with course details and student name. Queued after course completion detection.

### app/tasks/webhook_tasks.py

Webhook delivery tasks. Celery task for delivering event webhooks to registered endpoints. Includes signature verification and retry logic.

---

## Utils Module (app/utils/)

Utility functions and helper code used throughout the application.

### app/utils/__init__.py

Empty init file for utils module.

### app/utils/constants.py

Application constants. Role constants (ADMIN, INSTRUCTOR, STUDENT), lesson type constants, quiz type constants, enrollment status constants, attempt status constants. Used throughout the application for type safety and maintainability.

### app/utils/pagination.py

Pagination utilities. Paginator class for database query pagination. Returns page number, page size, total items, total pages, and items list. Used by list endpoints for consistent pagination response format.

### app/utils/validators.py

Validation utilities. Email validation, URL validation, password strength validation. Custom validators for specific business rules.

### app/utils/mime_utils.py

MIME type utilities. Maps file extensions to MIME types, validates allowed file types for uploads. Integrates with python-magic for actual file type detection.

---

## Alembic Migrations (alembic/)

Database migration management using Alembic.

### alembic/env.py

Alembic migration environment configuration. Sets up SQLAlchemy engine and metadata for migration context. Configures Python path for model imports. Implements run_migrations_offline and run_migrations_online functions.

### alembic/script.py.mako

Template for Alembic migration scripts. Defines standard migration structure with upgrade and downgrade functions.

### alembic/versions/0001_initial_schema.py

Initial database schema migration. Creates all core tables: users, courses, lessons, enrollments, quizzes, questions, attempts, certificates, files, assignments, submissions. Adds indexes for performance. Sets up foreign key constraints.

---

## Tests (tests/)

Comprehensive test suite for the application.

### tests/conftest.py

Pytest configuration and fixtures. Database session fixture, test client fixture, test user fixtures (admin, instructor, student). Provides reusable test data for all test modules.

### tests/helpers.py

Test helper functions. Utility functions for creating test data, authenticating test requests, asserting response formats.

### tests/test_auth.py

Authentication endpoint tests. Tests for registration, login, logout, token refresh, password reset, email verification.

### tests/test_courses.py

Course endpoint tests. Tests for course CRUD, enrollment, lesson completion.

### tests/test_quizzes.py

Quiz endpoint tests. Tests for quiz creation, question management, attempt handling, grading.

### tests/test_certificates.py

Certificate endpoint tests. Tests for certificate generation, download, verification.

### tests/test_analytics.py

Analytics endpoint tests. Tests for student, instructor, and admin analytics.

### tests/test_assignments.py

Assignment endpoint tests. Tests for assignment CRUD, submission, grading.

### tests/test_assignments_grading.py

Assignment grading tests. Instructor grading workflow tests.

### tests/test_config.py

Configuration tests. Environment variable validation, production settings validation.

### tests/test_auth_cookie_router.py

Cookie-based auth router tests. Tests for production authentication flow.

### tests/perf/k6_smoke.js

K6 load test smoke test. Basic endpoint availability testing with low load.

### tests/perf/k6_realistic.js

K6 load test realistic scenario. Simulates realistic user behavior with authentication, course browsing, quiz taking.

---

## Scripts (scripts/)

Utility scripts for development, deployment, and operations.

### scripts/wait_for_db.py

Database connection wait script. Attempts database connection with exponential backoff until success or timeout. Used by Docker compose to ensure database is ready before migrations.

### scripts/validate_environment.py

Environment validation script. Checks required environment variables, validates configuration, reports missing or invalid settings. Used in CI/CD pipelines and deployment.

### scripts/validate_env.sh

Bash environment validation. Shell script version of validate_environment for Unix systems.

### scripts/test_smtp_connection.py

SMTP connectivity test. Tests email sending capability, reports connection errors. Useful for debugging email configuration.

### scripts/test_firebase_integration.py

Firebase integration test. Tests Firebase SDK initialization and token verification. Used when Firebase authentication is enabled.

### scripts/seed_demo_data.py

Demo data seeding script. Creates demo users (admin, instructor, student), sample course with lessons, enrollment, quiz with questions, graded attempt, and certificate. Generates JSON snapshot for Postman demo collection.

### scripts/create_admin.py

Admin user creation script. Creates admin user with specified email and password. Simplest way to bootstrap admin access.

### scripts/create_instructor.py

Instructor user creation script. Creates instructor user with customizable email, password, and name. Supports updating existing users.

### scripts/create_user.py

Generic user creation script. Creates users of any role with full customization. Supports update-existing flag.

### scripts/generate_postman_collection.py

Postman collection generator. Generates Postman collection and environment from OpenAPI specification. Creates importable JSON files for API testing.

### scripts/generate_full_api_documentation.py

API documentation generator. Generates comprehensive Markdown API reference from live OpenAPI schema. Creates docs/09-full-api-reference.md.

### scripts/generate_demo_postman.py

Demo Postman collection generator. Creates Postman collection with pre-populated data from seed snapshot. Generates realistic demo environment.

### scripts/deploy_azure_vm.ps1

PowerShell Azure VM deployment script. Automates Azure VM provisioning, Docker installation, application deployment. Used by GitHub Actions for Azure deployment.

### scripts/deploy_azure_vm.sh

Bash Azure VM deployment script. Unix equivalent of PowerShell deployment script.

### scripts/backup_db.bat

Windows database backup script. Creates PostgreSQL backup using pg_dump, names files with timestamp. Stores in backups/ directory.

### scripts/restore_db.bat

Windows database restore script. Restores PostgreSQL database from backup file. Supports --yes flag for non-interactive mode.

### scripts/setup_backup_task.ps1

Windows scheduled backup task setup. Creates Windows Task Scheduler task for daily backups. Configurable time and task name.

### scripts/setup_restore_drill_task.ps1

Windows restore drill task setup. Creates scheduled task for weekly restore drills. Validates backup recoverability.

### scripts/remove_backup_task.ps1

Windows backup task removal. Cleans up scheduled backup task.

### scripts/remove_restore_drill_task.ps1

Windows restore drill task removal. Cleans up scheduled restore drill task.

### scripts/run_project.ps1

PowerShell project startup script. Starts Docker compose with configurable options: -NoBuild, -NoMigrate, -CreateAdmin, -CreateInstructor, -SeedDemoData, -FollowLogs.

### scripts/run_project.bat

Batch project startup script. Windows batch equivalent of run_project.ps1.

### scripts/run_demo.bat

Demo startup script. Runs seed_demo_data after container startup for immediate demo environment.

### scripts/run_staging.bat

Staging startup script. Starts staging environment with appropriate configuration.

### scripts/run_observability.bat

Observability stack startup script. Starts Prometheus, Grafana, and Alertmanager for monitoring.

### scripts/run_load_test.bat

Load test startup script. Runs k6 smoke test against specified URL.

### scripts/run_load_test_realistic.bat

Realistic load test startup script. Runs full realistic scenario load test with multiple users.

### scripts/run_restore_drill.ps1

Restore drill execution script. Performs actual database restore from latest backup to validate recoverability.

---

## GitHub Workflows (.github/workflows/)

CI/CD pipeline definitions using GitHub Actions.

### .github/workflows/ci.yml

Continuous integration workflow. Runs on push to main, develop, feature/*, chore/* branches and pull requests. Steps include: checkout, Python setup with caching, dependency installation, static sanity checks (compileall, pip check, Postman generation), test execution with coverage gate (75% minimum). Tests run on both Python 3.11 and 3.12. Includes separate job for PostgreSQL integration tests.

### .github/workflows/security.yml

Security scanning workflow. Runs pip-audit for vulnerable dependencies, bandit for security issues, gitleaks for secret detection. Runs on push, pull request, and weekly schedule (Saturday 00:00 UTC). Fail-stop for critical issues.

### .github/workflows/deploy-azure-vm.yml

Azure VM deployment workflow. Deploys to Azure Virtual Machine on main branch push. Triggers Azure VM provisioning and application deployment. Includes environment configuration and deployment verification.

---

## Docker Compose Files

### docker-compose.yml

Development Docker compose configuration. Defines services: api (FastAPI application), db (PostgreSQL), redis (Redis), celery-worker (Celery worker), celery-beat (Celery beat scheduler). Configures volume mounts for development, environment variables for local development. Uses standard Docker networking.

### docker-compose.prod.yml

Production Docker compose configuration. Similar services but with production-appropriate settings: non-root user (nobody), health checks, restart policies, separate migrate service for database migrations. Expects external managed PostgreSQL and Redis via PROD_* environment variables. Includes Caddy reverse proxy with automatic HTTPS. TLS certificate management via Let's Encrypt.

### docker-compose.staging.yml

Staging Docker compose configuration. Intermediate environment between development and production. Uses staging-specific environment variables. Similar to production but with debug enabled for troubleshooting.

### docker-compose.observability.yml

Observability stack Docker compose. Defines Prometheus for metrics collection, Grafana for visualization, Alertmanager for alert routing. Includes Prometheus configuration with alerting rules.

---

## Ops Configuration (ops/)

Infrastructure configuration files for production operations.

### ops/caddy/Caddyfile

Caddy web server configuration. Configures reverse proxy to API service, automatic HTTPS via Let's Encrypt, security headers, gzip compression. Uses environment variables for domain and email configuration.

### ops/observability/prometheus/prometheus.yml

Prometheus configuration. Defines scrape targets for API metrics, scrape intervals, evaluation intervals.

### ops/observability/prometheus/alerts.yml

Prometheus alerting rules. Defines alert conditions for high error rate, high latency, service down.

---

## Postman (postman/)

API testing collections for Postman.

### postman/LMS Backend.postman_collection.json

Generated Postman collection from OpenAPI. Contains all API endpoints with request templates. Generated by scripts/generate_postman_collection.py.

### postman/LMS Backend.postman_environment.json

Postman environment template. Contains variable definitions for API base URL, authentication tokens. Generated by scripts/generate_postman_collection.py.

### postman/LMS Backend Demo.postman_collection.json

Demo Postman collection with seeded data. Contains pre-populated requests with actual IDs from seed data. Generated by scripts/generate_demo_postman.py.

### postman/LMS Backend Demo.postman_environment.json

Demo environment with seeded credentials. Contains authentication tokens for demo users (admin, instructor, student).

### postman/demo_seed_snapshot.json

Seed data snapshot JSON. Contains IDs and credentials for all demo data created by seed_demo_data.py. Used by generate_demo_postman.py.

### postman/LMS Backend Production.postman_collection.json

Production Postman collection. For testing production environment endpoints.

### postman/LMS Backend Production.postman_environment.json

Production environment template. Variables for production API base URL.

---

## Documentation Files (docs/)

Comprehensive documentation in multiple formats.

### docs/README.md

Documentation index with links to all documentation files. Quick navigation to specific topics.

### docs/01-overview-ar.md through docs/07-testing-and-quality-ar.md

Arabic-language documentation series. Comprehensive documentation in Arabic covering all aspects of the project.

### docs/08-api-documentation.md

API documentation overview. Introduction to API design principles and usage.

### docs/09-full-api-reference.md

Complete API reference. Generated from OpenAPI specification. Lists all endpoints, request/response schemas, authentication requirements.

### docs/legal/

Legal and compliance templates. Privacy policy, terms of service, data processing agreements.

---

## Tech Documentation (docs/tech/)

Detailed technical documentation covering all aspects of the project.

Contains multiple documentation files covering architecture, implementation, deployment, operations, testing, and more. See MASTER-COMPREHENSIVE-DOCUMENTATION.md for the complete index.

---

## Root Batch Scripts

### run_demo.bat

Convenience script for starting demo environment. Executes seed_demo_data.py after container startup.

### run_staging.bat

Convenience script for starting staging environment.

### run_observability.bat

Convenience script for starting observability stack.

### run_load_test.bat

Convenience script for running load tests.

### run_load_test_realistic.bat

Convenience script for running realistic load tests.

### restore_drill.bat

Convenience script for running restore drills.

### backup_db.bat

Convenience script for creating database backups.

### restore_db.bat

Convenience script for restoring from backups.

---

## Summary

This file-by-file documentation provides comprehensive coverage of every file in the LMS Backend project. Each file's purpose, functionality, and relationships are documented to aid understanding and maintenance of the codebase.

For more detailed information about specific areas, refer to the specialized documentation files in docs/tech/ or examine the inline code comments and docstrings.
