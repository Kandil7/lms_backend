# Comprehensive Project Guide: EduConnect Pro LMS

Welcome to the definitive guide for the **EduConnect Pro LMS Backend**. This document serves as the master entry point for understanding the system's architecture, core components, and functional modules. It is designed to transform a new developer into a productive contributor.

---

## 📋 Table of Contents
1. [Project Vision & Architecture](#1-project-vision--architecture)
2. [The Core Engine (`app/core/`)](#2-the-core-engine-appcore)
3. [Functional Modules (`app/modules/`)](#3-functional-modules-appmodules)
4. [Authentication & Security](#4-authentication--security)
5. [Data Flow & Lifecycle](#5-data-flow--lifecycle)
6. [Operational Infrastructure](#6-operational-infrastructure)
7. [Developer Workflows](#7-developer-workflows)

---

## 1. Project Vision & Architecture

**EduConnect Pro** is a scalable, secure Learning Management System (LMS) designed for the modern web. It supports three distinct personas:
- **Students**: Consume content, take quizzes, and earn certificates.
- **Instructors**: Create courses, manage content, and track student progress.
- **Admins**: Oversee the platform, manage users, and monitor system health.

### The Modular Monolith Pattern
We use a **Modular Monolith** architecture. Instead of a "spaghetti code" monolith or the complexity of microservices, we organize code into self-contained **Modules**.

- **Loose Coupling**: Modules interact via public interfaces (Services), not by reaching into each other's databases.
- **High Cohesion**: Related logic (e.g., Quizzes + Questions + Attempts) stays together.
- **Future-Proof**: A module can be extracted into a microservice if scaling demands it.

---

## 2. The Core Engine (`app/core/`)
The `core` folder is the infrastructure layer. It contains code that *supports* the business logic but doesn't contain business logic itself.

- **`config.py`**: The single source of truth for configuration. It loads environment variables (from `.env`) into a Pydantic settings object.
- **`database.py`**: Manages the PostgreSQL connection pool and SQLAlchemy sessions.
- **`security.py`**: Implements password hashing (Bcrypt) and JWT token generation/validation.
- **`permissions.py`**: Defines the Role-Based Access Control (RBAC) matrix (e.g., `Instructor` -> `can_create_course`).
- **`dependencies.py`**: FastAPI dependencies for injecting Users, Database Sessions, and Permissions into routes.
- **`middleware/`**: Logic that wraps every request (Logging, Rate Limiting, Response Envelopes).

> **👉 Deep Dive**: Read the [Core Folder Details](./CORE_FOLDER_DETAILS.md) for a line-by-line explanation.

---

## 3. Functional Modules (`app/modules/`)
This is where the business value lives. Each folder is a mini-application.

### 🔑 Identity & Access
- **[Auth](./MODULE_AUTH_IDENTITY.md)**: Login, Registration, MFA, and Token Rotation.
- **[Users](./MODULE_AUTH_IDENTITY.md)**: Profile management and Role assignment.
- **[Instructors](./MODULE_AUTH_IDENTITY.md)**: Specialized onboarding and verification flows for teachers.
- **[Admin](./MODULE_AUTH_IDENTITY.md)**: System-wide governance and user management.

### 📚 Learning Content
- **[Courses](./MODULE_COURSE_CONTENT.md)**: The catalog structure (Course -> Section -> Lesson).
- **[Files](./MODULE_COURSE_CONTENT.md)**: Secure asset management for videos and documents.

### 🎓 The Student Journey
- **[Enrollments](./MODULE_LEARNING_JOURNEY.md)**: Tracks the relationship between a User and a Course.
- **[Quizzes](./MODULE_LEARNING_JOURNEY.md)**: Complex assessment engine with automated grading.
- **[Assignments](./MODULE_LEARNING_JOURNEY.md)**: Manual submission and grading workflows.
- **[Certificates](./MODULE_LEARNING_JOURNEY.md)**: PDF generation upon course completion.

### 💼 Business Operations
- **[Payments](./MODULE_BUSINESS_OPS.md)**: Monetization, transactions, and revenue splitting.
- **[Analytics](./MODULE_BUSINESS_OPS.md)**: Data aggregation for dashboards (Student, Instructor, Admin).
- **[WebSockets](./WEBSOCKETS_REALTIME.md)**: Real-time event broadcasting (Notifications, Progress Sync).

---

## 4. Authentication & Security
Security is baked into the design, not added as an afterthought.

### Dual-Mode Authentication
1. **JWT (Stateless)**: Used for Mobile Apps and API Integrations. Requires `Authorization: Bearer <token>`.
2. **HttpOnly Cookies (Stateful)**: Used for the Web Frontend. Prevents XSS attacks by making tokens inaccessible to JavaScript.

### Defense Layers
- **Rate Limiting**: Redis-backed protection against Brute Force and DoS attacks.
- **CSRF Protection**: Critical for cookie-based auth to prevent Cross-Site Request Forgery.
- **Input Sanitization**: All HTML input is scrubbed to prevent Stored XSS.

> **👉 Deep Dive**: Read the [Security Deep Dive](./SECURITY_DEEP_DIVE.md).

---

## 5. Data Flow & Lifecycle
How does data move through the system?

1. **Request**: Enters via **FastAPI Router** (`api/v1/api.py`).
2. **Validation**: Validated by **Pydantic Schemas** (`modules/*/schemas.py`).
3. **Logic**: Processed by the **Service Layer** (`modules/*/service.py`).
4. **Persistence**: Saved by the **Repository Layer** (`modules/*/repository.py`) using **SQLAlchemy models**.
5. **Background**: Heavy tasks (Emails, PDF gen) are offloaded to **Celery Workers** (`tasks/`).
6. **Response**: Returned to the client wrapped in a standard JSON envelope.

---

## 6. Operational Infrastructure
Keeping the lights on in production.

- **Docker Compose**: Orchestrates the API, Database, Redis, and Worker containers.
- **PostgreSQL**: The relational backbone. Uses UUIDs for primary keys.
- **Redis**: Powering caching, session storage, and the Celery task queue.
- **Sentry**: Real-time error tracking and performance monitoring.
- **Prometheus/Grafana**: Metrics for system health (Request Latency, DB Pool size).

> **👉 Deep Dive**: Read the [DevOps & Deployment Handbook](./DEVOPS_DEPLOYMENT.md).

---

## 7. Developer Workflows
How to contribute effectively.

- **Adding Features**: Follow the [Module Creation Guide](./ADDING_NEW_MODULE.md).
- **Testing**: We use **PyTest**. Run `pytest` to execute the suite. See [Testing Strategy](./TESTING_QA_STRATEGY.md).
- **Frontend Integration**: See the [Frontend Guide](./FRONTEND_INTEGRATION.md) for connecting your UI.
- **Troubleshooting**: Stuck? Check the [Troubleshooting Guide](./TROUBLESHOOTING_GUIDE.md).

---

## 🔗 Quick Links
- [API Documentation (Swagger)](http://localhost:8000/docs)
- [Postman Collection](./postman_guidance.md)
- [Integration Status](../../INTEGRATION_STATUS.md)
