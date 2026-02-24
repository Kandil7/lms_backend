# Scripts Reference

This document covers all scripts in the `scripts/` directory.

## Directory Structure

```
scripts/
├── database/
│   ├── seed_demo_data.py      # Seed demo data
│   └── wait_for_db.py         # Wait for database
├── deployment/
│   ├── deploy_azure_demo_vm.ps1
│   ├── deploy_azure_vm.ps1
│   └── validate_environment.py
├── docs/
│   ├── generate_demo_postman.py
│   ├── generate_full_api_documentation.py
│   └── generate_postman_collection.py
├── local/
│   ├── deploy_production.bat
│   ├── deploy_production.sh
│   ├── execute_comprehensive_tests.py
│   ├── final_comprehensive_test.py
│   ├── health_check.py
│   ├── run_comprehensive_tests.py
│   ├── run_comprehensive_tests.bat
│   ├── start_lms_complete.ps1
│   ├── start_lms_full.bat
│   ├── start_lms_full.ps1
│   ├── test_backend.ps1
│   └── verify_integration.py
├── maintenance/
│   ├── remove_backup_task.ps1
│   ├── remove_restore_drill_task.ps1
│   ├── run_restore_drill.ps1
│   ├── setup_backup_task.ps1
│   └── setup_restore_drill_task.ps1
├── platform/
│   ├── linux/
│   │   ├── deploy_azure_demo_vm.sh
│   │   ├── deploy_azure_vm.sh
│   │   └── validate_env.sh
│   └── windows/
│       ├── backup_db.bat
│       ├── restore_db.bat
│       ├── run_demo.bat
│       ├── run_demo_proxy_duckdns.bat
│       ├── run_demo_side_by_side.bat
│       ├── run_load_test.bat
│       ├── run_load_test_realistic.bat
│       ├── run_observability.bat
│       ├── run_staging.bat
│       ├── start_lms_full.bat
│       └── stop_demo_proxy_duckdns.bat
├── testing/
│   ├── test_firebase_integration.py
│   └── test_smtp_connection.py
├── user_management/
│   ├── create_admin.py
│   ├── create_instructor.py
│   └── create_user.py
└── generate_module_migration.py
```

---

## Database Scripts

### seed_demo_data.py

**Purpose**: Populate database with demo data for testing.

**Location**: `scripts/database/seed_demo_data.py`

**Usage**:
```bash
python scripts/database/seed_demo_data.py
```

**Functionality**:
- Creates demo users (admin, instructors, students)
- Creates demo courses with lessons
- Creates demo enrollments
- Creates demo assignments and submissions

**Environment Variables**:
```
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db
```

### wait_for_db.py

**Purpose**: Wait for database to be ready before starting application.

**Location**: `scripts/database/wait_for_db.py`

**Usage**:
```bash
python scripts/database/wait_for_db.py
```

**Functionality**:
- Attempts database connection
- Retries with exponential backoff
- Exits with code 0 when ready

---

## Deployment Scripts

### deploy_azure_vm.ps1

**Purpose**: Deploy application to Azure VM.

**Location**: `scripts/deployment/deploy_azure_vm.ps1`

**Usage**:
```powershell
.\deploy_azure_vm.ps1 -ResourceGroup "rg-lms" -VMName "lms-vm"
```

**Functionality**:
1. Build Docker image
2. Push to Azure Container Registry
3. Deploy to Azure VM via SSH
4. Start containers with docker-compose

### deploy_azure_demo_vm.ps1

**Purpose**: Deploy demo environment to Azure.

**Location**: `scripts/deployment/deploy_azure_demo_vm.ps1`

**Usage**:
```powershell
.\deploy_azure_demo_vm.ps1
```

### validate_environment.py

**Purpose**: Validate environment configuration.

**Location**: `scripts/deployment/validate_environment.py`

**Usage**:
```bash
python scripts/deployment/validate_environment.py
```

**Checks**:
- Required environment variables
- Database connectivity
- Redis connectivity
- Azure credentials (if using Azure)

---

## Local Development Scripts

### start_lms_full.ps1

**Purpose**: Start full LMS stack locally.

**Location**: `scripts/local/start_lms_full.ps1`

**Usage**:
```powershell
.\start_lms_full.ps1
```

**Starts PostgreSQL (Docker**:
-)
- Redis (Docker)
- API (uvicorn)
- Celery worker
- Celery beat

### start_lms_complete.ps1

**Purpose**: Complete startup with all services.

**Location**: `scripts/local/start_lms_complete.ps1`

**Usage**:
```powershell
.\start_lms_complete.ps1
```

### start_lms_full.bat

