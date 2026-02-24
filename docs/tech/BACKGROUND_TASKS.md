# Background Tasks Documentation

This document covers all background task processing in the LMS Backend using Celery.

## Table of Contents

1. [Celery Configuration](#celery-configuration)
2. [Task Types](#task-types)
3. [Task Dispatching](#task-dispatching)
4. [Queue Management](#queue-management)
5. [Monitoring](#monitoring)

---

## Celery Configuration

**File**: `app/tasks/celery_app.py`

### Overview

Celery is configured for distributed task processing with:
- Redis as message broker
- Redis as result backend
- Multiple queues for different task types
- Automatic retry with exponential backoff

### Configuration

```python
from celery import Celery

celery_app = Celery(
    "lms_backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.certificate_tasks",
        "app.tasks.progress_tasks",
        "app.tasks.webhook_tasks",
    ],
)

# Task settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,  # Restart after 1000 tasks
)
```

### Celery Beat Schedule

For scheduled tasks:

```python
celery_app.conf.beat_schedule = {
    "cleanup-expired-sessions": {
        "task": "app.tasks.misc_tasks.cleanup_expired_sessions",
        "schedule": 3600.0,  # Every hour
    },
    "generate-daily-analytics": {
        "task": "app.tasks.analytics_tasks.generate_daily_analytics",
        "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
    },
}
```

---

## Task Types

### Email Tasks

**File**: `app/tasks/email_tasks.py`

Handles all email-related background tasks.

#### Tasks

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(SMTPException, ConnectionError),
)
def send_welcome_email(self, user_id: str, email: str, name: str):
    """Send welcome email to new users"""
    # Create email content
    # Send via SMTP or Firebase
    pass

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_password_reset_email(self, email: str, name: str, reset_token: str):
    """Send password reset email"""
    pass

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_enrollment_confirmation(
    self, user_id: str, email: str, course_name: str
):
    """Send enrollment confirmation email"""
    pass

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_certificate_email(
    self, user_id: str, email: str, certificate_url: str, course_name: str
):
    """Send certificate notification email"""
    pass
```

#### Email Provider Options

1. **SMTP** - Direct email sending via SMTP
2. **Firebase Cloud Functions** - Use Firebase for email sending

```python
# Configuration
SMTP_HOST: str | None
SMTP_PORT: int = 587
SMTP_USERNAME: str | None
SMTP_PASSWORD: str | None
SMTP_USE_TLS: bool = True

FIREBASE_ENABLED: bool = False
FIREBASE_FUNCTIONS_URL: str | None  # For sending emails via cloud function
```

---

### Certificate Tasks

**File**: `app/tasks/certificate_tasks.py`

Handles certificate generation and delivery.

#### Tasks

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def generate_certificate(self, enrollment_id: str):
    """Generate PDF certificate for completed course"""
    try:
        # 1. Get enrollment details
        enrollment = get_enrollment(enrollment_id)
        
        # 2. Verify completion requirements met
        if not enrollment.is_complete:
            raise ValueError("Enrollment not complete")
        
        # 3. Generate unique certificate number
        cert_number = generate_certificate_number()
        
        # 4. Create PDF
        pdf_bytes = create_certificate_pdf(
            user=enrollment.user,
            course=enrollment.course,
            certificate_number=cert_number,
        )
        
        # 5. Upload to storage
        pdf_url = upload_certificate_pdf(cert_number, pdf_bytes)
        
        # 6. Save certificate record
        certificate = save_certificate(
            enrollment_id=enrollment_id,
            certificate_number=cert_number,
            pdf_url=pdf_url,
        )
        
        # 7. Send notification email
        send_certificate_email.delay(
            user_id=str(enrollment.user.id),
            email=enrollment.user.email,
            certificate_url=pdf_url,
            course_name=enrollment.course.title,
        )
        
        return {"certificate_id": str(certificate.id), "url": pdf_url}
    
    except Exception as exc:
        # Retry on failure
        self.retry(exc=exc)
```

#### Certificate PDF Generation

Uses ReportLab for PDF creation:

```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

def create_certificate_pdf(
    user: User,
    course: Course,
    certificate_number: str,
) -> bytes:
    """Generate PDF certificate"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Title
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(4.25 * inch, 7 * inch, "Certificate of Completion")
    
    # Course name
    c.setFont("Helvetica", 24)
    c.drawCentredString(4.25 * inch, 6 * inch, course.title)
    
    # Student name
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(4.25 * inch, 5 * inch, user.full_name)
    
    # Date
    c.setFont("Helvetica", 14)
    c.drawCentredString(
        4.25 * inch, 4 * inch, 
        f"Completed on {datetime.now().strftime('%B %d, %Y')}"
    )
    
    # Certificate number
    c.setFont("Helvetica", 10)
    c.drawCentredString(
        4.25 * inch, 1 * inch,
        f"Certificate No: {certificate_number}"
    )
    
    c.save()
    buffer.seek(0)
    return buffer.read()
```

---

### Progress Tracking Tasks

**File**: `app/tasks/progress_tasks.py`

Handles student progress tracking and analytics.

#### Tasks

```python
@celery_app.task(bind=True)
def update_enrollment_progress(self, enrollment_id: str, lesson_id: str):
    """Update progress when lesson is completed"""
    enrollment = get_enrollment(enrollment_id)
    lesson = get_lesson(lesson_id)
    
    # Calculate new progress
    completed_lessons = count_completed_lessons(enrollment, lesson.course)
    total_lessons = count_total_lessons(lesson.course)
    progress = int((completed_lessons / total_lessons) * 100)
    
    # Update enrollment
    enrollment.progress_percentage = progress
    if progress == 100:
        enrollment.completed_at = datetime.now(UTC)
    
    save_enrollment(enrollment)
    
    # Check for course completion
    if progress == 100:
        trigger_course_completion(enrollment_id)
    
    return {"progress": progress}

@celery_app.task(bind=True)
def trigger_course_completion(self, enrollment_id: str):
    """Handle course completion"""
    enrollment = get_enrollment(enrollment_id)
    
    # Generate certificate
    generate_certificate.delay(enrollment_id)
    
    # Send completion notification
    send_course_completion_email.delay(
        user_id=str(enrollment.user_id),
        course_id=str(enrollment.course_id),
    )
    
    # Update analytics
    update_course_completion_analytics(enrollment.course_id)

@celery_app.task(bind=True)
def calculate_course_completion_rate(self, course_id: str):
    """Calculate and cache course completion rate"""
    enrollments = get_course_enrollments(course_id)
    completed = sum(1 for e in enrollments if e.completed_at is not None)
    rate = (completed / len(enrollments) * 100) if enrollments else 0
    
    # Cache the result
    cache.set(f"completion_rate:{course_id}", rate, ttl=3600)
    
    return {"course_id": course_id, "completion_rate": rate}
```

---

### Webhook Tasks

**File**: `app/tasks/webhook_tasks.py`

Handles external webhook notifications.

#### Tasks

```python
import httpx

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def dispatch_webhook(self, event_type: str, payload: dict, webhook_url: str = None):
    """Dispatch webhook to external service"""
    # Get webhook URL if not provided
    if not webhook_url:
        webhook_url = get_webhook_url(event_type)
    
    if not webhook_url:
        return
    
    # Sign payload
    signed_payload = sign_payload(payload)
    
    # Send webhook
    try:
        response = httpx.post(
            webhook_url,
            json=signed_payload,
            timeout=settings.WEBHOOK_TIMEOUT_SECONDS,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signed_payload["signature"],
                "X-Webhook-Event": event_type,
            },
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        self.retry(exc=exc)

@celery_app.task(bind=True)
def dispatch_webhooks_batch(self, event_type: str, payload: dict):
    """Dispatch to all registered webhooks"""
    webhook_urls = get_registered_webhooks(event_type)
    
    for url in webhook_urls:
        dispatch_webhook.delay(event_type, payload, url)
```

#### Webhook Events

| Event | Description | Payload |
|-------|-------------|---------|
| `user.registered` | New user registered | `{user_id, email, role}` |
| `course.enrolled` | User enrolled | `{user_id, course_id}` |
| `course.completed` | Course completed | `{user_id, course_id, certificate_id}` |
| `payment.completed` | Payment successful | `{payment_id, amount, course_id}` |
| `certificate.generated` | Certificate created | `{certificate_id, user_id, course_id}` |

---

## Task Dispatching

### Dispatcher Pattern

**File**: `app/tasks/dispatcher.py`

Centralized task dispatching:

```python
from app.tasks.email_tasks import (
    send_welcome_email,
    send_password_reset_email,
    send_enrollment_confirmation,
)
from app.tasks.certificate_tasks import generate_certificate
from app.tasks.progress_tasks import update_enrollment_progress
from app.tasks.webhook_tasks import dispatch_webhooks_batch

class TaskDispatcher:
    @staticmethod
    def dispatch_welcome(user_id: str, email: str, name: str):
        if settings.TASKS_FORCE_INLINE:
            send_welcome_email(user_id, email, name)
        else:
            send_welcome_email.delay(user_id, email, name)
    
    @staticmethod
    def dispatch_enrollment(user_id: str, course_id: str, email: str, course_name: str):
        if settings.TASKS_FORCE_INLINE:
            send_enrollment_confirmation(user_id, email, course_name)
            update_enrollment_progress.delay(...)  # Still async
        else:
            send_enrollment_confirmation.delay(user_id, email, course_name)
    
    @staticmethod
    def dispatch_certificate(enrollment_id: str):
        if settings.TASKS_FORCE_INLINE:
            generate_certificate(enrollment_id)
        else:
            generate_certificate.delay(enrollment_id)
```

### Inline Execution

For development/testing, tasks can run inline:

```python
# Configuration
TASKS_FORCE_INLINE: bool = False  # Run async in production
```

When enabled, tasks execute synchronously - useful for:
- Local development
- Unit testing
- Debugging

---

## Queue Management

### Queue Configuration

```python
# Define queues
CELERY_TASK_ROUTES = {
    "app.tasks.email_tasks.*": {"queue": "emails"},
    "app.tasks.certificate_tasks.*": {"queue": "certificates"},
    "app.tasks.progress_tasks.*": {"queue": "progress"},
    "app.tasks.webhook_tasks.*": {"queue": "webhooks"},
}
```

### Queue Purposes

| Queue | Purpose | Priority |
|-------|---------|----------|
| `celery` | Default tasks | Low |
| `emails` | Email sending | Medium |
| `certificates` | PDF generation | Low |
| `progress` | Progress updates | Medium |
| `webhooks` | External notifications | Low |

### Worker Configuration

```yaml
# docker-compose.yml
celery-worker:
  command: celery -A app.tasks.celery_app.celery_app worker \
    --loglevel=info \
    --queues=emails,progress,certificates,webhooks \
    --concurrency=4
```

### Scaling Workers

```bash
# Start workers for specific queues
celery -A app.tasks.celery_app worker -Q emails --concurrency=8
celery -A app.tasks.celery_app worker -Q certificates --concurrency=2
celery -A app.tasks.celery_app worker -Q default --concurrency=4
```

---

## Monitoring

### Celery Flower

Real-time Celery monitoring:

```bash
# Install
pip install flower

# Run
celery -A app.tasks.celery_app flower --port=5555
```

Features:
- Worker status
- Task history
- Queue monitoring
- Task execution time

### Prometheus Metrics

Export Celery metrics:

```python
from celery_prometheus_exporter import start_prometheus_metrics_server

# Start metrics server
start_prometheus_metrics_server()
```

Available metrics:
- `celery_tasks_total` - Total tasks by state
- `celery_task_duration_seconds` - Task execution time
- `celery_workers` - Active workers

### Logging

Task logging configuration:

```python
celery_app.conf.update(
    worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)
```

---

## Error Handling

### Automatic Retries

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # seconds
    autoretry_for=(SMTPException, ConnectionError, TimeoutError),
    retry_backoff=True,  # Exponential backoff
    retry_backoff_max=600,  # Max 10 minutes
)
def send_email_with_retry(self, ...):
    # Task code
    pass
```

### Manual Retry

```python
@celery_app.task(bind=True)
def task_with_manual_retry(self, ...):
    try:
        # Do work
        pass
    except SpecificException as exc:
        # Retry after 5 minutes
        self.retry(exc=exc, countdown=300)
```

### Task States

```python
from celery.result import AsyncResult

# Check task state
result = AsyncResult(task_id)
print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE

# Get result
if result.ready():
    print(result.get())
```

---

## Testing

### Unit Testing Tasks

```python
from unittest.mock import patch, MagicMock

@patch("app.tasks.email_tasks.send_email")
def test_welcome_email(mock_send):
    # Call task synchronously
    send_welcome_email("user_id", "test@test.com", "Test User")
    
    # Verify was called
    mock_send.assert_called_once()
```

### Integration Testing

```python
import pytest
from celery import Celery

@pytest.fixture
def celery_app():
    app = Celery("test")
    app.config_from_object({"task_always_eager": True})
    return app

def test_task_execution(celery_app):
    result = add.delay(2, 3)
    assert result.get(timeout=10) == 5
```

---

## Performance Considerations

### Task Optimization

1. **Idempotency** - Tasks should be idempotent (safe to retry)
2. **Small Payloads** - Keep payload size minimal
3. **Lazy Loading** - Import heavy modules inside tasks
4. **Batch Operations** - Combine multiple operations

### Worker Sizing

| Queue | Recommended Workers | Rationale |
|-------|---------------------|-----------|
| `emails` | 2-4 | I/O bound, need concurrency |
| `certificates` | 1-2 | CPU intensive |
| `progress` | 2-4 | Frequent, low latency needed |
| `webhooks` | 1-2 | Depends on external services |

### Monitoring Metrics

Key metrics to monitor:
- Task queue depth
- Task execution time
- Task failure rate
- Worker CPU/memory usage
- Broker connection status
