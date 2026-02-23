# Comprehensive Scripts Reference Documentation

This document provides exhaustive documentation for every script in the LMS Backend project. Each script is described in terms of its purpose, functionality, usage instructions, command-line arguments, and integration points with other system components. This reference serves as the definitive guide for developers and operators working with the project's automation tools.

---

## Script Organization

The scripts directory contains several categories of automation tools designed for different operational purposes. Understanding the categorization helps in locating the appropriate script for any given task.

**Database Management Scripts** handle backup, restore, and migration operations. These scripts ensure data safety and enable disaster recovery procedures. They are critical for operational continuity and should be scheduled and tested regularly.

**User Management Scripts** facilitate the creation and management of user accounts across different roles. These scripts provide administrative functionality for bootstrapping new environments and managing user lifecycles.

**Development Scripts** support the development workflow including project startup, testing, and data seeding. These scripts streamline common development tasks and ensure consistent environments.

**Deployment Scripts** handle application deployment to various environments including local, staging, and production. They automate complex deployment procedures and ensure consistency across deployments.

**Postman Collection Scripts** generate API documentation and testing artifacts from the live application. These scripts maintain synchronization between the API implementation and testing collections.

**Testing Scripts** execute various testing procedures including load testing and integration testing. They validate system behavior under different conditions and help ensure quality.

---

## Database Management Scripts

### backup_db.bat

**Purpose**: Creates PostgreSQL database backups for disaster recovery and data preservation.

**Location**: scripts/backup_db.bat

**Description**: This Windows batch script uses pg_dump to create a complete backup of the PostgreSQL database. The backup includes all table data, schema definitions, indexes, and constraints. Backups are stored in the backups/db/ directory with timestamped filenames following the format lms_YYYYMMDD_HHMMSS.dump.

The script first ensures the backups directory exists, creating it if necessary. It then executes pg_dump with appropriate flags for a complete backup including schema and data. The output is compressed where possible and written to the timestamped file.

**Usage**:
```batch
backup_db.bat
```

**Output**: Creates backup file at backups/db/lms_YYYYMMDD_HHMMSS.dump

**Prerequisites**: PostgreSQL client tools must be installed and accessible in PATH. The database must be running and accessible with the configured credentials.

**Scheduling**: This script can be scheduled using Windows Task Scheduler for automated daily backups. Use the setup_backup_task.ps1 script to configure automated scheduling.

**Retention**: Implement a separate retention policy to delete old backup files. Recommended retention is 30 days for daily backups with longer retention for weekly full backups.

---

### restore_db.bat

**Purpose**: Restores PostgreSQL database from a previously created backup file.

**Location**: scripts/restore_db.bat

**Description**: This Windows batch script restores the database from a pg_dump backup file. It provides interactive confirmation before proceeding with the restore operation to prevent accidental data loss.

The script accepts the backup file path as an argument. If no path is provided, it prompts for the filename interactively. The --yes flag can be used to skip confirmation for automated restore procedures.

**Usage**:
```batch
restore_db.bat backups\db\lms_20240115_100000.dump
restore_db.bat backups\db\lms_20240115_100000.dump --yes
```

**Arguments**:
- First argument: Path to the backup file (required)
- --yes: Skip confirmation prompt (optional)

**Prerequisites**: PostgreSQL client tools must be installed. The database server must be running. The target database must exist or the user must have permission to create it.

**Warning**: Restore operations overwrite existing data. Ensure you have a current backup of any existing data before proceeding. Consider using pg_restore with --no-data flag for schema-only restore if you want to preserve existing data.

---

### setup_backup_task.ps1

**Purpose**: Creates a Windows Task Scheduler task for automated daily database backups.

**Location**: scripts/setup_backup_task.ps1

**Description**: This PowerShell script creates a scheduled task that runs the backup_db.bat script at a configured time daily. It uses Windows Task Scheduler for reliable execution independent of user sessions.

The script accepts parameters for task name, execution time, and optional configuration. It creates a task that runs whether the user is logged in or not, ensuring backups continue even without an active session.

**Usage**:
```powershell
.\scripts\setup_backup_task.ps1 -TaskName LMS-DB-Backup -Time 02:00
```

**Parameters**:
- TaskName: Name for the scheduled task (default: LMS-DB-Backup)
- Time: Execution time in HH:MM format (default: 02:00)
- Credential: Optional credential for task execution

