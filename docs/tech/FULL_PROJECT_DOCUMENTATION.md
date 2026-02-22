# Comprehensive LMS Backend Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Tech Stack and Technology Choices](#tech-stack-and-technology-choices)
3. [Project Structure](#project-structure)
4. [Configuration System](#configuration-system)
5. [Database and Migrations](#database-and-migrations)
6. [Core Infrastructure Modules](#core-infrastructure-modules)
7. [Feature Modules](#feature-modules)
8. [Background Tasks (Celery)](#background-tasks-celery)
9. [Docker and Deployment](#docker-and-deployment)
10. [CI/CD Pipeline (.github/workflows)](#cicd-pipeline-githubworkflows)
11. [Operations Infrastructure (ops/)](#operations-infrastructure-ops)
12. [Observability Stack](#observability-stack)
13. [Security Implementation](#security-implementation)
14. [API Design and Endpoints](#api-design-and-endpoints)

---

## Project Overview

This is a comprehensive **Learning Management System (LMS) Backend** built with modern Python technologies. The system provides a complete platform for managing online courses, enrollments, quizzes, certificates, and analytics.

### Key Features
- **User Authentication**: JWT-based auth with refresh tokens, MFA support, account lockout
- **Course Management**: Courses, lessons, categories, prerequisites
- **Enrollment System**: Student enrollment, progress tracking
- **Quiz System**: Questions, answers, attempts, scoring
- **File Management**: Local and Azure Blob storage support
- **Certificate Generation**: Auto-generated certificates upon course completion
- **Analytics**: Student, instructor, and system analytics
- **Webhooks**: Event-driven integrations

---

## Tech Stack and Technology Choices

### Why These Technologies?

| Category | Technology | Version | Rationale |
|----------|------------|---------|-----------|
| **Web Framework** | FastAPI | >=0.115.0 | High-performance async framework, automatic OpenAPI docs, type validation with Pydantic |
| **Server** | Uvicorn | >=0.34.0 | ASGI server, supports multiple workers, hot reload in development |
| **ORM** | SQLAlchemy | >=2.0.36 | Mature ORM with async support, migration tools via Alembic |
| **Database** | PostgreSQL | 16 | Robust relational DB, excellent JSON support, ACID compliance |
| **Database Driver** | psycopg2-binary | >=2.9.10 | Fast PostgreSQL adapter, binary distribution for easy install |
| **Migrations** | Alembic | >=1.14.0 | Schema version control, incremental changes |
| **Configuration** | pydantic-settings | >=2.7.1 | Type-safe configuration with environment variable support |
| **Authentication** | python-jose | >=3.3.0 | JWT encoding/decoding, RS256/HS256 support |
| **Password Hashing** | passlib[bcrypt] | >=1.7.4 | Industry-standard bcrypt with automatic upgrades |
| **Caching/Session** | Redis | 7 | In-memory data store, pub/sub, session management |
| **Task Queue** | Celery | >=5.4.0 | Distributed task queue, multiple queue support |
| **Monitoring** | Prometheus | v2.54.1 | Metrics collection, time-series database |
| **Visualization** | Grafana | 11.2.2 | Dashboard creation, alerting |
| **Error Tracking** | Sentry | >=2.18.0 | Error monitoring, performance tracing |
| **File Storage** | Azure Blob | >=12.26.0 | Cloud storage integration |
| **PDF Generation** | fpdf2 | >=2.8.2 | Certificate PDF generation |
| **Email** | Built-in SMTP | - | Standard email protocol support |
| **Testing** | pytest | >=8.3.4 | Comprehensive test framework |

### Architecture Pattern: Modular Monolith
The project follows a **modular monolith** architecture:
- **Separation by Feature**: Each feature (auth, courses, enrollments) is a separate module
- **Shared Infrastructure**: Common utilities, middleware, and database models are centralized
- **Single Deployment**: All modules deployed together but logically separated
- **Future-Ready**: Can be split into microservices if needed

---

## Project Structure

```
lms_backend/
├── app/                          # Main application code
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── api/
│   │   └── v1/
│   │       └── api.py            # API router aggregation
│   ├── core/                     # Core infrastructure
│   │   ├── config.py             # Configuration management
│   │   ├── database.py           # Database connection
│   │   ├── security.py           # JWT, password hashing
│   │   ├── dependencies.py       # FastAPI dependencies
│   │   ├── exceptions.py         # Custom exceptions
│   │   ├── health.py             # Health checks
│   │   ├── metrics.py            # Prometheus metrics
│   │   ├── observability.py      # Sentry integration
│   │   ├── cache.py              # Redis caching
│   │   ├── webhooks.py           # Webhook dispatcher
│   │   ├── permissions.py        # Role-based permissions
│   │   ├── model_registry.py     # Model loading
│   │   ├── secrets.py            # Secrets management
│   │   ├── account_lockout.py    # Account security
│   │   ├── cookie_utils.py       # Cookie utilities
│   │   └── middleware/           # Custom middleware
│   │       ├── __init__.py
│   │       ├── rate_limit.py     # Rate limiting
│   │       ├── security_headers.py
│   │       ├── request_logging.py
│   │       └── response_envelope.py
│   ├── modules/                  # Feature modules
│   │   ├── auth/                 # Authentication
│   │   ├── users/                # User management
│   │   ├── courses/              # Course management
│   │   ├── enrollments/          # Student enrollments
│   │   ├── quizzes/              # Quiz system
│   │   ├── files/                # File uploads
│   │   ├── certificates/         # Certificate generation
│   │   └── analytics/            # Analytics
│   ├── tasks/                    # Celery tasks
│   │   ├── celery_app.py
│   │   ├── email_tasks.py
│   │   ├── progress_tasks.py
│   │   ├── certificate_tasks.py
│   │   └── webhook_tasks.py
│   └── utils/                    # Utilities
│       ├── constants.py
│       ├── pagination.py
│       ├── validators.py
│       └── mime_utils.py
├── ops/                          # Operational configs
│   ├── caddy/                    # Caddy reverse proxy
│   │   └── Caddyfile
│   └── observability/            # Monitoring stack
│       ├── prometheus/
│       ├── grafana/
│       └── alertmanager/
├── .github/
│   └── workflows/                # CI/CD pipelines
│       ├── ci.yml
│       ├── deploy-azure-vm.yml
│       └── security.yml
├── alembic/                     # Database migrations
│   ├── env.py
│   └── versions/
├── tests/                       # Test suite
├── docker-compose.yml           # Development
├── docker-compose.prod.yml      # Production
├── docker-compose.staging.yml   # Staging
├── docker-compose.observability.yml
├── requirements.txt
├── alembic.ini
└── .env.example
```

---

## Configuration System

### Configuration Architecture (`app/core/config.py`)

The project uses **Pydantic Settings** for type-safe configuration management with environment variable support.

#### Key Design Decisions:

1. **Environment-Based Configuration**
   - Different settings for development, staging, and production
   - Production requires strict validation

2. **Secrets Management**
   - Development: Environment variables / .env files
   - Production: HashiCorp Vault integration with fallback to env vars
   - Azure Key Vault support

3. **Configuration Categories**
   ```python
   # Core Settings
   PROJECT_NAME, VERSION, ENVIRONMENT, DEBUG
   
   # API Settings
   API_V1_PREFIX, ENABLE_API_DOCS, METRICS_ENABLED
   
   # Database Settings
   DATABASE_URL, SQLALCHEMY_ECHO, DB_POOL_SIZE
   
   # Security Settings
   SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
   MFA_CHALLENGE_TOKEN_EXPIRE_MINUTES, ACCESS_TOKEN_BLACKLIST_ENABLED
   
   # Rate Limiting
   RATE_LIMIT_REQUESTS_PER_MINUTE, RATE_LIMIT_WINDOW_SECONDS
   AUTH_RATE_LIMIT_REQUESTS_PER_MINUTE
   
   # File Upload
   UPLOAD_DIR, MAX_UPLOAD_MB, ALLOWED_UPLOAD_EXTENSIONS
   FILE_STORAGE_PROVIDER (local/azure)
   
   # Email/SMTP
   SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD
   
   # Azure Storage
   AZURE_STORAGE_CONNECTION_STRING, AZURE_STORAGE_CONTAINER_NAME
   
   # Caching
   CACHE_ENABLED, CACHE_DEFAULT_TTL_SECONDS
   COURSE_CACHE_TTL_SECONDS, LESSON_CACHE_TTL_SECONDS
   ```

4. **Validation Properties**
   ```python
   @property
   def MAX_UPLOAD_BYTES(self) -> int:
       return self.MAX_UPLOAD_MB * 1024 * 1024
   
   @property
   def API_DOCS_EFFECTIVE_ENABLED(self) -> bool:
       if self.ENVIRONMENT == "production":
           return False
       return self.ENABLE_API_DOCS
   ```

5. **Production Validation**
   ```python
   @model_validator(mode="after")
   def validate_production_settings(self):
       if self.ENVIRONMENT == "production":
           # Force DEBUG=False
           # Load secrets from Vault
           # Validate SECRET_KEY strength
           # Require ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED
           # Ensure TASKS_FORCE_INLINE=False
   ```

---

## Database and Migrations

### Database Architecture (`app/core/database.py`)

```python
# SQLAlchemy Setup
engine = create_engine(settings.DATABASE_URL, **kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Connection Pooling (PostgreSQL)
pool_size = 20        # Base connections
max_overflow = 40     # Additional connections under load

# Health Check
def check_database_health() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
```

### Migration System (Alembic)

**Why Alembic?**
- Incremental schema changes
- Version control for database schema
- Easy rollback capability
- Support for data migrations

**Migration Structure** (`alembic/versions/`):
- `0001_initial_schema.py` - Initial tables
- `0002_phase1_security_and_performance.py` - Security indexes
- `0003_phase1_infrastructure_indexes.py` - Performance indexes
- `0004_phase1_quiz_indexes.py` - Quiz performance
- `0005_phase1_remaining_indexes.py` - Additional indexes
- `0006_add_users_email_verified_at.py` - Email verification
- `0007_add_users_mfa_enabled.py` - MFA support

**Model Registry** (`app/core/model_registry.py`)
- Loads all SQLAlchemy models at startup
- Ensures metadata is populated for migrations

---

## Core Infrastructure Modules

### 1. Security Module (`app/core/security.py`)

**Features:**
- JWT token creation and validation
- Password hashing with bcrypt
- Token blacklist management (Redis + memory fallback)
- Multiple token types: Access, Refresh, Password Reset, Email Verification, MFA Challenge

**Design Decisions:**

```python
# Token Blacklist with Dual Backend
class AccessTokenBlacklist:
    # Primary: Redis (distributed, persistent)
    # Fallback: In-memory (for development/failover)
    # Production: Fail-closed if Redis unavailable
```

### 2. Rate Limiting (`app/core/middleware/rate_limit.py`)

**Why Custom Rate Limiting?**
- Flexible rule-based limiting
- Redis-backed for distributed systems
- Memory fallback for reliability
- Per-path, per-user, per-IP granularity

**Configuration:**
```python
# Default: 100 requests per minute
# Auth paths: 60 requests per minute (stricter)
# File uploads: 100 requests per hour (most strict)
```

### 3. Middleware Stack (`app/core/middleware/`)

| Middleware | Purpose | Key Features |
|-----------|---------|--------------|
| `RateLimitMiddleware` | Prevent abuse | Redis/memory, custom rules |
| `SecurityHeadersMiddleware` | OWASP protection | HSTS, CSP, X-Frame-Options |
| `RequestLoggingMiddleware` | Audit trail | Request/response logging |
| `ResponseEnvelopeMiddleware` | API consistency | Standard response format |
| `MetricsMiddleware` | Observability | Prometheus metrics |

### 4. Health Checks (`app/core/health.py`)

**Endpoints:**
- `/health` - Basic liveness check
- `/ready` - Readiness check (DB + Redis)

### 5. Caching (`app/core/cache.py`)

**Cache Strategy:**
- Redis-based distributed cache
- Different TTLs per entity type:
  - Course: 120 seconds
  - Lesson: 120 seconds  
  - Quiz: 120 seconds

### 6. Observability (`app/core/observability.py`)

**Sentry Integration:**
- Error tracking
- Performance monitoring
- Release tracking
- Separate config for Celery workers

---

## Feature Modules

### Module Architecture Pattern

Each module follows consistent structure:
```
module_name/
├── __init__.py
├── models.py           # SQLAlchemy models
├── schemas.py          # Pydantic request/response schemas
├── router.py           # FastAPI routes
├── service.py          # Business logic
├── repository.py      # Data access (optional)
└── storage/           # Storage backends (for files)
```

### 1. Authentication Module (`app/modules/auth/`)

**Features:**
- JWT-based authentication
- Cookie-based auth (production)
- Access + Refresh token pattern
- MFA (TOTP) support
- Account lockout after failed attempts
- Email verification
- Password reset flow

**Files:**
- `models.py` - Token models
- `schemas.py` - Auth request/response schemas
- `router.py` - API endpoints (development)
- `router_cookie.py` - Cookie-based endpoints (production)
- `service.py` - Authentication logic
- `service_cookie.py` - Cookie-specific logic
- `schemas_cookie.py` - Cookie-specific schemas

### 2. Users Module (`app/modules/users/`)

**Features:**
- User CRUD operations
- Profile management
- Role-based access (admin, instructor, student)
- Password change/reset

### 3. Courses Module (`app/modules/courses/`)

**Features:**
- Course creation and management
- Lesson organization
- Course categories
- Prerequisites
- Publishing workflow

**Sub-modules:**
- `services/course_service.py`
- `services/lesson_service.py`
- `repositories/course_repository.py`
- `repositories/lesson_repository.py`

### 4. Enrollments Module (`app/modules/enrollments/`)

**Features:**
- Student enrollment
- Progress tracking
- Completion status

### 5. Quizzes Module (`app/modules/quizzes/`)

**Features:**
- Quiz creation
- Question types (multiple choice)
- Answer validation
- Attempt tracking
- Scoring

**Structure:**
- `models/quiz.py`, `models/question.py`, `models/attempt.py`
- `services/quiz_service.py`, `question_service.py`, `attempt_service.py`
- `repositories/quiz_repository.py`, `attempt_repository.py`

### 6. Files Module (`app/modules/files/`)

**Features:**
- File upload/download
- Local storage (default)
- Azure Blob storage (production)
- Signed URLs for secure access
- MIME type validation

**Storage Abstraction:**
```python
# Base class
class BaseStorage(ABC):
    @abstractmethod
    def upload(self, file_data, path): ...
    @abstractmethod
    def download(self, path): ...
    @abstractmethod
    def get_signed_url(self, path, expiry): ...

# Implementations
class LocalStorage(BaseStorage): ...
class AzureBlobStorage(BaseStorage): ...
```

### 7. Certificates Module (`app/modules/certificates/`)

**Features:**
- Auto-generation on course completion
- PDF generation with fpdf2
- Unique certificate IDs
- Downloadable PDFs

### 8. Analytics Module (`app/modules/analytics/`)

**Features:**
- Student analytics (progress, quiz scores)
- Instructor analytics (course performance)
- System analytics (usage stats)

---

## Background Tasks (Celery)

### Architecture (`app/tasks/`)

**Why Celery?**
- Asynchronous task processing
- Distributed execution
- Multiple queue support
- Retry mechanisms
- Scheduled tasks (beat)

### Task Queues

| Queue | Purpose | Tasks |
|-------|---------|-------|
| `emails` | Email delivery | Welcome, password reset, enrollment |
| `progress` | Progress calculations | Enrollment progress updates |
| `certificates` | PDF generation | Certificate creation |
| `webhooks` | External integrations | Event notifications |

### Task Configuration

```python
celery_app.conf.update(
    task_routes={...},
    task_acks_late=True,           # Ack after processing
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1, # Fair scheduling
    task_time_limit=300,          # Hard limit
    task_soft_time_limit=240,     # Graceful cancellation
)
```

### Task Files

1. **email_tasks.py**
   - Send welcome emails
   - Password reset emails
   - Enrollment notifications
   - Certificate notification

2. **progress_tasks.py**
   - Recalculate enrollment progress
   - Update lesson completion status

3. **certificate_tasks.py**
   - Generate PDF certificates
   - Queue certificate downloads

4. **webhook_tasks.py**
   - Dispatch webhook events
   - Retry failed webhooks

---

## Docker and Deployment

### Development (`docker-compose.yml`)

```yaml
services:
  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes: .:/app
    depends_on: [db, redis]
  
  celery-worker:
    command: celery -A app.tasks.celery_app.celery_app worker --loglevel=info
  
  celery-beat:
    command: celery -A app.tasks.celery_app.celery_app beat --loglevel=info
  
  db:
    image: postgres:16-alpine
    volumes: postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
```

**Why This Setup?**
- Hot reload for development
- Separate worker containers for background tasks
- Named volumes for data persistence

### Production (`docker-compose.prod.yml`)

```yaml
services:
  migrate:
    command: alembic upgrade head
    restart: "no"
  
  api:
    user: "0:0"                    # Run as non-root
    command: uvicorn --workers ${UVICORN_WORKERS:-2}
    healthcheck: enabled
    restart: unless-stopped
  
  celery-worker:
    user: "0:0"
    restart: unless-stopped
  
  celery-beat:
    user: "0:0"
    volumes: celerybeat_data:/tmp
    restart: unless-stopped
  
  caddy:
    image: caddy:2-alpine
    ports: [80:80, 443:443]
    volumes: ./ops/caddy/Caddyfile:/etc/caddy/Caddyfile:ro
    restart: unless-stopped
  
  redis:
    image: redis:7-alpine
    healthcheck: enabled
    restart: unless-stopped
```

**Production Considerations:**
- Non-root user (security)
- Multiple workers (performance)
- Health checks (reliability)
- Caddy for HTTPS/TLS
- Volume mounts for persistence

### Staging (`docker-compose.staging.yml`)

- Similar to production but with staging-specific configs
- Separate database (`lms_staging`)
- Port 8001 (vs 8000 in dev)

### Observability (`docker-compose.observability.yml`)

- Prometheus for metrics
- Grafana for visualization
- Alertmanager for alerts

---

## CI/CD Pipeline (.github/workflows)

### 1. Continuous Integration (`ci.yml`)

**Triggers:**
- Push to main, develop, feature/**, chore/**
- Pull requests to main, develop

**Jobs:**

```yaml
test:
  runs-on: ubuntu-latest
  strategy:
    matrix:
      python-version: ["3.11", "3.12"]
  
  steps:
  - Checkout
  - Setup Python (with pip cache)
  - Install dependencies
  - Static sanity checks:
    - compileall (syntax check)
    - pip check (dependency issues)
    - Generate Postman collection
    - Validate JSON files
  - Run tests with coverage:
    pytest --cov=app --cov-report=term-missing --cov-fail-under=75

test-postgres:
  # Integration tests with real PostgreSQL
  # Tests against Python 3.12 only
```

**Why These Steps?**
- Multiple Python versions for compatibility
- Static checks catch issues early
- 75% minimum coverage requirement
- Integration tests with real DB

### 2. Security Scanning (`security.yml`)

**Triggers:**
- Push to main, develop
- Pull requests to main, develop
- Weekly schedule (Monday 3 AM)
- Manual dispatch

**Scans:**

```yaml
# Dependency vulnerability scan
pip-audit -r requirements.txt --strict

# Static security scan
bandit -r app scripts -x tests -lll -ii

# Secret scanning
gitleaks/gitleaks-action@v2
```

**Why These Scans?**
- **pip-audit**: Known CVEs in dependencies
- **bandit**: Common security issues in Python code
- **gitleaks**: Accidental secret commits

### 3. Azure VM Deployment (`deploy-azure-vm.yml`)

**Triggers:**
- Push to main
- Manual dispatch

**Process:**

```yaml
# 1. Create release archive
git archive --format=tar.gz -o release.tar.gz HEAD

# 2. Upload to VM (SCP)
appleboy/scp-action

# 3. Deploy (SSH)
# - Extract archive
# - Run deploy script
# - Pass environment variables
```

**Environment Variables:**
- `PROD_DATABASE_URL`
- `SECRET_KEY`
- `APP_DOMAIN`
- `SMTP_*` settings
- `SENTRY_DSN`

---

## Operations Infrastructure (ops/)

### 1. Caddy Reverse Proxy (`ops/caddy/Caddyfile`)

```caddy
{
    email {$LETSENCRYPT_EMAIL}
}

{$APP_DOMAIN} {
    encode zstd gzip
    reverse_proxy api:8000
}
```

**Why Caddy?**
- Automatic HTTPS (Let's Encrypt)
- HTTP/3 support
- Simple configuration
- Automatic TLS certificate renewal
- Gzip/Brotli compression

**Configuration Features:**
- ACME email for certificate notifications
- Domain-based routing
- Built-in compression
- Reverse proxy to API

### 2. Observability Stack (`ops/observability/`)

#### Prometheus (`ops/observability/prometheus/`)

**prometheus.yml:**
```yaml
scrape_configs:
  - job_name: prometheus      # Self-monitoring
  - job_name: lms_api_prod   # Production API
  - job_name: lms_api_staging # Staging API
```

**alerts.yml:**
- **LMSApiDown**: API target unreachable (2m)
- **LMSHighErrorRate**: 5xx errors > 5% (10m)
- **LMSHighP95Latency**: p95 latency > 750ms (10m)
- **LMSRateLimitSpike**: 429 responses > 2/sec (10m)

#### Grafana (`ops/observability/grafana/`)

**Dashboards:**
1. `lms-api-overview.json` - API metrics
2. `lms-course-performance.json` - Course analytics
3. `lms-student-progress.json` - Student tracking
4. `lms-security-events.json` - Security monitoring
5. `lms-system-health.json` - System health

**Provisioning:**
- `datasources/prometheus.yml` - Prometheus connection
- `dashboards/dashboards.yml` - Dashboard definitions

#### Alertmanager (`ops/observability/alertmanager/`)

**alertmanager.yml:**
- Route alerts to appropriate receivers
- Group similar alerts
- Configure notification receivers (email, Slack, etc.)

---

## Security Implementation

### Authentication Security

1. **JWT Tokens**
   - Short-lived access tokens (15 min)
   - Long-lived refresh tokens (30 days)
   - Token blacklist for revocation
   - Multiple token types

2. **Password Security**
   - Bcrypt hashing (cost factor 12)
   - Password strength validation
   - Secure password reset flow

3. **Account Protection**
   - Failed login lockout (5 attempts)
   - MFA support (TOTP)
   - Email verification required option

### API Security

1. **Rate Limiting**
   - Global: 100 req/min
   - Auth paths: 60 req/min
   - File uploads: 100 req/hour
   - Per-IP and per-user modes

2. **CORS Configuration**
   - Configurable allowed origins
   - Credentials support

3. **Security Headers**
   - HSTS (HTTP Strict Transport Security)
   - X-Frame-Options (clickjacking protection)
   - X-Content-Type-Options
   - Content Security Policy

4. **Trusted Hosts**
   - Host header validation
   - Prevents host header injection

### Infrastructure Security

1. **Non-root Containers**
   - Production runs as `nobody` user
   - Minimal container privileges

2. **Secrets Management**
   - HashiCorp Vault integration
   - Azure Key Vault support
   - Environment variable fallback

3. **Network Security**
   - Internal service communication
   - Exposed only necessary ports

---

## API Design and Endpoints

### API Structure

```
/api/v1/
├── /health              # Health check
├── /ready              # Readiness check
├── /auth/              # Authentication
│   ├── /register       # User registration
│   ├── /login          # Login
│   ├── /logout        # Logout
│   ├── /token          # Token refresh
│   ├── /mfa/*         # MFA endpoints
│   └── /password/*    # Password reset
├── /users/             # User management
├── /courses/           # Course management
├── /lessons/           # Lesson management
├── /enrollments/       # Enrollment management
├── /quizzes/           # Quiz management
├── /questions/         # Question management
├── /attempts/          # Quiz attempts
├── /files/             # File management
├── /certificates/      # Certificate management
└── /analytics/         # Analytics endpoints
```

### Design Principles

1. **RESTful Conventions**
   - Proper HTTP methods (GET, POST, PUT, DELETE)
   - Resource-based URLs
   - Status codes

2. **Response Envelope** (configurable)
   ```json
   {
     "message": "Success",
     "data": { ... }
   }
   ```

3. **Pagination**
   - Offset-based pagination
   - Consistent response format

4. **Error Handling**
   - Custom exception handlers
   - Structured error responses

---

## Summary

This LMS Backend project demonstrates a production-ready architecture with:

- **Modern Tech Stack**: FastAPI, PostgreSQL, Redis, Celery
- **Comprehensive Security**: JWT, MFA, rate limiting, security headers
- **Observability**: Prometheus, Grafana, Sentry, Alertmanager
- **CI/CD**: Automated testing, security scanning, deployment
- **Production-Ready**: Health checks, error handling, monitoring
- **Developer Experience**: Hot reload, API docs, clear structure

The modular architecture allows for easy extension and future microservices migration if needed.
