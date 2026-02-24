# Troubleshooting Guide

This guide addresses common issues encountered during development and deployment of the EduConnect Pro LMS Backend.

---

## 🏗️ 1. Database & Migrations

### Issue: `Target database is not up to date`
**Cause**: Your local database schema is behind the latest migration scripts.
**Solution**: Run the upgrade command:
```bash
alembic upgrade head
```

### Issue: `Relation "X" does not exist`
**Cause**: A module was added but its model hasn't been imported into the metadata registry.
**Solution**: Ensure your module's model is registered in `app/core/model_registry.py`.
```python
# app/core/model_registry.py
def load_all_models():
    import app.modules.users.models
    import app.modules.your_new_module.models  # Add this!
```

---

## 🔑 2. Authentication & Security

### Issue: `401 Unauthorized` even with a valid token
**Cause**: The token might have expired (default 15 mins) or the `SECRET_KEY` changed.
**Solution**: 
1. Check the `exp` claim in your JWT.
2. Refresh the token using `POST /auth/refresh`.
3. If using Cookies, ensure `HttpOnly` and `SameSite` flags match your environment.

### Issue: `403 Forbidden` for Admin endpoints
**Cause**: The user role in the database is not 'admin'.
**Solution**: Manually update the role in PostgreSQL for testing:
```sql
UPDATE users SET role = 'admin' WHERE email = 'your-email@example.com';
```

---

## 🚀 3. Environment & Docker

### Issue: `Connection refused` to Redis or PostgreSQL
**Cause**: Containers are not in the same network or haven't finished starting.
**Solution**:
1. Check logs: `docker-compose logs -f db` or `docker-compose logs -f redis`.
2. Ensure `.env` points to the service names (e.g., `REDIS_URL=redis://redis:6379`) instead of `localhost`.

### Issue: Changes in code not reflecting in Docker
**Cause**: Docker cache is reusing the old build.
**Solution**: Force a rebuild:
```bash
docker-compose build --no-cache api
```

---

## ⚡ 4. Background Tasks (Celery)

### Issue: Progress percentage not updating
**Cause**: The Celery worker is either not running or cannot connect to the broker.
**Solution**:
1. Ensure the worker is started: `celery -A app.tasks.celery_app worker --loglevel=info`.
2. Check the Redis queue for pending tasks.

---

## 📊 5. Observability

### Issue: Metrics not showing at `/metrics`
**Cause**: Prometheus middleware is disabled or the endpoint is blocked by a rate limiter.
**Solution**:
1. Check `METRICS_ENABLED=true` in your `.env`.
2. Ensure `/metrics` is in the `RATE_LIMIT_EXCLUDED_PATHS`.

---

## 🛠️ 6. Useful Debugging Commands

- **Reset Database**: `alembic downgrade base && alembic upgrade head`
- **View active DB connections**: `SELECT * FROM pg_stat_activity;`
- **Inspect JWT**: Use [jwt.io](https://jwt.io) to see payload and expiry.
- **Check Redis Keys**: `redis-cli KEYS "*"`
