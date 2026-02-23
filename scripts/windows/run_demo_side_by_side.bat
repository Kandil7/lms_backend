@echo off
setlocal

if /I "%~1"=="--help" (
  echo Usage: %~nx0 [--logs]
  echo.
  echo Starts an isolated demo stack on http://localhost:8002
  echo and seeds demo users/data automatically.
  exit /b 0
)

set "PROJECT_NAME=lms-demo"
set "COMPOSE_FILE=docker-compose.demo.yml"
set "ENV_FILE=.env.demo"
set "ENV_EXAMPLE=.env.demo.example"
set "SEED_JSON=postman/demo_seed_snapshot.demo.json"
set "DEMO_COLLECTION=postman/LMS Backend Demo Side-by-Side.postman_collection.json"
set "DEMO_ENV=postman/LMS Backend Demo Side-by-Side.postman_environment.json"

if not exist "%ENV_FILE%" (
  if exist "%ENV_EXAMPLE%" (
    copy /Y "%ENV_EXAMPLE%" "%ENV_FILE%" >nul
    echo [demo] Created %ENV_FILE% from %ENV_EXAMPLE%
  ) else (
    echo [demo] Missing %ENV_EXAMPLE%
    exit /b 1
  )
)

echo [demo] Starting side-by-side demo stack on http://localhost:8002 ...
docker compose -p "%PROJECT_NAME%" -f "%COMPOSE_FILE%" up -d --build
if errorlevel 1 exit /b %ERRORLEVEL%

echo [demo] Seeding demo data...
docker compose -p "%PROJECT_NAME%" -f "%COMPOSE_FILE%" exec -T api python scripts/database/seed_demo_data.py --reset-passwords --json-output "%SEED_JSON%"
if errorlevel 1 exit /b %ERRORLEVEL%

echo [demo] Generating demo Postman files...
docker compose -p "%PROJECT_NAME%" -f "%COMPOSE_FILE%" exec -T api python scripts/documentation/generate_demo_postman.py --seed-file "%SEED_JSON%" --output-collection "%DEMO_COLLECTION%" --output-environment "%DEMO_ENV%" --base-url "http://localhost:8002"
if errorlevel 1 exit /b %ERRORLEVEL%

echo.
echo [demo] Ready:
echo        API:  http://localhost:8002
echo        Docs: http://localhost:8002/docs
echo        Readiness: http://localhost:8002/api/v1/ready
echo.
echo [demo] Demo credentials:
echo        admin@lms.local / AdminPass123
echo        instructor@lms.local / InstructorPass123
echo        student@lms.local / StudentPass123
echo.
echo [demo] Stop command:
echo        scripts\windows\stop_demo_side_by_side.bat

if /I "%~1"=="--logs" (
  docker compose -p "%PROJECT_NAME%" -f "%COMPOSE_FILE%" logs -f api db redis
)

exit /b 0
