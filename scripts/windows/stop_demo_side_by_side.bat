@echo off
setlocal

set "PROJECT_NAME=lms-demo"
set "COMPOSE_FILE=docker-compose.demo.yml"

echo [demo] Stopping side-by-side demo stack...
docker compose -p "%PROJECT_NAME%" -f "%COMPOSE_FILE%" down -v
exit /b %ERRORLEVEL%
