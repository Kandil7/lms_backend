@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
if not defined PROJECT_ROOT (
    echo ERROR: Failed to resolve project root.
    exit /b 1
)

set "BASE_URL=http://localhost:8000"
set "DURATION=5m"
set "HOST_HEADER="
set "STUDENT_RATE=5"
set "INSTRUCTOR_RATE=2"
set "ADMIN_RATE=1"

if not "%~1"=="" set "BASE_URL=%~1"
if not "%~2"=="" set "DURATION=%~2"
if not "%~3"=="" set "HOST_HEADER=%~3"
if not "%~4"=="" set "STUDENT_RATE=%~4"
if not "%~5"=="" set "INSTRUCTOR_RATE=%~5"
if not "%~6"=="" set "ADMIN_RATE=%~6"

set "K6_SCRIPT=%PROJECT_ROOT%\tests\perf\k6_realistic.js"
if not exist "%K6_SCRIPT%" (
    echo ERROR: Missing k6 script: %K6_SCRIPT%
    exit /b 1
)

where k6 >nul 2>&1
if "%errorlevel%"=="0" (
    echo.
    echo ==^> Running realistic load test with local k6
    echo BASE_URL=%BASE_URL% DURATION=%DURATION% HOST_HEADER=%HOST_HEADER%
    echo STUDENT_RATE=%STUDENT_RATE% INSTRUCTOR_RATE=%INSTRUCTOR_RATE% ADMIN_RATE=%ADMIN_RATE%
    k6 run ^
      -e BASE_URL=%BASE_URL% ^
      -e DURATION=%DURATION% ^
      -e HOST_HEADER=%HOST_HEADER% ^
      -e STUDENT_RATE=%STUDENT_RATE% ^
      -e INSTRUCTOR_RATE=%INSTRUCTOR_RATE% ^
      -e ADMIN_RATE=%ADMIN_RATE% ^
      "%K6_SCRIPT%"
    exit /b %errorlevel%
)

echo.
echo ==^> k6 not found locally, running with Docker image
if "%BASE_URL%"=="http://localhost:8000" (
  set "BASE_URL=http://host.docker.internal:8000"
  if "%HOST_HEADER%"=="" set "HOST_HEADER=localhost"
)
echo BASE_URL=%BASE_URL% DURATION=%DURATION% HOST_HEADER=%HOST_HEADER%
echo STUDENT_RATE=%STUDENT_RATE% INSTRUCTOR_RATE=%INSTRUCTOR_RATE% ADMIN_RATE=%ADMIN_RATE%

docker run --rm -i ^
  --add-host=host.docker.internal:host-gateway ^
  -v "%PROJECT_ROOT%\tests\perf:/scripts" ^
  -e BASE_URL=%BASE_URL% ^
  -e DURATION=%DURATION% ^
  -e HOST_HEADER=%HOST_HEADER% ^
  -e STUDENT_RATE=%STUDENT_RATE% ^
  -e INSTRUCTOR_RATE=%INSTRUCTOR_RATE% ^
  -e ADMIN_RATE=%ADMIN_RATE% ^
  grafana/k6 run /scripts/k6_realistic.js

exit /b %errorlevel%

