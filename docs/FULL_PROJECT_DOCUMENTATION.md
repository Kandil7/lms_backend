# LMS Backend - Full Project Documentation

## 1. Project Overview

This project is a production-oriented Learning Management System (LMS) backend built with FastAPI using a modular monolith architecture.

Primary capabilities:

- Authentication and authorization with role-based access.
- User management.
- Course and lesson management.
- Enrollment and progress tracking.
- Quiz authoring and grading.
- Student and instructor analytics.
- File upload/download with pluggable storage.
- Certificate generation, verification, and download.
- Background jobs with Celery.

## 2. Architecture

The codebase uses a modular monolith design:

- Shared platform layer in `app/core`.
- Vertical modules in `app/modules/*`.
- API composition in `app/api/v1/api.py`.
- Async/background tasks in `app/tasks`.

### Request Lifecycle

1. Request enters `FastAPI` app (`app/main.py`).
2. Middleware stack runs:
   - CORS
   - GZip
   - Trusted host
   - Request logging
   - Rate limiting (Redis-backed with in-memory fallback)
3. Router dispatches to module endpoint.
4. Dependencies inject auth/session context.
5. Service and repository layers execute business logic and persistence.
6. Response is returned with rate-limit headers.

## 3. Tech Stack

- Python 3.11
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Redis
- Celery
- Pydantic Settings
- JWT (`python-jose`)
- Password hashing (`passlib` + `bcrypt`)
- Pytest

## 4. Repository Structure

```text
app/
  api/
    v1/
      api.py
  core/
    config.py
    database.py
    dependencies.py
    exceptions.py
    permissions.py
    security.py
    middleware/
      rate_limit.py
      request_logging.py
  modules/
    auth/
    users/
    courses/
    enrollments/
    quizzes/
    analytics/
    files/
    certificates/
  tasks/
    celery_app.py
    email_tasks.py
    progress_tasks.py
    certificate_tasks.py
alembic/
tests/
scripts/
docs/
```

## 5. Runtime Components

Defined in `docker-compose.yml`:

- `api`: FastAPI app (Uvicorn).
- `db`: PostgreSQL 16.
- `redis`: Redis 7.
- `celery-worker`: async worker queues.
- `celery-beat`: scheduler process.

## 6. Setup and Run

### Docker (Recommended)

```bash
docker compose up -d --build
docker compose exec -T api alembic upgrade head
```

Windows helper scripts:

- PowerShell: `.\scripts\run_project.ps1`
- Batch: `scripts\run_project.bat`

### Local Python

```bash
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Useful URLs

- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/api/v1/health`

## 7. Configuration

Settings are defined in `app/core/config.py` and loaded from `.env`.

### Application

| Variable | Purpose | Example |
|---|---|---|
| `PROJECT_NAME` | API title | `LMS Backend` |
| `ENVIRONMENT` | Runtime mode | `development` |
| `API_V1_PREFIX` | API prefix | `/api/v1` |
| `DEBUG` | Debug mode | `true` |

### Database

| Variable | Purpose | Example |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy DB URL | `postgresql+psycopg2://lms:lms@localhost:5432/lms` |
| `SQLALCHEMY_ECHO` | SQL debug logging | `false` |
| `DB_POOL_SIZE` | DB pool size | `20` |
| `DB_MAX_OVERFLOW` | DB pool overflow | `40` |

### Security and Auth

| Variable | Purpose | Example |
|---|---|---|
| `SECRET_KEY` | JWT signing key | strong random string |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `30` |

### CORS and Host Validation

| Variable | Purpose | Example |
|---|---|---|
| `CORS_ORIGINS` | Allowed origins (CSV) | `http://localhost:3000,http://localhost:5173` |
| `TRUSTED_HOSTS` | Allowed hosts (CSV) | `localhost,127.0.0.1,testserver` |

### Redis, Celery, and Rate Limit

| Variable | Purpose | Example |
|---|---|---|
| `REDIS_URL` | Redis client URL | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker | `redis://localhost:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery backend | `redis://localhost:6379/2` |
| `RATE_LIMIT_USE_REDIS` | Use Redis backend | `true` |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | Max requests per minute | `100` |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate-limit window | `60` |
| `RATE_LIMIT_REDIS_PREFIX` | Redis key prefix | `ratelimit` |
| `RATE_LIMIT_EXCLUDED_PATHS` | Excluded paths (CSV) | `/,/docs,/redoc,/openapi.json,/api/v1/health` |

