# Project Architecture Overview

## High-Level Architecture

The LMS Backend is a production-oriented Learning Management System built as a **modular monolith** using FastAPI. This architecture provides the best of both worlds: the simplicity and consistency of a monolithic application with the modularity and maintainability of microservices.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   Web App   │  │ Mobile App  │  │   Desktop   │  │  WebSocket CLI  │  │
│  │  (React)    │  │  (React N)  │  │   (Elec)    │  │    (Python)     │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘  │
└─────────┼────────────────┼────────────────┼─────────────────┼────────────┘
          │                │                │                 │
          └────────────────┴────────────────┴─────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LOAD BALANCER / REVERSE PROXY                       │
│                         (Nginx / Azure App Gateway)                         │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI APPLICATION                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         API LAYER (app/api/)                         │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │  Health  │ │  Auth    │ │  Users   │ │ Courses  │ │ Enroll   │  │   │
│  │  │ Routes   │ │ Routes   │ │ Routes   │ │ Routes   │ │ Routes   │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │ Quizzes  │ │Assignmnt │ │   Files  │ │Analytics │ │Payments  │  │   │
│  │  │ Routes   │ │ Routes   │ │ Routes   │ │ Routes   │ │ Routes   │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    MIDDLEWARE (app/core/middleware/)                │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │   │
│  │  │   CORS   │ │ Security │ │Request   │ │  Rate   │ │Response│  │   │
│  │  │          │ │ Headers  │ │Logging   │ │ Limit   │ │Envelope│  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      CORE SERVICES (app/core/)                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │   │
│  │  │  Config  │ │ Database │ │Security  │ │Permissions│ │Cache  │  │   │
│  │  │          │ │          │ │          │ │          │ │       │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    MODULES (app/modules/)                           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │   │
│  │  │   Auth   │ │  Users   │ │ Courses  │ │Enrollmnt │ │ Quizzes│  │   │
│  │  │  Module  │ │  Module  │ │  Module  │ │  Module  │ │ Module │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │   │
│  │  │Assignmnts │ │  Files   │ │Analytics │ │Payments │ │Admin  │  │   │
│  │  │  Module  │ │  Module  │ │  Module  │ │  Module  │ │Module │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   PostgreSQL    │   │      Redis      │   │      Celery     │
│   Database      │   │  Cache/Broker   │   │  Background     │
│                 │   │                 │   │     Workers      │
│  - Users        │   │  - Session      │   │                 │
│  - Courses      │   │  - Cache        │   │  - Emails       │
│  - Enrollments  │   │  - Rate Limit   │   │  - Certificates │
│  - Assignments  │   │  - Token Blklst │   │  - Webhooks     │
│  - Payments     │   │                 │   │  - Progress     │
└─────────────────┘   └─────────────────┘   └─────────────────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │    Celery      │
                        │    Workers     │
                        │  ┌───────────┐ │
                        │  │   emails  │ │
                        │  │progress   │ │
                        │  │certificates│ │
                        │  │webhooks   │ │
                        │  └───────────┘ │
                        └─────────────────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │  External       │
                        │  Services       │
                        │  ┌───────────┐  │
                        │  │   SMTP    │  │
                        │  │  (Email)  │  │
                        │  └───────────┘  │
                        │  ┌───────────┐  │
                        │  │  Azure   │  │
                        │  │  Blob    │  │
                        │  └───────────┘  │
                        │  ┌───────────┐  │
                        │  │  Stripe  │  │
                        │  │ (Payments)│  │
                        │  └───────────┘  │
                        │  ┌───────────┐  │
                        │  │ Firebase │  │
                        │  │(Push Notif)│ │
                        │  └───────────┘  │
                        └─────────────────┘
