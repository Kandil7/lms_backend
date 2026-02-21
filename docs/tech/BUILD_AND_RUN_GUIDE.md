# How to Build and Run the LMS Backend

This comprehensive guide provides step-by-step instructions for building and running the LMS Backend project from scratch. Whether you are setting up a development environment, running tests, or deploying to production, this guide covers everything you need.

---

## Prerequisites

Before beginning, ensure you have the following installed on your system:

### Required Software

**Python 3.11 or Higher**: The project requires Python 3.11+ for type hints, modern language features, and performance improvements. Download from python.org or use a version manager like pyenv (Linux/Mac) or py launcher (Windows).

**PostgreSQL 14 or Higher**: The primary relational database. Install from postgresql.org or use Docker to run PostgreSQL in a container. Ensure you have administrative access to create databases and users.

**Redis 7 or Higher**: Required for caching, rate limiting, and as the Celery message broker. Install from redis.io or use Docker. Redis runs on port 6379 by default.

**Git**: For version control and cloning the repository. Install from git-scm.com.

**Docker and Docker Compose** (Optional but Recommended): For containerized development and deployment. Install Docker Desktop (Windows/Mac) or Docker Engine (Linux).

### Optional but Useful Tools

**Postman or Insomnia**: For testing API endpoints interactively. Postman collections are included in the postman/ directory.

**pgAdmin or DBeaver**: For database administration and visualization. Helpful for understanding data and debugging issues.

**Visual Studio Code or PyCharm**: Recommended IDEs with Python support. VS Code is free and excellent for Python development.

---

## Step 1: Clone the Repository

Begin by cloning the project repository to your local machine:

```bash
git clone <repository-url>
cd lms_backend
```

If you do not have the repository, you would need to obtain it from your version control system. The project structure should match what was described in the project overview documentation.

---

## Step 2: Set Up Python Environment

The project uses a virtual environment to isolate dependencies from your system Python. This prevents conflicts with other Python projects and ensures reproducible builds.

### Creating the Virtual Environment

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

On Linux or Mac:

```bash
python3 -m venv venv
source venv/bin/activate
```

You should see (venv) prefix in your terminal prompt, indicating the virtual environment is active.

### Installing Dependencies

With the virtual environment activated, install all required packages:

```bash
pip install -r requirements.txt
```

This installs all Python packages defined in requirements.txt. The installation may take a few minutes as it compiles some packages like SQLAlchemy and lxml.

---

## Step 3: Configure Environment Variables

The application requires configuration through environment variables. The project includes an example file that you can copy and customize.

### Copy the Example Environment File

```bash
cp .env.example .env
```

### Edit the Configuration

Open .env in your preferred text editor and configure the following key settings:

**Database Connection**:

```env
DATABASE_URL=postgresql+psycopg2://lms:lms@localhost:5432/lms
```

Replace lms:lms with your PostgreSQL username and password. Replace localhost:5432 with your PostgreSQL host and port if different.

**Redis Connection**:

```env
REDIS_URL=redis://localhost:6379/0
```

This assumes Redis runs on localhost port 6379. The /0 specifies database number 0.

**Security Settings**:

```env
SECRET_KEY=your-secret-key-here-minimum-32-characters
```

Generate a secure secret key. On Linux/Mac, you can generate one:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Environment Mode**:

```env
ENVIRONMENT=development
DEBUG=True
```

For production, change these to ENVIRONMENT=production and DEBUG=False.

---

## Step 4: Set Up Database

### Option A: Using Docker (Recommended)

The easiest way to run PostgreSQL and Redis is using Docker Compose:

```bash
docker-compose up -d db redis
```

This starts PostgreSQL on port 5432 and Redis on port 6379. The containers persist data in Docker volumes.

### Option B: Local Installation

If you prefer running databases locally:

1. Start PostgreSQL service
2. Create a database named lms
3. Create a user named lms with password lms
4. Grant all privileges on lms database to lms user

