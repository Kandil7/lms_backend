# Deployment and Operations Guide

This guide covers deploying and operating the LMS Backend in production environments. It includes Docker deployment, container orchestration, monitoring, security hardening, and operational procedures.

---

## Table of Contents

1. [Production Requirements](#production-requirements)
2. [Docker Deployment](#docker-deployment)
3. [Environment Configuration](#environment-configuration)
4. [Security Hardening](#security-hardening)
5. [Monitoring and Observability](#monitoring-and-observability)
6. [Backup and Recovery](#backup-and-recovery)
7. [Scaling Considerations](#scaling-considerations)
8. [Operational Procedures](#operational-procedures)

---

## Production Requirements

### Infrastructure Requirements

Before deploying to production, ensure you have the following infrastructure components:

**Compute Resources**:
- API Servers: Minimum 2 cores, 4GB RAM per instance
- Celery Workers: 2 cores, 4GB RAM per worker
- Database: 4 cores, 8GB RAM minimum (PostgreSQL)
- Cache: 2 cores, 4GB RAM (Redis)

**Storage**:
- Database: 50GB minimum, SSD recommended
- File Storage: Azure Blob Storage or equivalent
- Logs: 10GB minimum for log retention

**Network**:
- Load balancer or reverse proxy
- SSL/TLS termination
- Firewall rules for required ports

### Software Requirements

- Docker Engine 20.10+
- Docker Compose 2.0+
- PostgreSQL 14+
- Redis 7+
- Python 3.11+ (for local development)

---

## Docker Deployment

### Building the Production Image

The Dockerfile creates an optimized production image. Build it with:

```bash
docker build -t lms-backend:latest .
```

Or use Docker Compose which handles building automatically:

```bash
docker-compose -f docker-compose.prod.yml build
```

### Production Services

The production Docker Compose file defines these services:

```yaml
services:
  api:
    # Main API server
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 4G
    
  celery-worker:
    # Background task processor
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 2G
    
  celery-beat:
    # Task scheduler
    replicas: 1
    
  db:
    # PostgreSQL database
    image: postgres:14-alpine
    
  redis:
    # Cache and message broker
    image: redis:7-alpine
```

### Starting Production Services

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f api
```

---

## Environment Configuration

### Required Production Settings

Create a production .env file with these critical settings:

```env
# Environment
ENVIRONMENT=production
DEBUG=False

# Security - Generate a strong secret key
SECRET_KEY=<generate-64-character-random-string>

# Database
DATABASE_URL=postgresql+psycopg2://user:password@db:5432/lms

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# CORS - Restrict to your domains
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security Headers
SECURITY_HEADERS_ENABLED=True

# Rate Limiting
RATE_LIMIT_USE_REDIS=True
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Background Tasks
TASKS_FORCE_INLINE=False

# Monitoring (optional)
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# File Storage
FILE_STORAGE_PROVIDER=azure
AZURE_STORAGE_CONNECTION_STRING=<connection-string>
AZURE_STORAGE_CONTAINER_NAME=lms-files
```

### Generating Secrets

Generate a secure SECRET_KEY:

```bash
# Linux/Mac
python -c "import secrets; print(secrets.token_hex(32))"

# Windows (PowerShell)
python -c "import secrets; print(secrets.token_hex(32))"
```

Store all secrets securely. In production, consider using:
- HashiCorp Vault
- AWS Secrets Manager
- Azure Key Vault
- Kubernetes Secrets

---

## Security Hardening

### Network Security

**Firewall Configuration**:
```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable
```

**Container Isolation**:
- Run containers with limited privileges
- Use read-only root filesystems where possible
- Avoid running as root in containers

```yaml
# docker-compose.yml
services:
  api:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /app/uploads
```

### Application Security

**Enable All Security Features**:

```env
# Force HTTPS
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https

# Security headers
SECURITY_HEADERS_ENABLED=True

# Disable API docs in production
ENABLE_API_DOCS=False

# Strict CORS
CORS_ORIGINS=https://yourdomain.com

# Rate limiting with Redis
RATE_LIMIT_USE_REDIS=True

# Token security
ACCESS_TOKEN_BLACKLIST_ENABLED=True
ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED=True
```

**Database Security**:
- Use strong passwords
- Enable SSL connections
- Restrict user permissions
- Regular security updates

**Secret Management**:
- Never commit secrets to version control
- Use secrets management tools
- Rotate secrets regularly
- Audit secret access

### SSL/TLS Configuration

**Using a Reverse Proxy (Recommended)**:

Configure Nginx or Traefik as a reverse proxy with SSL termination:

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
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

## Monitoring and Observability

### Application Metrics

The application exposes Prometheus metrics at /metrics. Configure Prometheus to scrape these metrics:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'lms-backend'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
```

### Key Metrics to Monitor

**API Metrics**:
- Request rate by endpoint
- Response times (p50, p95, p99)
- Error rates
- Active connections

**Business Metrics**:
- User registrations
- Course enrollments
- Quiz submissions
- Certificate generations

**Infrastructure Metrics**:
- CPU and memory usage
- Database connections
- Redis memory usage
- Disk I/O

### Logging

**Log Aggregation**:

Configure structured JSON logging for production:

```env
LOG_FORMAT=json
LOG_LEVEL=INFO
```

**Log Analysis**:

Use tools like:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Loki + Grafana
- CloudWatch Logs (AWS)
- Azure Monitor

### Health Checks

The application provides health check endpoints:

- `/api/v1/health`: Basic liveness check
- `/api/v1/ready`: Readiness check (includes DB and Redis)

Configure your orchestrator to use these:

```yaml
# docker-compose.yml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Error Tracking

**Sentry Integration**:

Configure Sentry for error tracking:

```env
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

Sentry captures:
- Unhandled exceptions
- Performance traces
- User context
- Release information

---

## Backup and Recovery

### Database Backups

**Automated Backups**:

```bash
# Create backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="lms_backup_$DATE.sql"

pg_dump $DATABASE_URL > $BACKUP_DIR/$FILENAME

# Compress
gzip $BACKUP_DIR/$FILENAME

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

Schedule with cron:
```cron
0 2 * * * /path/to/backup.sh
```

**Backup Verification**:

Regularly test backup restoration:
```bash
# Create test database
createdb lms_test

# Restore backup
zcat backup.sql.gz | psql lms_test

# Verify
psql lms_test -c "SELECT COUNT(*) FROM users;"
```

### File Backups

If using local storage, back up uploaded files:

```bash
# Backup uploads directory
rsync -avz uploads/ backup:/path/to/uploads/

# Or use Docker volumes
docker volume backup lms_backend_uploads
```

### Disaster Recovery Plan

1. **Database Failure**:
   - Restore from latest backup
   - Point application to restored database
   - Verify data integrity

2. **Complete Infrastructure Failure**:
   - Provision new infrastructure
   - Restore database from backup
   - Deploy application containers
   - Update DNS records

3. **Data Corruption**:
   - Stop application
   - Restore from clean backup
   - Replay transaction logs if available

---

## Scaling Considerations

### Horizontal Scaling

The application is designed for horizontal scaling. Add more API instances:

```bash
docker-compose -f docker-compose.prod.yml up -d --scale api=4
```

Ensure:
- Load balancer distributes traffic
- Redis is used for caching (not local memory)
- Database connection pool is sized appropriately
- Session state is in Redis (not local memory)

### Database Scaling

**Read Replicas**:

For read-heavy workloads, add read replicas:

```yaml
# docker-compose.prod.yml
services:
  db-replica:
    image: postgres:14
    environment:
      POSTGRES_REPLICATION_MODE: replica
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_MASTER_HOST: db
```

Update application to route read queries to replicas.

**Connection Pooling**:

Use PgBouncer for connection pooling:

```yaml
services:
  pgbouncer:
    image: pgbouncer/pgbouncer
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/lms
      POOL_MODE: transaction
      MAX_CLIENT_CONN: 500
      DEFAULT_POOL_SIZE: 50
```

### Caching Strategy

Scale Redis for caching:

- Use Redis Cluster for high availability
- Configure appropriate maxmemory
- Use eviction policies (allkeys-lru for cache)

```env
REDIS_MAXMEMORY=2gb
REDIS_MAXMEMORY_POLICY=allkeys-lru
```

### Background Task Scaling

Scale Celery workers based on queue depth:

```bash
# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=4

# Monitor queue depth
celery -A app.tasks.celery_app inspect active_queues
```

---

## Operational Procedures

### Deployment Procedure

1. **Pre-deployment**:
   ```bash
   # Run tests
   pytest
   
   # Check for pending migrations
   alembic check
   ```

2. **Deploy**:
   ```bash
   # Pull latest code
   git pull origin main
   
   # Rebuild images
   docker-compose -f docker-compose.prod.yml build
   
   # Deploy with zero downtime
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Post-deployment**:
   ```bash
   # Check health
   curl http://localhost:8000/api/v1/ready
   
   # Verify logs
   docker-compose logs -f api
   ```

### Rollback Procedure

If issues are detected:

```bash
# List previous images
docker images | grep lms-backend

# Rollback to previous version
docker-compose -f docker-compose.prod.yml up -d --force-recreate --build api
```

Or use Docker image tags for versioned deployments:

```bash
# Tag current version
docker tag lms-backend:latest lms-backend:previous

# Deploy specific version
docker-compose -f docker-compose.prod.yml up -d lms-backend:v1.2.3
```

### Database Migration Procedure

1. **Create migration**:
   ```bash
   alembic revision --autogenerate -m "description"
   ```

2. **Test migration**:
   ```bash
   # On test database
   alembic upgrade head
   ```

3. **Deploy migration**:
   ```bash
   # Run before deploying new code
   docker-compose exec api alembic upgrade head
   ```

4. **Rollback if needed**:
   ```bash
   docker-compose exec api alembic downgrade -1
   ```

### Monitoring Procedures

**Daily Checks**:
- Review error rates in Sentry
- Check system metrics dashboards
- Verify backup completion

**Weekly Checks**:
- Review slow queries
- Check disk usage
- Review log retention

**Monthly Checks**:
- Review security updates
- Update dependencies
- Test disaster recovery

### Incident Response

1. **Detection**: Monitor alerts and user reports
2. **Assessment**: Determine scope and severity
3. **Containment**: Isolate affected components
4. **Resolution**: Fix the issue
5. **Post-mortem**: Document and prevent recurrence

Example incident commands:

```bash
# Check service status
docker-compose ps

# View recent errors
docker-compose logs --tail=100 api | grep ERROR

# Check resource usage
docker stats

# Restart service
docker-compose restart api

# Access container shell
docker exec -it lms-api-1 /bin/bash
```

---

## Summary

This deployment and operations guide covers the essential practices for running the LMS Backend in production. Key points:

1. **Security**: Enable all security features, use SSL/TLS, manage secrets properly
2. **Monitoring**: Track metrics, logs, and errors comprehensively
3. **Backup**: Regular automated backups with tested restore procedures
4. **Scaling**: Design for horizontal scaling with stateless API instances
5. **Operations**: Have clear procedures for deployment, rollback, and incidents

For additional help, consult the project documentation or engage with the development team.