```

## Technology Stack

### Why These Technologies?

| Technology | Choice | Reasoning |
|------------|--------|-----------|
| **FastAPI** | Framework | FastAPI provides automatic OpenAPI documentation, built-in validation with Pydantic, native async support, and excellent performance (comparable to Node.js/Go). Chosen over Flask (no async, manual validation) and Django (too heavyweight for this use case). |
| **SQLAlchemy** | ORM | Provides type-safe database operations, migration support via Alembic, connection pooling, and works seamlessly with Pydantic. Chosen over raw SQL (error-prone) and other ORMs (less mature async support). |
| **PostgreSQL** | Database | ACID compliance, rich JSON support, excellent full-text search, robust concurrency handling. Chosen over MySQL (weaker JSON support) and NoSQL (relational data fits LMS domain well). |
| **Redis** | Cache/Broker | Sub-millisecond latency for caching, built-in pub/sub, atomic operations for rate limiting, native Celery broker support. |
| **Celery** | Task Queue | Mature Python async task framework with Redis broker, retry mechanisms, scheduling via Celery Beat, and excellent monitoring capabilities. |
| **Pydantic** | Validation | Built into FastAPI ecosystem, automatic serialization/deserialization, complex validation logic, TypeScript generation. |
| **JWT + Cookies** | Auth | JWT for stateless authentication, HTTP-only cookies for XSS protection, refresh tokens for long sessions, optional MFA support. |

### Complete Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **API Framework** | FastAPI | Latest |
| **ORM** | SQLAlchemy | 2.x |
| **Database** | PostgreSQL | 16 |
| **Cache/Message Broker** | Redis | 7 |
| **Task Queue** | Celery | 5.x |
| **Validation** | Pydantic | 2.x |
| **Password Hashing** | bcrypt | Latest |
| **Token Auth** | python-jose | Latest |
| **File Storage** | Azure Blob Storage | Latest |
| **Containerization** | Docker | Latest |
| **CI/CD** | GitHub Actions | Latest |

## Modular Monolith Architecture

### Design Principles

The project follows a **modular monolith** architecture with these key principles:

1. **Domain-Driven Design (DDD)**: Each module represents a bounded context in the LMS domain
2. **Separation of Concerns**: Clear boundaries between API routes, business logic, and data access
3. **Shared Infrastructure**: Common utilities in `app/core/` are shared across modules
4. **Future-Proofing**: Modules can be extracted into microservices if needed

### Module Structure

Each module follows a consistent structure:

```
module_name/
├── __init__.py           # Module exports
├── models/               # SQLAlchemy models
│   └── *.py
├── repositories/         # Data access layer
│   └── *.py
├── schemas/              # Pydantic request/response schemas
│   └── *.py
├── services/             # Business logic
│   └── *.py
├── routers/              # FastAPI route handlers
│   └── *.py
└── dependencies.py       # Module-specific dependencies
```

### Module Dependencies

```
                    ┌──────────────┐
                    │     Auth     │  (Core - must be available)
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│    Users      │  │   Courses     │  │   Payments    │
│   Module      │  │   Module      │  │   Module      │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  Enrollments  │  │  Assignments  │  │   Quizzes     │
│   Module      │  │   Module      │  │   Module      │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
                ┌───────────────────┐
                │   Certificates    │
                │      Module       │
                └───────────────────┘
```

## Data Flow and Request Lifecycle

### HTTP Request Flow

```
┌─────────────┐
│   Client    │  1. Makes HTTP/HTTPS request
│  (Browser)  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LOAD BALANCER / NGINX                       │
│              (SSL Termination, Path Routing)                    │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI APPLICATION                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    MIDDLEWARE STACK                       │   │
│  │  1. TrustedHostMiddleware (validate Host header)         │   │
│  │  2. CORSMiddleware (CORS handling)                       │   │
│  │  3. CSRFMiddleware (CSRF protection - production)        │   │
│  │  4. GZipMiddleware (compression)                         │   │
│  │  5. SecurityHeadersMiddleware (security headers)        │   │
│  │  6. RequestLoggingMiddleware (request/response logging)  │   │
│  │  7. MetricsMiddleware (Prometheus metrics)               │   │
│  │  8. RateLimitMiddleware (rate limiting)                  │   │
│  │  9. ResponseEnvelopeMiddleware (response formatting)   │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    ROUTING LAYER                          │   │
│  │  api_router → module_router → handler                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 DEPENDENCY INJECTION                      │   │
│  │  get_db() → get_current_user() → require_roles()         │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    BUSINESS LOGIC                         │   │
│  │  router → service → repository                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    DATA LAYER                            │   │
│  │  repository → SQLAlchemy → PostgreSQL                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                       RESPONSE FLOW                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Service returns Pydantic model                          │   │
│  │  → Router validates response schema                      │   │
│  │  → Middleware may wrap response (envelope)              │   │
│  │  → Security headers added                               │   │
│  │  → CORS headers added                                   │   │
│  │  → Response sent to client                              │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Background Task Flow

