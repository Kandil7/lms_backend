# CI/CD, Scripts & Operations

## Complete Documentation for CI/CD Pipelines, Automation Scripts, and Operational Procedures

This document covers the CI/CD pipelines, automation scripts, backup procedures, and operational tools in the LMS backend project.

---

## Table of Contents

1. [GitHub Workflows (CI/CD)](#1-github-workflows-cicd)
2. [Database Scripts](#2-database-scripts)
3. [Backup & Restore](#3-backup--restore)
4. [Load Testing](#4-load-testing)
5. [Demo Data Generation](#5-demo-data-generation)
6. [Postman Collections](#6-postman-collections)
7. [Windows Automation Scripts](#7-windows-automation-scripts)
8. [Operational Procedures](#8-operational-procedures)

---

## 1. GitHub Workflows (CI/CD)

### CI Pipeline

```yaml
# .github/workflows/ci.yml
name: Continuous Integration

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_lms
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run linting
        run: |
          pip install flake8 black isort
          flake8 app/ --max-line-length=120 --ignore=E501,W503
          black --check app/
          isort --check-only app/
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test_lms
          REDIS_URL: redis://localhost:6379/0
          ENVIRONMENT: testing
        run: |
          pytest tests/ -v --cov=app --cov-fail-under=75 --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          flags: unittests
```

### Security Pipeline

```yaml
# .github/workflows/security.yml
name: Security Scanning

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  security:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Run pip-audit
        run: |
          pip install pip-audit
          pip-audit -r requirements.txt || true
      
      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r app/ -f json -o bandit-report.json || true
          bandit -r app/ || true
      
      - name: Run GitLeaks
        run: |
          pip install gitleaks
          gitleaks detect --source . --report-format json --report gitleaks-report.json || true
      
      - name: Upload security reports
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            bandit-report.json
            gitleaks-report.json
```

### Why These Pipelines?

| Pipeline | Purpose | Triggers |
|----------|---------|----------|
| CI | Run tests, check code quality | Every push/PR |
| Security | Vulnerability scanning | Push to main, weekly |

---

## 2. Database Scripts

### Create Admin User

```python
# scripts/create_admin.py
#!/usr/bin/env python
"""
Create admin user script.

Usage:
    python scripts/create_admin.py
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import async_session_maker
from app.core.security import hash_password
from app.modules.users.models import User
from uuid import uuid4
from datetime import datetime

async def create_admin():
    """Create default admin user"""
    
    email = input("Enter admin email [admin@example.com]: ") or "admin@example.com"
    password = input("Enter admin password: ")
    full_name = input("Enter admin full name [Admin]: ") or "Admin"
    
    if not password:
        print("Error: Password is required")
        return
    
    async with async_session_maker() as session:
        # Check if admin exists
        from sqlalchemy import select
        from app.modules.users.models import User
        
        result = await session.execute(
            select(User).where(User.email == email)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"User {email} already exists")
            return
        
        # Create admin
        admin = User(
            id=uuid4(),
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role="admin",
            is_active=True,
            email_verified_at=datetime.utcnow()
        )
        
        session.add(admin)
        await session.commit()
        
        print(f"Admin user created successfully!")
        print(f"Email: {email}")
        print(f"Role: admin")

if __name__ == "__main__":
    asyncio.run(create_admin())
```

### Seed Demo Data

```python
# scripts/seed_demo_data.py
#!/usr/bin/env python
"""
Seed database with demo data for testing and development.

Creates:
    - 3 users (admin, instructor, student)
    - 1 course with lessons
    - 1 quiz with questions
    - 1 enrollment with progress
    - 1 certificate
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import async_session_maker
from app.core.security import hash_password
from app.modules.users.models import User
from app.modules.courses.models.course import Course
from app.modules.courses.models.lesson import Lesson
from app.modules.quizzes.models.quiz import Quiz
from app.modules.quizzes.models.question import QuizQuestion
from app.modules.enrollments.models import Enrollment, LessonProgress
from app.modules.certificates.models import Certificate
from uuid import uuid4
from datetime import datetime, timedelta

async def seed_demo_data():
    """Seed database with demo data"""
    
    async with async_session_maker() as session:
        
        # Create users
        admin = User(
            id=uuid4(),
            email="admin@example.com",
            password_hash=hash_password("admin123"),
            full_name="Admin User",
            role="admin",
            is_active=True,
            email_verified_at=datetime.utcnow()
        )
        
        instructor = User(
            id=uuid4(),
            email="instructor@example.com",
            password_hash=hash_password("instructor123"),
            full_name="John Instructor",
            role="instructor",
            is_active=True,
            email_verified_at=datetime.utcnow()
        )
        
        student = User(
            id=uuid4(),
            email="student@example.com",
            password_hash=hash_password("student123"),
            full_name="Jane Student",
            role="student",
            is_active=True,
            email_verified_at=datetime.utcnow()
        )
        
        session.add_all([admin, instructor, student])
        await session.flush()
        
        # Create course
        course = Course(
            id=uuid4(),
            title="Python Programming Fundamentals",
            slug="python-fundamentals",
            description="Learn Python from scratch",
            instructor_id=instructor.id,
            category="programming",
            difficulty_level="beginner",
            is_published=True,
            estimated_duration_minutes=1200
        )
        
        session.add(course)
        await session.flush()
        
        # Create lessons
        lessons = [
            Lesson(
                id=uuid4(),
                course_id=course.id,
                title="Introduction to Python",
                slug="intro-python",
                description="Getting started with Python",
                lesson_type="video",
                order_index=1,
                duration_minutes=30,
                is_preview=True
            ),
            Lesson(
                id=uuid4(),
                course_id=course.id,
                title="Variables and Data Types",
                slug="variables-data-types",
                description="Learn about variables",
                lesson_type="text",
                order_index=2,
                duration_minutes=20
            ),
            Lesson(
                id=uuid4(),
                course_id=course.id,
                title="Python Basics Quiz",
                slug="python-basics-quiz",
                lesson_type="quiz",
                order_index=3,
                duration_minutes=15
            )
        ]
        
        session.add_all(lessons)
        await session.flush()
        
        # Create quiz
        quiz = Quiz(
            id=uuid4(),
            lesson_id=lessons[2].id,
            title="Python Basics Assessment",
            description="Test your knowledge",
            quiz_type="graded",
            passing_score=70.0,
            max_attempts=3,
            is_published=True
        )
        
        session.add(quiz)
        await session.flush()
        
        # Create questions
        questions = [
            QuizQuestion(
                id=uuid4(),
                quiz_id=quiz.id,
                question_text="What is Python?",
                question_type="multiple_choice",
                points=1.0,
                order_index=1,
                options=[
                    {"id": "a", "text": "A programming language"},
                    {"id": "b", "text": "A snake"},
                    {"id": "c", "text": "A framework"},
                ],
                correct_answer="a"
            ),
            QuizQuestion(
                id=uuid4(),
                quiz_id=quiz.id,
                question_text="Python is interpreted.",
                question_type="true_false",
                points=1.0,
                order_index=2,
                correct_answer="true"
            )
        ]
        
        session.add_all(questions)
        await session.flush()
        
        # Create enrollment
        enrollment = Enrollment(
            id=uuid4(),
            student_id=student.id,
            course_id=course.id,
            enrolled_at=datetime.utcnow() - timedelta(days=5),
            started_at=datetime.utcnow() - timedelta(days=5),
            status="active",
            progress_percentage=66.67,
            completed_lessons_count=2,
            total_lessons_count=3,
            total_time_spent_seconds=3600
        )
        
        session.add(enrollment)
        await session.flush()
        
        # Create lesson progress
        lesson_progress = [
            LessonProgress(
                id=uuid4(),
                enrollment_id=enrollment.id,
                lesson_id=lessons[0].id,
                status="completed",
                started_at=datetime.utcnow() - timedelta(days=5),
                completed_at=datetime.utcnow() - timedelta(days=4),
                time_spent_seconds=1800,
                completion_percentage=100
            ),
            LessonProgress(
                id=uuid4(),
                enrollment_id=enrollment.id,
                lesson_id=lessons[1].id,
                status="completed",
                started_at=datetime.utcnow() - timedelta(days=3),
                completed_at=datetime.utcnow() - timedelta(days=2),
                time_spent_seconds=1800,
                completion_percentage=100
            )
        ]
        
        session.add_all(lesson_progress)
        
        # Create certificate
        certificate = Certificate(
            id=uuid4(),
            enrollment_id=enrollment.id,
            student_id=student.id,
            course_id=course.id,
            certificate_number=f"CERT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}",
            pdf_path="certificates/demo-certificate.pdf",
            completion_date=datetime.utcnow() - timedelta(days=1),
            issued_at=datetime.utcnow() - timedelta(days=1)
        )
        
        session.add(certificate)
        
        await session.commit()
        
        print("=" * 50)
        print("Demo data seeded successfully!")
        print("=" * 50)
        print("\nUsers created:")
        print(f"  Admin: admin@example.com / admin123")
        print(f"  Instructor: instructor@example.com / instructor123")
        print(f"  Student: student@example.com / student123")
        print(f"\nCourse: {course.title}")
        print(f"Enrollment: {student.full_name} enrolled")
        print(f"Certificate: {certificate.certificate_number}")

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
```

---

## 3. Backup & Restore

### Backup Script

```batch
@echo off
REM scripts/backup_db.bat
REM Database backup script for Windows

setlocal

set DB_NAME=lms
set DB_USER=lms_user
set DB_HOST=localhost
set BACKUP_DIR=%~dp0..\backups
set DATE=%date:~-4%%date:~4,2%%date:~7,2%
set TIME=%time:~0,2%%time:~3,2%%time:~6,2%
set DATETIME=%DATE%_%TIME%

echo Starting database backup...

REM Create backup directory if not exists
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM Get password from environment or prompt
if "%POSTGRES_PASSWORD%"=="(
    set /p POSTGRES_PASSWORD="Enter database password: "
)

REM Run pg_dump
"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe" ^
    -h %DB_HOST% ^
    -U %DB_USER% ^
    -d %DB_NAME% ^
    -F c ^
    -b ^
    -v ^
    -f "%BACKUP_DIR%\lms_backup_%DATETIME%.dump"

if %errorlevel% equ 0 (
    echo Backup completed successfully!
    echo File: %BACKUP_DIR%\lms_backup_%DATETIME%.dump
    
    REM Keep only last 7 backups
    for /f "skip=7 delims=" %%i in ('dir /b /o-d "%BACKUP_DIR%\lms_backup_*.dump"') do (
        del "%%i"
    )
) else (
    echo Backup failed!
    exit /b 1
)

endlocal
```

### Restore Script

```batch
@echo off
REM scripts/restore_db.bat
REM Database restore script for Windows

setlocal

set DB_NAME=lms
set DB_USER=lms_user
set DB_HOST=localhost
set BACKUP_DIR=%~dp0..\backups

echo Database Restore Script
echo ========================
echo.

REM List available backups
echo Available backups:
dir /b "%BACKUP_DIR%\lms_backup_*.dump" 2>nul
echo.

set /p BACKUP_FILE="Enter backup filename: "

if not exist "%BACKUP_DIR%\%BACKUP_FILE%" (
    echo Error: File not found!
    exit /b 1
)

echo.
echo WARNING: This will overwrite the current database!
set /p CONFIRM="Are you sure? (yes/no): "

if not "%CONFIRM%"=="yes" (
    echo Restore cancelled.
    exit /b 0
)

if "%POSTGRES_PASSWORD%"=="(
    set /p POSTGRES_PASSWORD="Enter database password: "
)

echo Restoring database...

"C:\Program Files\PostgreSQL\16\bin\pg_restore.exe" ^
    -h %DB_HOST% ^
    -U %DB_USER% ^
    -d %DB_NAME% ^
    -c ^
    -v ^
    "%BACKUP_DIR%\%BACKUP_FILE%"

if %errorlevel% equ 0 (
    echo Restore completed successfully!
) else (
    echo Restore failed!
    exit /b 1
)

endlocal
```

---

## 4. Load Testing

### K6 Smoke Test

```javascript
// tests/perf/k6_smoke.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    vus: 1,
    duration: '1m',
    thresholds: {
        http_req_duration: ['p(95)<500'],
        http_req_failed: ['rate<0.01'],
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TOKEN = __ENV.TOKEN || '';

export default function () {
    // Health check
    const health = http.get(`${BASE_URL}/health`);
    check(health, {
        'health is 200': (r) => r.status === 200,
    });
    
    // List courses
    const courses = http.get(`${BASE_URL}/api/v1/courses`);
    check(courses, {
        'courses list works': (r) => r.status === 200,
    });
    
    // Get single course
    const course = http.get(`${BASE_URL}/api/v1/courses`);
    if (course.json('data') && course.json('data').length > 0) {
        const courseId = course.json('data')[0].id;
        const courseDetail = http.get(`${BASE_URL}/api/v1/courses/${courseId}`);
        check(courseDetail, {
            'course detail works': (r) => r.status === 200,
        });
    }
    
    sleep(1);
}
```

### K6 Realistic Load Test

```javascript
// tests/perf/k6_realistic.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const courseListDuration = new Trend('course_list_duration');

export const options = {
    stages: [
        { duration: '2m', target: 10 },   // Ramp up
        { duration: '5m', target: 10 },  // Steady
        { duration: '2m', target: 20 },  // Spike
        { duration: '5m', target: 20 },  // Steady high
        { duration: '2m', target: 0 },   // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<1000', 'p(99)<2000'],
        http_req_failed: ['rate<0.05'],
        errors: ['rate<0.05'],
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
    // Homepage / health
    const start = new Date();
    const health = http.get(`${BASE_URL}/health`);
    courseListDuration.add(new Date() - start);
    errorRate.add(health.status !== 200);
    
    // Browse courses
    const courses = http.get(`${BASE_URL}/api/v1/courses?page=1&page_size=12`);
    check(courses, {
        'courses loaded': (r) => r.status === 200,
    });
    errorRate.add(courses.status !== 200);
    
    // View course details
    if (courses.json('data') && courses.json('data').length > 0) {
        const course = courses.json('data')[Math.floor(Math.random() * courses.json('data').length)];
        const detail = http.get(`${BASE_URL}/api/v1/courses/${course.id}`);
        check(detail, {
            'course detail loaded': (r) => r.status === 200,
        });
        errorRate.add(detail.status !== 200);
    }
    
    // Random think time
    sleep(Math.random() * 3 + 1);
}
```

### Running Load Tests

```batch
@echo off
REM scripts/run_load_test.bat

echo Running Load Tests...
echo ====================

REM Install k6 if not present
where k6 >nul 2>&1
if %errorlevel% neq 0 (
    echo k6 not found. Installing...
    choco install k6 -y
)

REM Run smoke test
echo.
echo Running Smoke Test...
k6 run tests/perf/k6_smoke.js --out json=k6-smoke.json

echo.
echo Smoke test completed!

REM Run realistic test
echo.
echo Running Realistic Load Test...
k6 run tests/perf/k6_realistic.js --out json=k6-realistic.json

echo.
echo Load tests completed!
echo Results saved to k6-*.json
```

---

## 5. Demo Data Generation

### Generate Postman Collection

```python
# scripts/generate_postman_collection.py
#!/usr/bin/env python
"""
Generate Postman collection from API routes.

Reads the OpenAPI spec and generates a Postman collection.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from app.main import app

def generate_postman_collection():
    """Generate Postman collection from OpenAPI"""
    
    # Get OpenAPI spec
    from fastapi.openapi import get_openapi
    
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes
    )
    
    # Convert to Postman format
    collection = {
        "info": {
            "name": schema["info"]["title"],
            "description": schema["info"]["description"],
            "schema": "https://schema.getpostman.com/json/draft-v4/collection.json"
        },
        "item": []
    }
    
    # Group by tags
    items_by_tag = {}
    
    for path, methods in schema["paths"].items():
        for method, details in methods.items():
            if method not in ["parameters", "summary", "description"]:
                tags = details.get("tags", ["Other"])
                
                for tag in tags:
                    if tag not in items_by_tag:
                        items_by_tag[tag] = []
                    
                    item = {
                        "name": details.get("summary", path),
                        "request": {
                            "method": method.upper(),
                            "url": {
                                "raw": f"{{{{baseUrl}}}}{path}",
                                "host": ["{{baseUrl}}"],
                                "path": path.strip("/").split("/")
                            }
                        }
                    }
                    
                    # Add request body if present
                    if "requestBody" in details:
                        content = details["requestBody"]["content"]
                        if "application/json" in content:
                            item["request"]["body"] = {
                                "mode": "raw",
                                "raw": json.dumps(
                                    content["application/json"]["schema"],
                                    indent=2
                                )
                            }
                    
                    items_by_tag[tag].append(item)
    
    # Add items to collection
    for tag, items in items_by_tag.items():
        collection["item"].append({
            "name": tag,
            "item": items
        })
    
    # Add auth variable
    collection["variable"] = [
        {
            "key": "baseUrl",
            "value": "http://localhost:8000/api/v1"
        },
        {
            "key": "token",
            "value": ""
        }
    ]
    
    # Save collection
    output_path = Path(__file__).parent.parent / "postman" / "LMS Backend.postman_collection.json"
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(collection, f, indent=2)
    
    print(f"Postman collection generated: {output_path}")

if __name__ == "__main__":
    generate_postman_collection()
```

---

## 6. Postman Collections

### Collection Structure

```
postman/
├── LMS Backend.postman_collection.json     # Main collection
├── LMS Backend.postman_environment.json   # Dev environment
├── LMS Backend Demo.postman_collection.json # Demo collection
├── LMS Backend Demo.postman_environment.json # Demo environment
└── demo_seed_snapshot.json               # Demo data snapshot
```

### Environment Variables

```json
{
    "id": "environment-id",
    "name": "Development",
    "values": [
        {
            "key": "baseUrl",
            "value": "http://localhost:8000/api/v1",
            "type": "default"
        },
        {
            "key": "token",
            "value": "",
            "type": "default"
        },
        {
            "key": "userId",
            "value": "",
            "type": "default"
        }
    ]
}
```

---

## 7. Windows Automation Scripts

### Setup Backup Task

```powershell
# scripts/setup_backup_task.ps1
# Setup Windows scheduled task for database backups

param(
    [string]$TaskName = "LMS-Backup",
    [string]$Time = "02:00"  # 2 AM daily
)

$scriptPath = Join-Path $PSScriptRoot "backup_db.bat"
$action = New-ScheduledTaskAction -Execute $scriptPath
$trigger = New-ScheduledTaskTrigger -Daily -At $Time

# Register task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Description "LMS Database Backup" `
    -RunLevel Highest

Write-Host "Backup task created: $TaskName"
Write-Host "Runs daily at $Time"
```

### Setup Restore Drill

```powershell
# scripts/setup_restore_drill_task.ps1
# Setup Windows scheduled task for restore drills (monthly)

param(
    [string]$TaskName = "LMS-RestoreDrill",
    [int]$DayOfMonth = 1,  # First day of month
    [string]$Time = "03:00"  # 3 AM
)

$scriptPath = Join-Path $PSScriptRoot "run_restore_drill.bat"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File `"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth $DayOfMonth -At $Time

# Register task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Description "LMS Monthly Restore Drill" `
    -RunLevel Highest

Write-Host "Restore drill task created: $TaskName"
Write-Host "Runs monthly on day $DayOfMonth at $Time"
```

---

## 8. Operational Procedures

### Deployment Checklist

```markdown
## Pre-Deployment Checklist

### Code
- [ ] All tests passing
- [ ] Code review approved
- [ ] Changelog updated
- [ ] Version bumped

### Testing
- [ ] Unit tests > 75% coverage
- [ ] Integration tests passing
- [ ] Smoke tests passing
- [ ] Load tests within SLA

### Security
- [ ] No secrets in code
- [ ] Dependencies audited
- [ ] Security scan passed
- [ ] CSP configured

### Database
- [ ] Migrations tested
- [ ] Backup verified
- [ ] Rollback plan ready

### Infrastructure
- [ ] Health checks configured
- [ ] Monitoring alerts set
- [ ] Logs forwarded
- [ ] SSL certificates valid

### Communication
- [ ] Stakeholders notified
- [ ] Rollback plan communicated
- [ ] On-call team ready
```

### Incident Response

```markdown
## Incident Response Procedure

### 1. Detection
- Automated alerts trigger
- Customer reports issue

### 2. Assessment
- Determine severity (P1-P4)
- Identify affected components
- Assess business impact

### 3. Communication
- Acknowledge incident
- Update status page
- Notify stakeholders

### 4. Resolution
- Implement fix
- Test in staging
- Deploy to production

### 5. Post-Incident
- Root cause analysis
- Document lessons learned
- Implement improvements
```

### Rollback Procedure

```bash
# Quick rollback
git revert HEAD
git push origin main

# Or rollback to specific version
git reset --hard v1.2.3
git push --force origin main

# Rollback database (if needed)
psql -U lms_user -d lms < backup_pre_deployment.sql
```

---

## Summary

This documentation covers the operational aspects of the LMS backend:

| Category | Tools | Purpose |
|----------|-------|---------|
| CI/CD | GitHub Actions | Automated testing and security scanning |
| Database | pg_dump/pg_restore | Backup and restore |
| Load Testing | K6 | Performance validation |
| Postman | Collections | API testing |
| Automation | PowerShell | Scheduled tasks |
| Operations | Runbooks | Incident response |

---

*This document provides comprehensive documentation for CI/CD, scripts, and operational procedures in the LMS backend.*
