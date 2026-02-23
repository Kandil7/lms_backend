# LMS Backend - Complete Project Structure

## Project Overview

The LMS Backend is a production-ready Learning Management System built with FastAPI. This document provides a comprehensive overview of the entire project structure.

---

## Directory Structure

```
lms_backend/
├── .github/                    # GitHub configuration
│   └── workflows/              # CI/CD pipelines
│       ├── ci.yml             # Continuous Integration
│       ├── security.yml       # Security scanning
│       └── deploy-azure-vm.yml  # Azure deployment
│
├── .pytest_cache/              # Pytest cache
│
├── alembic/                    # Database migrations
│   ├── env.py                 # Alembic environment
│   ├── script.py.mako         # Migration template
│   └── versions/              # Migration files
│
├── app/                        # Main application
│   ├── __init__.py
│   ├── main.py                # FastAPI entry point
│   │
│   ├── api/                   # API routing
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── api.py         # Router aggregation
│   │
│   ├── core/                  # Core infrastructure
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   ├── database.py        # Database connection
│   │   ├── security.py        # JWT & password security
│   │   ├── dependencies.py    # FastAPI dependencies
│   │   ├── exceptions.py      # Exception handling
│   │   ├── permissions.py     # RBAC permissions
│   │   ├── cache.py          # Redis caching
│   │   ├── metrics.py        # Prometheus metrics
│   │   ├── health.py         # Health checks
│   │   ├── firebase.py       # Firebase integration
│   │   ├── secrets.py        # Secrets management
│   │   ├── webhooks.py       # Webhook delivery
│   │   ├── cookie_utils.py   # Cookie utilities
│   │   ├── account_lockout.py # Account lockout
│   │   ├── model_registry.py # Model loading
│   │   ├── observability.py  # Sentry integration
│   │   │
│   │   └── middleware/        # Custom middleware
│   │       ├── __init__.py
│   │       ├── security_headers.py
│   │       ├── rate_limit.py
│   │       ├── request_logging.py
│   │       └── response_envelope.py
│   │
│   ├── modules/               # Feature modules
│   │   ├── auth/            # Authentication
│   │   ├── users/          # User management
│   │   ├── courses/         # Course management
│   │   ├── enrollments/     # Enrollment tracking
│   │   ├── quizzes/         # Quiz system
│   │   ├── assignments/    # Assignments
│   │   ├── certificates/    # Certificates
│   │   ├── files/          # File uploads
│   │   └── analytics/       # Analytics
│   │
│   ├── tasks/               # Celery background tasks
│   │   ├── celery_app.py    # Celery configuration
│   │   ├── dispatcher.py   # Task dispatcher
│   │   ├── email_tasks.py  # Email sending
│   │   ├── progress_tasks.py # Progress tracking
│   │   ├── certificate_tasks.py # Certificate generation
│   │   └── webhook_tasks.py # Webhook delivery
│   │
│   └── utils/               # Utilities
│       ├── constants.py     # Application constants
│       ├── validators.py    # Input validators
│       ├── pagination.py    # Pagination helpers
│       └── mime_utils.py    # MIME type utilities
│
├── docs/                      # Documentation
│   ├── tech/               # Technical guides
│   ├── ops/                # Operations guides
│   ├── legal/              # Legal templates
│   ├── templates/           # QA templates
│   ├── 01-09-*.md         # Arabic guides
│   └── README.md           # Main index
│
├── functions/                 # Firebase Cloud Functions
│   ├── main.py             # Email function
│   └── requirements.txt
│
├── ops/                      # Infrastructure configs
│   ├── caddy/              # Caddy reverse proxy
│   │   └── Caddyfile
│   │
│   └── observability/       # Monitoring stack
│       ├── prometheus/      # Prometheus config
│       ├── grafana/        # Grafana dashboards
│       └── alertmanager/   # Alert routing
│
├── scripts/                  # Automation scripts
│   ├── wait_for_db.py
│   ├── validate_environment.py
│   ├── seed_demo_data.py
│   ├── create_admin.py
│   ├── create_instructor.py
│   ├── create_user.py
│   ├── test_smtp_connection.py
│   ├── test_firebase_integration.py
│   ├── generate_postman_collection.py
│   ├── generate_demo_postman.py
│   ├── generate_full_api_documentation.py
│   ├── deploy_azure_vm.ps1
│   ├── deploy_azure_vm.sh
│   ├── setup_backup_task.ps1
│   ├── setup_restore_drill_task.ps1
│   ├── remove_backup_task.ps1
│   ├── remove_restore_drill_task.ps1
│   ├── run_restore_drill.ps1
│   └── *.bat / *.sh        # Helper scripts
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   ├── helpers.py          # Test helpers
│   ├── perf/               # Performance tests
│   │   ├── k6_smoke.js
│   │   └── k6_realistic.js
│   └── test_*.py           # Unit/Integration tests
│
├── postman/                  # API testing collections
│   ├── LMS Backend.postman_collection.json
│   ├── LMS Backend.postman_environment.json
│   ├── LMS Backend Demo.postman_collection.json
│   ├── LMS Backend Demo.postman_environment.json
│   ├── LMS Backend Production.postman_collection.json
│   └── demo_seed_snapshot.json
│
├── uploads/                  # User uploads (runtime)
│   └── course-materials/
│
├── certificates/            # Generated certificates (runtime)
│
├── .env                    # Environment config
├── .env.example            # Environment template
├── .env.staging.example   # Staging template
├── .env.production.example # Production template
├── .env.observability.example
│
├── .dockerignore
├── .gitignore
├── .coverage
│
├── alembic.ini            # Alembic config
├── Dockerfile             # Application image
├── firebase.json          # Firebase config
├── .firebaserc
│
├── docker-compose.yml          # Development
├── docker-compose.staging.yml  # Staging
├── docker-compose.prod.yml      # Production
├── docker-compose.observability.yml  # Monitoring
│
├── requirements.txt       # Python dependencies
├── README.md            # Main README
└── implementation_plan.md
```

