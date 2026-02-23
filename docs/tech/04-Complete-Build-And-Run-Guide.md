# Complete Build and Run Guide

This comprehensive guide provides detailed instructions for building and running the LMS Backend project in all environments. Whether you are setting up a local development environment, preparing for staging deployment, or configuring production infrastructure, this guide covers all necessary steps with explanations of each decision and configuration choice.

---

## Prerequisites and System Requirements

Before beginning the setup process, ensure your development machine or server meets the following requirements. The LMS Backend is designed to run on modern hardware and supports multiple operating systems including Windows, macOS, and Linux.

### Hardware Requirements

For local development, a machine with at least 8GB of RAM is recommended to run the full stack including PostgreSQL, Redis, and the application containers. The application itself requires minimal resources, but the database and cache services benefit from additional memory for optimal performance. At least 20GB of available disk space is needed for the database, uploaded files, and application dependencies.

For production deployment, the requirements depend on expected user load. A minimal production setup can run on a virtual machine with 2 vCPUs and 4GB of RAM, while a high-traffic deployment may require 4+ vCPUs and 8GB+ of RAM. PostgreSQL should be provisioned with sufficient IOPS for query performance, and Redis requires adequate memory for caching and session storage.

### Software Requirements

The following software must be installed on your development machine or build server. Each requirement includes the version constraints and rationale for the choice.

Python 3.11 or 3.12 is required as the application runtime. Python 3.11 is recommended for its balance of performance and stability, while Python 3.12 offers slightly better performance but may have compatibility issues with some packages. The application is tested against both versions in CI, ensuring compatibility with either choice.

Docker Desktop (Windows/macOS) or Docker Engine (Linux) is required for containerized development and deployment. Docker Compose is included with Docker Desktop and Docker Engine. The minimum supported Docker version is 20.10, which provides the features required for multi-container orchestration.

PostgreSQL 16 is recommended for local development if running without Docker. The application uses PostgreSQL-specific features including JSON columns and advanced indexing. For production, Azure Database for PostgreSQL Flexible Server or Amazon RDS for PostgreSQL are recommended managed options.

Redis 7 is required for caching, session storage, and Celery message broker. The Redis server should be accessible via network connection from the application. In production, managed Redis services like Azure Cache for Redis or Redis Enterprise Cloud provide high availability and automatic failover.

---

## Local Development Setup

The local development setup allows you to run the application directly on your machine without Docker. This approach provides faster iteration cycles, easier debugging, and direct access to Python debugging tools.

### Virtual Environment Creation

Create a Python virtual environment to isolate project dependencies from your system Python installation. This prevents version conflicts with other Python projects and ensures reproducible builds. Navigate to the project root directory and execute the following commands to create and activate the virtual environment.

Using venv (built-in Python module), create the environment with the command python -m venv venv. On Windows, activate it with venv\Scripts\activate, and on Unix systems, use source venv/bin/activate. Once activated, your terminal prompt will show the virtual environment name, indicating that Python commands will use the isolated environment.

Alternatively, you may use Poetry or Pipenv for dependency management. Poetry provides lockfile-based dependency resolution and built-in virtual environment management. To use Poetry, install it with pip install poetry and run poetry install in the project root. The project includes pyproject.toml for Poetry users, though requirements.txt is provided for pip-based workflows.

### Dependency Installation

With the virtual environment activated, install all project dependencies using pip. The requirements.txt file contains all necessary packages with version constraints ensuring compatibility. Execute pip install -r requirements.txt to install the core dependencies including FastAPI, SQLAlchemy, Celery, and all other required packages.

The installation process may take several minutes as it compiles some dependencies like lxml and cryptography. On Windows, you may need to install Visual C++ Build Tools if prompted. If you encounter errors related to python-magic, you can install the system magic library or use the pre-built wheel.

After installation, verify that all dependencies are correctly installed by running python -c "import fastapi; import sqlalchemy; import celery; print('OK')". This quick check confirms that the core packages are importable and correctly linked.

### Environment Configuration

The application reads configuration from environment variables. The .env.example file in the project root contains all required configuration options with sensible defaults for development. Copy this file to create your local configuration.

Execute cp .env.example .env to create the local environment file. Open the .env file in a text editor and review the configuration options. For local development, most defaults are appropriate, but you should at minimum configure the following settings to ensure proper operation.

The SECRET_KEY should be set to a random string of at least 32 characters. In development, you can use any string, but it must meet the minimum length requirement. Generate a secure key with python -c "import secrets; print(secrets.token_hex(32))" and copy the result to your .env file.

