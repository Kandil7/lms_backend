@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
if not defined PROJECT_ROOT (
    echo ERROR: Failed to resolve project root.
    exit /b 1
)

set "BACKUP_DIR=%PROJECT_ROOT%\backups\db"
if not "%~1"=="" set "BACKUP_DIR=%~1"

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
if errorlevel 1 (
    echo ERROR: Unable to create backup directory: %BACKUP_DIR%
    exit /b 1
)

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "STAMP=%%I"
if not defined STAMP (
    echo ERROR: Failed to generate backup timestamp.
    exit /b 1
)

set "COMPOSE_FILE=%PROJECT_ROOT%\docker-compose.yml"
set "BACKUP_FILE=%BACKUP_DIR%\lms_%STAMP%.dump"

echo.
echo ==^> Creating PostgreSQL backup
echo Output: %BACKUP_FILE%

docker compose -f "%COMPOSE_FILE%" exec -T db sh -lc "pg_dump -U \"$POSTGRES_USER\" -d \"$POSTGRES_DB\" -Fc" > "%BACKUP_FILE%"
if errorlevel 1 (
    echo ERROR: Backup failed.
    if exist "%BACKUP_FILE%" del /q "%BACKUP_FILE%" >nul 2>&1
    exit /b 1
)

echo Backup created successfully: %BACKUP_FILE%
exit /b 0

