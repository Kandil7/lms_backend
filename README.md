# LMS Backend

Production-oriented LMS backend built as a modular monolith with FastAPI.

## Documentation
- Full technical documentation: `docs/FULL_PROJECT_DOCUMENTATION.md`
- Documentation index: `docs/README.md`
- Arabic detailed docs set: `docs/01-overview-ar.md` -> `docs/07-testing-and-quality-ar.md`

## Architecture
- `app/core`: config, database, security, dependencies, middleware.
- `app/modules/*`: vertical modules with `models/schemas/repositories/services/routers`.
- `app/api/v1/api.py`: router aggregation and API prefix wiring.
- `alembic`: migrations.
- `tests`: API integration tests.

## Implemented Modules
- `auth`: registration/login/refresh/logout, refresh token revocation.
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

PowerShell one-command startup (Windows):
```powershell
.\scripts\run_project.ps1
```

Batch one-command startup (Windows):
```bat
scripts\run_project.bat
```

Useful flags:
- `-NoBuild`
- `-NoMigrate`
- `-CreateAdmin`
- `-SeedDemoData`
- `-FollowLogs`

## Demo Branch Quick Start
For a full running demo environment with seeded data:

```powershell
.\scripts\run_demo.ps1
```

or

```bat
scripts\run_demo.bat
```

Demo credentials:
- `admin.demo@example.com / AdminPass123`
- `instructor.demo@example.com / InstructorPass123`
- `student.demo@example.com / StudentPass123`

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

## Demo Data Seed
Use this script to create demo users, one published course, lessons, enrollment, quiz, and a graded attempt.

```bash
python scripts/seed_demo_data.py
```

Options:
- `--create-tables`: create tables before seeding.
- `--reset-passwords`: reset passwords for existing demo users.
- `--skip-attempt`: skip creating/submitting demo quiz attempt.

Default demo credentials:
- `admin.demo@example.com / AdminPass123`
- `instructor.demo@example.com / InstructorPass123`
- `student.demo@example.com / StudentPass123`

## Postman Collection
Generate Postman artifacts from OpenAPI:

```bash
python scripts/generate_postman_collection.py
```

Generated files:
- `postman/LMS Backend.postman_collection.json`
- `postman/LMS Backend.postman_environment.json`

## Production Hardening
- CI pipeline: `.github/workflows/ci.yml` runs compile checks + tests on Python 3.11 and 3.12.
- Rate limiting supports Redis with in-memory fallback.
- File storage is pluggable (`local` or `s3`).

Important environment flags:
- `RATE_LIMIT_USE_REDIS=true`
- `RATE_LIMIT_REQUESTS_PER_MINUTE=100`
- `RATE_LIMIT_WINDOW_SECONDS=60`
- `FILE_STORAGE_PROVIDER=local` (or `s3`)
- `FILE_DOWNLOAD_URL_EXPIRE_SECONDS=900`

## Branch Strategy
- `main`: stable releases.
- `develop`: integration branch.
- `feature/*` and `chore/*`: scoped implementation branches.
- Merge style: `--no-ff` from feature branches into `develop`, then `develop` into `main`.

## Notes
- Local uploads are served from `/uploads/*`.
- Certificate files are stored in `certificates/` and downloadable through certificate endpoints.
- First migration is provided in `alembic/versions/0001_initial_schema.py`.
