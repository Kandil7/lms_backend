# LMS Backend Onboarding Execution Plan

This guide is a practical, execution-first onboarding path for this repository.
It is designed so a new engineer can move from "reading code" to "shipping safe changes".

## Outcomes
- Understand architecture and request flow end-to-end.
- Understand domain modules and ownership boundaries.
- Run the app and test suite correctly.
- Implement one safe change with tests.

## Core Map
- App entrypoint: `app/main.py`
- API router aggregation: `app/api/v1/api.py`
- Core infra:
  - `app/core/config.py`
  - `app/core/database.py`
  - `app/core/dependencies.py`
  - `app/core/security.py`
  - `app/core/middleware/`
- Business modules: `app/modules/*`
- Background jobs: `app/tasks/*`
- Migrations: `alembic/versions/*`
- Tests: `tests/*`

## Day 1: Runtime + Request Path

### Goal
Know how a request moves through middleware, auth dependency, service, repository, and DB.

### Read in order
1. `app/main.py`
2. `app/api/v1/api.py`
3. `app/core/config.py`
4. `app/core/dependencies.py`
5. `app/core/middleware/rate_limit.py`
6. `app/core/exceptions.py`

### Run
```powershell
python -m pytest --version
python -m uvicorn app.main:app --reload
```

Then verify:
- `GET /api/v1/health`
- `GET /api/v1/ready`
- `GET /docs` (if docs are enabled by env)

### Checkpoint
- You can explain why `STRICT_ROUTER_IMPORTS_EFFECTIVE` changes behavior in production.
- You can explain where authentication is enforced (`get_current_user` dependency).

## Day 2: Identity and Access

### Goal
Fully understand auth, token rotation, MFA, and role/permission gates.

### Read in order
1. `app/modules/auth/router.py`
2. `app/modules/auth/service.py`
3. `app/modules/auth/models.py`
4. `app/modules/users/models.py`
5. `app/modules/users/services/user_service.py`
6. `app/core/permissions.py`

### Run focused tests
```powershell
python -m pytest tests/test_auth.py -q
```

### Checkpoint
- You can explain access + refresh token lifecycle and revocation.
- You can explain account lockout and where failures are counted.

## Day 3: Learning Journey (Courses -> Enrollment -> Quizzes/Assignments)

### Goal
Understand the primary student journey and business rules.

### Read in order
1. `app/modules/courses/models/course.py`
2. `app/modules/courses/services/course_service.py`
3. `app/modules/enrollments/service.py`
4. `app/modules/quizzes/services/attempt_service.py`
5. `app/modules/assignments/services/services.py`

### Run focused tests
```powershell
python -m pytest tests/test_courses.py tests/test_enrollments.py tests/test_quizzes.py tests/test_assignments.py -q
```

### Checkpoint
- You can explain exactly when enrollment becomes `completed`.
- You can explain quiz grading and answer masking behavior.

## Day 4: Files, Certificates, Analytics, Payments

### Goal
Understand operational modules and external integration points.

### Read in order
1. `app/modules/files/service.py`
2. `app/modules/files/storage/azure_blob.py`
3. `app/modules/certificates/service.py`
4. `app/modules/analytics/services/*`
5. `app/modules/payments/services/payment_service.py`

### Run focused tests
```powershell
python -m pytest tests/test_files.py tests/test_certificates.py tests/test_analytics.py tests/test_payment_endpoints.py -q
```

### Checkpoint
- You can explain local vs Azure file storage fallback.
- You can explain certificate issuance trigger conditions.

## Day 5: Ops, Migrations, CI, First Change

### Goal
Be able to ship a safe change with tests and migration awareness.

### Read in order
1. `alembic/env.py`
2. `alembic/versions/*`
3. `.github/workflows/ci.yml`
4. `.github/workflows/security.yml`
5. `docker-compose.yml`
6. `docker-compose.prod.yml`

### Execute first change
1. Pick one small behavior change in a single module.
2. Add/adjust tests first.
3. Implement minimal code.
4. Run target tests + smoke tests.

### Verification commands
```powershell
python -m pytest tests/test_basic_functionality.py -q
python -m pytest -q
```

## Fast Debug Playbook
- Router not loading: check `STRICT_ROUTER_IMPORTS_EFFECTIVE` + startup logs.
- Auth failures: inspect `decode_token` flow and role gates.
- 429 unexpectedly: inspect `RateLimitMiddleware` rule matching.
- Missing data: confirm repository query filters and eager loads.
- Async tasks missing: inspect `enqueue_task_with_fallback` and `TASKS_FORCE_INLINE`.

## Known Mismatch Risk Areas (Read Before Refactoring)
- `admin` and `instructors` services currently use patterns that may diverge from `UserService` signatures.
- `websocket` router is minimal/in-memory while service layer includes richer Redis-based abstractions.
- Some docs files are stale compared to implementation; code is source of truth.

## Immediate Start (Now)
Run this exact session:
```powershell
python -m uvicorn app.main:app --reload
```
Then open and inspect in order:
1. `app/main.py`
2. `app/api/v1/api.py`
3. `app/modules/auth/router.py`
4. `app/modules/auth/service.py`

After that run:
```powershell
python -m pytest tests/test_basic_functionality.py tests/test_auth.py -q
```
