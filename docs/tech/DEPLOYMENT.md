# Deployment Guide

This document provides comprehensive deployment instructions for the LMS Backend.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Local Development](#local-development)
4. [Staging Deployment](#staging-deployment)
5. [Production Deployment](#production-deployment)
6. [Azure Deployment](#azure-deployment)
7. [Post-Deployment](#post-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Disk | 20 GB | 50+ GB |
| Docker | 20. |
| Docker Compose | 210+ | Latest.0+ | Latest |
| Python | 3.11 | 3.11 |

### Required Accounts

- [ ] Docker Hub (for base images)
- [ ] Azure Account (for production)
- [ ] SMTP Provider (SendGrid, AWS SES, etc.)
- [ ] Stripe Account (for payments)

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/lms-backend.git
cd lms-backend
```

### 2. Environment Configuration

Create environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Project
PROJECT_NAME=LMS Backend
VERSION=1.0.0
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+psycopg2://lms:lms@localhost:5432/lms

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# Security
SECRET_KEY=your-secret-key-min-32-chars-change-this
ALGORITHM=HS256
```

### 3. Install Dependencies

```bash
# Using uv (recommended)
pip install uv
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

---

## Local Development

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- API (port 8000)
- Celery Worker
- Celery Beat

### Option 2: Local Development Server

```bash
# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis (via Docker)
docker run -d --name postgres -e POSTGRES_USER=lms -e POSTGRES_PASSWORD=lms -e POSTGRES_DB=lms -p 5432:5432 postgres:16
docker run -d --name redis -p 6379:6379 redis:7

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000

# In another terminal, start Celery worker
celery -A app.tasks.celery_app.celery_app worker --loglevel=info
```

### Initial Setup

```bash
# Create admin user
python scripts/user_management/create_admin.py \
    --email admin@example.com \
    --name "Admin User" \
    --password "Admin123!" \
    --role admin

# Create demo data (optional)
python scripts/database/seed_demo_data.py
```

### Access Services

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Prometheus | http://localhost:8000/metrics |

---

## Staging Deployment

### 1. Prepare Staging Server

```bash
# Create server (Ubuntu 22.04)
ssh user@staging-server
sudo apt update && sudo apt install -y docker.io docker-compose
```

### 2. Configure Staging Environment

Create `.env.staging`:

```bash
ENVIRONMENT=staging
DEBUG=False
SECRET_KEY=<generate-secure-key>
DATABASE_URL=postgresql+psycopg2://user:pass@staging-db.postgres.database.azure.com:5432/lms
REDIS_URL=redis://staging.redis.cache.windows.net:6380
AZURE_STORAGE_CONNECTION_STRING=<connection-string>
FILE_STORAGE_PROVIDER=azure
CSRF_ENABLED=True
ACCESS_TOKEN_BLACKLIST_ENABLED=True
```

### 3. Deploy

```bash
# Copy files to server
scp -r . user@staging-server:/opt/lms/

# SSH into server
ssh user@staging-server

# Pull latest code
cd /opt/lms
git pull origin staging

# Deploy
docker-compose -f docker-compose.staging.yml up -d --build
```

### 4. Verify

```bash
# Check services
curl http://staging-server:8000/api/v1/health

# Check logs
docker-compose -f docker-compose.staging.yml logs -f
```

---

## Production Deployment

### 1. Pre-Deployment Checklist

- [ ] Domain configured
- [ ] SSL certificates obtained
- [ ] Database provisioned
- [ ] Redis cache provisioned
- [ ] Blob storage configured
- [ ] Secrets configured in Azure Key Vault
- [ ] Backup strategy in place

### 2. Configure Production Environment

Create `.env.production`:

```bash
# Project
ENVIRONMENT=production
DEBUG=False
PROJECT_NAME="LMS Backend"

# Security - CRITICAL
SECRET_KEY=<generate-64-char-random-key>
ALGORITHM=HS256

# Database - Azure PostgreSQL
DATABASE_URL=postgresql+psycopg2://user:password@prod-db.postgres.database.azure.com:5432/lms?sslmode=require

# Redis - Azure Cache
REDIS_URL=redis://prod.redis.cache.windows.net:6380
CELERY_BROKER_URL=redis://prod.redis.cache.windows.net:6380/1

# Storage - Azure Blob
FILE_STORAGE_PROVIDER=azure
AZURE_STORAGE_CONNECTION_STRING=<connection-string>
AZURE_STORAGE_CONTAINER_NAME=lms-files

# Authentication
CSRF_ENABLED=True
ACCESS_TOKEN_BLACKLIST_ENABLED=True
ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED=True

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=<sendgrid-api-key>

# Monitoring
SENTRY_DSN=<sentry-dsn>
SENTRY_ENVIRONMENT=production
```

### 3. Deploy with Docker Compose

```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f api
```

### 4. Deploy with Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/lms
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Azure Deployment

### Option 1: Azure Virtual Machines

#### 1. Create Resources

```bash
# Create resource group
az group create --name rg-lms --location eastus

# Create VM
az vm create \
  --resource-group rg-lms \
  --name lms-vm \
  --image UbuntuLTS \
  --admin-username azureuser \
  --ssh-key-value @~/.ssh/id_rsa.pub

# Open ports
az vm open-port --resource-group rg-lms --name lms-vm --port 8000
```

#### 2. Install Docker on VM

```bash
ssh azureuser@lms-vm

# Install Docker
curl -fsSL https://get.docker.com | sh

# Add user to docker group
sudo usermod -aG docker azureuser

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 3. Deploy Application

```bash
# Copy deployment script
scp scripts/platform/linux/deploy_azure_vm.sh azureuser@lms-vm:~/

# Run deployment
ssh azureuser@lms-vm
./deploy_azure_vm.sh
```

### Option 2: Azure Container Apps (Future)

```yaml
# azure-container-apps.yaml
resources:
  - type: Microsoft.App/containerApps
    name: lms-api
    properties:
      managedEnvironmentId: /subscriptions/.../environments/lms-env
      configuration:
        ingress:
          external: true
          targetPort: 8000
      template:
        containers:
          - name: lms-api
            image: myregistry.azure.io/lms-api:latest
            resources:
              cpu: 1.0
              memory: 2Gi
```

### Azure Services Used

| Service | Purpose | Tier |
|---------|---------|------|
| Azure Database for PostgreSQL | Primary database | General Purpose |
| Azure Cache for Redis | Cache & Celery broker | Standard |
| Azure Blob Storage | File storage | Standard LRS |
| Azure Key Vault | Secrets management | Standard |
| Azure VM | Compute | B2s |

---

## Post-Deployment

### 1. Verify Deployment

```bash
# Health check
curl https://api.yourdomain.com/api/v1/health

# Readiness check
curl https://api.yourdomain.com/api/v1/ready

# Metrics
curl https://api.yourdomain.com/metrics
```

### 2. Configure Monitoring

```bash
# Set up Sentry
# Already configured via SENTRY_DSN

# Set up Prometheus alerts (if using)
# Configure alert rules in Prometheus
```

### 3. Create Admin User

```bash
python scripts/user_management/create_admin.py \
    --email admin@yourdomain.com \
    --name "Admin" \
    --password "<secure-password>" \
    --role admin
```

### 4. Configure Backups

```bash
# Set up automated database backups
# See scripts/maintenance/
```

---

## Troubleshooting

### Common Issues

#### Database Connection Failed

```bash
# Check database status
docker-compose logs db

# Verify connection string
echo $DATABASE_URL

# Test connection
docker exec -it lms-api python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); print(engine.connect())"
```

#### Redis Connection Failed

```bash
# Check Redis status
docker-compose logs redis

# Test connection
docker exec -it lms-api python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"
```

#### 502 Bad Gateway

```bash
# Check API logs
docker-compose logs api

# Check if API is running
docker-compose ps

# Restart API
docker-compose restart api
```

#### CORS Errors

```bash
# Check CORS settings
# In .env:
CORS_ORIGINS=https://your-frontend.com
```

#### Slow Performance

```bash
# Check resource usage
docker stats

# Check database queries
# Enable SQLALCHEMY_ECHO=True in .env temporarily
```

### Health Check Commands

```bash
# Full health check
python scripts/local/health_check.py --url https://api.yourdomain.com

# Database check
docker exec -it lms-db psql -U lms -c "SELECT 1;"

# Redis check
docker exec -it lms-redis redis-cli ping
```

### Rollback Procedure

```bash
# Rollback to previous version
git checkout <previous-commit>
docker-compose -f docker-compose.prod.yml up -d --build

# Or rollback to previous image
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```

---

## Maintenance

### Regular Tasks

| Task | Frequency | Command |
|------|-----------|---------|
| Update containers | Weekly | `docker-compose pull` |
| Clean unused images | Monthly | `docker system prune -a` |
| Backup database | Daily | See backup scripts |
| Review logs | Weekly | `docker-compose logs` |
| Update dependencies | Monthly | `pip install -U -r requirements.txt` |

### Backup and Restore

```bash
# Backup database
docker exec lms-db pg_dump -U lms > backup_$(date +%Y%m%d).sql

# Restore database
docker exec -i lms-db psql -U lms < backup_20240101.sql
```

### Log Management

```bash
# View logs
docker-compose logs -f api

# Keep logs from last 7 days
docker-compose logs --tail=1000 > logs_$(date +%Y%m%d).txt

# Clear old logs
docker-compose logs --rm
```

---

## Security Hardening

### Production Checklist

- [ ] HTTPS enforced (SSL/TLS)
- [ ] Strong SECRET_KEY (64+ random characters)
- [ ] DEBUG=False
- [ ] CSRF protection enabled
- [ ] Rate limiting enabled
- [ ] Security headers enabled
- [ ] Firewall configured
- [ ] Database credentials rotated
- [ ] Regular security updates
- [ ] Audit logging enabled
- [ ] Sentry error tracking configured

### Security Commands

```bash
# Check for vulnerabilities in dependencies
pip audit

# Run security scan
bandit -r app/

# Check Docker security
docker scan lms-api:latest
```
