@echo off
setlocal

set "BACKUP_DIR=backups\db"
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "STAMP=%%I"
set "BACKUP_FILE=%BACKUP_DIR%\lms_%STAMP%.dump"
set "DB_USER=%POSTGRES_USER%"
set "DB_NAME=%POSTGRES_DB%"
if "%DB_USER%"=="" set "DB_USER=lms"
if "%DB_NAME%"=="" set "DB_NAME=lms"

echo [backup_db] Writing backup to %BACKUP_FILE%
docker compose exec -T db pg_dump -U %DB_USER% -d %DB_NAME% -Fc > "%BACKUP_FILE%"
if errorlevel 1 exit /b %ERRORLEVEL%

echo [backup_db] Backup completed: %BACKUP_FILE%
exit /b 0

