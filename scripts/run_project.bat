@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "NO_BUILD=0"
set "NO_MIGRATE=0"
set "SEED_DEMO_DATA=0"
set "CREATE_ADMIN=0"
set "FOLLOW_LOGS=0"

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="-NoBuild" set "NO_BUILD=1" & shift & goto parse_args
if /I "%~1"=="--no-build" set "NO_BUILD=1" & shift & goto parse_args
if /I "%~1"=="-NoMigrate" set "NO_MIGRATE=1" & shift & goto parse_args
if /I "%~1"=="--no-migrate" set "NO_MIGRATE=1" & shift & goto parse_args
if /I "%~1"=="-SeedDemoData" set "SEED_DEMO_DATA=1" & shift & goto parse_args
if /I "%~1"=="--seed-demo-data" set "SEED_DEMO_DATA=1" & shift & goto parse_args
if /I "%~1"=="-CreateAdmin" set "CREATE_ADMIN=1" & shift & goto parse_args
if /I "%~1"=="--create-admin" set "CREATE_ADMIN=1" & shift & goto parse_args
if /I "%~1"=="-FollowLogs" set "FOLLOW_LOGS=1" & shift & goto parse_args
if /I "%~1"=="--follow-logs" set "FOLLOW_LOGS=1" & shift & goto parse_args
if /I "%~1"=="-h" goto show_help
if /I "%~1"=="--help" goto show_help
echo Unknown option: %~1
goto show_help

:args_done
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
if not defined PROJECT_ROOT (
    echo ERROR: Failed to resolve project root.
    exit /b 1
)
pushd "%PROJECT_ROOT%" 2>nul
if errorlevel 1 (
    echo ERROR: Failed to switch to project root.
    exit /b 1
)

where docker >nul 2>&1
if errorlevel 1 (
    echo ERROR: docker command not found in PATH.
    exit /b 1
)

echo.
echo ==^> Preparing environment file
if not exist .env (
    if not exist .env.example (
        echo ERROR: Missing both .env and .env.example
        popd
        exit /b 1
    )
    copy /Y .env.example .env >nul
    echo Created .env from .env.example
) else (
    echo .env already exists
)

set "COMPOSE_FILE=%PROJECT_ROOT%\docker-compose.yml"

echo.
echo ==^> Starting containers
if "%NO_BUILD%"=="1" (
    docker compose -f "%COMPOSE_FILE%" up -d
) else (
    docker compose -f "%COMPOSE_FILE%" up -d --build
)
if errorlevel 1 (
    popd
    exit /b 1
)

if "%NO_MIGRATE%"=="0" (
    echo.
    echo ==^> Applying database migrations
    docker compose -f "%COMPOSE_FILE%" exec -T api alembic upgrade head
    if errorlevel 1 (
        popd
        exit /b 1
    )
)

if "%CREATE_ADMIN%"=="1" (
    echo.
    echo ==^> Creating admin user
    docker compose -f "%COMPOSE_FILE%" exec -T api python scripts/create_admin.py
    if errorlevel 1 (
        popd
        exit /b 1
    )
)

if "%SEED_DEMO_DATA%"=="1" (
    echo.
    echo ==^> Seeding demo data
    docker compose -f "%COMPOSE_FILE%" exec -T api python scripts/seed_demo_data.py
    if errorlevel 1 (
        popd
        exit /b 1
    )
)

echo.
echo ==^> Waiting for API readiness endpoint
set "HEALTH_OK=0"
for /L %%I in (1,1,30) do (
    curl.exe -fsS "http://localhost:8000/api/v1/ready" >nul 2>&1
    if !errorlevel! EQU 0 (
        set "HEALTH_OK=1"
        goto health_done
    )
    timeout /t 2 /nobreak >nul
)

:health_done
if "%HEALTH_OK%"=="1" (
    echo API is ready at http://localhost:8000/api/v1/ready
) else (
    echo WARNING: API readiness check did not become ready in time.
    echo Check logs with: docker compose logs --tail=200 api
)

echo.
echo ==^> Project is running
echo API Docs: http://localhost:8000/docs
echo ReDoc:    http://localhost:8000/redoc

if "%FOLLOW_LOGS%"=="1" (
    echo.
    echo ==^> Following API and worker logs (Ctrl+C to stop)
    docker compose -f "%COMPOSE_FILE%" logs -f api celery-worker celery-beat
)

popd
exit /b 0

:show_help
echo.
echo Usage:
echo   scripts\run_project.bat [options]
echo.
echo Options:
echo   -NoBuild ^| --no-build
echo   -NoMigrate ^| --no-migrate
echo   -CreateAdmin ^| --create-admin
echo   -SeedDemoData ^| --seed-demo-data
echo   -FollowLogs ^| --follow-logs
echo   -h ^| --help
echo.
exit /b 1