### File Storage

| Variable | Purpose | Example |
|---|---|---|
| `UPLOAD_DIR` | Local uploads folder | `uploads` |
| `CERTIFICATES_DIR` | Local certificates folder | `certificates` |
| `MAX_UPLOAD_MB` | Upload size limit | `100` |
| `ALLOWED_UPLOAD_EXTENSIONS` | Allowed extensions (CSV) | `mp4,avi,mov,pdf,doc,docx,jpg,jpeg,png` |
| `FILE_STORAGE_PROVIDER` | `local` or `azure` | `local` |
| `FILE_DOWNLOAD_URL_EXPIRE_SECONDS` | Signed URL TTL | `900` |

### Optional Azure Blob

`AZURE_STORAGE_CONNECTION_STRING`, `AZURE_STORAGE_ACCOUNT_NAME`, `AZURE_STORAGE_ACCOUNT_KEY`, `AZURE_STORAGE_ACCOUNT_URL`, `AZURE_STORAGE_CONTAINER_NAME`, `AZURE_STORAGE_CONTAINER_URL`

## 8. Authentication and Authorization

### Authentication

- Access and refresh JWT tokens are generated in `app/core/security.py`.
- Access token contains:
  - `sub` (user id)
  - `role`
  - `typ=access`
  - `jti`, `iat`, `exp`
- Refresh token contains:
  - `sub`
  - `typ=refresh`
  - `jti`, `iat`, `exp`

### Password Hashing

- Uses `passlib` with `bcrypt`.
- Requirement pin includes `bcrypt<5.0.0` for compatibility.

### Authorization

Defined in `app/core/permissions.py` and dependency helpers in `app/core/dependencies.py`.

Roles:

- `admin`
- `instructor`
- `student`

Permission checks are enforced through:

- `require_roles(...)`
- `require_permissions(...)`

## 9. Data Model

Current core tables:

- `users`
- `refresh_tokens`
- `courses`
- `lessons`
- `enrollments`
- `lesson_progress`
- `quizzes`
- `quiz_questions`
- `quiz_attempts`
- `uploaded_files`
- `certificates`

Main relationships:

- `courses.instructor_id -> users.id`
- `lessons.course_id -> courses.id`
- `enrollments.student_id -> users.id`
- `enrollments.course_id -> courses.id`
- `lesson_progress.enrollment_id -> enrollments.id`
- `lesson_progress.lesson_id -> lessons.id`
- `quizzes.lesson_id -> lessons.id`
- `quiz_questions.quiz_id -> quizzes.id`
- `quiz_attempts.enrollment_id -> enrollments.id`
- `quiz_attempts.quiz_id -> quizzes.id`
- `uploaded_files.uploader_id -> users.id`
- `certificates.enrollment_id -> enrollments.id`
- `certificates.student_id -> users.id`
- `certificates.course_id -> courses.id`

Migrations are managed with Alembic:

- Current baseline revision: `0001_initial_schema`

## 10. API Surface (Current Routes)

### System

- `GET /`
- `GET /api/v1/health`

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### Users

- `GET /api/v1/users`
- `POST /api/v1/users`
- `GET /api/v1/users/me`
- `GET /api/v1/users/{user_id}`
- `PATCH /api/v1/users/{user_id}`

### Courses and Lessons

- `GET /api/v1/courses`
- `POST /api/v1/courses`
- `GET /api/v1/courses/{course_id}`
- `PATCH /api/v1/courses/{course_id}`
- `DELETE /api/v1/courses/{course_id}`
- `POST /api/v1/courses/{course_id}/publish`
- `GET /api/v1/courses/{course_id}/lessons`
- `POST /api/v1/courses/{course_id}/lessons`
- `GET /api/v1/lessons/{lesson_id}`
- `PATCH /api/v1/lessons/{lesson_id}`
- `DELETE /api/v1/lessons/{lesson_id}`

### Enrollments and Progress

- `POST /api/v1/enrollments`
- `GET /api/v1/enrollments/my-courses`
- `GET /api/v1/enrollments/{enrollment_id}`
- `GET /api/v1/enrollments/courses/{course_id}`
- `GET /api/v1/enrollments/courses/{course_id}/stats`
- `PUT /api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/progress`
- `POST /api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/complete`
- `POST /api/v1/enrollments/{enrollment_id}/review`

### Quizzes

