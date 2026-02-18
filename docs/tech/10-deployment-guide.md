# Deployment Guide

This comprehensive guide covers production deployment strategies, infrastructure setup, security hardening, and operational best practices.

---

## Table of Contents

1. [Deployment Architecture](#1-deployment-architecture)
2. [Environment Configuration](#2-environment-configuration)
3. [Docker Production Setup](#3-docker-production-setup)
4. [Manual Deployment](#4-manual-deployment)
5. [Database Setup](#5-database-setup)
6. [Reverse Proxy Configuration](#6-reverse-proxy-configuration)
7. [Security Hardening](#7-security-hardening)
8. [Monitoring and Logging](#8-monitoring-and-logging)
9. [Backup and Recovery](#9-backup-and-recovery)
10. [Scaling Considerations](#10-scaling-considerations)

---

## 1. Deployment Architecture

### Production Infrastructure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION INFRASTRUCTURE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│    ┌─────────┐     ┌─────────────┐     ┌─────────────────────────┐     │
│    │  User   │────▶│   CDN/Load  │────▶│      Nginx/HAProxy      │     │
│    │ Browser │     │   Balancer  │     │    (Reverse Proxy)       │     │
│    └─────────┘     └─────────────┘     └───────────┬─────────────┘     │
│                                                     │                   │
│                                                     ▼                   │
│                                          ┌─────────────────────┐       │
│                                          │    API Servers      │       │
│                                          │  (Multiple Nodes)   │       │
│                                          │  ┌─────┐ ┌─────┐   │       │
│                                          │  │ API │ │ API │   │       │
│                                          │  └─────┘ └─────┘   │       │
│                                          └─────────┬───────────┘       │
│                                                    │                   │
│                          ┌─────────────────────────┼──────────────┐   │
│                          │                         │              │   │
│                          ▼                         ▼              ▼   │
│                   ┌───────────┐            ┌───────────┐    ┌─────────┐ │
│                   │PostgreSQL│            │   Redis   │    │   S3    │ │
│                   │ Primary  │◀──────────▶│  Cluster  │    │ Bucket  │ │
│                   │   +     │            │ (Cache+   │    │(Files)  │ │
│                   │ Replica │            │   Queue)  │    └─────────┘ │
│                   └─────────┘            └───────────┘               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Service Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Load Balancer | Nginx/HAProxy | Distribute traffic |
| API Servers | FastAPI (Gunicorn/Uvicorn) | Handle requests |
| Database | PostgreSQL | Data storage |
| Cache/Queue | Redis Cluster | Caching + Celery |
| Object Storage | AWS S3 | File storage |
| CDN | CloudFlare/AWS CloudFront | Static assets |

---

## 2. Environment Configuration

### Production Environment Variables

Create a production `.env` file:

```env
# =====================
# APPLICATION (REQUIRED)
# =====================
PROJECT_NAME=LMS Backend
VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
API_V1_PREFIX=/api/v1

# =====================
# SECURITY (CRITICAL)
# =====================
# Generate: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<your-64-character-hex-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30

# =====================
# DATABASE
# =====================
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/lms
DATABASE_URL_SYNC=postgresql+psycopg2://user:password@postgres:5432/lms
SQLALCHEMY_ECHO=false
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# =====================
# REDIS
# =====================
REDIS_URL=redis://redis:6379/0

# =====================
# EMAIL (SMTP)
# =====================
EMAIL_FROM=noreply@yourdomain.com
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=<sendgrid-api-key>
SMTP_USE_TLS=true

# =====================
# FILE STORAGE (S3)
# =====================
FILE_STORAGE_PROVIDER=s3
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
AWS_REGION=us-east-1
AWS_S3_BUCKET=lms-files-prod

# =====================
# CACHING
# =====================
CACHE_ENABLED=true
CACHE_DEFAULT_TTL_SECONDS=300
COURSE_CACHE_TTL_SECONDS=3600

# =====================
# RATE LIMITING
# =====================
RATE_LIMIT_USE_REDIS=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# =====================
# CORS
# =====================
CORS_ORIGINS=https://app.yourdomain.com,https://admin.yourdomain.com

# =====================
# CELERY
# =====================
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
CELERY_TASK_ALWAYS_EAGER=false
```

---

## 3. Docker Production Setup

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 2G

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A app.tasks.celery_app worker -l info -c 2
    env_file:
      - .env
    depends_on:
      - redis
      - db
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A app.tasks.celery_app beat -l info
    env_file:
      - .env
    depends_on:
      - redis
      - db
    restart: unless-stopped

  db:
    image: postgres:16
    environment:
      POSTGRES_USER: lms
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: lms
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

volumes:
  postgres_data:
  redis_data:
```

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run with Gunicorn
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]
```

---

## 4. Manual Deployment

### Server Setup (Ubuntu)

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Python
sudo apt install -y python3.11 python3.11-venv python3-pip

# 3. Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 4. Install Redis
sudo apt install -y redis-server

# 5. Install Nginx
sudo apt install -y nginx

# 6. Configure firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### Application Deployment

```bash
# 1. Create application user
sudo useradd -m -s /bin/bash appuser
sudo mkdir -p /var/www/lms-backend
sudo chown appuser:appuser /var/www/lms-backend

# 2. Setup virtual environment
cd /var/www/lms-backend
python3.11 -m venv venv
source venv/bin/activate

# 3. Clone and install
git clone <repo-url> .
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env  # Edit production settings

# 5. Run migrations
alembic upgrade head

# 6. Create systemd service
sudo nano /etc/systemd/system/lms-api.service

[Unit]
Description=LMS Backend API
After=network.target

[Service]
User=appuser
Group=appuser
WorkingDirectory=/var/www/lms-backend
Environment="PATH=/var/www/lms-backend/venv/bin"
ExecStart=/var/www/lms-backend/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target

# 7. Start services
sudo systemctl daemon-reload
sudo systemctl start lms-api
sudo systemctl enable lms-api
```

---

## 5. Database Setup

### PostgreSQL Production Configuration

```sql
-- /etc/postgresql/16/main/postgresql.conf

# Memory
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 128MB

# Write Ahead Log
wal_level = replica
max_wal_size = 1GB
min_wal_size = 80MB

# Connections
max_connections = 200

# Query Planning
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
```

### Database Backup

```bash
# Create backup script
#!/bin/bash
# /usr/local/bin/backup-db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/postgres"
DB_NAME="lms"
DB_USER="lms"

mkdir -p $BACKUP_DIR

pg_dump -U $DB_USER -Fc $DB_NAME > $BACKUP_DIR/lms_$DATE.dump

# Keep only last 7 backups
find $BACKUP_DIR -name "lms_*.dump" -mtime +7 -delete

echo "Backup completed: lms_$DATE.dump"

# Add to crontab
# 0 2 * * * /usr/local/bin/backup-db.sh
```

---

## 6. Reverse Proxy Configuration

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/lms-backend

upstream lms_api {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;  # Second instance
}

server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Proxy to API
    location / {
        proxy_pass http://lms_api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support (if needed)
    location /ws/ {
        proxy_pass http://lms_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 7. Security Hardening

### SSL/TLS Setup

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run

# Add to crontab
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### Application Security Checklist

| Setting | Value | Purpose |
|---------|-------|---------|
| `DEBUG` | `false` | Hide error details |
| `SECRET_KEY` | Random 64-char | Secure token signing |
| `CORS_ORIGINS` | Specific domains | Restrict cross-origin |
| `RATE_LIMIT` | 60/min | Prevent abuse |
| `HSTS` | Enabled | Enforce HTTPS |

---

## 8. Monitoring and Logging

### Health Check Endpoint

```bash
# Basic health check
curl https://api.yourdomain.com/api/v1/health

# Full readiness check
curl https://api.yourdomain.com/api/v1/ready
```

### Logging Configuration

```python
# app/core/logging.py
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.handlers.RotatingFileHandler(
            "/var/log/lms/app.log",
            maxBytes=10_000_000,  # 10MB
            backupCount=5
        )
    ]
)
```

### Prometheus Metrics

```python
# Add to main.py
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

Instrumentator().instrument(app).expose(app)
```

---

## 9. Backup and Recovery

### Backup Strategy

| Data | Frequency | Retention |
|------|-----------|-----------|
| Database | Daily | 30 days |
| File uploads | Daily | 7 days |
| Logs | Weekly | 90 days |
| Config | On change | Forever |

### Recovery Procedures

```bash
# Restore database
pg_restore -U lms -d lms -c /var/backups/postgres/lms_20240115_020000.dump

# Verify restoration
psql -U lms -c "SELECT COUNT(*) FROM users;"
```

---

## 10. Scaling Considerations

### Horizontal Scaling

```yaml
# docker-compose.prod.yml - scale API
services:
  api:
    deploy:
      replicas: 4  # Scale to 4 instances
  
  # Add load balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
```

### Database Read Replicas

```yaml
# docker-compose.prod.yml
services:
  db-primary:
    image: postgres:16
    environment:
      POSTGRES_USER: lms
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: lms
    volumes:
      - db-primary:/var/lib/postgresql/data
  
  db-replica:
    image: postgres:16
    command: postgres -c replica=on
    environment:
      POSTGRES_USER: lms
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_MASTER_HOST: db-primary
    depends_on:
      - db-primary
```

---

## Deployment Checklist

- [ ] Generate production SECRET_KEY
- [ ] Configure database with proper credentials
- [ ] Set up SSL/TLS certificates
- [ ] Configure CORS with specific origins
- [ ] Enable rate limiting
- [ ] Set up log rotation
- [ ] Configure database backups
- [ ] Test health check endpoints
- [ ] Verify all environment variables
- [ ] Run migrations
- [ ] Test with staging data

This deployment guide provides a complete roadmap for production deployment with security, scalability, and maintainability in mind.
