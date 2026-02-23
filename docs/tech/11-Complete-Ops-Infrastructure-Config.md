# Complete Ops and Infrastructure Configuration Documentation

This comprehensive documentation details all operational infrastructure configurations in the LMS Backend project. The ops/ directory contains critical infrastructure-as-code configurations for reverse proxy, monitoring, alerting, and visualization. Each component is explained with its purpose, configuration details, and integration points.

---

## Caddy Reverse Proxy Configuration

### Overview

The Caddy web server serves as the reverse proxy and TLS termination point in production deployments. Caddy was chosen over Nginx and Traefik for its automatic HTTPS capability, declarative configuration syntax, and minimal resource footprint. The automatic certificate management eliminates manual certificate renewal processes.

### Configuration File: ops/caddy/Caddyfile

**Location**: ops/caddy/Caddyfile

**Purpose**: Defines the reverse proxy behavior, security headers, and routing rules for production traffic.

**Configuration Analysis**:

```caddy
{
	email {$LETSENCRYPT_EMAIL}
	acme_ca https://acme-v02.api.letsencrypt.org/directory
}
```

This global configuration block sets up Let's Encrypt certificate authority. The email is provided via environment variable for security. The acme_ca directive points to the production Let's Encrypt directory. For testing, you would change this to the staging directory URL.

```caddy
{$APP_DOMAIN} {
	encode zstd gzip
```

The {$APP_DOMAIN} placeholder is replaced at runtime with the APP_DOMAIN environment variable. This allows the same configuration to work across different deployments (production, staging) with different domain names. The encode directive enables compression using both zstd (newer, better compression) and gzip (broader compatibility).

```caddy
	header {
		X-Content-Type-Options nosniff
		X-Frame-Options DENY
		X-XSS-Protection "1; mode=block"
		Referrer-Policy strict-origin-when-cross-origin
		Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
	}
```

The header block adds critical security headers to all responses. X-Content-Type-Options with nosniff prevents browsers from MIME-type sniffing, protecting against content confusion attacks. X-Frame-Options with DENY prevents the site from being embedded in iframes, protecting against clickjacking. X-XSS-Protection enables XSS filtering in older browsers. Referrer-Policy controls information sent in the Referer header. Strict-Transport-Security (HSTS) enforces HTTPS for one year and includes subdomains.

```caddy
	reverse_proxy api:8000
}
```

The reverse_proxy directive forwards all requests to the API service running in the Docker container on port 8000. The hostname "api" refers to the service name in Docker Compose, which Docker's internal DNS resolves to the container's IP address.

**Why Caddy?**: Automatic HTTPS from Let's Encrypt eliminates certificate management overhead. The configuration file is declarative and easy to understand. The Alpine-based image is lightweight. HTTP/2 and HTTP/3 support is built-in. The security headers are easy to configure.

---

## Observability Stack Configuration

### Overview

The observability stack provides comprehensive monitoring, alerting, and visualization capabilities. It consists of Prometheus for metrics collection, Alertmanager for alert routing, and Grafana for visualization. This stack enables proactive monitoring and rapid incident response.

### Prometheus Configuration

#### prometheus.yml

**Location**: ops/observability/prometheus/prometheus.yml

**Purpose**: Configures Prometheus metrics collection, including scrape targets, intervals, and alert rule files.

**Configuration Analysis**:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 30s
```

The global block sets default scrape and evaluation intervals. Scrape interval (15s) determines how often Prometheus collects metrics from targets. Evaluation interval (30s) determines how often Prometheus evaluates alerting rules. These intervals balance metric freshness with resource usage.

```yaml
rule_files:
  - /etc/prometheus/alerts.yml

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093
```

The rule_files directive includes the alert definitions from alerts.yml. The alerting block configures Alertmanager integration, pointing to the alertmanager service on port 9093.

```yaml
scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets:
          - localhost:9090