```
┌─────────────┐
│   API       │  1. Creates task (e.g., send welcome email)
│   Handler   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CELERY DISPATCH                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Task dispatched to queue:                                │   │
│  │  - emails:     welcome, password reset, enrollment       │   │
│  │  - certificates: generation, PDF creation               │   │
│  │  - progress:    enrollment tracking, completion         │   │
│  │  - webhooks:    external notifications                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CELERY BROKER (REDIS)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Messages stored in Redis queues                         │   │
│  │  Workers consume from assigned queues                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CELERY WORKERS                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │email-worker│ │cert-worker│ │prog-worker│ │webhook  │      │
│  │(emails q) │ │(cert q)  │ │(prog q)  │ │(webhook q)│     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│       │             │              │              │              │
│       ▼             ▼              ▼              ▼              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              TASK EXECUTION                               │  │
│  │  - Connect to external service (SMTP, Stripe, etc.)     │  │
│  │  - Perform operation                                     │  │
│  │  - Handle errors/retry                                  │  │
│  │  - Log results                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### WebSocket Flow

```
┌─────────────┐
│   Client    │  1. Establishes WebSocket connection
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                  WEBSOCKET UPGRADE                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  1. Request received at /ws/{endpoint}                  │   │
│  │  2. Authentication validated (JWT in query param)      │   │
│  │  3. Connection registered in ClientRegistry             │   │
│  │  4. Bidirectional communication established              │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│               WEBSOCKET COMMUNICATION                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     SERVER                               │   │
│  │  - Receive message from client                          │   │
│  │  - Process via WebSocketService                         │   │
│  │  - Broadcast to relevant clients                        │   │
│  │                                                         │   │
│  │                     CLIENTS                              │   │
│  │  - Receive real-time updates                           │   │
│  │  - Update UI reactively                                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Multi-Environment Support

The project supports multiple deployment environments:

### Development
- Local PostgreSQL and Redis (via Docker)
- Debug mode enabled
- API documentation accessible at `/docs`
- JWT-based authentication
- File storage: Local filesystem

### Staging
- Cloud-based PostgreSQL (Azure)
- Cloud-based Redis
- Debug disabled
- API documentation may be enabled
- Cookie-based authentication
- File storage: Azure Blob

### Production
- Production-grade PostgreSQL with backups
- Redis with clustering
- Debug disabled
- API documentation disabled
- Cookie-based authentication with CSRF protection
- File storage: Azure Blob
- Full observability (Sentry, metrics)

### Environment Configuration

```python
# Environment-specific settings
ENVIRONMENT: Literal["development", "staging", "production"]

# Key differences by environment
| Setting               | Development     | Production        |
|-----------------------|-----------------|-------------------|
| DEBUG                 | True            | False             |
| API Docs              | Enabled         | Disabled          |
| Auth Method           | JWT Bearer      | Cookie + CSRF     |
| CSRF Protection       | Disabled        | Enabled           |
| Token Blacklist       | Optional        | Required          |
| Secrets Management    | .env file       | Azure Key Vault  |
| File Storage          | Local           | Azure Blob       |
```

## Deployment Architecture

### Docker Compose (Development)

```
┌────────────────────────────────────────────────────────────┐
│                   docker-compose.yml                        │
│                                                            │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐               │
│  │   API   │    │  Celery │    │ Celery  │               │
│  │  (Fast) │    │ Worker  │    │  Beat   │               │
│  └────┬────┘    └────┬────┘    └────┬────┘               │
│       │               │               │                     │
│       └───────────────┼───────────────┘                     │
│                       │                                     │
│       ┌───────────────┼───────────────┐                     │
│       │               │               │                     │
│       ▼               ▼               ▼                     │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐               │
│  │Postgres │    │  Redis  │    │         │               │
│  │   DB    │    │(Cache+  │    │         │               │
│  │         │    │ Broker) │    │         │               │
│  └─────────┘    └─────────┘    └─────────┘               │
└────────────────────────────────────────────────────────────┘
```

