# Technology Stack Overview

## Complete Technology Choices and Rationale

This document explains every technology choice in this LMS backend project, the alternatives considered, and why each decision was made.

---

## 1. Backend Framework: FastAPI

### Why FastAPI?

| Factor | Choice | Rationale |
|--------|--------|-----------|
| **Performance** | FastAPI | Built on Starlette, native async support. Comparable to Node.js and Go in benchmarks |
| **Type Safety** | Pydantic v2 | Automatic data validation, serialization, and OpenAPI schema generation |
| **Documentation** | Built-in | Auto-generates Swagger UI and ReDoc from type hints |
| **Developer Experience** | Excellent | Auto-completion, clear error messages, minimal boilerplate |
| **Ecosystem** | Large | Extensive middleware, dependency injection, and extension support |

### Alternatives Considered

1. **Django**: Full-featured framework with admin panel, but heavier and less flexible for API-first design
2. **Flask**: Lightweight and flexible, but requires more manual setup for validation and docs
3. **Aiohttp**: Low-level async HTTP, lacks validation and documentation automation

### Version Requirements

```python
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.10.0
pydantic-settings>=2.7.1
```

---

## 2. Database: PostgreSQL

### Why PostgreSQL?

| Feature | Benefit for LMS |
|---------|-----------------|
| **ACID Compliance** | Critical for payments and enrollment transactions |
| **JSON Support** | Flexible metadata storage without separate tables |
| **Full-Text Search** | Course content search capabilities |
| **Robust Indexing** | Performance for complex queries |
| **UUID Support** | Native UUID type for global uniqueness |
| **Maturity** | 30+ years of production reliability |

### Alternatives Considered

1. **MySQL**: Less JSON support, fewer indexing options
2. **SQLite**: Not suitable for production concurrent access
3. **MongoDB**: No ACID for transactions, less structured for LMS data
4. **NoSQL (DynamoDB)**: Expensive, less flexible queries

### Version: PostgreSQL 16

```yaml
# docker-compose.yml
postgresql:
  image: postgres:16-alpine
  environment:
    POSTGRES_DB: lms
    POSTGRES_USER: lms_user
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

---

## 3. ORM: SQLAlchemy 2.0

### Why SQLAlchemy?

| Feature | Benefit |
|---------|---------|
| **Async Support** | Native async/await with `AsyncSession` |
| **Type Safety** | `Mapped` and `mapped_column` for type hints |
| **Query Building** | Type-safe query construction |
| **Migration Integration** | Works seamlessly with Alembic |
| **Performance** | Connection pooling, query optimization |

### Alternatives Considered

1. **Django ORM**: Tied to Django framework, less flexible
2. **Peewee**: Lightweight but less feature-rich
3. **Tortoise ORM**: Async-first but smaller ecosystem
4. **Prisma**: Not Python-native, requires separate CLI

### Version Requirements

```python
sqlalchemy>=2.0.36
alembic>=1.14.0
psycopg2-binary>=2.9.10
asyncpg>=0.30.0  # Async driver
```

---

## 4. Migrations: Alembic

### Why Alembic?

| Feature | Benefit |
|---------|---------|
| **Version Control** | Track schema changes in git |
| **Rollback Support** | Easy down migrations |
| **Auto-Generation** | Can infer from models |
| **Branching** | Support for multiple branches |
| **SQL Output** | Preview SQL before execution |

### Migration Strategy

```
alembic/
├── env.py              # Alembic configuration
├── script.py.mako     # Template for migrations
└── versions/
    ├── 0001_initial_schema.py
    ├── 0002_security_indexes.py
    └── ... (8 migrations total)
