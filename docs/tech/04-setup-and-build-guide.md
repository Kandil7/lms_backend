# Setup and Build Guide

This comprehensive guide explains how to set up, configure, and build this LMS Backend project from scratch.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project Setup](#2-project-setup)
3. [Environment Configuration](#3-environment-configuration)
4. [Database Setup](#4-database-setup)
5. [Running the Application](#5-running-the-application)
6. [Docker Development](#6-docker-development)
7. [Building for Production](#7-building-for-production)
8. [Verification Steps](#8-verification-steps)
9. [Common Issues](#9-common-issues)

---

## 1. Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.11+ | Runtime |
| **PostgreSQL** | 14+ | Database |
| **Redis** | 7+ | Cache & Message Broker |
| **Docker** | Latest | Containerization |
| **Docker Compose** | Latest | Orchestration |

### Installing Prerequisites

#### Python (Windows)
```powershell
# Download from https://www.python.org/downloads/
# OR use winget
winget install Python.Python.3.11

# Verify installation
python --version
```

#### PostgreSQL (Windows)
```powershell
# Option 1: Download from https://www.postgresql.org/download/windows/
# Option 2: Use Docker (recommended - see below)
```

#### Redis (Windows)
```powershell
# Option 1: Use Memurai or Redis Windows port
# Option 2: Use Docker (recommended - see below)
```

---

## 2. Project Setup

### Clone the Project
```bash
git clone <repository-url>
cd lms_backend
```

### Create Virtual Environment

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
python -m venv venv
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 3. Environment Configuration

### Create Environment File

Copy the example environment file:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### Configure Environment Variables

Edit `.env` with your settings:

```env
# =====================
# APPLICATION SETTINGS
# =====================
PROJECT_NAME=LMS Backend
VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
API_V1_PREFIX=/api/v1

# =====================
# DATABASE
# =====================
DATABASE_URL=postgresql+asyncpg://lms:lms@localhost:5432/lms
# For sync operations (Alembic):
DATABASE_URL_SYNC=postgresql+psycopg2://lms:lms@localhost:5432/lms
SQLALCHEMY_ECHO=false
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# =====================
# SECURITY
# =====================
# Generate a secure secret key:
# python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-super-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30

# =====================
# REDIS
# =====================
REDIS_URL=redis://localhost:6379/0

# =====================
# EMAIL (SMTP)
# =====================
EMAIL_FROM=noreply@example.com
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
SMTP_USE_SSL=false

# =====================
# FILE STORAGE
# =====================
FILE_STORAGE_PROVIDER=local
UPLOAD_DIR=uploads
CERTIFICATES_DIR=certificates
MAX_UPLOAD_MB=100
ALLOWED_UPLOAD_EXTENSIONS=.jpg,.jpeg,.png,.pdf,.mp4,.webm,.txt,.doc,.docx

# AWS S3 (optional)
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# AWS_REGION=us-east-1
# AWS_S3_BUCKET=
# AWS_S3_BUCKET_URL=

# =====================
# CACHING
# =====================
CACHE_ENABLED=true
CACHE_DEFAULT_TTL_SECONDS=120
COURSE_CACHE_TTL_SECONDS=3600
LESSON_CACHE_TTL_SECONDS=1800

# =====================
# RATE LIMITING
# =====================
RATE_LIMIT_USE_REDIS=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_WINDOW_SECONDS=60

# =====================
# CORS
# =====================
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# =====================
# CELERY
# =====================
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TASK_ALWAYS_EAGER=false
TASKS_FORCE_INLINE=true  # Set to false in production
```

---

## 4. Database Setup

### Option A: Docker (Recommended)

Start PostgreSQL and Redis using Docker:

```bash
docker-compose up -d db redis
```

### Option B: Local Installation

Create the database manually:

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create user and database
CREATE USER lms WITH PASSWORD 'lms';
CREATE DATABASE lms OWNER lms;
GRANT ALL PRIVILEGES ON DATABASE lms TO lms;
```

### Run Migrations

Generate the initial migration and apply it:

```bash
# Apply all migrations
alembic upgrade head

# Or apply step by step
alembic upgrade +1

# Check current version
alembic current

# See migration history
alembic history
```

### Create Initial Data (Optional)

Run the seed script to create initial data:

```bash
python scripts/seed_data.py
```

---

## 5. Running the Application

### Development Mode

#### Start the API Server

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the run script
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Start Celery Worker (for background tasks)

```bash
# Start Celery worker
celery -A app.tasks.celery_app worker -l info

# Or use the provided script (if available)
python scripts/run_celery_worker.py
```

#### Start Celery Beat (for scheduled tasks)

```bash
celery -A app.tasks.celery_app beat -l info
```

### Verify Application

Open your browser and navigate to:

| URL | Description |
|-----|-------------|
| `http://localhost:8000` | Root endpoint |
| `http://localhost:8000/docs` | Swagger API documentation |
| `http://localhost:8000/redoc` | ReDoc documentation |
| `http://localhost:8000/api/v1/health` | Health check |
| `http://localhost:8000/api/v1/ready` | Readiness check |

---

## 6. Docker Development

### Start All Services

```bash
# Start all services (API, Celery, PostgreSQL, Redis)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Service Breakdown

| Service | Port | Description |
|---------|------|-------------|
| `api` | 8000 | FastAPI application |
| `celery-worker` | - | Background task worker |
| `celery-beat` | - | Task scheduler |
| `db` | 5432 | PostgreSQL database |
| `redis` | 6379 | Redis cache/broker |

### Docker Commands

```bash
# Rebuild containers
docker-compose build

# View logs for specific service
docker-compose logs -f api
docker-compose logs -f celery-worker

# Restart a service
docker-compose restart api

# Access container shell
docker-compose exec api bash
docker-compose exec db psql -U lms
```

---

## 7. Building for Production

### Production Docker Compose

```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up -d --build
```

### Production Environment Variables

Set these critical variables in production:

```env
# SECURITY (REQUIRED)
SECRET_KEY=<generate-secure-key>
DEBUG=false
ENVIRONMENT=production

# DATABASE
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/lms

# REDIS
REDIS_URL=redis://prod-redis:6379/0

# PRODUCTION SETTINGS
CELERY_TASK_ALWAYS_EAGER=false
RATE_LIMIT_USE_REDIS=true

# EMAIL
SMTP_HOST=<production-smtp-host>
SMTP_USERNAME=<username>
SMTP_PASSWORD=<password>
```

### Building Docker Image

```bash
# Build the image
docker build -t lms-backend:latest .

# Or build with no cache
docker build --no-cache -t lms-backend:latest .
```

---

## 8. Verification Steps

### 1. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 2. Database Connection

```bash
curl http://localhost:8000/api/v1/ready
```

Expected response:
```json
{
  "database": "connected",
  "redis": "connected"
}
```

### 3. API Documentation

Navigate to:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py
```

---

## 9. Common Issues

### Issue: Database Connection Error

**Error:** `could not connect to server: Connection refused`

**Solution:**
1. Check if PostgreSQL is running: `docker ps` or check services
2. Verify DATABASE_URL in `.env`
3. Ensure database exists: `psql -U lms -l`

---

### Issue: Redis Connection Error

**Error:** `Error 111 connecting to localhost:6379`

**Solution:**
1. Start Redis: `docker-compose up -d redis`
2. Or install Redis locally

---

### Issue: Migration Errors

**Error:** `relation "table_name" does not exist`

**Solution:**
```bash
# Run migrations
alembic upgrade head
```

---

### Issue: Port Already in Use

**Error:** `Error: bind: address already in use`

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process
taskkill /PID <process_id> /F

# Or use different port
uvicorn app.main:app --port 8001
```

---

### Issue: Import Errors

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
1. Ensure virtual environment is activated
2. Install dependencies: `pip install -r requirements.txt`
3. Check Python path

---

## Quick Start Summary

```bash
# 1. Clone and setup
git clone <repo>
cd lms_backend
python -m venv venv
.\venv\Scripts\Activate

# 2. Install and configure
pip install -r requirements.txt
copy .env.example .env

# 3. Start infrastructure
docker-compose up -d db redis

# 4. Run migrations
alembic upgrade head

# 5. Start application
uvicorn app.main:app --reload
```

---

## Next Steps

After setup, you may want to:

1. **Explore the API** - Visit `/docs` endpoint
2. **Run tests** - `pytest`
3. **Add data** - Use the admin panel or API
4. **Configure production** - See deployment guide
