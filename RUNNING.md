# Running the LMS Backend

## Prerequisites
- Python 3.9+
- Docker Desktop (recommended)
- PostgreSQL and Redis (optional if using Docker)

## Quick Start

### Option 1: Docker Compose (Recommended)
```powershell
# Copy environment file
cp .env.example .env

# Start all services
docker-compose up --build
```

### Option 2: Direct Python Execution
```powershell
# Create virtual environment and install dependencies
python -m venv venv
venv\Scripts\pip install -r requirements.txt

# Run the development server
venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Run Scripts

### PowerShell Script (`run.ps1`)
```powershell
# Default: Docker mode
.\run.ps1

# Development mode
.\run.ps1 -Mode dev

# Debug mode
.\run.ps1 -Mode debug

# Database migrations only
.\run.ps1 -Mode migrate

# Help
.\run.ps1 -Help
```

### Batch Script (`run.bat`)
```cmd
# Default: Docker mode
run.bat

# Development mode
run.bat dev

# Debug mode
run.bat debug

# Migrations
run.bat migrate
```

## Environment Configuration
1. Copy `.env.example` to `.env`
2. Customize database, Redis, and other settings
3. For production, use `.env.production.example` as template

## API Access
- Development: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health