```

The first scrape target is Prometheus itself, enabling monitoring of the monitoring system.

```yaml
  - job_name: lms_api_prod
    metrics_path: /metrics
    static_configs:
      - targets:
          - host.docker.internal:8000
        labels:
          service: lms-backend
          environment: production
```

This scrape configuration collects metrics from the production LMS API. The metrics_path /metrics is the default Prometheus endpoint exposed by the application. The target host.docker.internal:8000 allows Prometheus running in Docker to access the host machine's port 8000. Labels provide categorization for querying and alerting.

```yaml
  - job_name: lms_api_staging
    metrics_path: /metrics
    static_configs:
      - targets:
          - host.docker.internal:8001
        labels:
          service: lms-backend
          environment: staging
```

Similar configuration for staging environment, pointing to port 8001.

**Why Prometheus?**: Prometheus is the de facto standard for cloud-native monitoring. The pull model works well with containerized applications. Powerful PromQL enables complex queries. Wide ecosystem integration with Grafana and Alertmanager. Active community and CNCF project.

#### alerts.yml

**Location**: ops/observability/prometheus/alerts.yml

**Purpose**: Defines alerting rules for various LMS components and business metrics.

**Alert Groups**:

**LMS Backend Alerts** - Application-level monitoring:
- LMSApiDown: Triggers when API target cannot be scraped for 2 minutes. Severity: critical.
- LMSHighErrorRate: Triggers when 5xx error rate exceeds 5% over 10 minutes. Severity: warning.
- LMSHighP95Latency: Triggers when p95 latency exceeds 750ms for 10 minutes. Severity: warning.
- LMSRateLimitSpike: Triggers when rate-limited requests exceed 2 per second. Severity: warning.

**Database Alerts** - PostgreSQL monitoring:
- LMSDBConnectionHigh: Triggers when database connection usage exceeds 95%. Severity: critical.
- LMSDBSlowQueries: Triggers when slow query rate exceeds 10 per minute. Severity: warning.

**Cache Alerts** - Redis monitoring:
- LMSCacheHitRatioLow: Triggers when cache hit ratio falls below 80%. Severity: warning.
- LMSRedisMemoryHigh: Triggers when Redis memory usage exceeds 90%. Severity: critical.

**Celery Alerts** - Background task monitoring:
- LMSCeleryQueueHigh: Triggers when queue depth exceeds 1000 tasks. Severity: critical.
- LMSCeleryWorkerDown: Triggers when no Celery workers are reporting. Severity: critical.

**Security Alerts** - Authentication monitoring:
- LMSFailedLoginHigh: Triggers when failed logins exceed 50 per 5 minutes. Severity: warning.
- LMSAccountLockoutHigh: Triggers when account lockouts exceed 10 per 10 minutes. Severity: critical.

**User Engagement Alerts** - Business metrics:
- LMSUserDropoutHigh: Triggers when student dropout rate exceeds 20% per hour. Severity: warning.
- LMSCourseCompletionLow: Triggers when course completion rate falls below 60%. Severity: warning.

**Why These Alerts?**: Each alert addresses a critical operational or business metric. The thresholds are starting points that should be adjusted based on actual traffic patterns and acceptable service levels.

---

### Alertmanager Configuration

#### alertmanager.yml

**Location**: ops/observability/alertmanager/alertmanager.yml

**Purpose**: Configures alert routing, grouping, and notification delivery.

**Configuration Analysis**:

```yaml
global:
  resolve_timeout: 5m
```

The resolve_timeout determines how long Alertmanager waits for an alert to be resolved before notifying. This prevents flapping alerts from creating notification storms.

```yaml
route:
  receiver: webhook-default
  group_by:
    - alertname
    - job
    - severity
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 2h
```

The route block configures alert routing. The receiver specifies where to send notifications. Grouping combines alerts into single notifications to reduce noise. Group wait (30s) waits for initial alerts before sending the first notification. Group interval (5m) determines how often new grouped alerts are sent. Repeat interval (2h) determines how often alert notifications are repeated if still firing.

```yaml
receivers:
  - name: webhook-default
    webhook_configs:
      - url: ${ALERTMANAGER_WEBHOOK_URL}
        send_resolved: true
