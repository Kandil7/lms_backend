# Core Folder Deep Dive: The Engine Room

This guide explains the `app/core/` directory, which provides the foundation for all functional modules.

---

## ⚙️ Configuration (`config.py`)
- **Pydantic Settings**: We use `BaseSettings` to load environment variables.
- **Validation**: It crashes the app at startup if critical vars (like `DATABASE_URL`) are missing.
- **Computed Properties**: Derived settings (e.g., constructing the full `ASYNC_DATABASE_URL` from parts).

## 🗄️ Database (`database.py` & `model_registry.py`)
- **`database.py`**:
  - Creates the `SQLAlchemy` engine with connection pooling.
  - Defines the `get_db` dependency generator.
- **`model_registry.py`**:
  - The "Yellow Pages" of the app. It imports all models so `Alembic` can see them.
  - Prevents circular import errors by centralizing model loading.

## 🛡️ Security (`security.py` & `permissions.py`)
- **`security.py`**:
  - `hash_password()`: Bcrypt hashing.
  - `create_access_token()`: JWT generation.
  - `verify_token()`: Decodes and validates JWT signature.
- **`permissions.py`**:
  - Defines the `Role` enum.
  - `Permission`: A class mapping Actions (Create Course) to Roles (Instructor).

## 🌐 Middleware (`middleware/`)
- **`RequestLoggingMiddleware`**: Logs every request (Method, Path, Status, Duration). **Crucial**: Redacts headers like `Authorization`.
- **`ResponseEnvelopeMiddleware`**: Wraps every JSON response in `{ success: true, data: ... }`.
- **`RateLimitMiddleware`**: Redis-backed limiter.

## 🧱 Dependencies (`dependencies.py`)
Reusable logic for `fastapi.Depends`:
- `get_current_user`: Validates token -> Fetches User.
- `get_current_active_user`: Checks `user.is_active`.
- `require_role(Role.ADMIN)`: Authorization guard.

## 👁️ Observability (`observability.py` & `metrics.py`)
- **`observability.py`**: Configures Sentry SDK.
- **`metrics.py`**: Exports Prometheus metrics (request count, error rate).
- **`health.py`**: logic for `/health` and `/ready` endpoints. Checks DB/Redis connectivity.
