# Background Jobs & Celery

## Async Task Processing Architecture

This document explains the background job system, Celery configuration, task routing, and scheduling in this LMS backend.

---

## 1. Why Background Jobs?

### Synchronous vs Async Processing

```
┌─────────────────────────────────────────────────────────────────┐
│              SYNCHRONOUS vs ASYNCHRONOUS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SYNCHRONOUS (Blocking)                                        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│  │ Request  │───►│  Process  │───►│ Response │                 │
│  │          │    │  Email    │    │          │                 │
│  └──────────┘    └──────────┘    └──────────┘                 │
│       │               │                                        │
│       │               │ 5 seconds                               │
│       └───────────────┘                                        │
│                                                                 │
│  User waits for email to send before getting response           │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ASYNCHRONOUS (Non-blocking)                                   │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│  │ Request  │───►│  Queue    │    │ Response │                 │
│  │          │    │  Task     │    │          │                 │
│  └──────────┘    └────┬─────┘    └──────────┘                 │
│       │               │                                        │
│       │               ▼                                        │
│       │         ┌──────────┐    ┌──────────┐                 │
│       │         │  Worker  │───►│  Email   │                 │
│       │         │  Process │    │  Sent    │                 │
│       │         └──────────┘    └──────────┘                 │
│       │                                                   │
│       └─────────── Immediate response (milliseconds)        │
│                                                                 │
│  User gets response immediately, email processes in background │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### What Goes to Background?

| Task | Reason |
|------|--------|
| Send Email | Slow, can retry |
| Generate PDF | CPU intensive |
| Progress Calculation | Not urgent |
| Webhooks | External API calls |
| Scheduled Reports | Batch processing |

---

## 2. Celery Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CELERY ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐                                              │
│   │   FastAPI   │                                              │
│   │   (API)     │                                              │
│   └──────┬──────┘                                              │
│          │                                                     │
│          │ enqueue task                                        │
│          ▼                                                     │
│   ┌─────────────┐                                              │
│   │    Redis    │  (Message Broker)                           │
│   │   (Port 6379)│                                              │
│   └──────┬──────┘                                              │
│          │                                                     │
│          │ consume                                             │
│          ▼                                                     │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐    │
│   │   Celery    │     │   Celery    │     │   Celery    │    │
│   │   Worker    │     │   Worker    │     │   Worker    │    │
│   │  (emails)  │     │(certificates)│     │ (progress) │    │
│   └─────────────┘     └─────────────┘     └─────────────┘    │
│          │                   │                   │            │
│          ▼                   ▼                   ▼            │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐    │
│   │    Send     │     │  Generate   │     │   Update    │    │
│   │    Email    │     │    PDF      │     │   Stats     │    │
│   └─────────────┘     └─────────────┘     └─────────────┘    │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐ │
│   │                    Celery Beat                           │ │
│   │              (Task Scheduler)                            │ │
│   │   ┌─────────────────┐  ┌─────────────────┐            │ │
│   │   │ Weekly Report   │  │ Daily Reminder  │            │ │
│   │   │ Every Monday    │  │ Every Day       │            │ │
│   │   └─────────────────┘  └─────────────────┘            │ │
│   └─────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Celery Configuration

### Main Configuration

```python
# app/tasks/celery_app.py
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "lms_backend",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.certificate_tasks",
        "app.tasks.progress_tasks",
        "app.tasks.webhook_tasks",
    ]
)

# Configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "emails"},
        "app.tasks.certificate_tasks.*": {"queue": "certificates"},
        "app.tasks.progress_tasks.*": {"queue": "progress"},
        "app.tasks.webhook_tasks.*": {"queue": "webhooks"},
    },
    
    # Task execution
    task_acks_late=True,              # Acknowledge after processing
    task_reject_on_worker_lost=True,  # Requeue if worker dies
    worker_prefetch_multiplier=1,     # Fair distribution
    
    # Time limits
    task_time_limit=300,              # Hard timeout (5 minutes)
    task_soft_time_limit=240,         # Graceful cancellation (4 minutes)
    
    # Result backend
    result_expires=3600,              # Results expire after 1 hour
    result_persistent=True,           # Store results in Redis
    
    # Beat schedule
    beat_schedule={
        "weekly-progress-report": {
            "task": "app.tasks.email_tasks.send_weekly_progress_report",
            "schedule": crontab(minute=0, hour=9, day_of_week="monday"),
        },
        "daily-course-reminders": {
            "task": "app.tasks.email_tasks.send_course_reminders",
            "schedule": crontab(minute=0, hour=10),
        },
    },
)
```

### Why These Settings?

| Setting | Value | Reason |
|---------|-------|--------|
| task_acks_late | True | Don't lose tasks if worker dies |
| task_reject_on_worker_lost | True | Requeue abandoned tasks |
| worker_prefetch_multiplier | 1 | Fair distribution |
| task_time_limit | 300s | Prevent stuck tasks |
| task_soft_time_limit | 240s | Graceful cleanup |

---

## 4. Task Categories

### 4.1 Email Tasks

```python
# app/tasks/email_tasks.py
from .celery_app import celery_app
from app.modules.emails.service import EmailService

email_service = EmailService()

@celery_app.task(
    name="app.tasks.email_tasks.send_welcome_email",
    max_retries=3,
    default_retry_delay=60,
)
def send_welcome_email(user_id: str, email: str, full_name: str):
    """Send welcome email to new user"""
    try:
        email_service.send_welcome_email(email, full_name)
    except Exception as exc:
        # Retry on failure
        raise send_welcome_email.retry(exc=exc)

@celery_app.task(
    name="app.tasks.email_tasks.send_password_reset_email",
    max_retries=3,
)
def send_password_reset_email(email: str, reset_token: str):
    """Send password reset email"""
    email_service.send_password_reset(email, reset_token)

@celery_app.task(
    name="app.tasks.email_tasks.send_course_enrolled_email",
    max_retries=3,
)
def send_course_enrolled_email(user_id: str, course_id: str):
    """Send course enrollment confirmation"""
    email_service.send_course_enrolled(user_id, course_id)

@celery_app.task(
    name="app.tasks.email_tasks.send_certificate_email",
    max_retries=3,
)
def send_certificate_email(user_id: str, certificate_id: str):
    """Send certificate issued email"""
    email_service.send_certificate_issued(user_id, certificate_id)

@celery_app.task(
    name="app.tasks.email_tasks.send_weekly_progress_report",
    max_retries=2,
)
def send_weekly_progress_report():
    """Send weekly progress reports to all students"""
    email_service.send_weekly_reports()

@celery_app.task(
    name="app.tasks.email_tasks.send_course_reminders",
    max_retries=2,
)
def send_course_reminders():
    """Send reminders to inactive students"""
    email_service.send_reminders()
```

### Queue: `emails`

- Priority: High
- Retry: 3 attempts, 60s delay
- Timeout: 60s

### 4.2 Certificate Tasks

```python
# app/tasks/certificate_tasks.py
from .celery_app import celery_app
from app.modules.certificates.service import CertificateService

certificate_service = CertificateService()

@celery_app.task(
    name="app.tasks.certificate_tasks.generate_certificate",
    max_retries=2,
    time_limit=120,
)
def generate_certificate(enrollment_id: str):
    """Generate PDF certificate for completed course"""
    certificate_service.generate_certificate(enrollment_id)

@celery_app.task(
    name="app.tasks.certificate_tasks.revoke_certificate",
    max_retries=1,
)
def revoke_certificate(certificate_id: str, reason: str):
    """Revoke a certificate"""
    certificate_service.revoke_certificate(certificate_id, reason)
```

### Queue: `certificates`

- Priority: Medium
- Retry: 2 attempts
- Timeout: 120s (CPU intensive)

### 4.3 Progress Tasks

```python
# app/tasks/progress_tasks.py
from .celery_app import celery_app

