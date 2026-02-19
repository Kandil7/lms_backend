@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "NO_BUILD=0"
set "NO_MIGRATE=0"
set "FOLLOW_LOGS=0"
set "RESET_PASSWORDS=1"

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
if /I "%~1"=="-NoResetPasswords" (
    set "RESET_PASSWORDS=0"
    shift
    goto parse_args
)
if /I "%~1"=="--no-reset-passwords" (
    set "RESET_PASSWORDS=0"
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

set "RUN_PROJECT_ARGS=-CreateAdmin"
if "%NO_BUILD%"=="1" set "RUN_PROJECT_ARGS=!RUN_PROJECT_ARGS! -NoBuild"
if "%NO_MIGRATE%"=="1" set "RUN_PROJECT_ARGS=!RUN_PROJECT_ARGS! -NoMigrate"

echo.
echo ==^> Starting project stack for demo
call scripts\run_project.bat !RUN_PROJECT_ARGS!
if errorlevel 1 (
    popd
    exit /b 1
)

set "COMPOSE_FILE=%PROJECT_ROOT%\docker-compose.yml"
set "SEED_ARGS=--json-output postman/demo_seed_snapshot.json"
if "%RESET_PASSWORDS%"=="1" set "SEED_ARGS=!SEED_ARGS! --reset-passwords"

echo.
echo ==^> Seeding demo data and writing snapshot JSON
docker compose -f "%COMPOSE_FILE%" exec -T api python scripts/seed_demo_data.py !SEED_ARGS!
if errorlevel 1 (
    popd
    exit /b 1
)

echo.
echo ==^> Regenerating base Postman files
python scripts/generate_postman_collection.py
if errorlevel 1 (
    popd
    exit /b 1
)

echo.
echo ==^> Generating demo Postman files from seeded data
python scripts/generate_demo_postman.py --seed-file postman/demo_seed_snapshot.json
if errorlevel 1 (
    popd
    exit /b 1
)

echo.
echo ==^> Demo assets are ready
echo Seed snapshot:                postman/demo_seed_snapshot.json
echo Demo collection:              postman/LMS Backend Demo.postman_collection.json
echo Demo environment:             postman/LMS Backend Demo.postman_environment.json
echo API docs:                     http://localhost:8000/docs

if /I not "%FOLLOW_LOGS%"=="1" goto after_follow_logs

echo.
echo ==^> Following API and worker logs (Ctrl+C to stop)
docker compose -f "%COMPOSE_FILE%" logs -f api celery-worker celery-beat

:after_follow_logs

popd
exit /b 0

:show_help
echo.
echo Usage:
echo   scripts\run_demo.bat [options]
echo.
echo Options:
echo   -NoBuild ^| --no-build
echo   -NoMigrate ^| --no-migrate
echo   -NoResetPasswords ^| --no-reset-passwords
echo   -FollowLogs ^| --follow-logs
echo   -h ^| --help
echo.
exit /b 1
