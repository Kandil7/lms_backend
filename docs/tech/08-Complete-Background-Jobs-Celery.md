# Complete Background Jobs and Celery Implementation

This comprehensive guide documents the background task processing system in the LMS Backend. It covers Celery configuration, task implementation, queue architecture, monitoring, and best practices for asynchronous processing.

---

## Architecture Overview

The LMS Backend uses Celery with Redis as the message broker for asynchronous task processing. This architecture enables long-running operations to be processed in the background without blocking API responses. The system provides reliability, scalability, and monitoring capabilities for production workloads.

### Why Background Tasks?

Many operations in an LMS don't require immediate completion from the user's perspective. Sending welcome emails, generating certificates, processing webhooks, and updating analytics can all happen asynchronously. Background processing improves user experience by returning API responses quickly while time-consuming work continues in the background. It also enables retry logic for operations that might fail temporarily, such as external API calls or email delivery.

---

## Celery Configuration

### Core Configuration (app/tasks/celery_app.py)

The Celery application is configured in app/tasks/celery_app.py. This file initializes the Celery instance with broker and backend settings, imports all task modules, and configures worker behavior.

```python
celery_app = Celery(
    "lms_backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.progress_tasks",
        "app.tasks.certificate_tasks",
        "app.tasks.webhook_tasks",
    ],
)
```

The broker and backend both use Redis with different database numbers. Database 1 serves as the Celery message broker, while database 2 stores task results. This separation prevents interference between queuing and result storage.

### Worker Configuration

The configuration includes worker-specific settings:

```python
celery_app.conf.update(
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "emails"},
        "app.tasks.progress_tasks.*": {"queue": "progress"},
        "app.tasks.certificate_tasks.*": {"queue": "certificates"},
        "app.tasks.webhook_tasks.*": {"queue": "webhooks"},
    },
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_acks_on_failure_or_timeout=False,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_default_retry_delay=5,
    task_time_limit=300,
    task_soft_time_limit=240,
)
```

**task_routes** directs tasks to specific queues based on their module. This enables independent scaling of different task types.

**task_acks_late=True** acknowledges tasks only after processing completes. This prevents task loss if workers crash during processing.

**task_reject_on_worker_lost=True** requeues tasks when workers are lost, ensuring tasks aren't stuck in processing state.

**worker_prefetch_multiplier=1** ensures fair distribution. Workers fetch only one task at a time, allowing other workers to take remaining tasks.

**task_time_limit=300** sets a hard 5-minute limit. Tasks exceeding this limit are terminated.

**task_soft_time_limit=240** sets a 4-minute soft limit. Tasks can use this for cleanup before the hard limit.

---

## Task Queues

The system uses four distinct queues for different task types. This separation provides isolation, independent scaling, and priority handling.

### Emails Queue

The emails queue handles all transactional email operations. These tasks are typically small and numerous but important for user communication.

**Tasks in this queue**:
- Welcome emails on registration
- Password reset emails
- Email verification emails
- Enrollment confirmation emails
- Course completion notifications
- Certificate issuance notifications

**SLA expectations**: Emails should be delivered within seconds to minutes. The queue should remain low as these tasks process quickly.

### Progress Queue

The progress queue handles enrollment progress calculations and updates. These tasks are triggered by user actions like completing lessons.

**Tasks in this queue**:
- Lesson completion tracking
- Course progress recalculation
- Enrollment status updates
- Completion detection
- Quiz attempt scoring triggers

**SLA expectations**: Progress should update within seconds of completion. Users expect immediate feedback on their progress.

### Certificates Queue

The certificates queue handles resource-intensive PDF generation tasks. Certificate generation involves template rendering, PDF creation, and file storage.

**Tasks in this queue**:
- Certificate PDF generation
- Certificate storage
- Certificate delivery notifications

**SLA expectations**: Certificates should generate within minutes of course completion. This is a lower priority since users can continue learning while waiting.

### Webhooks Queue

The webhooks queue handles external event notifications. These tasks make HTTP calls to external systems and must handle failures gracefully.

**Tasks in this queue**:
- Enrollment event webhooks
- Course completion webhooks
- Certificate issuance webhooks
- Custom event webhooks

**SLA expectations**: Webhook delivery attempts should complete within the configured timeout. Retries may extend total delivery time.

---

## Task Implementation

### Email Tasks (app/tasks/email_tasks.py)

Email tasks handle all outbound email functionality. The tasks are designed for reliability with retry logic and error handling.