@celery_app.task(
    name="app.tasks.progress_tasks.update_enrollment_progress",
    max_retries=2,
)
def update_enrollment_progress(enrollment_id: str):
    """Update enrollment progress percentage"""
    # Recalculate progress based on lesson completion
    pass

@celery_app.task(
    name="app.tasks.progress_tasks.calculate_course_statistics",
    max_retries=1,
)
def calculate_course_statistics(course_id: str):
    """Calculate and cache course statistics"""
    pass

@celery_app.task(
    name="app.tasks.progress_tasks.cleanup_old_progress",
    max_retries=1,
)
def cleanup_old_progress():
    """Clean up old progress records"""
    pass
```

### Queue: `progress`

- Priority: Low
- Batch processing

### 4.4 Webhook Tasks

```python
# app/tasks/webhook_tasks.py
from .celery_app import celery_app

@celery_app.task(
    name="app.tasks.webhook_tasks.dispatch_webhook",
    max_retries=3,
    default_retry_delay=30,
)
def dispatch_webhook(webhook_url: str, event_type: str, payload: dict):
    """Dispatch webhook to external URL"""
    import httpx
    
    try:
        response = httpx.post(
            webhook_url,
            json={"event": event_type, "data": payload},
            timeout=10
        )
        response.raise_for_status()
    except Exception as exc:
        raise dispatch_webhook.retry(exc=exc)
```

### Queue: `webhooks`

- Priority: Medium
- External API calls

---

## 5. Task Dispatching

### Hybrid Execution Model

```python
# app/tasks/dispatcher.py
from app.tasks.celery_app import celery_app
from app.core.config import settings

def send_task(task_name: str, *args, fallback=None, **kwargs):
    """
    Hybrid task dispatcher.
    
    - Development: Execute inline (synchronous)
    - Production: Queue to Celery (asynchronous)
    """
    if settings.TASKS_FORCE_INLINE:
        # Development: Run synchronously
        return _run_fallback(task_name, *args, fallback=fallback, **kwargs)
    else:
        # Production: Queue to Celery
        if enqueue_task(task_name, *args, **kwargs):
            return "queued"
        else:
            # Fallback if queue fails
            if fallback:
                return _run_fallback(task_name, *args, fallback=fallback, **kwargs)
            return "failed"

def enqueue_task(task_name: str, *args, **kwargs):
    """Add task to Celery queue"""
    try:
        celery_app.send_task(task_name, args=args, kwargs=kwargs)
        return True
    except Exception as e:
        logger.error(f"Failed to enqueue task {task_name}: {e}")
        return False

def _run_fallback(task_name: str, *args, fallback=None, **kwargs):
    """Run task synchronously as fallback"""
    if fallback:
        return fallback(*args, **kwargs)
    return None
```

### Usage Example

```python
# In API route
@router.post("/enrollments")
async def enroll_in_course(enrollment_data: EnrollmentCreate, ...):
    # Create enrollment
    enrollment = await create_enrollment(enrollment_data)
    
    # Send email asynchronously (production) or inline (development)
    send_task(
        "app.tasks.email_tasks.send_course_enrolled_email",
        user_id=str(enrollment.student_id),
        course_id=str(enrollment.course_id),
        fallback=lambda: email_service.send_course_enrolled(
            enrollment.student_id, 
            enrollment.course_id
        )
    )
    
    return enrollment
