@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "FOLLOW_LOGS=0"

:parse_args
if "%~1"=="" goto args_done
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

if not exist .env.observability (
    if not exist .env.observability.example (
        echo ERROR: Missing .env.observability and .env.observability.example
        popd
        exit /b 1
    )
    copy /Y .env.observability.example .env.observability >nul
    echo Created .env.observability from .env.observability.example
)

set "COMPOSE_FILE=%PROJECT_ROOT%\docker-compose.observability.yml"

echo.
echo ==^> Starting observability stack
docker compose -f "%COMPOSE_FILE%" up -d
if errorlevel 1 (
    popd
    exit /b 1
)

echo.
echo ==^> Observability stack is running
echo Prometheus:   http://localhost:9090
echo Alertmanager: http://localhost:9093
echo Grafana:      http://localhost:3001

if /I not "%FOLLOW_LOGS%"=="1" goto after_follow_logs
echo.
echo ==^> Following observability logs (Ctrl+C to stop)
docker compose -f "%COMPOSE_FILE%" logs -f prometheus alertmanager grafana

:after_follow_logs
popd
exit /b 0

:show_help
echo.
echo Usage:
echo   scripts\run_observability.bat [options]
echo.
echo Options:
echo   -FollowLogs ^| --follow-logs
echo   -h ^| --help
echo.
exit /b 1