**Example with custom settings**:
```powershell
.\scripts\setup_backup_task.ps1 -TaskName "LMS Nightly Backup" -Time "03:30"
```

**Verification**: After creation, verify the task exists using Get-ScheduledTask or by viewing Task Scheduler. Check that the task runs successfully by examining the task history.

---

### setup_restore_drill_task.ps1

**Purpose**: Creates a Windows Task Scheduler task for weekly restore drill procedures.

**Location**: scripts/setup_restore_drill_task.ps1

**Description**: This PowerShell script creates a scheduled task that performs weekly restore drills to validate backup integrity. The restore drill is a critical operational procedure that ensures backups are valid and recovery procedures work correctly.

The script configures the task to run on a specified day and time, typically weekly during low-traffic periods. It uses the run_restore_drill.ps1 script to perform the actual restore operation.

**Usage**:
```powershell
.\scripts\setup_restore_drill_task.ps1 -TaskName LMS-DB-Restore-Drill -Time 03:30 -DaysOfWeek Sunday
```

**Parameters**:
- TaskName: Name for the scheduled task (default: LMS-DB-Restore-Drill)
- Time: Execution time in HH:MM format (default: 03:30)
- DaysOfWeek: Day of week for execution (default: Sunday)
- ComposeFile: Docker compose file to use (default: docker-compose.prod.yml)

**Importance**: Regular restore drills are essential for disaster recovery preparedness. Without testing, backup files may be corrupted or recovery procedures may not work when needed.

---

### remove_backup_task.ps1

**Purpose**: Removes the scheduled backup task created by setup_backup_task.ps1.

**Location**: scripts/remove_backup_task.ps1

**Description**: This PowerShell script removes the scheduled task for database backups. It cleans up the Task Scheduler entry and associated configuration.

**Usage**:
```powershell
.\scripts\remove_backup_task.ps1 -TaskName LMS-DB-Backup
```

---

### remove_restore_drill_task.ps1

**Purpose**: Removes the scheduled restore drill task.

**Location**: scripts/remove_restore_drill_task.ps1

**Description**: This PowerShell script removes the scheduled restore drill task.

**Usage**:
```powershell
.\scripts\remove_restore_drill_task.ps1 -TaskName LMS-DB-Restore-Drill
```

---

### run_restore_drill.ps1

**Purpose**: Executes a database restore drill to validate backup integrity.

**Location**: scripts/run_restore_drill.ps1

**Description**: This PowerShell script performs a complete restore drill procedure. It restores the database from the most recent backup to a test environment, verifies the restore was successful, and cleans up.

The drill creates a temporary database for testing, restores to that temporary database, verifies the restore by querying table counts, and then drops the temporary database. This procedure validates that backups are valid and can be restored without data loss.

**Usage**:
```powershell
.\scripts\run_restore_drill.ps1 -ComposeFile docker-compose.prod.yml
```

**Parameters**:
- ComposeFile: Docker compose file to use for the drill

**Verification**: After successful drill completion, review logs to confirm all verification queries passed. Document any issues found for investigation.

---

## User Management Scripts

### create_admin.py

**Purpose**: Creates an administrator user account for the LMS system.

**Location**: scripts/create_admin.py

**Description**: This Python script creates a new admin user with the administrator role. It is typically used during initial system setup to create the first administrative account with full system access.

The script generates a password hash using bcrypt and stores the user record in the database. It supports customization through environment variables or command-line arguments.

**Usage**:
```bash
python scripts/create_admin.py
python scripts/create_admin.py --email admin@example.com --password MySecurePassword --full-name "System Administrator"
```

**Environment Variables**:
- ADMIN_EMAIL: Email address for the admin user (default: admin@lms.local)
- ADMIN_PASSWORD: Password for the admin user (default: AdminPass123)
- ADMIN_FULL_NAME: Full name for the admin user (default: Demo Admin)

**Database Requirements**: The database must be running and accessible. The users table must exist (run migrations first).

**Security Considerations**: Change the default password immediately after first login. Use strong passwords following organizational password policies. Consider using a password manager for credential storage.

---

### create_instructor.py

**Purpose**: Creates an instructor user account for the LMS system.

**Location**: scripts/create_instructor.py

