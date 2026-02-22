# Operations and Infrastructure Documentation

This document provides comprehensive documentation for the operations infrastructure of the LMS Backend project, including reverse proxy configuration, observability stack, CI/CD pipelines, and deployment automation.

---

## Table of Contents

1. [Reverse Proxy (Caddy)](#reverse-proxy-caddy)
2. [Observability Stack](#observability-stack)
3. [CI/CD Pipelines](#cicd-pipelines)
4. [Deployment Scripts](#deployment-scripts)
5. [Infrastructure Configuration](#infrastructure-configuration)

---

## Reverse Proxy (Caddy)

### Overview

The project uses Caddy as a reverse proxy server to handle SSL termination, HTTP/2 support, and automatic HTTPS. Caddy was chosen for its simplicity, automatic TLS certificate management, and minimal configuration requirements.

### Caddyfile Configuration

The Caddy configuration is located at `ops/caddy/Caddyfile`:

```caddyfile
{
    email {$LETSENCRYPT_EMAIL}
}

{$APP_DOMAIN} {
    encode zstd gzip
    reverse_proxy api:8000
}
```

### Configuration Explanation

**Global Options Block**:
- `email {$LETSENCRYPT_EMAIL}`: Email address used for Let's Encrypt registration and certificate renewal notifications. This is provided through an environment variable.

**Site Block**:
- `{$APP_DOMAIN}`: The domain name for the application, passed as an environment variable. This allows the same configuration to be used across different environments.

**encode zstd gzip**: Enables automatic compression using both Gzip and Zstandard algorithms. This significantly reduces bandwidth and improves response times:
- Gzip: Universal compression, excellent compatibility
- Zstd: Modern compression with better ratios than Gzip, supported by modern browsers

**reverse_proxy api:8000**: Routes all requests to the API container running on port 8000. Docker's internal DNS resolves "api" to the container's IP address.

### Why Caddy?

Caddy was selected for several reasons:

1. **Automatic HTTPS**: Automatically obtains and renews SSL certificates from Let's Encrypt
2. **HTTP/2 Support**: Native support for HTTP/2 protocol
3. **Simplicity**: Minimal configuration compared to Nginx
4. **Zero Configuration TLS**: Works out of the box with sensible defaults

### Alternative Configurations

**Development with HTTP**:
```caddyfile
localhost:8080 {
    reverse_proxy api:8000
}
```

**With Custom SSL Certificates**:
```caddyfile
example.com {
    tls /path/to/cert.pem /path/to/key.pem
    reverse_proxy api:8000
}
```

---

## Observability Stack

### Overview

The observability stack provides comprehensive monitoring, alerting, and visualization for the LMS Backend. It consists of:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Metrics visualization and dashboards
- **Alertmanager**: Alert routing and notification management

### Prometheus Configuration

The Prometheus configuration is located at `ops/observability/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 30s

rule_files:
  - /etc/prometheus/alerts.yml

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets:
          - localhost:9090

  - job_name: lms_api_prod
    metrics_path: /metrics
    static_configs:
      - targets:
          - host.docker.internal:8000
        labels:
          service: lms-backend
          environment: production

  - job_name: lms_api_staging
    metrics_path: /metrics
    static_configs:
      - targets:
          - host.docker.internal:8001
        labels:
          service: lms-backend
          environment: staging
```

**Configuration Details**:

- **scrape_interval: 15s**: How often to scrape metrics from targets
- **evaluation_interval: 30s**: How often to evaluate alert rules
- **metrics_path: /metrics**: The endpoint where the application exposes Prometheus metrics

**Scrape Targets**:

1. **Prometheus**: Self-monitoring metrics
2. **lms_api_prod**: Production API metrics
3. **lms_api_staging**: Staging API metrics

**Labels**: Each target includes labels for service identification and environment classification, enabling filtering in Grafana dashboards.

### Prometheus Alerts

Alerts are defined in `ops/observability/prometheus/alerts.yml`. These alerts monitor:

- API availability
- Response time degradation
- Error rate thresholds
- Resource utilization (CPU, memory)
- Database connection issues

### Alertmanager Configuration

Located at `ops/observability/alertmanager/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  receiver: webhook-default
  group_by:
    - alertname
    - job
    - severity
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 2h

receivers:
  - name: webhook-default
    webhook_configs:
      - url: ${ALERTMANAGER_WEBHOOK_URL}
        send_resolved: true
```

**Alert Routing**:

- **group_by**: Groups alerts by name, job, and severity to prevent alert storms
- **group_wait: 30s**: Wait 30 seconds before sending the first alert for a group
- **group_interval: 5m**: Send new alerts for a group every 5 minutes
- **repeat_interval: 2h**: Repeat alerts every 2 hours until resolved

### Grafana Dashboards

The project includes pre-configured Grafana dashboards for comprehensive monitoring:

#### 1. LMS API Overview (`lms-api-overview.json`)

This dashboard provides a high-level view of API performance:
- Request rate by endpoint
- Response time percentiles (p50, p95, p99)
- Error rates by status code
- Active connections

#### 2. LMS Course Performance (`lms-course-performance.json`)

Course-specific metrics:
- Enrollment trends over time
- Course completion rates
- Popular courses ranking
- Average course progress

#### 3. LMS Student Progress (`lms-student-progress.json`)

Student engagement metrics:
- Active students over time
- Lessons completed per student
- Quiz attempt statistics
- Time spent learning

#### 4. LMS Security Events (`lms-security-events.json`)

Security monitoring:
- Failed login attempts
- Rate limiting events
- Unusual access patterns
- Token validation failures

#### 5. LMS System Health (`lms-system-health.json`)

Infrastructure monitoring:
- API server health status
- Database connection pool usage
- Redis memory usage
- Celery worker status

### Grafana Provisioning

Dashboards and datasources are automatically provisioned:

**Dashboards Provisioning** (`ops/observability/grafana/provisioning/dashboards/dashboards.yml`):
```yaml
apiVersion: 1

providers:
  - name: 'LMS Dashboards'
    folder: 'LMS'
    type: file
    options:
      path: /var/lib/grafana/dashboards
```

**Datasources Provisioning** (`ops/observability/grafana/provisioning/datasources/prometheus.yml`):
```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

### Running the Observability Stack

Start the complete observability stack with Docker Compose:

```bash
docker-compose -f docker-compose.observability.yml up -d
```

This starts:
- Prometheus (port 9090)
- Grafana (port 3000)
- Alertmanager (port 9093)

---

## CI/CD Pipelines

### Overview

The project uses GitHub Actions for continuous integration and deployment. There are three main workflows:

1. **CI Pipeline** (`ci.yml`): Runs tests and validation
2. **Security Pipeline** (`security.yml`): Security scanning and vulnerability detection
3. **Deploy Pipeline** (`deploy-azure-vm.yml`): Production deployment to Azure VM

### CI Pipeline

Located at `.github/workflows/ci.yml`, this pipeline runs on every push and pull request.

**Triggers**:
- Push to main, develop, feature/**, or chore/** branches
- Pull requests to main or develop branches

**Jobs**:

1. **Test Job** (Python 3.11 and 3.12):
   - Checkout code
   - Setup Python with pip caching
   - Install dependencies
   - Run static sanity checks:
     - Compile all Python files
     - Check for broken dependencies
     - Generate Postman collection
     - Validate JSON files
   - Run tests with coverage (minimum 75%)

2. **PostgreSQL Test Job**:
   - Starts PostgreSQL 16 service container
   - Waits for database to be ready
   - Runs tests against real PostgreSQL database

**Why Two Test Jobs?**:
- First job tests with SQLite for fast feedback
- Second job tests with PostgreSQL to catch database-specific issues

### Security Pipeline

Located at `.github/workflows/security.yml`, this pipeline runs security scans.

**Triggers**:
- Push to main or develop
- Pull requests to main or develop
- Weekly schedule (Monday 3 AM UTC)
- Manual trigger

**Security Scanning Steps**:

1. **Dependency Vulnerability Scan** (pip-audit):
   - Checks all dependencies against known vulnerabilities
   - Strict mode fails on any vulnerability
   - Ignores CVE-2024-23342 (known false positive)

2. **Static Security Scan** (bandit):
   - Finds common security issues in Python code
   - `-lll` flag shows all findings
   - `-ii` flag confirms security issues

3. **Secret Scan** (gitleaks):
   - Scans for leaked credentials
   - Uses GitHub token for authentication
   - Prevents accidental secret commits

**Why These Tools?**:
- **pip-audit**: Official Python security audit tool
- **bandit**: Standard Python static analysis tool
- **gitleaks**: Industry-standard secret detection

### Deploy Pipeline

Located at `.github/workflows/deploy-azure-vm.yml`, this pipeline deploys to production.

**Triggers**:
- Push to main branch
- Manual workflow dispatch

**Deployment Process**:

1. **Checkout**: Get the latest code
2. **Build Archive**: Create a tar.gz of the release
3. **Upload to VM**: Use SCP to transfer to Azure VM
4. **Deploy Script**: Run the deployment script

**Environment Variables Required**:
- `PROD_DATABASE_URL`: Production database connection
- `SECRET_KEY`: JWT signing key
- `APP_DOMAIN`: Production domain
- `LETSENCRYPT_EMAIL`: Email for TLS certificates
- `FRONTEND_BASE_URL`: Frontend application URL
- `CORS_ORIGINS`: Allowed CORS origins
- `TRUSTED_HOSTS`: Allowed hosts
- `SMTP_*`: Email server configuration
- `SENTRY_DSN`: Error tracking configuration

**Why Azure VM?**:
- Full control over the environment
- Easier to customize
- Direct SSH access for debugging
- Cost-effective for medium workloads

### Pipeline Security

All pipelines follow security best practices:

1. **Secrets Management**: All sensitive values stored in GitHub Secrets
2. **Environment Protection**: Production deployments require approval
3. **Artifact Handling**: Release archives don't include git history
4. **Minimal Permissions**: Pipelines use minimal required permissions

---

## Deployment Scripts

### Azure VM Deployment Script

Located at `scripts/deploy_azure_vm.sh`, this script handles the complete deployment process.

**Script Overview**:

```bash
#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/lms_backend}"
ENV_FILE="$APP_DIR/.env"
COMPOSE_FILE="$APP_DIR/docker-compose.prod.yml"
```

**Key Functions**:

1. **require_env()**: Validates required environment variables
2. **upsert_env()**: Updates or inserts environment variables in .env file

**Deployment Steps**:

1. **Create Application Directory**:
   ```bash
   mkdir -p "$APP_DIR"
   cd "$APP_DIR"
   ```

2. **Create Environment File**:
   ```bash
   if [[ ! -f "$ENV_FILE" ]]; then
     cp .env.production.example "$ENV_FILE"
   fi
   ```

3. **Validate Required Variables**:
   - PROD_DATABASE_URL
   - SECRET_KEY
   - APP_DOMAIN
   - LETSENCRYPT_EMAIL
   - SMTP configuration

4. **Set Production Defaults**:
   ```bash
   ENVIRONMENT=production
   DEBUG=false
   ENABLE_API_DOCS=false
   STRICT_ROUTER_IMPORTS=true
   TASKS_FORCE_INLINE=false
   ACCESS_TOKEN_BLACKLIST_FAIL_CLOSED=true
   ```

5. **Pull and Deploy**:
   ```bash
   docker-compose -f "$COMPOSE_FILE" pull
   docker-compose -f "$COMPOSE_FILE" down --remove-orphans
   docker-compose -f "$COMPOSE_FILE" up -d --build
   ```

6. **Health Check**:
   ```bash
   curl http://localhost:8000/api/v1/ready
   ```

### Why This Approach?

1. **Idempotent**: Can be run multiple times safely
2. **Atomic**: Uses transactions and rollback where possible
3. **Verifiable**: Health check ensures deployment success
4. **Configurable**: All settings through environment variables

---

## Infrastructure Configuration

### Docker Compose Production Configuration

The production Docker Compose (`docker-compose.prod.yml`) extends the base configuration with production-specific settings:

```yaml
services:
  api:
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 4G
    environment:
      - DEBUG=false
      - ENVIRONMENT=production

  celery-worker:
    deploy:
      replicas: 2
    command: celery -A app.tasks.celery_app worker --loglevel=info

  db:
    image: postgres:14-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
```

### Environment Variables for Production

| Variable | Description | Example |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection | postgresql://user:pass@host:5432/db |
| REDIS_URL | Redis connection | redis://host:6379/0 |
| SECRET_KEY | JWT signing key | 64-char random string |
| ENVIRONMENT | Deployment environment | production |
| DEBUG | Debug mode | false |
| CORS_ORIGINS | Allowed origins | https://app.example.com |
| SMTP_HOST | Email server | smtp.example.com |
| SMTP_PORT | Email port | 587 |
| SENTRY_DSN | Error tracking | https://sentry.io/... |

### SSL/TLS Configuration

Production uses Let's Encrypt through Caddy:

1. **Automatic Certificate Management**: Caddy obtains and renews certificates
2. **HTTP/2 Support**: Enabled for improved performance
3. **Security Headers**: HSTS, CSP, X-Frame-Options

### Monitoring Integration

Production includes full monitoring:

1. **Prometheus Scraping**: Metrics at /metrics endpoint
2. **Grafana Dashboards**: Pre-configured monitoring views
3. **Alertmanager**: Automated alert notifications
4. **Sentry Integration**: Error tracking and performance monitoring

---

## Summary

The operations infrastructure provides a complete, production-ready deployment solution:

1. **Caddy**: Simple reverse proxy with automatic HTTPS
2. **Observability Stack**: Complete monitoring with Prometheus, Grafana, and Alertmanager
3. **CI/CD**: Automated testing and deployment through GitHub Actions
4. **Deployment Script**: Reliable, idempotent deployment process
5. **Security**: Production-hardened configuration with proper defaults

This infrastructure enables:
- Fast development cycles with automated testing
- Reliable deployments with health checks
- Comprehensive monitoring and alerting
- Easy scaling and maintenance
