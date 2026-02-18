# Background Jobs and Celery

This document explains the background task architecture, Celery configuration, task definitions, and how to run background jobs.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Celery Configuration](#2-celery-configuration)
3. [Task Definitions](#3-task-definitions)
4. [Task Dispatching](#4-task-dispatching)
5. [Task Queues](#5-task-queues)
6. [Scheduling with Celery Beat](#6-scheduling-with-celery-beat)
7. [Monitoring with Flower](#7-monitoring-with-flower)
8. [Running Background Jobs](#8-running-background-jobs)
9. [Task Best Practices](#9-task-best-practices)

---

## 1. Architecture Overview

### Why Background Jobs?

Background jobs are essential for operations that are:
- **Time-consuming** - PDF generation, bulk operations
- **Non-critical** - Email notifications, analytics
- **Scheduled** - Daily reports, cleanup tasks
- **Resource-intensive** - Video processing, report generation

```
┌──────────────────────────────────────────────────────────────────┐
│                      REQUEST FLOW                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SYNCHRONOUS (User waits):          ASYNC (User doesn't wait): │
│  ─────────────────────────          ─────────────────────────── │
│                                                                  │
│  User → API → Process → Response    User → API → Response       │
│                                      │                          │
│                                      ▼                          │
│                                 Queue (Redis)                    │
│                                      │                          │
│                                      ▼                          │
│                                 Celery Worker                   │
│                                      │                          │
│                                      ▼                          │
│                                 Background Task                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Message Broker | Redis | Store task queue |
| Task Queue | Celery | Manage task execution |
| Scheduler | Celery Beat | Schedule recurring tasks |
| Worker | Celery | Execute tasks |

---

## 2. Celery Configuration

### Celery App Setup

```python
# app/tasks/celery_app.py
from celery import Celery
from celery.schedules import crontab

# Create Celery application
celery_app = Celery("lms")

# Configuration
celery_app.conf.update(
    # Broker settings
    broker_url="redis://redis:6379/0",
    result_backend="redis://redis:6379/1",
    
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_acks_late=True,  # Acknowledge after task completes
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=4,
    
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Task routes (see Task Queues section)
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "emails"},
        "app.tasks.certificate_tasks.*": {"queue": "certificates"},
        "app.tasks.progress_tasks.*": {"queue": "progress"},
    },
    
    # Beat schedule
    beat_schedule={
        "cleanup-expired-tokens": {
            "task": "app.tasks.maintenance.cleanup_expired_tokens",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
        },
        "generate-daily-analytics": {
            "task": "app.tasks.analytics.generate_daily_analytics",
            "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
        },
    },
)
```

### Configuration Options Explained

| Setting | Value | Purpose |
|---------|-------|---------|
| `broker_url` | Redis URL | Message broker connection |
| `result_backend` | Redis URL | Store task results |
| `task_serializer` | json | How to serialize task data |
| `task_acks_late` | true | Don't lose tasks on worker crash |
| `worker_prefetch_multiplier` | 4 | Workers can grab multiple tasks |

---

## 3. Task Definitions

### Email Tasks

```python
# app/tasks/email_tasks.py
from celery import shared_task
from app.tasks.celery_app import celery_app

@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_id: str):
    """Send welcome email to new users."""
    try:
        user = get_user_by_id(user_id)
        
        subject = "Welcome to LMS Platform!"
        body = f"""
        Hi {user.full_name},
        
        Welcome to our Learning Management System!
        We're excited to have you on board.
        
        Get started by exploring our courses.
        """
        
        send_email(
            to=user.email,
            subject=subject,
            body=body
        )
        
        return {"status": "success", "user_id": user_id}
        
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@shared_task(bind=True)
def send_password_reset_email(self, user_id: str, reset_token: str):
    """Send password reset email."""
    user = get_user_by_id(user_id)
    
    reset_url = f"https://app.example.com/reset-password?token={reset_token}"
    
    send_email(
        to=user.email,
        subject="Password Reset Request",
        body=f"Click here to reset your password: {reset_url}"
    )
```

### Certificate Tasks

```python
# app/tasks/certificate_tasks.py
from celery import shared_task
from app.tasks.celery_app import celery_app
import uuid

@shared_task(bind=True, max_retries=3)
def generate_certificate(self, enrollment_id: str):
    """Generate PDF certificate for completed course."""
    try:
        # Get enrollment data
        enrollment = get_enrollment(enrollment_id)
        
        if not enrollment or enrollment.progress_percentage < 100:
            return {"status": "skipped", "reason": "Course not completed"}
        
        # Check if certificate already exists
        if enrollment.certificate:
            return {"status": "skipped", "reason": "Certificate already exists"}
        
        # Generate PDF
        pdf_content = create_certificate_pdf(enrollment)
        
        # Save certificate
        certificate = save_certificate(
            enrollment_id=enrollment_id,
            pdf_content=pdf_content
        )
        
        # Send notification
        send_email(
            to=enrollment.student.email,
            subject="Congratulations! You've earned a certificate!",
            body=f"Your certificate for {enrollment.course.title} is ready!"
        )
        
        return {
            "status": "success",
            "certificate_id": str(certificate.id),
            "certificate_number": certificate.certificate_number
        }
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)

@shared_task
def revoke_certificate(certificate_id: str):
    """Revoke a certificate."""
    certificate = get_certificate(certificate_id)
    certificate.is_revoked = True
    certificate.revoked_at = datetime.utcnow()
    save_certificate(certificate)
```

### Progress Tasks

```python
# app/tasks/progress_tasks.py
from celery import shared_task
from sqlalchemy import select
from app.core.database import AsyncSessionLocal

@shared_task
def recalculate_course_progress(course_id: str):
    """Recalculate progress for all enrollments in a course."""
    async def _recalculate():
        async with AsyncSessionLocal() as db:
            # Get all enrollments for course
            result = await db.execute(
                select(Enrollment).where(Enrollment.course_id == course_id)
            )
            enrollments = result.scalars().all()
            
            for enrollment in enrollments:
                # Recalculate progress
                progress = calculate_enrollment_progress(enrollment)
                enrollment.progress_percentage = progress.percentage
                enrollment.completed_lessons_count = progress.completed
                enrollment.total_lessons_count = progress.total
            
            await db.commit()
    
    return asyncio.run(_recalculate())

@shared_task
def cleanup_stale_progress():
    """Clean up lesson progress entries for dropped enrollments."""
    # Implementation
    ...
```

---

## 4. Task Dispatching

### Task Dispatcher

```python
# app/tasks/dispatcher.py
from app.core.config import settings

class TaskDispatcher:
    """Unified task dispatcher with inline/external execution."""
    
    @staticmethod
    def send_welcome_email(user_id: str):
        """Send welcome email."""
        if settings.TASKS_FORCE_INLINE or settings.ENVIRONMENT == "testing":
            # Run synchronously (development/testing)
            from app.tasks.email_tasks import send_welcome_email
            send_welcome_email(user_id)
        else:
            # Queue for background processing (production)
            send_welcome_email.delay(user_id)
    
    @staticmethod
    def generate_certificate(enrollment_id: str):
        """Generate certificate."""
        if settings.TASKS_FORCE_INLINE:
            from app.tasks.certificate_tasks import generate_certificate
            generate_certificate(enrollment_id)
        else:
            generate_certificate.delay(enrollment_id)
```

### Usage in Services

```python
# app/modules/enrollments/services/enrollment_service.py
from app.tasks.dispatcher import TaskDispatcher
from app.tasks.email_tasks import send_enrollment_confirmation

class EnrollmentService:
    async def enroll_student(self, student_id: UUID, course_id: UUID):
        # Create enrollment
        enrollment = await self.create_enrollment(student_id, course_id)
        
        # Send confirmation email (background)
        TaskDispatcher.send_enrollment_email(str(student_id))
        
        return enrollment
    
    async def complete_course(self, enrollment_id: UUID):
        # Update enrollment
        enrollment = await self.mark_completed(enrollment_id)
        
        # Trigger certificate generation (background)
        TaskDispatcher.generate_certificate(str(enrollment_id))
        
        return enrollment
```

---

## 5. Task Queues

### Queue Architecture

```
                    ┌─────────────┐
                    │   Redis     │
                    │  (Broker)   │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   ┌───────────┐    ┌───────────┐    ┌───────────┐
   │  emails   │    │certificates│    │ progress  │
   │  (queue)  │    │  (queue)  │    │  (queue)  │
   └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
         │                 │                 │
         ▼                 ▼                 ▼
  ┌───────────┐    ┌───────────┐    ┌───────────┐
  │ Worker 1  │    │ Worker 2  │    │ Worker 3  │
  │ (email)   │    │ (cert)    │    │ (progress)│
  └───────────┘    └───────────┘    └───────────┘
```

### Task Routes

```python
# app/tasks/celery_app.py
celery_app.conf.task_routes = {
    # Email tasks go to emails queue
    "app.tasks.email_tasks.*": {"queue": "emails"},
    "app.tasks.notification_tasks.*": {"queue": "emails"},
    
    # Certificate tasks go to certificates queue
    "app.tasks.certificate_tasks.*": {"queue": "certificates"},
    
    # Progress tasks go to progress queue
    "app.tasks.progress_tasks.*": {"queue": "progress"},
    "app.tasks.analytics_tasks.*": {"queue": "progress"},
    
    # Default queue
    "app.tasks.*": {"queue": "default"},
}
```

### Starting Workers for Specific Queues

```bash
# Start worker for emails queue only
celery -A app.tasks.celery_app worker -Q emails -l info

# Start worker for certificates queue only
celery -A app.tasks.celery_app worker -Q certificates -l info

# Start worker for all queues
celery -A app.tasks.celery_app worker -l info

# Start multiple workers
celery -A app.tasks.celery_app worker -Q default,emails -c 2 -l info
```

---

## 6. Scheduling with Celery Beat

### Periodic Tasks

```python
# app/tasks/celery_app.py
celery_app.conf.beat_schedule = {
    # Daily at 3 AM
    "cleanup-expired-tokens": {
        "task": "app.tasks.maintenance.cleanup_expired_tokens",
        "schedule": crontab(hour=3, minute=0),
    },
    
    # Every hour
    "generate-hourly-analytics": {
        "task": "app.tasks.analytics.generate_hourly_analytics",
        "schedule": 3600,  # seconds
    },
    
    # Every Monday at 9 AM
    "weekly-report": {
        "task": "app.tasks.reports.generate_weekly_report",
        "schedule": crontab(hour=9, minute=0, day_of_week=1),
    },
    
    # First day of month at midnight
    "monthly-archive": {
        "task": "app.tasks.archive.monthly_archive",
        "schedule": crontab(0, 0, day=1),
    },
}
```

### Maintenance Task Example

```python
# app/tasks/maintenance.py
from celery import shared_task
from datetime import datetime, timedelta

@shared_task
def cleanup_expired_tokens():
    """Clean up expired refresh tokens."""
    expired_before = datetime.utcnow()
    
    # Delete expired tokens from database
    deleted_count = delete_expired_refresh_tokens(expired_before)
    
    return {"deleted": deleted_count}

@shared_task
def cleanup_unverified_users():
    """Remove unverified users after 7 days."""
    threshold = datetime.utcnow() - timedelta(days=7)
    
    deleted_count = delete_unverified_users(threshold)
    
    return {"deleted": deleted_count}
```

---

## 7. Monitoring with Flower

### Flower Installation

```bash
pip install flower
```

### Starting Flower

```bash
# Start flower on port 5555
celery -A app.tasks.celery_app flower --port=5555
```

### Flower Features

| Feature | Description |
|---------|-------------|
| Dashboard | Real-time worker statistics |
| Tasks | View all tasks, status, results |
| Workers | Monitor worker health |
| Queues | View queue sizes |
| History | Task execution history |
| Rate Limits | Monitor rate limiting |

---

## 8. Running Background Jobs

### Development Mode

```bash
# Option 1: Run inline (no background processing)
# Set in .env:
TASKS_FORCE_INLINE=true

# Start API server
uvicorn app.main:app --reload
```

### Production Mode

```bash
# Start Celery worker
celery -A app.tasks.celery_app worker -l info

# Start Celery beat (scheduler)
celery -A app.tasks.celery_app beat -l info

# Or run both together
celery -A app.tasks.celery_app worker -l info --beat
```

### Docker Compose

```yaml
# docker-compose.yml
services:
  celery-worker:
    build: .
    command: celery -A app.tasks.celery_app worker -l info
    volumes:
      - .:/app
    depends_on:
      - redis
      - db
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
  
  celery-beat:
    build: .
    command: celery -A app.tasks.celery_app beat -l info
    volumes:
      - .:/app
    depends_on:
      - redis
```

---

## 9. Task Best Practices

### Task Design

```python
# ✅ Good: Idempotent tasks
@shared_task
def send_welcome_email(user_id: str):
    """Can be safely retried."""
    user = get_user(user_id)
    send_email(user.email, "Welcome!")
    # If fails, retry sends to same user (idempotent)

# ❌ Bad: Non-idempotent tasks
@shared_task
def charge_user(user_id: str, amount: float):
    """Should NOT retry - could charge twice!"""
    payment = charge(user_id, amount)  # DANGER!
```

### Error Handling

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_upload(self, file_id: str):
    try:
        file = get_file(file_id)
        process_file(file)
    except TemporaryError as exc:
        # Retry with exponential backoff
        raise self.retry(
            exc=exc,
            countdown=60 * (2 ** self.request.retries)
        )
    except PermanentError:
        # Don't retry
        notify_admin(file_id)
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

@shared_task
def generate_certificate(enrollment_id: str):
    logger.info(f"Starting certificate generation for enrollment {enrollment_id}")
    
    try:
        # ... generation logic
        logger.info(f"Certificate generated successfully for {enrollment_id}")
    except Exception as e:
        logger.error(f"Certificate generation failed: {e}")
        raise
```

---

## Background Jobs Summary

| Component | Implementation |
|-----------|----------------|
| Task Queue | Celery with Redis broker |
| Task Storage | Redis result backend |
| Scheduling | Celery Beat |
| Monitoring | Flower |
| Email Queue | Separate queue |
| Certificate Queue | Separate queue |
| Progress Queue | Separate queue |

This architecture ensures:
- **Responsive API** - Users don't wait for long operations
- **Reliability** - Failed tasks are retried
- **Scalability** - Workers scale independently
- **Maintainability** - Clear task separation by queue