**Description**: This Python script creates a new instructor user with the instructor role. Instructors have permissions to create and manage courses, lessons, and quizzes. They can also grade assignments submitted by students.

The script supports updating existing instructor accounts, making it useful for resetting instructor credentials or updating their information.

**Usage**:
```bash
python scripts/create_instructor.py
python scripts/create_instructor.py --email instructor@example.com --password InstructorPass --full-name "John Instructor"
```

**Environment Variables**:
- INSTRUCTOR_EMAIL: Email address for the instructor (default: instructor@lms.local)
- INSTRUCTOR_PASSWORD: Password for the instructor (default: InstructorPass123)
- INSTRUCTOR_FULL_NAME: Full name for the instructor (default: Demo Instructor)
- INSTRUCTOR_UPDATE_EXISTING: Update existing user if found (default: false)

**Features**:
- Creates new instructor if email does not exist
- Updates existing instructor if --update-existing flag is set
- Preserves existing user data when updating

---

### create_user.py

**Purpose**: Creates a generic user account with any role.

**Location**: scripts/create_user.py

**Description**: This Python script provides maximum flexibility for user creation. It supports creating users of any role (admin, instructor, student) with full customization of all user attributes.

This is the most versatile user creation script, suitable for creating additional users beyond the default demo accounts or for bulk user creation scenarios.

**Usage**:
```bash
python scripts/create_user.py --email user@example.com --password SecurePass123 --full-name "User Name" --role student
python scripts/create_user.py --email admin2@example.com --password AdminPass --full-name "Second Admin" --role admin --update-existing
```

**Command-Line Arguments**:
- --email: Email address for the user (required)
- --password: Password for the user (required)
- --full-name: Full name for the user (required)
- --role: Role for the user - admin, instructor, or student (required)
- --update-existing: Update existing user if found (optional flag)

**Role Permissions**:
- admin: Full system access, user management, all analytics
- instructor: Course creation and management, student grading
- student: Course enrollment, lesson completion, quiz taking

---

## Development Scripts

### seed_demo_data.py

**Purpose**: Seeds the database with demo data for testing and demonstration purposes.

**Location**: scripts/seed_demo_data.py

**Description**: This comprehensive Python script creates a complete demo environment including multiple user types, a sample course with lessons, enrollments, quiz with questions and attempts, and certificate generation. This is essential for demonstrations, testing, and generating Postman collections.

The script performs several operations in sequence. It creates demo users (admin, instructor, student) if they do not exist. It creates a sample course "Python LMS Demo Course" with three lessons. It enrolls the student in the course. It marks non-quiz lessons as completed. It creates and submits a quiz attempt. Finally, it generates a certificate for course completion.

**Usage**:
```bash
python scripts/seed_demo_data.py
python scripts/seed_demo_data.py --create-tables --reset-passwords
python scripts/seed_demo_data.py --skip-attempt --json-output postman/demo_seed_snapshot.json
```

**Command-Line Arguments**:
- --create-tables: Create database tables before seeding (optional)
- --reset-passwords: Reset passwords for existing demo users (optional)
- --skip-attempt: Skip creating quiz attempt and certificate (optional)
- --json-output <path>: Write seed snapshot JSON to specified path (optional)

**Environment Configuration**: The script imports and uses application modules, requiring proper database configuration in the environment. Ensure DATABASE_URL is set correctly before running.

**Demo Credentials After Seeding**:
- Admin: admin@lms.local / AdminPass123
- Instructor: instructor@lms.local / InstructorPass123
- Student: student@lms.local / StudentPass123

**Postman Integration**: The JSON output feature generates a snapshot file containing all created IDs and credentials. Use this with generate_demo_postman.py to create demo Postman collections.

---

### wait_for_db.py

**Purpose**: Waits for database availability before proceeding with operations.

**Location**: scripts/wait_for_db.py

**Description**: This Python script implements a connection retry mechanism for database-dependent operations. It attempts to connect to PostgreSQL with exponential backoff, waiting up to a configurable timeout before failing.

The script is used in Docker container startup to ensure the database is ready before migrations or application startup. This prevents race conditions where the application starts before the database is available.

**Usage**:
```bash
python scripts/wait_for_db.py
python scripts/wait_for_db.py --timeout 180 --interval 2
```

