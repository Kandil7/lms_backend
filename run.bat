@echo off
REM LMS Backend Run Script
REM Usage: run.bat [mode]
REM Modes: docker, dev, debug, migrate

SET MODE=%1

IF "%MODE%"=="" (
    SET MODE=docker
)

ECHO Starting LMS Backend in %MODE% mode...

IF "%MODE%"=="docker" (
    ECHO Running with Docker Compose...
    docker-compose up --build
) ELSE IF "%MODE%"=="dev" (
    ECHO Running development server...
    python -m venv venv
    venv\Scripts\pip install -r requirements.txt
    venv\Scripts\uvicorn app.main:app --port 8000 --reload
) ELSE IF "%MODE%"=="debug" (
    ECHO Running in debug mode...
    python -m venv venv
    venv\Scripts\pip install -r requirements.txt
    set DEBUG=true
    set LOG_LEVEL=DEBUG
    venv\Scripts\uvicorn app.main:app --port 8000 --reload --log-level debug
) ELSE IF "%MODE%"=="migrate" (
    ECHO Running database migrations...
    python -m venv venv
    venv\Scripts\pip install -r requirements.txt
    venv\Scripts\alembic upgrade head
) ELSE (
    ECHO Usage: run.bat [docker|dev|debug|migrate]
    ECHO Default: docker
)