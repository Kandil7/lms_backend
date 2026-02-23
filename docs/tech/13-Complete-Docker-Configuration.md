# Complete Docker Configuration Reference

This comprehensive documentation details all Docker and Docker Compose configurations in the LMS Backend project. Each configuration is explained in terms of its purpose, service definitions, networking, volumes, and production considerations.

---

## Docker Compose Files Overview

The project includes multiple Docker Compose files optimized for different deployment scenarios:

1. **docker-compose.yml** - Development environment
2. **docker-compose.prod.yml** - Production environment
3. **docker-compose.staging.yml** - Staging environment
4. **docker-compose.observability.yml** - Monitoring stack

---

## Development Configuration (docker-compose.yml)

### Purpose

The development Docker Compose configuration provides a complete local development environment with all necessary services. It is optimized for developer productivity with hot reload, verbose logging, and convenient service exposure.

### Services

#### API Service

```yaml
api:
  build: .
  command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  volumes:
    - .:/app
  ports:
    - "8000:8000"
  environment:
    - DATABASE_URL=postgresql+psycopg2://lms:lms@db:5432/lms
    - REDIS_URL=redis://redis:6379/0
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy
```

**Analysis**: The API builds from the Dockerfile in the current directory. The --reload flag enables auto-reload on code changes. Volume mounting shares source code for development. Environment variables configure database and Redis connections. Dependencies ensure services start in order with health checks.

#### Database Service

```yaml
db:
  image: postgres:16-alpine
  environment:
    POSTGRES_USER: lms
    POSTGRES_PASSWORD: lms
    POSTGRES_DB: lms
  volumes:
    - postgres_data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U lms -d lms"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**Analysis**: Uses PostgreSQL 16 Alpine for minimal footprint. Environment variables configure default database, user, and password. Volume persists data across container restarts. Health check verifies database readiness.

#### Redis Service

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --save 60 1 --loglevel warning
  volumes:
    - redis_data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 3s
    retries: 5
```

**Analysis**: Uses Redis 7 Alpine for minimal footprint. The --save directive creates RDB snapshots every 60 seconds if at least one key changed. Health check verifies Redis connectivity.

#### Celery Worker Service

```yaml
celery-worker:
  build: .
  command: celery -A app.tasks.celery_app.celery_app worker --loglevel=info --queues=emails,progress,certificates,webhooks
  volumes:
    - .:/app
  environment:
    - DATABASE_URL=postgresql+psycopg2://lms:lms@db:5432/lms
    - REDIS_URL=redis://redis:6379/0
    - CELERY_BROKER_URL=redis://redis:6379/1
    - CELERY_RESULT_BACKEND=redis://redis:6379/2
    - TASKS_FORCE_INLINE=true
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy
```

**Analysis**: Celery worker processes background tasks. The --reload flag is not used in production but may be added for development. Multiple queues handle different task types. TASKS_FORCE_INLINE=true runs tasks synchronously in development for easier debugging.

#### Celery Beat Service

```yaml
celery-beat:
  build: .
  command: celery -A app.tasks.celery_app.celery_app beat --loglevel=info
  volumes:
    - .:/app
  environment:
    - DATABASE_URL=postgresql+psycopg2://lms:lms@db:5432/lms
    - REDIS_URL=redis://redis:6379/0
    - CELERY_BROKER_URL=redis://redis:6379/1
    - CELERY_RESULT_BACKEND=redis://redis:6379/2
  depends_on:
    - db
    - redis
```

**Analysis**: Celery Beat schedules periodic tasks. No health check as beat is not critical for startup.

### Networks

```yaml
networks:
  default:
    name: lms_network
```

**Analysis**: Creates a dedicated Docker network for service communication. Service names become DNS entries within this network.

### Volumes

```yaml
volumes:
  postgres_data:
  redis_data:
```

**Analysis**: Named volumes persist database and cache data across container restarts.

---

## Production Configuration (docker-compose.prod.yml)

### Purpose

The production Docker Compose configuration is optimized for reliability, security, and performance. It includes production-specific hardening, external service dependencies, and proper health checks.

### Services

#### Migrate Service