**Command-Line Arguments**:
- --timeout: Maximum time to wait in seconds (default: 180)
- --interval: Time between retry attempts in seconds (default: 2)

**Exit Codes**: The script exits with code 0 on successful connection, 1 on timeout or connection failure.

---

### validate_environment.py

**Purpose**: Validates environment configuration and reports missing or invalid settings.

**Location**: scripts/validate_environment.py

**Description**: This Python script checks the environment configuration for required variables and valid values. It is used in CI/CD pipelines and deployment procedures to catch configuration issues early.

The script validates several categories of settings. Required settings include DATABASE_URL, SECRET_KEY, and REDIS_URL. Production-specific settings are validated when ENVIRONMENT=production. Security settings are checked for appropriate values.

**Usage**:
```bash
python scripts/validate_environment.py
```

**Output**: The script prints validation results for each checked setting. It returns exit code 0 if all validations pass, 1 if any validation fails.

**Checks Performed**:
- Database connection string format
- Redis connection string format
- JWT secret key length
- Debug mode setting for production
- Rate limiting configuration
- Email configuration completeness

---

### validate_env.sh

**Purpose**: Bash equivalent of validate_environment.py for Unix systems.

**Location**: scripts/validate_env.sh

**Description**: This shell script provides environment validation for Unix/Linux systems where Python may not be readily available or where shell-based validation is preferred.

**Usage**:
```bash
bash scripts/validate_env.sh
```

---

### test_smtp_connection.py

**Purpose**: Tests SMTP email configuration and connectivity.

**Location**: scripts/test_smtp_connection.py

**Description**: This Python script verifies email sending capability by connecting to the configured SMTP server and optionally sending a test email. It helps debug email configuration issues before deploying.

The script attempts to connect to the SMTP server using the configured settings. If a recipient email is provided, it sends a test email to verify end-to-end functionality.

**Usage**:
```bash
python scripts/test_smtp_connection.py
python scripts/test_smtp_connection.py --to your-email@example.com
```

**Command-Line Arguments**:
- --to: Recipient email address for test email (optional)

**Configuration**: The script reads SMTP configuration from environment variables. Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_USE_TLS appropriately.

**Troubleshooting**: If connection fails, verify SMTP server address and port. Check firewall rules if testing from a restricted network. For Gmail and other providers, ensure app-specific passwords are used if 2FA is enabled.

---

### test_firebase_integration.py

**Purpose**: Tests Firebase SDK initialization and token verification.

**Location**: scripts/test_firebase_integration.py

**Description**: This Python script validates Firebase configuration when Firebase authentication is enabled. It tests SDK initialization and verifies token verification functionality.

**Usage**:
```bash
python scripts/test_firebase_integration.py
```

**Configuration**: Set FIREBASE_ENABLED=true, FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, and FIREBASE_CLIENT_EMAIL in the environment.

---

## Deployment Scripts

### run_project.ps1

**Purpose**: Unified PowerShell script for starting the development environment.

**Location**: scripts/run_project.ps1

**Description**: This comprehensive PowerShell script provides a single interface for starting the development environment with various configuration options. It simplifies the common development workflow by combining multiple operations into one command.

The script handles Docker Compose startup, optional database migrations, optional user creation, optional demo data seeding, and optional log following. It provides a convenient way to start development without remembering multiple commands.

**Usage**:
```powershell
.\scripts\run_project.ps1
.\scripts\run_project.ps1 -NoBuild -NoMigrate -CreateAdmin -CreateInstructor -SeedDemoData -FollowLogs
```

**Parameters**:
- NoBuild: Skip Docker image building (use existing images)
- NoMigrate: Skip database migration execution
- CreateAdmin: Create admin user after startup
- CreateInstructor: Create instructor user after startup
- SeedDemoData: Seed demo data after startup
- FollowLogs: Stream container logs after startup

**Examples**:
```powershell
# Full startup with everything
.\scripts\run_project.ps1 -SeedDemoData -FollowLogs

# Quick restart without rebuilding
.\scripts\run_project.ps1 -NoBuild -NoMigrate -FollowLogs

# Initial setup with users
.\scripts\run_project.ps1 -CreateAdmin -CreateInstructor -SeedDemoData
```

---

### run_project.bat

**Purpose**: Batch script equivalent of run_project.ps1 for Windows cmd.

**Location**: scripts/run_project.bat