Example commands for Linux:

```bash
sudo -u postgres createuser -s lms
sudo -u postgres psql -c "alter user lms with password 'lms';"
sudo -u postgres createdb lms
sudo -u postgres psql -c "grant all privileges on database lms to lms;"
```

### Run Database Migrations

With the database running, create the initial schema:

```bash
alembic upgrade head
```

This applies all migration files in alembic/versions/ to create the database tables. You should see output indicating successful migration.

---

## Step 5: Start the Application

### Development Server

Start the FastAPI development server with auto-reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The --reload flag enables auto-reload on code changes, useful during development. The server runs on all interfaces (0.0.0.0) on port 8000.

### Verify the Application

Open your browser and navigate to:

- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc
- Health Check: http://localhost:8000/api/v1/health
- Readiness Check: http://localhost:8000/api/v1/ready

You should see the Swagger UI with all available endpoints documented.

---

## Step 6: Background Services

For full functionality, you need to run Celery workers for background task processing.

### Start Celery Worker

In a new terminal (with virtual environment activated):

```bash
celery -A app.tasks.celery_app.celery_app worker --loglevel=info --queues=emails,progress,certificates
```

This starts a Celery worker processing tasks from the emails, progress, and certificates queues. The worker logs task execution information.

### Start Celery Beat (Optional)

For scheduled tasks, start the Celery beat scheduler:

```bash
celery -A app.tasks.celery_app.celery_app beat --loglevel=info
```

Beat schedules periodic tasks like cleanup jobs or analytics updates.

---

## Step 7: Running Tests

The project includes comprehensive test coverage. Run tests to verify everything works correctly.

### Run All Tests

```bash
pytest
```

This discovers and runs all tests in the tests/ directory. You should see output showing passed and failed tests.

### Run Tests with Coverage

```bash
pytest --cov=app --cov-report=html
```

This generates an HTML coverage report in the htmlcov/ directory. Open index.html to see which lines are covered by tests.

### Run Specific Test Files

```bash
pytest tests/test_auth.py -v
pytest tests/test_courses.py -v
pytest tests/test_quizzes.py -v
```

Use the -v flag for verbose output showing individual test names.

### Run Tests in Watch Mode

For development, use pytest-watch to run tests automatically on file changes:

```bash
pip install pytest-watch
pytest-watch
```

---

## Step 8: Docker-Based Development

Instead of running services locally, you can use Docker Compose for the entire development environment.

### Start All Services

```bash
docker-compose up -d
```

This starts:
- API server on port 8000
- Celery worker
- Celery beat scheduler
- PostgreSQL on port 5432
- Redis on port 6379

### View Logs

```bash
docker-compose logs -f api
docker-compose logs -f celery-worker
```

### Stop Services

```bash
docker-compose down
```

This stops and removes all containers. Data in volumes is preserved.

---

## Step 9: Production Deployment

For production deployment, use the production Docker Compose configuration.

### Build Production Image

```bash
docker-compose -f docker-compose.prod.yml build
```

### Configure Production Settings

Create a production .env file with:

```env
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<strong-64-character-key>
DATABASE_URL=postgresql+psycopg2://<user>:<password>@db:5432/lms
REDIS_URL=redis://redis:6379/0
CORS_ORIGINS=https://your-domain.com
SECURITY_HEADERS_ENABLED=True
RATE_LIMIT_USE_REDIS=True
TASKS_FORCE_INLINE=False
SENTRY_DSN=<your-sentry-dsn>
```

### Start Production Services

```bash
docker-compose -f docker-compose.prod.yml up -d
```

This starts optimized production containers with:
- Gunicorn as the ASGI server
- Multiple worker processes
- Proper logging configuration
- Health checks enabled

---

## Step 10: Common Development Tasks

### Creating a Test User

You can create a test user through the API:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "full_name": "Test User"
  }'
