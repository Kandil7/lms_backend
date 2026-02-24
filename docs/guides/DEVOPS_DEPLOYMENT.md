# DevOps & Deployment Handbook

This guide is for DevOps engineers and developers responsible for maintaining the production infrastructure of the EduConnect Pro LMS.

---

## 📋 Table of Contents
1. [Infrastructure Overview](#1-infrastructure-overview)
2. [Environment Configuration](#2-environment-configuration)
3. [Deployment Workflows](#3-deployment-workflow)
4. [CI/CD Pipelines](#4-cicd-pipelines)
5. [Database Maintenance](#5-database-maintenance)
6. [Scaling & High Availability](#6-scaling--high-availability)

---

## 1. Infrastructure Overview
The system is built to be cloud-agnostic but is currently optimized for **Azure VM** or **AWS EC2**.

- **App Server**: FastAPI running inside Docker.
- **Database**: Azure PostgreSQL Flexible Server (managed).
- **Cache**: Azure Cache for Redis (managed).
- **Reverse Proxy**: Caddy (for automatic SSL and load balancing).
- **Storage**: Azure Blob Storage (for course materials and certificates).

---

## 2. Environment Configuration
We use `.env` files to manage secrets and settings.

### Key Variables:
- `ENVIRONMENT`: `development`, `staging`, or `production`.
- `DATABASE_URL`: Connection string for PostgreSQL.
- `SECRET_KEY`: Used for signing JWTs (keep this safe!).
- `CORS_ORIGINS`: JSON list of allowed frontend domains.
- `ENABLE_API_DOCS`: Set to `false` in production for security.

---

## 3. Deployment Workflow
We use **Docker Compose** for orchestration.

### Initial Setup:
```bash
# Clone the repo
git clone <repo_url>
cd lms_backend

# Setup production environment
cp .env.production.example .env

# Build and start
docker-compose -f docker-compose.prod.yml up -d --build
```

### Updates (Zero Downtime):
1. Pull latest code.
2. Run migrations: `alembic upgrade head`.
3. Build new image.
4. Restart containers one by one or use a blue-green strategy.

---

## 4. CI/CD Pipelines
Located in `.github/workflows/`:

- **CI (`ci.yml`)**: Runs Linting (Ruff), Type-checking (Mypy), and PyTest on every push.
- **Security (`security.yml`)**: Scans for vulnerabilities in dependencies.
- **Deploy (`deploy-azure-vm.yml`)**: Automatically deploys to the production server when a release tag is created.

---

## 5. Database Maintenance

### Backups:
- Managed by Azure PostgreSQL with a 7-day retention period.
- Manual dumps can be taken using `pg_dump`:
  ```bash
  pg_dump $DATABASE_URL > backup.sql
  ```

### Migrations:
Always run migrations *before* deploying new code to avoid "column does not exist" errors in the active API.

---

## 6. Scaling & High Availability

### API Scaling:
Increase the number of API workers in the Docker config or scale the number of container instances behind a load balancer.

### Worker Scaling:
Heavy background tasks? Scale the `celery_worker` service independently:
```bash
docker-compose up -d --scale celery_worker=10
```

---

## 🚨 Emergency Procedures
- **Rollback Code**: Revert the Git commit and rebuild the Docker image.
- **Rollback DB**: `alembic downgrade -1` (Warning: may cause data loss).
- **Flush Cache**: `redis-cli FLUSHALL` (if Redis state is causing issues).
- **View Logs**: `docker-compose logs -f --tail=100 api`
