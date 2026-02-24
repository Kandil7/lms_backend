# Docker and Infrastructure Documentation

This document covers all Docker and infrastructure configuration for the LMS Backend.

## Table of Contents

1. [Dockerfiles](#dockerfiles)
2. [Docker Compose Configurations](#docker-compose-configurations)
3. [Environment Variables](#environment-variables)
4. [Service Orchestration](#service-orchestration)
5. [Azure Deployment](#azure-deployment)

---

## Dockerfiles

### Main Dockerfile

**Location**: `Dockerfile`

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    mkdir -p /app/uploads /app/certificates && \
    chown -R appuser:appuser /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --retries 5 --timeout 120 -r requirements.txt

COPY . .

# Set permissions for runtime directories
RUN chown -R appuser:appuser /app/uploads /app/certificates

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Python 3.11 slim | Lightweight, current stable version |
| Non-root user | Security - follow principle of least privilege |
| Multi-stage build potential | Can be optimized for production |
| Requirements separation | Better caching on rebuild |

---

## Docker Compose Configurations

### Development Configuration

**Location**: `docker-compose.yml`

```yaml
services:
  api:
    build: .
    container_name: lms-api
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql+psycopg2://lms:lms@db:5432/lms
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/1
      CELERY_RESULT_BACKEND: redis://redis:6379/2
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    depends_on:
      - db
      - redis

  celery-worker:
    build: .
    container_name: lms-celery-worker
    command: celery -A app.tasks.celery_app.celery_app worker --loglevel=info --queues=emails,progress,certificates,webhooks
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql+psycopg2://lms:lms@db:5432/lms
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/1
      CELERY_RESULT_BACKEND: redis://redis:6379/2
    volumes:
      - .:/app
    depends_on:
      - db
      - redis

  celery-beat:
    build: .
    container_name: lms-celery-beat
    command: celery -A app.tasks.celery_app.celery_app beat --loglevel=info
    env_file:
      - .env
    environment:
      DATABASE_URL: postgresql+psycopg2://lms:lms@db:5432/lms
      REDIS_URL: redis://redis:6379/0
      CELERY_BROKER_URL: redis://redis:6379/1
      CELERY_RESULT_BACKEND: redis://redis:6379/2
    volumes:
      - .:/app
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    container_name: lms-postgres
    environment:
      POSTGRES_USER: lms
      POSTGRES_PASSWORD: lms
      POSTGRES_DB: lms
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: lms-redis
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Staging Configuration

**Location**: `docker-compose.staging.yml`

Similar to development with:
- Production-grade settings
- Different environment variables
- No debug mode
- Separate network

### Production Configuration

**Location**: `docker-compose.prod.yml`

```yaml
services:
  api:
    build: .
    image: lms-api:latest
    restart: unless-stopped
    env_file:
      - .env.production
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
    ports:
      - "8000:8000"
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - lms-network

  celery-worker:
    build: .
    restart: unless-stopped
    command: celery -A app.tasks.celery_app.celery_app worker --loglevel=info --concurrency=4
    env_file:
      - .env.production
    depends_on:
      - db
      - redis
    networks:
      - lms-network

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    networks:
      - lms-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - lms-network

networks:
  lms-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

### Demo Configuration

**Location**: `docker-compose.demo.yml`

For demonstration purposes with simplified setup.

### Observability Configuration

**Location**: `docker-compose.observability.yml`

Adds monitoring stack:
- Prometheus
- Grafana
- AlertManager

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
```

---

## Environment Variables

### Development (.env)

```bash
# Project
PROJECT_NAME=LMS Backend
VERSION=1.0.0
ENVIRONMENT=development
DEBUG=True

# API
API_V1_PREFIX=/api/v1
ENABLE_API_DOCS=True

# Database
DATABASE_URL=postgresql+psycopg2://lms:lms@localhost:5432/lms
SQLALCHEMY_ECHO=False

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Security (development only)
SECRET_KEY=change-me-in-development
ALGORITHM=HS256

# Auth
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
ACCESS_TOKEN_BLACKLIST_ENABLED=False

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Production (.env.production)

```bash
# Project
PROJECT_NAME=LMS Backend
VERSION=1.0.0
ENVIRONMENT=production
DEBUG=False

# Database
DATABASE_URL=postgresql+psycopg2://user:password@prod-db.postgres.database.azure.com:5432/lms

# Redis
REDIS_URL=redis://prod-redis.redis.cache.windows.net:6380
CELERY_BROKER_URL=redis://prod-redis.redis.cache.windows.net:6380/1

# Security
SECRET_KEY=<strong-random-64-char-key>
ALGORITHM=HS256

# Production settings
CSRF_ENABLED=True
ACCESS_TOKEN_BLACKLIST_ENABLED=True
ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED=True

# Azure
AZURE_STORAGE_CONNECTION_STRING=<azure-connection-string>
AZURE_STORAGE_CONTAINER_NAME=lms-files
FILE_STORAGE_PROVIDER=azure
```

### Demo (.env.demo)

```bash
ENVIRONMENT=demo
DEBUG=True
DEMO_MODE=True
```

---

## Service Orchestration

### Startup Order

```
┌─────────────────────────────────────────────────────────────┐
│                        STARTUP                               │
│                                                              │
│  1. Infrastructure Layer                                    │
│     ├── PostgreSQL (wait for ready)                         │
│     └── Redis (wait for ready)                             │
│                                                              │
│  2. Application Layer                                       │
│     ├── Celery Beat (scheduler)                            │
│     ├── Celery Workers (task processors)                    │
│     └── API (FastAPI server)                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Health Checks

Each service includes health checks:

```yaml
# API health check
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s

# Database health check
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U lms"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### Networking

All services communicate via Docker network:

```yaml
networks:
  lms-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Volume Management

| Volume | Purpose | Backup Strategy |
|--------|---------|-----------------|
| `postgres_data` | Database files | Daily snapshots |
| `redis_data` | Redis persistence | Not critical (cache) |
| `uploads` | File uploads | Azure Blob |
| `certificates` | Generated certificates | Azure Blob |

---

## Azure Deployment

### Azure VM Deployment

**Files**:
- `.github/workflows/deploy-azure-vm.yml`

**Steps**:

1. **Build & Push**
   ```dockerfile
   # Build image
   docker build -t lms-api:${{ github.sha }} .
   
   # Push to Azure Container Registry
   az acr build --registry myRegistry --image lms-api:${{ github.sha }} .
   ```

2. **Deploy to VM**
   ```bash
   # SSH into VM
   ssh user@vm-host
   
   # Pull latest image
   docker pull myregistry.azure.io/lms-api:${{ github.sha }}
   
   # Restart services
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Azure Container Apps Alternative

```yaml
# azure-container-apps.yml
resources:
  - type: Microsoft.App/containerApps
    name: lms-api
    properties:
      containerApps:
        - name: lms-api
          containers:
            - name: lms-api
              image: myregistry.azure.io/lms-api:latest
              resources:
                cpu: 1.0
                memory: 2Gi
```

### Azure Database

```bash
# Create Azure Database for PostgreSQL
az postgres flexible-server create \
  --name lms-db \
  --resource-group rg-lms \
  --sku-name Standard_B1ms \
  --tier Burstable
```

### Azure Cache for Redis

```bash
# Create Azure Cache for Redis
az redis create \
  --name lms-redis \
  --resource-group rg-lms \
  --sku Basic \
  --vm-size c0
```

### Azure Blob Storage

```bash
# Create storage account
az storage account create \
  --name lmsstorage \
  --resource-group rg-lms \
  --sku Standard_LRS

# Create container
az storage container create \
  --name lms-files \
  --account-name lmsstorage
```

---

## CI/CD Integration

### GitHub Actions

**File**: `.github/workflows/ci.yml`

```yaml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/ -v
      
      - name: Build Docker
        run: docker build -t lms-api:test .
      
      - name: Push to registry
        if: github.ref == 'refs/heads/main'
        run: |
          echo "${{ secrets.REGISTRY_PASSWORD }}" | docker login -u "${{ secrets.REGISTRY_USER }}" --password-stdin
          docker push ${{ secrets.REGISTRY }}/lms-api:latest
```

### Deploy to Azure VM

**File**: `.github/workflows/deploy-azure-vm.yml`

```yaml
name: Deploy to Azure VM

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v0.1.6
        with:
          host: ${{ secrets.AZURE_VM_HOST }}
          username: ${{ secrets.AZURE_VM_USER }}
          key: ${{ secrets.AZURE_VM_SSH_KEY }}
          script: |
            cd /opt/lms
            docker-compose -f docker-compose.prod.yml pull
            docker-compose -f docker-compose.prod.yml up -d
            docker system prune -f
```

---

## Security Considerations

### Image Security

| Practice | Implementation |
|----------|----------------|
| Non-root user | `USER appuser` in Dockerfile |
| Minimal base image | `python:3.11-slim` |
| No secrets in image | Use environment variables |
| Regular updates | Update base images monthly |

### Network Security

| Practice | Implementation |
|----------|----------------|
| Network isolation | Custom bridge network |
| No exposed ports | Only 8000 (API) exposed |
| TLS/SSL | Terminated at load balancer |

### Secret Management

| Environment | Method |
|-------------|--------|
| Development | `.env` file |
| Staging | GitHub secrets |
| Production | Azure Key Vault |

---

## Scaling Considerations

### Horizontal Scaling

```yaml
# Scale API instances
docker-compose up -d --scale api=3
```

### Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 512M
```

### Load Balancing

```bash
# Nginx upstream configuration
upstream lms_api {
    server api:8000;
    server api_2:8000;
    server api_3:8000;
}
```

---

## Monitoring

### Container Logs

```bash
# View logs
docker-compose logs -f api
docker-compose logs -f celery-worker

# View specific container
docker logs lms-api
```

### Resource Usage

```bash
# Check resource usage
docker stats

# Check container health
docker inspect lms-api --format='{{.State.Health.Status}}'
```

### Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/api/v1/health` | Basic health check |
| `/api/v1/ready` | Readiness check (DB + Redis) |
| `/metrics` | Prometheus metrics |
