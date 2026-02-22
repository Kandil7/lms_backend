# Deployment & Production

## Complete Deployment Guide

This document covers Docker-based deployment, production configurations, monitoring, and operational procedures.

---

## 1. Architecture Overview

### Production Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PRODUCTION ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                           ┌─────────────────────┐                            │
│                           │     Load Balancer   │                            │
│                           │    (Nginx/ALB)      │                            │
│                           └──────────┬──────────┘                            │
│                                      │                                        │
│                         ┌────────────┼────────────┐                         │
│                         │            │            │                         │
│                         ▼            ▼            ▼                         │
│                   ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│                   │  API     │ │  API     │ │  API     │                   │
│                   │ Instance │ │ Instance │ │ Instance │                   │
│                   │  (8000)  │ │  (8000)  │ │  (8000)  │                   │
│                   └────┬─────┘ └────┬─────┘ └────┬─────┘                   │
│                        │            │            │                          │
│                        └────────────┼────────────┘                         │
│                                     │                                        │
│                   ┌─────────────────┼─────────────────┐                    │
│                   │                 │                 │                    │
│                   ▼                 ▼                 ▼                    │
│            ┌──────────┐      ┌──────────┐      ┌──────────┐               │
│            │ PostgreSQL│      │   Redis  │      │    S3    │               │
│            │  (5432)  │      │  (6379)   │      │          │               │
│            └──────────┘      └──────────┘      └──────────┘               │
│                                       │                                      │
│                        ┌──────────────┼──────────────┐                    │
│                        │              │              │                     │
│                        ▼              ▼              ▼                    │
│                  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│                  │ Celery   │  │ Celery   │  │ Celery   │                  │
│                  │ Worker   │  │ Worker   │  │ Worker   │                  │
│                  │(emails)  │  │(certs)   │  │(progress)│                  │
│                  └──────────┘  └──────────┘  └──────────┘                  │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     Monitoring Stack                                │   │
│   │  ┌──────────┐  ┌────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│   │  │Prometheus│◄─│  Exporters  │  │  Grafana    │  │   Sentry   │  │   │
│   │  └──────────┘  └────────────┘  └─────────────┘  └────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Docker Configuration

### Production Dockerfile

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
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY gunicorn.conf.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash nobody

# Set ownership
RUN chown -R nobody:nogroup /app

# Switch to non-root user
USER nobody

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run with Gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    build: .
    image: lms-backend:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    env_file:
      - .env.production
    volumes:
      - uploads:/app/uploads
      - certificates:/app/certificates
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/ready"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery_worker:
    build: .
    restart: unless-stopped
    command: celery -A app.tasks.celery_app worker --loglevel=info -Q emails,certificates,progress,webhooks
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    env_file:
      - .env.production
    volumes:
      - uploads:/app/uploads
      - certificates:/app/certificates
    depends_on:
      - postgres
      - redis

  celery_beat:
    build: .
    restart: unless-stopped
    command: celery -A app.tasks.celery_app beat --loglevel=info
    environment:
      - ENVIRONMENT=production
      - REDIS_URL=${REDIS_URL}
    env_file:
      - .env.production
    depends_on:
      - redis

  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
  uploads:
  certificates:

networks:
  default:
    name: lms-network
```

---

## 3. Environment Configuration

### Production Environment Variables

```bash
# .env.production

# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-32-character-secret-key-here
API_DOCS_ENABLED=false

# Database
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/lms
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://:password@redis:6379/0
REDIS_PASSWORD=your-redis-password

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
JWT_ALGORITHM=HS256

# Security
ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED=true
RATE_LIMIT_PER_MINUTE=100

# File Storage
FILE_STORAGE_PROVIDER=s3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=lms-files
AWS_REGION=us-east-1

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-email-password
SMTP_FROM=noreply@yourdomain.com

# Payments
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
MYFATOORAH_API_KEY=your-api-key

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production

# Celery
TASKS_FORCE_INLINE=false
```

### Required Secrets

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Generate database password
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

---

## 4. Database Setup

### Initial Setup

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Create admin user
docker-compose -f docker-compose.prod.yml exec api python scripts/create_admin.py
```

### Database Backup

