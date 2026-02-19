@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "NO_BUILD=0"
set "NO_MIGRATE=0"
set "FOLLOW_LOGS=0"

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="-NoBuild" (
    set "NO_BUILD=1"
    shift
    goto parse_args
)
if /I "%~1"=="--no-build" (
    set "NO_BUILD=1"
    shift
    goto parse_args
)
if /I "%~1"=="-NoMigrate" (
    set "NO_MIGRATE=1"
    shift
    goto parse_args
)
if /I "%~1"=="--no-migrate" (
    set "NO_MIGRATE=1"
    shift
    goto parse_args
)
if /I "%~1"=="-FollowLogs" (
    set "FOLLOW_LOGS=1"
    shift
    goto parse_args
)
if /I "%~1"=="--follow-logs" (
    set "FOLLOW_LOGS=1"
    shift
    goto parse_args
)
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

if not exist .env (
    if not exist .env.staging.example (
        echo ERROR: Missing .env and .env.staging.example
        popd
        exit /b 1
    )
    copy /Y .env.staging.example .env >nul
    echo Created .env from .env.staging.example
)

set "COMPOSE_FILE=%PROJECT_ROOT%\docker-compose.staging.yml"

echo.
echo ==^> Starting staging containers
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
    echo ==^> Applying staging migrations
    docker compose -f "%COMPOSE_FILE%" exec -T api alembic upgrade head
    if errorlevel 1 (
        popd
        exit /b 1
    )
)

echo.
echo ==^> Waiting for staging readiness endpoint
set "HEALTH_OK=0"
for /L %%I in (1,1,30) do (
    curl.exe -fsS "http://localhost:8001/api/v1/ready" >nul 2>&1
    if !errorlevel! EQU 0 (
        set "HEALTH_OK=1"
        goto health_done
    )
    timeout /t 2 /nobreak >nul
)

:health_done
if "%HEALTH_OK%"=="1" (
    echo Staging API is ready at http://localhost:8001/api/v1/ready
) else (
    echo WARNING: Staging readiness check did not become ready in time.
    echo Check logs with: docker compose -f docker-compose.staging.yml logs --tail=200 api
)

echo.
echo ==^> Staging is running
echo Staging Docs:    http://localhost:8001/docs
echo Staging Metrics: http://localhost:8001/metrics

if /I not "%FOLLOW_LOGS%"=="1" goto after_follow_logs
echo.
echo ==^> Following staging logs (Ctrl+C to stop)
docker compose -f "%COMPOSE_FILE%" logs -f api celery-worker celery-beat
:after_follow_logs

popd
exit /b 0

:show_help
echo.
echo Usage:
echo   scripts\run_staging.bat [options]
echo.
echo Options:
echo   -NoBuild ^| --no-build
echo   -NoMigrate ^| --no-migrate
echo   -FollowLogs ^| --follow-logs
echo   -h ^| --help
echo.
exit /b 1