The DATABASE_URL should point to your PostgreSQL instance. For local development with default PostgreSQL settings, use postgresql+psycopg2://lms:lms@localhost:5432/lms. Create the database first with createdb lms if it does not exist, and ensure the user lms with password lms has appropriate permissions.

The REDIS_URL should point to your Redis instance. For local development with default Redis settings, use redis://localhost:6379/0. Ensure Redis is running before starting the application.

### Database Setup

With dependencies installed and configuration complete, set up the database schema using Alembic migrations. The migration system manages database schema changes in a version-controlled manner, allowing you to easily upgrade or downgrade the database structure.

Execute alembic upgrade head to apply all migrations and create the initial schema. This command connects to the database using the DATABASE_URL configuration and creates all required tables, indexes, and constraints. The first migration (0001_initial_schema.py) creates the complete initial schema for all modules.

If you need to create the database schema without migrations (for quick testing), you can use SQLAlchemy's create_all method. However, this approach is not recommended for production as it does not provide upgrade paths. The migration-based approach is always preferred.

To verify database setup, you can inspect the created tables using your preferred PostgreSQL client. Connect to the lms database and run \dt to list all tables. You should see tables for users, courses, lessons, enrollments, quizzes, questions, attempts, certificates, files, assignments, and submissions.

### Creating Initial Users

After database setup, create the initial admin user to access the application. The project includes convenience scripts for user creation with appropriate defaults.

Execute python scripts/create_admin.py to create an admin user with default credentials (admin@lms.local / AdminPass123). The script accepts environment variables for customization: ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_FULL_NAME. You can also specify --update-existing to update an existing admin user's password.

For an instructor account, execute python scripts/create_instructor.py. This creates an instructor user with credentials instructor@lms.local / InstructorPass123 by default. Customize via INSTRUCTOR_EMAIL, INSTRUCTOR_PASSWORD, INSTRUCTOR_FULL_NAME environment variables.

The generic user creation script python scripts/create_user.py accepts --email, --password, --full-name, --role, and --update-existing flags for full customization. Use this for creating student accounts or additional users of any role.

### Running the Development Server

With database and users configured, start the development server using Uvicorn. The development server provides auto-reload functionality, automatically restarting when code changes are detected.

Execute uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 to start the server. The --reload flag enables auto-reload, --host 0.0.0.0 makes the server accessible on all network interfaces, and --port 8000 sets the HTTP port.

Once started, the server logs will show the startup process including loaded routers and middleware. The application is accessible at http://localhost:8000. The API documentation is available at http://localhost:8000/docs (Swagger UI) and http://localhost:8000/redoc (ReDoc).

For Windows-specific convenience, you can use the provided scripts. Execute scripts\run_project.bat for a fully configured startup experience with optional flags like -NoMigrate, -CreateAdmin, -SeedDemoData. Run scripts\run_project.ps1 for PowerShell users with the same functionality.

---

## Docker-Based Development

Docker-based development provides a consistent environment that matches production infrastructure. This approach is recommended for teams wanting to minimize environment-specific issues and for testing production-like configurations locally.

### Docker Compose Overview

The project includes multiple Docker Compose files for different purposes. The primary docker-compose.yml defines the development stack with all necessary services.

The development stack includes the following services running in containers. The api service runs the FastAPI application with uvicorn. The db service runs PostgreSQL 16 Alpine for the database. The redis service runs Redis 7 Alpine for caching and message broker. The celery-worker service runs Celery worker for background tasks. The celery-beat service runs Celery beat for scheduled tasks.

Each service is configured with appropriate resource limits, health checks, and restart policies. The services communicate over a shared Docker network, with the database and redis exposed only internally.

### Starting the Stack

To start the development stack, execute docker compose up --build in the project root. The --build flag ensures images are built before containers start, picking up any code changes. On first run, this builds the application image which may take several minutes.

After containers start, view logs with docker compose logs -f to monitor the startup process. The api service will be ready when you see "Application startup complete" in the logs. The db and redis services include health checks that must pass before the application can connect.

The application is accessible at http://localhost:8000 with full API documentation. PostgreSQL is accessible at localhost:5432 with credentials lms/lms/lms. Redis is accessible at localhost:6379 for debugging with redis-cli.

### Using Development Scripts

Several convenience scripts simplify Docker-based development. The scripts/run_project.ps1 script (PowerShell) or scripts/run_project.bat (Batch) provides a unified interface with multiple options.