**Purpose**: Windows batch version for full startup.

**Location**: `scripts/local/start_lms_full.bat`

**Usage**:
```cmd
start_lms_full.bat
```

### deploy_production.sh

**Purpose**: Deploy to production environment.

**Location**: `scripts/local/deploy_production.sh`

**Usage**:
```bash
./scripts/local/deploy_production.sh
```

### deploy_production.bat

**Purpose**: Windows deployment script.

**Location**: `scripts/local/deploy_production.bat`

**Usage**:
```cmd
deploy_production.bat
```

---

## Testing Scripts

### execute_comprehensive_tests.py

**Purpose**: Run comprehensive test suite.

**Location**: `scripts/local/execute_comprehensive_tests.py`

**Usage**:
```bash
python scripts/local/execute_comprehensive_tests.py
```

**Runs**:
- Unit tests
- Integration tests
- Endpoint validation
- Performance tests

### final_comprehensive_test.py

**Purpose**: Final comprehensive test before release.

**Location**: `scripts/local/final_comprehensive_test.py`

**Usage**:
```bash
python scripts/local/final_comprehensive_test.py
```

### run_comprehensive_tests.py

**Purpose**: Run all tests with reporting.

**Location**: `scripts/local/run_comprehensive_tests.py`

**Usage**:
```bash
python scripts/local/run_comprehensive_tests.py --coverage
```

### run_comprehensive_tests.bat

**Purpose**: Windows batch for running tests.

**Location**: `scripts/local/run_comprehensive_tests.bat`

**Usage**:
```cmd
run_comprehensive_tests.bat
```

### test_backend.ps1

**Purpose**: Quick backend test script.

**Location**: `scripts/local/test_backend.ps1`

**Usage**:
```powershell
.\test_backend.ps1
```

### health_check.py

**Purpose**: Check application health.

**Location**: `scripts/local/health_check.py`

**Usage**:
```bash
python scripts/local/health_check.py --url http://localhost:8000
```

**Checks**:
- API health endpoint
- Database connectivity
- Redis connectivity

### verify_integration.py

**Purpose**: Verify integration between services.

**Location**: `scripts/local/verify_integration.py`

**Usage**:
```bash
python scripts/local/verify_integration.py
```

---

## Platform-Specific Scripts

### Windows Scripts

**Location**: `scripts/platform/windows/`

| Script | Purpose |
|--------|---------|
| `start_lms_full.bat` | Start full LMS stack |
| `run_demo.bat` | Run demo environment |
| `run_staging.bat` | Run staging environment |
| `run_observability.bat` | Run with observability |
| `run_load_test.bat` | Run load tests |
| `run_load_test_realistic.bat` | Realistic load tests |
| `run_demo_side_by_side.bat` | Demo with side-by-side |
| `run_demo_proxy_duckdns.bat` | Demo with DuckDNS proxy |
| `stop_demo_proxy_duckdns.bat` | Stop DuckDNS demo |
| `backup_db.bat` | Backup database |
| `restore_db.bat` | Restore database |

#### backup_db.bat

**Usage**:
```cmd
backup_db.bat
```

**Creates**:
- SQL dump of PostgreSQL database
- Timestamped backup file

#### restore_db.bat

**Usage**:
```cmd
restore_db.bat backup_file.sql
```

### Linux Scripts

**Location**: `scripts/platform/linux/`

| Script | Purpose |
|--------|---------|
| `deploy_azure_vm.sh` | Deploy to Azure VM |
| `deploy_azure_demo_vm.sh` | Deploy demo |
| `validate_env.sh` | Validate environment |

---

## Maintenance Scripts

### setup_backup_task.ps1

**Purpose**: Setup automated database backups.

**Location**: `scripts/maintenance/setup_backup_task.ps1`

**Usage**:
```powershell
.\setup_backup_task.ps1 -Schedule "Daily" -Time "02:00"
```

### setup_restore_drill_task.ps1

**Purpose**: Setup restore drill schedule.

**Location**: `scripts/maintenance/setup_restore_drill_task.ps1`

### run_restore_drill.ps1

**Purpose**: Test database restore from backup.

**Location**: `scripts/maintenance/run_restore_drill.ps1`

### remove_backup_task.ps1

**Purpose**: Remove automated backup task.

**Location**: `scripts/maintenance/remove_backup_task.ps1`

### remove_restore_drill_task.ps1

**Purpose**: Remove restore drill task.

**Location**: `scripts/maintenance/remove_restore_drill_task.ps1`

---

## Testing Utility Scripts

### test_smtp_connection.py

**Purpose**: Test SMTP email configuration.

