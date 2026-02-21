# Observability Guide

This document outlines the observability strategy for the LMS backend in production environments.

## 1. Overview

The LMS backend uses a comprehensive observability stack with:
- **Metrics**: Prometheus + Grafana
- **Tracing**: Sentry (APM)
- **Logging**: Centralized logging (to be implemented)
- **Alerting**: Alertmanager

## 2. Metrics Collection

### 2.1 Prometheus Configuration
The Prometheus configuration is located at `ops/observability/prometheus/prometheus.yml` and includes:
- Target scraping for LMS API, PostgreSQL, Redis, and system metrics
- Alert rules for critical thresholds
- Recording rules for derived metrics

### 2.2 Key Metrics Categories

#### Application Metrics
- HTTP request rates, errors, and latency
- Authentication success/failure rates
- Course enrollment and completion rates
- Quiz attempt and pass rates
- Certificate issuance rates

#### System Metrics
- CPU, memory, and disk usage
- Database connection pool utilization
- Redis client connections and memory usage
- Celery worker queue lengths
- File upload/download rates

#### Business Metrics
- Active users by role (student, instructor, admin)
- Course completion rates
- Student engagement scores
- Instructor workload metrics

## 3. Grafana Dashboards

The following dashboards are available:

### 3.1 LMS Course Performance Dashboard
- Course completion rates
- API request rates and latency
- Student progress overview
- Quiz performance metrics
- Instructor workload metrics

### 3.2 LMS Student Progress Dashboard
- Individual student progress tracking
- Lesson type completion rates
- Quiz performance per student
- Certificate issuance tracking
- Student engagement scores

### 3.3 LMS System Health Dashboard
- Infrastructure resource utilization (CPU, memory, disk)
- API request rates and error rates
- Latency percentiles (P95, P99)
- Database and Redis connection metrics
- Celery queue monitoring

### 3.4 LMS Security Events Dashboard
- Failed login attempts
- Rate limit violations
- Suspicious activity detection
- Access control events (unauthorized/forbidden requests)
- Authentication-related events (password resets, email verification, MFA)

## 4. Alerting Strategy

### 4.1 Critical Alerts (Page immediately)
- API error rate > 5%
- Database connection pool > 90% utilization
- High latency (P95 > 2s)
- Failed login attempts > 10/min from single IP
- Service unavailability (health check failures)

### 4.2 Warning Alerts (Notify via Slack/email)
- API error rate > 2%
- Resource utilization > 70%
- Queue backlogs > 100 items
- Rate limit violations > 5/min
- Security events threshold exceeded

### 4.3 Informational Alerts (Log only)
- Normal operational events
- Scheduled maintenance notifications
- Capacity planning alerts

## 5. Production Deployment Steps

1. **Verify Prometheus targets**: Ensure all services are being scraped
2. **Import dashboards**: Load all LMS-specific dashboards into Grafana
3. **Configure alerting**: Set up Alertmanager routes and receivers
4. **Test alerts**: Trigger test alerts to verify notification channels
5. **Monitor for 24 hours**: Observe metrics and alert behavior

## 6. Verification Commands

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana dashboards
curl -u admin:admin http://localhost:3000/api/search

# Test alert rules
promtool check rules ops/observability/prometheus/alerts.yml
```

## 7. Troubleshooting

### Common Issues:
- **Dashboard not showing data**: Verify Prometheus targets and metric names
- **Alerts not firing**: Check Alertmanager configuration and routing
- **High latency**: Investigate database queries and Redis performance
- **Missing metrics**: Verify application instrumentation and export endpoints

### Debugging:
- Use Prometheus query explorer to validate metric availability
- Check application logs for instrumentation errors
- Verify network connectivity between services
- Review scrape configurations for correct endpoints