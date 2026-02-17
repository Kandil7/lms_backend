# LMS Backend

Modular monolith LMS backend built with FastAPI + SQLAlchemy.

## Stack
- FastAPI
- PostgreSQL (SQLAlchemy ORM + Alembic)
- Redis (cache / queues)
- Celery for background tasks

## Run Locally
1. Create virtualenv and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and adjust values.
3. Run API:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Open docs at `http://localhost:8000/docs`.

## Docker
```bash
docker compose up --build
```

## Migrations
```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## Branch Strategy
- `main`: production-ready branch.
- `develop`: integration branch.
- `feature/*` or `chore/*`: short-lived implementation branches.
- Merge policy: `--no-ff` merges from feature branches into `develop`, then `develop` into `main`.

## Current Status
Core infrastructure is bootstrapped. Domain modules are implemented in follow-up feature branches.
