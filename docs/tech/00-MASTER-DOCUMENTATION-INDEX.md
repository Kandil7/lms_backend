# Master Documentation Index

This document provides a complete index and navigation guide for all technical documentation in the LMS Backend project.

---

## Quick Start - Start Here

| File | Description |
|------|-------------|
| **25-HOW-TO-BUILD-PROJECT.md** | Step-by-step guide to build and run the project |
| **26-COMPLETE-MODULE-DOCUMENTATION.md** | Every module explained in detail |
| **01-tech-stack-and-choices.md** | Technology stack and design decisions |

> **Recommendation**: Start with `25-HOW-TO-BUILD-PROJECT.md` to set up your environment, then explore `26-COMPLETE-MODULE-DOCUMENTATION.md` to understand how every component works.

---

## Complete Documentation List

### Foundational (01-04)

| # | File | Description |
|---|------|-------------|
| 1 | **01-tech-stack-and-choices.md** | Technology stack - Python, FastAPI, PostgreSQL, Redis, Celery |
| 2 | **02-architecture-decisions.md** | Modular monolith, layered architecture, vertical slices |
| 3 | **03-project-structure.md** | Directory structure and organization |
| 4 | **04-setup-and-build-guide.md** | Step-by-step setup instructions |

### Database & API (05-07)

| # | File | Description |
|---|------|-------------|
| 5 | **05-database-design.md** | Complete database schema, entities, relationships |
| 6 | **06-api-design-rationale.md** | REST API patterns and conventions |
| 7 | **07-security-implementation.md** | JWT, MFA, RBAC, rate limiting |

### Operations (08-10)

| # | File | Description |
|---|------|-------------|
| 8 | **08-background-jobs-celery.md** | Celery tasks, queues, scheduling |
| 9 | **09-testing-strategy.md** | pytest, fixtures, testing patterns |
| 10 | **10-deployment-guide.md** | Docker, production deployment |

### Module Documentation (11-12)

| # | File | Description |
|---|------|-------------|
| 11 | **11-modules-complete-reference.md** | Complete module reference |
| 12 | **12-module-design-decisions.md** | Why we made specific choices |

### Comprehensive Code Documentation (13-23)

| # | File | Description |
|---|------|-------------|
| 13 | **13-core-infrastructure.md** | Core modules: config, database, security, permissions |
| 14 | **14-api-routes-complete.md** | Complete API route documentation |
| 15 | **15-services-repositories.md** | Service and repository patterns |
| 16 | **16-relationships-diagram.md** | Entity relationship diagrams |
| 17 | **17-code-examples.md** | Practical code examples |
| 18 | **18-data-flows.md** | Complete data flow documentation |
| 19 | **19-application-entry-point.md** | main.py deep dive |
| 20 | **20-complete-configuration-reference.md** | Complete configuration reference |
| 21 | **21-utilities-helpers.md** | Utilities and helpers |
| 22 | **22-observability-metrics.md** | Metrics and observability |
| 23 | **23-payments-module.md** | Payments module documentation |

### Comprehensive Guides (24-26)

| # | File | Description |
|---|------|-------------|
| 25 | **25-HOW-TO-BUILD-PROJECT.md** | Complete build guide with step-by-step instructions |
| 26 | **26-COMPLETE-MODULE-DOCUMENTATION.md** | Every module explained in detail with all decisions |

---

## Quick Start Guide

### New to the Project?

1. **Start Here**: Read `01-tech-stack-and-choices.md` to understand the technology stack
2. **Architecture**: Read `02-architecture-decisions.md` to understand the architecture
3. **Setup**: Follow `04-setup-and-build-guide.md` to set up your development environment

### Working on a Specific Feature?

- **Courses**: See `11-modules-complete-reference.md` → Courses section
- **Payments**: See `23-payments-module.md`
- **Quizzes**: See `11-modules-complete-reference.md` → Quizzes section

### Need to Add a New Feature?

1. **Architecture**: Understand patterns in `02-architecture-decisions.md`
2. **API Design**: See `06-api-design-rationale.md`
3. **Database**: See `05-database-design.md` for schema patterns
4. **Testing**: See `09-testing-strategy.md`

---

## Key Concepts

### Architecture Patterns

| Pattern | Description | Document |
|---------|-------------|----------|
| Modular Monolith | Single deployable with modular structure | `02-architecture-decisions.md` |
| Layered Architecture | Routes → Services → Repositories | `02-architecture-decisions.md` |
| Vertical Slices | Self-contained feature modules | `02-architecture-decisions.md` |

