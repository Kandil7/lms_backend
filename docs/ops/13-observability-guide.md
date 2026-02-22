# Observability Guide for LMS Production Deployment

This document provides comprehensive guidance for setting up observability for the LMS backend in production environments.

## 1. Monitoring Architecture

### 1.1 Components Overview
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboarding
- **Alertmanager**: Alert routing and notification
- **Sentry**: Error tracking and exception monitoring
- **ELK Stack (Optional)**: Log aggregation and analysis

### 1.2 Data Flow
```
Application → Prometheus (metrics) → Grafana (visualization)
Application → Sentry (errors) → Alertmanager (notifications)
Application → Logging → ELK/CloudWatch (logs)
```

## 2. LMS-Specific Metrics

### 2.1 Core API Metrics
- **Request Rate**: Requests per second by endpoint
- **Latency**: p50, p90, p99 latency by endpoint
- **Error Rate**: HTTP 4xx/5xx error rates
- **Throughput**: Bytes transferred per second

### 2.2 User Engagement Metrics
- **Active Users**: DAU, WAU, MAU
- **Course Completion Rate**: % of enrolled users who complete courses
- **Lesson Progress**: Average progress percentage
- **Quiz Performance**: Average scores, pass/fail rates

### 2.3 System Health Metrics
- **Database Connections**: Active connections, pool usage
- **Redis Cache Hit Ratio**: Cache efficiency
- **Celery Worker Queue**: Task queue length, processing time
- **File Upload/Download**: Throughput, success rates

## 3. LMS-Specific Grafana Dashboards

### 3.1 API Performance Dashboard
- Request rate by endpoint (with drill-down)
- Latency distribution (p50, p90, p99)
- Error rate by status code
- Response size distribution

### 3.2 User Engagement Dashboard
- Active users over time
- Course enrollment trends
- Lesson completion rates
- Quiz attempt statistics
- Student performance metrics

### 3.3 System Health Dashboard
- Database health (connections, queries/sec, slow queries)
- Redis cache metrics (hit ratio, memory usage, evictions)
- Celery worker metrics (queue depth, task duration)
- File storage metrics (upload/download rates, errors)

### 3.4 Security Dashboard
- Failed login attempts
- Account lockouts
- API rate limit violations
- Suspicious activity patterns

## 4. Alerting Rules

### 4.1 Critical Alerts (SEV-1)
- API availability < 99% for 5 minutes
- Database connection pool exhausted (> 95%)
- Redis memory usage > 90%
- Celery queue depth > 1000 tasks
- High error rate (> 5% HTTP 5xx) for 5 minutes

### 4.2 Warning Alerts (SEV-2)
- API latency p99 > 2s for 10 minutes
- Cache hit ratio < 80%
- Database slow queries > 100ms
- File upload failures > 1%
- Unusual login patterns (geographic anomalies)

### 4.3 Informational Alerts (SEV-3)
- Daily summary reports
- Weekly capacity utilization
- Monthly security scan results

## 5. Alert Configuration

### 5.1 Prometheus Alert Rules
```yaml
# ops/observability/prometheus/alerts.yml
groups:
  - name: lms-api-alerts
    rules:
      - alert: LMSAPIHighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on LMS API"
          description: "Error rate is {{ $value }}% over last 5 minutes"

      - alert: LMSAPILatencyHigh
        expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High API latency"
          description: "p99 latency is {{ $value }} seconds"

      - alert: LMSDBConnectionHigh
        expr: postgresql_connections{datname="lms"} / postgresql_max_connections > 0.95
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool exhausted"
          description: "Connection usage is {{ $value }}%"

  - name: lms-system-alerts
    rules:
      - alert: LMSCeleryQueueHigh
        expr: celery_queue_length > 1000
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Celery queue depth too high"
          description: "Queue depth is {{ $value }} tasks"
```

## 6. Sentry Configuration

### 6.1 Required Settings
- **SENTRY_DSN**: Production DSN
- **SENTRY_ENVIRONMENT**: "production"
- **SENTRY_RELEASE**: Git commit hash
- **SENTRY_TRACES_SAMPLE_RATE**: 0.1 (10% sampling)
- **SENTRY_PROFILES_SAMPLE_RATE**: 0.0 (disable profiling in production)
- **SENTRY_SEND_PII**: false (disable PII in production)

### 6.2 Error Grouping
- Configure custom fingerprinting for similar errors
- Set up release health monitoring
- Enable user feedback for critical errors

## 7. Log Collection

### 7.1 Required Log Fields
- Timestamp
- Level (INFO, WARNING, ERROR, CRITICAL)
- Service name
- Request ID (for distributed tracing)
- User ID (anonymized)
- Endpoint/path
- Status code
- Duration
- Error details (sanitized)

### 7.2 Retention Policy
- Critical errors: 365 days
- Warnings: 90 days
- Info logs: 30 days
- Debug logs: 7 days (development only)

## 8. Verification Steps

### 8.1 Pre-Production Validation
- [ ] All dashboards render correctly
- [ ] Alert rules trigger as expected
- [ ] Metrics are collected from all services
- [ ] Sentry error reporting works
- [ ] Log collection is functioning

### 8.2 Production Validation
- [ ] Monitor for 24 hours after deployment
- [ ] Verify alert delivery to incident channels
- [ ] Test incident response workflow
- [ ] Validate metric accuracy against business KPIs

## 9. Tools and References

### 9.1 Grafana Dashboard Templates
- [LMS API Dashboard](https://grafana.com/grafana/dashboards/12345) (example)
- [Database Performance](https://grafana.com/grafana/dashboards/67890)
- [System Health](https://grafana.com/grafana/dashboards/54321)

### 9.2 Prometheus Exporters
- `prometheus-fastapi-exporter` for FastAPI metrics
- `redis_exporter` for Redis metrics
- `postgres_exporter` for PostgreSQL metrics
- `celery-exporter` for Celery metrics

## 10. Emergency Procedures

### 10.1 Alert Flood Mitigation
- Temporarily increase alert thresholds
- Disable non-critical alerts
- Route alerts to secondary channel

### 10.2 Metric Collection Failure
- Check exporter health
- Verify network connectivity
- Restart affected services
- Fallback to local logging

## Appendix A: Sample Dashboard JSON

```json
{
  "dashboard": {
    "id": null,
    "uid": "lms-api-performance",
    "title": "LMS API Performance",
    "tags": ["lms", "api", "performance"],
    "timezone": "browser",
    "schemaVersion": 30,
    "version": 0,
    "refresh": "5s",
    "panels": [
      {
        "title": "Request Rate",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (endpoint)",
            "legendFormat": "{{endpoint}}"
          }
        ]
      }
    ]
  }
}
```

**Note**: Adapt dashboard configurations for your specific environment and requirements.