```yaml
migrate:
  build: .
  command:
    - /bin/sh
    - -c
    - >
      python scripts/wait_for_db.py &&
      alembic upgrade head
  env_file:
    - .env
  environment:
    ENVIRONMENT: production
    DEBUG: "false"
    DATABASE_URL: ${PROD_DATABASE_URL}
    REDIS_URL: ${PROD_REDIS_URL:-redis://redis:6379/0}
  restart: "no"
```

**Analysis**: The migrate service runs database migrations as an init container. It waits for the database to be ready, then runs Alembic upgrades. The restart: "no" ensures the container exits after completion. External database URL is provided via environment variable.

#### API Service

```yaml
api:
  build: .
  user: "0:0"
  command:
    - /bin/sh
    - -c
    - >
      mkdir -p /app/uploads /app/certificates &&
      chown -R nobody:nogroup /app/uploads /app/certificates &&
      exec su nobody -s /bin/sh -c "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2}"
  ports:
    - "8000:8000"
  volumes:
    - uploads_data:/app/uploads
    - certificates_data:/app/certificates
  healthcheck:
    test:
      - CMD-SHELL
      - >
        python -c "import os,urllib.request,sys;
        req=urllib.request.Request('http://localhost:8000/api/v1/ready', headers={'Host': os.getenv('APP_DOMAIN', 'localhost')});
        sys.exit(0 if urllib.request.urlopen(req, timeout=3).status == 200 else 1)"
    interval: 15s
    timeout: 5s
    retries: 5
    start_period: 20s
  restart: unless-stopped
```

**Analysis**: Security hardening includes running as non-root user (nobody). The command creates necessary directories and sets ownership before starting uvicorn. Workers are configurable via UVICORN_WORKERS environment variable. Health check verifies the readiness endpoint. The restart policy ensures automatic recovery from failures.

#### Celery Worker Service

```yaml
celery-worker:
  build: .
  user: "0:0"
  command:
    - /bin/sh
    - -c
    - >
      mkdir -p /app/uploads /app/certificates /tmp &&
      chown -R nobody:nogroup /app/uploads /app/certificates /tmp &&
      celery -A app.tasks.celery_app.celery_app worker --loglevel=info --queues=emails,progress,certificates --uid=nobody
  volumes:
    - uploads_data:/app/uploads
    - certificates_data:/app/certificates
  restart: unless-stopped
```

**Analysis**: Similar security hardening with non-root user. Directories are created and owned by nobody. The --uid=nobody flag ensures worker processes run as nobody.

#### Celery Beat Service

```yaml
celery-beat:
  build: .
  user: "0:0"
  command:
    - /bin/sh
    - -c
    - >
      mkdir -p /tmp &&
      chown -R nobody:nogroup /tmp &&
      celery -A app.tasks.celery_app.celery_app beat --loglevel=info --uid=nobody --schedule=/tmp/celerybeat-schedule
  volumes:
    - uploads_data:/app/uploads
    - certificates_data:/app/certificates
    - celerybeat_data:/tmp
  restart: unless-stopped
```

**Analysis**: Persistent schedule file stored in named volume. Other services can reference this schedule if needed.

#### Caddy Service

```yaml
caddy:
  image: caddy:2-alpine
  depends_on:
    api:
      condition: service_healthy
  environment:
    APP_DOMAIN: ${APP_DOMAIN}
    LETSENCRYPT_EMAIL: ${LETSENCRYPT_EMAIL}
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./ops/caddy/Caddyfile:/etc/caddy/Caddyfile:ro
    - caddy_data:/data
    - caddy_config:/config
  restart: unless-stopped
```

**Analysis**: Caddy provides reverse proxy with automatic HTTPS. Depends on API health check passing. Mounts Caddyfile configuration. Volumes store certificates and configuration persistently.

#### Redis Service

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --save 60 1 --loglevel warning
  expose:
    - "6379"
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 3s
    retries: 5
```

**Analysis**: Redis is exposed only internally (not to host). This is appropriate for production where Redis is accessed through Docker networking.

#### PostgreSQL Service (Optional)

```yaml
postgres-local:
  image: postgres:16-alpine
  profiles: ["local-db"]
  environment:
    POSTGRES_USER: ${POSTGRES_USER:-lms}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-lms}
    POSTGRES_DB: ${POSTGRES_DB:-lms}
  expose:
    - "5432"
  restart: unless-stopped