**Description**: This batch script provides the same functionality as run_project.ps1 for environments where PowerShell is not available or preferred. It wraps Docker Compose commands with the same options.

**Usage**:
```batch
scripts\run_project.bat
scripts\run_project.bat -SeedDemoData
```

---

### run_demo.bat

**Purpose**: Convenience script for starting the demo environment with seeded data.

**Location**: run_demo.bat

**Description**: This batch script located in the project root provides a quick way to start the development environment with demo data. It is a shortcut for running seed_demo_data.py after Docker startup.

**Usage**:
```batch
run_demo.bat
```

**Equivalent Command**:
```bash
docker compose up -d
python scripts/seed_demo_data.py --create-tables
```

---

### run_staging.bat

**Purpose**: Convenience script for starting the staging environment.

**Location**: run_staging.bat

**Description**: This batch script starts the staging environment using docker-compose.staging.yml. It provides a quick way to launch staging without remembering the full docker compose command.

**Usage**:
```batch
run_staging.bat
```

---

### run_observability.bat

**Purpose**: Convenience script for starting the observability stack.

**Location**: run_observability.bat

**Description**: This batch script starts the observability stack including Prometheus, Grafana, and Alertmanager. These services provide monitoring and alerting capabilities for the application.

**Usage**:
```batch
run_observability.bat
```

**Access**:
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

---

### deploy_azure_vm.ps1

**Purpose**: Deploys the application to Azure Virtual Machine.

**Location**: scripts/deploy_azure_vm.ps1

**Description**: This comprehensive PowerShell script automates the entire Azure VM deployment process. It handles VM provisioning, Docker installation, application configuration, and deployment. The script is typically triggered by the GitHub Actions workflow but can be run manually.

The deployment process includes several phases. Azure authentication and subscription verification come first. VM provisioning with specified size and location follows. Docker and Docker Compose installation on the VM comes next. Application configuration via environment variables is applied. Docker Compose stack deployment completes the process. Finally, health verification ensures successful deployment.

**Usage**:
```powershell
.\scripts\deploy_azure_vm.ps1 -ResourceGroupName lms-rg -VmName lms-vm -Location eastus
```

**Parameters**:
- ResourceGroupName: Azure resource group name
- VMName: Name for the virtual machine
- Location: Azure region for deployment
- VmSize: VM size (default: Standard_D2s_v3)
- AdminUsername: VM admin username (default: azureuser)

**Prerequisites**: Azure subscription with contributor access, Azure CLI installed and authenticated.

---

### deploy_azure_vm.sh

**Purpose**: Bash equivalent of deploy_azure_vm.ps1 for Unix systems.

**Location**: scripts/deploy_azure_vm.sh

**Description**: This shell script provides the same Azure VM deployment functionality for Unix/Linux environments. It uses Azure CLI commands to provision and configure the VM.

**Usage**:
```bash
bash scripts/deploy_azure_vm.sh -r lms-rg -n lms-vm -l eastus
```

---

## Testing Scripts

### run_load_test.bat

**Purpose**: Runs k6 smoke load test against the application.

**Location**: run_load_test.bat

**Description**: This batch script executes a k6 load test to verify basic endpoint availability and performance under light load. The smoke test is designed to run quickly and verify the system is functioning correctly.

**Usage**:
```batch
run_load_test.bat
run_load_test.bat http://localhost:8000 20 60s localhost true
```