```

---

## 6. Scheduled Tasks (Celery Beat)

### Beat Schedule

```python
# app/tasks/celery_app.py
beat_schedule = {
    # Weekly reports - Every Monday at 9 AM
    "weekly-progress-report": {
        "task": "app.tasks.email_tasks.send_weekly_progress_report",
        "schedule": crontab(minute=0, hour=9, day_of_week="monday"),
    },
    
    # Daily reminders - Every day at 10 AM
    "daily-course-reminders": {
        "task": "app.tasks.email_tasks.send_course_reminders",
        "schedule": crontab(minute=0, hour=10),
    },
    
    # Monthly analytics - First day of month
    "monthly-analytics": {
        "task": "app.tasks.progress_tasks.calculate_monthly_analytics",
        "schedule": crontab(minute=0, hour=2, day_of_month=1),
    },
}
```

### Crontab Expressions

| Expression | Meaning |
|------------|---------|
| `crontab(minute=0, hour=9)` | Daily at 9:00 AM |
| `crontab(minute=0, hour=9, day_of_week="monday")` | Every Monday at 9:00 AM |
| `crontab(minute=0, hour=2, day_of_month=1)` | 1st of every month at 2:00 AM |
| `crontab(minute="*/15")` | Every 15 minutes |

---

## 7. Docker Services

### Docker Compose Configuration

```yaml
# docker-compose.yml
services:
  # Main API
  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql+asyncpg://...
      - REDIS_URL=redis://redis:6379/0
  
  # Celery Worker
  celery_worker:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info -Q emails,certificates,progress,webhooks
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql+asyncpg://...
      - REDIS_URL=redis://redis:6379/0
  
  # Celery Beat (Scheduler)
  celery_beat:
    build: .
    command: celery -A app.tasks.celery_app beat --loglevel=info
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
  
  # Flower (Celery Monitor)
  flower:
    build: .
    command: celery -A app.tasks.celery_app flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
  
  # PostgreSQL
  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

---

## 8. Monitoring with Flower

### Flower Dashboard

```
URL: http://localhost:5555
```

### Features

- View worker status
- Monitor task queue lengths
- View task details and results
- Task history and statistics
- Restart workers

---

## 9. Task Error Handling

### Retry Strategy

```python
@celery_app.task(
    name="app.tasks.email_tasks.send_email",
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(Exception,),  # Auto retry on exception
    retry_backoff=True,  # Exponential backoff
    retry_backoff_max=600,  # Max 10 minutes
    retry_jitter=True,  # Random jitter
)
def send_email_task(email: str, subject: str, template: str):
    # Task logic
    pass
```

### Retry Pattern

```
Attempt 1: Failed → Wait 60s
Attempt 2: Failed → Wait 120s
Attempt 3: Failed → Wait 240s
Attempt 4: Failed → Give up, log error
```

### Error Logging

```python
@celery_app.task(
    name="app.tasks.email_tasks.send_email",
    max_retries=3,
)
def send_email_task(email: str, subject: str, template: str):
    try:
        email_service.send(email, subject, template)
    except Exception as exc:
        logger.error(
            f"Failed to send email to {email}: {exc}",
            extra={"email": email, "subject": subject}
        )
        raise send_email_task.retry(exc=exc)
```

---

## 10. Best Practices

### Task Design

| Practice | Reason |
|----------|--------|
| Idempotency | Safe to retry |
| Small tasks | Better parallelization |
| Avoid blocking | Use async where possible |
| Log failures | For debugging |
| Set timeouts | Prevent stuck tasks |

### Monitoring

- Use Flower for task monitoring
- Set up alerts for failed tasks
- Monitor queue depths
- Track task duration

### Queue Priority

```
High Priority (emails):
  - Welcome emails
  - Password reset
  - Certificate notifications

Medium Priority (certificates, webhooks):
  - PDF generation
  - Webhook dispatch

Low Priority (progress, analytics):
  - Statistics calculation
  - Cleanup tasks
```

---

## Summary

This background job system provides:

| Feature | Implementation |
|---------|----------------|
| Broker | Redis |
| Workers | Multiple queues by task type |
| Scheduling | Celery Beat for cron tasks |
| Error Handling | Retry with exponential backoff |
| Monitoring | Flower dashboard |
| Development | Inline execution fallback |

The hybrid execution model ensures:
- Easy development (no Celery needed)
- Production performance (async processing)
- Reliability (fallback on failure)
