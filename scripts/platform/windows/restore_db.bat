@echo off
setlocal EnableDelayedExpansion

set "BACKUP_FILE=%~1"
set "CONFIRM_FLAG=%~2"
set "DRY_RUN=false"

if /I "%CONFIRM_FLAG%"=="--dry-run" set "DRY_RUN=true"
if /I "%~3"=="--dry-run" set "DRY_RUN=true"

if "%BACKUP_FILE%"=="" (
  echo Usage: %~nx0 backups\db\lms_YYYYMMDD_HHMMSS.dump [--yes] [--dry-run]
  exit /b 1
)

if not exist "%BACKUP_FILE%" (
  echo [restore_db] Backup file not found: %BACKUP_FILE%
  exit /b 1
)

if /I not "%CONFIRM_FLAG%"=="--yes" if /I not "%~3"=="--yes" (
  set /p CONFIRM=[restore_db] This will overwrite current database. Continue? (yes/no): 
  if /I not "!CONFIRM!"=="yes" (
    echo [restore_db] Restore cancelled.
    exit /b 1
  )
)

if /I "%DRY_RUN%"=="true" (
  echo [restore_db] Dry run OK. Backup file is readable: %BACKUP_FILE%
  exit /b 0
)

set "DB_USER=%POSTGRES_USER%"
set "DB_NAME=%POSTGRES_DB%"
set "COMPOSE_FILE=%LMS_COMPOSE_FILE%"
if "%DB_USER%"=="" set "DB_USER=lms"
if "%DB_NAME%"=="" set "DB_NAME=lms"
if "%COMPOSE_FILE%"=="" set "COMPOSE_FILE=docker-compose.yml"

echo [restore_db] Restoring %BACKUP_FILE% into database %DB_NAME%...
type "%BACKUP_FILE%" | docker compose -f "%COMPOSE_FILE%" exec -T db pg_restore -U %DB_USER% -d %DB_NAME% --clean --if-exists --no-owner --no-privileges
exit /b %ERRORLEVEL%