**Parameters**:
- First argument: Base URL for testing (default: http://localhost:8000)
- Second argument: Virtual users (default: 20)
- Third argument: Duration (default: 60s)
- Fourth argument: Host header (default: localhost)
- Fifth argument: Authenticated test (default: true)

**Test Location**: The test script is located at tests/perf/k6_smoke.js

---

### run_load_test_realistic.bat

**Purpose**: Runs k6 realistic load test simulating full user journeys.

**Location**: run_load_test_realistic.bat

**Description**: This batch script executes a comprehensive load test that simulates realistic user behavior. Users authenticate, browse courses, view lessons, and take quizzes. This test provides more accurate performance data than simple endpoint testing.

**Usage**:
```batch
run_load_test_realistic.bat
run_load_test_realistic.bat http://localhost:8001 10m localhost 8 3 1
```

**Parameters**:
- First argument: Base URL (default: http://localhost:8000)
- Second argument: Duration (default: 10m)
- Third argument: Host header (default: localhost)
- Fourth argument: Admin users (default: 8)
- Fifth argument: Instructor users (default: 3)
- Sixth argument: Student users (default: 1)

**Test Location**: The test script is located at tests/perf/k6_realistic.js

---

## Postman Collection Scripts

### generate_postman_collection.py

**Purpose**: Generates Postman collection from OpenAPI specification.

**Location**: scripts/generate_postman_collection.py

**Description**: This Python script queries the running application's OpenAPI endpoint and generates Postman collection and environment JSON files. These files can be imported into Postman for API testing.

The script fetches the OpenAPI schema from /openapi.json, generates a Postman collection structure, and creates environment templates with variables for URLs and authentication tokens.

**Usage**:
```bash
python scripts/generate_postman_collection.py
```

**Output Files**:
- postman/LMS Backend.postman_collection.json
- postman/LMS Backend.postman_environment.json

**Prerequisites**: The application must be running to fetch the OpenAPI specification.

---

### generate_demo_postman.py

**Purpose**: Generates demo Postman collection with seeded data.

**Location**: scripts/generate_demo_postman.py

**Description**: This Python script generates Postman collections pre-populated with actual IDs from the seeded database. This provides more realistic testing scenarios with real enrollment IDs, course IDs, and user credentials.

The script reads the seed snapshot JSON file, extracts IDs and credentials, and generates a Postman collection with pre-configured variables and authenticated sessions for each role.

**Usage**:
```bash
python scripts/generate_demo_postman.py --seed-file postman/demo_seed_snapshot.json
```

**Command-Line Arguments**:
- --seed-file: Path to seed snapshot JSON (required)

**Output Files**:
- postman/LMS Backend Demo.postman_collection.json
- postman/LMS Backend Demo.postman_environment.json

---

### generate_full_api_documentation.py

**Purpose**: Generates comprehensive API documentation from OpenAPI.

**Location**: scripts/generate_full_api_documentation.py

**Description**: This Python script generates a complete Markdown API reference document from the live OpenAPI specification. The generated documentation includes all endpoints, request/response schemas, and authentication requirements.

**Usage**:
```bash
python scripts/generate_full_api_documentation.py
```

**Output**: Creates docs/09-full-api-reference.md

---

## Root Level Convenience Scripts

Several convenience scripts are located at the project root for quick access.

### restore_drill.bat

**Purpose**: Executes database restore drill.

**Location**: restore_drill.bat

**Description**: Shortcut for running the restore drill script with Docker Compose production configuration.

**Usage**:
```batch
restore_drill.bat -ComposeFile docker-compose.prod.yml
```

---

## Script Dependencies

Understanding script dependencies helps with troubleshooting and development.

**Python Version**: All Python scripts require Python 3.11 or higher. Ensure python command points to correct version.

**Environment Variables**: Most scripts require proper environment configuration. Copy .env.example to .env and configure appropriate values.

**Database Connection**: Scripts that interact with the database require DATABASE_URL to be set correctly.

**Docker**: Deployment and convenience scripts require Docker and Docker Compose to be installed and running.

**PostgreSQL Client**: Backup and restore scripts require PostgreSQL client tools (pg_dump, psql) in PATH.

---

## Common Workflows

This section documents common workflow patterns using the scripts.

**Initial Development Setup**:
1. Copy environment: cp .env.example .env
2. Start services: .\scripts\run_project.ps1 -FollowLogs
3. Create admin: .\scripts\run_project.ps1 -CreateAdmin
4. Seed demo: .\scripts\run_project.ps1 -SeedDemoData

**Production Deployment**:
1. Configure .env with production values
2. Run migrations: docker compose -f docker-compose.prod.yml up migrate
3. Deploy: docker compose -f docker-compose.prod.yml up -d
4. Verify: curl https://domain/api/v1/ready

**Backup and Restore**:
1. Backup: .\scripts\backup_db.bat
2. Verify backup created
3. Restore: .\scripts\restore_db.bat backups\db\filename.dump

---

This comprehensive scripts reference provides complete documentation for all automation tools in the LMS Backend project. Each script is designed for specific operational tasks and can be used independently or combined into complex workflows. For additional information about any script, examine the source code which includes inline comments explaining the implementation details.
