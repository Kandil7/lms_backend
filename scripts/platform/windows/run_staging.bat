@echo off
setlocal

set "COMPOSE_FILE=docker-compose.staging.yml"

if not exist ".env" (
  if exist ".env.staging.example" (
    copy /Y ".env.staging.example" ".env" >nul
    echo [run_staging] Created .env from .env.staging.example
  )
)

docker compose -f "%COMPOSE_FILE%" up -d --build
if errorlevel 1 exit /b %ERRORLEVEL%

docker compose -f "%COMPOSE_FILE%" exec -T api alembic upgrade head
exit /b %ERRORLEVEL%