```

The receivers block defines notification destinations. This configuration sends alerts to a webhook URL specified by environment variable. The send_resolved option notifies when alerts resolve.

**Why Alertmanager?**: Centralized alert management reduces notification noise. Grouping prevents alert storms. Routing enables different alerts to go to different teams. Integration with common notification channels.

---

### Grafana Dashboards

#### Dashboard Files

**Location**: ops/observability/grafana/dashboards/

The project includes pre-configured Grafana dashboards for comprehensive monitoring:

**lms-api-overview.json**: High-level API metrics including request rate, error rate, response time, and active users.

**lms-api-performance.json**: Detailed API performance metrics including endpoint-level latency, throughput, and error breakdowns.

**lms-user-engagement.json**: User engagement metrics including active users, session duration, and feature usage.

**lms-student-progress.json**: Student-specific metrics including course enrollment, lesson completion rates, quiz performance, and certification rates.

**lms-course-performance.json**: Course-level metrics including enrollment trends, completion rates, popular courses, and drop-off analysis.

**lms-security-events.json**: Security metrics including login attempts, authentication failures, lockout events, and suspicious activity.

**lms-system-health.json**: Overall system health including database connectivity, Redis status, API availability, and Celery worker status.

#### Provisioning Configuration

**Location**: ops/observability/grafana/provisioning/

Datasource and dashboard provisioning enable automatic configuration:

**datasources/prometheus.yml**: Configures Prometheus as the datasource with appropriate access settings.

**dashboards/dashboards.yml**: Enables dashboard provisioning from the dashboards directory.

---

## Docker Compose Observability Stack

### docker-compose.observability.yml

**Location**: docker-compose.observability.yml

**Purpose**: Defines the complete observability stack as Docker services.

**Services Analysis**:

**Prometheus Service**:
```yaml
prometheus:
  image: prom/prometheus:v2.54.1
  command:
    - --config.file=/etc/prometheus/prometheus.yml
    - --storage.tsdb.path=/prometheus
    - --web.enable-lifecycle
  volumes:
    - ./ops/observability/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - ./ops/observability/prometheus/alerts.yml:/etc/prometheus/alerts.yml:ro
    - prometheus_data:/prometheus
  ports:
    - "9090:9090"
  extra_hosts:
    - "host.docker.internal:host-gateway"
  restart: unless-stopped
```

Prometheus uses version 2.54.1 (specific version for reproducibility). The command-line options specify config file location, data storage path, and enable lifecycle API. Volumes mount configuration files read-only and persistent storage for metrics data. The extra_hosts setting enables Docker-in-Docker metrics collection. Restart policy ensures recovery from failures.

**Alertmanager Service**:
```yaml
alertmanager:
  image: prom/alertmanager:v0.27.0
  command:
    - --config.file=/etc/alertmanager/alertmanager.yml
    - --storage.path=/alertmanager
    - --config.expand-env
  volumes:
    - ./ops/observability/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    - alertmanager_data:/alertmanager
  ports:
    - "9093:9093"
  restart: unless-stopped
```

Similar pattern for Alertmanager with version 0.27.0. The --config.expand-env option enables environment variable expansion in configuration.

**Grafana Service**:
```yaml
grafana:
  image: grafana/grafana:11.2.2
  environment:
    GF_SECURITY_ADMIN_USER: ${GRAFANA_ADMIN_USER:-admin}
    GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin}
    GF_USERS_ALLOW_SIGN_UP: "false"
    GF_AUTH_ANONYMOUS_ENABLED: "false"
  volumes:
    - grafana_data:/var/lib/grafana
    - ./ops/observability/grafana/provisioning/datasources:/etc/grafana/provisioning/datasources:ro
    - ./ops/observability/grafana/provisioning/dashboards:/etc/grafana/provisioning/dashboards:ro
    - ./ops/observability/grafana/dashboards:/etc/grafana/provisioning/dashboards/lms:ro
  ports:
    - "3001:3000"
  depends_on:
    - prometheus
  restart: unless-stopped
