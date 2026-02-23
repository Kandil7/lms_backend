# LMS Backend - Comprehensive Technical Documentation

## Project Overview

This document provides complete technical documentation for the LMS (Learning Management System) Backend project. The LMS Backend is a production-oriented system built as a modular monolith using FastAPI, designed to support full online learning platform functionality including user management, course creation, enrollment tracking, quiz assessments, certificate issuance, and comprehensive analytics.

The project follows clean architecture principles with clear separation between core infrastructure, modules, API layers, and background tasks. It implements industry-standard security practices, observability features, and deployment patterns suitable for production environments.

---

## Documentation Index

This master index provides quick navigation to all technical documentation files within the docs/tech/ directory. Each document covers specific aspects of the project in exhaustive detail.

### Getting Started

| Document | Description |
|----------|-------------|
| [01-Complete-Project-Overview.md](01-Complete-Project-Overview.md) | Comprehensive project overview including tech stack, architecture, and core capabilities |
| [02-Complete-Architecture-Decisions.md](02-Complete-Architecture-Decisions.md) | Detailed explanation of architectural decisions and the reasoning behind each choice |
| [03-Complete-Setup-And-Configuration.md](03-Complete-Setup-And-Configuration.md) | Step-by-step setup guide for development, staging, and production environments |
| [04-Complete-Build-And-Run-Guide.md](04-Complete-Build-And-Run-Guide.md) | Complete instructions for building and running the project locally and in containers |

### Core Infrastructure

| Document | Description |
|----------|-------------|
| [05-Complete-Core-Modules-Reference.md](05-Complete-Core-Modules-Reference.md) | Detailed reference for all core infrastructure modules |
| [06-Complete-Database-And-Migrations.md](07-Complete-Database-And-Migrations.md) | Database schema design, migrations, and data model documentation |
| [07-Complete-Security-And-Authentication.md](06-Complete-Security-And-Authentication.md) | Security implementation details including JWT, rate limiting, and protection mechanisms |
| [08-Complete-Background-Jobs-Celery.md](08-Complete-Background-Jobs-Celery.md) | Celery task configuration, task types, and async processing patterns |

### Module Reference

| Document | Description |
|----------|-------------|
| [09-Complete-Modules-Detailed.md](09-Complete-Modules-Detailed.md) | Comprehensive documentation of all application modules |
| [10-Complete-API-Routes-Reference.md](10-Complete-API-Routes-Reference.md) | Complete API endpoint reference with request/response schemas |
| [11-Complete-Services-Repositories.md](11-Complete-Services-Repositories.md) | Service layer and repository pattern implementation details |

### Operations and Deployment

| Document | Description |
|----------|-------------|
| [12-Complete-Operations-Infrastructure.md](12-Complete-Operations-Infrastructure.md) | Production operations, Docker configuration, and infrastructure setup |
| [13-Complete-Deployment-Guide.md](13-Complete-Deployment-Guide.md) | Deployment procedures for various environments |
| [14-Complete-Scripts-Reference.md](14-Complete-Scripts-Reference.md) | Complete reference for all scripts in the scripts/ directory |
| [15-Complete-GitHub-Workflows.md](15-Complete-GitHub-Workflows.md) | CI/CD pipeline documentation and GitHub Actions workflows |

### Quality Assurance

| Document | Description |
|----------|-------------|
| [16-Complete-Testing-Strategy.md](16-Complete-Testing-Strategy.md) | Testing approach, test types, and coverage requirements |
| [17-Complete-File-By-File-Documentation.md](17-Complete-File-By-File-Documentation.md) | Exhaustive file-by-file documentation of entire project |

---

## Technology Stack Summary

The LMS Backend utilizes a carefully selected technology stack optimized for performance, maintainability, and production readiness:

**Framework and Runtime**: FastAPI serves as the primary web framework, chosen for its async capabilities, automatic OpenAPI documentation generation, and excellent performance characteristics. The application runs on Python 3.11+ with Uvicorn as the ASGI server.

**Database**: PostgreSQL 16 provides the primary data store with SQLAlchemy 2.0 as the ORM. Alembic handles database migrations, enabling version-controlled schema changes. The database connection pool is configured with appropriate sizing for production workloads.

**Caching and Message Broker**: Redis 7 serves dual purposes as an in-memory cache for frequently accessed data and as the message broker for Celery task queue. This eliminates the need for separate systems and simplifies infrastructure.

**Background Processing**: Celery 5.4 manages asynchronous task processing with dedicated queues for different task types (emails, progress tracking, certificate generation, webhooks). The architecture supports horizontal scaling of workers.

**Container Orchestration**: Docker and Docker Compose provide containerization for all services. The production setup uses Caddy as a reverse proxy with automatic HTTPS certificate management via Let's Encrypt.

