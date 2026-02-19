# LMS Backend

Production-oriented LMS backend built as a modular monolith with FastAPI.

## Documentation
- Full technical documentation: `docs/FULL_PROJECT_DOCUMENTATION.md`
- Documentation index: `docs/README.md`
- Arabic detailed docs set: `docs/01-overview-ar.md` -> `docs/07-testing-and-quality-ar.md`
- Operations runbook: `docs/ops/01-production-runbook.md`
- Staging checklist: `docs/ops/02-staging-release-checklist.md`

## Architecture
- `app/core`: config, database, security, dependencies, middleware.
- `app/modules/*`: vertical modules with `models/schemas/repositories/services/routers`.
- `app/api/v1/api.py`: router aggregation and API prefix wiring.
- `alembic`: migrations.
- `tests`: API integration tests.

## Implemented Modules
- `auth`: registration/login/refresh/logout, refresh token revocation, forgot/reset password, email verification, optional MFA login challenge.
- `users`: profile + admin user management.
- `courses`: course and lesson CRUD with ownership checks.
- `enrollments`: enrollment lifecycle, lesson progress aggregation, reviews.
- `quizzes`: quiz/question authoring, attempts, grading.
- `analytics`: student dashboard, course analytics, instructor and system overview.
- `files`: upload/list/download with local storage backend.
- `certificates`: automatic issuance on completion, verify/download/revoke.

## Local Setup
1. Create virtualenv and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy environment template:
   ```bash
   cp .env.example .env
   ```
3. Run database migrations:
   ```bash
   alembic upgrade head
   ```
4. (Optional) create admin:
   ```bash
   python scripts/create_admin.py
   ```
5. Run API:
   ```bash
   uvicorn app.main:app --reload
   ```

Docs: `http://localhost:8000/docs`

## Docker
```bash
docker compose up --build
```

Production-like stack:
```bash
cp .env.production.example .env
docker compose -f docker-compose.prod.yml up -d --build
```

Staging stack:
```bash
cp .env.staging.example .env
docker compose -f docker-compose.staging.yml up -d --build
```

Note: `docker-compose.prod.yml` uses `PROD_*` URLs (for DB/Redis/Celery) so local dev `.env` values like `localhost` do not leak into production containers.

PowerShell one-command startup (Windows):
```powershell
.\scripts\run_project.ps1
```

Batch one-command startup (Windows):
```bat
scripts\run_project.bat
```

Demo one-command startup (Windows, includes seed + demo Postman JSON):
```bat
run_demo.bat
```

Staging one-command startup (Windows):
```bat
run_staging.bat
```

Useful flags:
- `-NoBuild`
- `-NoMigrate`
- `-CreateAdmin`
- `-SeedDemoData`
- `-FollowLogs`

Readiness endpoint:
- `http://localhost:8000/api/v1/ready`

Metrics endpoint:
- `http://localhost:8000/metrics`

Services included in `docker-compose.yml`:
- `api`
- `db`
- `redis`
- `celery-worker`
- `celery-beat`

## Tests
```bash
pytest -q
```

Coverage gate (same style as CI):
```bash
pytest -q --cov=app --cov-report=term-missing --cov-fail-under=75
```

Load test smoke baseline:
```bat
run_load_test.bat
```
Optional authenticated flow:
```bat
run_load_test.bat http://localhost:8000 20 60s localhost true
```

## Database Backup and Restore
Create a backup (Windows):
```bat
backup_db.bat
```

Restore from backup (Windows):
```bat
restore_db.bat backups\db\lms_YYYYMMDD_HHMMSS.dump --yes
```

Create a daily scheduled backup task (Windows):
```powershell
.\scripts\setup_backup_task.ps1 -TaskName LMS-DB-Backup -Time 02:00
```

## Demo Data Seed
Use this script to create demo users, one published course, lessons, enrollment, quiz, and a graded attempt.

```bash
python scripts/seed_demo_data.py
```

Options:
- `--create-tables`: create tables before seeding.
- `--reset-passwords`: reset passwords for existing demo users.
- `--skip-attempt`: skip creating/submitting demo quiz attempt.
- `--json-output <path>`: write a seed snapshot JSON for Postman demo generation.

Default demo credentials:
- `admin@lms.local / AdminPass123`
- `instructor@lms.local / InstructorPass123`
- `student@lms.local / StudentPass123`

## Postman Collection
Generate Postman artifacts from OpenAPI:

```bash
python scripts/generate_postman_collection.py
```

Generated files:
- `postman/LMS Backend.postman_collection.json`
- `postman/LMS Backend.postman_environment.json`

Generate demo Postman artifacts from seeded data snapshot:

```bash
python scripts/generate_demo_postman.py --seed-file postman/demo_seed_snapshot.json
```

Generated demo files:
- `postman/LMS Backend Demo.postman_collection.json`
- `postman/LMS Backend Demo.postman_environment.json`
- `postman/demo_seed_snapshot.json`

## Production Hardening
- CI pipeline: `.github/workflows/ci.yml` runs compile checks, dependency checks, coverage gate, and tests on Python 3.11 and 3.12.
- Security pipeline: `.github/workflows/security.yml` runs `pip-audit` and `bandit` on push/PR and weekly schedule.
- Rate limiting supports Redis with in-memory fallback.
- File storage is pluggable (`local` or `s3`).
- API docs (`/docs`, `/redoc`, `/openapi.json`) are disabled by default in production.
- Router loading is fail-fast in production (startup fails if any router import fails).

Important environment flags:
- `RATE_LIMIT_USE_REDIS=true`
- `RATE_LIMIT_REQUESTS_PER_MINUTE=100`
- `RATE_LIMIT_WINDOW_SECONDS=60`
- `ENABLE_API_DOCS=false` in production
- `STRICT_ROUTER_IMPORTS=true` in production
- `METRICS_ENABLED=true`
- `METRICS_PATH=/metrics`
- `FILE_STORAGE_PROVIDER=local` (or `s3`)
- `FILE_DOWNLOAD_URL_EXPIRE_SECONDS=900`
- `TASKS_FORCE_INLINE=true` for local/dev, `false` for production
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `FRONTEND_BASE_URL` (used in password reset links)
- `EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES`
- `REQUIRE_EMAIL_VERIFICATION_FOR_LOGIN`
- `MFA_CHALLENGE_TOKEN_EXPIRE_MINUTES`
- `MFA_LOGIN_CODE_EXPIRE_MINUTES`
- `MFA_LOGIN_CODE_LENGTH`

## Branch Strategy
- `main`: stable releases.
- `develop`: integration branch.
- `feature/*` and `chore/*`: scoped implementation branches.
- Merge style: `--no-ff` from feature branches into `develop`, then `develop` into `main`.

## Notes
- Local uploads are served from `/uploads/*`.
- Certificate files are stored in `certificates/` and downloadable through certificate endpoints.
- First migration is provided in `alembic/versions/0001_initial_schema.py`.
