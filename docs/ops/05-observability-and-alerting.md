# Observability and Alerting Guide

## 1. Components
- Prometheus for metrics scraping and alert rules.
- Grafana for dashboards.
- Alertmanager for notification routing.
- Sentry for error tracking in API and Celery workers.

## 2. Startup
1. Prepare env file:
```bash
cp .env.observability.example .env.observability
```
2. Start observability stack:
```bat
run_observability.bat
```
3. Start API stack (prod or staging):
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## 3. URLs
- Prometheus: `http://localhost:9090`
- Alertmanager: `http://localhost:9093`
- Grafana: `http://localhost:3001`
- Metrics endpoint: `http://localhost:8000/metrics` (prod) or `http://localhost:8001/metrics` (staging)

## 4. Grafana Dashboard
- Provisioned dashboard:
  - `ops/observability/grafana/dashboards/lms-api-overview.json`
- Key panels:
  - requests/sec
  - 5xx error rate
  - p95 latency
  - request rate by status
  - top endpoints

## 5. Alert Rules
- Rules file:
  - `ops/observability/prometheus/alerts.yml`
- Default alerts:
  - API target down
  - high 5xx error rate
  - high p95 latency
  - rate limit spikes (429)

## 6. Sentry Setup
Configure in `.env`:
```env
SENTRY_DSN=<your-sentry-dsn>
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=<git-sha-or-version>
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.0
SENTRY_SEND_PII=false
SENTRY_ENABLE_FOR_CELERY=true
```

Code integration points:
- API: `app/main.py`
- Celery: `app/tasks/celery_app.py`
- Shared setup: `app/core/observability.py`

## 7. Alert Routing
- Set `ALERTMANAGER_WEBHOOK_URL` in `.env.observability` to your incident channel receiver.
- Validate by firing a test alert from Prometheus UI (`/alerts`) and confirming delivery.