**Observability**: Prometheus client library exposes application metrics, while Sentry provides error tracking and performance monitoring. The observability stack includes Grafana for visualization.

---

## Module Architecture

The application follows a modular monolith architecture where related functionality is grouped into vertical modules. Each module typically contains:

- **Models**: SQLAlchemy ORM models defining database schema
- **Schemas**: Pydantic models for request validation and response serialization
- **Repositories**: Data access layer implementing database operations
- **Services**: Business logic layer containing core functionality
- **Routers**: FastAPI route handlers exposing API endpoints

This pattern promotes code organization, separation of concerns, and makes the codebase navigable and maintainable despite being a monolithic application.

---

## Project Structure Overview

The project root contains the following primary directories:

- **app/**: Main application code including core infrastructure and modules
- **alembic/**: Database migration files
- **scripts/**: Utility scripts for deployment, data management, and development
- **tests/**: Test suite including unit, integration, and performance tests
- **ops/**: Infrastructure configuration files (Caddy, observability)
- **.github/workflows/**: GitHub Actions CI/CD pipelines
- **docs/**: Technical documentation in multiple languages
- **postman/**: Postman collections for API testing
- **certificates/**: Generated certificate PDFs
- **uploads/**: User-uploaded course materials

---

## Quick Start Commands

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload

# Run tests
pytest -q --cov=app --cov-fail-under=75
```

### Docker Development

```bash
# Start all services
docker compose up --build

# Start with demo data
docker compose up --build
python scripts/seed_demo_data.py --create-tables
```

### Production Deployment

```bash
# Configure production environment
cp .env.example .env
# Edit .env with production values

# Deploy with Docker
docker compose -f docker-compose.prod.yml up -d --build
```

---

## API Documentation

Interactive API documentation is available at the following endpoints when the application is running:

- **Swagger UI**: `/docs` - Interactive API documentation with request/response visualization
- **ReDoc**: `/redoc` - Alternative API documentation format
- **OpenAPI Schema**: `/openapi.json` - Raw OpenAPI specification in JSON format

Note: API documentation is disabled in production by default for security reasons. Set `ENABLE_API_DOCS=true` in development or staging environments to access these features.

---

## Configuration Reference

The application uses environment variables for configuration. Key configuration categories include:

- **Application**: Project name, version, environment, debug mode
- **Database**: PostgreSQL connection URL, pool settings
- **Security**: JWT secret key, token expiration times, rate limiting
- **Email**: SMTP configuration for transactional emails
- **Storage**: Local or Azure Blob storage for file uploads
- **Observability**: Sentry DSN, Prometheus metrics settings
- **Webhooks**: Webhook URLs and signing secrets for event notifications

See [03-Complete-Setup-And-Configuration.md](03-Complete-Setup-And-Configuration.md) for complete configuration options.

---

## Security Features

The LMS Backend implements comprehensive security measures:

- **Authentication**: JWT-based authentication with access and refresh tokens
- **Authorization**: Role-based access control (RBAC) with three roles: admin, instructor, student
- **Password Security**: Bcrypt hashing with salt for secure password storage
- **Rate Limiting**: Configurable rate limiting with Redis backend and in-memory fallback
- **Security Headers**: HTTP security headers via middleware (HSTS, X-Frame-Options, etc.)
- **Input Validation**: Pydantic models validate all incoming requests
- **SQL Injection Prevention**: ORM usage prevents SQL injection vulnerabilities
- **CORS**: Configurable cross-origin resource sharing settings

---

## Monitoring and Observability

The application includes comprehensive observability features:

- **Metrics**: Prometheus-compatible metrics endpoint at `/metrics`
- **Health Checks**: Readiness and liveness probes at `/api/v1/ready` and `/api/v1/health`
- **Error Tracking**: Sentry integration for exception tracking and performance monitoring
- **Request Logging**: All requests logged with timing information
- **Structured Logging**: JSON-formatted logs for production environments

---

## CI/CD Pipeline

GitHub Actions workflows handle continuous integration and deployment:

- **CI Workflow** (ci.yml): Runs on every push and pull request, executing static checks, unit tests, and coverage verification across Python 3.11 and 3.12
- **Security Workflow** (security.yml): Runs pip-audit, bandit security scanning, and gitleaks secret detection
- **Deploy Workflow** (deploy-azure-vm.yml): Deploys to Azure Virtual Machine on main branch merges

---

## Support and Contributing

For technical questions or contributions:

1. Review the relevant documentation in docs/tech/
2. Check existing GitHub issues
3. Review API documentation at /docs when running locally
4. Examine test files in tests/ for implementation patterns

---

## Version Information

- **Current Version**: 1.0.0
- **Python Support**: 3.11, 3.12
- **Database**: PostgreSQL 16
- **Last Updated**: 2026

---

*This documentation is part of the LMS Backend project. For the most up-to-date information, refer to the source code and inline documentation.*