### Security

| Concept | Document |
|---------|----------|
| JWT Authentication | `07-security-implementation.md` |
| MFA | `07-security-implementation.md` |
| Rate Limiting | `07-security-implementation.md` |
| RBAC | `07-security-implementation.md` |

### Data

| Concept | Document |
|---------|----------|
| Database Schema | `05-database-design.md` |
| Entity Relationships | `16-relationships-diagram.md` |
| Data Flows | `18-data-flows.md` |

---

## API Reference

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/auth/register | POST | Register new user |
| /api/v1/auth/login | POST | Login |
| /api/v1/auth/refresh | POST | Refresh token |
| /api/v1/auth/logout | POST | Logout |
| /api/v1/auth/mfa/enable | POST | Enable MFA |

### Courses

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/courses | GET | List courses |
| /api/v1/courses | POST | Create course |
| /api/v1/courses/{id} | GET | Get course |
| /api/v1/courses/{id} | PATCH | Update course |
| /api/v1/courses/{id}/publish | POST | Publish course |

### Enrollments

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/enrollments | POST | Enroll in course |
| /api/v1/enrollments/my-courses | GET | My enrollments |
| /api/v1/enrollments/{id}/lessons/{lesson_id}/complete | POST | Complete lesson |

### Quizzes

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/quizzes | GET | List quizzes |
| /api/v1/quizzes | POST | Create quiz |
| /api/v1/quizzes/{id}/attempts | POST | Start attempt |
| /api/v1/quizzes/{id}/attempts/{attempt_id}/submit | POST | Submit attempt |

---

## Database Entities

### Core Entities

| Entity | Description | Document |
|--------|-------------|----------|
| User | User accounts | `05-database-design.md` |
| Course | Course content | `05-database-design.md` |
| Lesson | Course lessons | `05-database-design.md` |
| Enrollment | Student enrollment | `05-database-design.md` |
| LessonProgress | Progress tracking | `05-database-design.md` |

### Assessment Entities

| Entity | Description | Document |
|--------|-------------|----------|
| Quiz | Quiz configuration | `05-database-design.md` |
| QuizQuestion | Quiz questions | `05-database-design.md` |
| QuizAttempt | Student attempts | `05-database-design.md` |

### Payment Entities

| Entity | Description | Document |
|--------|-------------|----------|
| Payment | Payment records | `23-payments-module.md` |
| Subscription | Subscription records | `23-payments-module.md` |

---

## Configuration

### Environment Variables

| Category | Document |
|----------|----------|
| Application | `20-complete-configuration-reference.md` |
| Database | `20-complete-configuration-reference.md` |
| Security | `20-complete-configuration-reference.md` |
| Redis | `20-complete-configuration-reference.md` |
| AWS | `20-complete-configuration-reference.md` |

---

## Development Workflow

### Setting Up Development Environment

```bash
# 1. Clone the project
git clone <repo-url>
cd lms_backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env

# 5. Start services
docker-compose up -d db redis

# 6. Run migrations
alembic upgrade head

# 7. Start development server
uvicorn app.main:app --reload
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py
```

### Code Style

```bash
# Format code
black .

# Sort imports
isort .

# Lint
ruff check .
```

---

## Deployment

### Development

```bash
docker-compose up -d
```

### Production

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d --build
```

See `10-deployment-guide.md` for complete deployment guide.

---

## Support

### Common Issues

| Issue | Solution |
|-------|-----------|
| Database connection error | Check DATABASE_URL in .env |
| Redis connection error | Check REDIS_URL in .env |
| Import errors | Ensure virtual environment is activated |
| Port already in use | Stop existing process or use different port |

### Getting Help

1. Check documentation in `docs/tech/`
2. Review error logs in application
3. Check health endpoints: `/api/v1/health`, `/api/v1/ready`

---

## Version Information

| Component | Version |
|-----------|---------|
| Python | 3.11+ |
| FastAPI | 0.115.0+ |
| PostgreSQL | 14+ |
| Redis | 7+ |
| Celery | 5.4.0+ |

---

## Summary

This documentation provides a complete reference for the LMS Backend project:

- ✅ 23 comprehensive technical documents
- ✅ Complete API reference
- ✅ Database schema documentation
- ✅ Configuration guide
- ✅ Development workflow
- ✅ Deployment guide

For more information, see individual documents in `docs/tech/`.