Available flags include -NoBuild to skip the build step when you know images are current, -NoMigrate to skip database migration if already applied, -CreateAdmin to create an admin user after startup, -CreateInstructor to create an instructor user, -SeedDemoData to populate demo data, and -FollowLogs to stream container logs after startup.

For example, to start the stack with demo data and follow logs, execute .\scripts\run_project.ps1 -SeedDemoData -FollowLogs. This single command starts all services, runs migrations, creates demo users, seeds sample course data, and displays the logs.

### Development with Hot Reload

The development Docker configuration enables hot reload for rapid iteration. Volume mounts share your source code into the container, and the uvicorn server is configured with reload enabled.

When you edit Python files in your local editor, the changes are reflected in the running container within seconds. This provides a fast feedback loop similar to local development while maintaining Docker's consistency benefits.

Note that some operations like database migrations may require container restart to pick up changes to migration files. If you modify Alembic migrations, restart the api container with docker compose restart api or rebuild with docker compose up --build.

---

## Demo Data Seeding

The demo data seeding script creates a complete sample environment for testing and demonstration purposes. This includes multiple user types, a sample course with lessons, quiz questions, enrollment, and certificate generation.

### Running the Seed Script

Execute python scripts/seed_demo_data.py to populate the database with demo data. By default, the script creates demo users, a sample course, lessons, enrollment, a quiz with questions, a submitted attempt, and a certificate.

The script supports several options for customization. Use --create-tables to create database tables if they do not exist (useful for fresh databases). Use --reset-passwords to update passwords if demo users already exist. Use --skip-attempt to skip creating the quiz attempt and certificate. Use --json-output <path> to generate a JSON snapshot of seeded data for Postman collection generation.

After seeding, you can log in with the following demo credentials. The admin account is admin@lms.local with password AdminPass123. The instructor account is instructor@lms.local with password InstructorPass123. The student account is student@lms.local with password StudentPass123.

The seeded course "Python LMS Demo Course" includes three lessons: a welcome video lesson marked as preview, a text-based Python basics lesson, and a quiz lesson. The student is enrolled with all lessons completed except the quiz, and a graded quiz attempt is included. This demonstrates the full student journey from enrollment through completion.

### Generating Postman Collections

After seeding, you can generate Postman collections that include actual data IDs from your database. This enables testing with realistic data rather than placeholder values.

Execute python scripts/generate_postman_collection.py to generate the base collection from the OpenAPI specification. This creates postman/LMS Backend.postman_collection.json and postman/LMS Backend.postman_environment.json.

Execute python scripts/generate_demo_postman.py --seed-file postman/demo_seed_snapshot.json to generate the demo collection with actual seeded data IDs. This creates postman/LMS Backend Demo.postman_collection.json and postman/LMS Backend Demo.postman_environment.json with authenticated sessions for each demo user role.

Import these JSON files into Postman to get a fully functional API testing environment. The demo collection includes pre-configured requests for common workflows like user login, course enrollment, lesson completion, and quiz submission.

---

## Testing the Application

The project includes a comprehensive test suite covering unit tests, integration tests, and performance tests. Running tests ensures code quality and helps prevent regressions.

### Running Unit and Integration Tests

Execute pytest -q to run all tests with concise output. The test suite uses pytest with several plugins including pytest-asyncio for async tests, pytest-cov for coverage reporting, and Faker for generating test data.

By default, tests use SQLite in-memory database for speed. Tests that require PostgreSQL-specific features (like specific JSON handling) are marked and can be run separately against a PostgreSQL instance.

The test configuration in conftest.py provides fixtures for common testing scenarios. The db_session fixture provides a clean database session for each test. The client fixture provides a FastAPI test client. Fixtures for admin_user, instructor_user, and student_user create test users with appropriate roles.

### Coverage Requirements

The CI pipeline enforces a minimum code coverage of 75%. To run tests with coverage reporting, execute pytest -q --cov=app --cov-report=term-missing --cov-fail-under=75.

This command runs tests, reports coverage statistics, and fails the command if coverage falls below the threshold. The coverage report shows which lines are not covered by tests, helping identify areas needing additional test coverage.

For local development, you may run tests without the coverage gate while working on new features. Before submitting code, ensure coverage meets the threshold to avoid CI failures.

### Performance Testing

The project includes k6-based load tests for performance validation. These tests simulate realistic user traffic to identify bottlenecks and verify system performance under load.