```

Grafana version 11.2.2 provides the visualization interface. Environment variables configure admin credentials (override with environment variables). Volumes provision datasources, dashboards, and persistent storage. Port 3001 on host maps to container port 3000 (3000 may conflict with frontend dev server).

---

## GitHub Actions Workflows

### CI Workflow (.github/workflows/ci.yml)

**Purpose**: Continuous integration pipeline that validates code changes through testing and quality gates.

**Triggers**:
- Push to main, develop, feature/*, chore/* branches
- Pull requests to main and develop branches

**Jobs**:

**Test Job** (runs on Python 3.11 and 3.12):
1. Checkout code
2. Setup Python with pip caching
3. Install dependencies
4. Static sanity checks (compileall, pip check, Postman generation, JSON validation)
5. Run pytest with coverage gate (75% minimum)

**Test-Postgres Job**:
1. PostgreSQL service container
2. Wait for database availability
3. Run full test suite against PostgreSQL

**Why This Design?**: Testing against both Python versions ensures compatibility. Matrix strategy runs tests in parallel. PostgreSQL-specific tests catch SQLite-incompatible queries. Coverage gate ensures test investment. Static checks catch obvious issues early.

### Security Workflow (.github/workflows/security.yml)

**Purpose**: Continuous security scanning for vulnerabilities, code issues, and secret leaks.

**Triggers**:
- Push to main, develop branches
- Pull requests to main and develop branches
- Weekly schedule (Monday 03:00 UTC)
- Manual workflow dispatch

**Security Scanning Tools**:

**pip-audit**: Scans Python dependencies for known vulnerabilities. The --strict flag fails on any vulnerability. The --ignore-vuln excludes known false positives.

**bandit**: Static security analysis for Python code. The -r flag scans recursively. The -x tests excludes test directories. The -lll flags show low-level findings. The -ii flag includes informational issues.

**gitleaks**: Scans for secrets committed to the repository. Uses GitHub Actions integration for seamless scanning.

**Why This Design?**: Multiple scanning tools provide layered security. Push and PR triggers catch issues in changes. Weekly scans catch newly discovered vulnerabilities in existing dependencies. Manual trigger enables on-demand scanning.

### Deploy Workflow (.github/workflows/deploy-azure-vm.yml)

**Purpose**: Automated deployment to Azure Virtual Machine on production merges.

**Triggers**:
- Push to main branch
- Manual workflow dispatch

**Deployment Steps**:

1. **Checkout**: Fetch repository code
2. **Build archive**: Create git archive for deployment
3. **Upload to VM**: Use SCP to transfer archive
4. **Deploy on VM**: Use SSH to execute deployment script

**Environment Variables**: The workflow passes numerous environment variables to the VM including database URL, Redis URL, SMTP settings, Sentry configuration, Azure storage settings, and security credentials.

**Why This Design?**: The workflow creates a self-contained deployment package. SSH-based deployment provides full control. Environment variables enable configuration without hardcoding. The deployment script handles the actual installation and startup.

---

## Firebase Cloud Functions

### functions/ Directory

**Location**: functions/

**Purpose**: Serverless email function using Firebase Cloud Functions as an alternative to direct SMTP.

### main.py

**Purpose**: HTTP-triggered Cloud Function for sending emails.

**Function Analysis**:

```python
@https_fn.on_request(
    cors=options.CorsOptions(
        cors_origins=["*"],
        cors_methods=["POST"],
    )
)
def sendEmail(req: https_fn.Request) -> https_fn.Response:
```

The function is an HTTP-triggered Cloud Function. CORS is configured to accept POST requests from any origin (configure restrictively in production).

```python
    if req.method != "POST":
        return https_fn.Response("Only POST requests are accepted", status=405)
