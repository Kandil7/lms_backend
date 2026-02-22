# LMS Backend

Production-oriented LMS backend built as a modular monolith with FastAPI.

## Live Environments
- Production base URL: `https://egylms.duckdns.org`
- Production API base: `https://egylms.duckdns.org/api/v1`
- Production readiness endpoint: `https://egylms.duckdns.org/api/v1/ready`
- Development base URL: `http://localhost:8000`
- Development API docs: `http://localhost:8000/docs`
- Production docs are disabled by default (`ENABLE_API_DOCS=false`).

## Documentation
- Full technical documentation: `docs/FULL_PROJECT_DOCUMENTATION.md`
- Documentation index: `docs/README.md`
- Arabic detailed docs set: `docs/01-overview-ar.md` -> `docs/07-testing-and-quality-ar.md`
- API reference (implementation-accurate): `docs/08-api-documentation.md`
- Operations runbook: `docs/ops/01-production-runbook.md`
- Staging checklist: `docs/ops/02-staging-release-checklist.md`
- Launch readiness tracker: `docs/ops/03-launch-readiness-tracker.md`
- UAT/Bug bash plan: `docs/ops/04-uat-and-bug-bash-plan.md`
- Observability guide: `docs/ops/05-observability-and-alerting.md`
- Security sign-off guide: `docs/ops/07-security-signoff-and-hardening.md`
- SLA/SLO and incident policy: `docs/ops/09-sla-slo-incident-support-policy.md`
- Legal/compliance templates: `docs/legal/`

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

Production stack notes:
- `docker-compose.prod.yml` expects an external managed Postgres via `PROD_DATABASE_URL` (Azure Database for PostgreSQL Flexible Server recommended).
- TLS is terminated by `caddy` on ports `80/443` using `APP_DOMAIN` + `LETSENCRYPT_EMAIL`.
- API container is internal-only on port `8000` behind Caddy reverse proxy.

Staging stack:
```bash
cp .env.staging.example .env
docker compose -f docker-compose.staging.yml up -d --build
```

Observability stack (Grafana + Prometheus + Alertmanager):
```bash
cp .env.observability.example .env.observability
docker compose -f docker-compose.observability.yml up -d
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

Observability one-command startup (Windows):
```bat
run_observability.bat
```

Useful flags:
- `-NoBuild`
- `-NoMigrate`
- `-CreateAdmin`
- `-SeedDemoData`
- `-FollowLogs`

Readiness endpoint:
- `http://localhost:8000/api/v1/ready`
- `https://egylms.duckdns.org/api/v1/ready` (current production)

Metrics endpoint:
- `http://localhost:8000/metrics`
- `https://egylms.duckdns.org/metrics` (production if exposed through Caddy)

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

Realistic sign-off scenario (student/instructor/admin):
```bat
run_load_test_realistic.bat http://localhost:8001 10m localhost 8 3 1
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

Run restore drill manually (Windows):
```bat
restore_drill.bat -ComposeFile docker-compose.prod.yml
```

Create a weekly restore drill task (Windows):
```powershell
.\scripts\setup_restore_drill_task.ps1 -TaskName LMS-DB-Restore-Drill -Time 03:30 -DaysOfWeek Sunday -ComposeFile docker-compose.prod.yml
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

## Full API Documentation
Generate a complete Markdown API reference from the live OpenAPI schema:

```bash
python scripts/generate_full_api_documentation.py
```

Generated file:
- `docs/09-full-api-reference.md`

## Production Hardening
- CI pipeline: `.github/workflows/ci.yml` runs compile checks, dependency checks, coverage gate, and tests on Python 3.11 and 3.12.
- Security pipeline: `.github/workflows/security.yml` runs `pip-audit` and `bandit` on push/PR and weekly schedule.
- Secret scanning: `security.yml` also runs `gitleaks`.
- Rate limiting supports Redis with in-memory fallback.
- File storage is pluggable (`local` or `azure`).
- API docs (`/docs`, `/redoc`, `/openapi.json`) are disabled by default in production.
- Router loading is fail-fast in production (startup fails if any router import fails).
- Error tracking supports Sentry for API and Celery.

Important environment flags:
- `RATE_LIMIT_USE_REDIS=true`
- `RATE_LIMIT_REQUESTS_PER_MINUTE=100`
- `RATE_LIMIT_WINDOW_SECONDS=60`
- `ENABLE_API_DOCS=false` in production
- `STRICT_ROUTER_IMPORTS=true` in production
- `METRICS_ENABLED=true`
- `METRICS_PATH=/metrics`
- `API_RESPONSE_ENVELOPE_ENABLED` and `API_RESPONSE_SUCCESS_MESSAGE`
- `API_RESPONSE_ENVELOPE_EXCLUDED_PATHS`
- `SENTRY_DSN`
- `SENTRY_ENVIRONMENT`
- `SENTRY_RELEASE`
- `SENTRY_TRACES_SAMPLE_RATE`
- `SENTRY_PROFILES_SAMPLE_RATE`
- `SENTRY_SEND_PII`
- `SENTRY_ENABLE_FOR_CELERY`
- `WEBHOOKS_ENABLED`
- `WEBHOOK_TARGET_URLS`
- `WEBHOOK_SIGNING_SECRET`
- `WEBHOOK_TIMEOUT_SECONDS`
- `FILE_STORAGE_PROVIDER=local` (or `azure`)
- `FILE_DOWNLOAD_URL_EXPIRE_SECONDS=900`
- `AUTH_RATE_LIMIT_REQUESTS_PER_MINUTE`
- `AUTH_RATE_LIMIT_WINDOW_SECONDS`
- `AUTH_RATE_LIMIT_PATHS`
- `FILE_UPLOAD_RATE_LIMIT_REQUESTS_PER_HOUR`
- `FILE_UPLOAD_RATE_LIMIT_WINDOW_SECONDS`
- `FILE_UPLOAD_RATE_LIMIT_PATHS`
- `TASKS_FORCE_INLINE=true` for local/dev, `false` for production
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `FRONTEND_BASE_URL` (used in password reset links)
- `EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES`
- `REQUIRE_EMAIL_VERIFICATION_FOR_LOGIN`
- `MFA_CHALLENGE_TOKEN_EXPIRE_MINUTES`
- `MFA_LOGIN_CODE_EXPIRE_MINUTES`
- `MFA_LOGIN_CODE_LENGTH`

SMTP provider quick start (Resend):
- `SMTP_HOST=smtp.resend.com`
- `SMTP_PORT=587`
- `SMTP_USERNAME=resend`
- `SMTP_PASSWORD=<resend_api_key>`
- `SMTP_USE_TLS=true`

SMTP connectivity check:
```bash
python scripts/test_smtp_connection.py
python scripts/test_smtp_connection.py --to your-email@example.com
```

## Branch Strategy
- `main`: stable releases.
- `develop`: integration branch.
- `feature/*` and `chore/*`: scoped implementation branches.
- Merge style: `--no-ff` from feature branches into `develop`, then `develop` into `main`.

## Notes
- Local uploads are served from `/uploads/*`.
- Certificate files are stored in `certificates/` and downloadable through certificate endpoints.
- First migration is provided in `alembic/versions/0001_initial_schema.py`.
