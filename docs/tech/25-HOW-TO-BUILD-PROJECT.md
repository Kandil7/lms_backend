# How to Build the LMS Backend Project - Complete Guide

This comprehensive guide explains exactly how to build, configure, and run the LMS Backend project from scratch. Every step is documented with explanations of why each action is necessary.

---

## Table of Contents

1. [Prerequisites and Environment Setup](#1-prerequisites-and-environment-setup)
2. [Project Initialization](#2-project-initialization)
3. [Database Configuration](#3-database-configuration)
4. [Application Configuration](#4-application-configuration)
5. [Running the Application](#5-running-the-application)
6. [Background Services](#6-background-services)
7. [Verification and Testing](#7-verification-and-testing)
8. [Optional: Adding Demo Data](#8-optional-adding-demo-data)

---

## 1. Prerequisites and Environment Setup

### 1.1 Required Software

Before building this project, you need to install the following software:

| Software | Version Required | Purpose | Installation Link |
|----------|-----------------|---------|-------------------|
| **Python** | 3.11 or higher | Runtime environment | https://www.python.org/downloads/ |
| **PostgreSQL** | 14 or higher | Primary database | https://www.postgresql.org/download/ |
| **Redis** | 7 or higher | Cache & message broker | https://redis.io/download |
| **Docker** | Latest | Containerization | https://docs.docker.com/get-docker/ |
| **Docker Compose** | Latest | Service orchestration | Included with Docker Desktop |

### 1.2 Why These Prerequisites?

**Why Python 3.11+?**
- This project uses modern Python features like type hints, dataclasses, and structural pattern matching
- FastAPI requires Python 3.9+ for optimal performance
- SQLAlchemy 2.0 has better async support with Python 3.11+

**Why PostgreSQL?**
- ACID compliance is critical for financial and educational data
- JSONB support allows flexible metadata storage
- Excellent indexing for complex queries
- The project uses PostgreSQL-specific features like UUID types

**Why Redis?**
- Dual purpose: caching AND message broker (saves infrastructure costs)
- Pub/sub for Celery task distribution
- Used for rate limiting and session management
- Extremely fast in-memory operations

**Why Docker?**
- Ensures consistent environment across development and production
- Simplifies complex multi-service setup
- Same as production environment

### 1.3 Installing Prerequisites

#### Windows (using Winget)

```powershell
# Install Python
winget install Python.Python.3.11

# Install Docker Desktop (includes Docker Compose)
# Download from https://www.docker.com/products/docker-desktop
```

#### macOS (using Homebrew)

```bash
# Install Python
brew install python@3.11

# Install PostgreSQL
brew install postgresql@14

# Install Redis
brew install redis

# Install Docker
# Download from https://www.docker.com/products/docker-desktop
```

#### Linux (Ubuntu/Debian)

```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.11 python3.11-venv python3.11-dev

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Install Redis
sudo apt install redis-server

# Install Docker
sudo apt install docker.io docker-compose
```

---

## 2. Project Initialization

### 2.1 Clone the Repository

```bash
git clone <repository-url>
cd lms_backend
```

### 2.2 Create Virtual Environment

**Why use a virtual environment?**
- Isolates project dependencies from system Python
- Prevents version conflicts between projects
- Makes it easy to reproduce and share environments

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2.3 Install Dependencies

```bash
pip install -r requirements.txt
```

**What does requirements.txt contain?**

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.115.0 | Web framework |
| uvicorn[standard] | >=0.34.0 | ASGI server |
| sqlalchemy | >=2.0.36 | ORM |
| alembic | >=1.14.0 | Database migrations |
| psycopg2-binary | >=2.9.10 | PostgreSQL driver |
| pydantic-settings | >=2.7.1 | Configuration management |
| python-jose[cryptography] | >=3.3.0 | JWT token handling |
| passlib[bcrypt] | >=1.7.4 | Password hashing |
| redis | >=5.2.1 | Redis client |
| prometheus-client | >=0.20.0 | Metrics |
| sentry-sdk[fastapi] | >=2.18.0 | Error tracking |
| celery | >=5.4.0 | Background tasks |
| flower | >=2.0.1 | Celery monitoring |
| boto3 | ==1.42.51 | AWS S3 SDK |
| jinja2 | >=3.1.5 | Email templates |
| fastapi-mail | >=1.4.1 | Email sending |
| fpdf2 | >=2.8.2 | PDF generation |
| httpx | >=0.28.1 | HTTP client for tests |
| pytest | >=8.3.4 | Testing framework |
| pytest-asyncio | >=0.25.0 | Async testing |
| pytest-cov | >=6.0.0 | Code coverage |
| faker | >=33.1.0 | Fake data for tests |

---

## 3. Database Configuration

### 3.1 Option A: Using Docker (Recommended)

The easiest way to set up PostgreSQL and Redis is using Docker:

```bash
# Start only the database services
docker-compose up -d db redis
```

This creates:
- PostgreSQL container on port 5432
- Redis container on port 6379

**Why Docker for database?**
- No manual installation required
- Easy to reset and recreate
- Same configuration as production
- Cross-platform consistency

### 3.2 Option B: Local PostgreSQL Installation

If you prefer local installation:

```bash
# Start PostgreSQL service
# Windows (using pg_ctl)
pg_ctl -D "C:\Program Files\PostgreSQL\14\data" start

# Linux/Mac
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE USER lms WITH PASSWORD 'lms';
CREATE DATABASE lms OWNER lms;
GRANT ALL PRIVILEGES ON DATABASE lms TO lms;
```

### 3.3 Database Connection Settings

The default connection string in `.env`:

```
DATABASE_URL=postgresql+psycopg2://lms:lms@localhost:5432/lms
```

**Connection string breakdown:**
```
postgresql+psycopg2://  [Protocol: psycopg2 is synchronous driver]
lms:lms@               [Username:Password]
localhost:5432/        [Host:Port]
lms                    [Database name]
```

**Why psycopg2?**
- Most mature PostgreSQL driver for Python
- Supports Postgre allSQL features
- Binary version (psycopg2-binary) has no compilation requirements

---

## 4. Application Configuration

### 4.1 Create Environment File

```bash
# Copy example environment file
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac
```

### 4.2 Essential Configuration Variables

Edit the `.env` file with these essential settings:

```env
# =====================
# APPLICATION SETTINGS
# =====================
PROJECT_NAME=LMS Backend
VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# =====================
# SECURITY - IMPORTANT
# =====================
# Generate a secure secret key:
# Open Python: python
# >>> import secrets
# >>> secrets.token_hex(32)
SECRET_KEY=your-64-character-hex-string-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# =====================
# DATABASE
# =====================
DATABASE_URL=postgresql+psycopg2://lms:lms@localhost:5432/lms

# =====================
# REDIS
# =====================
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# =====================
# API SETTINGS
# =====================
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000

# =====================
# FILE STORAGE
# =====================
FILE_STORAGE_PROVIDER=local
UPLOAD_DIR=uploads
CERTIFICATES_DIR=certificates
MAX_UPLOAD_MB=100
```

### 4.3 Generate Secure Secret Key

```python
# Run this to generate a secure key
python -c "import secrets; print(secrets.token_hex(32))"
```

**Why is SECRET_KEY important?**
- Used to sign JWT tokens
- If compromised, attackers can create valid tokens
- Must be kept secret in production
- Must be consistent across restarts (tokens depend on it)

### 4.4 Understanding Configuration Design

**Why Pydantic Settings?**
- Type validation of environment variables
- Automatic type conversion
- Documentation through type hints
- IDE autocomplete support
- Default values with validation

The configuration system in `app/core/config.py` provides:
- Environment-based configuration
- Validation of required fields
- Production safety checks
- Computed properties for derived settings

---

## 5. Running the Application

### 5.1 Initialize Database Schema

Before running the application, create the database tables:

```bash
# Apply all migrations
alembic upgrade head
```

**What does alembic do?**
- Reads migration files from `alembic/versions/`
- Creates tables based on model definitions
- Tracks which migrations have been applied
- Allows rolling back changes

**Migration files included:**
| Migration | Description |
|-----------|-------------|
| 0001_initial_schema.py | Users, courses, lessons, enrollments |
| 0002_phase1_security_and_performance.py | Security indexes |
| 0003_phase1_infrastructure_indexes.py | Performance indexes |
| 0004_phase1_quiz_indexes.py | Quiz system indexes |
| 0005_phase1_remaining_indexes.py | Final indexes |
| 0006_add_users_email_verified_at.py | Email verification |
| 0007_add_users_mfa_enabled.py | MFA support |
| 0008_add_payments_module.py | Payment tables |

### 5.2 Start the API Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**What does this command do?**
```
uvicorn          # ASGI server implementation
app.main:app     # Import path to FastAPI application
--reload         # Auto-restart on code changes (development only)
--host 0.0.0.0   # Listen on all network interfaces
--port 8000     # HTTP port
```

**Alternative: Using Python module syntax**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5.3 Verify the Server is Running

Open your browser and navigate to:

| URL | Description |
|-----|-------------|
| http://localhost:8000 | Root endpoint - returns basic info |
| http://localhost:8000/docs | Swagger API documentation |
| http://localhost:8000/redoc | ReDoc alternative documentation |
| http://localhost:8000/openapi.json | OpenAPI schema JSON |
| http://localhost:8000/api/v1/health | Health check endpoint |
| http://localhost:8000/api/v1/ready | Readiness check (includes DB/Redis) |

**Expected responses:**

```json
// GET /
{"message": "LMS Backend API"}

// GET /api/v1/health
{"status": "ok"}

// GET /api/v1/ready
{
  "status": "ok",
  "database": "up",
  "redis": "up"
}
```

---

## 6. Background Services

The LMS Backend uses Celery for background tasks. These include:
- Sending emails
- Generating certificates
- Processing webhooks
- Calculating progress

### 6.1 Start Celery Worker

```bash
# Start Celery worker (handles background tasks)
celery -A app.tasks.celery_app.celery_app worker --loglevel=info --queues=emails,progress,certificates
```

**What does this do?**
```
celery                    # Celery command
-A app.tasks.celery_app   # Application module
worker                    # Run as worker process
--loglevel=info          # Logging level
--queues=emails,progress,certificates  # Process these queues
```

**Why separate queues?**
- Different task types have different resource needs
- Can scale workers independently
- Prioritize critical tasks

### 6.2 Start Celery Beat (Scheduler)

```bash
# Start Celery Beat (scheduled tasks)
celery -A app.tasks.celery_app.celery_app beat --loglevel=info
```

**What scheduled tasks exist?**

| Task | Schedule | Purpose |
|------|----------|---------|
| send_weekly_progress_report | Monday 9:00 AM | Email students their progress |
| send_course_reminders | Daily 10:00 AM | Reminder for inactive students |

### 6.3 Start Flower (Monitoring)

```bash
# Start Flower (Celery monitoring UI)
celery -A app.tasks.celery_app.celery_app flower --port=5555
```

Access at: http://localhost:5555

---

## 7. Verification and Testing

### 7.1 Run Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run tests matching pattern
pytest -k "test_login"

# Run with verbose output
pytest -vv
```

### 7.2 Test Coverage by Module

| Test File | Coverage |
|-----------|----------|
| tests/test_auth.py | Registration, login, logout, tokens |
| tests/test_courses.py | Course CRUD, publishing |
| tests/test_quizzes.py | Quiz creation, attempts, grading |
| tests/test_enrollments.py | Enrollment, progress tracking |
| tests/test_payments.py | Payment processing, webhooks |
| tests/test_certificates.py | Certificate generation |
| tests/test_emails.py | Email sending |
| tests/test_files.py | File upload/download |
| tests/test_permissions.py | Role-based access control |

### 7.3 Smoke Test Script

```bash
# Run smoke tests
python scripts/smoke_prod_like.py
```

---

## 8. Optional: Adding Demo Data

### 8.1 Create Demo Data

```bash
# Create demo users, courses, and enrollments
python scripts/seed_demo_data.py
```

### 8.2 Create Admin User

```bash
# Create admin user
python scripts/create_admin.py --email admin@example.com --password admin123 --name "Admin User"
```

---

## Complete Development Stack

After following all steps, you should have running:

| Service | URL | Purpose |
|---------|-----|---------|
| API Server | http://localhost:8000 | Main application |
| Swagger Docs | http://localhost:8000/docs | API documentation |
| Flower | http://localhost:5555 | Celery monitoring |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache/Message Broker |

---

## Troubleshooting

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'app'` | Virtual environment not activated | Run `source venv/bin/activate` |
| `could not connect to server` | PostgreSQL not running | Run `docker-compose up -d db` |
| `Error 111 connecting to Redis` | Redis not running | Run `docker-compose up -d redis` |
| `relation "users" does not exist` | Migrations not run | Run `alembic upgrade head` |
| `Port already in use` | Port 8000 in use | Use `--port 8001` or kill process |

### Getting Help

1. Check health endpoints: `/api/v1/health`, `/api/v1/ready`
2. Review application logs
3. Check Celery worker logs
4. Verify database and Redis connectivity

---

## Next Steps

After successfully building the project:

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Read the Architecture Guide**: See docs/tech/02-architecture-decisions.md
3. **Understand the Database**: See docs/tech/05-database-design.md
4. **Configure for Production**: See docs/tech/10-deployment-guide.md
5. **Set up Monitoring**: See docs/tech/22-observability-metrics.md

---

## Summary

This guide covered:

1. **Prerequisites**: Python 3.11+, PostgreSQL, Redis, Docker
2. **Project Setup**: Virtual environment, dependencies
3. **Database**: PostgreSQL via Docker or local
4. **Configuration**: Environment variables, SECRET_KEY
5. **Running**: API server, Celery workers, Beat scheduler
6. **Testing**: pytest, coverage, smoke tests
7. **Demo Data**: Seed scripts, admin creation

The project is now ready for development. Happy coding!
