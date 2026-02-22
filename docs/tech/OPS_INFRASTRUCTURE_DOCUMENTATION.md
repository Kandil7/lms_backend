# Operations Infrastructure Documentation (ops/)

## Overview

The `ops/` directory contains operational configurations for deployment, reverse proxy, and observability. This folder is designed to be environment-agnostic and can be used with Docker Compose or Kubernetes.

---

## 1. Caddy Reverse Proxy (`ops/caddy/`)

### Files

#### Caddyfile

```caddy
{
    email {$LETSENCRYPT_EMAIL}
}

{$APP_DOMAIN} {
    encode zstd gzip
    reverse_proxy api:8000
}
```

### Configuration Breakdown

#### 1. Global Options Block

```caddy
{
    email {$LETSENCRYPT_EMAIL}
}
```

**Purpose**: Configure ACME (Automated Certificate Management Environment) for Let's Encrypt.

**Why This Structure**:
- **email**: Contact email for certificate notifications
- **Environment Variable**: `{$LETSENCRYPT_EMAIL}` allows configuration without hardcoding

**Decision Rationale**:
- Let's Encrypt is free and automated
- Email required for expiration warnings
- Alternative: Could use CloudFlare, AWS Route53, or other DNS providers

#### 2. Site Block

```caddy
{$APP_DOMAIN} {
    encode zstd gzip
    reverse_proxy api:8000
}
```

**Purpose**: Configure the main application site.

**Components**:

1. **Domain Variable** (`{$APP_DOMAIN}`)
   - Allows flexible domain configuration
   - Example: `lms.example.com`

2. **encode zstd gzip**
   - **zstd**: Broader compression, faster decompression
   - **gzip**: Legacy browser support
   - Why both? Maximum compatibility with performance

3. **reverse_proxy api:8000**
   - Routes traffic to API container
   - **api:8000**: Docker Compose service name and port
   - Health-aware by default

### Why Caddy?

| Feature | Benefit |
|---------|---------|
| Auto HTTPS | No manual certificate management |
| HTTP/3 Support | Faster modern web |
| Simple Config | Single file configuration |
| Graceful Reloads | No downtime on config changes |
| Minimal Memory | Lightweight compared to Nginx |

### Alternative Considerations

- **Nginx**: More control, steeper learning curve
- **Traefik**: Built for containers, automatic service discovery
- **HAProxy**: High performance, complex config

Caddy was chosen for simplicity and automatic HTTPS.

---

## 2. Observability Stack (`ops/observability/`)

### Directory Structure

```
ops/observability/
├── prometheus/
│   ├── prometheus.yml
│   └── alerts.yml
├── grafana/
│   ├── dashboards/
│   │   ├── lms-api-overview.json
│   │   ├── lms-course-performance.json
│   │   ├── lms-student-progress.json
│   │   ├── lms-security-events.json
│   │   └── lms-system-health.json
│   └── provisioning/
│       ├── datasources/
│       │   └── prometheus.yml
│       └── dashboards/
│           └── dashboards.yml
└── alertmanager/
    └── alertmanager.yml
```

### Prometheus Configuration (`ops/observability/prometheus/`)

#### prometheus.yml

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

**Configuration Breakdown**:

1. **Global Settings**
   - `scrape_interval`: How often to collect metrics (15s)
   - `evaluation_interval`: How often to evaluate rules (30s)

2. **Rule Files**
   - Load alert rules from alerts.yml
   - Defines when to trigger alerts

3. **Alertmanagers**
   - Where to send alerts
   - Points to Alertmanager service

4. **Scrape Targets**

   | Job | Target | Labels |
   |-----|--------|--------|
   | prometheus | localhost:9090 | Self-monitoring |
   | lms_api_prod | host.docker.internal:8000 | Production |
   | lms_api_staging | host.docker.internal:8001 | Staging |

**Why These Targets**:
- **prometheus**: Self-monitoring for system health
- **host.docker.internal**: Access host machine from Docker
- **Different ports**: 8000 (prod), 8001 (staging)
- **Labels**: For filtering in Grafana

#### alerts.yml

```yaml
groups:
  - name: lms-backend-alerts
    rules:
      - alert: LMSApiDown
        expr: up{job=~"lms_api_.*"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "LMS API target is down"
          description: "Prometheus cannot scrape {{ $labels.job }} for at least 2 minutes."

      - alert: LMSHighErrorRate
        expr: |
          sum(rate(http_requests_total{job=~"lms_api_.*",status=~"5.."}[5m]))
          /
          clamp_min(sum(rate(http_requests_total{job=~"lms_api_.*"}[5m])), 0.001)
          > 0.05
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High 5xx error rate"
          description: "5xx rate is above 5% on {{ $labels.job }} for 10 minutes."

      - alert: LMSHighP95Latency
        expr: |
          histogram_quantile(
            0.95,
            sum(rate(http_request_duration_seconds_bucket{job=~"lms_api_.*"}[5m])) by (le, job)
          ) > 0.75
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High API latency (p95)"
          description: "p95 request latency is above 750ms on {{ $labels.job }}."

      - alert: LMSRateLimitSpike
        expr: sum(rate(http_requests_total{job=~"lms_api_.*",status="429"}[5m])) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Rate limit spike detected"
          description: "429 responses are above 2 req/s over 5m on {{ $labels.job }}."
```