Run the smoke test with run_load_test.bat (Windows) or the equivalent shell script. The smoke test verifies basic endpoint availability with a small number of virtual users over a short duration.

Run the realistic test with run_load_test_realistic.bat to simulate full user journeys including authentication, course browsing, lesson viewing, and quiz completion. This test runs longer with more virtual users to stress test the system.

The realistic test accepts parameters for URL, duration, host, and user counts. Adjust these parameters based on your hardware capabilities. Start with fewer users and increase gradually to find your system's capacity.

---

## Production Deployment

Production deployment requires additional configuration for security, reliability, and scalability. The following sections guide you through preparing for and executing production deployment.

### Production Configuration

Create a production .env file based on the example but with production-appropriate values. Critical production settings differ significantly from development defaults.

Set ENVIRONMENT=production to enable production-specific behaviors including disabling API docs, enforcing strict router imports, and requiring stronger security settings. Set DEBUG=false to disable debug mode which exposes sensitive information in error responses.

Configure a strong SECRET_KEY of at least 64 characters generated using a cryptographically secure random generator. This key should be stored in a secrets management system rather than the .env file. The application supports Azure Key Vault and HashiCorp Vault for secrets retrieval.

Set DATABASE_URL to point to your production PostgreSQL instance. For managed PostgreSQL services, use the provided connection string. Ensure the database accepts connections from your application servers with appropriate SSL configuration.

Configure RATE_LIMIT_USE_REDIS=true to use Redis-backed rate limiting in production. This provides distributed rate limiting across multiple API instances and persists limits across restarts.

Set TASKS_FORCE_INLINE=false to enable Celery worker processing for background tasks. In development, tasks run inline for simpler debugging. Production requires async task processing for scalability.

Configure SENTRY_DSN, SENTRY_ENVIRONMENT, and SENTRY_TRACES_SAMPLE_RATE for error tracking. Set the traces sample rate to around 0.1 (10%) to capture performance data without excessive overhead.

### Docker Production Stack

The docker-compose.prod.yml file defines the production stack with multiple containers providing redundancy and scalability. The stack includes the following services running in production mode.

The migrate service runs database migrations during deployment and exits. It waits for the database to be available, applies pending migrations, and completes. This ensures schema is up to date before the API starts.

The api service runs the FastAPI application with multiple workers (configured via UVICORN_WORKERS environment variable, default 2). It runs as a non-root user (nobody) for security. Health checks verify the application is responding correctly.

The celery-worker service processes background tasks from multiple queues: emails, progress, certificates, and webhooks. Multiple worker instances can be scaled horizontally for higher throughput.

The celery-beat service runs scheduled tasks including periodic cleanup and notification jobs. This service is typically run as a single instance.

The caddy service provides reverse proxy with automatic HTTPS via Let's Encrypt. It terminates TLS, adds security headers, and forwards requests to the API service. The service includes health checks that depend on the API being healthy.

The redis service provides caching and Celery message broker. Use a managed Redis service for production with high availability configuration.

### Deployment Process

Deploy the production stack using Docker Compose with the production configuration file. The deployment process includes the following steps ensuring a safe and repeatable deployment.

First, ensure all configuration is complete in your .env file with production values. Review each setting and verify that secrets are properly configured. Use a secrets management system for sensitive values rather than plain text in .env.

Second, pull the latest version of the application image if using pre-built images. If building locally, run docker compose -f docker-compose.prod.yml build to create production images with optimized settings.

Third, run database migrations before starting the application. Execute docker compose -f docker-compose.prod.yml up migrate to run migrations in isolation. Review migration output to ensure success.

Fourth, start the production stack with docker compose -f docker-compose.prod.yml up -d. The -d flag runs containers in detached mode. Monitor logs with docker compose -f docker-compose.prod.yml logs -f to verify successful startup.

Fifth, verify deployment by checking the readiness endpoint. Execute curl https://your-domain/api/v1/ready to verify all dependencies are available. The response should show "status": "ok" with database and redis marked as "up".

### Azure VM Deployment

For deployment to Azure Virtual Machines, use the provided GitHub Actions workflow or deployment scripts. The workflow automates provisioning, configuration, and application deployment.

The Azure VM deployment requires Azure subscription with contributor access. Configure Azure credentials as GitHub secrets. Set environment variables for VM size, location, and application configuration.

The deployment script (scripts/deploy_azure_vm.ps1) handles Azure VM provisioning, Docker installation, Docker Compose setup, and application deployment. It can be run manually or triggered by the GitHub Actions workflow on main branch pushes.