- `GET /api/v1/courses/{course_id}/quizzes`
- `POST /api/v1/courses/{course_id}/quizzes`
- `GET /api/v1/courses/{course_id}/quizzes/{quiz_id}`
- `PATCH /api/v1/courses/{course_id}/quizzes/{quiz_id}`
- `POST /api/v1/courses/{course_id}/quizzes/{quiz_id}/publish`
- `GET /api/v1/courses/{course_id}/quizzes/{quiz_id}/questions`
- `POST /api/v1/courses/{course_id}/quizzes/{quiz_id}/questions`
- `PATCH /api/v1/courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}`
- `POST /api/v1/quizzes/{quiz_id}/attempts`
- `GET /api/v1/quizzes/{quiz_id}/attempts/start`
- `GET /api/v1/quizzes/{quiz_id}/attempts/{attempt_id}`
- `POST /api/v1/quizzes/{quiz_id}/attempts/{attempt_id}/submit`
- `GET /api/v1/quizzes/{quiz_id}/attempts/my-attempts`

### Analytics

- `GET /api/v1/analytics/my-progress`
- `GET /api/v1/analytics/my-dashboard`
- `GET /api/v1/analytics/courses/{course_id}`
- `GET /api/v1/analytics/instructors/{instructor_id}/overview`
- `GET /api/v1/analytics/system/overview`

### Files

- `POST /api/v1/files/upload`
- `GET /api/v1/files/my-files`
- `GET /api/v1/files/download/{file_id}`

### Certificates

- `POST /api/v1/certificates/enrollments/{enrollment_id}/generate`
- `GET /api/v1/certificates/my-certificates`
- `GET /api/v1/certificates/{certificate_id}/download`
- `POST /api/v1/certificates/{certificate_id}/revoke`
- `GET /api/v1/certificates/verify/{certificate_number}`

## 11. Background Jobs and Queues

Celery app configuration is in `app/tasks/celery_app.py`.

Queue routing:

- `emails`: `app.tasks.email_tasks.*`
- `progress`: `app.tasks.progress_tasks.*`
- `certificates`: `app.tasks.certificate_tasks.*`

Defined task stubs:

- `app.tasks.email_tasks.send_welcome_email`
- `app.tasks.progress_tasks.recalculate_course_progress`
- `app.tasks.certificate_tasks.generate_certificate`

## 12. Files and Certificates

### File Storage

- Storage provider can be `local` or `azure`.
- Uploaded file metadata is stored in `uploaded_files`.
- Static local files are mounted by FastAPI:
  - `/uploads`
  - `/certificates-static`

### Certificates

- Certificate records are persisted in `certificates`.
- PDF generation logic is in `app/modules/certificates/service.py`.
- Public verification endpoint is available.

## 13. Testing

Run tests:

```bash
pytest -q
```

Current suite covers:

- auth
- courses
- enrollments
- quizzes
- analytics
- files
- certificates
- permission boundaries

## 14. Scripts

Located in `scripts/`:

- `create_admin.py`: create an admin account.
- `seed_demo_data.py`: seed sample data.
- `generate_postman_collection.py`: build Postman artifacts from OpenAPI.
- `run_project.ps1`: one-command startup (PowerShell).
- `run_project.bat`: one-command startup (Batch).

## 15. Branching and Commit Strategy

Recommended flow:

- `main`: stable/release branch.
- `develop`: integration branch.
- `feature/*`, `fix/*`, `chore/*`: scoped branches.

Commit conventions:

- Small, focused commits.
- Prefix by area and type:
  - `feat(...)`
  - `fix(...)`
  - `chore(...)`
  - `docs(...)`
  - `test(...)`

## 16. Operations and Troubleshooting

### Common Run Commands

```bash
docker compose up -d --build
docker compose exec -T api alembic upgrade head
docker compose ps
docker compose logs --tail=200 api
```

### Frequent Issues

- Missing `.env`: copy from `.env.example`.
- DB not initialized: run Alembic migration.
- Container-to-container URL mismatch: use service names (`db`, `redis`) inside Docker network.
- Rate-limit Redis failure in tests/runtime: middleware falls back to in-memory mode.

## 17. Production Checklist

- Set a strong `SECRET_KEY`.
- Set `DEBUG=false`.
- Restrict `CORS_ORIGINS` and `TRUSTED_HOSTS`.
- Use managed PostgreSQL/Redis.
- Configure backups and monitoring.
- Configure real Azure Blob credentials if using `FILE_STORAGE_PROVIDER=azure`.
- Run CI tests before merge.
- Keep migrations and application version in sync.