**Alert Definitions**:

| Alert | Expression | For | Severity | Purpose |
|-------|------------|-----|----------|---------|
| LMSApiDown | `up{job=~"lms_api_.*"} == 0` | 2m | Critical | API unreachable |
| LMSHighErrorRate | 5xx rate > 5% | 10m | Warning | Server errors |
| LMSHighP95Latency | p95 > 750ms | 10m | Warning | Performance degradation |
| LMSRateLimitSpike | 429s > 2/s | 10m | Warning | Possible attack |

**Why These Thresholds**:

1. **LMSApiDown**
   - 2 minutes: Avoid false positives from temporary network issues
   - Critical: Complete service failure

2. **LMSHighErrorRate**
   - 5% threshold: Industry standard for "degraded" service
   - 10 minutes: Avoid reacting to brief spikes

3. **LMSHighP95Latency**
   - 750ms: Reasonable for API responses
   - p95: Captures most user experience (vs p99 which can be outliers)

4. **LMSRateLimitSpike**
   - 2 req/s: Low threshold for early detection
   - Could indicate attack or misbehaving client

### Grafana Configuration (`ops/observability/grafana/`)

#### provisioning/datasources/prometheus.yml

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

**Purpose**: Configure Prometheus as the default data source.

**Key Settings**:
- **access: proxy**: Grafana proxies requests (vs direct)
- **url**: Internal Docker service name
- **editable: false**: Prevent accidental changes

#### provisioning/dashboards/dashboards.yml

```yaml
apiVersion: 1

providers:
  - name: 'LMS Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards/lms
      foldersFromFilesStructure: true
```

**Purpose**: Auto-load dashboards from the dashboards folder.

**Key Settings**:
- **type: file**: Load from filesystem
- **allowUiUpdates: true**: Allow in-app changes
- **path**: Mounted dashboard JSON files

#### Dashboard Files

| Dashboard | Purpose |
|-----------|---------|
| lms-api-overview.json | API request metrics, response times |
| lms-course-performance.json | Course views, completions |
| lms-student-progress.json | Student activity tracking |
| lms-security-events.json | Login failures, rate limits |
| lms-system-health.json | CPU, memory, database metrics |

**Why Separate Dashboards**:
- Different audiences (students, instructors, admins)
- Focused metrics for each use case
- Easier to maintain and update

### Alertmanager Configuration (`ops/observability/alertmanager/`)

#### alertmanager.yml

```yaml
# (See actual file for complete configuration)
```

**Purpose**: Route alerts to appropriate notification channels.

**Key Concepts**:

1. **Route Tree**
   - Matches alerts based on labels
   - Routes to appropriate receiver

2. **Receivers**
   - Email notifications
   - Slack/Teams webhooks
   - PagerDuty integration

3. **Inhibition Rules**
   - Suppress related alerts
   - Reduce alert fatigue

**Why Alertmanager**:
- Deduplicates alerts
- Groups similar alerts
- Manages alert timing
- Routes to multiple channels

---

## Docker Compose Integration

### Observability Stack (`docker-compose.observability.yml`)

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.54.1
    volumes:
      - ./ops/observability/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./ops/observability/prometheus/alerts.yml:/etc/prometheus/alerts.yml:ro
    ports:
      - "9090:9090"
    extra_hosts:
      - "host.docker.internal:host-gateway"

  alertmanager:
    image: prom/alertmanager:v0.27.0
    volumes:
      - ./ops/observability/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    ports:
      - "9093:9093"

  grafana:
    image: grafana/grafana:11.2.2
    volumes:
      - ./ops/observability/grafana/provisioning/datasources:/etc/grafana/provisioning/datasources:ro
      - ./ops/observability/grafana/provisioning/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./ops/observability/grafana/dashboards:/etc/grafana/provisioning/dashboards/lms:ro
    ports:
      - "3001:3000"
```

### Caddy Integration (`docker-compose.prod.yml`)

```yaml
services:
  caddy:
    image: caddy:2-alpine
    volumes:
      - ./ops/caddy/Caddyfile:/etc/caddy/Caddyfile:ro
    ports:
      - "80:80"
      - "443:443"
```

---

## Version Decisions

| Component | Version | Rationale |
|-----------|---------|-----------|
| Prometheus | v2.54.1 | Stable, widely tested |
| Alertmanager | v0.27.0 | Compatible with Prometheus 2.x |
| Grafana | 11.2.2 | Latest stable |
| Caddy | 2-alpine | Latest 2.x, minimal image |

---

## Decision Summary

### Why This Observability Stack?

1. **Prometheus + Grafana**
   - Industry standard
   - Free and open source
   - Large community
   - Extensive integrations

2. **Alertmanager**
   - Native Prometheus integration
   - Flexible routing
   - Deduplication

3. **Caddy**
   - Automatic HTTPS
   - Simple configuration
   - Production-ready

### Why Separate Dashboards?

1. **Separation of Concerns**
   - Different teams need different views
   - Students, instructors, admins

2. **Performance**
   - Smaller dashboard files
   - Faster loading

3. **Maintainability**
   - Easier to update
   - Clear ownership

### Why These Alert Thresholds?

1. **Balanced Sensitivity**
   - Not too sensitive (alert fatigue)
   - Not too lenient (miss real issues)

2. **Industry Best Practices**
   - Based on SRE principles
   - Proven in production
