# Complete Observability and Metrics Documentation

This document provides comprehensive documentation for the observability and metrics system in the LMS Backend.

---

## Table of Contents

1. [Metrics System](#1-metrics-system)
2. [Prometheus Metrics](#2-prometheus-metrics)
3. [Metrics Middleware](#3-metrics-middleware)
4. [Metrics Endpoint](#4-metrics-endpoint)
5. [Available Metrics](#5-available-metrics)
6. [Sentry Integration](#6-sentry-integration)

---

## 1. Metrics System

**Location:** `app/core/metrics.py`

The metrics system uses Prometheus for collecting and exposing application metrics.

### Dependencies

```bash
pip install prometheus-client
```

### Configuration

```python
from app.core.config import settings

METRICS_ENABLED = True  # Enable metrics collection
METRICS_PATH = "/metrics"  # Metrics endpoint
```

---

## 2. Prometheus Metrics

### Counter

Counts the total number of HTTP requests.

```python
from app.core.metrics import HTTP_REQUESTS_TOTAL

HTTP_REQUESTS_TOTAL.labels(
    method="GET",
    path="/api/v1/courses",
    status="200"
).inc()
```

### Gauge

Tracks the number of in-progress requests.

```python
from app.core.metrics import HTTP_REQUESTS_IN_PROGRESS

# Increment when request starts
HTTP_REQUESTS_IN_PROGRESS.inc()

# Decrement when request completes
HTTP_REQUESTS_IN_PROGRESS.dec()
```

### Histogram

Measures request duration.

```python
from app.core.metrics import HTTP_REQUEST_DURATION_SECONDS

HTTP_REQUEST_DURATION_SECONDS.labels(
    method="GET",
    path="/api/v1/courses"
).observe(0.123)  # Duration in seconds
```

---

## 3. Metrics Middleware

The MetricsMiddleware automatically collects metrics for all HTTP requests.

### Usage

```python
from app.core.metrics import MetricsMiddleware

app.add_middleware(MetricsMiddleware, excluded_paths={"/metrics"})
```

### Functionality

1. Increments in-progress gauge when request starts
2. Records request duration
3. Increments total counter with status code
4. Decrements in-progress gauge when request completes

---

## 4. Metrics Endpoint

Exposes Prometheus-format metrics.

```python
from app.core.metrics import build_metrics_router

# Add metrics router
app.include_router(build_metrics_router("/metrics"))
```

### Endpoint

```
GET /metrics
```

### Response Format

```prometheus
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/api/v1/courses",status="200"} 1234

# HELP http_request_duration_seconds HTTP request latency in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",path="/api/v1/courses",le="0.1"} 987
http_request_duration_seconds_bucket{method="GET",path="/api/v1/courses",le="0.25"} 1123
http_request_duration_seconds_bucket{method="GET",path="/api/v1/courses",le="0.5"} 1189

# HELP http_requests_in_progress In-progress HTTP requests
# TYPE http_requests_in_progress gauge
http_requests_in_progress 3
```

---

## 5. Available Metrics

### http_requests_total

Total number of HTTP requests.

| Label | Type | Description |
|-------|------|-------------|
| method | string | HTTP method (GET, POST, etc.) |
| path | string | Request path |
| status | string | Response status code |

### http_request_duration_seconds

Request duration in seconds.

| Label | Type | Description |
|-------|------|-------------|
| method | string | HTTP method |
| path | string | Request path |

### http_requests_in_progress

Number of in-progress requests.

| Label | Type | Description |
|-------|------|-------------|
| (none) | gauge | Current in-progress count |

---

## 6. Sentry Integration

**Location:** `app/core/observability.py`

Sentry provides error tracking and performance monitoring.

### Configuration

```python
from app.core.config import settings

# Environment variables
SENTRY_DSN=https://key@sentry.io/project
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Initialization

```python
from app.core.observability import init_sentry_for_api

# Initialize Sentry
init_sentry_for_api()
```

### Features

- Error tracking
- Performance monitoring
- Release tracking
- Context enrichment

---

## Summary

The observability system provides:

1. **Prometheus Metrics** - For monitoring request rates and durations
2. **Sentry** - For error tracking and performance monitoring
3. **Middleware** - Automatic metrics collection
4. **Endpoint** - Prometheus-compatible metrics export