```python
@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_welcome_email(self, user_id: str, email: str, full_name: str):
    """Send welcome email to new users."""
    try:
        # Email sending logic
        smtp_connection.send_message(msg)
    except SMTPException as exc:
        # Log and retry
        logger.error(f"Failed to send welcome email: {exc}")
        raise
```

**Features**:
- Automatic retry with exponential backoff
- Maximum 3 retry attempts
- Detailed logging for debugging
- Error tracking through Sentry

### Progress Tasks (app/tasks/progress_tasks.py)

Progress tasks calculate and update student progress. These tasks are triggered synchronously when students complete lessons but run asynchronously.

```python
@celery_app.task(bind=True)
def update_lesson_completion(self, enrollment_id: str, lesson_id: str, user_id: str):
    """Update enrollment progress after lesson completion."""
    with session_scope() as db:
        enrollment = db.query(Enrollment).get(enrollment_id)
        # Calculate new progress percentage
        # Check for course completion
        # Trigger certificate generation if complete
```

**Features**:
- Database transaction management
- Progress recalculation
- Completion detection
- Certificate trigger on completion

### Certificate Tasks (app/tasks/certificate_tasks.py)

Certificate tasks generate PDF certificates for course completions. These are the most resource-intensive tasks in the system.

```python
@celery_app.task(bind=True)
def generate_certificate(self, enrollment_id: str):
    """Generate PDF certificate for course completion."""
    with session_scope() as db:
        # Fetch enrollment and course details
        # Generate PDF using Jinja2 template and fpdf2
        # Save PDF to storage
        # Update certificate record
```

**Features**:
- PDF generation with fpdf2
- Jinja2 template rendering
- Unique certificate number generation
- File storage management

### Webhook Tasks (app/tasks/webhook_tasks.py)

Webhook tasks deliver events to external systems. They include retry logic and signature verification.

```python
@celery_app.task(bind=True)
def deliver_webhook(self, event_type: str, payload: dict, webhook_url: str):
    """Deliver webhook event to external URL."""
    # Sign payload with HMAC
    # Make HTTP POST request
    # Handle response
    # Retry on failure
```

**Features**:
- HMAC signature generation
- HTTP timeout handling
- Retry with backoff
- Response validation

---

## Task Dispatching

### Synchronous vs Asynchronous

The application supports both synchronous (inline) and asynchronous task execution. The TASKS_FORCE_INLINE configuration determines behavior.

**Development (TASKS_FORCE_INLINE=true)**: Tasks execute immediately in the same process. This simplifies debugging but blocks API responses.

**Production (TASKS_FORCE_INLINE=false)**: Tasks queue to Celery workers for asynchronous execution. This returns API responses quickly while work continues in the background.

### Dispatcher Pattern (app/tasks/dispatcher.py)

The dispatcher provides a consistent interface for queueing tasks. It abstracts the choice between sync and async execution.

```python
def send_email_async(email_type: str, **kwargs):
    """Dispatch email task."""
    if settings.TASKS_FORCE_INLINE:
        # Execute directly
        send_email_task.execute(**kwargs)
    else:
        # Queue to Celery
        send_email_task.delay(**kwargs)
```

---

## Celery Beat Scheduling

Celery Beat provides periodic task scheduling. The beat scheduler runs tasks at configured intervals for maintenance and recurring operations.

### Beat Configuration

Beat is configured in the docker-compose.prod.yml. It uses a schedule file to define periodic tasks.

```yaml
celery-beat:
  command: celery -A app.tasks.celery_app.celery_app beat --loglevel=info --schedule=/tmp/celerybeat-schedule
```

### Periodic Tasks

Common periodic tasks include cleanup of old sessions, statistics aggregation, and health checks. The specific periodic tasks depend on operational needs.

---

## Worker Management

### Starting Workers

Workers are started through Docker Compose in production:

```bash
docker compose up -d celery-worker
```

Multiple workers can run for horizontal scaling:

```bash
docker compose up -d --scale celery-worker=3
```

### Worker Queues

Workers can be started with specific queue subscriptions:

```bash
celery -A app.tasks.celery_app.celery_app worker -Q emails,progress --concurrency=4
```

This starts a worker that only processes emails and progress tasks with 4 concurrent processes.

### Monitoring Workers

Monitor worker health through:
- Container health checks
- Worker logs
- Celery Flower (optional monitoring UI)
- Prometheus metrics

---

## Error Handling and Retries

### Automatic Retries

Celery tasks include automatic retry configuration:

