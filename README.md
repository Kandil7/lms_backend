# LMS Backend

[![CI Status](https://github.com/Kadnil7/lms_backend/actions/workflows/ci.yml/badge.svg)](https://github.com/Kadnil7/lms_backend/actions/workflows/ci.yml)
[![Code Coverage](https://img.shields.io/codecov/c/github/Kadnil7/lms_backend)](https://codecov.io/github/Kadnil7/lms_backend)
[![Security Scan](https://github.com/Kadnil7/lms_backend/actions/workflows/security.yml/badge.svg)](https://github.com/Kadnil7/lms_backend/actions/workflows/security.yml)

Production-oriented LMS backend built as a modular monolith with FastAPI.

## Quick Start

Get up and running in minutes:

1. **Clone the repository**
   ```bash
   git clone https://github.com/Kadnil7/lms_backend.git
   cd lms_backend
   ```

2. **Set up Python environment (3.11 or 3.12 recommended)**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and other settings
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the API server**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access API documentation**
   - Local: `http://localhost:8000/docs`
   - Ready endpoint: `http://localhost:8000/api/v1/ready`

> **Note**: For production deployment, use Docker with `docker-compose.prod.yml` and appropriate environment files.

## Live Environments
- Production base URL: `https://egylms.duckdns.org`
- Production API base: `https://egylms.duckdns.org/api/v1`
- Production readiness endpoint: `https://egylms.duckdns.org/api/v1/ready`
- Development base URL: `http://localhost:8000`
- Development API docs: `http://localhost:8000/docs`
- Production docs are disabled by default (`ENABLE_API_DOCS=false`).

## Documentation
- Full technical summary: `docs/tech/18-Complete-Project-Summary.md`
- Documentation index: `docs/README.md`
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
The LMS backend follows a **modular monolith** architecture pattern, balancing the benefits of monolithic simplicity with the maintainability of microservices.

### Core Structure
- `app/core`: Configuration, database, security, dependencies, middleware, and shared utilities.
- `app/modules/*`: Vertical business modules with clear separation of concerns:
  - `models`: SQLAlchemy ORM models
  - `schemas`: Pydantic schemas for request/response validation
  - `repositories`: Data access layer with database operations
  - `services`: Business logic implementation
  - `routers`: FastAPI routers with endpoint definitions
- `app/api/v1/api.py`: Router aggregation and API prefix wiring.
- `alembic`: Database migrations.
- `tests`: API integration tests.

### Key Design Principles
- **Domain-Driven Design**: Each module represents a bounded context
- **Separation of Concerns**: Clear boundaries between data access, business logic, and presentation
- **Testability**: Each module can be tested in isolation
- **Extensibility**: New modules can be added without affecting existing code

## Implemented Modules
- `auth`: Registration/login/refresh/logout, refresh token revocation, forgot/reset password, email verification, optional MFA login challenge.
- `users`: Profile + admin user management.
- `courses`: Course and lesson CRUD with ownership checks.
- `enrollments`: Enrollment lifecycle, lesson progress aggregation, reviews.
- `quizzes`: Quiz/question authoring, attempts, grading.
- `analytics`: Student dashboard, course analytics, instructor and system overview.
- `files`: Upload/list/download with Azure Blob (default) and local fallback backend.
- `certificates`: Automatic issuance on completion, verify/download/revoke.
- `payments`: Order management, payment processing (DEFERRED - skeleton ready, not wired into API).
- `websocket`: Real-time communication infrastructure.

## Python Compatibility
- **Supported Versions**: Python 3.11 and 3.12
- **CI Validation**: Both versions are tested in the CI pipeline
- **Recommendation**: Use Python 3.12 for development and production

## Contribution Guidelines

### Branch Strategy
- `main`: Stable releases (protected branch)
- `develop`: Integration branch for upcoming releases
- `feature/*`: Scoped implementation branches
- `chore/*`: Maintenance and refactoring branches

### Pull Request Process
1. Create a feature branch from `develop`
2. Implement your changes with proper tests
3. Run local tests: `pytest -q`
4. Ensure code coverage ≥ 75%: `pytest --cov=app --cov-fail-under=75`
5. Submit PR to `develop` (not `main`)
6. CI will run automated tests, security scans, and dependency checks
7. After review and approval, merge to `develop`

### Code Quality Requirements
- Follow PEP 8 style guide
- Type hints for all public interfaces
- Comprehensive test coverage for new functionality
- Documentation for new modules and significant changes
- Security considerations for all new endpoints

### Testing Strategy
- Unit tests: `pytest -q`
- Integration tests: `pytest tests/integration/`
- Database tests: `pytest --db-url postgresql+psycopg2://...`
- Load testing: `scripts/windows/run_load_test.bat`
- Security scanning: `pip-audit`, `bandit`, `gitleaks`

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
   python scripts/user_management/create_admin.py
   ```
5. (Optional) create instructor in one command:
   ```bash
   python scripts/user_management/create_instructor.py
   ```
6. Run API:
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

Production preflight validation:
```bash
python scripts/deployment/validate_environment.py --env-file .env --strict-warnings
```
The Azure VM deploy script also runs this validator automatically before migrations.

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
.\scripts\helpers\run_project.ps1
```

Demo one-command startup (Windows, includes seed + demo Postman JSON):
```bat
scripts\windows\run_demo.bat
```

Staging one-command startup (Windows):
```bat
scripts\windows\run_staging.bat
```

Observability one-command startup (Windows):
```bat
scripts\windows\run_observability.bat
```

Side-by-side demo startup (Windows, separate stack on port `8002`):
```bat
run_demo_side_by_side.bat
```
Stop side-by-side demo:
```bat
stop_demo_side_by_side.bat
```

Side-by-side demo stack (manual):
```bash
cp .env.demo.example .env.demo
docker compose -p lms-demo -f docker-compose.demo.yml up -d --build
docker compose -p lms-demo -f docker-compose.demo.yml exec -T api python scripts/database/seed_demo_data.py --reset-passwords --json-output postman/demo_seed_snapshot.demo.json
```

Demo domain on DuckDNS with separate reverse proxy (Windows):
```bat
run_demo_side_by_side.bat
run_demo_proxy_duckdns.bat
```

Demo domain setup (manual):
```bash
cp .env.demo.proxy.example .env.demo.proxy
# edit .env.demo.proxy:
# - DEMO_DOMAIN (e.g. egylmsdemo.duckdns.org)
# - LETSENCRYPT_EMAIL
# - DUCKDNS_SUBDOMAINS
# - DUCKDNS_TOKEN
docker compose -p lms-demo-proxy --env-file .env.demo.proxy -f docker-compose.demo.proxy.yml up -d
```

Stop demo reverse proxy:
```bat
stop_demo_proxy_duckdns.bat
```

Notes:
- `docker-compose.demo.proxy.yml` assumes demo API is reachable at `http://localhost:8002` (change `DEMO_UPSTREAM` if needed).
- If another service is already using ports `80/443`, adjust `DEMO_HTTP_PORT` and `DEMO_HTTPS_PORT` in `.env.demo.proxy`.

Azure demo deployment (dedicated VM, TLS on `80/443`):
```bash
cp .env.demo.azure.example .env.demo.azure
docker compose --env-file .env.demo.azure -f docker-compose.demo.azure.yml up -d --build
docker compose --env-file .env.demo.azure -f docker-compose.demo.azure.yml exec -T api python scripts/database/seed_demo_data.py --reset-passwords --skip-attempt --json-output postman/demo_seed_snapshot.azure.json
```

Azure demo deploy script (remote):
```bash
export AZURE_VM_HOST="<vm-public-ip>"
export AZURE_VM_USER="azureuser"
export APP_DOMAIN="egylmsdemo.duckdns.org"
export LETSENCRYPT_EMAIL="ops@example.com"
export SECRET_KEY="<32+ chars strong secret>"
bash scripts/linux/deploy_azure_demo_vm.sh
```

PowerShell equivalent:
```powershell
.\scripts\deployment\deploy_azure_demo_vm.ps1 -AzureVMHost "<vm-public-ip>" -AzureVMUser "azureuser" -AppDomain "egylmsdemo.duckdns.org" -LetsEncryptEmail "ops@example.com" -SecretKey "<32+ chars strong secret>"
```

Azure demo notes:
- `docker-compose.demo.azure.yml` is intended for a dedicated VM because it binds host ports `80/443`.
- Ensure Azure NSG + VM firewall allow inbound TCP `80` and `443`.

Useful flags:
- `-NoBuild`
- `-NoMigrate`
- `-CreateAdmin`
- `-CreateInstructor`
- `-SeedDemoData`
- `-FollowLogs`

Readiness endpoint:
- `http://localhost:8000/api/v1/ready`
- `https://egylms.duckdns.org/api/v1/ready` (current production)
- `http://localhost:8002/api/v1/ready` (side-by-side demo)
- `https://<your-demo-domain>/api/v1/ready` (demo domain via `docker-compose.demo.proxy.yml`)
- `https://<your-demo-azure-domain>/api/v1/ready` (Azure demo via `docker-compose.demo.azure.yml`)

Metrics endpoint:
- `http://localhost:8000/metrics`
- `https://egylms.duckdns.org/metrics` (production if exposed through Caddy)
- `https://<your-demo-domain>/metrics` (demo domain via `docker-compose.demo.proxy.yml`)
- `https://<your-demo-azure-domain>/metrics` (Azure demo via `docker-compose.demo.azure.yml`)

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
scripts\windows\run_load_test.bat
```
Optional authenticated flow:
```bat
scripts\windows\run_load_test.bat http://localhost:8000 20 60s localhost true
```

Realistic sign-off scenario (student/instructor/admin):
```bat
scripts\windows\run_load_test_realistic.bat http://localhost:8001 10m localhost 8 3 1
```

## Database Backup and Restore
Create a backup (Windows):
```bat
scripts\windows\backup_db.bat
```

Restore from backup (Windows):
```bat
scripts\windows\restore_db.bat backups\db\lms_YYYYMMDD_HHMMSS.dump --yes
```

Create a daily scheduled backup task (Windows):
```powershell
.\scripts\maintenance\setup_backup_task.ps1 -TaskName LMS-DB-Backup -Time 02:00
```

Run restore drill manually (Windows):
```bat
scripts\windows\restore_drill.bat -ComposeFile docker-compose.prod.yml
```

Create a weekly restore drill task (Windows):
```powershell
.\scripts\maintenance\setup_restore_drill_task.ps1 -TaskName LMS-DB-Restore-Drill -Time 03:30 -DaysOfWeek Sunday -ComposeFile docker-compose.prod.yml
```

## Demo Data Seed
Use this script to create demo users, one published course, lessons, enrollment, quiz, and a graded attempt.

```bash
python scripts/database/seed_demo_data.py
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

## Create Instructor Account
Fastest way (recommended):

```bash
python scripts/user_management/create_instructor.py
```

If API runs in Docker:

```bash
docker compose -f docker-compose.yml exec -T api python scripts/user_management/create_instructor.py
```

Customize via environment variables:

```bash
INSTRUCTOR_EMAIL=instructor@example.com \
INSTRUCTOR_PASSWORD=StrongPass123 \
INSTRUCTOR_FULL_NAME="Instructor One" \
INSTRUCTOR_UPDATE_EXISTING=true \
python scripts/user_management/create_instructor.py
```

Advanced/role-agnostic creation:

```bash
python scripts/user_management/create_user.py --email instructor@example.com --password StrongPass123 --full-name "Instructor One" --role instructor --update-existing
```

## Postman Collection
Generate Postman artifacts from OpenAPI:

```bash
python scripts/documentation/generate_postman_collection.py
```

Generated files:
- `postman/LMS Backend.postman_collection.json`
- `postman/LMS Backend.postman_environment.json`

Generate demo Postman artifacts from seeded data snapshot:

```bash
python scripts/documentation/generate_demo_postman.py --seed-file postman/demo_seed_snapshot.json
```

Generated demo files:
- `postman/LMS Backend Demo.postman_collection.json`
- `postman/LMS Backend Demo.postman_environment.json`
- `postman/demo_seed_snapshot.json`

## Full API Documentation
Generate a complete Markdown API reference from the live OpenAPI schema:

```bash
python scripts/documentation/generate_full_api_documentation.py
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
- `FILE_STORAGE_PROVIDER=azure` (or `local`)
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
python scripts/testing/test_smtp_connection.py
python scripts/testing/test_smtp_connection.py --to your-email@example.com
```

## Integration Status (February 23, 2026)
✅ **Integration Complete**

The LMS system is now fully integrated and ready for production deployment. All core functionality is working:

- Authentication: Login, register, MFA, password reset
- Courses: Browse, detail, enrollment, progress tracking
- Quizzes: Authoring, attempts, grading
- Assignments: Creation, submission, grading
- Files: Upload, download, management
- Certificates: Generation, verification, download
- Payments: Order management, payment processing (skeleton ready)
- Real-time: WebSocket infrastructure in place

### Next Steps
1. Run database migrations: `alembic upgrade head`
2. Start backend: `uvicorn app.main:app --reload`
3. Start frontend: `npm run dev`
4. Test user flows and replace mock data with real API calls

## Branch Strategy
- `main`: stable releases.
- `develop`: integration branch.
- `feature/*` and `chore/*`: scoped implementation branches.
- Merge style: `--no-ff` from feature branches into `develop`, then `develop` into `main`.

## Notes
- If `FILE_STORAGE_PROVIDER=local`, uploads are served from `/uploads/*`.
- Certificate files are stored in `certificates/` and downloadable through certificate endpoints.
- First migration is provided in `alembic/versions/0001_initial_schema.py`.