### Azure Deployment (Production)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AZURE CLOUD                                  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Azure Virtual Machine                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │  │
│  │  │   API    │  │ Celery   │  │ Celery   │  │  Nginx   │   │  │
│  │  │ Instance │  │ Worker 1 │  │ Worker 2 │  │ Reverse  │   │  │
│  │  │  (App)   │  │          │  │          │  │  Proxy   │   │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                    │                    │                          │
│                    ▼                    ▼                          │
│  ┌─────────────────────┐   ┌─────────────────────────────────────┐  │
│  │   Azure Database    │   │          Azure Cache               │  │
│  │   (PostgreSQL)      │   │          (Redis)                  │  │
│  └─────────────────────┘   └─────────────────────────────────────┘  │
│                                                                        │
│  ┌─────────────────────┐   ┌─────────────────────────────────────┐  │
│  │  Azure Blob Storage │   │       Azure Key Vault              │  │
│  │    (File Storage)   │   │       (Secrets)                    │  │
│  └─────────────────────┘   └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Architectural Decisions

### 1. Modular Monolith over Microservices

**Decision**: Use modular monolith architecture.

**Rationale**:
- LMS domain is cohesive - courses, enrollments, assignments are tightly related
- Single codebase easier to maintain for small team
- Can extract modules to microservices later if needed
- FastAPI makes it easy to structure as modules

**Alternative Considered**: Microservices
- Rejected due to increased operational complexity
- Would require service mesh, distributed tracing, etc.

### 2. SQLAlchemy with Async Support

**Decision**: Use SQLAlchemy with synchronous operations (for now).

**Rationale**:
- Simpler debugging and testing
- SQLAlchemy 2.0 provides better async support
- Can migrate to async incrementally

**Alternative Considered**: Pure async with databases (asyncpg)
- Rejected for complexity in migration
- Sync code is sufficient for current scale

### 3. Redis for Multiple Purposes

**Decision**: Use Redis for caching, rate limiting, session storage, and Celery broker.

**Rationale**:
- Single infrastructure component reduces complexity
- Redis handles all these use cases efficiently
- Easy to scale Redis separately if needed

**Alternative Considered**: Separate services (Memcached, etc.)
- Rejected for simplicity

### 4. Cookie-Based Auth in Production

**Decision**: Use HTTP-only cookies for authentication in production.

**Rationale**:
- Protects against XSS (tokens not accessible to JavaScript)
- Automatically sent with requests
- CSRF protection via SameSite cookies and CSRF tokens

**Alternative Considered**: LocalStorage + JWT
- Rejected due to XSS vulnerability

### 5. Azure Blob for File Storage

**Decision**: Use Azure Blob Storage for file uploads.

**Rationale**:
- Scalable without managing infrastructure
- CDN integration possible
- Cost-effective for typical LMS usage patterns

**Alternative Considered**: S3-compatible storage
- Would work similarly, but Azure is the target cloud provider

## Performance Considerations

### Connection Pooling

- PostgreSQL: 20 connections pool, 40 overflow
- Connection recycled every 30 minutes
- Pre-ping check on connection

### Caching Strategy

- Course data: 120 second TTL
- Lesson content: 120 second TTL
- Quiz data: 120 second TTL
- Cache invalidation on updates

### Rate Limiting

- Global: 100 requests/minute
- Auth endpoints: 60 requests/minute
- File uploads: 100 requests/hour
- Assignments: 60 requests/minute

### Background Processing

- Long-running tasks (emails, certificates) offloaded to Celery
- Separate queues for different task types
- Retry with exponential backoff

## Security Considerations

### Authentication
- JWT tokens with short expiration (15 minutes)
- Refresh tokens with 30-day expiration
- Optional MFA support
- Account lockout after 5 failed attempts

### Authorization
- Role-based access control (Admin, Instructor, Student)
- Permission-based endpoint protection
- Row-level security for user data

### Data Protection
- Passwords hashed with bcrypt
- Sensitive data redacted in logs
- CSRF protection in production
- Security headers (HSTS, X-Frame-Options, etc.)

### Infrastructure Security
- Secrets managed via Azure Key Vault in production
- HTTPS enforced in production
- Rate limiting on all endpoints
- Input validation via Pydantic
