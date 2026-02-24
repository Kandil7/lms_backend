# Background Tasks & Workers (Celery)

To keep the API responsive, we offload heavy or time-consuming operations to background workers. This guide explains how we use Celery and Redis to manage these tasks.

---

## 📋 Table of Contents
1. [Why Use Background Tasks?](#1-why-use-background-tasks)
2. [Task Architecture](#2-task-architecture)
3. [Common LMS Background Tasks](#3-common-lms-background-tasks)
4. [Creating a New Task](#4-creating-a-new-task)
5. [Monitoring and Scaling](#5-monitoring-and-scaling)

---

## 1. Why Use Background Tasks?
If a user action takes more than 200ms, it should likely be handled in the background. Examples include:
- Generating a PDF certificate.
- Sending email notifications.
- Recalculating course-wide progress analytics.
- Processing large file uploads.

---

## 2. Task Architecture
We use a **Producer-Consumer** model:
1. **Producer (FastAPI)**: Dispatches a task to the queue.
2. **Broker (Redis)**: Holds the task messages.
3. **Consumer (Celery Worker)**: Picks up the task and executes it.
4. **Result Backend (Redis)**: Stores the outcome (Success/Failure).

---

## 3. Common LMS Background Tasks
- **Progress Sync**: When a student completes a lesson, a task updates their total course percentage.
- **Certificate Generation**: Triggered automatically when progress reaches 100%.
- **Webhooks**: Notifying external systems (e.g., a CRM) about user enrollments.
- **Email Dispatch**: Sending welcome emails or password reset links.

---

## 4. Creating a New Task
Tasks are defined in `app/tasks/`.

### Step 1: Define the Task
```python
# app/tasks/email_tasks.py
from app.tasks.celery_app import celery_app

@celery_app.task(name="send_welcome_email")
def send_welcome_email(user_email: str, name: str):
    # Logic to send email via SMTP or API
    return f"Email sent to {user_email}"
```

### Step 2: Trigger from the API
```python
# app/modules/auth/router.py
from app.tasks.email_tasks import send_welcome_email

@router.post("/register")
def register(user: UserCreate):
    # ... registration logic ...
    send_welcome_email.delay(user.email, user.full_name)
    return {"status": "User created, email queued"}
```

---

## 5. Monitoring and Scaling

### Monitoring with Flower
We use **Flower**, a real-time web UI for monitoring Celery:
- View active/failed tasks.
- Inspect worker health.
- Retrying failed tasks manually.

### Scaling Workers
In production, we can scale workers independently of the API:
```bash
# Scale up to 5 workers in Docker Compose
docker-compose up -d --scale celery_worker=5
```

---

## ⚠️ Best Practices & Pitfalls
- **Idempotency**: Tasks might run more than once. Ensure your code handles this (e.g., checking if a certificate already exists before creating a new one).
- **Small Payloads**: Pass IDs (like `user_id`) to tasks, not full objects. The worker should fetch fresh data from the DB.
- **Timeouts**: Always set a `time_limit` for tasks to prevent them from hanging indefinitely.
- **Error Handling**: Use `try/except` within tasks and log errors to Sentry.