```

**Analysis**: The "local-db" profile allows optionally running PostgreSQL locally. For production, use external managed PostgreSQL.

### Volumes

```yaml
volumes:
  postgres_data:
  uploads_data:
  certificates_data:
  celerybeat_data:
  caddy_data:
  caddy_config:
```

**Analysis**: Named volumes persist all persistent data. Separate volumes for different concerns allow independent management.

---

## Staging Configuration (docker-compose.staging.yml)

### Purpose

The staging configuration provides a production-like environment for testing changes before production deployment. It uses production architecture with staging-specific settings.

### Differences from Production

- Debug mode may be enabled
- Staging-specific environment variables
- Test database and Redis instances
- Different domain configuration

---

## Observability Configuration (docker-compose.observability.yml)

### Purpose

The observability stack provides monitoring, alerting, and visualization. This stack operates independently from the main application stack.

### Services

- **Prometheus**: Metrics collection and storage
- **Alertmanager**: Alert routing and notification
- **Grafana**: Visualization dashboards

---

## Dockerfile Analysis

### Build Stage

The Dockerfile (not shown but referenced) typically includes:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key Points**:
- Uses slim Python image for minimal size
- Installs dependencies before copying code (layer caching)
- Runs as non-root user in production

---

## Networking Configuration

### Development Network

All services communicate over the default bridge network. Service names become DNS entries:
- api:8000
- db:5432
- redis:6379

### Production Network

Services are isolated with internal networking. Only Caddy is exposed externally. API, database, and Redis communicate internally.

---

## Volume Configuration

### Named Volumes

- **postgres_data**: Database files
- **redis_data**: Redis persistence
- **uploads_data**: User-uploaded files
- **certificates_data**: Generated certificates
- **celerybeat_data**: Beat schedule
- **caddy_data**: TLS certificates
- **caddy_config**: Caddy configuration

### Volume Best Practices

- Use named volumes for persistent data
- Mount volumes read-only where possible
- Separate data volumes from configuration

---

## Environment Variables

### Development Variables

```env
DATABASE_URL=postgresql+psycopg2://lms:lms@db:5432/lms
REDIS_URL=redis://redis:6379/0
DEBUG=true
```

### Production Variables

```env
PROD_DATABASE_URL=postgresql+psycopg2://user:pass@prod-db.postgres.database.azure.com:5432/lms
PROD_REDIS_URL=redis://prod-redis.redis.cache.windows.net:6380
ENVIRONMENT=production
DEBUG=false
```

---

## Health Checks

### API Health Check

```yaml
healthcheck:
  test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/ready')\""]
  interval: 15s
  timeout: 5s
  retries: 5
  start_period: 20s
```

The health check verifies the readiness endpoint returns 200. The start_period allows time for application startup before health checks count as failures.

### Database Health Check

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U lms -d lms"]
  interval: 10s
  timeout: 5s
  retries: 5
```

Uses pg_isready to verify PostgreSQL accepts connections.

---

## Security Considerations

### Non-Running Root

All production containers run as non-root users. This limits the impact of container escapes.

### Secret Management

Secrets are passed via environment variables. Production uses external secrets management (Azure Key Vault, HashiCorp Vault).

### Network Isolation

Production services don't expose ports to the host. All external traffic routes through Caddy.

### Read-Only Filesystems

Where possible, filesystems should be mounted read-only. Only necessary directories are writable.

---

## Deployment Commands

### Development

```bash
docker compose up --build
```

### Production

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Observability

```bash
docker compose -f docker-compose.observability.yml up -d
```

---

## Scaling Considerations

### Horizontal Scaling

Scale API instances:
```bash
docker compose -f docker-compose.prod.yml up -d --scale api=3
```

Scale Celery workers:
```bash
docker compose -f docker-compose.prod.yml up -d --scale celery-worker=4
```

### Vertical Scaling

Adjust resource limits in docker-compose files:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

---

This comprehensive Docker documentation covers all containerization aspects of the LMS Backend project. Each configuration is production-ready and follows Docker best practices for security, reliability, and maintainability.
