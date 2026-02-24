# Project Structure: A High-Level Map

This guide provides a mental map of the entire repository.

---

## 📂 Root Level
- **`app/`**: Source code.
- **`alembic/`**: Database migrations.
- **`tests/`**: Test suite.
- **`docs/`**: Documentation.
- **`docker-compose.yml`**: Local infrastructure.

## 📂 `app/` Breakdown
- **`api/`**: **Interface Layer**.
  - `v1/api.py`: The "Main Router". It imports all module routers and adds them to the FastAPI app.
- **`core/`**: **Infrastructure Layer**. Config, DB, Security.
- **`modules/`**: **Domain Layer** (Business Logic).
  - Each folder here is a "Bounded Context" (e.g., `courses`, `users`).
- **`tasks/`**: **Worker Layer**. Celery tasks for background processing.
- **`utils/`**: **Shared Kernel**. Helpers used by multiple modules (e.g., `pagination.py`).

## 📂 `modules/` Anatomy
Every module follows the **Service-Repository Pattern**:
- **`models.py`**: Database Tables.
- **`schemas.py`**: Pydantic Models (API Data Transfer Objects).
- **`repository.py`**: Direct DB queries (CRUD).
- **`service.py`**: Business Rules (Validation, Calculations).
- **`router.py`**: HTTP Endpoints (Calls Service).
- **`dependencies.py`**: Module-specific dependency injection.

## 📂 `tests/`
- **`unit/`**: Fast tests for Services/Utils.
- **`integration/`**: Tests checking Router -> Database flow.
- **`conftest.py`**: Global test fixtures (Test Client, Mock DB Session).
