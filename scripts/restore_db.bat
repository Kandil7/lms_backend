@echo off
setlocal EnableExtensions

if "%~1"=="" goto show_help

set "BACKUP_FILE=%~1"
if not exist "%BACKUP_FILE%" (
    echo ERROR: Backup file not found: %BACKUP_FILE%
    exit /b 1
)

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
if not defined PROJECT_ROOT (
    echo ERROR: Failed to resolve project root.
    exit /b 1
)

set "COMPOSE_FILE=%PROJECT_ROOT%\docker-compose.yml"
set "AUTO_CONFIRM=0"
if /I "%~2"=="--yes" set "AUTO_CONFIRM=1"
if /I "%~2"=="-y" set "AUTO_CONFIRM=1"

if "%AUTO_CONFIRM%"=="0" (
    echo.
    echo WARNING: This will overwrite current database data.
    set /p "CONFIRM=Type RESTORE to continue: "
    if /I not "%CONFIRM%"=="RESTORE" (
        echo Restore cancelled.
        exit /b 1
    )
)

echo.
echo ==^> Restoring PostgreSQL backup
echo Source: %BACKUP_FILE%

docker compose -f "%COMPOSE_FILE%" exec -T db sh -lc "pg_restore -U \"$POSTGRES_USER\" -d \"$POSTGRES_DB\" --clean --if-exists --no-owner --no-privileges" < "%BACKUP_FILE%"
if errorlevel 1 (
    echo ERROR: Restore failed.
    exit /b 1
)

echo Restore completed successfully.
exit /b 0

:show_help
echo.
echo Usage:
echo   scripts\restore_db.bat ^<backup_file^> [--yes]
echo.
echo Example:
echo   scripts\restore_db.bat backups\db\lms_20260218_235959.dump --yes
echo.
exit /b 1

