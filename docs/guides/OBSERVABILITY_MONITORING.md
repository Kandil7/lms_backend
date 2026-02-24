# Observability & Monitoring: Running a Reliable LMS

A production backend is only as good as its visibility. This guide covers how we track errors, monitor performance, and keep the system healthy.

---

## 📋 Table of Contents
1. [The Three Pillars of Observability](#1-the-three-pillars-of-observability)
2. [Error Tracking with Sentry](#2-error-tracking-with-sentry)
3. [Metrics with Prometheus & Grafana](#3-metrics-with-prometheus--grafana)
4. [Logging Strategy](#4-logging-strategy)
5. [Health & Readiness Checks](#5-health--readiness-checks)

---

## 1. The Three Pillars of Observability
- **Metrics**: Numerical data over time (e.g., "Requests per second").
- **Logs**: Discrete events (e.g., "User X enrolled in Course Y").
- **Traces**: The journey of a single request across services.

---

## 2. Error Tracking with Sentry
We use **Sentry** to capture every unhandled exception in real-time.

- **Automatic Capture**: The FastAPI middleware captures all 500-level errors.
- **Context**: Sentry includes the request headers, user ID, and stack trace.
- **Performance**: We also use Sentry for "Transaction Monitoring" to find slow database queries or API endpoints.

---

## 3. Metrics with Prometheus & Grafana
Numerical health is exposed at the `/metrics` endpoint.

### Key Metrics Tracked:
- **HTTP**: Request duration (latency), status code counts.
- **Database**: Pool usage (active vs. idle connections).
- **System**: CPU/Memory usage of the API and Celery workers.
- **Business**: Number of active users, course enrollments, and quiz attempts.

### Visualization:
We use **Grafana** to build dashboards that visualize these metrics, allowing us to spot trends (like a slow memory leak) before they crash the system.

---

## 4. Logging Strategy
Logs are our primary source for debugging specific user issues.

- **Structured Logging**: Logs are produced in a machine-readable format (JSON in production).
- **Log Levels**:
  - `DEBUG`: Verbose info for development only.
  - `INFO`: Standard operational events (starts, stops, success).
  - `WARNING`: Recoverable errors (e.g., invalid login).
  - `ERROR`: System failures that need attention.
- **Redaction**: As mentioned in the [Security Deep Dive](./SECURITY_DEEP_DIVE.md), we automatically redact PII (Personally Identifiable Information) from logs.

---

## 5. Health & Readiness Checks
The load balancer and Docker use these endpoints to manage traffic:

- **Liveness (`/health`)**: Returns `200 OK` if the process is alive.
- **Readiness (`/api/v1/ready`)**: Returns `200 OK` only if **both** the Database and Redis are connected and responsive.

---

## 🛠️ Operational Dashboard
If you are on-call, these are your primary tools:
1. **Sentry Dashboard**: For new error alerts.
2. **Grafana Dashboards**: For traffic spikes or high latency.
3. **Flower UI**: For Celery task failure rates.
4. **Caddy/Nginx Logs**: For low-level network issues or SSL failures.