---

## Core Components Explained

### 1. Application Entry Point (app/main.py)

The FastAPI application initialization. Configures:
- Middleware stack (CORS, security, rate limiting)
- Router aggregation
- Exception handlers
- Lifespan events (startup/shutdown)
- Health check endpoints

### 2. Core Infrastructure (app/core/)

**config.py**: Central configuration using Pydantic-settings. All environment variables are validated and typed.

**database.py**: SQLAlchemy engine and session management. Connection pooling for PostgreSQL.

**security.py**: JWT token creation/validation, password hashing with bcrypt, token blacklist management.

**dependencies.py**: FastAPI dependency injection for authentication and authorization.

**exceptions.py**: Custom HTTP exceptions and global exception handlers.

**cache.py**: Redis caching utilities with TTL support.

**metrics.py**: Prometheus metrics for request counting and latency tracking.

**middleware/**: Custom middleware for rate limiting, security headers, request logging.

### 3. Feature Modules (app/modules/)

Each module follows the pattern:
```
module_name/
├── models.py        # SQLAlchemy ORM models
├── schemas.py      # Pydantic request/response schemas
├── repository.py   # Data access layer
├── service.py      # Business logic
├── router.py       # API endpoints
└── (optional subdirectories)
```

**auth/**: JWT authentication, login/logout, password reset, MFA support

**users/**: User profiles, admin user management

**courses/**: Course CRUD, lesson management, publishing workflow

**enrollments/**: Student enrollment, progress tracking, completion detection

**quizzes/**: Quiz creation, questions, attempts, automatic grading

**assignments/**: Student assignments, instructor grading

**certificates/**: PDF certificate generation on course completion

**files/**: File upload/download with local or Azure storage

**analytics/**: Dashboards for students, instructors, admins

### 4. Background Tasks (app/tasks/)

Celery tasks for asynchronous processing:
- **email_tasks.py**: Transactional emails
- **progress_tasks.py**: Progress updates
- **certificate_tasks.py**: PDF generation
- **webhook_tasks.py**: External notifications

### 5. API Routing (app/api/)

The api.py aggregates all module routers:
```python
api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(users.router, prefix="/users")
# ... etc
```

---

## Configuration Files

### Docker Compose Files

| File | Purpose |
|------|---------|
| docker-compose.yml | Local development |
| docker-compose.staging.yml | Staging environment |
| docker-compose.prod.yml | Production deployment |
| docker-compose.observability.yml | Monitoring stack |

### Environment Files

| File | Purpose |
|------|---------|
| .env | Local development (not committed) |
| .env.example | Template for developers |
| .env.staging.example | Staging configuration |
| .env.production.example | Production configuration |
| .env.observability.example | Monitoring configuration |

---

## CI/CD Pipeline (.github/workflows/)

### ci.yml
- Runs on push/PR to main, develop, feature/*, chore/*
- Tests on Python 3.11 and 3.12
- Static checks (compileall, pip check)
- Unit tests with 75% coverage gate
- PostgreSQL integration tests

### security.yml
- Dependency vulnerability scanning (pip-audit)
- Code security analysis (bandit)
- Secret detection (gitleaks)
- Weekly scheduled scans

### deploy-azure-vm.yml
- Triggers on push to main
- Deploys to Azure Virtual Machine
- Runs deployment scripts

---

## Infrastructure (ops/)

### Caddy (ops/caddy/)
Reverse proxy with automatic HTTPS:
- TLS termination
- Security headers
- HTTP/2 support
- Let's Encrypt integration

### Prometheus (ops/observability/prometheus/)
Metrics collection:
- Application metrics scraping
- Alert rule definitions

### Grafana (ops/observability/grafana/)
Visualization:
- Pre-built dashboards
- Prometheus datasource
- Alert visualization

---

## Scripts Directory

### User Management
- create_admin.py
- create_instructor.py
- create_user.py

### Development
- seed_demo_data.py
- validate_environment.py
- wait_for_db.py

### Deployment
- deploy_azure_vm.ps1 / .sh

### Database
- backup_db.bat
- restore_db.bat
- setup_backup_task.ps1
- setup_restore_drill_task.ps1

### Testing
- test_smtp_connection.py
- test_firebase_integration.py

### Documentation
- generate_postman_collection.py
- generate_full_api_documentation.py
- generate_demo_postman.py

---

## Testing (tests/)

### Test Types
- **Unit Tests**: Individual function testing
- **Integration Tests**: API endpoint testing
- **Performance Tests**: k6 load tests

### Key Test Files
- test_auth.py
- test_courses.py
- test_quizzes.py
- test_enrollments.py
- test_certificates.py
- test_analytics.py
- test_files.py
- test_config.py

---

## Postman Collections (postman/)

| Collection | Purpose |
|-----------|---------|
| LMS Backend.postman_collection.json | Base API collection |
| LMS Backend Demo.postman_collection.json | Demo with seeded data |
| LMS Backend Production.postman_collection.json | Production testing |

---

## Technology Stack Summary

| Component | Technology |
|-----------|------------|
| Web Framework | FastAPI |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Cache/Broker | Redis 7 |
| Task Queue | Celery |
| Auth | JWT (python-jose) |
| Passwords | bcrypt |
| Container | Docker |
| Reverse Proxy | Caddy |
| Monitoring | Prometheus, Grafana |
| Cloud | Azure |

---

## Key Files Reference

| File | Purpose |
|------|---------|
| app/main.py | FastAPI app initialization |
| app/core/config.py | All configuration |
| app/core/database.py | Database connection |
| app/core/security.py | JWT & passwords |
| app/api/v1/api.py | Router aggregation |
| docker-compose.prod.yml | Production stack |
| .github/workflows/ci.yml | CI pipeline |
| ops/caddy/Caddyfile | Reverse proxy |
| scripts/deploy_azure_vm.sh | Deployment script |

---

*This is a comprehensive overview of the LMS Backend project structure.*