```

---

## 5. Authentication: JWT with Refresh Tokens

### Token Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     TOKEN ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐      ┌──────────────┐      ┌─────────────┐ │
│   │   Access     │      │   Refresh    │      │   Password  │ │
│   │   Token      │      │   Token      │      │   Reset     │ │
│   ├──────────────┤      ├──────────────┤      ├─────────────┤ │
│   │ 15 minutes   │      │   30 days     │      │   30 min    │ │
│   │              │◄────►│              │      │             │ │
│   │ JWT (stateless)    │ DB + Redis    │      │ Single-use  │ │
│   └──────────────┘      └──────────────┘      └─────────────┘ │
│                                                                 │
│   ┌──────────────┐      ┌──────────────┐                        │
│   │    Email     │      │     MFA      │                        │
│   │  Verification│      │   Challenge  │                        │
│   ├──────────────┤      ├──────────────┤                        │
│   │   24 hours   │      │    10 min     │                        │
│   │ Single-use   │      │  6-digit code │                        │
│   └──────────────┘      └──────────────┘                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Libraries Used

```python
python-jose[cryptography]>=3.3.0  # JWT encoding/decoding
passlib[bcrypt]>=1.7.4            # Password hashing
bcrypt>=4.2.0                      # Bcrypt hasher
```

### Why These Libraries?

1. **python-jose**: Fast, pure Python JWT implementation with cryptography
2. **passlib**: Unified interface for multiple hash algorithms
3. **bcrypt**: Industry-standard, salted hashing

---

## 6. Cache & Message Queue: Redis

### Why Redis?

| Use Case | Redis Feature | Benefit |
|----------|---------------|---------|
| **Caching** | In-memory store | Sub-millisecond access |
| **Rate Limiting** | INCR, EXPIRE | Token bucket algorithm |
| **Token Blacklist** | SET with TTL | Fast revocation checking |
| **Task Queue** | List/Broker | Celery broker backend |
| **Session Storage** | Hash operations | Fast session lookups |

### Alternatives Considered

1. **Memcached**: No persistence, limited data structures
2. **RabbitMQ**: More complex, requires Erlang
3. **Kafka**: Overkill for this use case, higher latency

### Redis in Architecture

```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes
  volumes:
    - redis_data:/data
```

---

## 7. Background Jobs: Celery

### Why Celery?

| Feature | Benefit |
|---------|---------|
| **Distributed** | Scale across multiple workers |
| **Scheduling** | Celery Beat for periodic tasks |
| **Retry Logic** | Automatic retry with backoff |
| **Monitoring** | Flower dashboard |
| **Language** | Native Python, no external dependencies |

### Task Queues Used

```python
task_routes = {
    "app.tasks.email_tasks.*": {"queue": "emails"},
    "app.tasks.certificate_tasks.*": {"queue": "certificates"},
    "app.tasks.progress_tasks.*": {"queue": "progress"},
    "app.tasks.webhook_tasks.*": {"queue": "webhooks"},
}
```

### Alternatives Considered

1. **RQ (Redis Queue)**: Simpler but less features
2. **Huey**: Lightweight but smaller ecosystem
3. ** Dramatiq**: Modern but newer, less battle-tested

---

## 8. Email: FastAPI-Mail + Jinja2

### Why This Combination?

| Component | Purpose |
|-----------|---------|
| **FastAPI-Mail** | Async email sending, connection pooling |
| **Jinja2** | Template rendering with inheritance |
| **Celery** | Queue email delivery for performance |

### Email Templates

```
app/modules/emails/templates/
├── base.html
├── welcome.html
├── password_reset.html
├── course_enrolled.html
├── certificate_issued.html
└── weekly_progress.html
```

---

## 9. PDF Generation: fpdf2

### Why fpdf2?

| Feature | Benefit |
|---------|---------|
| **Pure Python** | No external dependencies |
| **Lightweight** | Simple certificate generation |
| **Customizable** | Full control over layout |
| **Unicode Support** | Arabic and multilingual certificates |

### Alternatives Considered

1. **ReportLab**: More powerful but complex
2. **WeasyPrint**: Requires GTK, harder to deploy
3. **PDFKit**: Requires wkhtmltopdf binary

---

## 10. Testing: Pytest

### Testing Stack

```python
pytest>=8.3.0
pytest-asyncio>=0.25.0      # Async test support
pytest-cov>=6.0.0           # Coverage reporting
faker>=30.0.0               # Fake data generation
httpx>=0.28.0               # Async HTTP client for tests
```

### Why Pytest?

1. **Async Support**: pytest-asyncio handles async tests natively
2. **Fixtures**: Powerful dependency injection for tests
3. **Plugins**: Extensive ecosystem (cov, mock, timeout)
4. **Markers**: Easy test categorization

---

## 11. Containerization: Docker

### Docker Stack

```yaml
# docker-compose.yml includes:
services:
  api:          # FastAPI application
  celery_worker:# Background task processor
  celery_beat:  # Task scheduler
  flower:       # Celery monitoring
  postgres:     # Database
  redis:        # Cache and broker