```python
@celery_app.task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def task_with_retry():
    pass
```

**Retry strategies**:
- Exponential backoff: Wait times increase exponentially
- Linear backoff: Wait times increase linearly
- Fixed backoff: Wait times remain constant

### Manual Retries

Tasks can manually trigger retries:

```python
@celery_app.task(bind=True)
def task_with_manual_retry(self):
    try:
        # Task logic
    except TemporaryError:
        # Retry after specific delay
        raise self.retry(countdown=60)
```

### Dead Letter Queues

Failed tasks that exceed retry limits can be moved to dead letter queues for manual investigation. The configuration depends on Celery result backend settings.

---

## Performance Optimization

### Prefetch Multiplier

The prefetch_multiplier controls how many tasks workers fetch ahead:

- Higher values: More efficient for homogeneous workloads
- Lower values (1): Better for heterogeneous workloads with varying task duration

The default of 1 provides fair distribution across workers.

### Concurrency

Worker concurrency (--concurrency) determines parallel task execution:

```bash
celery worker --concurrency=4
```

Optimal concurrency depends on task characteristics:
- I/O bound tasks: Higher concurrency (8-16)
- CPU bound tasks: Lower concurrency (2-4)

### Task Routing

Route tasks to specific workers based on requirements:

```python
@celery_app.task(queue='emails')
def send_email():
    pass
```

This allows specialized workers for different task types.

---

## Testing Tasks

### Unit Testing

Mock external dependencies:

```python
@patch('app.tasks.email_tasks.send_email')
def test_welcome_email(mock_send):
    send_welcome_email(user_id, email, full_name)
    mock_send.assert_called_once()
```

### Integration Testing

Use pytest-celery or similar fixtures:

```python
def test_task_execution(celery_app, celery_session_worker):
    result = my_task.delay(arg1, arg2)
    assert result.get(timeout=10) == expected
```

---

## Troubleshooting

### Task Not Executing

Check queue assignment: Verify tasks are queued to the expected queue. Check worker subscriptions: Ensure workers are consuming from the correct queue. Review worker logs: Look for errors preventing task processing.

### Tasks Stuck in Pending

Check result backend: Ensure Redis is accessible. Verify task IDs: Pending tasks may be waiting for workers. Review task state: Check for retry loops or errors.

### High Memory Usage

Reduce prefetch: Lower prefetch_multiplier. Limit concurrency: Reduce worker processes. Optimize task payload: Minimize data passed to tasks.

### Slow Task Processing

Profile task execution: Identify bottlenecks. Scale workers: Add more worker processes or instances. Optimize database queries: Ensure efficient queries within tasks.

---

## Monitoring and Metrics

### Celery Flower

Flower provides web-based Celery monitoring:

```bash
pip install flower
celery -A app.tasks.celery_app.celery_app flower
```

Features include worker status, task history, queue lengths, and runtime metrics.

### Prometheus Integration

The application exposes Celery metrics through Prometheus. Key metrics include task success/failure counts, task duration histograms, and queue lengths.

### Log Monitoring

Worker logs provide detailed task execution information. Monitor logs for:
- Error messages
- Warning patterns
- Performance degradation

---

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| CELERY_BROKER_URL | Redis broker URL | redis://localhost:6379/1 |
| CELERY_RESULT_BACKEND | Redis result backend | redis://localhost:6379/2 |
| TASKS_FORCE_INLINE | Execute tasks inline | true (dev), false (prod) |

### Task Settings

| Setting | Description | Default |
|---------|-------------|---------|
| task_acks_late | Acknowledge after completion | true |
| task_time_limit | Hard time limit (seconds) | 300 |
| task_soft_time_limit | Soft time limit (seconds) | 240 |
| worker_prefetch_multiplier | Tasks to prefetch | 1 |

---

## Best Practices

### Task Design

Keep tasks atomic and idempotent. Tasks should complete successfully regardless of how many times they run. Use transactions for database operations within tasks. Handle exceptions gracefully with retry logic.

### Error Handling

Log errors with sufficient context for debugging. Use exponential backoff for retries. Implement dead letter handling for permanently failed tasks. Alert on repeated failures.

### Performance

Minimize task payload size. Use database indexes for queries within tasks. Close database connections within tasks. Monitor queue depths and worker utilization.

### Security

Validate input within tasks. Use parameterized queries. Avoid storing sensitive data in task results. Limit task execution time.

---

This comprehensive guide covers all aspects of background task processing in the LMS Backend. For specific task implementations, refer to the task files in app/tasks/.