**Location**: `scripts/testing/test_smtp_connection.py`

**Usage**:
```bash
python scripts/testing/test_smtp_connection.py --email test@example.com
```

**Tests**:
- SMTP connection
- Authentication
- Send test email

### test_firebase_integration.py

**Purpose**: Test Firebase configuration.

**Location**: `scripts/testing/test_firebase_integration.py`

**Usage**:
```bash
python scripts/testing/test_firebase_integration.py
```

**Tests**:
- Firebase project connection
- Authentication
- Cloud function invocation

---

## User Management Scripts

### create_user.py

**Purpose**: Create a new user.

**Location**: `scripts/user_management/create_user.py`

**Usage**:
```bash
python scripts/user_management/create_user.py \
    --email user@example.com \
    --name "John Doe" \
    --password securepass123 \
    --role student
```

**Arguments**:
| Argument | Description | Required |
|----------|-------------|-----------|
| `--email` | User email | Yes |
| `--name` | Full name | Yes |
| `--password` | Password | Yes |
| `--role` | Role (student/instructor/admin) | No (default: student) |

### create_instructor.py

**Purpose**: Create instructor user.

**Location**: `scripts/user_management/create_instructor.py`

**Usage**:
```bash
python scripts/user_management/create_instructor.py \
    --email instructor@example.com \
    --name "Jane Smith" \
    --password securepass123
```

### create_admin.py

**Purpose**: Create admin user.

**Location**: `scripts/user_management/create_admin.py`

**Usage**:
```bash
python scripts/user_management/create_admin.py \
    --email admin@example.com \
    --name "Admin User" \
    --password securepass123
```

---

## Documentation Generation Scripts

### generate_postman_collection.py

**Purpose**: Generate Postman collection from API.

**Location**: `scripts/docs/generate_postman_collection.py`

**Usage**:
```bash
python scripts/docs/generate_postman_collection.py --output postman_collection.json
```

### generate_full_api_documentation.py

**Purpose**: Generate comprehensive API docs.

**Location**: `scripts/docs/generate_full_api_documentation.py`

**Usage**:
```bash
python scripts/docs/generate_full_api_documentation.py --output docs/api.md
```

### generate_demo_postman.py

**Purpose**: Generate demo Postman collection.

**Location**: `scripts/docs/generate_demo_postman.py`

**Usage**:
```bash
python scripts/docs/generate_demo_postman.py --output demo.postman.json
```

---

## Migration Scripts

### generate_module_migration.py

**Purpose**: Generate Alembic migration for module.

**Location**: `scripts/generate_module_migration.py`

**Usage**:
```bash
python scripts/generate_module_migration.py --module courses
```

**Arguments**:
| Argument | Description |
|----------|-------------|
| `--module` | Module name to migrate |
| `--message` | Migration message |

---

## Environment Requirements

### Common Environment Variables

```bash
# Database
DATABASE_URL=postgresql+psycopg2://lms:lms@localhost:5432/lms

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Application
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-secret-key-here

# Email (optional)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=user
SMTP_PASSWORD=password
```

### Production Environment Variables

```bash
# Production-specific
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<strong-random-key>

# Azure
AZURE_STORAGE_CONNECTION_STRING=<connection-string>
AZURE_STORAGE_CONTAINER_NAME=lms-files

# Database
POSTGRES_PASSWORD=<secure-password>

# Secrets
SMTP_PASSWORD=<email-password>
SENTRY_DSN=<sentry-dsn>
```

---

## Common Usage Patterns

### Local Development

```bash
# 1. Start the stack
.\scripts\platform\windows\start_lms_full.bat

# 2. Wait for database
python scripts/database/wait_for_db.py

# 3. Create initial admin
python scripts/user_management/create_admin.py --email admin@example.com --password Admin123!

# 4. Seed demo data
python scripts/database/seed_demo_data.py

# 5. Run tests
python scripts/local/run_comprehensive_tests.py
```

### Deployment

```bash
# 1. Validate environment
python scripts/deployment/validate_environment.py

# 2. Deploy
.\scripts\deployment\deploy_azure_vm.ps1 -ResourceGroup "rg-lms"
```

### Testing

```bash
# Full test suite
python scripts/local/final_comprehensive_test.py

# Health check
python scripts/local/health_check.py

# Integration verification
python scripts/local/verify_integration.py
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Check if database is running
python scripts/database/wait_for_db.py

# Verify connection string
echo $DATABASE_URL
```

### Test Failures

```bash
# Run specific tests
pytest tests/ -v -k "test_name"

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Script Permission Issues (Linux)

```bash
# Make executable
chmod +x scripts/platform/linux/*.sh
```