```

Or use the Swagger UI at /docs to interact with the registration endpoint.

### Creating a Course (As Instructor)

First, register a user and update their role to instructor in the database, then:

```bash
curl -X POST http://localhost:8000/api/v1/courses \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Introduction to Python",
    "description": "Learn Python from scratch",
    "category": "Programming",
    "difficulty_level": "beginner"
  }'
```

### Enrolling in a Course (As Student)

```bash
curl -X POST http://localhost:8000/api/v1/enrollments \
  -H "Authorization: Bearer <student_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "<course-uuid>"
  }'
```

### Uploading a File

```bash
curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/file.pdf"
```

---

## Troubleshooting

### Database Connection Errors

**Problem**: Cannot connect to PostgreSQL.

**Solutions**:
- Verify PostgreSQL is running: docker-compose ps or systemctl status postgresql
- Check DATABASE_URL in .env is correct
- Verify database user has permissions: psql -U lms -d lms

### Redis Connection Errors

**Problem**: Cannot connect to Redis.

**Solutions**:
- Verify Redis is running: docker-compose ps or redis-cli ping
- Check REDIS_URL in .env
- Ensure port 6379 is not blocked

### Import Errors

**Problem**: Module not found errors.

**Solutions**:
- Ensure virtual environment is activated
- Reinstall dependencies: pip install -r requirements.txt
- Check PYTHONPATH includes project root

### Port Already in Use

**Problem**: Port 8000 is already in use.

**Solutions**:
- Find and stop the process: netstat -ano | findstr :8000 (Windows) or lsof -i :8000 (Mac/Linux)
- Change the port: uvicorn app.main:app --port 8001

### Migration Errors

**Problem**: Database migration fails.

**Solutions**:
- Check database is running and accessible
- Verify DATABASE_URL is correct
- Check migration files in alembic/versions/ for syntax errors

### Celery Connection Errors

**Problem**: Celery cannot connect to Redis broker.

**Solutions**:
- Verify Redis is running
- Check CELERY_BROKER_URL and CELERY_RESULT_BACKEND in settings
- Ensure Redis accepts connections from Celery containers

---

## Development Workflow Summary

A typical development workflow looks like:

1. **Start services**: docker-compose up -d db redis
2. **Start API**: uvicinnel app.main:app --reload
3. **Start Celery**: celery -A app.tasks.celery_app.celery_app worker --loglevel=info
4. **Make changes**: Edit code, tests auto-reload
5. **Run tests**: pytest
6. **Check docs**: Visit /docs

For Docker-based development:

1. **Start everything**: docker-compose up -d
2. **View logs**: docker-compose logs -f
3. **Stop**: docker-compose down

---

## Additional Resources

### API Documentation

Interactive API documentation is available at http://localhost:8000/docs when the server is running. This Swagger UI allows you to explore all endpoints and try them interactively.

### Database Schema

The complete database schema is defined in alembic/versions/ migration files. Each migration creates or modifies database tables. The final schema includes:

- users: User accounts with roles
- courses: Course content and metadata
- lessons: Individual lessons within courses
- enrollments: Student-course relationships
- lesson_progress: Lesson completion tracking
- quizzes: Quiz configurations
- quiz_questions: Questions within quizzes
- quiz_attempts: Student quiz attempts
- certificates: Generated completion certificates
- files: Uploaded file metadata
- refresh_tokens: Session tokens

### Configuration Reference

All configuration options are defined in app/core/config.py with detailed comments. Key categories include:

- Application settings (name, version, environment)
- Database configuration (URL, pool settings)
- Security settings (JWT, passwords, MFA)
- Cache settings (Redis, TTL values)
- Rate limiting (limits per endpoint type)
- File storage (providers, limits)

---

This guide provides everything you need to build, run, and develop the LMS Backend. For more detailed information about specific modules or features, refer to the other documentation files in the docs/tech/ directory.