---

## Staging Environment

The staging environment provides a production-like environment for testing changes before production deployment. It uses the same architecture as production but with smaller resources and test data.

### Staging Configuration

The docker-compose.staging.yml file defines the staging stack. Configuration values are similar to production but with staging-specific settings. Debug mode may be enabled in staging to facilitate troubleshooting.

Create a staging .env file with staging-appropriate values. Use separate staging database and Redis instances. Configure SENTRY_ENVIRONMENT=staging to distinguish staging errors in Sentry.

### Deploying to Staging

Deploy staging using docker compose -f docker-compose.staging.yml up --build. The process is identical to production deployment but uses the staging configuration file.

After deployment, verify staging is working by checking the readiness endpoint. Run through your standard test scenarios in staging before deploying to production.

---

## Observability Stack

The observability stack provides monitoring, alerting, and visualization capabilities for production operations. The docker-compose.observability.yml file defines this stack.

### Starting Observability

Execute docker compose -f docker-compose.observability.yml up -d to start Prometheus, Grafana, and Alertmanager. Access Grafana at http://localhost:3000 with default credentials admin/admin.

Configure Prometheus to scrape your application metrics by ensuring the API service is accessible at the configured scrape endpoint. The provided prometheus.yml includes the API service target.

### Metrics Endpoint

The application exposes Prometheus metrics at the /metrics endpoint (configurable via METRICS_PATH). Metrics include request counts by endpoint and status, response time histograms, and custom application metrics for business events.

To view metrics in Prometheus, navigate to http://localhost:9090 and query using PromQL. For visualizations, import Grafana dashboards from the ops/observability directory.

---

## Troubleshooting Common Issues

This section addresses common issues encountered during setup and operation, with solutions for each.

### Database Connection Issues

If the application cannot connect to PostgreSQL, verify the database is running and the DATABASE_URL is correct. Check that PostgreSQL is accepting connections from your application host. For Docker, ensure both services are on the same Docker network.

Common DATABASE_URL format issues include using localhost in Docker when referring to another container (use the service name instead), missing the psycopg2 driver prefix, and incorrect credentials. Verify credentials match your PostgreSQL user and password settings.

### Redis Connection Issues

If Redis connection fails, verify Redis is running and accessible. Check that REDIS_URL uses the correct host and port. For Docker, ensure services are on the same network.

Rate limiting may fall back to in-memory mode if Redis is unavailable. Check logs for "fallback to in-memory mode" messages. This is acceptable for development but indicates a problem in production.

### Migration Failures

If migrations fail, ensure the database exists and is accessible. Check that migration scripts are compatible with your database version. For migration conflicts (multiple heads), use alembic heads to identify conflicts and alembic merge to resolve them.

For complex migration issues, you can reset the database in development by dropping all tables and re-running alembic upgrade head. This is only appropriate in development, not production.

### Port Conflicts

If ports are already in use, either stop the conflicting service or change the application's port. The default port is 8000. Modify the --port parameter in your startup command or the PORT environment variable in Docker Compose.

Common port conflicts include other development servers, IDE debug servers, and system services. Use netstat (Windows) or lsof (Linux/macOS) to identify processes using specific ports.

### Import Errors

If you encounter ImportError for project modules, ensure you are running Python from the project root directory. The project structure requires the app module to be importable. You may need to add the project root to PYTHONPATH.

For Docker-based development, this is handled automatically. For local development, ensure your virtual environment is activated and you are in the project root when running Python commands.

---

## Quick Reference Commands

This section provides a quick reference for common commands used in project development and deployment.

Local development startup: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000. Docker development startup: docker compose up --build. Production deployment: docker compose -f docker-compose.prod.yml up -d.

Run migrations: alembic upgrade head. Create migration: alembic revision --autogenerate -m "description". Run tests: pytest -q --cov=app --cov-fail-under=75.

Create admin user: python scripts/create_admin.py. Seed demo data: python scripts/seed_demo_data.py. Generate Postman: python scripts/generate_postman_collection.py.

Backup database: docker compose exec -T postgres-local pg_dump -U lms lms > backups/db/backup.dump. Restore database: cat backups/db/backup.dump | docker compose exec -T postgres-local psql -U lms lms.

---

This comprehensive guide covers all aspects of building and running the LMS Backend project. For more detailed information about specific topics, refer to the specialized documentation files in the docs/tech/ directory or examine the source code comments and inline documentation.