```

The function only accepts POST requests, returning 405 Method Not Allowed for other methods.

```python
    try:
        data = req.get_json()
        to_email = data.get("to")
        subject = data.get("subject")
        body = data.get("body")

        if not all([to_email, subject, body]):
            return https_fn.Response(
                json.dumps({"error": "Missing required fields: to, subject, body"}),
                status=400,
                mimetype="application/json"
            )
```

The function validates required fields (to, subject, body). Returns 400 Bad Request if any field is missing.

```python
        # In a real scenario, integrate with an email provider (SendGrid, Resend, etc.)
        # For now, we log the email request.
        logger.info(f"Sending email to: {to_email} | Subject: {subject}")
        
        # Mock success response
        return https_fn.Response(
            json.dumps({
                "success": True, 
                "message_id": "mock-firebase-msg-id-12345",
                "message": "Email request received and logged"
            }),
            status=200,
            mimetype="application/json"
        )
```

The current implementation logs email requests rather than sending. This is a placeholder for integration with email providers like SendGrid, Resend, or Mailgun. Production would integrate with an actual email service.

### requirements.txt

**Location**: functions/requirements.txt

**Dependencies**:
- firebase-admin>=6.2.0: Firebase Admin SDK for Cloud Functions
- firebase-functions>=0.1.0: Firebase Functions SDK

**Why Firebase?**: Firebase Cloud Functions provides serverless compute in the Google Cloud ecosystem. Integration with Firebase Authentication is seamless. The free tier is sufficient for low-volume email sending. Alternative to managing own SMTP infrastructure.

---

## Integration Points

### Caddy to Application

Caddy receives external HTTPS traffic and forwards to the API container. The integration point is the Docker network where "api:8000" resolves to the API container. Health checks in docker-compose.prod.yml verify the API is ready before Caddy proxies requests.

### Prometheus to Application

Prometheus scrapes the /metrics endpoint on the API service. The application exposes Prometheus-format metrics through the prometheus-client library. The extra_hosts setting in docker-compose.observability.yml enables Docker-to-host access.

### Alertmanager to Notifications

Alertmanager receives alerts from Prometheus and routes to webhook endpoints. The ALERTMANAGER_WEBHOOK_URL environment variable configures the destination. Integration supports Slack, PagerDuty, OpsGenie, and custom webhooks.

### Grafana to Prometheus

Grafana uses Prometheus as a datasource for visualization. The provisioning configuration in ops/observability/grafana/provisioning/datasources/ automates datasource setup.

---

## Deployment Procedures

### Starting Observability Stack

```bash
# Using the convenience script
run_observability.bat

# Or directly with Docker Compose
docker compose -f docker-compose.observability.yml up -d
```

### Accessing Services

- Grafana: http://localhost:3001 (admin/admin)
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093

### Configuring Alerts

Modify ops/observability/prometheus/alerts.yml for alert rules. Changes require Prometheus reload (or container restart).

### Customizing Dashboards

Import additional dashboards through Grafana UI or add JSON files to ops/observability/grafana/dashboards/.

---

## Security Considerations

### Caddy Security

- Automatic HTTPS uses Let's Encrypt
- Security headers prevent common attacks
- Non-root container execution

### Prometheus/Grafana Security

- Default credentials should be changed
- Consider network isolation in production
- Secure webhook endpoints

### GitHub Actions Security

- Secrets stored encrypted in GitHub
- Environment protection rules for production
- Audit logging of all actions

---

This comprehensive ops documentation covers all infrastructure configuration in the LMS Backend project. Each component is production-ready and follows industry best practices for monitoring, alerting, and deployment automation.