```

### Why Docker?

| Benefit | Description |
|---------|-------------|
| **Consistency** | Same environment dev/prod |
| **Isolation** | Separate services don't conflict |
| **Scaling** | Easy to add more workers |
| **CI/CD** | Simple pipeline integration |

---

## 12. Payment Gateways

### Supported Providers

| Provider | Type | Use Case |
|----------|------|----------|
| **MyFatoorah** | Regional (MENA) | Primary for EGP payments |
| **Stripe** | Global | International cards, subscriptions |
| **Paymob** | Regional (Egypt) | Alternative local provider |

### Why Multiple Providers?

1. **Market Coverage**: Local providers for EGP, Stripe for international
2. **Redundancy**: Backup if one fails
3. **Features**: Different subscription models

---

## 13. File Storage

### Storage Backends

| Provider | Use Case | Configuration |
|----------|----------|---------------|
| **Local** | Development | Default, no setup |
| **S3** | Production | AWS credentials, bucket config |

### Why This Design?

1. **Simplicity**: Start with local, migrate to S3 later
2. **Signed URLs**: Secure time-limited access
3. **Presigned URLs**: Client uploads directly to S3

---

## 14. Monitoring & Observability

### Tools Used

| Tool | Purpose |
|------|---------|
| **Prometheus** | Metrics collection |
| **Grafana** | Metrics visualization |
| **Sentry** | Error tracking |
| **Flower** | Celery monitoring |

### Metrics Exposed

- Request latency histogram
- Request count by endpoint
- Database connection pool usage
- Celery task success/failure rates

---

## 15. API Documentation

### Why Built-in Docs?

| Feature | Benefit |
|---------|---------|
| **Swagger UI** | Interactive API testing |
| **ReDoc** | Alternative documentation view |
| **OpenAPI** | Machine-readable schema |
| **Auto-Generated** | Always in sync with code |

---

## Summary: Technology Decision Matrix

| Component | Choice | Key Rationale |
|-----------|--------|---------------|
| Framework | FastAPI | Async, type safety, auto-docs |
| Database | PostgreSQL | ACID, JSON, indexing |
| ORM | SQLAlchemy 2.0 | Async, type-safe |
| Migrations | Alembic | Version control, rollback |
| Auth | JWT + Refresh | Stateless, scalable |
| Cache/Queue | Redis | Multi-purpose, fast |
| Background Jobs | Celery | Distributed, scheduling |
| Testing | Pytest | Async support, fixtures |
| Container | Docker | Consistency, scaling |
| Monitoring | Prometheus + Sentry | Metrics + errors |

---

## Version Compatibility Matrix

| Component | Version | Python Version |
|-----------|---------|----------------|
| FastAPI | 0.115+ | 3.11+ |
| SQLAlchemy | 2.0+ | 3.11+ |
| Pydantic | 2.10+ | 3.11+ |
| PostgreSQL | 16 | N/A |
| Redis | 7 | N/A |
| Celery | 5.4+ | 3.11+ |

---

*This technology stack was chosen to provide a balance of performance, maintainability, security, and developer experience while remaining suitable for production deployment.*
