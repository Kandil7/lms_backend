# Tech Stack and Key Choices

This document summarizes the main technology choices in the LMS backend and the currently enforced defaults.

## Runtime and API

- Python `3.11+` / `3.12`
- FastAPI for HTTP API and OpenAPI generation
- Pydantic v2 for validation and settings

## Data and Background Jobs

- PostgreSQL as the primary relational database
- SQLAlchemy + Alembic for ORM and migrations
- Redis for caching/rate-limit state and Celery broker/result backend
- Celery for async/background jobs

## File Storage Decision

- Default provider: `azure`
- Supported providers: `azure`, `local`
- Production behavior is **fail-closed** for Azure:
  - If `FILE_STORAGE_PROVIDER=azure` and Azure backend is not available, startup/runtime fails instead of silently falling back to local.

## Required Production Storage Settings (Azure)

When `ENVIRONMENT=production` and `FILE_STORAGE_PROVIDER=azure`, these are required:

- `AZURE_STORAGE_CONTAINER_NAME`
- One of:
  - `AZURE_STORAGE_CONNECTION_STRING`
  - `AZURE_STORAGE_ACCOUNT_URL`

Recommended optional settings:

- `AZURE_STORAGE_ACCOUNT_NAME`
- `AZURE_STORAGE_ACCOUNT_KEY`
- `AZURE_STORAGE_CONTAINER_URL`

## Why Azure Blob Storage

- Managed durability and availability for media/doc uploads
- Better separation between app compute and file persistence
- Supports secure URL-based access and private containers
- Fits Azure-native production deployments used in this project

## Local Development

- `FILE_STORAGE_PROVIDER=azure` is the default.
- For local-only testing, you can still use `FILE_STORAGE_PROVIDER=local`.
- In non-production environments, unavailable Azure backend may fall back to local storage.