```bash
# Backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U user lms > backup.sql

# Restore
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U user lms < backup.sql
```

---

## 5. Health Checks

### Health Check Endpoints

```
GET /api/v1/health     - Basic health check
GET /api/v1/ready       - Readiness check (database + redis)
GET /metrics           - Prometheus metrics
```

### Readiness Response

```json
{
  "status": "ok",
  "database": "up",
  "redis": "up"
}
```

---

## 6. Monitoring

### Prometheus Metrics

```
GET /metrics
```

Exposed metrics:
- Request duration (histogram)
- Request count (counter)
- Database connection pool (gauge)
- Celery task stats (gauge)

### Grafana Dashboard

```yaml
# docker-compose.observability.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./dashboards:/etc/grafana/provisioning/dashboards
```

### Sentry Integration

```python
# app/core/observability.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    integrations=[
        FastApiIntegration(),
        CeleryIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% of transactions
    send_default_pii=False,
)
```

---

## 7. Logging

### Structured Logging

```python
# app/core/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = str(record.user_id)
        
        return json.dumps(log_data)

# Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": JSONFormatter},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}
```

### Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Detailed debugging info |
| INFO | Normal operations |
| WARNING | Unexpected but handled |
| ERROR | Exceptions, failures |
| CRITICAL | System shutdown |

---

## 8. SSL/TLS Configuration

### Nginx Configuration

```nginx
# nginx.conf
upstream lms_backend {
    server api:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://lms_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /ws {
        proxy_pass http://lms_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 9. Scaling

### Horizontal Scaling

```bash
# Scale API instances
docker-compose -f docker-compose.prod.yml up -d --scale api=3

# Scale Celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celery_worker=2
```

### Load Balancing

```yaml
# docker-compose.prod.yml with nginx
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
```

---

## 10. CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run tests
        run: |
          docker-compose up -d
          docker-compose exec -T api pytest
      
      - name: Build image
        run: docker-compose -f docker-compose.prod.yml build
      
      - name: Deploy to production
        if: github.ref == 'refs/heads/main'
        run: |
          # Push to registry
          docker-compose -f docker-compose.prod.yml push
          
          # Deploy to server
          ssh $SERVER_HOST "docker-compose -f docker-compose.prod.yml pull && docker-compose -f docker-compose.prod.yml up -d"
```

---

## 11. Rollback Procedure

### Rollback Steps

```bash
# 1. Check current version
docker-compose -f docker-compose.prod.yml ps

# 2. Rollback to previous version
docker-compose -f docker-compose.prod.yml exec api alembic downgrade -1

# 3. Or rollback image
docker-compose -f docker-compose.prod.yml up -d --build api

# 4. Verify
docker-compose -f docker-compose.prod.yml logs -f api
```

---

## 12. Performance Optimization

### Database Optimization

```python
# app/core/database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)
```

### Caching Strategy

```python
# app/core/config.py
CACHE_ENABLED: bool = True
CACHE_DEFAULT_TTL_SECONDS: int = 120
COURSE_CACHE_TTL_SECONDS: int = 300
LESSON_CACHE_TTL_SECONDS: int = 300
```

---

## 13. Security Checklist

### Pre-Production Checklist

- [ ] DEBUG=false
- [ ] SECRET_KEY is 32+ characters
- [ ] Strong database password
- [ ] Strong Redis password
- [ ] SSL/TLS configured
- [ ] CORS configured for production domains
- [ ] Rate limiting enabled
- [ ] Security headers enabled
- [ ] Token blacklist fail-closed
- [ ] Sentry configured
- [ ] Log level set to INFO
- [ ] Health checks enabled

---

## Summary

This deployment guide covers:

| Topic | Key Points |
|-------|------------|
| Docker | Multi-container, health checks |
| Environment | Production variables, secrets |
| Database | Migrations, backup/restore |
| Monitoring | Prometheus, Grafana, Sentry |
| Logging | Structured JSON logs |
| SSL | Nginx with Let's Encrypt |
| Scaling | Horizontal with nginx |
| CI/CD | GitHub Actions |
| Security | Checklist, fail-closed |

The production setup is designed for reliability, scalability, and security.
